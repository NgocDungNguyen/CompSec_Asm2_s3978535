"""
Database Initialization Script
Drops all tables and recreates them with the new schema.
Includes both CAS (Credit Application System) and CIC (Credit Information Center) models.
"""

# Import CIC models to ensure they're registered with SQLAlchemy
import cic_models
from app import app, db

print("=" * 70)
print("🗄️  DATABASE INITIALIZATION (CAS + CIC)")
print("=" * 70)

with app.app_context():
    print("\n🗑️  Dropping all existing tables...")
    db.drop_all()
    print("  ✅ All tables dropped")

    print("\n🔧 Creating tables with new schema...")
    print("  📋 CAS tables (Users, LoanApplications, CreditChecks)")
    print(
        "  📋 CIC tables (Customers, Accounts, PaymentHistory, Assets, Inquiries, etc.)"
    )
    db.create_all()
    print("  ✅ All tables created")

print("\n✅ Database initialization complete!")
print("=" * 70)
print("\n💡 Next steps:")
print("  1️⃣  Run 'python seed_data_new.py' to populate CAS data (users + applications)")
print("  2️⃣  Run 'python seed_cic_data.py' to populate CIC data (credit profiles)")
print("=" * 70 + "\n")
