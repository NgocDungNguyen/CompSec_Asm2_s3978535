"""
Vietnam Credit Information Center (CIC) - Service Layer

This module provides the business logic for:
1. Credit Score Calculation (Vietnamese banking standards)
2. Credit Report Generation
3. Risk Assessment
4. CIC API Integration (internal API simulating external bureau)

Credit Scoring Model (Vietnam CIC):
Based on Vietnamese banking practices and international standards (FICO-like):

Score Range: 300-900
- 300-579: Poor (High Risk)
- 580-669: Fair (Moderate-High Risk)
- 670-739: Good (Moderate Risk)
- 740-799: Very Good (Low Risk)
- 800-900: Excellent (Very Low Risk)

Scoring Factors (Weighted):
1. Payment History (35%) - Most important factor
   - On-time payment percentage
   - Number of late payments (30, 60, 90+ days)
   - Recent payment behavior (last 12 months)

2. Credit Utilization (30%) - Debt usage ratio
   - Current balance vs. credit limits
   - Total outstanding debt vs. income
   - Debt-to-income ratio (DTI)

3. Credit History Length (15%)
   - Age of oldest account
   - Average age of all accounts
   - Time since last account opened

4. Credit Mix (10%)
   - Variety of credit types (installment, revolving)
   - Number of active accounts

5. Recent Credit Activity (10%)
   - Number of recent inquiries (last 6 months)
   - New accounts opened recently
   - Credit-seeking behavior

Additional Vietnamese-specific factors:
- Asset ownership (real estate, vehicles)
- Employment stability
- Income verification
- Public records (court judgments, bankruptcies)
- Blacklist status
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func

from cic_models import (
    CICAccountStatus,
    CICAsset,
    CICCreditAccount,
    CICCreditScoreHistory,
    CICCustomer,
    CICInquiry,
    CICInquiryType,
    CICPaymentHistory,
    CICPaymentStatus,
    CICPublicRecord,
)
from models import db


class CICService:
    """
    Main service class for CIC operations.
    Handles credit scoring, report generation, and risk assessment.
    """

    # Credit Score Weights (must sum to 1.0)
    WEIGHT_PAYMENT_HISTORY = 0.35
    WEIGHT_CREDIT_UTILIZATION = 0.30
    WEIGHT_CREDIT_HISTORY_LENGTH = 0.15
    WEIGHT_CREDIT_MIX = 0.10
    WEIGHT_RECENT_ACTIVITY = 0.10

    # Base score and ranges
    BASE_SCORE = 300
    MAX_SCORE = 900
    SCORE_RANGE = MAX_SCORE - BASE_SCORE  # 600 points to distribute

    @staticmethod
    def calculate_credit_score(national_id: str) -> Dict:
        """
        Calculate comprehensive credit score for a customer.

        This is the main scoring function that:
        1. Retrieves customer data from CIC database
        2. Analyzes payment history, utilization, etc.
        3. Calculates component scores
        4. Combines into final credit score
        5. Determines risk category

        Args:
            national_id: Customer's national ID number

        Returns:
            Dictionary containing:
            - score: Final credit score (300-900)
            - risk_category: LOW / MEDIUM / HIGH / SEVERE
            - components: Breakdown of score components
            - factors: Key factors affecting score
            - recommendation: Lending recommendation
        """

        customer = CICCustomer.query.filter_by(national_id=national_id).first()

        if not customer:
            return {
                "error": "Customer not found in CIC database",
                "score": None,
                "risk_category": "UNKNOWN",
            }

        # If customer is blacklisted, return minimum score immediately
        if customer.is_blacklisted:
            return {
                "score": CICService.BASE_SCORE,
                "risk_category": "SEVERE",
                "components": {},
                "factors": ["Customer is blacklisted - severe credit history issues"],
                "recommendation": "REJECT - Blacklisted customer",
                "blacklisted": True,
            }

        # Calculate each component score
        payment_score = CICService._calculate_payment_history_score(customer)
        utilization_score = CICService._calculate_utilization_score(customer)
        history_length_score = CICService._calculate_history_length_score(customer)
        credit_mix_score = CICService._calculate_credit_mix_score(customer)
        recent_activity_score = CICService._calculate_recent_activity_score(customer)

        # Weighted combination
        final_score = (
            CICService.BASE_SCORE
            + (
                payment_score
                * CICService.WEIGHT_PAYMENT_HISTORY
                * CICService.SCORE_RANGE
            )
            + (
                utilization_score
                * CICService.WEIGHT_CREDIT_UTILIZATION
                * CICService.SCORE_RANGE
            )
            + (
                history_length_score
                * CICService.WEIGHT_CREDIT_HISTORY_LENGTH
                * CICService.SCORE_RANGE
            )
            + (credit_mix_score * CICService.WEIGHT_CREDIT_MIX * CICService.SCORE_RANGE)
            + (
                recent_activity_score
                * CICService.WEIGHT_RECENT_ACTIVITY
                * CICService.SCORE_RANGE
            )
        )

        # Round to integer
        final_score = int(round(final_score))

        # Apply penalties for public records
        final_score = CICService._apply_public_record_penalties(customer, final_score)

        # Apply bonuses for assets
        final_score = CICService._apply_asset_bonuses(customer, final_score)

        # Ensure score stays in valid range
        final_score = max(CICService.BASE_SCORE, min(CICService.MAX_SCORE, final_score))

        # Determine risk category
        risk_category = CICService._determine_risk_category(final_score)

        # Get key factors affecting score
        factors = CICService._get_score_factors(
            customer,
            {
                "payment": payment_score,
                "utilization": utilization_score,
                "history_length": history_length_score,
                "credit_mix": credit_mix_score,
                "recent_activity": recent_activity_score,
            },
        )

        # Get lending recommendation
        recommendation = CICService._get_lending_recommendation(final_score, customer)

        return {
            "score": final_score,
            "risk_category": risk_category,
            "components": {
                "payment_history": round(payment_score * 100, 1),
                "credit_utilization": round(utilization_score * 100, 1),
                "history_length": round(history_length_score * 100, 1),
                "credit_mix": round(credit_mix_score * 100, 1),
                "recent_activity": round(recent_activity_score * 100, 1),
            },
            "factors": factors,
            "recommendation": recommendation,
            "blacklisted": False,
        }

    @staticmethod
    def _calculate_payment_history_score(customer: CICCustomer) -> float:
        """
        Calculate payment history component (35% of total score).

        Analyzes:
        - Percentage of on-time payments
        - Number and severity of late payments
        - Recent payment behavior (last 12 months weighted more)
        - Missed payments vs. late payments

        Returns:
            Score from 0.0 to 1.0
        """

        accounts = customer.credit_accounts
        if not accounts:
            return 0.5  # No history = neutral score

        total_payments = 0
        on_time_payments = 0
        late_30_count = 0
        late_60_count = 0
        late_90_count = 0
        missed_count = 0

        for account in accounts:
            total_payments += account.total_payments_made
            on_time_payments += account.on_time_payments

            # Count late payments by severity from payment history
            for payment in account.payment_history:
                if payment.payment_status == CICPaymentStatus.LATE_1_30:
                    late_30_count += 1
                elif payment.payment_status == CICPaymentStatus.LATE_31_60:
                    late_60_count += 1
                elif payment.payment_status == CICPaymentStatus.LATE_61_90:
                    late_90_count += 1
                elif payment.payment_status in [
                    CICPaymentStatus.LATE_90_PLUS,
                    CICPaymentStatus.MISSED,
                ]:
                    missed_count += 1

        if total_payments == 0:
            return 0.5

        # Base score: on-time payment percentage
        on_time_ratio = on_time_payments / total_payments
        score = on_time_ratio

        # Penalties for late payments (progressive severity)
        score -= late_30_count * 0.02  # -2% per 30-day late
        score -= late_60_count * 0.05  # -5% per 60-day late
        score -= late_90_count * 0.10  # -10% per 90-day late
        score -= missed_count * 0.15  # -15% per missed payment

        # Bonus for perfect payment history
        if on_time_ratio == 1.0 and total_payments >= 12:
            score += 0.10  # +10% bonus for 1+ year perfect history

        return max(0.0, min(1.0, score))

    @staticmethod
    def _calculate_utilization_score(customer: CICCustomer) -> float:
        """
        Calculate credit utilization component (30% of total score).

        Analyzes:
        - Credit utilization ratio (balance / limit)
        - Debt-to-income ratio
        - Total outstanding debt
        - Per-account utilization

        Optimal: <30% utilization
        Acceptable: 30-50%
        High: 50-75%
        Critical: >75%

        Returns:
            Score from 0.0 to 1.0
        """

        if customer.total_credit_limit == 0:
            # No credit limit means only installment loans
            # Use debt-to-income ratio
            if customer.monthly_income and customer.monthly_income > 0:
                monthly_debt = CICService._estimate_monthly_debt_payment(customer)
                dti_ratio = float(monthly_debt) / float(customer.monthly_income)

                # DTI scoring: <20% excellent, 20-36% good, 36-50% fair, >50% poor
                if dti_ratio <= 0.20:
                    return 1.0
                elif dti_ratio <= 0.36:
                    return 0.80
                elif dti_ratio <= 0.50:
                    return 0.60
                else:
                    return 0.30
            else:
                return 0.5  # No income data

        # Calculate utilization ratio
        utilization_ratio = float(customer.total_outstanding_debt) / float(
            customer.total_credit_limit
        )

        # Score based on utilization
        if utilization_ratio <= 0.10:
            score = 1.0  # Excellent: using <10%
        elif utilization_ratio <= 0.30:
            score = 0.90  # Very good: 10-30%
        elif utilization_ratio <= 0.50:
            score = 0.70  # Good: 30-50%
        elif utilization_ratio <= 0.75:
            score = 0.50  # Fair: 50-75%
        elif utilization_ratio <= 0.90:
            score = 0.30  # Poor: 75-90%
        else:
            score = 0.10  # Very poor: >90% (maxed out)

        return score

    @staticmethod
    def _calculate_history_length_score(customer: CICCustomer) -> float:
        """
        Calculate credit history length component (15% of total score).

        Longer credit history = more predictable behavior.

        Analyzes:
        - Age of oldest account
        - Average age of all accounts
        - Time since last account opened

        Returns:
            Score from 0.0 to 1.0
        """

        if not customer.first_credit_date:
            return 0.0  # No credit history

        # Calculate credit history length in years
        history_years = (datetime.utcnow() - customer.first_credit_date).days / 365.25

        # Score based on history length
        if history_years >= 10:
            score = 1.0
        elif history_years >= 7:
            score = 0.90
        elif history_years >= 5:
            score = 0.80
        elif history_years >= 3:
            score = 0.70
        elif history_years >= 2:
            score = 0.60
        elif history_years >= 1:
            score = 0.50
        else:
            score = 0.30  # Less than 1 year

        return score

    @staticmethod
    def _calculate_credit_mix_score(customer: CICCustomer) -> float:
        """
        Calculate credit mix component (10% of total score).

        Diverse credit types show ability to manage different obligations.

        Analyzes:
        - Number of different credit types
        - Mix of installment vs. revolving credit
        - Active accounts count

        Returns:
            Score from 0.0 to 1.0
        """

        accounts = customer.credit_accounts
        if not accounts:
            return 0.0

        # Count unique account types
        account_types = set(
            acc.account_type
            for acc in accounts
            if acc.account_status == CICAccountStatus.ACTIVE
        )
        num_types = len(account_types)

        # Score based on diversity
        if num_types >= 4:
            score = 1.0  # Excellent mix
        elif num_types == 3:
            score = 0.85
        elif num_types == 2:
            score = 0.70
        elif num_types == 1:
            score = 0.50
        else:
            score = 0.0

        # Bonus for having both installment and revolving credit
        has_installment = any(
            acc.account_type
            in ["PERSONAL_LOAN", "HOME_LOAN", "AUTO_LOAN", "STUDENT_LOAN"]
            for acc in accounts
            if acc.account_status == CICAccountStatus.ACTIVE
        )
        has_revolving = any(
            acc.account_type in ["CREDIT_CARD", "OVERDRAFT"]
            for acc in accounts
            if acc.account_status == CICAccountStatus.ACTIVE
        )

        if has_installment and has_revolving:
            score += 0.10  # +10% bonus

        return min(1.0, score)

    @staticmethod
    def _calculate_recent_activity_score(customer: CICCustomer) -> float:
        """
        Calculate recent credit activity component (10% of total score).

        Too many recent inquiries = credit-seeking behavior (risk).

        Analyzes:
        - Hard inquiries in last 6 months
        - Hard inquiries in last 12 months
        - New accounts opened recently

        Returns:
            Score from 0.0 to 1.0
        """

        six_months_ago = datetime.utcnow() - timedelta(days=180)
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)

        # Count hard inquiries
        recent_inquiries_6m = CICInquiry.query.filter(
            CICInquiry.customer_id == customer.id,
            CICInquiry.inquiry_type == CICInquiryType.HARD_INQUIRY,
            CICInquiry.inquiry_date >= six_months_ago,
        ).count()

        recent_inquiries_12m = CICInquiry.query.filter(
            CICInquiry.customer_id == customer.id,
            CICInquiry.inquiry_type == CICInquiryType.HARD_INQUIRY,
            CICInquiry.inquiry_date >= twelve_months_ago,
        ).count()

        # Score based on inquiry count (6 months weighted more)
        if recent_inquiries_6m == 0:
            score = 1.0  # No recent inquiries - excellent
        elif recent_inquiries_6m == 1:
            score = 0.90  # One inquiry - very good
        elif recent_inquiries_6m == 2:
            score = 0.75  # Two inquiries - good
        elif recent_inquiries_6m <= 4:
            score = 0.60  # 3-4 inquiries - fair
        else:
            score = 0.30  # 5+ inquiries - concerning credit-seeking behavior

        # Additional penalty for many inquiries in 12 months
        if recent_inquiries_12m > 6:
            score -= 0.20

        return max(0.0, score)

    @staticmethod
    def _apply_public_record_penalties(customer: CICCustomer, score: int) -> int:
        """
        Apply penalties for public records (bankruptcies, judgments, etc.).

        These are severe negative factors.
        """

        public_records = CICPublicRecord.query.filter_by(
            customer_id=customer.id, status="ACTIVE"
        ).all()

        for record in public_records:
            if "BANKRUPTCY" in record.record_type:
                score -= 150  # Major penalty
            elif "JUDGMENT" in record.record_type:
                score -= 100
            elif "LIEN" in record.record_type:
                score -= 75

        if customer.has_bankruptcy:
            score -= 100
        if customer.has_court_judgment:
            score -= 75
        if customer.has_debt_restructuring:
            score -= 50

        return score

    @staticmethod
    def _apply_asset_bonuses(customer: CICCustomer, score: int) -> int:
        """
        Apply bonuses for significant asset holdings.

        Assets provide security and recovery potential.
        """

        total_unencumbered_assets = 0

        assets = CICAsset.query.filter_by(customer_id=customer.id).all()
        for asset in assets:
            if not asset.is_encumbered:
                total_unencumbered_assets += float(asset.estimated_value)

        # Bonus based on asset value relative to debt
        if customer.total_outstanding_debt > 0:
            asset_to_debt_ratio = total_unencumbered_assets / float(
                customer.total_outstanding_debt
            )

            if asset_to_debt_ratio >= 2.0:
                score += 30  # Assets >= 2x debt
            elif asset_to_debt_ratio >= 1.0:
                score += 20  # Assets >= debt
            elif asset_to_debt_ratio >= 0.5:
                score += 10  # Assets >= 50% of debt

        return score

    @staticmethod
    def _determine_risk_category(score: int) -> str:
        """Map credit score to risk category."""
        if score >= 740:
            return "LOW"
        elif score >= 670:
            return "MEDIUM"
        elif score >= 580:
            return "HIGH"
        else:
            return "SEVERE"

    @staticmethod
    def _get_score_factors(customer: CICCustomer, component_scores: Dict) -> List[str]:
        """
        Generate human-readable factors affecting the score.
        """

        factors = []

        # Payment history factors
        if component_scores["payment"] >= 0.90:
            factors.append("Excellent payment history - consistently on time")
        elif component_scores["payment"] >= 0.70:
            factors.append("Good payment history with some minor delays")
        elif component_scores["payment"] >= 0.50:
            factors.append("Fair payment history - several late payments")
        else:
            factors.append("Poor payment history - frequent late or missed payments")

        # Utilization factors
        if customer.total_credit_limit > 0:
            util_ratio = float(
                customer.total_outstanding_debt / customer.total_credit_limit
            )
            if util_ratio > 0.75:
                factors.append(
                    f"High credit utilization ({util_ratio*100:.0f}%) - maxing out credit"
                )
            elif util_ratio > 0.50:
                factors.append(f"Moderate credit utilization ({util_ratio*100:.0f}%)")
            elif util_ratio < 0.30:
                factors.append(
                    f"Low credit utilization ({util_ratio*100:.0f}%) - responsible usage"
                )

        # History length
        if customer.first_credit_date:
            years = (datetime.utcnow() - customer.first_credit_date).days / 365.25
            if years >= 5:
                factors.append(f"Established credit history ({years:.1f} years)")
            elif years < 2:
                factors.append(f"Limited credit history ({years:.1f} years)")

        # Recent activity
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        recent_inquiries = CICInquiry.query.filter(
            CICInquiry.customer_id == customer.id,
            CICInquiry.inquiry_type == CICInquiryType.HARD_INQUIRY,
            CICInquiry.inquiry_date >= six_months_ago,
        ).count()

        if recent_inquiries >= 4:
            factors.append(
                f"Multiple recent credit applications ({recent_inquiries}) - credit-seeking behavior"
            )
        elif recent_inquiries == 0:
            factors.append("No recent credit inquiries - stable credit usage")

        # Asset factors
        debt_threshold = float(customer.total_outstanding_debt or 0) * 1.5
        if customer.total_assets_value > debt_threshold:
            factors.append("Strong asset base - assets exceed debt significantly")

        # Negative factors
        if customer.number_of_delinquent_accounts > 0:
            factors.append(
                f"{customer.number_of_delinquent_accounts} account(s) currently delinquent"
            )

        if customer.has_bankruptcy:
            factors.append("Bankruptcy on record")

        if customer.has_court_judgment:
            factors.append("Court judgment on record")

        return factors

    @staticmethod
    def _get_lending_recommendation(score: int, customer: CICCustomer) -> str:
        """
        Generate lending recommendation based on score and profile.
        """

        if customer.is_blacklisted:
            return "REJECT - Customer is blacklisted"

        if score >= 800:
            return "STRONGLY APPROVE - Excellent credit profile, minimal risk"
        elif score >= 740:
            return "APPROVE - Very good credit, low risk"
        elif score >= 670:
            return "APPROVE WITH CONDITIONS - Good credit, standard terms"
        elif score >= 600:
            return "MANUAL REVIEW - Moderate risk, consider collateral or guarantor"
        elif score >= 550:
            return (
                "CAUTIOUS APPROVAL - Higher risk, require collateral and reduced limit"
            )
        else:
            return "REJECT - High risk profile, recommend denial"

    @staticmethod
    def _estimate_monthly_debt_payment(customer: CICCustomer) -> Decimal:
        """Estimate total monthly debt payments from all accounts."""
        total = Decimal(0)
        for account in customer.credit_accounts:
            if (
                account.account_status == CICAccountStatus.ACTIVE
                and account.monthly_payment
            ):
                total += account.monthly_payment
        return total

    @staticmethod
    def perform_credit_check(
        national_id: str,
        applicant_name: str,
        loan_amount: Decimal,
        inquiring_institution: str = "RMIT NeoBank",
    ) -> Dict:
        """
        Perform a full credit check (simulates external CIC API call).

        This function:
        1. Records the inquiry in CIC database (hard inquiry)
        2. Calculates current credit score
        3. Retrieves credit report summary
        4. Returns comprehensive credit assessment

        Args:
            national_id: Customer's national ID
            applicant_name: Customer's full name
            loan_amount: Requested loan amount
            inquiring_institution: Name of requesting bank

        Returns:
            Dictionary with credit check results
        """

        # Find customer
        customer = CICCustomer.query.filter_by(national_id=national_id).first()

        if not customer:
            return {
                "success": False,
                "error": "CUSTOMER_NOT_FOUND",
                "message": f"No credit record found for national ID: {national_id}",
                "bureau_reference": None,
                "score": None,
                "risk_band": "UNKNOWN",
            }

        # Record the inquiry (hard inquiry impacts score slightly)
        inquiry = CICInquiry(
            customer_id=customer.id,
            inquiry_type=CICInquiryType.HARD_INQUIRY,
            inquiring_institution=inquiring_institution,
            inquiry_purpose=f"Loan Application - Amount: {loan_amount:,.0f} VND",
            loan_amount_requested=loan_amount,
            inquiry_date=datetime.utcnow(),
        )
        db.session.add(inquiry)

        # Calculate credit score
        score_result = CICService.calculate_credit_score(national_id)

        # Update customer's current score
        customer.current_credit_score = score_result["score"]
        customer.score_last_updated = datetime.utcnow()
        customer.risk_category = score_result["risk_category"]

        # Save score history
        score_history = CICCreditScoreHistory(
            customer_id=customer.id,
            score=score_result["score"],
            score_date=datetime.utcnow().date(),
            risk_category=score_result["risk_category"],
            primary_factor=(
                score_result["factors"][0] if score_result["factors"] else None
            ),
        )
        db.session.add(score_history)

        # Commit changes
        db.session.commit()

        # Generate bureau reference
        bureau_reference = f"CIC-VN-{datetime.utcnow().strftime('%Y%m%d')}-{national_id}-{int(datetime.utcnow().timestamp())}"

        # Build comprehensive response
        return {
            "success": True,
            "bureau_reference": bureau_reference,
            "score": score_result["score"],
            "risk_band": score_result["risk_category"],
            "recommendation": score_result["recommendation"],
            "customer_info": {
                "national_id": customer.national_id,
                "full_name": customer.full_name,
                "date_of_birth": customer.date_of_birth.strftime("%Y-%m-%d"),
                "employment_status": customer.employment_status,
                "monthly_income": (
                    float(customer.monthly_income) if customer.monthly_income else None
                ),
            },
            "credit_summary": {
                "total_outstanding_debt": float(customer.total_outstanding_debt),
                "total_credit_limit": float(customer.total_credit_limit),
                "number_of_active_accounts": customer.number_of_active_accounts,
                "number_of_delinquent_accounts": customer.number_of_delinquent_accounts,
                "total_assets_value": float(customer.total_assets_value),
            },
            "score_components": score_result["components"],
            "key_factors": score_result["factors"],
            "flags": {
                "is_blacklisted": customer.is_blacklisted,
                "has_bankruptcy": customer.has_bankruptcy,
                "has_court_judgment": customer.has_court_judgment,
                "has_debt_restructuring": customer.has_debt_restructuring,
            },
            "raw_response": json.dumps(score_result, indent=2),
        }

    @staticmethod
    def get_credit_report(national_id: str) -> Optional[Dict]:
        """
        Retrieve full credit report for a customer.

        Used by loan officers to review detailed credit history.
        """

        customer = CICCustomer.query.filter_by(national_id=national_id).first()
        if not customer:
            return None

        # Get all related data
        accounts = CICCreditAccount.query.filter_by(customer_id=customer.id).all()
        assets = CICAsset.query.filter_by(customer_id=customer.id).all()
        inquiries = (
            CICInquiry.query.filter_by(customer_id=customer.id)
            .order_by(CICInquiry.inquiry_date.desc())
            .limit(10)
            .all()
        )
        public_records = CICPublicRecord.query.filter_by(customer_id=customer.id).all()
        score_history = (
            CICCreditScoreHistory.query.filter_by(customer_id=customer.id)
            .order_by(CICCreditScoreHistory.score_date.desc())
            .limit(12)
            .all()
        )

        return {
            "customer": customer,
            "accounts": accounts,
            "assets": assets,
            "inquiries": inquiries,
            "public_records": public_records,
            "score_history": score_history,
            "current_score": customer.current_credit_score,
            "risk_category": customer.risk_category,
        }
