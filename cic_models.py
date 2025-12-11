"""
Vietnam National Credit Information Center (CIC) - Database Models

This module simulates the Vietnamese Credit Information Center database,
which stores comprehensive financial profiles of all Vietnamese citizens
and entities for credit risk assessment.

Real-world Context:
The CIC (Credit Information Center) is operated by the State Bank of Vietnam
and collects credit information from:
- Commercial banks
- Microfinance institutions
- Finance companies
- Insurance companies
- Securities firms

Data Categories:
1. Personal/Entity Information (PII)
2. Credit Accounts (loans, credit cards, overdrafts)
3. Payment History (on-time, late, defaults)
4. Assets and Collateral
5. Liabilities and Debt
6. Credit Inquiries (hard pulls)
7. Public Records (bankruptcies, court judgments)
8. Employment and Income Information

Educational Purpose:
Demonstrates how credit bureaus structure data for risk assessment
and how financial institutions integrate with such systems.
"""

from datetime import datetime

from models import db

# ============================================================================
# CIC Status and Category Constants
# ============================================================================


class CICCustomerType:
    """Customer classification in CIC system"""

    INDIVIDUAL = "INDIVIDUAL"  # Personal customers
    BUSINESS = "BUSINESS"  # SME, corporations
    GOVERNMENT = "GOVERNMENT"  # Public sector entities


class CICAccountType:
    """Types of credit accounts tracked by CIC"""

    PERSONAL_LOAN = "PERSONAL_LOAN"
    HOME_LOAN = "HOME_LOAN"
    AUTO_LOAN = "AUTO_LOAN"
    CREDIT_CARD = "CREDIT_CARD"
    BUSINESS_LOAN = "BUSINESS_LOAN"
    OVERDRAFT = "OVERDRAFT"
    MICROFINANCE = "MICROFINANCE"
    STUDENT_LOAN = "STUDENT_LOAN"


class CICAccountStatus:
    """Credit account status classifications"""

    ACTIVE = "ACTIVE"  # Currently active and in good standing
    CLOSED = "CLOSED"  # Paid off and closed
    CURRENT = "CURRENT"  # Active with no delinquency
    DELINQUENT_30 = "DELINQUENT_30"  # 1-30 days late
    DELINQUENT_60 = "DELINQUENT_60"  # 31-60 days late
    DELINQUENT_90 = "DELINQUENT_90"  # 61-90 days late
    DELINQUENT_120_PLUS = "DELINQUENT_120_PLUS"  # 90+ days late
    DEFAULT = "DEFAULT"  # Defaulted / written off
    RESTRUCTURED = "RESTRUCTURED"  # Debt restructuring


class CICPaymentStatus:
    """Payment record status for each billing cycle"""

    ON_TIME = "ON_TIME"  # Paid on or before due date
    LATE_1_30 = "LATE_1_30"  # 1-30 days late
    LATE_31_60 = "LATE_31_60"  # 31-60 days late
    LATE_61_90 = "LATE_61_90"  # 61-90 days late
    LATE_90_PLUS = "LATE_90_PLUS"  # 90+ days late
    MISSED = "MISSED"  # Payment not made
    PAID_SETTLEMENT = "PAID_SETTLEMENT"  # Settled for less than owed


class CICAssetType:
    """Types of assets recorded in CIC"""

    REAL_ESTATE = "REAL_ESTATE"  # Land, houses, apartments
    VEHICLE = "VEHICLE"  # Cars, motorcycles
    SECURITIES = "SECURITIES"  # Stocks, bonds
    DEPOSITS = "DEPOSITS"  # Bank deposits, certificates
    BUSINESS = "BUSINESS"  # Business ownership
    OTHER = "OTHER"  # Other valuable assets


class CICInquiryType:
    """Types of credit inquiries"""

    HARD_INQUIRY = "HARD_INQUIRY"  # Credit application (impacts score)
    SOFT_INQUIRY = "SOFT_INQUIRY"  # Pre-qualification (no impact)
    ACCOUNT_REVIEW = "ACCOUNT_REVIEW"  # Existing account monitoring
    PROMOTIONAL = "PROMOTIONAL"  # Marketing purposes


class CICEmploymentStatus:
    """Employment status classifications"""

    FULL_TIME_EMPLOYED = "FULL_TIME_EMPLOYED"
    PART_TIME_EMPLOYED = "PART_TIME_EMPLOYED"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    BUSINESS_OWNER = "BUSINESS_OWNER"
    RETIRED = "RETIRED"
    STUDENT = "STUDENT"
    UNEMPLOYED = "UNEMPLOYED"
    HOMEMAKER = "HOMEMAKER"


# ============================================================================
# CIC Database Models
# ============================================================================


class CICCustomer(db.Model):
    """
    Core customer profile in CIC database.

    This represents the master record for each individual/entity
    tracked by the Credit Information Center.

    Privacy & Security:
    - In real systems, PII is encrypted at rest (AES-256)
    - Access is logged and audited (regulatory requirement)
    - Data retention policies apply (e.g., 7 years in Vietnam)
    - GDPR-like protections: right to access, correction, erasure
    """

    __tablename__ = "cic_customers"

    id = db.Column(db.Integer, primary_key=True)

    # Identity Information (PII - Protected Data)
    national_id = db.Column(
        db.String(32), unique=True, nullable=False, index=True
    )  # CCCD/CMND
    full_name = db.Column(db.String(128), nullable=False, index=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(16), nullable=True)  # MALE / FEMALE / OTHER
    customer_type = db.Column(
        db.String(32), nullable=False, default=CICCustomerType.INDIVIDUAL
    )

    # Contact Information
    phone_number = db.Column(db.String(32), nullable=True)
    email = db.Column(db.String(128), nullable=True)
    current_address = db.Column(db.Text, nullable=True)
    permanent_address = db.Column(db.Text, nullable=True)
    province_city = db.Column(db.String(64), nullable=True)  # Ho Chi Minh, Hanoi, etc.

    # Employment & Income Information
    employment_status = db.Column(db.String(32), nullable=True)
    employer_name = db.Column(db.String(128), nullable=True)
    occupation = db.Column(db.String(128), nullable=True)
    monthly_income = db.Column(db.Numeric(18, 2), nullable=True)  # VND
    years_employed = db.Column(db.Integer, nullable=True)

    # Financial Summary (Calculated Fields - Updated Periodically)
    total_credit_limit = db.Column(
        db.Numeric(18, 2), default=0
    )  # Total available credit
    total_outstanding_debt = db.Column(db.Numeric(18, 2), default=0)  # Current debt
    total_assets_value = db.Column(db.Numeric(18, 2), default=0)  # Declared assets
    number_of_active_accounts = db.Column(db.Integer, default=0)
    number_of_closed_accounts = db.Column(db.Integer, default=0)
    number_of_delinquent_accounts = db.Column(db.Integer, default=0)

    # Credit Score (CIC Proprietary Score - Similar to FICO)
    # Range: 300-900 (300-579: Poor, 580-669: Fair, 670-739: Good, 740-799: Very Good, 800-900: Excellent)
    current_credit_score = db.Column(db.Integer, nullable=True, index=True)
    score_last_updated = db.Column(db.DateTime, nullable=True)
    previous_credit_score = db.Column(db.Integer, nullable=True)

    # Risk Classification
    risk_category = db.Column(
        db.String(16), nullable=True
    )  # LOW / MEDIUM / HIGH / SEVERE
    internal_rating = db.Column(
        db.String(16), nullable=True
    )  # AAA, AA, A, BBB, BB, B, CCC, CC, C, D

    # Flags and Alerts
    is_blacklisted = db.Column(
        db.Boolean, default=False
    )  # Severe default / fraud history
    has_bankruptcy = db.Column(db.Boolean, default=False)
    has_court_judgment = db.Column(db.Boolean, default=False)
    has_debt_restructuring = db.Column(db.Boolean, default=False)

    # Timestamps
    first_credit_date = db.Column(
        db.DateTime, nullable=True
    )  # Date of first credit account
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<CICCustomer {self.national_id} - {self.full_name} (Score: {self.current_credit_score})>"


class CICCreditAccount(db.Model):
    """
    Individual credit accounts (loans, credit cards, etc.) tracked by CIC.

    Each customer can have multiple credit accounts from different lenders.
    This model represents the trade lines that appear on credit reports.
    """

    __tablename__ = "cic_credit_accounts"

    id = db.Column(db.Integer, primary_key=True)

    # Link to Customer
    customer_id = db.Column(
        db.Integer, db.ForeignKey("cic_customers.id"), nullable=False, index=True
    )

    # Account Identification
    account_number = db.Column(
        db.String(64), unique=True, nullable=False, index=True
    )  # Hashed/masked in real systems
    lender_name = db.Column(db.String(128), nullable=False)  # Bank / Finance Company
    lender_code = db.Column(db.String(32), nullable=True)  # Institution identifier

    # Account Details
    account_type = db.Column(db.String(32), nullable=False)  # Loan type
    account_status = db.Column(
        db.String(32), nullable=False, default=CICAccountStatus.ACTIVE
    )
    disbursement_date = db.Column(db.Date, nullable=True)  # When loan was given
    maturity_date = db.Column(db.Date, nullable=True)  # When loan should be paid off
    closure_date = db.Column(db.Date, nullable=True)  # When account was closed

    # Financial Details
    original_loan_amount = db.Column(db.Numeric(18, 2), nullable=False)
    current_balance = db.Column(
        db.Numeric(18, 2), nullable=False
    )  # Outstanding principal
    credit_limit = db.Column(
        db.Numeric(18, 2), nullable=True
    )  # For revolving credit (credit cards)
    monthly_payment = db.Column(db.Numeric(18, 2), nullable=True)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=True)  # Annual percentage rate

    # Performance Metrics
    days_past_due = db.Column(db.Integer, default=0)  # Current delinquency
    highest_days_past_due = db.Column(
        db.Integer, default=0
    )  # Worst delinquency ever recorded
    total_payments_made = db.Column(db.Integer, default=0)
    on_time_payments = db.Column(db.Integer, default=0)
    late_payments = db.Column(db.Integer, default=0)
    missed_payments = db.Column(db.Integer, default=0)

    # Collateral (if secured loan)
    is_secured = db.Column(db.Boolean, default=False)
    collateral_type = db.Column(
        db.String(64), nullable=True
    )  # House, car, deposit, etc.
    collateral_value = db.Column(db.Numeric(18, 2), nullable=True)

    # Timestamps
    last_payment_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    customer = db.relationship("CICCustomer", backref="credit_accounts", lazy=True)

    def __repr__(self):
        return f"<CICCreditAccount {self.account_number} - {self.account_type} ({self.account_status})>"


class CICPaymentHistory(db.Model):
    """
    Monthly payment records for each credit account.

    This is the most important factor in credit scoring (typically 35% weight).
    Shows payment behavior over time - the primary indicator of creditworthiness.
    """

    __tablename__ = "cic_payment_history"

    id = db.Column(db.Integer, primary_key=True)

    # Link to Account
    account_id = db.Column(
        db.Integer, db.ForeignKey("cic_credit_accounts.id"), nullable=False, index=True
    )

    # Payment Period
    payment_month = db.Column(db.Integer, nullable=False)  # 1-12
    payment_year = db.Column(db.Integer, nullable=False)  # e.g., 2024
    payment_due_date = db.Column(db.Date, nullable=False)

    # Payment Details
    amount_due = db.Column(db.Numeric(18, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(18, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=True)  # Actual payment date
    days_late = db.Column(db.Integer, default=0)

    # Status
    payment_status = db.Column(
        db.String(32), nullable=False, default=CICPaymentStatus.ON_TIME
    )

    # Flags
    is_partial_payment = db.Column(db.Boolean, default=False)
    is_settlement = db.Column(db.Boolean, default=False)  # Settled for less than owed

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    account = db.relationship("CICCreditAccount", backref="payment_history", lazy=True)

    def __repr__(self):
        return f"<CICPaymentHistory {self.payment_year}-{self.payment_month:02d} ({self.payment_status})>"


class CICAsset(db.Model):
    """
    Customer assets registered in CIC system.

    Assets are important for:
    - Collateral-based lending
    - Debt-to-asset ratio calculation
    - Net worth assessment
    - Recovery potential in case of default
    """

    __tablename__ = "cic_assets"

    id = db.Column(db.Integer, primary_key=True)

    # Link to Customer
    customer_id = db.Column(
        db.Integer, db.ForeignKey("cic_customers.id"), nullable=False, index=True
    )

    # Asset Details
    asset_type = db.Column(db.String(32), nullable=False)
    asset_description = db.Column(db.String(256), nullable=True)
    asset_location = db.Column(db.String(256), nullable=True)  # For real estate

    # Valuation
    estimated_value = db.Column(db.Numeric(18, 2), nullable=False)
    valuation_date = db.Column(db.Date, nullable=False)
    valuation_method = db.Column(
        db.String(64), nullable=True
    )  # Market, Book, Appraisal

    # Ownership
    ownership_percentage = db.Column(
        db.Numeric(5, 2), default=100.00
    )  # In case of joint ownership
    is_encumbered = db.Column(
        db.Boolean, default=False
    )  # Has existing loan/lien against it
    encumbrance_amount = db.Column(db.Numeric(18, 2), nullable=True)  # Outstanding lien

    # Documentation
    registration_number = db.Column(
        db.String(64), nullable=True
    )  # Property deed, vehicle registration
    acquisition_date = db.Column(db.Date, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    customer = db.relationship("CICCustomer", backref="assets", lazy=True)

    def __repr__(self):
        return f"<CICAsset {self.asset_type} - {self.estimated_value:,.0f} VND>"


class CICInquiry(db.Model):
    """
    Credit inquiry records - when a lender checks a customer's credit.

    Hard inquiries (for credit applications) can temporarily lower credit scores.
    Multiple inquiries in short time indicate credit-seeking behavior (risk factor).
    """

    __tablename__ = "cic_inquiries"

    id = db.Column(db.Integer, primary_key=True)

    # Link to Customer
    customer_id = db.Column(
        db.Integer, db.ForeignKey("cic_customers.id"), nullable=False, index=True
    )

    # Inquiry Details
    inquiry_type = db.Column(db.String(32), nullable=False)
    inquiring_institution = db.Column(db.String(128), nullable=False)  # Bank name
    institution_code = db.Column(db.String(32), nullable=True)
    inquiry_purpose = db.Column(
        db.String(128), nullable=True
    )  # Loan type being applied

    # Timestamps
    inquiry_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Context
    loan_amount_requested = db.Column(
        db.Numeric(18, 2), nullable=True
    )  # How much customer applied for

    # Relationships
    customer = db.relationship("CICCustomer", backref="inquiries", lazy=True)

    def __repr__(self):
        return f"<CICInquiry {self.inquiring_institution} - {self.inquiry_date.strftime('%Y-%m-%d')}>"


class CICPublicRecord(db.Model):
    """
    Public records affecting creditworthiness.

    Includes:
    - Bankruptcies
    - Court judgments
    - Tax liens
    - Civil suits
    - Criminal financial offenses
    """

    __tablename__ = "cic_public_records"

    id = db.Column(db.Integer, primary_key=True)

    # Link to Customer
    customer_id = db.Column(
        db.Integer, db.ForeignKey("cic_customers.id"), nullable=False, index=True
    )

    # Record Details
    record_type = db.Column(
        db.String(64), nullable=False
    )  # BANKRUPTCY / JUDGMENT / LIEN
    filing_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), nullable=False)  # ACTIVE / RESOLVED / DISCHARGED
    court_name = db.Column(db.String(128), nullable=True)
    case_number = db.Column(db.String(64), nullable=True)

    # Financial Impact
    amount = db.Column(
        db.Numeric(18, 2), nullable=True
    )  # Judgment amount, debt discharged
    resolution_date = db.Column(db.Date, nullable=True)

    # Description
    description = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    customer = db.relationship("CICCustomer", backref="public_records", lazy=True)

    def __repr__(self):
        return f"<CICPublicRecord {self.record_type} - {self.status}>"


class CICCreditScoreHistory(db.Model):
    """
    Historical credit scores for trend analysis.

    Tracks how a customer's creditworthiness changes over time.
    Useful for:
    - Identifying improving or deteriorating credit profiles
    - Audit trails for score changes
    - Regulatory compliance and dispute resolution
    """

    __tablename__ = "cic_credit_score_history"

    id = db.Column(db.Integer, primary_key=True)

    # Link to Customer
    customer_id = db.Column(
        db.Integer, db.ForeignKey("cic_customers.id"), nullable=False, index=True
    )

    # Score Details
    score = db.Column(db.Integer, nullable=False)
    score_date = db.Column(db.Date, nullable=False, index=True)
    risk_category = db.Column(db.String(16), nullable=True)

    # Contributing Factors (Reason Codes)
    primary_factor = db.Column(db.String(128), nullable=True)
    secondary_factor = db.Column(db.String(128), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    customer = db.relationship("CICCustomer", backref="score_history", lazy=True)

    def __repr__(self):
        return f"<CICCreditScoreHistory Score: {self.score} on {self.score_date}>"
