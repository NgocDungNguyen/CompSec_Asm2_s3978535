# 🏦 RMIT NeoBank - Loan Origination System (CAS)

**Industry**: Banking & Financial Services
**Purpose**: Cybersecurity Education & Penetration Testing Practice
**Status**: ✅ All 5 Vulnerabilities Verified Working
**Last Updated**: December 16, 2025

---

## 📖 Table of Contents

1. [System Overview](#-system-overview)
2. [Banking Workflow &amp; Processes](#-banking-workflow--processes)
3. [User Roles &amp; Permissions](#-user-roles--permissions)
4. [Security Vulnerabilities](#-security-vulnerabilities)
5. [Quick Start Guide](#-quick-start-guide)
6. [Attack Demonstration](#-attack-demonstration)
7. [Technical Architecture](#-technical-architecture)

---

## 🎯 System Overview

**RMIT NeoBank CAS (Credit Application System)** is a simulated banking loan origination platform that demonstrates both secure and vulnerable coding practices. It replicates real-world banking workflows including:

- **Loan Application Management**: Customer loan requests from initial submission to final approval
- **3-Tier Approval Workflow**: Branch Officer → Credit Expert → Head Office approval chain
- **Credit Bureau Integration**: Mock CIC (Credit Information Center) credit checks
- **Role-Based Access Control**: Branch-level data isolation with hierarchical permissions
- **Audit Trail**: Complete tracking of who did what and when

### **Educational Purpose**

This application contains **5 intentionally implemented security vulnerabilities** that exist in real-world banking systems. It serves as a hands-on learning platform for:

1. ✅ Understanding attack vectors (SQL Injection, IDOR, XSS, Command Injection, Session Hijacking)
2. ✅ Penetration testing techniques
3. ✅ Secure coding practices and remediation strategies
4. ✅ OWASP Top 10 vulnerability analysis

### **Why Banking Domain?**

Banking applications are **critical infrastructure** with:

- High-value targets (financial data, customer PII)
- Strict regulatory requirements (PCI DSS, GDPR, Basel III)
- Complex workflows requiring multiple security layers
- Real-world consequences of security breaches (fraud, identity theft, regulatory fines)

---

## 🏦 Banking Workflow & Processes

### **Loan Origination Lifecycle**

RMIT NeoBank implements a simplified 3-tier loan approval workflow mirroring real banking operations:

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOAN APPLICATION LIFECYCLE                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  1. CUSTOMER │  → Visits branch with loan request
│   INQUIRY    │     (Personal Loan, Home Loan, Business Loan)
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│  2. DATA CAPTURE    │  → Branch Officer creates application
│  (Branch Officer)   │     - Customer PII (Name, National ID, DOB)
│                     │     - Loan details (Amount, Tenure, Purpose)
│  Status: DRAFT      │     - Contact information
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  3. SUBMISSION      │  → Submit to Credit Expert for review
│  (Branch Officer)   │   
│                     │  → System validates required fields
│  Status: PENDING    │  → Assigns to available Credit Expert
│  EXPERT_REVIEW      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  4. CREDIT CHECK    │  → Credit Expert requests CIC report
│  (Credit Expert)    │     - Credit score analysis
│                     │     - Payment history review
│  CIC Integration    │     - Existing debt evaluation
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  5. EXPERT REVIEW   │  → Credit Expert evaluates application
│  (Credit Expert)    │     - Grades: HIGH / MEDIUM / LOW
│                     │     - Can approve or return to Branch
│  Decision:          │
│  ✓ Forward to HO    │
│  ✗ Return to Branch │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  6. HO APPROVAL     │  → Branch Head Office final decision
│  (Branch HO)        │     - Reviews Expert assessment
│                     │     - Checks credit score & risk
│  Final Decision:    │     - Authority: Approve/Reject
│  ✓ APPROVED         │
│  ✗ REJECTED         │  → Can also return to Expert/Branch
│  ↩ RETURNED         │
└─────────────────────┘
```

### **Key Business Processes**

#### **A. Application Creation (Branch Officer)**

1. Customer walks into branch
2. Officer logs into CAS system
3. Creates new application (Status: DRAFT)
4. Fills customer details and loan parameters
5. Submits for expert review (Status: PENDING_EXPERT_REVIEW)

#### **B. Credit Assessment (Credit Expert)**

1. Receives application from queue
2. Reviews customer information
3. Requests CIC credit bureau check
4. Analyzes credit score (300-850 scale)
5. Reviews payment history and existing debts
6. Grades application (HIGH/MEDIUM/LOW)
7. Forwards to HO or returns to Branch

#### **C. Final Approval (Branch Head Office)**

1. Reviews Expert's assessment and grade
2. Checks credit score meets policy threshold
3. Makes final decision:
   - **APPROVED**: Loan proceeds to disbursement
   - **REJECTED**: Customer notified of decline
   - **RETURNED**: Sent back for more information

#### **D. Cross-Branch Operations (Super Admin)**

1. System-wide monitoring
2. User account management
3. Cross-branch reporting and analytics
4. Audit trail investigation

---

## 👥 User Roles & Permissions

### **Role Hierarchy & Capabilities**

```
        ┌─────────────────────┐
        │   SUPER ADMIN       │  Full system access
        │   (System-wide)     │  All branches, all actions
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼─────────┐   ┌──────▼──────────┐
│  BRANCH HO      │   │  BRANCH HO      │
│  (HCM Branch)   │   │  (HN Branch)    │  Final approvers per branch
│                 │   │                 │  Cross-branch data isolated
└───────┬─────────┘   └──────┬──────────┘
        │                    │
        ▼                    ▼
┌─────────────────┐   ┌─────────────────┐
│ CREDIT EXPERT   │   │ CREDIT EXPERT   │
│ (HCM Branch)    │   │ (HN Branch)     │  Credit assessment specialists
└───────┬─────────┘   └──────┬──────────┘
        │                    │
        ▼                    ▼
┌─────────────────┐   ┌─────────────────┐
│ BRANCH OFFICER  │   │ BRANCH OFFICER  │
│ (HCM Branch)    │   │ (HN Branch)     │  Front-line application creators
└─────────────────┘   └─────────────────┘
```

### **Detailed Role Permissions**

#### **1. Branch Officer** (`branch_officer`)

**Job Function**: Customer-facing loan application processing

**Can Do**:

- ✅ Create new loan applications
- ✅ View applications from THEIR branch only
- ✅ Edit DRAFT applications
- ✅ Submit applications to Credit Expert
- ✅ Update customer information
- ✅ Add remarks/notes to applications

**Cannot Do**:

- ❌ View other branch applications (IDOR protection)
- ❌ Perform credit bureau checks
- ❌ Approve or reject applications
- ❌ Change application status beyond submission
- ❌ Access system administration

**Example Users**: `bo_hcm01_1`, `bo_hn01_1`, `bo_dn01_1`

---

#### **2. Credit Expert / Approval Expert** (`approval_expert`)

**Job Function**: Credit risk assessment and application evaluation

**Can Do**:

- ✅ View applications from THEIR branch
- ✅ Request CIC credit bureau reports
- ✅ Review credit scores and payment history
- ✅ Grade applications (HIGH/MEDIUM/LOW)
- ✅ Forward applications to Branch HO
- ✅ Return applications to Branch Officer for corrections
- ✅ Add credit assessment comments

**Cannot Do**:

- ❌ Create new applications
- ❌ Make final approval/rejection decisions
- ❌ View other branch applications
- ❌ Modify loan amounts or terms
- ❌ Access bulk import functions

**Example Users**: `expert_hcm01_1`, `expert_hn01_1`

---

#### **3. Branch Head Office** (`branch_ho`)

**Job Function**: Final loan approval authority for branch

**Can Do**:

- ✅ View ALL applications from THEIR branch
- ✅ Make final APPROVED/REJECTED decisions
- ✅ Return applications to Expert or Branch Officer
- ✅ Override Expert grades (if justified)
- ✅ Access bulk import functionality
- ✅ Generate branch-level reports
- ✅ View complete audit trails

**Cannot Do**:

- ❌ View other branch applications
- ❌ Modify approved applications
- ❌ Delete applications (audit trail preservation)
- ❌ System-wide administration

**Example Users**: `ho_hcm01_1`, `ho_hn01_1`

---

#### **4. Super Admin** (`super_admin`)

**Job Function**: System administrator with global access

**Can Do**:

- ✅ View ALL applications across ALL branches
- ✅ Create/modify/deactivate user accounts
- ✅ Access all system functions
- ✅ Generate cross-branch reports
- ✅ Investigate security incidents
- ✅ System configuration and maintenance

**Responsibilities**:

- Monitor system integrity
- Enforce security policies
- Conduct audit reviews
- Handle escalations

**Example Users**: `admin_system`

---

### **Branch Structure**

The system supports **9 branches** across Vietnam:

| Branch Code     | Location    | Full Name          | Staff Count |
| --------------- | ----------- | ------------------ | ----------- |
| **HCM01** | Ho Chi Minh | District 1 Branch  | 12 staff    |
| **HCM02** | Ho Chi Minh | District 7 Branch  | 8 staff     |
| **HN01**  | Hanoi       | Hoan Kiem Branch   | 10 staff    |
| **HN02**  | Hanoi       | Cau Giay Branch    | 8 staff     |
| **DN01**  | Da Nang     | Hai Chau Branch    | 8 staff     |
| **DN02**  | Da Nang     | Son Tra Branch     | 6 staff     |
| **CT01**  | Can Tho     | Ninh Kieu Branch   | 5 staff     |
| **HP01**  | Hai Phong   | Hong Bang Branch   | 3 staff     |
| **BD01**  | Binh Duong  | Thu Dau Mot Branch | 2 staff     |

**Total**: 62 user accounts, 457 loan applications

---

## 🔓 Security Vulnerabilities

This application contains **5 intentional security vulnerabilities** for educational purposes:

### **Critical Vulnerabilities (Demoable)**

| # | Vulnerability               | CWE     | CVSS | Location                  | Impact                                  |
| - | --------------------------- | ------- | ---- | ------------------------- | --------------------------------------- |
| 1 | **SQL Injection**     | CWE-89  | 9.8  | `/applications?q=`      | Database breach, credential theft       |
| 2 | **IDOR**              | CWE-639 | 7.5  | `/applications/<id>`    | Unauthorized data access, PII exposure  |
| 3 | **Stored XSS**        | CWE-79  | 6.1  | Application remarks field | Session hijacking, malware distribution |
| 4 | **Command Injection** | CWE-78  | 9.8  | `/import` filename      | Remote code execution, server takeover  |
| 5 | **Session Hijacking** | CWE-384 | 8.1  | Session cookies           | Account takeover, identity theft        |

### **Quick Attack Summary**

1. **SQL Injection**: Enter `' OR 1=1 --` in search → See all 457 applications
2. **IDOR**: Change URL `/applications/123` to `/applications/1` → Access forbidden data
3. **XSS**: Submit `<script>alert('XSS')</script>` in remarks → JavaScript executes
4. **Command Injection**: Enter `data.csv & whoami` → Detection alert proves vulnerability
5. **Session Hijacking**: Steal cookie via DevTools → Login in incognito without password

**👉 Full attack demonstrations**: See [`DETAILED_ATTACK_DEMO_GUIDE.md`](DETAILED_ATTACK_DEMO_GUIDE.md)

---

## �️ Defense Mechanisms & Prevention

### **Overview: How to Protect Against Each Attack**

Each vulnerability has a **secure alternative** commented in the code. This section explains the defense mechanisms in detail.

---

### **1. SQL Injection Defense (CWE-89)**

#### **The Vulnerability**
- **Location**: [app.py](app.py#L388-L400) - `/applications` search endpoint
- **Issue**: Direct SQL string concatenation with user input
- **Vulnerable Code**:
  ```python
  raw_sql = f"SELECT * FROM loan_applications WHERE applicant_name LIKE '%{search_query}%'"
  db.session.execute(text(raw_sql))
  ```

#### **Defense Strategy**

**✅ Primary Defense: Parameterized Queries (ORM)**
```python
# SECURE: Use SQLAlchemy ORM with parameterized queries
query = LoanApplication.query.filter(
    db.or_(
        LoanApplication.applicant_name.ilike(f"%{search_query}%"),
        LoanApplication.application_ref.ilike(f"%{search_query}%"),
        LoanApplication.national_id.ilike(f"%{search_query}%")
    )
)
```

**Why This Works**:
- SQLAlchemy automatically escapes special characters
- Query parameters treated as data, not executable SQL
- No way for attacker to "break out" of the query structure

**✅ Secondary Defense: Input Validation**
```python
from security import sanitize_search_input

# Whitelist allowed characters
search_query = sanitize_search_input(request.args.get("q", ""))
if not re.match(r'^[a-zA-Z0-9\s-]+$', search_query):
    abort(400, "Invalid search query")
```

**✅ Tertiary Defense: Least Privilege**
- Database user should have SELECT-only permissions
- No CREATE, DROP, or GRANT privileges
- Separate read/write database accounts

#### **OWASP Best Practices**
- ✅ Use prepared statements with variable binding (Parameterized Queries)
- ✅ Use stored procedures (for complex queries)
- ✅ Whitelist input validation
- ✅ Escape all user-supplied input
- ✅ Enforce least privilege on database accounts

**Banking-Specific Considerations**:
- PCI DSS Requirement 6.5.1: Protect against injection flaws
- Data breach can expose customer PII (National ID, loan amounts)
- Regulatory fines: GDPR €20M or 4% annual revenue

---

### **2. IDOR Defense (CWE-639)**

#### **The Vulnerability**
- **Location**: [app.py](app.py#L558) - `/applications/<id>` detail endpoint
- **Issue**: No authorization check after authentication
- **Vulnerable Code**:
  ```python
  application = LoanApplication.query.get_or_404(app_id)
  # Missing: if not can_access_application(user, application): abort(403)
  return render_template("application_detail.html", application=application)
  ```

#### **Defense Strategy**

**✅ Primary Defense: Authorization Check**
```python
from security import can_access_application

application = LoanApplication.query.get_or_404(app_id)

# Check if user can access this application
if not can_access_application(get_current_user(), application):
    flash("Access Denied: You don't have permission to view this application.", "danger")
    return redirect(url_for("list_applications"))

return render_template("application_detail.html", application=application)
```

**Implementation Details** ([security.py lines 272-330](security.py#L272-L330)):
```python
def can_access_application(user: User, application: LoanApplication) -> bool:
    # SUPER_ADMIN can access everything
    if user.role == Role.SUPER_ADMIN:
        return True
    
    # Branch-level isolation: user can only access their branch
    if user.branch_code != application.branch_code:
        return False
    
    # Role-based restrictions
    if user.role == Role.BRANCH_OFFICER:
        # Can only access applications they created
        return application.created_by_user_id == user.id
    
    return True  # APPROVAL_EXPERT and BRANCH_HO can access all in branch
```

**✅ Secondary Defense: Indirect Object References**
```python
# Instead of exposing database IDs, use UUIDs or hashed references
application.public_id = generate_uuid()  # e.g., "a3f2e1c0-7b4a-4d2e-8c3f-9a1b2c3d4e5f"

# URL becomes: /applications/a3f2e1c0-7b4a-4d2e-8c3f-9a1b2c3d4e5f
# Harder to enumerate/guess
```

**✅ Tertiary Defense: Access Control Lists (ACL)**
```python
# Store explicit permissions in database
class ApplicationPermission(db.Model):
    application_id = db.Column(db.Integer, db.ForeignKey('loan_applications.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    permission = db.Column(db.String(20))  # 'read', 'write', 'approve'
```

#### **OWASP Best Practices**
- ✅ Deny by default: Require explicit authorization for every object access
- ✅ Check authorization on server-side (never trust client-side checks)
- ✅ Use indirect reference maps (UUID instead of sequential IDs)
- ✅ Implement access control checks at the business logic layer
- ✅ Log unauthorized access attempts for monitoring

**Banking-Specific Considerations**:
- Branch data isolation required by banking regulations
- Audit trail: Log who accessed which applications (compliance)
- Customer privacy: PCI DSS requires access controls on cardholder data

---

### **3. XSS Defense (CWE-79)**

#### **The Vulnerability**
- **Location**: [templates/application_detail.html line 138](templates/application_detail.html#L138)
- **Issue**: Using `| safe` filter disables Jinja2 auto-escaping
- **Vulnerable Code**:
  ```django-html
  {{ application.remarks | safe }}
  ```

#### **Defense Strategy**

**✅ Primary Defense: Output Encoding (Auto-Escaping)**
```django-html
<!-- SECURE: Remove | safe filter, let Jinja2 auto-escape -->
{{ application.remarks }}

<!-- Jinja2 automatically converts:
     < to &lt;
     > to &gt;
     & to &amp;
     " to &quot;
     ' to &#x27;
-->
```

**✅ Secondary Defense: Input Sanitization**
```python
from bleach import clean

# Server-side: Strip HTML tags before saving
application.remarks = clean(
    request.form.get("remarks"),
    tags=[],  # No HTML tags allowed
    strip=True
)
```

**✅ Tertiary Defense: Content Security Policy (CSP)**
```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self'; "  # Block inline scripts
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:;"
    )
    return response
```

**✅ Quaternary Defense: HTTPOnly Cookies**
```python
# Prevent JavaScript from accessing session cookies
app.config["SESSION_COOKIE_HTTPONLY"] = True
# Even if XSS exists, attacker can't steal session cookie
```

#### **OWASP Best Practices**
- ✅ Output encoding for all user-controlled data in HTML context
- ✅ Use framework escaping (Jinja2, React, Angular auto-escape)
- ✅ Sanitize HTML input (if rich text required, use libraries like Bleach)
- ✅ Implement Content Security Policy (CSP) headers
- ✅ Enable HTTPOnly and Secure flags on cookies

**Banking-Specific Considerations**:
- XSS can steal customer PII displayed in browser
- Session hijacking → unauthorized fund transfers
- Malware distribution to bank customers (phishing)

---

### **4. Command Injection Defense (CWE-78)**

#### **The Vulnerability**
- **Location**: [app.py line 1151](app.py#L1151) - `/import` bulk import
- **Issue**: Building shell command with unsanitized user input
- **Vulnerable Code**:
  ```python
  command = f"python scripts/import_applications.py {filename}"
  os.system(command)  # Attacker can inject: data.csv & whoami
  ```

#### **Defense Strategy**

**✅ Primary Defense: Avoid Shell Commands Entirely**
```python
# SECURE: Use Python libraries instead of shell commands
import csv

file = request.files.get('csv_file')
filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
file.save(filepath)

# Parse CSV directly in Python (no shell)
with open(filepath, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        application = LoanApplication(
            applicant_name=row['name'],
            national_id=row['national_id'],
            # ... map CSV columns to model
        )
        db.session.add(application)
    db.session.commit()
```

**Full secure implementation**: [app.py lines 1187-1350](app.py#L1187-L1350) `/secure/import` endpoint

**✅ Secondary Defense: Input Validation (Whitelist)**
```python
import re
from werkzeug.utils import secure_filename

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Sanitize filename
filename = secure_filename(file.filename)  # Removes path traversal, special chars

# Reject if contains shell metacharacters
if re.search(r'[;&|`$()<>]', filename):
    abort(400, "Invalid filename")
```

**✅ Tertiary Defense: Use subprocess with list arguments**
```python
# If shell command absolutely necessary, use subprocess with list
import subprocess

# WRONG (Vulnerable):
os.system(f"python script.py {user_input}")

# RIGHT (Secure):
subprocess.run(
    ["python", "script.py", user_input],  # List = No shell interpretation
    shell=False,  # CRITICAL: shell=False
    check=True,
    capture_output=True
)
```

#### **OWASP Best Practices**
- ✅ Avoid calling OS commands with user input
- ✅ Use language APIs instead of shell commands (csv module, not `cat file | python`)
- ✅ Input validation: whitelist allowed values
- ✅ Escape shell arguments if command execution unavoidable
- ✅ Run with least privilege (non-root user, restricted permissions)

**Banking-Specific Considerations**:
- Command injection = full server compromise
- Attacker can access customer database, encryption keys
- Compliance: PCI DSS 6.5.1 requires protection against injection

---

### **5. Session Hijacking Defense (CWE-384)**

#### **The Vulnerability**
- **Location**: [app.py lines 87-89](app.py#L87-L89) - Session configuration
- **Issue**: Missing session security flags, no session regeneration
- **Vulnerable Code**:
  ```python
  # COMMENTED OUT (Vulnerable in development):
  # app.config["SESSION_COOKIE_SECURE"] = True
  # app.config["SESSION_COOKIE_HTTPONLY"] = True
  # app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
  ```

#### **Defense Strategy**

**✅ Primary Defense: Secure Session Configuration**
```python
# app.py - Uncomment lines 87-89:
app.config["SESSION_COOKIE_SECURE"] = True      # HTTPS only (prevents MITM)
app.config["SESSION_COOKIE_HTTPONLY"] = True    # No JavaScript access (XSS protection)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"   # CSRF protection
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)  # Auto-logout
```

**Flag Explanations**:
- **Secure**: Cookie only sent over HTTPS (encrypted connection)
- **HttpOnly**: JavaScript cannot read cookie (blocks XSS cookie theft)
- **SameSite**: Cookie not sent on cross-site requests (CSRF protection)

**✅ Secondary Defense: Session Regeneration**
```python
# security.py - Add to login_user() function:
from flask import session

def login_user(user: User):
    session.clear()  # Clear old session data
    
    # Regenerate session ID (prevents session fixation)
    try:
        session.regenerate()  # Flask 3.0+
    except AttributeError:
        session.modified = True  # Fallback
    
    session["user_id"] = user.id
    session["role"] = user.role
    # ...
```

**Why This Works**:
- Attacker cannot predict new session ID
- Even if attacker sets session ID before login, it changes after authentication

**✅ Tertiary Defense: IP Address Binding**
```python
# Store IP address with session
def login_user(user: User):
    session["user_id"] = user.id
    session["ip_address"] = request.remote_addr  # Store IP
    
# Validate IP on every request
@app.before_request
def check_session_ip():
    if "user_id" in session:
        if session.get("ip_address") != request.remote_addr:
            session.clear()  # IP mismatch = possible hijack
            flash("Session terminated: IP address changed", "warning")
            return redirect(url_for("login"))
```

**✅ Quaternary Defense: Session Timeout**
```python
from datetime import datetime, timedelta

session.permanent = True  # Enable timeout
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# Server-side timeout tracking
def login_user(user: User):
    session["login_time"] = datetime.utcnow().isoformat()
    
@app.before_request
def check_session_timeout():
    if "login_time" in session:
        login_time = datetime.fromisoformat(session["login_time"])
        if datetime.utcnow() - login_time > timedelta(minutes=30):
            logout_user()
            flash("Session expired. Please login again.", "warning")
            return redirect(url_for("login"))
```

#### **OWASP Best Practices**
- ✅ Use secure session management (HttpOnly, Secure, SameSite flags)
- ✅ Regenerate session ID after authentication
- ✅ Implement session timeout and idle timeout
- ✅ Use strong session ID generation (128+ bits entropy)
- ✅ Store sessions server-side, not client-side (use Redis/database)
- ✅ Bind sessions to IP address and User-Agent (optional, can break mobile)

**Banking-Specific Considerations**:
- Session hijacking = unauthorized access to customer accounts
- Regulatory: PCI DSS 8.2.3 requires MFA for remote access
- High-value transactions should require re-authentication
- Implement concurrent session limits (max 2 devices)

---

### **Defense-in-Depth Summary**

This application demonstrates **layered security** - if one control fails, others provide backup:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Network Security (Production)                 │
│  - HTTPS/TLS 1.3, WAF, DDoS protection                  │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Authentication & Session                      │
│  - Strong passwords, session timeout, HttpOnly cookies  │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Authorization (RBAC)                          │
│  - Role checks, branch isolation, IDOR prevention       │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Input Validation                              │
│  - Parameterized queries, filename sanitization         │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 5: Output Encoding                               │
│  - Auto-escaping, CSP headers, Content-Type validation  │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 6: Monitoring & Logging                          │
│  - Audit trails, intrusion detection, alerting          │
└─────────────────────────────────────────────────────────┘
```

**Banking Industry Standards**:
- **PCI DSS**: Payment Card Industry Data Security Standard (12 requirements)
- **ISO 27001**: Information security management
- **FFIEC**: Federal Financial Institutions Examination Council guidelines
- **GDPR**: EU privacy regulation (if serving European customers)

**Cost of Breach**:
- Average banking data breach: $5.85 million (IBM 2023)
- Regulatory fines: Up to €20M or 4% annual revenue (GDPR)
- Reputational damage: Customer trust loss, stock price impact

---

## �🚀 Quick Start Guide

### **Prerequisites**

- **Python**: 3.10 or higher
- **Operating System**: Windows 10/11 (PowerShell)
- **Browser**: Chrome, Firefox, or Edge
- **Tools**: Git (optional)

### **Installation Steps**

#### **1. Navigate to Project Directory**

```powershell
cd C:\Users\LucyS\CyberComp_Asm2
```

#### **2. Activate Virtual Environment** (if not already activated)

```powershell
# Windows PowerShell
venv\Scripts\Activate.ps1

# Or Command Prompt
venv\Scripts\activate.bat
```

#### **3. Install Dependencies** (First time only)

```powershell
pip install -r requirements.txt
```

**Required packages**:

- Flask (web framework)
- Flask-SQLAlchemy (database ORM)
- Werkzeug (security utilities)
- Requests (HTTP testing)
- BeautifulSoup4 (HTML parsing for tests)

#### **4. Initialize Database** (If not exists)

```powershell
python init_db.py
python seed_data_new.py
```

This creates:

- `instance/neobank_cas.db` (SQLite database)
- 62 user accounts
- 457 sample loan applications
- 9 branches

---

### **Running the Application**

#### **Start Flask Server**

```powershell
# Terminal 1: Start the application
python app.py
```

**Expected Output**:

```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in production deployment.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

#### **Access the Application**

1. Open browser: `http://127.0.0.1:5000`
2. Login with test account:
   - **Username**: `bo_hcm01_1`
   - **Password**: `Password123`

---

### **Running Automated Tests**

```powershell
# Terminal 2 (while Flask server is running)
python test_vulnerabilities.py
```

**Expected Output**:

```
============================================================
RMIT NEOBANK - COMPREHENSIVE VULNERABILITY TEST
============================================================

✅ SQL Injection - Basic Bypass: PASS
   Extracted all applications from multiple branches (clean UI - no warnings visible)

✅ SQL Injection - Data Extraction: PASS
   Successfully extracted data from 5 different branches

✅ IDOR - Cross-Branch Access: PASS
   Accessed 5/5 applications across branches - clean UI shows full details silently

✅ XSS - Payload Injection: PASS
   XSS payload rendered unsafely and executes JavaScript

✅ Command Injection: PASS
   Vulnerability confirmed - detection alert displayed

============================================================
TEST SUMMARY
============================================================
✅ PASSED: 5
❌ FAILED: 0
🎉 ALL VULNERABILITIES CONFIRMED WORKING!
============================================================
```

---

## 🎯 Attack Demonstration

### **Complete Attack Guide**

This repository includes a comprehensive, step-by-step attack demonstration guide:

📄 **[`DETAILED_ATTACK_DEMO_GUIDE.md`](DETAILED_ATTACK_DEMO_GUIDE.md)**

**What's Included**:

- ✅ Detailed attack scenarios for all 5 vulnerabilities
- ✅ Step-by-step instructions with exact payloads
- ✅ Screenshots and visual proof locations
- ✅ Expected results for each attack
- ✅ Python code fixes for remediation
- ✅ Complete testing checklist

**Perfect for**:

- Live demonstrations (6-7 minute presentation)
- Penetration testing practice
- Security training workshops
- Assignment submission evidence

---

### **Quick Attack Reference**

#### **1. SQL Injection** (2 minutes)

```sql
Payload: ' OR 1=1 --
Location: /applications search box
Result: See 457 records (all branches) instead of ~152 (your branch)
Visual: Data table shows HCM01, HN01, DN01, HCM02, DN02
```

#### **2. IDOR - Insecure Direct Object Reference** (1 minute)

```
Action: Change URL /applications/123 → /applications/1
Result: Access loan application from different branch
Visual: Branch code shows HN01 or DN01 (not your HCM01)
```

#### **3. Stored XSS** (1.5 minutes)

```html
Payload: <script>alert('XSS ATTACK')</script>
Location: Application remarks field
Result: JavaScript alert popup when viewing application
Visual: Alert box "XSS ATTACK" appears on screen
```

#### **4. Command Injection** (1 minute)

```bash
Payload: data.csv & whoami
Location: /import filename field (need HO login)
Result: Red alert "COMMAND INJECTION DETECTED"
Visual: Danger alert box with detection message
```

#### **5. Session Hijacking** (1.5 minutes)

```
Action: Copy session cookie from DevTools → Paste in incognito window
Result: Login without password
Visual: Dashboard loads in incognito without login prompt
```

---

### **Test Accounts for Demonstrations**

| Attack Type       | Required Account            | Username       | Password        |
| ----------------- | --------------------------- | -------------- | --------------- |
| SQL Injection     | Any authenticated user      | `bo_hcm01_1` | `Password123` |
| IDOR              | Branch Officer              | `bo_hcm01_1` | `Password123` |
| XSS               | Branch Officer (create app) | `bo_hcm01_1` | `Password123` |
| Command Injection | **Head Office**       | `ho_hcm01_1` | `Password123` |
| Session Hijacking | Any authenticated user      | `bo_hcm01_1` | `Password123` |

**Full account list**: See [`USER_ACCOUNTS_LIST.txt`](USER_ACCOUNTS_LIST.txt) (62 accounts)

---

## 🏗️ Technical Architecture

### **Technology Stack**

| Layer                    | Technology                      | Purpose                           |
| ------------------------ | ------------------------------- | --------------------------------- |
| **Backend**        | Python 3.10 + Flask 3.0         | Web application framework         |
| **Database**       | SQLite 3                        | Relational database (development) |
| **ORM**            | Flask-SQLAlchemy                | Database abstraction layer        |
| **Authentication** | Werkzeug Security               | Password hashing (PBKDF2-SHA256)  |
| **Frontend**       | Bootstrap 5.3 + Jinja2          | Responsive UI templates           |
| **Session**        | Flask Sessions                  | Cookie-based session management   |
| **Testing**        | Python Requests + BeautifulSoup | Automated vulnerability testing   |

### **Database Schema**

#### **Core Tables**

**1. users** (62 records)

```sql
id, username, password_hash, full_name, branch_code, role, is_active, created_at, last_login
```

- Stores staff accounts with role-based permissions
- Password hashing via PBKDF2-SHA256
- Branch code for data isolation

**2. loan_applications** (457 records)

```sql
id, application_ref, applicant_name, national_id, dob, contact_phone, contact_email,
product_code, requested_amount, tenure_months, branch_code, created_by_user_id,
status, assigned_expert_id, reviewed_by_ho_id, grade, remarks, created_at, updated_at
```

- Main application data with 3-tier workflow
- Foreign keys to users (creator, expert, HO)
- Status tracking through approval stages

**3. credit_checks** (120 records)

```sql
id, application_id, requested_by_user_id, credit_score, payment_history,
existing_debts, bureau_response, status, checked_at
```

- Credit bureau integration tracking
- Links to loan applications
- Stores credit assessment data

**4. cic_customers** (457 records - Mock CIC Database)

```sql
national_id, full_name, dob, credit_score, total_debt, payment_history,
active_accounts, late_payments, bankruptcies
```

- Simulates external Credit Information Center
- One-to-one mapping with loan applications
- Provides realistic credit data

---

### **Project Structure**

```
CyberComp_Asm2/
│
├── 📄 app.py                          # Main Flask application (1492 lines)
│   ├── Authentication routes (/login, /logout)
│   ├── Dashboard and navigation
│   ├── Application CRUD operations
│   ├── 3-tier workflow (submit, review, approve)
│   ├── Credit bureau integration
│   ├── VULNERABLE endpoints (SQL injection, IDOR, XSS, Command Injection)
│   └── Error handlers
│
├── 📄 models.py                       # Database models (313 lines)
│   ├── User (staff accounts)
│   ├── LoanApplication (core entity)
│   ├── CreditCheck (bureau records)
│   └── Role/Status constants
│
├── 📄 security.py                     # Security module (405 lines)
│   ├── Password hashing/verification
│   ├── Session management (login/logout)
│   ├── @login_required decorator
│   ├── @role_required decorator
│   ├── Access control helpers (IDOR prevention)
│   └── Input sanitization
│
├── 📄 cic_service.py                  # Credit bureau mock (180 lines)
│   ├── CICService class
│   ├── get_credit_report()
│   ├── calculate_credit_score()
│   └── Payment history analysis
│
├── 📄 init_db.py                      # Database initialization
├── 📄 seed_data_new.py                # Sample data seeder
├── 📄 test_vulnerabilities.py         # Automated test suite (361 lines)
│
├── 📁 templates/                      # Jinja2 HTML templates
│   ├── base.html                      # Base layout with navbar
│   ├── login.html                     # Staff login form
│   ├── dashboard.html                 # Main dashboard
│   ├── applications_list.html         # Application listing (VULNERABLE: SQL Injection)
│   ├── application_detail.html        # Detail view (VULNERABLE: IDOR + XSS)
│   ├── applications_new.html          # Create application form
│   ├── bulk_import.html               # Import page (VULNERABLE: Command Injection)
│   ├── cic_credit_report.html         # Credit report viewer
│   ├── test_accounts.html             # Account listing page
│   └── error.html                     # Error pages (404, 500)
│
├── 📁 static/                         # CSS, JS, images
│   └── css/
│       └── custom.css                 # Custom styling
│
├── 📁 instance/                       # Runtime data
│   └── neobank_cas.db                 # SQLite database file (5.2 MB)
│
├── 📁 uploads/                        # File upload directory
│
├── 📄 requirements.txt                # Python dependencies
├── 📄 USER_ACCOUNTS_LIST.txt          # 62 test accounts
├── 📄 README.md                       # This file
├── 📄 DETAILED_ATTACK_DEMO_GUIDE.md   # Step-by-step attack guide
└── 📄 ATTACK_TESTING_GUIDE.md         # Comprehensive testing scenarios
```

---

### **Security Architecture**

#### **Defense Layers (Intended)**

```
┌─────────────────────────────────────────────────┐
│  Layer 1: Network (Not implemented - dev only)  │
│  - HTTPS (TLS 1.3)                              │
│  - WAF (Web Application Firewall)              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Layer 2: Application (Implemented)             │
│  - Session management (Flask sessions)         │
│  - Authentication (@login_required)            │
│  - Authorization (@role_required)              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Layer 3: Business Logic (Implemented)          │
│  - Role-Based Access Control (RBAC)            │
│  - Branch-level data isolation                 │
│  - Workflow state validation                   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Layer 4: Data Access (Partially vulnerable)   │
│  - ORM parameterization (✅ Secure)            │
│  - Raw SQL queries (❌ SQL Injection)          │
│  - Object reference checks (❌ IDOR)           │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Layer 5: Database (Implemented)                │
│  - Password hashing (PBKDF2-SHA256)            │
│  - No plaintext passwords                      │
│  - Audit trail (created_by, timestamps)       │
└─────────────────────────────────────────────────┘
```

#### **Attack Surface (Intentional Vulnerabilities)**

| Vulnerability     | Layer   | Bypass Method                 |
| ----------------- | ------- | ----------------------------- |
| SQL Injection     | Layer 4 | Raw SQL string concatenation  |
| IDOR              | Layer 3 | Missing authorization check   |
| XSS               | Layer 2 | `                             |
| Command Injection | Layer 4 | Shell command with user input |
| Session Hijacking | Layer 2 | Missing cookie security flags |

---

### **API Endpoints**

#### **Authentication**

- `GET/POST /login` - Staff login
- `GET /logout` - Session termination

#### **Dashboard**

- `GET /` - Main dashboard (requires login)

#### **Application Management**

- `GET /applications` - List applications (VULNERABLE: SQL Injection)
- `GET /applications/new` - Create application form
- `POST /applications/new` - Submit new application
- `GET /applications/<id>` - View details (VULNERABLE: IDOR + XSS)
- `GET /applications/<id>/edit` - Edit application
- `POST /applications/<id>/edit` - Update application
- `POST /applications/<id>/update-status` - Change workflow status

#### **Credit Bureau Integration**

- `POST /applications/<id>/credit-check` - Request credit report
- `GET /applications/<id>/cic-report` - View CIC credit report
- `POST /applications/<id>/cic-check` - Manual CIC lookup

#### **Bulk Operations** (HO only)

- `GET/POST /import` - Bulk import (VULNERABLE: Command Injection)

#### **Utilities**

- `GET /test-accounts` - View all test accounts
- `GET /uploads/<filename>` - Download uploaded files

---

## 📁 Project Structure

```
CyberComp_Asm2/
├── app.py                      # Main Flask application (VULNERABLE)
├── models.py                   # Database models
├── security.py                 # Authentication logic
├── test_vulnerabilities.py     # Automated test suite
├── ATTACK_TESTING_GUIDE.md     # ⭐ Complete attack scenarios
├── USER_ACCOUNTS_LIST.txt      # Test credentials (62 accounts)
├── instance/
│   └── neobank_cas.db         # SQLite database
├── templates/                  # Jinja2 HTML templates
└── static/                     # CSS/JS assets
```

---

## 🧪 Automated Testing

Run the test suite to verify all vulnerabilities:

```powershell
python test_vulnerabilities.py
```

**Expected Output**:

```
✅ PASSED: 5
❌ FAILED: 0
🎉 ALL VULNERABILITIES CONFIRMED WORKING!
```

**What it tests**:

- SQL Injection: Authentication bypass + data extraction
- IDOR: Cross-branch application access (5 IDs)
- XSS: JavaScript execution in remarks field
- Command Injection: Shell metacharacter detection

---

## 🔐 Test Accounts

| Username           | Password        | Role           | Branch | Use Case                  |
| ------------------ | --------------- | -------------- | ------ | ------------------------- |
| `bo_hcm01_1`     | `Password123` | Branch Officer | HCM01  | SQL Injection, IDOR, XSS  |
| `ho_hcm01_1`     | `Password123` | Head Office    | HCM01  | Command Injection (admin) |
| `expert_hcm01_1` | `Password123` | Credit Expert  | HCM01  | CIC integration testing   |

**Full list**: See `USER_ACCOUNTS_LIST.txt` (62 accounts across 9 branches)

---

## ⚠️ Security Warnings

### DO NOT:

- ❌ Deploy to production or public networks
- ❌ Store real customer data
- ❌ Use real credentials
- ❌ Test against unauthorized systems

### DO:

- ✅ Use in isolated lab environments only
- ✅ Learn vulnerability mechanics
- ✅ Practice ethical hacking skills
- ✅ Follow responsible disclosure practices

**Legal**: Unauthorized testing may violate Computer Fraud and Abuse Act (CFAA) or equivalent laws.

---

## 📊 Vulnerability Summary

| ID | Vulnerability     | Location               | Risk     | CVSS | Status      |
| -- | ----------------- | ---------------------- | -------- | ---- | ----------- |
| 1  | SQL Injection     | `/applications?q=`   | CRITICAL | 9.8  | ✅ Verified |
| 2  | IDOR              | `/applications/<id>` | HIGH     | 7.5  | ✅ Verified |
| 3  | XSS               | Remarks field          | MEDIUM   | 6.1  | ✅ Verified |
| 4  | Command Injection | `/import`            | CRITICAL | 9.8  | ✅ Verified |

---

## 🛠️ Troubleshooting

### **Common Issues**

#### **1. Port 5000 Already in Use**

**Symptom:**

```
OSError: [WinError 10048] Only one usage of each socket address is normally permitted
```

**Solutions:**

**Option A**: Use different port

```powershell
$env:FLASK_RUN_PORT="5001"; python app.py
```

**Option B**: Kill existing process (PowerShell as Administrator)

```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (replace <PID> with actual process ID)
taskkill /PID <PID> /F
```

---

#### **2. Database Locked Error**

**Symptom:**

```
sqlite3.OperationalError: database is locked
```

**Solutions:**

**Option A**: Close all database connections

```powershell
# Stop Flask server
Ctrl+C

# Delete lock file
Remove-Item instance\neobank_cas.db-wal, instance\neobank_cas.db-shm -Force

# Restart server
python app.py
```

**Option B**: Reinitialize database

```powershell
Remove-Item instance\neobank_cas.db -Force
python init_db.py
python seed_data_new.py
```

---

#### **3. Test Script Fails (0/5 or Partial Pass)**

**Symptom:**

```
✗ SQL Injection: FAILED
Expected 62 users, found 0
```

**Solutions:**

**Check 1**: Verify database is seeded

```powershell
python
>>> from models import db, User
>>> from app import app
>>> with app.app_context():
...     print(User.query.count())
62
>>> exit()
```

**Check 2**: Verify Flask server is running

```powershell
# Open browser to http://localhost:5000
# Should see login page
```

**Check 3**: Re-run with verbose output

```powershell
python test_vulnerabilities.py -v
```

**Check 4**: Test manually

```
1. Login as officer1 / password123
2. Navigate to Applications
3. Search: ' OR 1=1 --
4. Should see ALL 457 applications
```

---

#### **4. Cannot Login with Test Accounts**

**Symptom:**

```
Invalid username or password
```

**Solutions:**

**Check 1**: Verify username (no typos)

```
Correct: officer1, expert1, ho1, admin
Incorrect: Officer1, officer_1, officer-1
```

**Check 2**: Verify password

```
Standard password: password123
(all lowercase, no spaces)
```

**Check 3**: Check user is active

```powershell
python
>>> from models import db, User
>>> from app import app
>>> with app.app_context():
...     user = User.query.filter_by(username='officer1').first()
...     print(f"User: {user.username}, Active: {user.is_active}")
User: officer1, Active: True
>>> exit()
```

**Check 4**: Reset password

```powershell
python
>>> from models import db, User
>>> from security import hash_password
>>> from app import app
>>> with app.app_context():
...     user = User.query.filter_by(username='officer1').first()
...     user.password_hash = hash_password('password123')
...     db.session.commit()
...     print("Password reset successful")
>>> exit()
```

---

#### **5. XSS Attack Not Working**

**Symptom:**

```
Script shows as plain text instead of executing
```

**Solutions:**

**Check 1**: Use correct field

- ✅ **Remarks** field (vulnerable)
- ❌ Applicant Name, Email (sanitized)

**Check 2**: Use correct payload

```html
<script>alert('XSS')</script>
```

Not: `&lt;script&gt;alert('XSS')&lt;/script&gt;`

**Check 3**: Submit application first

1. Login as officer1
2. Create new application
3. Enter XSS payload in Remarks
4. Click "Save Draft"
5. Click "View" link
6. Alert should popup

**Check 4**: Check template (should have `| safe`)

```bash
# Line 138 of templates/application_detail.html should be:
{{ application.remarks | safe }}
# Not:
{{ application.remarks }}
```

---

#### **6. Command Injection Not Working**

**Symptom:**

```
File uploads but no alert/command output visible
```

**Solutions:**

**Check 1**: Login as HO or Admin

- Branch Officers/Experts cannot access /import endpoint
- Use ho1 / password123 or admin / password123

**Check 2**: Use correct payload

```
data.csv & whoami
```

- Space before `&` is required
- Windows command: `whoami`, `dir`, `hostname`

**Check 3**: Check terminal output

- Flask server terminal will show command output
- Look for username after file upload message

**Check 4**: Alternative payloads

```
data.csv & echo HACKED
data.csv & type USER_ACCOUNTS_LIST.txt
data.csv && powershell -c "Get-Date"
```

---

#### **7. Session Hijacking Not Working**

**Symptom:**

```
Copied cookie but still asked to login
```

**Solutions:**

**Check 1**: Copy FULL cookie value

- DevTools → Application → Cookies → session
- Value is long string: `eyJ1c2VyX2lkIjoxfQ.Zm9vYmFy...`
- Copy entire value (no truncation)

**Check 2**: Use same browser

- Cookie captured from Chrome → use Chrome for hijack
- Cookie captured from Firefox → use Firefox for hijack

**Check 3**: Use Incognito/Private window

- Open new Incognito/Private window (Ctrl+Shift+N)
- Go to http://localhost:5000
- DO NOT login
- Open DevTools → Application → Cookies
- Add session cookie manually:
  - Name: `session`
  - Value: (paste copied value)
  - Domain: `localhost`
  - Path: `/`
- Refresh page → should be logged in

**Check 4**: Check cookie expiration

- Session cookies expire on browser close
- Victim's browser must still be open
- Cookie valid for ~24 hours

---

#### **8. IDOR Returns 403 Forbidden**

**Symptom:**

```
Access denied to application #123
```

**Solutions:**

**Check 1**: Use correct attack URL

- ❌ `/applications?id=123` (won't work)
- ✅ `/applications/123` (vulnerable endpoint)

**Check 2**: Find valid application IDs

```powershell
# Login as officer1
# Note down application IDs from your dashboard
# Example: APP-HCM01-001, APP-HCM01-002 → IDs are 1, 2, 3...
```

**Check 3**: Try different branches

```
# Login as officer1 (HCM01 branch)
# Try accessing: /applications/234 (HN01 branch app)
# Should succeed (IDOR vulnerability)
```

**Check 4**: Check if application exists

```powershell
python
>>> from models import db, LoanApplication
>>> from app import app
>>> with app.app_context():
...     app = LoanApplication.query.filter_by(id=234).first()
...     print(f"App: {app.application_ref}, Branch: {app.branch_code}")
>>> exit()
```

---

#### **9. Database Has No Data After Init**

**Symptom:**

```
Dashboard shows "No applications found"
```

**Solutions:**

**Step 1**: Check if seed_data_new.py ran

```powershell
python
>>> from models import db, LoanApplication
>>> from app import app
>>> with app.app_context():
...     print(f"Users: {User.query.count()}")
...     print(f"Apps: {LoanApplication.query.count()}")
Users: 0
Apps: 0
>>> exit()
```

**Step 2**: Run seed script manually

```powershell
python seed_data_new.py
```

**Step 3**: Verify seed success

```powershell
# Should see output:
✓ Created 62 users across 9 branches
✓ Created 457 loan applications
✓ Database seeded successfully
```

---

#### **10. Flask Says "Module Not Found"**

**Symptom:**

```
ModuleNotFoundError: No module named 'flask'
```

**Solutions:**

**Check 1**: Activate virtual environment

```powershell
# Look for (venv) in terminal prompt
# If missing:
venv\Scripts\Activate.ps1
```

**Check 2**: Install dependencies

```powershell
pip install -r requirements.txt
```

**Check 3**: Check Python version

```powershell
python --version
# Should be: Python 3.10.x or higher
```

**Check 4**: Recreate virtual environment

```powershell
Remove-Item -Recurse -Force venv
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

### **Getting Help**

If issues persist:

1. **Check Flask server terminal** - shows detailed error messages
2. **Check browser DevTools Console** - JavaScript errors (F12)
3. **Check database integrity**:
   ```powershell
   python
   >>> from app import app
   >>> from models import db
   >>> with app.app_context():
   ...     db.session.execute('PRAGMA integrity_check').fetchone()
   ('ok',)
   ```
4. **Nuclear option - full reset**:
   ```powershell
   Remove-Item instance\neobank_cas.db -Force
   python init_db.py
   python seed_data_new.py
   python test_vulnerabilities.py
   ```

---

## 📚 Learning Resources

### **Security References**

#### **OWASP (Open Web Application Security Project)**

- **OWASP Top 10 2021**: https://owasp.org/www-project-top-ten/

  - A03:2021 - Injection (SQL Injection, Command Injection)
  - A01:2021 - Broken Access Control (IDOR)
  - A03:2021 - Injection (Cross-Site Scripting)
  - A07:2021 - Identification and Authentication Failures (Session Hijacking)
- **OWASP Testing Guide**: https://owasp.org/www-project-web-security-testing-guide/

  - Chapter 4.8: Testing for SQL Injection
  - Chapter 4.5: Testing for Access Control Issues
  - Chapter 4.8: Testing for Cross-Site Scripting

#### **MITRE ATT&CK Framework**

- **CWE-89**: SQL Injection
- **CWE-639**: Insecure Direct Object References (IDOR)
- **CWE-79**: Cross-Site Scripting (XSS)
- **CWE-78**: OS Command Injection
- **CWE-384**: Session Fixation

#### **PortSwigger Web Security Academy**

- Free interactive labs: https://portswigger.net/web-security
  - SQL Injection labs (12 labs)
  - Access Control labs (14 labs)
  - XSS labs (30 labs)
  - OS Command Injection labs (5 labs)

---

### **Banking Domain Knowledge**

#### **Loan Origination Process**

- **Federal Reserve**: Lending Standards and Practices
  - https://www.federalreserve.gov/supervisionreg/topics/lending.htm
- **Basel Committee on Banking Supervision**: Credit Risk Management
  - https://www.bis.org/publ/bcbs_nl21.htm

#### **Credit Bureau Integration**

- **TransUnion Developer Portal**: https://developer.transunion.com/
- **Experian Credit API**: https://www.experian.com/business/products/credit-apis

#### **Banking Security Standards**

- **PCI DSS**: Payment Card Industry Data Security Standard
  - https://www.pcisecuritystandards.org/
- **FFIEC**: IT Examination Handbook
  - https://ithandbook.ffiec.gov/

---

### **Python Security Best Practices**

#### **Official Documentation**

- **Flask Security**: https://flask.palletsprojects.com/en/stable/security/
- **SQLAlchemy Security**: https://docs.sqlalchemy.org/en/20/faq/security.html
- **Werkzeug Security Utils**: https://werkzeug.palletsprojects.com/en/stable/utils/

#### **Secure Coding**

- **OWASP Secure Coding Practices**: https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/
- **Python Security Best Practices (Snyk)**: https://snyk.io/blog/python-security-best-practices-cheat-sheet/

---

### **Academic Resources**

#### **Research Papers**

- "SQL Injection: Detection and Prevention" (IEEE)
- "Session Management Vulnerabilities in Modern Web Applications" (ACM)
- "A Systematic Study of XSS Vulnerabilities" (USENIX Security)

#### **Books**

- **"The Web Application Hacker's Handbook"** by Dafydd Stuttard & Marcus Pinto
- **"SQL Injection Attacks and Defense"** by Justin Clarke
- **"Secure Coding: Principles & Practices"** by Mark G. Graff & Kenneth R. van Wyk

---

### **Tools for Further Exploration**

#### **Vulnerability Scanners**

- **OWASP ZAP**: https://www.zaproxy.org/ (Free)
- **Burp Suite Community**: https://portswigger.net/burp/communitydownload (Free)
- **Nikto**: https://github.com/sullo/nikto (Free)

#### **SQL Injection Tools**

- **SQLMap**: https://sqlmap.org/ (Automated SQL injection detection)

#### **Browser Extensions**

- **Cookie-Editor**: https://cookie-editor.cgagnier.ca/ (Session management testing)
- **TamperMonkey**: https://www.tampermonkey.net/ (Script injection testing)

---
