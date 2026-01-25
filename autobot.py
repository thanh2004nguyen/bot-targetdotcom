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
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

# Python standard library
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
product_main = {
    "name": "Pokémon Trading Card Game: Mega Evolutions- Phantasmal Flames 9-Pocket Portfolio",
    "quantities": "2"
}
product_smalls = [
    {"name": "Skittles Sour Candy, Chewy Fruit Candies Share Size Bag - 13.7oz"}
]
FREE_SHIPPING_THRESHOLD = 35.00

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

def check_if_logged_in(sb):
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
    return False

def auto_login(sb, email, password):
    try:
        if is_element_visible(sb, 'a[data-test="@web/AccountLink"]', timeout=1):
            sb.click('a[data-test="@web/AccountLink"]')
        else:
            sb.open("https://www.target.com/account")
    except:
        return False
    
    try:
        if is_element_visible(sb, 'button[data-test="accountNav-signIn"]', timeout=1):
            sb.click('button[data-test="accountNav-signIn"]')
        else:
            return False
    except:
        return False
    
    try:
        if is_element_visible(sb, 'input#username', timeout=2):
            sb.type('input#username', email)
        else:
            return False
    except:
        return False
    
    try:
        sb.click('button:contains("Continue")')
        sb.click('#password')
        sb.type('input[name="password"]', password)
        sb.click('button:contains("Sign in")')
    except:
        return False
    
    return check_if_logged_in(sb)

def login_to_target(sb, email, password):
    sb.uc_open_with_reconnect("https://www.target.com", reconnect_time=2)
    
    if not check_if_logged_in(sb):
        if not auto_login(sb, email, password):
            return False
    
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

def find_and_click_product(sb, product_name):
    selectors = [
        f'div[title="{product_name}"]',
        f'a[title="{product_name}"]',
        f'div:contains("{product_name}")',
        f'a:contains("{product_name}")'
    ]
    
    for selector in selectors:
        try:
            if is_element_visible(sb, selector, timeout=1):
                sb.click(selector)
                return True
        except:
            continue
    return False

def navigate_to_product(sb, product_name):
    if not click_account_menu(sb):
        return False
    if not click_lists_and_favorites(sb):
        return False
    if not find_and_click_product(sb, product_name):
        return False
    return True

# ============================================================================
# STEP 3: ADD MAIN PRODUCT TO CART (OPTIMIZED)
# ============================================================================

def check_add_to_cart_button_status(sb):
    # Fast check - no scrolling, no sleep
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="shippingButton"]')
        for button in buttons:
            try:
                if button.is_displayed() and button.is_enabled():
                    text = button.text.strip()
                    aria = button.get_attribute('aria-label') or ''
                    if "Add to cart" in text or "Add to cart" in aria:
                        return "available"
            except:
                continue
    except:
        pass
    
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[id^="addToCartButtonOrTextIdFor"]')
        for button in buttons:
            try:
                if button.is_displayed() and button.is_enabled() and button.get_attribute('disabled') is None:
                    text = button.text.strip()
                    aria = button.get_attribute('aria-label') or ''
                    if "Add to cart" in text or "Add to cart" in aria:
                        return "available"
            except:
                continue
    except:
        pass
    
    try:
        preorder = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="preorderButtonDisabled"]')
        for btn in preorder:
            if btn.is_displayed():
                return "disabled"
    except:
        pass
    
    return "not_found"

def wait_for_add_to_cart_button_available(sb, max_wait_minutes=10080, check_interval=0.3):
    max_wait_seconds = max_wait_minutes * 60
    start_time = time.time()
    refresh_interval = 5  # Reduced from 15s to 5s
    last_refresh_time = start_time
    
    while True:
        status = check_add_to_cart_button_status(sb)
        if status == "available":
            return True
        
        current_time = time.time()
        if current_time - last_refresh_time >= refresh_interval:
            try:
                sb.driver.refresh()
                last_refresh_time = current_time
            except:
                pass
        
        if int(current_time - start_time) >= max_wait_seconds:
            return False
        
        sb.sleep(check_interval)

def check_and_update_cart_quantity(sb, desired_quantity=2):
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="custom-quantity-picker"]')
        for button in buttons:
            try:
                if "in cart" in button.text.lower() and button.is_displayed():
                    try:
                        span = button.find_element(By.CSS_SELECTOR, 'span[aria-label*="in cart"]')
                        aria = span.get_attribute('aria-label')
                        qty_match = re.search(r'(\d+)\s+in\s+cart', aria, re.IGNORECASE)
                        current_qty = int(qty_match.group(1)) if qty_match else 1
                    except:
                        current_qty = 1
                    
                    if current_qty == desired_quantity:
                        sb.open("https://www.target.com/cart")
                        return True
                    
                    button.click()
                    qty_selector = f'a[aria-label="{desired_quantity}"]'
                    if is_element_visible(sb, qty_selector, timeout=0.5):
                        sb.click(qty_selector)
                    sb.open("https://www.target.com/cart")
                    return True
            except:
                continue
    except:
        pass
    return False

def click_add_to_cart_button(sb):
    # Optimized: single method, no sleep, fast click
    selectors = [
        ('button[data-test="shippingButton"]', 'data-test'),
        ('button[id^="addToCartButtonOrTextIdFor"]', 'id'),
    ]
    
    for selector, method in selectors:
        try:
            buttons = sb.driver.find_elements(By.CSS_SELECTOR, selector)
            for button in buttons:
                try:
                    if button.is_displayed() and button.is_enabled() and button.get_attribute('disabled') is None:
                        text = button.text.strip()
                        aria = button.get_attribute('aria-label') or ''
                        if "Add to cart" in text or "Add to cart" in aria:
                            button.click()
                            return True
                except:
                    continue
        except:
            continue
    return False

def click_preorder_button(sb, quantity=2):
    if check_and_update_cart_quantity(sb, desired_quantity=quantity):
        return True
    
    # Select quantity
    try:
        qty_selectors = ['button[id^="select-"]', 'button[data-test="custom-quantity-picker"]']
        for selector in qty_selectors:
            if is_element_visible(sb, selector, timeout=0.5):
                sb.click(selector)
                qty_option = f'a[aria-label="{quantity}"]'
                if is_element_visible(sb, qty_option, timeout=0.5):
                    sb.click(qty_option)
                break
    except:
        pass
    
    # Click Add to cart
    if not click_add_to_cart_button(sb):
        return False
    
    # Navigate to cart
    try:
        cart_links = sb.driver.find_elements(By.CSS_SELECTOR, 'a[href="/cart"]')
        for link in cart_links:
            if link.is_displayed() and ("View cart" in link.text or "check out" in link.text.lower()):
                link.click()
                return True
    except:
        pass
    
    sb.open("https://www.target.com/cart")
    return True

def add_main_product_to_cart(sb, product_main, max_wait_minutes=10080):
    if not wait_for_add_to_cart_button_available(sb, max_wait_minutes, check_interval=0.3):
        return False
    
    quantity = int(product_main.get("quantities", 2))
    if not click_preorder_button(sb, quantity=quantity):
        return False
    
    return True

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
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="checkout-button"]')
        for button in buttons:
            if button.is_displayed() and button.is_enabled():
                button.click()
                return True
    except:
        pass
    return False

def click_place_order_button(sb):
    # Optimized: single method, minimal sleep
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="placeOrderButton"]')
        for button in buttons:
            if button.is_displayed() and button.is_enabled():
                button.click()
                break
        else:
            all_buttons = sb.driver.find_elements(By.TAG_NAME, 'button')
            for button in all_buttons:
                text = button.text.strip().lower()
                if button.is_displayed() and button.is_enabled() and ("place your order" in text or "place order" in text):
                    button.click()
                    break
        
        # Wait for CVV field
        cvv_selector = 'input#enter-cvv, input[name="enter-cvv"]'
        if is_element_visible(sb, cvv_selector, timeout=5):
            sb.type(cvv_selector, '325')
            return True
    except:
        pass
    return False

def checkout_and_place_order(sb):
    if not click_checkout_button(sb):
        return False
    return click_place_order_button(sb)

# ============================================================================
# STEP 6: MAIN WORKFLOW
# ============================================================================

def run_bot():
    print("=" * 60)
    print("Starting Target Bot - Automated Purchase Workflow")
    print("=" * 60)
    sb = None
    
    try:
        print("\n[Step 1] Initializing session...")
        sb = initialize_session(EMAIL, PASSWORD)
        if not sb:
            return False
        
        print("\n[Step 2] Navigating to product...")
        if not navigate_to_product(sb, product_main["name"]):
            return False
        
        print("\n[Step 3] Adding main product to cart...")
        if not add_main_product_to_cart(sb, product_main):
            return False
        
        print("\n[Step 4] Ensuring free shipping...")
        check_cart_and_ensure_free_shipping(sb, product_main, product_smalls, FREE_SHIPPING_THRESHOLD)
        
        print("\n[Step 5] Proceeding to checkout...")
        if not checkout_and_place_order(sb):
            return False
        
        print("\n" + "=" * 60)
        print("SUCCESS: Bot completed successfully!")
        print("=" * 60)
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
