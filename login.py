from seleniumbase import SB
import os
import pickle

# Session file to save login state
SESSION_FILE = "target_session.pkl"
# Login credentials
EMAIL = "abasto.ricky76@gmail.com"
PASSWORD = "@Hbpmott456!"

# ============================================================================
# STEP 1: LOGIN AND SAVE SESSION
# ============================================================================

# Step 1.1: Helper function to check if user is logged in
def check_if_logged_in(sb):
    # Check for user greeting text "Hi, " which appears after login
    try:
        if sb.is_text_visible("Hi,", timeout=3):
            return True
    except:
        pass
    # Check account link text - if contains "sign in" then not logged in
    try:
        account_link = sb.find_element('a[data-test="@web/AccountLink"]', timeout=3)
        link_text = account_link.text.lower()
        if "sign in" in link_text or link_text == "account":
            return False
        if "hi," in link_text or len(link_text) > 10:
            return True
    except:
        pass
    # Check for auth-related cookies
    try:
        cookies = sb.driver.get_cookies()
        for cookie in cookies:
            cookie_name = cookie.get('name', '').lower()
            if 'auth' in cookie_name or 'session' in cookie_name or 'token' in cookie_name:
                return True
    except:
        pass
    return False

# Step 1.2: Auto login function
def auto_login(sb, email, password):
    # Navigate to login page by clicking account link
    try:
        if sb.is_element_visible('a[data-test="@web/AccountLink"]', timeout=3):
            sb.click('a[data-test="@web/AccountLink"]')
            sb.sleep(2)
    except:
        sb.uc_open_with_reconnect("https://www.target.com/account", reconnect_time=2)
    # Enter email
    try:
        sb.type('input#username', email)
        sb.sleep(1)
    except Exception as e:
        print(f"Error entering email: {e}")
        return False
    # Click Continue button
    try:
        sb.click('button:contains("Continue")')
        sb.sleep(2)
    except Exception as e:
        print(f"Error clicking Continue: {e}")
        return False
    # Click Enter your password option
    try:
        sb.click('#password')
        sb.sleep(1)
    except Exception as e:
        print(f"Error selecting password option: {e}")
        return False
    # Enter password
    try:
        sb.type('input[name="password"]', password)
        sb.sleep(1)
    except Exception as e:
        print(f"Error entering password: {e}")
        return False
    # Click Sign in button
    try:
        sb.click('button:contains("Sign in")')
        sb.sleep(3)
    except Exception as e:
        print(f"Error clicking Sign in: {e}")
        return False
    # Check if login successful
    is_logged_in = check_if_logged_in(sb)
    return is_logged_in

# Step 1.3: Main function to login and save session
def login_to_target():
    # Open browser with UC Mode to avoid detection
    with SB(uc=True, incognito=False) as sb:
        # Open Target.com homepage
        url = "https://www.target.com"
        print("Opening Target.com...")
        sb.uc_open_with_reconnect(url, reconnect_time=3)
        # Check if already logged in
        is_logged_in = check_if_logged_in(sb)
        if not is_logged_in:
            # Auto login
            print("Logging in automatically...")
            is_logged_in = auto_login(sb, EMAIL, PASSWORD)
            if not is_logged_in:
                print("ERROR: Auto-login failed. Please check credentials.")
                return False
        else:
            print("Already logged in.")
        # Remove old session file if exists
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        # Get all cookies from current session
        cookies = sb.driver.get_cookies()
        # Save cookies to file using pickle
        with open(SESSION_FILE, 'wb') as f:
            pickle.dump(cookies, f)
        print(f"Session saved to {SESSION_FILE} ({len(cookies)} cookies)")
        sb.sleep(2)
        return True

if __name__ == "__main__":
    login_to_target()

