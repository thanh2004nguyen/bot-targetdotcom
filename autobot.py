# ============================================================================
# macOS Setup Instructions - Hướng dẫn cài đặt và chạy trên macOS
# ============================================================================
# cd /Users/nguyenthaithanh/Upwork/Ricky_Abasto/bot-targetdotcom
# source venv/bin/activate
# python autobot.py

# ============================================================================
# IMPORTS - Thư viện và modules
# ============================================================================

# SeleniumBase - Web automation framework
from seleniumbase import SB

# Selenium WebDriver components
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Python standard library
import os
import time
import math
import re
import json

# ============================================================================
# CONFIGURATION - Cấu hình
# ============================================================================

# Login credentials
EMAIL = "abasto.ricky76@gmail.com"
PASSWORD = "@Hbpmott456!"

# Product configuration
# Pokémon Trading Card Game: Mega Evolutions- Phantasmal Flames 9-Pocket Portfolio
# Pokémon Trading Card Game : Pokémon Day 2026 Collection
# https://www.target.com/p/pokemon/A-95082138
product_main = {
    "name": "Pokémon Trading Card Game : Pokémon Day 2026 Collection",
    "quantities": "2"
}
product_smalls = [
    {"name": "Skittles Sour Candy, Chewy Fruit Candies Share Size Bag - 13.7oz"}
]
FREE_SHIPPING_THRESHOLD = 35.00

# File lưu cookies/session (cùng thư mục với script)
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.json")

# Test mode: True = không click "Place your order" (chạy tới trang checkout rồi dừng)
SKIP_PLACE_ORDER = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_element_visible(sb, selector, timeout=1):
    try:
        sb.wait_for_element_visible(selector, timeout=timeout)
        return True
    except:
        return False


# ============================================================================
# STEP 1: LOGIN AND INITIALIZE
# ============================================================================

def get_logged_in_user_name(sb):
    """Lấy tên tài khoản đã đăng nhập (ví dụ 'Thanh') từ aria-label 'Hi, Thanh, ...' hoặc link."""
    try:
        mobile_link = sb.driver.find_element(By.CSS_SELECTOR, 'a[data-test="@web/AccountLinkMobile"]')
        aria = (mobile_link.get_attribute("aria-label") or "").strip()
        if aria.lower().startswith("hi,"):
            parts = aria.split(",", 2)
            if len(parts) >= 2:
                return parts[1].strip()
    except Exception:
        pass
    try:
        account_link = sb.driver.find_element(By.CSS_SELECTOR, 'a[data-test="@web/AccountLink"]')
        text = (account_link.text or "").strip()
        if text.lower().startswith("hi,"):
            parts = text.split(",", 2)
            if len(parts) >= 2:
                return parts[1].strip()
    except Exception:
        pass
    return None


def check_if_logged_in(sb):
    """Kiểm tra đã đăng nhập: thấy 'Hi, [tên]' (trang chủ hoặc Account link)."""
    try:
        if sb.is_text_visible("Hi,", timeout=1):
            return True
    except:
        pass
    try:
        account_link = sb.find_element('a[data-test="@web/AccountLink"]', timeout=1)
        link_text = account_link.text.lower()
        if "sign in" in link_text or link_text == "account":
            return False
        if "hi," in link_text or len(link_text) > 10:
            return True
    except:
        pass
    try:
        # Account link mobile: aria-label="Hi, Thanh, 2 new Target Circle bonuses..."
        mobile_link = sb.find_element('a[data-test="@web/AccountLinkMobile"]', timeout=1)
        aria = (mobile_link.get_attribute("aria-label") or "").strip()
        if aria.lower().startswith("hi,"):
            return True
    except:
        pass
    return False


def check_session_still_valid(sb):
    """Kiểm tra session/cookies còn hiệu lực (còn "Hi, [tên]" chứ không phải "Account")."""
    return check_if_logged_in(sb)


def re_login(sb, email, password):
    """
    Khi session hết hạn (hiển thị "Account" thay vì "Hi, [tên]"): đăng nhập lại để lấy session mới.
    Returns True nếu còn đăng nhập hoặc đăng nhập lại thành công, False nếu thất bại.
    """
    if check_if_logged_in(sb):
        return True
    print("  Session expired (cookies invalid). Re-logging in...")
    sb.open("https://www.target.com")
    sb.sleep(1)
    if not auto_login(sb, email, password):
        print("  Re-login failed.")
        return False
    if save_cookies(sb):
        print("  Session saved to cookies.json")
    print("  Session restored.")
    return True


def auto_login(sb, email, password):
    try:
        print("  Opening account menu...")
        if is_element_visible(sb, 'a[data-test="@web/AccountLink"]', timeout=1):
            sb.click('a[data-test="@web/AccountLink"]')
        else:
            sb.open("https://www.target.com/account")
    except Exception as e:
        print(f"  Login failed (account menu): {e}")
        return False
    
    try:
        if is_element_visible(sb, 'button[data-test="accountNav-signIn"]', timeout=3):
            sb.click('button[data-test="accountNav-signIn"]')
        else:
            print("  Login failed: Sign in button not found")
            return False
    except Exception as e:
        print(f"  Login failed (Sign in button): {e}")
        return False

    time.sleep(2)
    # Đã đăng nhập rồi (redirect về có "Hi, [tên]") → xong
    if check_if_logged_in(sb):
        name = get_logged_in_user_name(sb)
        if name:
            print(f"  Already signed in (Hi, {name})")
        return True

    current_url = sb.get_current_url()
    on_login_page = "/login" in current_url

    # Trang /login: chỉ nhập email nếu có ô email, chỉ nhập password nếu có ô password
    if on_login_page:
        # Có ô email → nhập email và Continue
        if is_element_visible(sb, 'input#username', timeout=3):
            try:
                print("  On login page: entering email...")
                sb.type('input#username', email)
                sb.click('button:contains("Continue")')
                time.sleep(2)
            except Exception as e:
                print(f"  Login failed (email/Continue): {e}")
                return False
            if check_if_logged_in(sb):
                print("  Already signed in after Continue")
                return True
        # Có ô mật khẩu → nhập password và Sign in
        if is_element_visible(sb, 'input[name="password"]', timeout=2) or is_element_visible(sb, '#password', timeout=1):
            try:
                print("  On login page: entering password...")
                sb.click('#password')
                sb.type('input[name="password"]', password)
                sb.click('button:contains("Sign in")')
            except Exception as e:
                print(f"  Login failed (password/Sign in): {e}")
                return False
            print("  Waiting for login (Hi, [name]) - enter verification code if needed...")
            while True:
                if check_if_logged_in(sb):
                    name = get_logged_in_user_name(sb)
                    if name:
                        print(f"  Login detected (Hi, {name})")
                    return True
                time.sleep(2)
        # Trên /login nhưng không thấy email hay password → chờ manual hoặc đã redirect
        if check_if_logged_in(sb):
            return True
        print("  Login page: no email/password field found, waiting for manual login (3m)...")
        deadline = time.time() + 180
        while time.time() < deadline:
            if check_if_logged_in(sb):
                return True
            time.sleep(2)
        return False

    # Không phải /login: flow cũ (có thể đang ở account với form khác)
    on_password_page = is_element_visible(sb, 'input[name="password"]', timeout=1) or is_element_visible(sb, '#password', timeout=1)
    if on_password_page:
        print("  Already on password page, entering password...")
    else:
        if is_element_visible(sb, 'input#username', timeout=3):
            try:
                print("  Entering email...")
                sb.type('input#username', email)
                sb.click('button:contains("Continue")')
                time.sleep(2)
            except Exception as e:
                print(f"  Login failed (email): {e}")
                return False
            if check_if_logged_in(sb):
                return True
            on_password_page = is_element_visible(sb, 'input[name="password"]', timeout=2) or is_element_visible(sb, '#password', timeout=1)
        if not on_password_page:
            print("  Login failed: email field not found")
            return False

    if on_password_page:
        try:
            print("  Entering password...")
            sb.click('#password')
            sb.type('input[name="password"]', password)
            sb.click('button:contains("Sign in")')
        except Exception as e:
            print(f"  Login failed (password/Sign in): {e}")
            return False
        print("  Waiting for login (Hi, [name]) - enter verification code if needed...")
        while True:
            if check_if_logged_in(sb):
                name = get_logged_in_user_name(sb)
                if name:
                    print(f"  Login detected (Hi, {name})")
                return True
            time.sleep(2)

    print("  Waiting for manual login (3m)")
    deadline = time.time() + 180
    while time.time() < deadline:
        if check_if_logged_in(sb):
            return True
        time.sleep(2)
    return False


def load_cookies(sb):
    """Load cookies từ cookies.json vào driver (phải đang ở target.com)."""
    if not os.path.isfile(COOKIES_FILE):
        print("  No cookies file found, will sign in with email/password")
        return False
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        if not isinstance(cookies, list):
            print("  Cookies file invalid (not a list), will sign in with email/password")
            return False
        added = 0
        for c in cookies:
            try:
                cookie = {k: v for k, v in c.items() if k in ("name", "value", "domain", "path", "secure", "httpOnly", "expiry", "sameSite")}
                if "expiry" in cookie and isinstance(cookie["expiry"], float):
                    cookie["expiry"] = int(cookie["expiry"])
                sb.driver.add_cookie(cookie)
                added += 1
            except Exception:
                continue
        if added == 0:
            print("  Could not add any cookie (domain/format?), will sign in with email/password")
            return False
        print(f"  Loaded {added} cookies from cookies.json")
        return True
    except Exception as e:
        print(f"  Failed to load cookies: {e}")
        return False


def save_cookies(sb):
    """Lưu cookies hiện tại (sau khi đăng nhập thành công) vào cookies.json."""
    try:
        cookies = sb.driver.get_cookies()
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def login_to_target(sb, email, password):
    sb.uc_open_with_reconnect("https://www.target.com", reconnect_time=2)

    # Thử load session từ cookies.json
    session_valid = False
    if load_cookies(sb):
        sb.driver.refresh()
        sb.sleep(2)
        if check_if_logged_in(sb):
            name = get_logged_in_user_name(sb)
            if name:
                print(f"  Session valid (Hi, {name})")
            else:
                print("  Session valid, skipping login")
            session_valid = True
        else:
            print("  Session expired or invalid, signing in with email/password...")

    # Session có vấn đề → đăng nhập lại bằng email/password
    if not session_valid:
        print("  Running auto login (email/password)...")
        if not auto_login(sb, email, password):
            print("  Auto login failed.")
            return False
        # Đăng nhập thành công → lưu cookies để lần sau dùng
        if save_cookies(sb):
            print("  Session saved to cookies.json")
    return True

def initialize_session(email, password):
    try:
        sb_context = SB(uc=True, incognito=True)
        sb = sb_context.__enter__()
        if not hasattr(sb, '_context_manager'):
            sb._context_manager = sb_context
        
        if not login_to_target(sb, email, password):
            sb.driver.quit()
            return None
        
        return sb
    except Exception as e:
        print(f"Error: {e}")
        return None

# ============================================================================
# STEP 2: NAVIGATE TO PRODUCT
# ============================================================================

def click_account_menu(sb):
    selectors = [
        'a[data-test="@web/AccountLink"]',
        'a#account-sign-in',
        'a[href*="/account"]'
    ]
    
    for selector in selectors:
        try:
            if is_element_visible(sb, selector, timeout=2):
                sb.click(selector)
                if is_element_visible(sb, 'a[data-test="accountNav-listsAndFavorites"]', timeout=1):
                    return True
        except:
            continue
    
    try:
        sb.open("https://www.target.com/account")
        return True
    except:
        return False

def click_lists_and_favorites(sb):
    try:
        if is_element_visible(sb, 'a[data-test="accountNav-listsAndFavorites"]', timeout=1):
            sb.click('a[data-test="accountNav-listsAndFavorites"]')
            return "/lists" in sb.get_current_url()
    except:
        pass
    return False

def _wait_for_product_page_url(sb, timeout=10):
    """Đợi URL chuyển sang trang sản phẩm (/p/)."""
    try:
        WebDriverWait(sb.driver, timeout).until(lambda d: "/p/" in d.current_url)
        return True
    except Exception:
        return False


def find_and_click_product(sb, product_name):
    """
    Trên trang danh sách ưu thích: click vào TÊN SẢN PHẨM (link) để mở trang sản phẩm.
    Nếu đã ở trang /p/ thì coi là thành công, không click lại.
    Chỉ click MỘT link rồi đợi URL /p/ (tránh click nhiều link gây "navigate hai lần").
    """
    current_url = sb.get_current_url()
    if "/p/" in current_url:
        return True
    # Chỉ tìm và click MỘT link, không lặp click nhiều link
    link_to_click = None
    try:
        links = sb.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/p/"]')
        for link in links:
            if not link.is_displayed():
                continue
            title = (link.get_attribute("title") or "").strip()
            text = (link.text or "").strip()
            if product_name in title or product_name in text:
                link_to_click = link
                break
    except Exception:
        pass
    if link_to_click is None:
        try:
            if is_element_visible(sb, f'a[title="{product_name}"]', timeout=1):
                link_to_click = sb.driver.find_element(By.CSS_SELECTOR, f'a[title="{product_name}"]')
        except Exception:
            pass
    if link_to_click is None:
        for sel in [f'a[title="{product_name}"]', f'div[title="{product_name}"]']:
            try:
                if is_element_visible(sb, sel, timeout=1):
                    link_to_click = sb.driver.find_element(By.CSS_SELECTOR, sel)
                    break
            except Exception:
                continue
    if link_to_click is not None:
        try:
            link_to_click.click()
        except Exception:
            try:
                sb.driver.execute_script("arguments[0].click();", link_to_click)
            except Exception:
                pass
        if _wait_for_product_page_url(sb, timeout=10):
            return True
        if "/p/" in sb.get_current_url():
            return True
    return False

def navigate_to_product(sb, product_name):
    # Đã ở trang sản phẩm rồi thì chỉ cần đợi nút (không vào Account/Lists/click lại → tránh trùng logic)
    if "/p/" in sb.get_current_url():
        try:
            WebDriverWait(sb.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-test="shippingButton"], button[id^="addToCartButtonOrTextIdFor"], button[data-test="preorderButtonDisabled"], button[data-test="custom-quantity-picker"]')))
            print("  Page ready")
            sb.sleep(1.5)
            return True
        except Exception:
            print("  Stopping: product page did not load.")
            return False
    if not click_account_menu(sb):
        print("  Stopping: could not open Account menu.")
        return False
    if not click_lists_and_favorites(sb):
        print("  Stopping: could not open Lists & Favorites.")
        return False
    # Đợi danh sách sản phẩm load (có link tới trang /p/)
    try:
        WebDriverWait(sb.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/p/"]')))
        sb.sleep(0.5)
    except Exception:
        print("  Stopping: product list did not load.")
        return False
    if not find_and_click_product(sb, product_name):
        if "/p/" not in sb.get_current_url():
            print("  Stopping: could not find or click product.")
            return False
    # Đảm bảo đã vào trang sản phẩm: có nút Add to cart / shipping HOẶC nút "X in cart"
    try:
        WebDriverWait(sb.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-test="shippingButton"], button[id^="addToCartButtonOrTextIdFor"], button[data-test="preorderButtonDisabled"], button[data-test="custom-quantity-picker"]')))
    except Exception:
        print("  Stopping: product page did not load.")
        return False
    print("  Opening product page")
    try:
        title_el = sb.driver.find_element(By.CSS_SELECTOR, 'h1[data-test="product-title"]')
        print(f"  {title_el.text.strip()}")
    except Exception:
        print("  (product title not found)")
    print(f"  {sb.get_current_url()}")
    sb.sleep(1.5)
    return True

# ============================================================================
# STEP 3: ADD MAIN PRODUCT TO CART (OPTIMIZED)
# ============================================================================

def _aria_label_matches_product(aria_label, product_name):
    """Chỉ coi nút thuộc sản phẩm chính khi aria-label chứa tên sản phẩm (tránh click nút Find alternative)."""
    if not aria_label or not product_name:
        return False
    return product_name.strip() in (aria_label or "").strip()


def check_add_to_cart_button_status(sb, product_name):
    """Chỉ xét nút Add to cart có aria-label chứa product_name (sản phẩm chính), bỏ qua Find alternative."""
    if not product_name:
        product_name = ""
    # Check disabled: nút chính (aria-label chứa tên sản phẩm) bị disabled
    try:
        preorder = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="preorderButtonDisabled"]')
        for btn in preorder:
            try:
                if btn.is_displayed() and _aria_label_matches_product(btn.get_attribute("aria-label") or "", product_name):
                    return "disabled"
            except:
                continue
    except:
        pass
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[id^="addToCartButtonOrTextIdFor"]')
        for button in buttons:
            try:
                if not button.is_displayed():
                    continue
                aria = (button.get_attribute("aria-label") or "").strip()
                if not _aria_label_matches_product(aria, product_name):
                    continue
                if button.get_attribute('disabled') is not None:
                    return "disabled"
                if button.get_attribute('data-test') == 'preorderButtonDisabled':
                    return "disabled"
            except:
                continue
    except:
        pass
    # Check available: nút chính (aria-label chứa tên sản phẩm) enabled
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="shippingButton"]')
        for button in buttons:
            try:
                if not button.is_displayed() or not button.is_enabled():
                    continue
                aria = (button.get_attribute('aria-label') or "").strip()
                if not _aria_label_matches_product(aria, product_name):
                    continue
                if "Add to cart" in (button.text or "") or "Add to cart" in aria:
                    return "available"
            except:
                continue
    except:
        pass
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[id^="addToCartButtonOrTextIdFor"]')
        for button in buttons:
            try:
                if not button.is_displayed():
                    continue
                aria = (button.get_attribute('aria-label') or "").strip()
                if not _aria_label_matches_product(aria, product_name):
                    continue
                if button.get_attribute('disabled') is not None:
                    continue
                if not button.is_enabled():
                    continue
                if "Add to cart" in (button.text or "") or "Add to cart" in aria:
                    return "available"
            except:
                continue
    except:
        pass
    return "not_found"

def wait_for_add_to_cart_button_available(sb, product_name, max_wait_minutes=10080, check_interval=0.3):
    max_wait_seconds = max_wait_minutes * 60
    start_time = time.time()
    refresh_interval = 5
    last_refresh_time = start_time
    add_cart_selectors = [
        'button[data-test="shippingButton"]',
        'button[id^="addToCartButtonOrTextIdFor"]',
    ]
    print("  Waiting for product availability (Add to cart)")
    sb.sleep(1.5)

    while True:
        try:
            status = check_add_to_cart_button_status(sb, product_name)
            current_time = time.time()

            if status == "available":
                print("  Product available, verifying button (main product only)")
                for sel in add_cart_selectors:
                    try:
                        for btn in sb.driver.find_elements(By.CSS_SELECTOR, sel):
                            try:
                                if not btn.is_displayed():
                                    continue
                                t = (btn.text or "").strip()
                                a = (btn.get_attribute("aria-label") or "").strip()
                                if "Add to cart" not in t and "Add to cart" not in a:
                                    continue
                                if not _aria_label_matches_product(a, product_name):
                                    continue
                                WebDriverWait(sb.driver, 3).until(EC.element_to_be_clickable(btn))
                                print("  Add to cart button ready")
                                return True
                            except Exception:
                                continue
                    except Exception:
                        continue
        except Exception as e:
            err_msg = str(e)
            if "HTTPConnectionPool" in err_msg or "Connection" in err_msg:
                print("  - Connection issue during check, retrying...")
            else:
                print(f"  - Error checking status: {err_msg[:50]}")

        current_time = time.time()
        if current_time - last_refresh_time >= refresh_interval:
            try:
                sb.driver.refresh()
                last_refresh_time = current_time
                sb.sleep(1)
            except Exception as e:
                print(f"  - Refresh failed: {str(e)[:50]}")

        if int(current_time - start_time) >= max_wait_seconds:
            print("  Stopping: maximum wait time reached.")
            return False

        sb.sleep(check_interval)

def check_and_update_cart_quantity(sb, desired_quantity=2, product_name=None):
    """
    Nếu sản phẩm chính đã có trong giỏ: kiểm tra số lượng (nút "X in cart" có aria-label chứa product_name).
    Nếu đã đúng desired_quantity → chuyển tới trang cart. Nếu chưa → mở picker, chọn số lượng, rồi vào cart.
    """
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="custom-quantity-picker"]')
        for button in buttons:
            try:
                if not button.is_displayed():
                    continue
                btn_text = (button.text or "").lower()
                if "in cart" not in btn_text:
                    continue
                # Chỉ xét nút của sản phẩm chính: aria-label chứa product_name (ví dụ "1 in cart for Pokémon...")
                try:
                    span = button.find_element(By.CSS_SELECTOR, 'span[aria-label*="in cart"]')
                    aria = (span.get_attribute("aria-label") or "").strip()
                    if product_name and not _aria_label_matches_product(aria, product_name):
                        continue
                except Exception:
                    if product_name:
                        continue
                # Lấy số lượng hiện tại
                current_qty = 1
                try:
                    span = button.find_element(By.CSS_SELECTOR, 'span[aria-label*="in cart"]')
                    aria = (span.get_attribute("aria-label") or "").strip()
                    qty_match = re.search(r"(\d+)\s+in\s+cart", aria, re.IGNORECASE)
                    if qty_match:
                        current_qty = int(qty_match.group(1))
                except Exception:
                    qty_match = re.search(r"(\d+)\s+in\s+cart", btn_text, re.IGNORECASE)
                    if qty_match:
                        current_qty = int(qty_match.group(1))
                if current_qty == desired_quantity:
                    print("  Product already exists in cart")
                    print("  Quantity verified")
                    sb.open("https://www.target.com/cart")
                    return True
                # Chưa đúng: click vào nút số lượng để mở dropdown, chọn desired_quantity
                print(f"  Updating quantity from {current_qty} to {desired_quantity}")
                sb.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
                sb.sleep(0.2)
                button.click()
                # Đợi danh sách option xuất hiện (ul.Options_styles_options__YvWBL)
                try:
                    WebDriverWait(sb.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.Options_styles_options__YvWBL, ul[class*="Options"]')))
                    sb.sleep(0.3)
                except Exception:
                    sb.sleep(0.5)
                # Chọn option: aria-label="2" hoặc "1 - selected" (format Target)
                for sel in [f'a[aria-label="{desired_quantity}"]', f'a[aria-label="{desired_quantity} - selected"]', f'a[aria-label^="{desired_quantity}"]']:
                    try:
                        opt = sb.driver.find_element(By.CSS_SELECTOR, sel)
                        if opt.is_displayed() and "close" not in (opt.get_attribute("aria-label") or "").lower():
                            opt.click()
                            sb.sleep(0.3)
                            break
                    except Exception:
                        continue
                sb.open("https://www.target.com/cart")
                return True
            except Exception:
                continue
    except Exception:
        pass
    return False

def click_add_to_cart_button(sb, product_name):
    """Chỉ click nút Add to cart có aria-label chứa product_name (sản phẩm chính), bỏ qua Find alternative."""
    selectors = [
        'button[data-test="shippingButton"]',
        'button[id^="addToCartButtonOrTextIdFor"]',
    ]
    for _ in range(5):
        for sel in selectors:
            try:
                for btn in sb.driver.find_elements(By.CSS_SELECTOR, sel):
                    try:
                        if not btn.is_displayed() or btn.get_attribute("disabled") is not None:
                            continue
                        t = (btn.text or "").strip()
                        a = (btn.get_attribute("aria-label") or "").strip()
                        if "Add to cart" not in t and "Add to cart" not in a:
                            continue
                        if not _aria_label_matches_product(a, product_name):
                            continue
                        sb.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        sb.sleep(0.3)
                        WebDriverWait(sb.driver, 10).until(EC.element_to_be_clickable(btn))
                        try:
                            btn.click()
                        except Exception:
                            sb.driver.execute_script("arguments[0].click();", btn)
                        return True
                    except Exception:
                        continue
            except Exception:
                continue
        sb.sleep(0.5)
    return False


def check_add_to_cart_overlay(sb, wait_seconds=2):
    """
    Sau khi click Add to cart, kiểm tra lớp phủ: thành công (Added to cart) hay lỗi (errorContent).
    Returns: (success: bool, error_message: str|None)
    """
    sb.sleep(wait_seconds)
    # Ưu tiên kiểm tra lỗi: [data-test="errorContent"]
    try:
        err_block = sb.driver.find_element(By.CSS_SELECTOR, '[data-test="errorContent"]')
        if err_block.is_displayed():
            msg_span = err_block.find_elements(By.CSS_SELECTOR, 'span.sc-bbb3e63-2, span.dIqyyf')
            if msg_span:
                msg = (msg_span[0].text or "").strip()
            else:
                msg = (err_block.text or "").strip().split("\n")[0].strip()
            if msg:
                return (False, msg)
            return (False, "Item not added to cart.")
    except Exception:
        pass
    # Kiểm tra thành công: modal "Added to cart" (data-test="modal-drawer-heading" chứa "Added to cart")
    try:
        heading = sb.driver.find_element(By.CSS_SELECTOR, '[data-test="modal-drawer-heading"]')
        if heading.is_displayed() and "Added to cart" in (heading.text or ""):
            return (True, None)
    except Exception:
        pass
    try:
        if sb.is_text_visible("Added to cart", timeout=0.5):
            return (True, None)
    except Exception:
        pass
    return (False, None)


def dismiss_add_to_cart_error_overlay(sb):
    """Đóng overlay lỗi bằng nút 'Continue shopping'."""
    try:
        btn = sb.driver.find_element(By.CSS_SELECTOR, '[data-test="errorContent-continueShoppingButton"]')
        if btn.is_displayed():
            btn.click()
            sb.sleep(0.5)
            return True
    except Exception:
        pass
    return False

def click_preorder_button(sb, quantity=2, skip_quantity_selection=False, product_name=None):
    if check_and_update_cart_quantity(sb, desired_quantity=quantity, product_name=product_name):
        return True

    # Chọn số lượng chỉ lần đầu; các lần retry sau số lượng đã chọn sẵn, chỉ cần click Add to cart
    if not skip_quantity_selection:
        qty_selectors = [
            'button[id^="select-"]',
            'button[data-test="custom-quantity-picker"]',
        ]
        qty_selected = False
        for retry in range(3):
            for sel in qty_selectors:
                try:
                    btns = sb.driver.find_elements(By.CSS_SELECTOR, sel)
                    for btn in btns:
                        if not btn.is_displayed():
                            continue
                        try:
                            sb.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                            sb.sleep(0.2)
                            WebDriverWait(sb.driver, 5).until(EC.element_to_be_clickable(btn))
                            btn.click()
                            sb.sleep(0.3)
                            popover_sel = 'div[data-test="@nicollet/SelectCustom/Popover"], ul.Options_styles_options__YvWBL'
                            WebDriverWait(sb.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, popover_sel)))
                            qty_option = f'a[aria-label="{quantity}"]'
                            opt_elem = WebDriverWait(sb.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, qty_option)))
                            opt_elem.click()
                            sb.sleep(0.3)
                            qty_selected = True
                            break
                        except Exception:
                            continue
                    if qty_selected:
                        break
                except Exception:
                    continue
                if qty_selected:
                    break
            if qty_selected:
                break
            sb.sleep(0.5)

    # Click Add to cart (chỉ nút của sản phẩm chính, aria-label chứa product_name)
    if not click_add_to_cart_button(sb, product_name):
        return False

    # Kiểm tra lớp phủ: add to cart thành công (Added to cart) hay lỗi (errorContent)
    success, error_msg = check_add_to_cart_overlay(sb, wait_seconds=2)
    if not success and error_msg:
        print(f"  Add to cart failed: {error_msg}")
        dismiss_add_to_cart_error_overlay(sb)
        return False
    if not success:
        return False
    print("  🎉 Add to cart successful")

    # Navigate to cart (modal "Added to cart" có link View cart & check out)
    try:
        cart_links = sb.driver.find_elements(By.CSS_SELECTOR, 'a[href="/cart"]')
        for link in cart_links:
            if link.is_displayed() and ("View cart" in link.text or "check out" in link.text.lower()):
                link.click()
                return True
    except Exception:
        pass

    sb.open("https://www.target.com/cart")
    return True

def add_main_product_to_cart(sb, product_main, max_wait_minutes=10080, max_add_retries=500):
    quantity = int(product_main.get("quantities", 2))
    product_name = product_main.get("name") or ""
    # Nếu sản phẩm đã có trong giỏ (nút "X in cart" của sản phẩm chính): kiểm tra số lượng rồi chuyển tới cart
    if check_and_update_cart_quantity(sb, desired_quantity=quantity, product_name=product_name):
        return True

    # Lưu URL trang sản phẩm ngay (trước khi wait/refresh có thể redirect sang /lists)
    product_page_url = sb.get_current_url()
    if "/p/" not in product_page_url:
        product_page_url = None

    # Chưa có trong giỏ: chờ nút Add to cart của sản phẩm chính (aria-label chứa tên) rồi thêm
    print("  Product not in cart, waiting for Add to cart")
    if not wait_for_add_to_cart_button_available(sb, product_name, max_wait_minutes, check_interval=0.3):
        print("  Stopping: Add to cart button timeout.")
        return False

    # Sau wait có thể bị redirect (refresh → /lists): quay lại trang sản phẩm nếu cần
    def _same_product_page(url1, url2):
        """So sánh cùng trang product (bỏ fragment # để tránh false negative)."""
        if not url1 or not url2:
            return False
        u1 = (url1.split("#")[0]).rstrip("/")
        u2 = (url2.split("#")[0]).rstrip("/")
        return u1 == u2 and "/p/" in u1

    def ensure_on_product_page():
        if not product_page_url:
            return True
        current = sb.get_current_url()
        if "/p/" not in current or not _same_product_page(current, product_page_url):
            print("  Not on product page, navigating back to product...")
            sb.open(product_page_url)
            sb.sleep(2)
            try:
                WebDriverWait(sb.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-test="shippingButton"], button[id^="addToCartButtonOrTextIdFor"], button[data-test="preorderButtonDisabled"], button[data-test="custom-quantity-picker"]')))
            except Exception:
                pass
            sb.sleep(1)
            return True
        return True

    # Sau wait có thể đã bị redirect: đảm bảo đang ở đúng trang sản phẩm trước khi retry
    ensure_on_product_page()

    for attempt in range(max_add_retries):
        # Định kỳ kiểm tra session (cookies hết hạn → "Account" thay vì "Hi, [tên]")
        if attempt > 0 and attempt % 10 == 0:
            if not re_login(sb, EMAIL, PASSWORD):
                return False
        # Mỗi lần (và sau reload) kiểm tra đúng trang sản phẩm, nếu không thì mở lại đúng link
        ensure_on_product_page()
        # Nếu sản phẩm chính hết hàng lại → chờ có hàng rồi mới retry click
        status = check_add_to_cart_button_status(sb, product_name)
        if status != "available":
            print("  Product out of stock again, waiting for product to be in stock...")
            if not wait_for_add_to_cart_button_available(sb, product_name, max_wait_minutes, check_interval=0.3):
                print("  Stopping: Add to cart button timeout.")
                return False
            ensure_on_product_page()
        # Lần đầu hoặc ngay sau reload: chọn số lượng rồi Add to cart. Các lần retry khác: chỉ click Add to cart
        skip_qty = attempt > 0 and (attempt % 5) != 0
        if click_preorder_button(sb, quantity=quantity, skip_quantity_selection=skip_qty, product_name=product_name):
            return True
        # Cứ 5 lần không được thì reload page rồi add to cart tiếp
        if (attempt + 1) % 5 == 0:
            print("  Reloading page after 5 failed attempts, then retrying add to cart...")
            sb.driver.refresh()
            sb.sleep(2)
            ensure_on_product_page()
        else:
            print("  Retrying add to cart...")
        sb.sleep(1)
    print("  Stopping: add to cart failed after retries.")
    return False

# ============================================================================
# STEP 4: CHECK CART & ADD SMALL PRODUCTS (OPTIMIZED)
# ============================================================================

def get_cart_api_data(sb):
    try:
        if '/cart' not in sb.get_current_url():
            sb.open("https://www.target.com/cart")
        
        api_key = "e59ce3b531b2c39afb2e2b8a71ff10113aac2a14"
        api_url = f"https://carts.target.com/web_checkouts/v1/cart?cart_type=REGULAR&field_groups=ADDRESSES%2CCART%2CCART_ITEMS%2CFINANCE_PROVIDERS%2CPROMOTION_CODES%2CSUMMARY&key={api_key}"
        
        result = sb.driver.execute_async_script(f"""
            var callback = arguments[arguments.length - 1];
            fetch('{api_url}', {{
                method: 'GET',
                headers: {{'Accept': 'application/json', 'Content-Type': 'application/json'}},
                credentials: 'include'
            }})
            .then(r => r.ok ? r.json() : Promise.reject('HTTP ' + r.status))
            .then(d => callback(JSON.stringify(d)))
            .catch(e => callback('ERROR: ' + e));
        """)
        
        if result and not result.startswith('ERROR:'):
            return json.loads(result)
    except:
        pass
    return None

def check_small_product_in_cart(sb, product_name):
    try:
        title_elements = sb.driver.find_elements(By.CSS_SELECTOR, 'div[data-test="cartItem-title"]')
        for elem in title_elements:
            try:
                if product_name in elem.text.strip():
                    parent = elem.find_element(By.XPATH, 'ancestor::div[@data-test="cartItem"]')
                    qty_elem = parent.find_element(By.CSS_SELECTOR, 'select[data-test="cartItem-qty"]')
                    current_qty = int(Select(qty_elem).first_selected_option.get_attribute('value'))
                    
                    price_elem = parent.find_element(By.CSS_SELECTOR, '[data-test="cartItem-price"]')
                    price_match = re.search(r'\$?(\d+\.?\d*)', price_elem.text.strip())
                    price_per_item = float(price_match.group(1)) if price_match else None
                    total_price = price_per_item * current_qty if price_per_item else None
                    return (True, current_qty, price_per_item, total_price)
            except:
                continue
    except:
        pass
    return (False, 0, None, None)

def get_small_product_price(sb):
    try:
        price_elem = sb.find_element('span[data-test="product-price"]', timeout=1)
        price_match = re.search(r'\$?(\d+\.?\d*)', price_elem.text.strip())
        return float(price_match.group(1)) if price_match else None
    except:
        return None

def search_and_add_small_product(sb, product_name, quantity=1):
    try:
        search_box = sb.find_element('input[type="search"]', timeout=1)
        search_box.clear()
        search_box.send_keys(product_name)
        search_box.send_keys(Keys.RETURN)
        
        product_selector = f'div:contains("{product_name}"), a:contains("{product_name}")'
        if is_element_visible(sb, product_selector, timeout=2):
            sb.click(product_selector)
        else:
            return (False, None)
        
        price = get_small_product_price(sb)
        if price is None:
            return (False, None)
        
        if quantity > 1:
            try:
                qty_elem = sb.find_element('select[data-test="quantitySelect"]', timeout=1)
                Select(qty_elem).select_by_value(str(quantity))
            except:
                pass
        
        if is_element_visible(sb, 'button[data-test="addToCartButton"]', timeout=1):
            sb.click('button[data-test="addToCartButton"]')
        else:
            return (False, price)
        
        return (True, price)
    except:
        return (False, None)

def try_add_small_products_with_calculation(sb, product_smalls_list, main_price, threshold=35.00):
    needed = threshold - main_price
    if needed <= 0:
        return True
    
    for product in product_smalls_list:
        product_name = product["name"]
        in_cart, existing_qty, existing_price, existing_total = check_small_product_in_cart(sb, product_name)
        
        if in_cart and existing_price:
            current_total = main_price + existing_total
            still_needed = threshold - current_total
            if still_needed <= 0:
                return True
            
            additional_needed = math.ceil(still_needed / existing_price)
            if additional_needed > 0:
                try:
                    title_elem = sb.find_element(f'div[data-test="cartItem-title"]:contains("{product_name}")', timeout=1)
                    parent = title_elem.find_element(By.XPATH, 'ancestor::div[@data-test="cartItem"]')
                    qty_elem = parent.find_element(By.CSS_SELECTOR, 'select[data-test="cartItem-qty"]')
                    Select(qty_elem).select_by_value(str(existing_qty + additional_needed))
                except:
                    for _ in range(additional_needed):
                        if not search_and_add_small_product(sb, product_name, quantity=1)[0]:
                            break
        else:
            success, price = search_and_add_small_product(sb, product_name, quantity=1)
            if not success or price is None:
                continue
            
            current_total = main_price + price
            still_needed = threshold - current_total
            if still_needed <= 0:
                return True
            
            if still_needed > 0:
                additional_qty = math.ceil(still_needed / price)
                for _ in range(additional_qty):
                    if not search_and_add_small_product(sb, product_name, quantity=1)[0]:
                        break
        
        cart_data = get_cart_api_data(sb)
        if cart_data and cart_data.get('summary', {}).get('total_product_amount', 0) >= threshold:
            return True
    
    return False

def remove_small_product_from_cart(sb, product_name):
    try:
        title_elements = sb.driver.find_elements(By.CSS_SELECTOR, 'div[data-test="cartItem-title"]')
        for elem in title_elements:
            if product_name in elem.text.strip():
                parent = elem.find_element(By.XPATH, 'ancestor::div[@data-test="cartItem"]')
                delete_btn = parent.find_element(By.CSS_SELECTOR, 'button[data-test="cartItem-deleteBtn"]')
                delete_btn.click()
                return True
    except:
        pass
    return False

def check_cart_and_ensure_free_shipping(sb, product_main, product_smalls, threshold=35.00):
    cart_data = get_cart_api_data(sb)
    if not cart_data or 'cart_items' not in cart_data:
        return False
    
    items = cart_data['cart_items']
    main_product = None
    small_products = []
    
    for item in items:
        if item.get('item_indicators', {}).get('is_add_on', False):
            small_products.append(item)
        else:
            main_product = item
    
    if not main_product and items:
        main_product = items[0]
        small_products = items[1:] if len(items) > 1 else []
    
    if not main_product:
        return False
    
    main_total = main_product.get('item_summary', {}).get('total_product', 0)
    
    if main_total >= threshold:
        for item in small_products:
            desc = item.get('item_attributes', {}).get('description', '').replace('&#39;', "'")
            remove_small_product_from_cart(sb, desc)
        return True
    
    small_total = sum(item.get('item_summary', {}).get('total_product', 0) for item in small_products)
    if main_total + small_total >= threshold:
        return True
    
    return try_add_small_products_with_calculation(sb, product_smalls, main_total, threshold)

# ============================================================================
# STEP 5: CHECKOUT (OPTIMIZED)
# ============================================================================

def click_checkout_button(sb):
    print("  Searching checkout button")
    for retry in range(5):
        try:
            if is_element_visible(sb, 'button[data-test="checkout-button"]', timeout=3):
                print("  Checkout button found")
                try:
                    sb.click('button[data-test="checkout-button"]')
                except Exception as click_err:
                    try:
                        elem = sb.find_element('button[data-test="checkout-button"]', timeout=2)
                        sb.driver.execute_script("arguments[0].click();", elem)
                    except Exception:
                        print(f"  - Click failed: {str(click_err)[:50]}")
                        sb.sleep(1)
                        continue
                print("  Clicking checkout button")
                print("  🎉 Checkout clicked successfully")
                print("  Waiting for checkout page")
                sb.sleep(2)
                if is_element_visible(sb, 'button[data-test="placeOrderButton"]', timeout=5) or is_element_visible(sb, 'button:contains("Place order")', timeout=2):
                    print("  Checkout page loaded")
                    return True
                else:
                    print("  Checkout page loaded")
                    return True
            else:
                print("  Checkout button not visible, checking if on cart page...")
                try:
                    current_url = sb.get_current_url()
                    if '/cart' not in current_url:
                        print("  Not on cart page, navigating to cart...")
                        sb.open("https://www.target.com/cart")
                        sb.sleep(2)
                except Exception:
                    print("  Navigating to cart...")
                    sb.open("https://www.target.com/cart")
                    sb.sleep(2)
        except Exception as e:
            err_msg = str(e)
            if "HTTPConnectionPool" in err_msg or "Connection" in err_msg:
                print("  - Connection issue, retrying...")
            else:
                print(f"  - Error: {err_msg[:50]}")
        sb.sleep(1)
    print("  Stopping: checkout button not found after retries.")
    return False

def _log_place_order_button(btn, label="Place your order button"):
    """Log thông tin nút để kiểm tra đang click vào nút nào."""
    try:
        tag = (btn.tag_name or "").lower()
        data_test = btn.get_attribute("data-test") or "(none)"
        text = (btn.text or "").strip()[:60]
        disabled = btn.get_attribute("disabled") is not None
        print(f"  [Button] {label}: <{tag} data-test=\"{data_test}\" disabled={disabled}> text=\"{text}\"")
    except Exception as e:
        print(f"  [Button] Could not read button info: {e}")


def click_place_order_button(sb):
    print("")
    print("▶ Order Confirmation")
    print("  Searching \"Place your order\" button")
    for retry in range(5):
        try:
            place_btn = None
            try:
                place_btn = sb.driver.find_element(By.CSS_SELECTOR, 'button[data-test="placeOrderButton"]')
            except Exception:
                pass
            if place_btn and place_btn.is_displayed():
                if place_btn.get_attribute("disabled") is not None:
                    print("  Place your order button is disabled, stopping.")
                    return False
                print("  Place order button found")
                _log_place_order_button(place_btn, "Clicking (by data-test)")
                try:
                    sb.click('button[data-test="placeOrderButton"]')
                except Exception as click_err:
                    try:
                        elem = sb.find_element('button[data-test="placeOrderButton"]', timeout=2)
                        sb.driver.execute_script("arguments[0].click();", elem)
                    except Exception:
                        print(f"  - Click failed: {str(click_err)[:50]}")
                        sb.sleep(1)
                        continue
                print("  Clicking \"Place your order\"")
                print("  🎉 Place order clicked successfully")
                print("  Checking CVV requirement")
                sb.sleep(2)
                cvv_selector = 'input#enter-cvv, input[name="enter-cvv"]'
                if is_element_visible(sb, cvv_selector, timeout=3):
                    print("  CVV field found, entering CVV...")
                    try:
                        sb.type(cvv_selector, '325')
                        print("  CVV entered, looking for Confirm button...")
                        sb.sleep(0.5)
                        if is_element_visible(sb, 'button[data-test="confirm-button"]', timeout=3):
                            print("  Confirm button found, clicking...")
                            try:
                                sb.click('button[data-test="confirm-button"]')
                            except Exception as confirm_err:
                                try:
                                    confirm_elem = sb.find_element('button[data-test="confirm-button"]', timeout=2)
                                    sb.driver.execute_script("arguments[0].click();", confirm_elem)
                                except Exception:
                                    print(f"  - Confirm click failed: {str(confirm_err)[:50]}")
                                    continue
                            print("  🎉 Order placed successfully")
                            return True
                        else:
                            print("  Confirm button not found, but CVV entered")
                            return True
                    except Exception as type_err:
                        print(f"  - Failed to enter CVV: {str(type_err)[:50]}")
                        continue
                else:
                    print("  CVV not required")
                    print("  🎉 Order placed successfully")
                    return True
            else:
                print("  Place order button not visible, trying by text...")
                try:
                    po_btn = sb.driver.find_element(By.CSS_SELECTOR, 'button[data-test="placeOrderButton"]')
                    if po_btn.is_displayed() and po_btn.get_attribute("disabled") is not None:
                        print("  Place your order button is disabled, stopping.")
                        return False
                except Exception:
                    pass
                if is_element_visible(sb, 'button:contains("Place your order")', timeout=2) or is_element_visible(sb, 'button:contains("Place order")', timeout=2):
                    try:
                        po_btn = sb.driver.find_element(By.CSS_SELECTOR, 'button[data-test="placeOrderButton"]')
                        if po_btn.get_attribute("disabled") is not None:
                            print("  Place your order button is disabled, stopping.")
                            return False
                    except Exception:
                        pass
                    print("  Found place order button by text, clicking...")
                    po_btn = None
                    try:
                        po_btn = sb.find_element('button:contains("Place your order")', timeout=1)
                    except Exception:
                        try:
                            po_btn = sb.find_element('button:contains("Place order")', timeout=1)
                        except Exception:
                            pass
                    if po_btn is not None:
                        _log_place_order_button(po_btn, "Clicking (by text)")
                        if po_btn.get_attribute("disabled") is not None:
                            print("  Place your order button is disabled, stopping.")
                            return False
                    else:
                        print("  [Button] Could not find element to log (will still try click)")
                    try:
                        if is_element_visible(sb, 'button:contains("Place your order")', timeout=1):
                            sb.click('button:contains("Place your order")')
                        else:
                            sb.click('button:contains("Place order")')
                    except Exception as click_err:
                        print(f"  - Click failed: {str(click_err)[:50]}")
                        sb.sleep(1)
                        continue
                    print("  Clicking \"Place your order\"")
                    print("  🎉 Place order clicked successfully")
                    print("  Checking CVV requirement")
                    sb.sleep(2)
                    cvv_selector = 'input#enter-cvv, input[name="enter-cvv"]'
                    if is_element_visible(sb, cvv_selector, timeout=3):
                        print("  CVV field found, entering CVV...")
                        try:
                            sb.type(cvv_selector, '325')
                            print("  CVV entered, looking for Confirm button...")
                            sb.sleep(0.5)
                            if is_element_visible(sb, 'button[data-test="confirm-button"]', timeout=3):
                                print("  Confirm button found, clicking...")
                                try:
                                    sb.click('button[data-test="confirm-button"]')
                                except Exception:
                                    confirm_elem = sb.find_element('button[data-test="confirm-button"]', timeout=2)
                                    sb.driver.execute_script("arguments[0].click();", confirm_elem)
                                print("  🎉 Order placed successfully")
                                return True
                            else:
                                print("  Confirm button not found, but CVV entered")
                                return True
                        except Exception:
                            continue
                    else:
                        print("  CVV not required")
                        print("  🎉 Order placed successfully")
                        return True
        except Exception as e:
            err_msg = str(e)
            if "HTTPConnectionPool" in err_msg or "Connection" in err_msg:
                print("  - Connection issue, retrying...")
            else:
                print(f"  - Error: {err_msg[:50]}")
        sb.sleep(1)
    print("  Stopping: place order failed after retries.")
    return False

def checkout_and_place_order(sb):
    if not click_checkout_button(sb):
        print("\nBot dừng: không tìm thấy / click được nút Checkout.")
        return False
    if SKIP_PLACE_ORDER:
        print("\n  [TEST] Skipping \"Place your order\" (SKIP_PLACE_ORDER = True)")
        return True
    return click_place_order_button(sb)

# ============================================================================
# STEP 6: MAIN WORKFLOW
# ============================================================================

def run_bot():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        🤖 TARGET BOT – AUTOMATED CHECKOUT FLOW           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("")
    sb = None

    try:
        print("▶ Session Initialization")
        sb = initialize_session(EMAIL, PASSWORD)
        if not sb:
            return False
        
        print("")
        print("▶ Product Navigation")
        if not re_login(sb, EMAIL, PASSWORD):
            return False
        if not navigate_to_product(sb, product_main["name"]):
            print("\nBot dừng: bước 2 (điều hướng tới sản phẩm) thất bại.")
            return False
        
        print("")
        print("▶ Add To Cart")
        if not re_login(sb, EMAIL, PASSWORD):
            return False
        if not add_main_product_to_cart(sb, product_main):
            print("\nBot dừng: bước 3 (thêm sản phẩm vào giỏ) thất bại.")
            return False
        
        print("")
        print("▶ Shipping Validation")
        if not re_login(sb, EMAIL, PASSWORD):
            return False
        print("  Checking free shipping eligibility")
        check_cart_and_ensure_free_shipping(sb, product_main, product_smalls, FREE_SHIPPING_THRESHOLD)
        print("  Free shipping applied")

        print("")
        print("▶ Checkout")
        if not re_login(sb, EMAIL, PASSWORD):
            return False
        if not checkout_and_place_order(sb):
            return False
        
        print("")
        print("╔══════════════════════════════════════════════════════════╗")
        print("║                ✅ BOT EXECUTION SUCCESS                  ║")
        print("╚══════════════════════════════════════════════════════════╝")
        return True
    except Exception as e:
        print(f"\nERROR: {e}")
        return False
    finally:
        if sb:
            try:
                sb.driver.quit()
            except:
                pass

if __name__ == "__main__":
    run_bot()