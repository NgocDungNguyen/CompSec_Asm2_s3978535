"""
Seed Script - Generate 3-Tier Workflow Banking Data
Creates users, branches, and realistic loan applications with 3-tier approval workflow.
"""

import random
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from app import app
from models import (
    ApplicationGrade,
    ApplicationStatus,
    CreditCheck,
    CreditCheckStatus,
    LoanApplication,
    Role,
    User,
    db,
)

# ============================================================================
# Configuration
# ============================================================================

BRANCHES = [
    {"code": "HCM01", "city": "Ho Chi Minh City", "name": "District 1 Branch"},
    {"code": "HCM02", "city": "Ho Chi Minh City", "name": "District 7 Branch"},
    {"code": "HN01", "city": "Hanoi", "name": "Hoan Kiem Branch"},
    {"code": "HN02", "city": "Hanoi", "name": "Cau Giay Branch"},
    {"code": "HN03", "city": "Hanoi", "name": "Dong Da Branch"},
    {"code": "DN01", "city": "Da Nang", "name": "Hai Chau Branch"},
    {"code": "DN02", "city": "Da Nang", "name": "Son Tra Branch"},
    {"code": "CT01", "city": "Can Tho", "name": "Ninh Kieu Branch"},
    {"code": "HP01", "city": "Hai Phong", "name": "Hong Bang Branch"},
]

DEFAULT_PASSWORD = "Password123"


# ============================================================================
# Name Generation
# ============================================================================


def generate_vietnamese_names():
    """Generate realistic Vietnamese names."""
    surnames = [
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
    ]
    middle_names = [
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
    given_names_male = [
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
    ]
    given_names_female = [
        "Lan",
        "Mai",
        "Nga",
        "Hoa",
        "Huong",
        "Linh",
        "Phuong",
        "Thao",
        "Trang",
        "Yen",
        "Chi",
        "Ha",
        "Nhi",
        "Quynh",
        "Thu",
        "Uyen",
    ]

    names = []
    for _ in range(20):
        surname = random.choice(surnames)
        if random.random() < 0.5:
            middle = random.choice(middle_names)
            given = random.choice(given_names_male)
        else:
            middle = "Thi"
            given = random.choice(given_names_female)
        names.append(f"{surname} {middle} {given}")

    return names


# ============================================================================
# User Creation
# ============================================================================


def create_users():
    """Create users for all branches with 3-tier structure."""
    print("\n🏦 Creating users...")
    users_created = 0

    # Create SUPER_ADMIN
    super_admin = User(
        username="superadmin",
        password_hash=generate_password_hash(DEFAULT_PASSWORD),
        full_name="System Administrator",
        branch_code="HEAD_OFFICE",
        role=Role.SUPER_ADMIN,
        is_active=True,
    )
    db.session.add(super_admin)
    users_created += 1
    print(f"  ✅ Created SUPER_ADMIN: superadmin")

    # Create users for each branch
    for branch in BRANCHES:
        branch_code = branch["code"]
        branch_name = branch["name"]

        # 2 Branch Officers per branch
        for i in range(1, 3):
            username = f"bo_{branch_code.lower()}_{i}"
            full_name = f"Branch Officer {i} - {branch_name}"
            user = User(
                username=username,
                password_hash=generate_password_hash(DEFAULT_PASSWORD),
                full_name=full_name,
                branch_code=branch_code,
                role=Role.BRANCH_OFFICER,
                is_active=True,
            )
            db.session.add(user)
            users_created += 1

        # 2-3 Approval Experts per branch
        expert_count = 2 if len(BRANCHES) <= 7 else 3
        for i in range(1, expert_count + 1):
            username = f"expert_{branch_code.lower()}_{i}"
            full_name = f"Approval Expert {i} - {branch_name}"
            user = User(
                username=username,
                password_hash=generate_password_hash(DEFAULT_PASSWORD),
                full_name=full_name,
                branch_code=branch_code,
                role=Role.APPROVAL_EXPERT,
                is_active=True,
            )
            db.session.add(user)
            users_created += 1

        # 1-2 Branch HO per branch
        ho_count = 1 if branch_code in ["CT01", "HP01"] else 2
        for i in range(1, ho_count + 1):
            username = f"ho_{branch_code.lower()}_{i}"
            full_name = f"Branch HO {i} - {branch_name}"
            user = User(
                username=username,
                password_hash=generate_password_hash(DEFAULT_PASSWORD),
                full_name=full_name,
                branch_code=branch_code,
                role=Role.BRANCH_HO,
                is_active=True,
            )
            db.session.add(user)
            users_created += 1

        print(f"  ✅ Created users for {branch_code}: {branch_name}")

    db.session.commit()
    print(f"\n✅ Total users created: {users_created}")
    return users_created


# ============================================================================
# Application Generation
# ============================================================================


def generate_realistic_application(branch_code, creator_user, days_ago):
    """Generate a realistic loan application with 3-tier workflow."""
    names = generate_vietnamese_names()
    name = random.choice(names)

    # Generate realistic national ID (12 digits)
    national_id = f"{random.randint(100000000000, 999999999999)}"

    # Generate date of birth (age 22-65)
    age = random.randint(22, 65)
    dob = datetime.now().date() - timedelta(days=age * 365 + random.randint(0, 364))

    # Generate phone number
    phone_prefix = random.choice(
        [
            "090",
            "091",
            "093",
            "094",
            "097",
            "098",
            "032",
            "033",
            "034",
            "035",
            "036",
            "037",
            "038",
            "039",
        ]
    )
    phone = (
        f"+84 {phone_prefix} {random.randint(100, 999)} {random.randint(1000, 9999)}"
    )

    # Generate email
    email_name = name.lower().replace(" ", ".")
    email_domain = random.choice(
        ["gmail.com", "yahoo.com", "outlook.com", "vtc.vn", "fpt.vn"]
    )
    email = f"{email_name}{random.randint(1, 999)}@{email_domain}"

    # Product codes with realistic loan amounts
    products = {
        "PL_SAL": (5000000, 50000000),  # Personal Loan: 5M-50M VND
        "PL_BIZ": (10000000, 200000000),  # Business Loan: 10M-200M VND
        "HL_RES": (100000000, 2000000000),  # Home Loan: 100M-2B VND
        "AL_NEW": (50000000, 500000000),  # Auto Loan: 50M-500M VND
        "AL_USED": (30000000, 300000000),  # Used Auto: 30M-300M VND
        "EDU_LOAN": (20000000, 150000000),  # Education: 20M-150M VND
    }

    product = random.choice(list(products.keys()))
    amount_range = products[product]
    amount = random.randint(amount_range[0], amount_range[1])
    amount = (amount // 1000000) * 1000000  # Round to nearest million

    # Tenure based on loan type
    if product.startswith("HL_"):
        tenure = random.choice([120, 180, 240, 300, 360])
    elif product.startswith("AL_"):
        tenure = random.choice([12, 24, 36, 48, 60, 84])
    elif product == "EDU_LOAN":
        tenure = random.choice([24, 36, 48, 60])
    else:
        tenure = random.choice([6, 12, 18, 24, 36, 48])

    # Generate CIF-like application reference
    app_ref = f"CIF{branch_code}{random.randint(100000, 999999)}"

    # Realistic timestamp
    created_at = datetime.now() - timedelta(days=days_ago)
    updated_at = created_at + timedelta(hours=random.randint(1, 48))

    # Create application
    app = LoanApplication(
        application_ref=app_ref,
        applicant_name=name,
        national_id=national_id,
        dob=dob,
        contact_phone=phone,
        contact_email=email,
        product_code=product,
        requested_amount=amount,
        tenure_months=tenure,
        branch_code=branch_code,
        created_by_user_id=creator_user.id,
        status=ApplicationStatus.DRAFT,
        remarks=f"Application created on {created_at.strftime('%Y-%m-%d')}",
        created_at=created_at,
        updated_at=updated_at,
    )

    return app


def assign_workflow_status(app, branch_users):
    """Assign realistic workflow status and assignments."""
    # Get experts and HOs for this branch
    experts = [u for u in branch_users if u.role == Role.APPROVAL_EXPERT]
    hos = [u for u in branch_users if u.role == Role.BRANCH_HO]

    # Status distribution for realistic workflow
    status_roll = random.random()

    if status_roll < 0.15:  # 15% still in draft
        app.status = ApplicationStatus.DRAFT
        app.remarks = "Customer reviewing terms before submission"

    elif status_roll < 0.35:  # 20% waiting for expert review
        app.status = ApplicationStatus.PENDING_EXPERT_REVIEW
        if experts:
            app.assigned_expert_id = random.choice(experts).id
        app.remarks = "Submitted to expert for review"
        app.updated_at = app.created_at + timedelta(hours=random.randint(2, 24))

    elif status_roll < 0.50:  # 15% at HO for approval
        app.status = ApplicationStatus.PENDING_HO_APPROVAL
        if experts:
            expert = random.choice(experts)
            app.assigned_expert_id = expert.id
            app.application_grade = random.choice(
                [
                    ApplicationGrade.HIGH,
                    ApplicationGrade.MEDIUM,
                    ApplicationGrade.MEDIUM,
                    ApplicationGrade.LOW,
                ]
            )
            app.expert_remarks = (
                f"Assessed by {expert.full_name}. Grade: {app.application_grade}"
            )
        app.updated_at = app.created_at + timedelta(days=random.randint(1, 5))

    elif status_roll < 0.70:  # 20% approved
        app.status = ApplicationStatus.APPROVED
        if experts:
            expert = random.choice(experts)
            app.assigned_expert_id = expert.id
            app.application_grade = random.choice(
                [ApplicationGrade.HIGH, ApplicationGrade.MEDIUM]
            )
            app.expert_remarks = f"Approved by expert. Grade: {app.application_grade}"
        if hos:
            ho = random.choice(hos)
            app.reviewed_by_ho_id = ho.id
            app.ho_remarks = f"Final approval by {ho.full_name}. Good credit profile."
        app.updated_at = app.created_at + timedelta(days=random.randint(3, 10))

    elif status_roll < 0.85:  # 15% rejected
        app.status = ApplicationStatus.REJECTED
        if experts:
            expert = random.choice(experts)
            app.assigned_expert_id = expert.id
            app.application_grade = ApplicationGrade.LOW
            app.expert_remarks = f"Low credit score. Grade: {app.application_grade}"
        if hos:
            ho = random.choice(hos)
            app.reviewed_by_ho_id = ho.id
            app.ho_remarks = (
                f"Rejected by {ho.full_name}. Insufficient income verification."
            )
        app.updated_at = app.created_at + timedelta(days=random.randint(2, 7))

    elif status_roll < 0.92:  # 7% returned to branch
        app.status = ApplicationStatus.RETURNED_TO_BRANCH
        if experts:
            expert = random.choice(experts)
            app.assigned_expert_id = expert.id
            app.expert_remarks = f"Returned by {expert.full_name}. Missing documents."
        app.updated_at = app.created_at + timedelta(days=random.randint(1, 3))

    else:  # 8% returned to expert
        app.status = ApplicationStatus.RETURNED_TO_EXPERT
        if experts:
            expert = random.choice(experts)
            app.assigned_expert_id = expert.id
            app.application_grade = ApplicationGrade.MEDIUM
            app.expert_remarks = f"Initial assessment by {expert.full_name}"
        if hos:
            ho = random.choice(hos)
            app.reviewed_by_ho_id = ho.id
            app.ho_remarks = (
                f"Returned by {ho.full_name}. Need re-verification of employment."
            )
        app.updated_at = app.created_at + timedelta(days=random.randint(4, 8))


def create_applications():
    """Create loan applications for all branches."""
    print("\n📝 Creating loan applications...")
    apps_created = 0

    # Get all users by branch
    all_users = User.query.all()
    users_by_branch = {}
    for user in all_users:
        if user.branch_code not in users_by_branch:
            users_by_branch[user.branch_code] = []
        users_by_branch[user.branch_code].append(user)

    # Create applications for each branch
    for branch in BRANCHES:
        branch_code = branch["code"]
        branch_users = users_by_branch.get(branch_code, [])
        branch_officers = [u for u in branch_users if u.role == Role.BRANCH_OFFICER]

        if not branch_officers:
            print(f"  ⚠️ No branch officers found for {branch_code}")
            continue

        # Generate 40-60 applications per branch
        num_apps = random.randint(40, 60)

        for i in range(num_apps):
            creator = random.choice(branch_officers)
            days_ago = random.randint(1, 180)  # Applications from last 6 months

            app = generate_realistic_application(branch_code, creator, days_ago)
            assign_workflow_status(app, branch_users)

            db.session.add(app)
            apps_created += 1

        print(f"  ✅ Created {num_apps} applications for {branch_code}")

    db.session.commit()
    print(f"\n✅ Total applications created: {apps_created}")
    return apps_created


# ============================================================================
# Main
# ============================================================================


def main():
    """Main seed function."""
    print("\n" + "=" * 70)
    print("🌱 SEED DATA - 3-TIER WORKFLOW BANKING SYSTEM")
    print("=" * 70)

    with app.app_context():
        # Clear existing data
        print("\n🗑️  Clearing existing data...")
        db.session.query(CreditCheck).delete()
        db.session.query(LoanApplication).delete()
        db.session.query(User).delete()
        db.session.commit()
        print("  ✅ Database cleared")

        # Create users
        users_count = create_users()

        # Create applications
        apps_count = create_applications()

        print("\n" + "=" * 70)
        print("✅ SEED COMPLETED")
        print("=" * 70)
        print(f"📊 Summary:")
        print(f"  - Branches: {len(BRANCHES)}")
        print(f"  - Users: {users_count}")
        print(f"  - Applications: {apps_count}")
        print(f"\n🔐 Default Password: {DEFAULT_PASSWORD}")
        print("\n📋 Sample Logins:")
        print("  - superadmin / Password123 (Global access)")
        print("  - bo_hcm01_1 / Password123 (Branch Officer - HCM01)")
        print("  - expert_hcm01_1 / Password123 (Approval Expert - HCM01)")
        print("  - ho_hcm01_1 / Password123 (Branch HO - HCM01)")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
