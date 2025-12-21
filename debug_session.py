"""
Debug script to test session cookie validity
"""

from flask import Flask
from itsdangerous import BadSignature, URLSafeTimedSerializer

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-in-production-use-strong-random-key"


def test_session_cookie(cookie_value):
    """Test if a session cookie is valid"""
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

    try:
        session_data = serializer.loads(cookie_value)
        print("✅ Cookie is VALID!")
        print(f"\n📋 Session Data:")
        for key, value in session_data.items():
            print(f"   {key}: {value}")
        return True
    except BadSignature:
        print("❌ Cookie is INVALID (bad signature)")
        print("   Possible reasons:")
        print("   - Cookie was copied incorrectly (missing characters)")
        print("   - SECRET_KEY changed in app.py")
        print("   - Cookie is from a different Flask app")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SESSION COOKIE VALIDATOR")
    print("=" * 60)
    print("\nPaste the session cookie value below:")
    print("(The long string from DevTools → Cookies → session)")
    print("-" * 60)

    cookie_value = input("Cookie value: ").strip()

    if not cookie_value:
        print("\n❌ No cookie provided!")
    elif len(cookie_value) < 50:
        print(f"\n⚠️  Cookie seems too short ({len(cookie_value)} chars)")
        print("   Expected: 200+ characters")
        print("   Make sure you copied the ENTIRE value")
    else:
        print(f"\n📏 Cookie length: {len(cookie_value)} characters")
        print("\n🔍 Testing cookie validity...")
        print("-" * 60)
        test_session_cookie(cookie_value)

    print("\n" + "=" * 60)
    input("\nPress Enter to exit...")
