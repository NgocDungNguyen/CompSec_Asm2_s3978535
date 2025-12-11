"""
RMIT NeoBank Loan Origination System - Database Models

This module defines the SQLAlchemy ORM models for the banking application.
Simulates a real-world loan origination system (CAS) with:
- User management (branch officers, HO officers)
- Loan application lifecycle
- Credit bureau integration records

Educational purpose: Demonstrates proper database design for secure banking applications.
"""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ============================================================================
# Role and Status Constants
# ============================================================================


class Role:
    """
    User role definitions for the 3-tier approval workflow.

    BRANCH_OFFICER: Creates and manages loan applications for customers.
                    Can only submit to next stage. Lowest level in workflow.

    APPROVAL_EXPERT: External reviewers who assess application quality.
                     Can approve/rate applications or send back to Branch Officer.
                     Middle tier in workflow.

    BRANCH_HO: Branch Head Office - Final approver for the branch.
               Can approve, reject, or send back to Expert or Branch Officer.
               Highest tier in workflow (per branch).

    SUPER_ADMIN: System administrator with full cross-branch access.
                 Can perform any action on any application regardless of branch.

    Workflow: BRANCH_OFFICER → APPROVAL_EXPERT → BRANCH_HO → APPROVED/REJECTED
    """

    BRANCH_OFFICER = "branch_officer"
    APPROVAL_EXPERT = "approval_expert"
    BRANCH_HO = "branch_ho"
    SUPER_ADMIN = "super_admin"


class ApplicationStatus:
    """
    3-Tier Workflow Statuses:

    DRAFT: Being created by Branch Officer (not yet submitted)
    PENDING_EXPERT_REVIEW: Submitted by Branch Officer, awaiting Expert review
    PENDING_HO_APPROVAL: Approved by Expert, awaiting HO final decision
    APPROVED: Final approval by Branch HO
    REJECTED: Rejected by Branch HO
    RETURNED_TO_BRANCH: Sent back to Branch Officer for corrections
    RETURNED_TO_EXPERT: Sent back to Expert by HO for reassessment

    Workflow:
    1. Branch Officer: DRAFT → PENDING_EXPERT_REVIEW
    2. Expert: PENDING_EXPERT_REVIEW → PENDING_HO_APPROVAL (or → RETURNED_TO_BRANCH)
    3. Branch HO: PENDING_HO_APPROVAL → APPROVED/REJECTED (or → RETURNED_TO_EXPERT/RETURNED_TO_BRANCH)
    """

    DRAFT = "DRAFT"
    PENDING_EXPERT_REVIEW = "PENDING_EXPERT_REVIEW"
    PENDING_HO_APPROVAL = "PENDING_HO_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED_TO_BRANCH = "RETURNED_TO_BRANCH"
    RETURNED_TO_EXPERT = "RETURNED_TO_EXPERT"


class ApplicationGrade:
    """
    Application quality grading by Approval Experts.
    Helps Branch HO make final decision.
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CreditCheckStatus:
    """
    Credit bureau integration status tracking.
    Essential for audit trails and regulatory compliance.
    """

    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ============================================================================
# Database Models
# ============================================================================


class User(db.Model):
    """
    Banking staff user model.

    Security Design Considerations:
    - Passwords are NEVER stored in plaintext (hashed with Werkzeug's pbkdf2:sha256)
    - branch_code enables data isolation (branch officers only see their branch's data)
    - role field enables RBAC enforcement
    - is_active allows account deactivation without deletion (audit trail preservation)

    Real-world parallel: In actual banks, this would integrate with:
    - Active Directory / LDAP for SSO
    - HR systems for automatic provisioning/deprovisioning
    - Multi-factor authentication (MFA)
    - Session timeout policies
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    branch_code = db.Column(db.String(16), nullable=False, index=True)
    role = db.Column(
        db.String(32), nullable=False, default=Role.BRANCH_OFFICER, index=True
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username} ({self.role}/{self.branch_code})>"


class LoanApplication(db.Model):
    """
    Core loan application entity modeling a simplified CAS workflow.

    Business Context:
    In real banking loan origination systems (e.g., Temenos, Finastra, Oracle FLEXCUBE):
    1. Lead/Application Capture: Branch officer creates initial application
    2. Data Entry & Verification: Applicant details, loan parameters
    3. Credit Assessment: Bureau checks, internal scoring
    4. Approval Workflow: Maker-checker, limit-based approvals
    5. Disbursement: Funds transfer to customer

    Security Considerations:
    - branch_code field enables horizontal access control (IDOR prevention)
    - Foreign key to created_by ensures audit trail
    - remarks field is the INTENTIONAL XSS vulnerability point for demonstration
    - In production: PII fields (national_id, contact details) would be encrypted at rest

    Attack Surface (Educational):
    - remarks: Stored XSS if rendered without escaping
    - applicant_name: SQL Injection if used in raw queries
    - File attachments (not implemented): Path traversal, malicious uploads
    """

    __tablename__ = "loan_applications"

    id = db.Column(db.Integer, primary_key=True)
    application_ref = db.Column(db.String(32), unique=True, nullable=False, index=True)

    # Applicant Personal Information
    applicant_name = db.Column(db.String(128), nullable=False, index=True)
    national_id = db.Column(db.String(32), nullable=False)  # In production: encrypted
    dob = db.Column(db.Date, nullable=False)
    contact_phone = db.Column(db.String(32), nullable=False)
    contact_email = db.Column(db.String(128), nullable=False)

    # Loan Details
    product_code = db.Column(
        db.String(32), nullable=False
    )  # e.g., PL_SAL, HL_STD, BL_SME
    requested_amount = db.Column(db.Numeric(18, 2), nullable=False)
    tenure_months = db.Column(db.Integer, nullable=False)

    # Workflow and Access Control Fields
    branch_code = db.Column(
        db.String(16), nullable=False, index=True
    )  # CRITICAL for RBAC
    created_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    status = db.Column(
        db.String(32), nullable=False, default=ApplicationStatus.DRAFT, index=True
    )

    # 3-Tier Workflow Fields
    assigned_expert_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )  # Expert assigned when submitted by Branch Officer
    reviewed_by_ho_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )  # HO who made final decision
    application_grade = db.Column(
        db.String(16), nullable=True
    )  # HIGH, MEDIUM, LOW (assessed by Expert)
    expert_remarks = db.Column(db.Text, nullable=True)  # Expert assessment notes
    ho_remarks = db.Column(db.Text, nullable=True)  # HO decision notes

    # Free-text field - INTENTIONAL XSS VULNERABILITY POINT
    # In secure implementation: would be sanitized/escaped on output
    # In vulnerable implementation: rendered with |safe filter (demo purposes)
    remarks = db.Column(db.Text, nullable=True)

    # CIC Credit Check Integration Fields
    cic_check_status = db.Column(
        db.String(32), nullable=True, default="NOT_CHECKED"
    )  # NOT_CHECKED, PENDING, COMPLETED, FAILED
    cic_credit_score = db.Column(db.Integer, nullable=True)  # 300-900 score from CIC
    cic_risk_category = db.Column(
        db.String(16), nullable=True
    )  # LOW, MEDIUM, HIGH, SEVERE
    cic_bureau_reference = db.Column(
        db.String(128), nullable=True
    )  # CIC reference number for audit
    cic_recommendation = db.Column(db.Text, nullable=True)  # CIC lending recommendation
    cic_key_factors = db.Column(db.Text, nullable=True)  # JSON: Key score factors
    cic_checked_at = db.Column(
        db.DateTime, nullable=True
    )  # When CIC check was performed
    cic_checked_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )  # Who requested CIC check

    # Audit timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    created_by = db.relationship(
        "User", foreign_keys=[created_by_user_id], backref="applications", lazy=True
    )
    assigned_expert = db.relationship(
        "User", foreign_keys=[assigned_expert_id], lazy=True
    )
    reviewed_by_ho = db.relationship(
        "User", foreign_keys=[reviewed_by_ho_id], lazy=True
    )
    cic_checked_by = db.relationship(
        "User", foreign_keys=[cic_checked_by_user_id], lazy=True
    )

    def __repr__(self):
        return f"<LoanApplication {self.application_ref} - {self.applicant_name}>"


class CreditCheck(db.Model):
    """
    Credit bureau integration record.

    Real-world Context:
    In actual banking systems (e.g., integration with CIC, Experian, Equifax):
    - Requests are digitally signed and encrypted (HTTPS + mutual TLS)
    - Bureau responses include detailed credit history, scores, delinquencies
    - Rate limiting prevents abuse (cost per query + regulatory limits)
    - Audit logs are mandatory for regulatory compliance (Basel III, GDPR)

    Security Best Practices Demonstrated:
    - Audit trail: who requested, when, what was returned
    - Status tracking: detect hanging/failed requests
    - Response storage: enables forensic analysis if disputes arise
    - Foreign key constraints: ensure data integrity

    In production, additional security measures:
    - Request/response encryption
    - API key rotation
    - Rate limiting per user/branch
    - Anomaly detection (unusual query patterns)
    """

    __tablename__ = "credit_checks"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("loan_applications.id"), nullable=False, index=True
    )
    requested_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    status = db.Column(
        db.String(16), nullable=False, default=CreditCheckStatus.PENDING, index=True
    )

    # Bureau response fields
    bureau_reference = db.Column(
        db.String(64), nullable=True, index=True
    )  # External reference for tracking
    score = db.Column(db.Integer, nullable=True)  # Typically 300-900 range (FICO-like)
    risk_band = db.Column(db.String(16), nullable=True)  # HIGH / MEDIUM / LOW
    raw_response = db.Column(db.Text, nullable=True)  # Full XML/JSON response for audit

    # Timestamps for SLA tracking and audit
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    application = db.relationship("LoanApplication", backref="credit_checks", lazy=True)
    requested_by = db.relationship("User", lazy=True)

    def __repr__(self):
        return f"<CreditCheck app={self.application_id} bureau_ref={self.bureau_reference} score={self.score}>"
