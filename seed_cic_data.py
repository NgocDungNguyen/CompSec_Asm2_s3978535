"""
CIC Data Seeding Script
Generates comprehensive Credit Information Center data for all loan applicants.

This script creates realistic credit profiles including:
- Customer records with employment and income
- Credit accounts (loans, credit cards) with payment history
- Assets (real estate, vehicles, securities)
- Credit inquiries
- Public records (for some customers)
- Credit scores calculated from all factors

Execution: python seed_cic_data.py
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func

from app import app
from cic_models import (
    CICAccountStatus,
    CICAccountType,
    CICAsset,
    CICAssetType,
    CICCreditAccount,
    CICCustomer,
    CICCustomerType,
    CICEmploymentStatus,
    CICInquiry,
    CICInquiryType,
    CICPaymentHistory,
    CICPaymentStatus,
    CICPublicRecord,
)
from cic_service import CICService
from models import LoanApplication, db

# ============================================================================
# Vietnamese Data Sets
# ============================================================================

VIETNAMESE_SURNAMES = [
    "Nguyen",
    "Tran",
    "Le",
    "Pham",
    "Hoang",
    "Phan",
    "Vo",
    "Dang",
    "Bui",
    "Do",
    "Ngo",
    "Duong",
    "Ly",
    "Vu",
    "Truong",
    "Dinh",
    "Huynh",
    "Lam",
    "Trinh",
]

VIETNAMESE_MIDDLE_NAMES = [
    "Van",
    "Thi",
    "Duc",
    "Minh",
    "Thanh",
    "Hoang",
    "Ngoc",
    "Anh",
    "Quoc",
    "Hong",
    "Thu",
    "Kim",
    "Ha",
    "Mai",
]

VIETNAMESE_GIVEN_NAMES = [
    "Anh",
    "Minh",
    "Tuan",
    "Hung",
    "Hai",
    "Nam",
    "Cuong",
    "Dung",
    "Hieu",
    "Long",
    "Phong",
    "Quan",
    "Son",
    "Thanh",
    "Tien",
    "Vinh",
    "Linh",
    "Hoa",
    "Lan",
    "My",
    "Phuong",
    "Thao",
    "Huong",
    "Nga",
]

VIETNAMESE_CITIES = [
    "Ho Chi Minh City",
    "Hanoi",
    "Da Nang",
    "Can Tho",
    "Hai Phong",
    "Bien Hoa",
    "Nha Trang",
    "Hue",
    "Vung Tau",
    "Buon Ma Thuot",
]

VIETNAMESE_DISTRICTS_HCM = [
    "District 1",
    "District 3",
    "District 5",
    "District 7",
    "District 10",
    "Binh Thanh",
    "Phu Nhuan",
    "Tan Binh",
    "Go Vap",
    "Binh Tan",
]

VIETNAMESE_STREETS = [
    "Le Loi",
    "Nguyen Hue",
    "Hai Ba Trung",
    "Tran Hung Dao",
    "Ly Thuong Kiet",
    "Vo Van Tan",
    "Dien Bien Phu",
    "Cach Mang Thang Tam",
    "Nam Ky Khoi Nghia",
    "Nguyen Trai",
]

OCCUPATIONS = [
    "Software Engineer",
    "Teacher",
    "Doctor",
    "Nurse",
    "Accountant",
    "Sales Manager",
    "Marketing Specialist",
    "Business Analyst",
    "Civil Engineer",
    "Architect",
    "Pharmacist",
    "Lawyer",
    "Bank Officer",
    "Government Officer",
    "Restaurant Owner",
    "Shop Owner",
    "Taxi Driver",
    "Factory Worker",
    "Office Administrator",
    "Customer Service Representative",
]

EMPLOYERS = [
    "Vingroup",
    "FPT Corporation",
    "Viettel Group",
    "Vietcombank",
    "BIDV",
    "Vietnam Airlines",
    "Vinamilk",
    "Hoa Phat Group",
    "Masan Group",
    "VinFast",
    "Ministry of Education",
    "Ministry of Health",
    "Cho Ray Hospital",
    "Bach Mai Hospital",
    "HCMC University",
    "Hanoi University",
    "Small Business Owner",
    "Self-Employed",
]

LENDERS = [
    "Vietcombank",
    "BIDV",
    "VietinBank",
    "Agribank",
    "Techcombank",
    "MB Bank",
    "ACB",
    "VPBank",
    "Sacombank",
    "HDBank",
    "SHB",
    "LienVietPostBank",
    "FE Credit",
    "Home Credit Vietnam",
    "Prudential Finance",
]


# ============================================================================
# Credit Profile Templates
# ============================================================================


class CreditProfileType:
    """Different credit profile archetypes for realistic distribution"""

    EXCELLENT = "EXCELLENT"  # 800-900 score
    VERY_GOOD = "VERY_GOOD"  # 740-799 score
    GOOD = "GOOD"  # 670-739 score
    FAIR = "FAIR"  # 580-669 score
    POOR = "POOR"  # 300-579 score


# Profile distribution (realistic for Vietnam)
PROFILE_DISTRIBUTION = {
    CreditProfileType.EXCELLENT: 0.10,  # 10%
    CreditProfileType.VERY_GOOD: 0.20,  # 20%
    CreditProfileType.GOOD: 0.35,  # 35%
    CreditProfileType.FAIR: 0.25,  # 25%
    CreditProfileType.POOR: 0.10,  # 10%
}


# ============================================================================
# Helper Functions
# ============================================================================


def random_date(start_date, end_date):
    """Generate random date between start and end."""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)


def generate_national_id():
    """Generate realistic Vietnamese National ID (12 digits)."""
    return "".join([str(random.randint(0, 9)) for _ in range(12)])


def generate_phone_number():
    """Generate Vietnamese phone number."""
    prefixes = ["090", "091", "093", "097", "098", "096", "086", "083", "084", "085"]
    return random.choice(prefixes) + "".join(
        [str(random.randint(0, 9)) for _ in range(7)]
    )


def generate_address(city):
    """Generate realistic Vietnamese address."""
    street_number = random.randint(1, 999)
    street = random.choice(VIETNAMESE_STREETS)
    if city == "Ho Chi Minh City":
        district = random.choice(VIETNAMESE_DISTRICTS_HCM)
    else:
        district = f"District {random.randint(1, 10)}"
    return f"{street_number} {street} Street, {district}, {city}"


def select_profile_type():
    """Select credit profile type based on distribution."""
    rand = random.random()
    cumulative = 0
    for profile_type, prob in PROFILE_DISTRIBUTION.items():
        cumulative += prob
        if rand <= cumulative:
            return profile_type
    return CreditProfileType.GOOD


# ============================================================================
# CIC Customer Creation
# ============================================================================


def create_cic_customer(loan_application: LoanApplication, profile_type: str):
    """
    Create comprehensive CIC customer profile with credit history.

    Args:
        loan_application: The loan application to create CIC profile for
        profile_type: Credit profile template (EXCELLENT, GOOD, FAIR, POOR)
    """

    print(
        f"Creating CIC profile for {loan_application.applicant_name} ({profile_type})..."
    )

    # Check if customer already exists
    existing = CICCustomer.query.filter_by(
        national_id=loan_application.national_id
    ).first()
    if existing:
        print(f"  ⚠️  Customer already exists in CIC: {existing.national_id}")
        return existing

    # Create base customer record
    customer = CICCustomer(
        national_id=loan_application.national_id,
        full_name=loan_application.applicant_name,
        date_of_birth=loan_application.dob,
        gender=random.choice(["MALE", "FEMALE"]),
        customer_type=CICCustomerType.INDIVIDUAL,
        phone_number=loan_application.contact_phone,
        email=loan_application.contact_email,
        current_address=generate_address(
            "Ho Chi Minh City"
            if loan_application.branch_code.startswith("HCM")
            else "Hanoi" if loan_application.branch_code.startswith("HN") else "Da Nang"
        ),
        permanent_address=generate_address(random.choice(VIETNAMESE_CITIES)),
        province_city=(
            "Ho Chi Minh City"
            if loan_application.branch_code.startswith("HCM")
            else "Hanoi" if loan_application.branch_code.startswith("HN") else "Da Nang"
        ),
    )

    # Employment and income based on profile type
    if profile_type == CreditProfileType.EXCELLENT:
        customer.employment_status = CICEmploymentStatus.FULL_TIME_EMPLOYED
        customer.monthly_income = Decimal(random.randint(30, 100)) * Decimal(
            1000000
        )  # 30-100M VND
        customer.years_employed = random.randint(5, 20)
        customer.occupation = random.choice(
            [
                "Software Engineer",
                "Doctor",
                "Lawyer",
                "Senior Manager",
                "Business Owner",
            ]
        )
        customer.employer_name = random.choice(EMPLOYERS[:10])  # Top employers

    elif profile_type == CreditProfileType.VERY_GOOD:
        customer.employment_status = CICEmploymentStatus.FULL_TIME_EMPLOYED
        customer.monthly_income = Decimal(random.randint(20, 50)) * Decimal(
            1000000
        )  # 20-50M VND
        customer.years_employed = random.randint(3, 15)
        customer.occupation = random.choice(OCCUPATIONS[:15])
        customer.employer_name = random.choice(EMPLOYERS)

    elif profile_type == CreditProfileType.GOOD:
        customer.employment_status = random.choice(
            [
                CICEmploymentStatus.FULL_TIME_EMPLOYED,
                CICEmploymentStatus.SELF_EMPLOYED,
            ]
        )
        customer.monthly_income = Decimal(random.randint(12, 30)) * Decimal(
            1000000
        )  # 12-30M VND
        customer.years_employed = random.randint(2, 10)
        customer.occupation = random.choice(OCCUPATIONS)
        customer.employer_name = random.choice(EMPLOYERS)

    elif profile_type == CreditProfileType.FAIR:
        customer.employment_status = random.choice(
            [
                CICEmploymentStatus.FULL_TIME_EMPLOYED,
                CICEmploymentStatus.PART_TIME_EMPLOYED,
                CICEmploymentStatus.SELF_EMPLOYED,
            ]
        )
        customer.monthly_income = Decimal(random.randint(8, 20)) * Decimal(
            1000000
        )  # 8-20M VND
        customer.years_employed = random.randint(1, 7)
        customer.occupation = random.choice(OCCUPATIONS)
        customer.employer_name = random.choice(EMPLOYERS)

    else:  # POOR
        customer.employment_status = random.choice(
            [
                CICEmploymentStatus.PART_TIME_EMPLOYED,
                CICEmploymentStatus.SELF_EMPLOYED,
                CICEmploymentStatus.UNEMPLOYED,
            ]
        )
        customer.monthly_income = Decimal(random.randint(5, 15)) * Decimal(
            1000000
        )  # 5-15M VND
        customer.years_employed = random.randint(0, 5)
        customer.occupation = random.choice(OCCUPATIONS[-10:])
        customer.employer_name = random.choice(EMPLOYERS[-5:])

    # Set first credit date (credit history length)
    if profile_type == CreditProfileType.EXCELLENT:
        years_ago = random.randint(7, 15)
    elif profile_type == CreditProfileType.VERY_GOOD:
        years_ago = random.randint(5, 10)
    elif profile_type == CreditProfileType.GOOD:
        years_ago = random.randint(3, 7)
    elif profile_type == CreditProfileType.FAIR:
        years_ago = random.randint(1, 4)
    else:
        years_ago = random.randint(1, 3)

    customer.first_credit_date = datetime.utcnow() - timedelta(days=years_ago * 365)

    db.session.add(customer)
    db.session.flush()  # Get customer ID

    # Create credit accounts based on profile
    create_credit_accounts(customer, profile_type)

    # Create assets based on profile
    create_assets(customer, profile_type)

    # Create credit inquiries
    create_inquiries(customer, profile_type)

    # Create public records (if poor profile)
    if profile_type == CreditProfileType.POOR and random.random() < 0.3:
        create_public_records(customer)

    # Calculate and update financial summary
    update_customer_summary(customer)

    db.session.commit()

    print(
        f"  ✅ Created CIC profile with {customer.number_of_active_accounts} accounts"
    )
    return customer


def create_credit_accounts(customer: CICCustomer, profile_type: str):
    """Create credit accounts (loans, credit cards) for customer."""

    # Number of accounts based on profile
    if profile_type == CreditProfileType.EXCELLENT:
        num_accounts = random.randint(4, 7)
        account_types = [
            CICAccountType.CREDIT_CARD,
            CICAccountType.HOME_LOAN,
            CICAccountType.AUTO_LOAN,
            CICAccountType.PERSONAL_LOAN,
        ]
    elif profile_type == CreditProfileType.VERY_GOOD:
        num_accounts = random.randint(3, 5)
        account_types = [
            CICAccountType.CREDIT_CARD,
            CICAccountType.PERSONAL_LOAN,
            CICAccountType.AUTO_LOAN,
        ]
    elif profile_type == CreditProfileType.GOOD:
        num_accounts = random.randint(2, 4)
        account_types = [CICAccountType.CREDIT_CARD, CICAccountType.PERSONAL_LOAN]
    elif profile_type == CreditProfileType.FAIR:
        num_accounts = random.randint(1, 3)
        account_types = [CICAccountType.PERSONAL_LOAN, CICAccountType.CREDIT_CARD]
    else:  # POOR
        num_accounts = random.randint(1, 2)
        account_types = [CICAccountType.PERSONAL_LOAN]

    for i in range(num_accounts):
        account_type = random.choice(account_types)
        create_single_credit_account(customer, account_type, profile_type)


def create_single_credit_account(
    customer: CICCustomer, account_type: str, profile_type: str
):
    """Create a single credit account with payment history."""

    # Generate account details based on type
    if account_type == CICAccountType.HOME_LOAN:
        original_amount = Decimal(random.randint(500, 3000)) * Decimal(
            1000000
        )  # 500M-3B VND
        tenure_months = random.randint(120, 300)  # 10-25 years
        interest_rate = Decimal(random.uniform(7.0, 12.0))
        is_secured = True
        collateral_type = "Real Estate"
        collateral_value = original_amount * Decimal(1.5)

    elif account_type == CICAccountType.AUTO_LOAN:
        original_amount = Decimal(random.randint(200, 800)) * Decimal(
            1000000
        )  # 200M-800M VND
        tenure_months = random.randint(36, 84)  # 3-7 years
        interest_rate = Decimal(random.uniform(8.0, 14.0))
        is_secured = True
        collateral_type = "Vehicle"
        collateral_value = original_amount * Decimal(1.2)

    elif account_type == CICAccountType.CREDIT_CARD:
        original_amount = Decimal(0)
        credit_limit = Decimal(random.randint(10, 100)) * Decimal(
            1000000
        )  # 10M-100M VND
        tenure_months = None
        interest_rate = Decimal(random.uniform(18.0, 24.0))
        is_secured = False
        collateral_type = None
        collateral_value = None

    else:  # PERSONAL_LOAN
        original_amount = Decimal(random.randint(20, 300)) * Decimal(
            1000000
        )  # 20M-300M VND
        tenure_months = random.randint(12, 60)  # 1-5 years
        interest_rate = Decimal(random.uniform(12.0, 20.0))
        is_secured = False
        collateral_type = None
        collateral_value = None

    # Determine account status and balance based on profile
    months_active = random.randint(
        6, min(60, int((datetime.utcnow() - customer.first_credit_date).days / 30))
    )

    if profile_type in [CreditProfileType.EXCELLENT, CreditProfileType.VERY_GOOD]:
        account_status = random.choice(
            [CICAccountStatus.CURRENT, CICAccountStatus.CLOSED]
        )
        days_past_due = 0
        on_time_ratio = random.uniform(0.95, 1.0)
    elif profile_type == CreditProfileType.GOOD:
        account_status = random.choice(
            [
                CICAccountStatus.CURRENT,
                CICAccountStatus.CURRENT,
                CICAccountStatus.CLOSED,
            ]
        )
        days_past_due = random.choice([0, 0, 0, 15])
        on_time_ratio = random.uniform(0.85, 0.95)
    elif profile_type == CreditProfileType.FAIR:
        account_status = random.choice(
            [
                CICAccountStatus.CURRENT,
                CICAccountStatus.DELINQUENT_30,
                CICAccountStatus.CLOSED,
            ]
        )
        days_past_due = random.choice([0, 15, 35, 45])
        on_time_ratio = random.uniform(0.70, 0.85)
    else:  # POOR
        account_status = random.choice(
            [
                CICAccountStatus.DELINQUENT_60,
                CICAccountStatus.DELINQUENT_90,
                CICAccountStatus.DEFAULT,
            ]
        )
        days_past_due = random.choice([65, 95, 120, 180])
        on_time_ratio = random.uniform(0.40, 0.70)

    # Calculate current balance
    if account_status == CICAccountStatus.CLOSED:
        current_balance = Decimal(0)
    elif account_type == CICAccountType.CREDIT_CARD:
        current_balance = credit_limit * Decimal(random.uniform(0.1, 0.8))
    else:
        # Amortization approximation
        payments_made = months_active
        current_balance = (
            original_amount * (1 - Decimal(payments_made / tenure_months))
            if tenure_months
            else original_amount * Decimal(0.5)
        )
        current_balance = max(Decimal(0), current_balance)

    # Calculate monthly payment
    if account_type == CICAccountType.CREDIT_CARD:
        monthly_payment = credit_limit * Decimal(0.05)  # 5% minimum payment
    elif tenure_months:
        monthly_payment = original_amount / Decimal(tenure_months)
    else:
        monthly_payment = None

    # Disbursement and maturity dates
    disbursement_date = (datetime.utcnow() - timedelta(days=months_active * 30)).date()
    if tenure_months:
        maturity_date = (
            datetime.utcnow() + timedelta(days=(tenure_months - months_active) * 30)
        ).date()
    else:
        maturity_date = None

    closure_date = (
        disbursement_date + timedelta(days=months_active * 30)
        if account_status == CICAccountStatus.CLOSED
        else None
    )

    # Create account
    account = CICCreditAccount(
        customer_id=customer.id,
        account_number=f"{random.choice(LENDERS)[:3].upper()}{generate_national_id()[:10]}",
        lender_name=random.choice(LENDERS),
        lender_code=f"BANK{random.randint(100, 999)}",
        account_type=account_type,
        account_status=account_status,
        disbursement_date=disbursement_date,
        maturity_date=maturity_date,
        closure_date=closure_date,
        original_loan_amount=original_amount,
        current_balance=current_balance,
        credit_limit=(
            credit_limit if account_type == CICAccountType.CREDIT_CARD else None
        ),
        monthly_payment=monthly_payment,
        interest_rate=interest_rate,
        days_past_due=days_past_due,
        highest_days_past_due=(
            days_past_due
            if profile_type == CreditProfileType.POOR
            else random.randint(0, 30)
        ),
        is_secured=is_secured,
        collateral_type=collateral_type,
        collateral_value=collateral_value,
    )

    db.session.add(account)
    db.session.flush()

    # Create payment history
    create_payment_history(account, months_active, on_time_ratio, profile_type)


def create_payment_history(
    account: CICCreditAccount,
    months_active: int,
    on_time_ratio: float,
    profile_type: str,
):
    """Generate monthly payment history for an account."""

    total_payments = 0
    on_time_payments = 0
    late_payments = 0
    missed_payments = 0

    for month_offset in range(months_active):
        payment_date_due = account.disbursement_date + timedelta(
            days=(month_offset + 1) * 30
        )

        # Determine if payment was on time
        if random.random() < on_time_ratio:
            # On time
            payment_status = CICPaymentStatus.ON_TIME
            days_late = 0
            payment_date_actual = payment_date_due
            on_time_payments += 1
        else:
            # Late or missed
            if profile_type in [
                CreditProfileType.EXCELLENT,
                CreditProfileType.VERY_GOOD,
            ]:
                days_late = random.randint(1, 15)
                payment_status = CICPaymentStatus.LATE_1_30
            elif profile_type == CreditProfileType.GOOD:
                days_late = random.randint(5, 45)
                payment_status = (
                    CICPaymentStatus.LATE_1_30
                    if days_late <= 30
                    else CICPaymentStatus.LATE_31_60
                )
            elif profile_type == CreditProfileType.FAIR:
                days_late = random.randint(10, 70)
                if days_late <= 30:
                    payment_status = CICPaymentStatus.LATE_1_30
                elif days_late <= 60:
                    payment_status = CICPaymentStatus.LATE_31_60
                else:
                    payment_status = CICPaymentStatus.LATE_61_90
            else:  # POOR
                days_late = random.randint(30, 120)
                if days_late <= 30:
                    payment_status = CICPaymentStatus.LATE_1_30
                elif days_late <= 60:
                    payment_status = CICPaymentStatus.LATE_31_60
                elif days_late <= 90:
                    payment_status = CICPaymentStatus.LATE_61_90
                else:
                    payment_status = CICPaymentStatus.LATE_90_PLUS

            payment_date_actual = payment_date_due + timedelta(days=days_late)
            late_payments += 1

        total_payments += 1

        amount_due = (
            account.monthly_payment if account.monthly_payment else Decimal(1000000)
        )
        amount_paid = (
            amount_due if payment_status != CICPaymentStatus.MISSED else Decimal(0)
        )

        payment_record = CICPaymentHistory(
            account_id=account.id,
            payment_month=payment_date_due.month,
            payment_year=payment_date_due.year,
            payment_due_date=payment_date_due,
            amount_due=amount_due,
            amount_paid=amount_paid,
            payment_date=payment_date_actual,
            days_late=days_late,
            payment_status=payment_status,
            is_partial_payment=False,
            is_settlement=False,
        )
        db.session.add(payment_record)

    # Update account statistics
    account.total_payments_made = total_payments
    account.on_time_payments = on_time_payments
    account.late_payments = late_payments
    account.missed_payments = missed_payments


def create_assets(customer: CICCustomer, profile_type: str):
    """Create asset records for customer."""

    if profile_type == CreditProfileType.EXCELLENT:
        num_assets = random.randint(2, 4)
        asset_types = [
            CICAssetType.REAL_ESTATE,
            CICAssetType.VEHICLE,
            CICAssetType.SECURITIES,
        ]
    elif profile_type == CreditProfileType.VERY_GOOD:
        num_assets = random.randint(1, 3)
        asset_types = [CICAssetType.REAL_ESTATE, CICAssetType.VEHICLE]
    elif profile_type == CreditProfileType.GOOD:
        num_assets = random.randint(0, 2)
        asset_types = [CICAssetType.VEHICLE, CICAssetType.DEPOSITS]
    elif profile_type == CreditProfileType.FAIR:
        num_assets = random.randint(0, 1)
        asset_types = [CICAssetType.VEHICLE]
    else:
        num_assets = 0
        asset_types = []

    for _ in range(num_assets):
        asset_type = random.choice(asset_types)

        if asset_type == CICAssetType.REAL_ESTATE:
            estimated_value = Decimal(random.randint(1000, 5000)) * Decimal(
                1000000
            )  # 1B-5B VND
            description = f"Apartment in {customer.province_city}"
            location = generate_address(customer.province_city)
            is_encumbered = random.choice([True, False])
            encumbrance = (
                estimated_value * Decimal(0.6) if is_encumbered else Decimal(0)
            )

        elif asset_type == CICAssetType.VEHICLE:
            estimated_value = Decimal(random.randint(200, 800)) * Decimal(
                1000000
            )  # 200M-800M VND
            description = random.choice(
                ["Honda CR-V", "Toyota Camry", "Mazda CX-5", "Honda City"]
            )
            location = customer.province_city
            is_encumbered = random.choice([True, False])
            encumbrance = (
                estimated_value * Decimal(0.5) if is_encumbered else Decimal(0)
            )

        elif asset_type == CICAssetType.SECURITIES:
            estimated_value = Decimal(random.randint(50, 500)) * Decimal(
                1000000
            )  # 50M-500M VND
            description = "Stock portfolio (VNIndex)"
            location = None
            is_encumbered = False
            encumbrance = Decimal(0)

        else:  # DEPOSITS
            estimated_value = Decimal(random.randint(20, 200)) * Decimal(
                1000000
            )  # 20M-200M VND
            description = "Fixed deposit"
            location = None
            is_encumbered = False
            encumbrance = Decimal(0)

        asset = CICAsset(
            customer_id=customer.id,
            asset_type=asset_type,
            asset_description=description,
            asset_location=location,
            estimated_value=estimated_value,
            valuation_date=datetime.utcnow().date(),
            valuation_method="Market",
            ownership_percentage=Decimal(100.0),
            is_encumbered=is_encumbered,
            encumbrance_amount=encumbrance,
            acquisition_date=random_date(
                customer.first_credit_date, datetime.utcnow()
            ).date(),
        )
        db.session.add(asset)


def create_inquiries(customer: CICCustomer, profile_type: str):
    """Create credit inquiry records."""

    # Number of inquiries in last 12 months
    if profile_type in [CreditProfileType.EXCELLENT, CreditProfileType.VERY_GOOD]:
        num_inquiries = random.randint(0, 2)
    elif profile_type == CreditProfileType.GOOD:
        num_inquiries = random.randint(1, 3)
    elif profile_type == CreditProfileType.FAIR:
        num_inquiries = random.randint(2, 5)
    else:  # POOR
        num_inquiries = random.randint(3, 8)

    for _ in range(num_inquiries):
        inquiry_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))

        inquiry = CICInquiry(
            customer_id=customer.id,
            inquiry_type=CICInquiryType.HARD_INQUIRY,
            inquiring_institution=random.choice(LENDERS),
            inquiry_purpose=random.choice(
                ["Personal Loan", "Credit Card", "Auto Loan", "Home Loan"]
            ),
            loan_amount_requested=Decimal(random.randint(10, 500)) * Decimal(1000000),
            inquiry_date=inquiry_date,
        )
        db.session.add(inquiry)


def create_public_records(customer: CICCustomer):
    """Create negative public records for poor credit customers."""

    record_types = ["COURT_JUDGMENT", "TAX_LIEN", "DEBT_COLLECTION"]
    record_type = random.choice(record_types)

    filing_date = (datetime.utcnow() - timedelta(days=random.randint(365, 1825))).date()

    record = CICPublicRecord(
        customer_id=customer.id,
        record_type=record_type,
        filing_date=filing_date,
        status="ACTIVE",
        court_name=f"{customer.province_city} People's Court",
        case_number=f"CV{random.randint(100000, 999999)}",
        amount=Decimal(random.randint(10, 100)) * Decimal(1000000),
        description=f"{record_type} - Financial dispute",
    )
    db.session.add(record)

    customer.has_court_judgment = True


def update_customer_summary(customer: CICCustomer):
    """Calculate and update customer financial summary fields."""

    accounts = CICCreditAccount.query.filter_by(customer_id=customer.id).all()

    total_credit_limit = Decimal(0)
    total_outstanding_debt = Decimal(0)
    num_active = 0
    num_closed = 0
    num_delinquent = 0

    for account in accounts:
        if account.credit_limit:
            total_credit_limit += account.credit_limit

        if (
            account.account_status == CICAccountStatus.ACTIVE
            or account.account_status == CICAccountStatus.CURRENT
        ):
            total_outstanding_debt += account.current_balance
            num_active += 1
        elif account.account_status == CICAccountStatus.CLOSED:
            num_closed += 1

        if (
            "DELINQUENT" in account.account_status
            or account.account_status == CICAccountStatus.DEFAULT
        ):
            num_delinquent += 1

    # Calculate total assets
    assets = CICAsset.query.filter_by(customer_id=customer.id).all()
    total_assets_value = sum(float(asset.estimated_value) for asset in assets)

    # Update customer
    customer.total_credit_limit = total_credit_limit
    customer.total_outstanding_debt = total_outstanding_debt
    customer.total_assets_value = Decimal(total_assets_value)
    customer.number_of_active_accounts = num_active
    customer.number_of_closed_accounts = num_closed
    customer.number_of_delinquent_accounts = num_delinquent


# ============================================================================
# Main Seeding Function
# ============================================================================


def seed_cic_data():
    """Main function to seed all CIC data."""

    print("=" * 80)
    print("🏦 SEEDING VIETNAM CREDIT INFORMATION CENTER (CIC) DATABASE")
    print("=" * 80)

    # Get all loan applications
    applications = LoanApplication.query.all()
    print(f"\n📊 Found {len(applications)} loan applications in CAS system")
    print(f"🎯 Creating comprehensive CIC profiles for each applicant...\n")

    created_count = 0
    skipped_count = 0

    for i, app in enumerate(applications, 1):
        # Check if already exists
        existing = CICCustomer.query.filter_by(national_id=app.national_id).first()
        if existing:
            skipped_count += 1
            continue

        # Select profile type
        profile_type = select_profile_type()

        # Create CIC profile
        try:
            create_cic_customer(app, profile_type)
            created_count += 1

            if created_count % 50 == 0:
                print(f"  ⏳ Progress: {created_count}/{len(applications)} created...")

        except Exception as e:
            print(f"  ❌ Error creating profile for {app.applicant_name}: {e}")
            db.session.rollback()

    print(f"\n" + "=" * 80)
    print(f"✅ CIC DATA SEEDING COMPLETE")
    print(f"=" * 80)
    print(f"📊 Created: {created_count} new CIC customer profiles")
    print(f"⏭️  Skipped: {skipped_count} (already existed)")
    print(f"\n🧮 Now calculating credit scores for all customers...\n")

    # Calculate credit scores for all customers
    calculate_all_credit_scores()


def calculate_all_credit_scores():
    """Calculate credit scores for all CIC customers."""

    customers = CICCustomer.query.all()
    print(f"🎯 Calculating credit scores for {len(customers)} customers...\n")

    for i, customer in enumerate(customers, 1):
        try:
            # Calculate score
            result = CICService.calculate_credit_score(customer.national_id)

            # Update customer record
            customer.current_credit_score = result["score"]
            customer.risk_category = result["risk_category"]
            customer.score_last_updated = datetime.utcnow()

            if i % 100 == 0:
                db.session.commit()
                print(f"  ⏳ Progress: {i}/{len(customers)} scores calculated...")

        except Exception as e:
            print(f"  ❌ Error calculating score for {customer.national_id}: {e}")

    db.session.commit()

    print(f"\n✅ All credit scores calculated successfully!")

    # Print statistics
    print(f"\n" + "=" * 80)
    print(f"📊 CREDIT SCORE DISTRIBUTION")
    print(f"=" * 80)

    excellent = CICCustomer.query.filter(
        CICCustomer.current_credit_score >= 800
    ).count()
    very_good = CICCustomer.query.filter(
        CICCustomer.current_credit_score >= 740,
        CICCustomer.current_credit_score < 800,
    ).count()
    good = CICCustomer.query.filter(
        CICCustomer.current_credit_score >= 670,
        CICCustomer.current_credit_score < 740,
    ).count()
    fair = CICCustomer.query.filter(
        CICCustomer.current_credit_score >= 580,
        CICCustomer.current_credit_score < 670,
    ).count()
    poor = CICCustomer.query.filter(CICCustomer.current_credit_score < 580).count()

    print(
        f"🟢 Excellent (800-900): {excellent} customers ({excellent/len(customers)*100:.1f}%)"
    )
    print(
        f"🔵 Very Good (740-799): {very_good} customers ({very_good/len(customers)*100:.1f}%)"
    )
    print(f"🟡 Good (670-739): {good} customers ({good/len(customers)*100:.1f}%)")
    print(f"🟠 Fair (580-669): {fair} customers ({fair/len(customers)*100:.1f}%)")
    print(f"🔴 Poor (300-579): {poor} customers ({poor/len(customers)*100:.1f}%)")

    avg_score = db.session.query(func.avg(CICCustomer.current_credit_score)).scalar()
    print(f"\n📈 Average Credit Score: {avg_score:.0f}")

    print(f"\n" + "=" * 80)
    print(f"🎉 CIC DATABASE FULLY POPULATED AND READY FOR INTEGRATION!")
    print(f"=" * 80)


if __name__ == "__main__":
    with app.app_context():
        seed_cic_data()
