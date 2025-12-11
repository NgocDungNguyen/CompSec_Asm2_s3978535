"""
Check all user accounts and test login
"""

from werkzeug.security import check_password_hash

from app import app
from models import User, db

with app.app_context():
    print("\n" + "=" * 90)
    print("🔐 USER ACCOUNTS LIST - LOGIN CREDENTIALS")
    print("=" * 90)

    users = User.query.order_by(User.role, User.branch_code, User.username).all()

    print(
        f"\n{'Username':<20} {'Password':<15} {'Role':<20} {'Branch':<12} {'Full Name'}"
    )
    print("-" * 90)

    # Test password for each user
    test_password = "Password123"

    for user in users:
        # Check if password works
        password_works = check_password_hash(user.password_hash, test_password)
        pwd_display = "Password123" if password_works else "UNKNOWN"

        print(
            f"{user.username:<20} {pwd_display:<15} {user.role:<20} {user.branch_code:<12} {user.full_name}"
        )

    print("=" * 90)
    print(f"Total Users: {len(users)}")
    print("=" * 90)

    # Verify password hashing for a sample user
    print("\n🔍 Testing Login for Sample Users:")
    print("-" * 90)

    test_users = ["superadmin", "bo_hcm01_1", "expert_hcm01_1", "ho_hcm01_1"]

    for username in test_users:
        user = User.query.filter_by(username=username).first()
        if user:
            # Test with Password123
            works = check_password_hash(user.password_hash, "Password123")
            status = "✅ LOGIN WORKS" if works else "❌ LOGIN FAILED"
            print(f"{username:<20} Password123 → {status}")
        else:
            print(f"{username:<20} → ❌ USER NOT FOUND")

    print("=" * 90 + "\n")
