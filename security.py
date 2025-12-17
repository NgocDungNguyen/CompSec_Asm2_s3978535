"""
RMIT NeoBank - Security Module

This module implements core security controls for the banking application:
1. Password hashing (defense against credential theft)
2. Session management (authentication state tracking)
3. Role-Based Access Control (RBAC) decorators
4. Access control enforcement (IDOR prevention)

Educational Focus:
Demonstrates defense-in-depth security architecture where multiple layers
of security controls work together to protect against OWASP Top 10 threats.

Security Architecture Alignment:
- OWASP A01:2021 Broken Access Control → role_required decorator
- OWASP A02:2021 Cryptographic Failures → password hashing
- OWASP A07:2021 Identification and Authentication Failures → login_required
"""

from functools import wraps

from flask import flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import Role, User, db

# ============================================================================
# Password Security (Defense against A02:2021 - Cryptographic Failures)
# ============================================================================


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using Werkzeug's secure hashing.

    Technical Details:
    - Uses PBKDF2-SHA256 by default (Werkzeug 3.x)
    - Salt is automatically generated and embedded in hash
    - Computational cost makes brute-force attacks infeasible

    Security Note:
    NEVER store passwords in plaintext or use weak hashing (MD5, SHA1).
    Real banking systems often use:
    - Bcrypt or Argon2 (stronger than PBKDF2)
    - Hardware Security Modules (HSMs) for key management
    - Regular password rotation policies

    Args:
        plain_password: User's plaintext password

    Returns:
        Hashed password string (includes salt and algorithm metadata)
    """
    return generate_password_hash(plain_password, method="pbkdf2:sha256")


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify a plaintext password against its stored hash.

    Security Feature: Constant-time comparison prevents timing attacks
    where attackers could determine password length or character matches
    based on response times.

    Args:
        plain_password: User-provided password to verify
        stored_hash: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return check_password_hash(stored_hash, plain_password)


# ============================================================================
# Session Management (Defense against A07:2021 - Auth Failures)
# ============================================================================


def get_current_user():
    """
    Retrieve the currently logged-in User object from session.

    Security Design:
    - Uses Flask's signed session cookies (tamper-proof)
    - Only stores user_id in session (minimal sensitive data exposure)
    - Database lookup ensures fresh data (detects disabled accounts)

    Production Enhancements:
    - Add session timeout (e.g., 15 minutes idle, 8 hours absolute)
    - Implement CSRF tokens for state-changing operations
    - Add IP address validation (detect session hijacking)
    - Log all session activities for audit trail

    Returns:
        User object if authenticated, None otherwise
    """
    user_id = session.get("user_id")
    if not user_id:
        return None

    # Fetch from database to ensure account is still active
    user = db.session.get(User, user_id)

    # Additional security check: ensure account is active
    if user and not user.is_active:
        logout_user()  # Force logout if account was deactivated
        return None

    return user


def login_user(user: User):
    """
    Establish an authenticated session for a user.

    Security Best Practice:
    - Regenerate session ID on login (prevents session fixation attacks)
    - Store minimal data in session (only what's needed for access control)
    - Set session flags: HttpOnly, Secure, SameSite (in production)

    Real Banking Systems Also:
    - Log login attempts (successful and failed)
    - Check for concurrent sessions (limit or alert)
    - Require MFA for privileged roles (HO_OFFICER, ADMIN)
    - Record login IP, device fingerprint

    Args:
        user: User object to authenticate
    """
    # Flask's session is signed with SECRET_KEY, preventing tampering
    session.clear()  # Clear any previous session data

    # ============================================================
    # SECURE ENHANCEMENT (Uncomment to enable protection):
    # ============================================================
    # # Regenerate session ID to prevent session fixation
    # # Flask 3.0+ provides session.regenerate() method
    # try:
    #     session.regenerate()  # New session ID issued
    # except AttributeError:
    #     # Fallback for older Flask versions
    #     session.modified = True
    #
    # Defense Mechanism:
    # - Prevents session fixation attacks (CWE-384)
    # - Attacker cannot predict/set victim's session ID
    # - Combined with HttpOnly, Secure, SameSite flags (app.py lines 87-89)
    # - OWASP: Session Management best practice
    # ============================================================

    session["user_id"] = user.id
    session["role"] = user.role
    session["branch_code"] = user.branch_code
    session["full_name"] = user.full_name

    # In production: also set session.permanent = True with PERMANENT_SESSION_LIFETIME
    # Update last login timestamp (audit trail)
    from datetime import datetime

    user.last_login = datetime.utcnow()
    db.session.commit()


def logout_user():
    """
    Terminate the current user's session.

    Security: Clears all session data to prevent unauthorized access
    via abandoned sessions.

    Production Enhancement:
    - Invalidate session on server side (store active sessions in Redis)
    - Log logout events (distinguish user-initiated vs timeout vs forced)
    """
    session.clear()


# ============================================================================
# Access Control Decorators (Defense against A01:2021 - Broken Access Control)
# ============================================================================


def login_required(fn):
    """
    Decorator to enforce authentication on protected routes.

    Usage:
        @app.route("/dashboard")
        @login_required
        def dashboard():
            return render_template("dashboard.html")

    Security Design:
    - Implements "deny by default" principle
    - Redirects unauthenticated users to login page
    - Preserves original URL for post-login redirect (in production)

    OWASP Alignment:
    - A07:2021 Identification and Authentication Failures
    - Prevents anonymous access to business functionality

    Args:
        fn: The route function to protect

    Returns:
        Wrapped function that checks authentication first
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Authentication required. Please log in to continue.", "warning")
            # In production: save request.url to session, redirect after login
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    """
    Decorator to enforce Role-Based Access Control (RBAC).

    Usage:
        @app.route("/ho-dashboard")
        @login_required
        @role_required(Role.HO_OFFICER, Role.ADMIN)
        def ho_dashboard():
            return render_template("ho_dashboard.html")

    Security Architecture:
    This implements the PRINCIPLE OF LEAST PRIVILEGE where users can only
    access resources necessary for their job function.

    Real Banking Context:
    - Branch officers: only their branch's applications
    - HO officers: all branches, credit checks, approvals
    - Admin: user management, system configuration

    STRIDE Threat Mitigation:
    - Spoofing: Combined with authentication (login_required)
    - Tampering: Prevents unauthorized data modification
    - Repudiation: Audit logs record who accessed what
    - Information Disclosure: Prevents data leaks across branches
    - Elevation of Privilege: Blocks privilege escalation attempts

    OWASP Alignment:
    - A01:2021 Broken Access Control
    - Defense in depth: role check + data-level filtering (see branch checks)

    Args:
        allowed_roles: Variable number of Role constants

    Returns:
        Decorator function that checks user's role
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash("Authentication required.", "warning")
                return redirect(url_for("login"))

            if user.role not in allowed_roles:
                # SECURITY EVENT: Log this as potential privilege escalation attempt
                flash(
                    f"Access Denied: Your role ({user.role}) is not authorized for this resource. "
                    f"Required roles: {', '.join(allowed_roles)}",
                    "danger",
                )
                # In production: log this event with full context
                # logger.warning(f"Unauthorized access attempt by {user.username} to {request.path}")
                return redirect(url_for("dashboard"))

            return fn(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Data-Level Access Control Helpers
# ============================================================================


def can_access_application(user: User, application) -> bool:
    """
    Check if a user can access a specific loan application.

    Implements horizontal access control (prevents IDOR attacks).

    Business Rules:
    - Branch officers: only their branch's applications
    - HO officers and Admin: all applications

    Security Note: This is the SECOND layer of defense.
    First layer: @role_required decorator ensures proper role.
    Second layer: This function ensures data-level authorization.

    IDOR (Insecure Direct Object Reference) Prevention:
    Without this check, a branch officer could access another branch's
    application by manipulating the URL: /applications/123 -> /applications/124

    Real-world Regulatory Impact:
    - Privacy violation (GDPR, CCPA)
    - Insider fraud risk
    - Regulatory penalties (fines, license revocation)

    Args:
        user: Current User object
        application: LoanApplication object to check access for

    Returns:
        True if user can access the application, False otherwise
    """
    # SUPER_ADMIN has global access to all applications
    if user.role == Role.SUPER_ADMIN:
        return True

    # Branch HO: only their branch
    if user.role == Role.BRANCH_HO:
        return application.branch_code == user.branch_code

    # Approval Expert: only applications assigned to them OR in their branch
    if user.role == Role.APPROVAL_EXPERT:
        return (
            application.branch_code == user.branch_code
            or application.assigned_expert_id == user.id
        )

    # Branch officers: only their branch
    if user.role == Role.BRANCH_OFFICER:
        return application.branch_code == user.branch_code

    # Default deny
    return False


def get_accessible_applications_query(user: User):
    """
    Return a SQLAlchemy query filtered by user's access rights.

    Defense in Depth Pattern:
    Instead of fetching all applications and filtering in Python,
    this applies the filter at the database level, which is:
    1. More efficient (database indexes)
    2. More secure (no accidental exposure if filter is forgotten)
    3. Auditable (database query logs)

    Usage:
        query = get_accessible_applications_query(current_user)
        applications = query.filter(LoanApplication.status == "PENDING").all()

    Args:
        user: Current User object

    Returns:
        SQLAlchemy query object pre-filtered for user's access
    """
    from models import LoanApplication

    query = LoanApplication.query

    # SUPER_ADMIN sees all applications across all branches
    if user.role == Role.SUPER_ADMIN:
        return query  # No filter

    # Branch HO: only their branch (can approve/reject)
    if user.role == Role.BRANCH_HO:
        query = query.filter(LoanApplication.branch_code == user.branch_code)

    # Approval Expert: only their branch (handles expert review stage)
    elif user.role == Role.APPROVAL_EXPERT:
        query = query.filter(LoanApplication.branch_code == user.branch_code)

    # Branch Officer: only their branch (creates and manages)
    elif user.role == Role.BRANCH_OFFICER:
        query = query.filter(LoanApplication.branch_code == user.branch_code)

    return query


# ============================================================================
# Input Validation Helpers (Defense against Injection Attacks)
# ============================================================================


def sanitize_search_input(search_term: str) -> str:
    """
    Sanitize user input for search functionality.

    Security Note:
    While parameterized queries (SQLAlchemy ORM) protect against SQL injection,
    it's still good practice to validate and sanitize inputs at the application layer.

    Defense in Depth: Multiple layers of protection.

    Args:
        search_term: User-provided search string

    Returns:
        Sanitized search term
    """
    if not search_term:
        return ""

    # Remove leading/trailing whitespace
    cleaned = search_term.strip()

    # Limit length to prevent DoS via extremely long search terms
    max_length = 100
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    # In production: could also strip special characters, HTML tags, etc.
    # For database search, ORM parameterization is the PRIMARY defense.

    return cleaned
