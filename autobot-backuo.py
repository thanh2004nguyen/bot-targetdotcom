print("Loading modules...")
print("Importing seleniumbase...")
from seleniumbase import SB
print("Importing other modules...")
import os
import sys
import time
import math
import re
import json
import html
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
print("All modules loaded successfully!")

# Login credentials
EMAIL = "abasto.ricky76@gmail.com"
PASSWORD = "@Hbpmott456!"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_element_visible_with_timeout(sb, selector, timeout=5):
    # Check if element is visible with timeout support
    try:
        sb.wait_for_element_visible(selector, timeout=timeout)
        return True
    except:
        return False

def is_text_visible_with_timeout(sb, text, timeout=5):
    # Check if text is visible with timeout support
    try:
        sb.wait_for_text_visible(text, timeout=timeout)
        return True
    except:
        return False

# Product configuration
product_main = {
    "name": "Pokémon Trading Card Game: Mega Evolutions- Phantasmal Flames 9-Pocket Portfolio",
    # "name": "It's Not Her (Target Exclusive) - by Mary Kubica (Hardcover)",
    # "sub_name": "It's Not Her Target Exclusive - by Mary Kubica Hardcover",
    "quantities": "2"
}
product_smalls = [
    {"name": "Skittles Sour Candy, Chewy Fruit Candies Share Size Bag - 13.7oz"}
]
FREE_SHIPPING_THRESHOLD = 35.00

# ============================================================================
# STEP 1: LOGIN AND INITIALIZE
# ============================================================================

def check_if_logged_in(sb):
    # Check if user is logged in
    try:
        if is_text_visible_with_timeout(sb, "Hi,", timeout=3):
            return True
    except:
        pass
    
    try:
        account_link = sb.find_element('a[data-test="@web/AccountLink"]', timeout=3)
        link_text = account_link.text.lower()
        if "sign in" in link_text or link_text == "account":
            return False
        if "hi," in link_text or len(link_text) > 10:
            return True
    except:
        pass
    
    try:
        cookies = sb.driver.get_cookies()
        for cookie in cookies:
            cookie_name = cookie.get('name', '').lower()
            if 'auth' in cookie_name or 'session' in cookie_name or 'token' in cookie_name:
                return True
    except:
        pass
    
    return False

def auto_login(sb, email, password):
    # Auto login function
    try:
        print("Clicking Account link to open sign-in overlay...")
        if is_element_visible_with_timeout(sb, 'a[data-test="@web/AccountLink"]', timeout=3):
            sb.click('a[data-test="@web/AccountLink"]')
            try:
                sb.wait_for_element_visible('button[data-test="accountNav-signIn"]', timeout=2)
            except:
                pass
        else:
            print("Account link not found, trying direct navigation...")
            sb.uc_open_with_reconnect("https://www.target.com/account", reconnect_time=2)
            try:
                sb.wait_for_element_visible('button[data-test="accountNav-signIn"]', timeout=2)
            except:
                pass
    except Exception as e:
        print(f"Error clicking Account link: {e}")
        return False
    
    try:
        print("Clicking 'Sign in or create account' button...")
        sign_in_button_selector = 'button[data-test="accountNav-signIn"]'
        if is_element_visible_with_timeout(sb, sign_in_button_selector, timeout=3):
            sb.click(sign_in_button_selector)
            try:
                sb.wait_for_element_visible('input#username', timeout=2)
            except:
                pass
        else:
            print("Sign in button not found in overlay.")
            return False
    except Exception as e:
        print(f"Error clicking Sign in button: {e}")
        return False
    
    try:
        print("Entering email...")
        if is_element_visible_with_timeout(sb, 'input#username', timeout=5):
            sb.type('input#username', email)
        else:
            print("Email input field not found.")
            return False
    except Exception as e:
        print(f"Error entering email: {e}")
        return False
    
    try:
        sb.click('button:contains("Continue")')
        try:
            sb.wait_for_element_visible('input[name="password"], #password', timeout=2)
        except:
            pass
    except Exception as e:
        print(f"Error clicking Continue: {e}")
        return False
    
    try:
        sb.click('#password')
    except Exception as e:
        print(f"Error selecting password option: {e}")
        return False
    
    try:
        sb.type('input[name="password"]', password)
    except Exception as e:
        print(f"Error entering password: {e}")
        return False
    
    try:
        sb.click('button:contains("Sign in")')
        try:
            sb.wait_for_element_visible('a[data-test="@web/AccountLink"]', timeout=3)
        except:
            pass
    except Exception as e:
        print(f"Error clicking Sign in: {e}")
        return False
    
    is_logged_in = check_if_logged_in(sb)
    return is_logged_in

def login_to_target(sb, email, password):
    # Login to Target - fresh login every time
    url = "https://www.target.com"
    print("Opening Target.com...")
    sb.uc_open_with_reconnect(url, reconnect_time=3)
    
    is_logged_in = check_if_logged_in(sb)
    if not is_logged_in:
        print("Logging in automatically...")
        is_logged_in = auto_login(sb, email, password)
        if not is_logged_in:
            print("ERROR: Auto-login failed. Please check credentials.")
            return False
    else:
        print("Already logged in.")
    
    print("Refreshing page to update UI...")
    try:
        sb.driver.refresh()
        try:
            sb.wait_for_element_present('a[data-test="@web/AccountLink"]', timeout=2)
        except:
            pass
    except Exception as e:
        print(f"Warning: Could not refresh page: {e}")
        try:
            sb.open("https://www.target.com")
            try:
                sb.wait_for_element_present('a[data-test="@web/AccountLink"]', timeout=2)
            except:
                pass
        except Exception as e2:
            print(f"Warning: Could not navigate: {e2}")
    
    return True

def initialize_session(email, password):
    # Initialize browser and login
    print("Opening browser (this may take a moment)...")
    sb = None
    sb_context = None
    
    try:
        sb_context = SB(uc=True, incognito=True)
        sb = sb_context.__enter__()
        if not hasattr(sb, '_context_manager'):
            sb._context_manager = sb_context
        print("Browser opened successfully!")
        
        try:
            current_url = sb.get_current_url()
            print(f"Browser is ready. Current URL: {current_url}")
        except Exception as e:
            print(f"Warning: Could not get current URL: {e}")
    except Exception as e:
        print(f"Error opening browser: {e}")
        print("Make sure Chrome browser is installed and up to date.")
        return None
    
    try:
        print("Logging in...")
        if not login_to_target(sb, email, password):
            print("Failed to login. Exiting.")
            try:
                if hasattr(sb, 'driver'):
                    sb.driver.quit()
                elif hasattr(sb, 'quit'):
                    sb.quit()
            except:
                pass
            return None
        
        print("Login successful! Starting bot workflow...")
        
        try:
            current_url = sb.get_current_url()
            print(f"Browser still open. Current URL: {current_url}")
        except Exception as e:
            print(f"ERROR: Browser was closed! {e}")
            return None
        
        return sb
    except Exception as e:
        print(f"Error during login: {e}")
        try:
            if hasattr(sb, 'driver'):
                sb.driver.quit()
            elif hasattr(sb, 'quit'):
                sb.quit()
        except:
            pass
        return None

# ============================================================================
# STEP 2: NAVIGATE TO LISTS & FAVORITES AND FIND PRODUCT
# ============================================================================

def click_account_menu(sb):
    # Click account link to open menu or navigate to account page
    
    selectors = [
        ('a[data-test="@web/AccountLink"]', 'AccountLink by data-test'),
        ('a#account-sign-in', 'AccountLink by ID'),
        ('a[href*="/account"]', 'AccountLink by href'),
    ]
    
    for selector, description in selectors:
        try:
            print(f"Trying to find account menu: {description}...")
            try:
                sb.wait_for_element_visible(selector, timeout=8)
                try:
                    element = sb.find_element(selector)
                    sb.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                except:
                    pass
                sb.click(selector)
                try:
                    sb.wait_for_element_visible('a[data-test="accountNav-listsAndFavorites"]', timeout=2)
                except:
                    pass
                print(f"Successfully clicked account menu using: {description}")
                return True
            except Exception as e:
                print(f"Element not found with {description}: {e}")
                continue
        except Exception as e:
            print(f"Failed with {description}: {e}")
            continue
    
    try:
        print("Trying to navigate directly to account page...")
        sb.open("https://www.target.com/account")
        try:
            sb.wait_for_element_visible('a[data-test="accountNav-listsAndFavorites"]', timeout=2)
        except:
            pass
        return True
    except Exception as e:
        print(f"Error navigating to account page: {e}")
        try:
            sb.driver.get("https://www.target.com/account")
            try:
                sb.wait_for_element_visible('a[data-test="accountNav-listsAndFavorites"]', timeout=2)
            except:
                pass
            return True
        except Exception as e2:
            print(f"Error with driver.get: {e2}")
    
    print("Could not find account menu.")
    return False

def click_lists_and_favorites(sb):
    # Click Lists & Favorites link
    try:
        if is_element_visible_with_timeout(sb, 'a[data-test="accountNav-listsAndFavorites"]', timeout=3):
            sb.click('a[data-test="accountNav-listsAndFavorites"]')
            try:
                sb.wait_for_element_present('div[title], a[title]', timeout=2)
            except:
                pass
            current_url = sb.get_current_url()
            if "/lists" in current_url:
                return True
    except Exception as e:
        print(f"Error clicking Lists & Favorites: {e}")
    
    print("Could not navigate to Lists & Favorites.")
    return False

def find_and_click_product(sb, product_name, sub_name=None):
    # Find and click product in list
    names_to_try = [product_name]
    if sub_name:
        names_to_try.append(sub_name)
    
    print(f"Searching for product: '{product_name}'" + (f" (also trying: '{sub_name}')" if sub_name else ""))
    
    for name in names_to_try:
        try:
            selector = f'div[title="{name}"]'
            if is_element_visible_with_timeout(sb, selector, timeout=3):
                sb.click(selector)
                try:
                    sb.wait_for_element_present('button[data-test="shippingButton"], button[data-test="preorderButtonDisabled"]', timeout=2)
                except:
                    pass
                return True
        except:
            pass
        
        try:
            selector = f'a[title="{name}"]'
            if is_element_visible_with_timeout(sb, selector, timeout=3):
                sb.click(selector)
                try:
                    sb.wait_for_element_present('button[data-test="shippingButton"], button[data-test="preorderButtonDisabled"]', timeout=2)
                except:
                    pass
                return True
        except:
            pass
        
        try:
            selector = f'div:contains("{name}")'
            if is_element_visible_with_timeout(sb, selector, timeout=3):
                sb.click(selector)
                try:
                    sb.wait_for_element_present('button[data-test="shippingButton"], button[data-test="preorderButtonDisabled"]', timeout=2)
                except:
                    pass
                return True
        except:
            pass
        
        try:
            selector = f'a:contains("{name}")'
            if is_element_visible_with_timeout(sb, selector, timeout=3):
                sb.click(selector)
                try:
                    sb.wait_for_element_present('button[data-test="shippingButton"], button[data-test="preorderButtonDisabled"]', timeout=2)
                except:
                    pass
                return True
        except:
            pass
    
    print(f"Could not find product: {product_name}" + (f" or {sub_name}" if sub_name else ""))
    return False

def verify_product_page(sb):
    # Verify product page loaded
    try:
        current_url = sb.get_current_url()
        if "/p/" in current_url:
            return True
    except:
        pass
    
    try:
        if is_element_visible_with_timeout(sb, 'button[data-test="shippingButton"]', timeout=3) or is_element_visible_with_timeout(sb, 'button[data-test="preorderButtonDisabled"]', timeout=3):
            return True
    except:
        pass
    
    return False

def navigate_to_product(sb, product_name, sub_name=None):
    # Main function to navigate to product
    if not click_account_menu(sb):
        return False
    
    if not click_lists_and_favorites(sb):
        return False
    
    if not find_and_click_product(sb, product_name, sub_name=sub_name):
        return False
    
    if not verify_product_page(sb):
        print("Product page may not have loaded correctly.")
        return False
    
    print(f"Successfully navigated to product: {product_name}")
    return True

# ============================================================================
# STEP 3: ADD MAIN PRODUCT TO CART (WITH POLLING)
# ============================================================================

def check_add_to_cart_button_status(sb):
    # Check Add to cart button status
    # Method 1: Find by data-test="shippingButton" (most reliable)
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="shippingButton"]')
        for button in buttons:
            try:
                # Scroll button into view
                sb.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", button)
                time.sleep(0.3)
                
                if button.is_displayed():
                    # Check if button is enabled (not disabled)
                    is_enabled = button.is_enabled()
                    button_text = button.text.strip()
                    aria_label = button.get_attribute('aria-label') or ''
                    
                    # Check if it's "Add to cart" button (not Preorder)
                    if is_enabled and ("Add to cart" in button_text or "Add to cart" in aria_label):
                        return "available"
            except Exception as e:
                continue
    except:
        pass
    
    # Method 2: Find by ID pattern "addToCartButtonOrTextIdFor" and text "Add to cart"
    try:
        buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[id^="addToCartButtonOrTextIdFor"]')
        for button in buttons:
            try:
                # Scroll button into view
                sb.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", button)
                time.sleep(0.3)
                
                if button.is_displayed() and button.is_enabled():
                    button_text = button.text.strip()
                    aria_label = button.get_attribute('aria-label') or ''
                    
                    # Check if it's "Add to cart" (not "Preorder")
                    if "Add to cart" in button_text or "Add to cart" in aria_label:
                        # Make sure it's not disabled
                        disabled_attr = button.get_attribute('disabled')
                        if disabled_attr is None:
                return "available"
            except:
                continue
    except:
        pass
    
    # Method 3: Try finding by text "Add to cart" in all buttons
    try:
        buttons = sb.driver.find_elements(By.TAG_NAME, 'button')
        for button in buttons:
            try:
                if button.is_displayed() and button.is_enabled():
                    button_text = button.text.strip()
                    aria_label = button.get_attribute('aria-label') or ''
                    disabled_attr = button.get_attribute('disabled')
                    
                    if ("Add to cart" in button_text or "Add to cart" in aria_label) and disabled_attr is None:
                        return "available"
            except:
                continue
    except:
        pass
    
    # Check for disabled Preorder button
    try:
        preorder_buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="preorderButtonDisabled"]')
        for button in preorder_buttons:
            try:
                if button.is_displayed():
            return "disabled"
            except:
                continue
    except:
        pass
    
    return "not_found"

def format_wait_time(seconds):
    # Format time for print message
    if seconds < 60:
        return f"{seconds}s"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    if not parts:
        return f"{seconds}s"
    
    return " ".join(parts)

def wait_for_add_to_cart_button_available(sb, max_wait_minutes=10080, check_interval=0.5):
    # Polling loop to wait for button available
    max_wait_seconds = max_wait_minutes * 60
    print_interval = 60
    start_time = time.time()
    last_print_time = start_time
    check_count = 0
    refresh_interval = 15
    last_refresh_time = start_time
    
    print("Monitoring Add to cart button... (Max wait: 7 days)")
    
    while True:
        check_count += 1
        current_time = time.time()
        elapsed_seconds = int(current_time - start_time)
        
        # Check button status BEFORE refresh to avoid missing it
        status = check_add_to_cart_button_status(sb)
        if status == "available":
            elapsed_formatted = format_wait_time(elapsed_seconds)
            print(f"Button available! Clicking... (Waited: {elapsed_formatted})")
            return True
        
        # Only refresh if button is not available and refresh interval passed
        if current_time - last_refresh_time >= refresh_interval:
            try:
                print("Refreshing page to check latest product status...")
                sb.driver.refresh()
                # Wait for page to load and button element to be ready
                try:
                    sb.wait_for_element_present('button[id^="addToCartButtonOrTextIdFor"], button[data-test="shippingButton"], button[data-test="preorderButtonDisabled"]', timeout=3)
                except:
                    pass
                last_refresh_time = current_time
            except Exception as e:
                print(f"Warning: Could not refresh page: {e}")
        
        if current_time - last_print_time >= print_interval:
            elapsed_formatted = format_wait_time(elapsed_seconds)
            print(f"Waiting... {elapsed_formatted} (Disabled)")
            last_print_time = current_time
        
        if elapsed_seconds >= max_wait_seconds:
            elapsed_formatted = format_wait_time(elapsed_seconds)
            print(f"Timeout: Button did not become available after {elapsed_formatted}")
            return False
        
        sb.sleep(check_interval)

def check_and_update_cart_quantity(sb, desired_quantity=2):
    # Check if product is already in cart and update quantity if needed
    try:
        in_cart_buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="custom-quantity-picker"]')
        for button in in_cart_buttons:
            try:
                button_text = button.text.strip()
                if "in cart" in button_text.lower() and button.is_displayed():
                    print(f"Product already in cart ({button_text}). Checking quantity...")
                    
                    # Extract current quantity from aria-label
                    try:
                        span_element = button.find_element(By.CSS_SELECTOR, 'span[aria-label*="in cart"]')
                        aria_label = span_element.get_attribute('aria-label')
                        qty_match = re.search(r'(\d+)\s+in\s+cart', aria_label, re.IGNORECASE)
                        current_qty = int(qty_match.group(1)) if qty_match else 1
                        print(f"Current quantity in cart: {current_qty}, desired: {desired_quantity}")
                    except:
                        current_qty = 1
                        print(f"Could not extract quantity, assuming 1")
                    
                    if current_qty == desired_quantity:
                        print(f"Quantity already correct ({desired_quantity}). Navigating to cart...")
                        sb.open("https://www.target.com/cart")
                        try:
                            sb.wait_for_element_present('div[data-test="cartItem"]', timeout=2)
                        except:
                            pass
                        return True
                    
                    # Click button to open dropdown
                    button.click()
                    try:
                        sb.wait_for_element_visible(f'a[aria-label="{desired_quantity}"], a[aria-label="{desired_quantity} - selected"]', timeout=1)
                    except:
                        pass
                    
                    # Select desired quantity
                    qty_option_selector = f'a[aria-label="{desired_quantity}"]'
                    if not is_element_visible_with_timeout(sb, qty_option_selector, timeout=1):
                        qty_option_selector = f'a[aria-label="{desired_quantity} - selected"]'
                    
                    if is_element_visible_with_timeout(sb, qty_option_selector, timeout=1):
                        sb.click(qty_option_selector)
                        print(f"Updated quantity from {current_qty} to {desired_quantity}")
                    else:
                        print(f"Could not find quantity option {desired_quantity}. Using current quantity.")
                    
                    # Navigate to cart
                    sb.open("https://www.target.com/cart")
                    try:
                        sb.wait_for_element_present('div[data-test="cartItem"]', timeout=2)
                    except:
                        pass
                    return True
            except Exception as e:
                print(f"Error processing in-cart button: {e}")
                continue
    except Exception as e:
        print(f"Error checking cart quantity: {e}")
    
    return False

def click_preorder_button(sb, quantity=2):
    # Select quantity and click Preorder button
    # First check if product is already in cart
    if check_and_update_cart_quantity(sb, desired_quantity=quantity):
        print("Product quantity updated. Verifying via XHR API...")
        cart_data = get_cart_api_data(sb)
        if cart_data and 'cart_items' in cart_data:
            items = cart_data['cart_items']
            if items:
                main_item = items[0]
                # Try different possible structures for quantity
                item_qty = None
                if 'quantity' in main_item:
                    if isinstance(main_item['quantity'], dict):
                        item_qty = main_item['quantity'].get('value', 0)
                    else:
                        item_qty = main_item['quantity']
                elif 'item_summary' in main_item and 'quantity' in main_item['item_summary']:
                    item_qty = main_item['item_summary']['quantity']
                
                if item_qty is not None:
                    print(f"Verified: Main product quantity in cart = {item_qty}")
                    if item_qty == quantity:
                        print("Quantity verified correctly!")
                        return True
                    else:
                        print(f"Warning: Quantity mismatch. Expected {quantity}, found {item_qty}")
                else:
                    print("Could not extract quantity from API, but product is in cart")
        return True
    
    try:
        print(f"Selecting quantity: {quantity}...")
        qty_selectors = [
            'button[id^="select-"]',
            'button:contains("Qty")',
            'button[aria-expanded="false"]:has(span:contains("Qty"))',
            'button[data-test="custom-quantity-picker"]'
        ]
        qty_button_found = False
        
        for selector in qty_selectors:
            try:
                if is_element_visible_with_timeout(sb, selector, timeout=1):
                    sb.click(selector)
                    try:
                        sb.wait_for_element_visible(f'a[aria-label="{quantity}"], a[aria-label="{quantity} - selected"]', timeout=0.5)
                    except:
                        pass
                    qty_button_found = True
                    print("Quantity dropdown opened.")
                    break
            except:
                continue
        
        if not qty_button_found:
            print("Quantity selector not found. Proceeding with default quantity.")
        else:
            try:
                qty_option_selector = f'a[aria-label="{quantity}"]'
                if not is_element_visible_with_timeout(sb, qty_option_selector, timeout=1):
                    qty_option_selector = f'a[aria-label="{quantity} - selected"]'
                
                if is_element_visible_with_timeout(sb, qty_option_selector, timeout=1):
                    sb.click(qty_option_selector)
                    print(f"Quantity {quantity} selected.")
                else:
                    print(f"Quantity option {quantity} not found. Using default.")
            except Exception as e:
                print(f"Error selecting quantity: {e}")
    except Exception as e:
        print(f"Error with quantity selector: {e}")
    
    try:
        print("Clicking Add to cart button...")
        add_to_cart_clicked = False
        
        # Method 1: Find by data-test="shippingButton" (most reliable - priority)
        try:
            shipping_buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="shippingButton"]')
            for button in shipping_buttons:
                try:
                    if button.is_displayed():
                        # Scroll into view
                        sb.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", button)
                        time.sleep(0.3)
                        
                        # Check if enabled and has "Add to cart" text
                        is_enabled = button.is_enabled()
                        button_text = button.text.strip()
                        aria_label = button.get_attribute('aria-label') or ''
                        disabled_attr = button.get_attribute('disabled')
                        
                        if is_enabled and disabled_attr is None and ("Add to cart" in button_text or "Add to cart" in aria_label):
                            button.click()
                            try:
                                sb.wait_for_element_visible('a[href="/cart"]', timeout=1)
                            except:
                                pass
                            print("Add to cart button clicked (by data-test='shippingButton').")
                            add_to_cart_clicked = True
                            break
                except Exception as e:
                    continue
        except:
            pass
        
        # Method 2: Find by id containing "addToCartButtonOrTextIdFor" and text "Add to cart"
        if not add_to_cart_clicked:
            try:
                buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[id^="addToCartButtonOrTextIdFor"]')
                for button in buttons:
                    try:
                        if button.is_displayed():
                            # Scroll into view
                            sb.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", button)
                            time.sleep(0.3)
                            
                            is_enabled = button.is_enabled()
                            button_text = button.text.strip()
                            aria_label = button.get_attribute('aria-label') or ''
                            disabled_attr = button.get_attribute('disabled')
                            
                            if is_enabled and disabled_attr is None and ("Add to cart" in button_text or "Add to cart" in aria_label):
                                button.click()
                                try:
                                    sb.wait_for_element_visible('a[href="/cart"]', timeout=1)
                                except:
                                    pass
                                print("Add to cart button clicked (by id).")
                                add_to_cart_clicked = True
                                break
                    except:
                        continue
            except:
                pass
        
        # Method 3: Find by text "Add to cart" in all buttons
        if not add_to_cart_clicked:
            try:
                all_buttons = sb.driver.find_elements(By.TAG_NAME, 'button')
                for button in all_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip()
                            aria_label = button.get_attribute('aria-label') or ''
                            disabled_attr = button.get_attribute('disabled')
                            
                            if disabled_attr is None and ("Add to cart" in button_text or "Add to cart" in aria_label):
                                # Scroll into view
                                sb.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", button)
                                time.sleep(0.3)
                                
                                button.click()
                                try:
                                    sb.wait_for_element_visible('a[href="/cart"]', timeout=1)
                                except:
                                    pass
                                print("Add to cart button clicked (by text).")
                                add_to_cart_clicked = True
                                break
                    except:
                        continue
            except:
                pass
        
        if not add_to_cart_clicked:
            print("Add to cart button not found or not enabled.")
            return False
        
        try:
            print("Looking for 'View cart & check out' link in overlay...")
            try:
                cart_links = sb.driver.find_elements(By.CSS_SELECTOR, 'a[href="/cart"]')
                for link in cart_links:
                    if link.is_displayed() and ("View cart" in link.text or "check out" in link.text.lower()):
                        link.click()
                        try:
                            sb.wait_for_element_present('div[data-test="cartItem"]', timeout=1)
                        except:
                            pass
                        print("Check out link clicked (fast method).")
                        return True
            except:
                pass
            
            checkout_link_selectors = [
                'a:contains("View cart & check out")',
                'a:contains("View cart")',
                'a[href="/cart"]',
                'a[href*="/cart"]'
            ]
            checkout_clicked = False
            
            for selector in checkout_link_selectors:
                try:
                    if is_element_visible_with_timeout(sb, selector, timeout=2):
                        sb.click(selector)
                        try:
                            sb.wait_for_element_present('div[data-test="cartItem"]', timeout=1)
                        except:
                            pass
                        print(f"Check out link clicked using: {selector}")
                        checkout_clicked = True
                        break
                except:
                    continue
            
            if not checkout_clicked:
                print("Check out link not found in overlay. May need to click Cart icon instead.")
                return False
            
            return True
        except Exception as e:
            print(f"Error clicking Check out link in overlay: {e}")
            return False
    except Exception as e:
        print(f"Error clicking Add to cart button: {e}")
        return False

def add_main_product_to_cart(sb, product_main, max_wait_minutes=10080, check_interval=0.5):
    # Main function to add main product to cart
    if not wait_for_add_to_cart_button_available(sb, max_wait_minutes, check_interval):
        return False
    
    quantity = int(product_main.get("quantities", 2))
    
    if not click_preorder_button(sb, quantity=quantity):
        print("Failed to click Add to cart button or checkout.")
        return False
    
    try:
        sb.wait_for_element_present('div[data-test="cartItem"]', timeout=2)
    except:
        pass
    return True

# ============================================================================
# STEP 4: CHECK CART & ADD SMALL PRODUCTS (FREE SHIPPING LOGIC)
# ============================================================================

def get_cart_api_data(sb):
    # Get cart data from XHR API (no reload unless fetch fails)
    try:
        try:
            current_url = sb.get_current_url()
        except Exception as e:
            print(f"✗ Browser is not accessible: {e}")
            return None
        
        if '/cart' not in current_url:
            print("⚠ Not on cart page, navigating to cart...")
            sb.open("https://www.target.com/cart")
            try:
                sb.wait_for_element_present('div[data-test="cartItem"]', timeout=2)
            except:
                pass
        
        api_key = None
        try:
            page_key = sb.driver.execute_script("""
                var scripts = document.getElementsByTagName('script');
                for (var i = 0; i < scripts.length; i++) {
                    var match = scripts[i].innerHTML.match(/key=([a-f0-9]{40})/);
                    if (match) return match[1];
                }
                return null;
            """)
            if page_key:
                api_key = page_key
        except:
            pass
        
        if not api_key:
            api_key = "e59ce3b531b2c39afb2e2b8a71ff10113aac2a14"
        
        api_url = f"https://carts.target.com/web_checkouts/v1/cart?cart_type=REGULAR&field_groups=ADDRESSES%2CCART%2CCART_ITEMS%2CFINANCE_PROVIDERS%2CPROMOTION_CODES%2CSUMMARY&key={api_key}"
        
        cart_data = None
        try:
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
                cart_data = json.loads(result)
                print("✓ Fetched cart data from XHR API")
            else:
                print("✗ Fetch failed, reloading and retrying...")
                sb.driver.refresh()
                try:
                    sb.wait_for_element_present('div[data-test="cartItem"]', timeout=2)
                except:
                    pass
                
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
                    cart_data = json.loads(result)
                    print("✓ Fetched cart data after reload")
                else:
                    print(f"✗ Still failed: {result}")
                    return None
        except Exception as e:
            print(f"✗ Error fetching cart data: {e}")
            return None
        
        return cart_data
    except Exception as e:
        print(f"✗ Error in get_cart_api_data: {e}")
        return None

def check_small_product_in_cart(sb, product_name):
    # Check if small product already exists in cart page
    try:
        title_elements = sb.driver.find_elements(By.CSS_SELECTOR, 'div[data-test="cartItem-title"]')
        title_element = None
        
        for elem in title_elements:
            try:
                text = elem.text.strip()
                if product_name in text:
                    title_element = elem
                    break
            except:
                continue
        
        if not title_element:
            title_selectors = [
                f'div[data-test="cartItem-title"]:contains("{product_name}")',
                f'span[data-test="cartItem-title"]:contains("{product_name}")'
            ]
            for selector in title_selectors:
                try:
                    if is_element_visible_with_timeout(sb, selector, timeout=3):
                        title_element = sb.find_element(selector, timeout=3)
                        break
                except:
                    continue
        
        if not title_element:
            return (False, 0, None, None)
        
        try:
            parent = title_element.find_element(By.XPATH, 'ancestor::div[@data-test="cartItem"]')
            try:
                qty_element = parent.find_element(By.CSS_SELECTOR, 'select[data-test="cartItem-qty"]')
            except:
                qty_element = parent.find_element(By.XPATH, './/select[@data-test="cartItem-qty"]')
            
            select = Select(qty_element)
            current_qty = int(select.first_selected_option.get_attribute('value'))
        except:
            current_qty = 1
        
        try:
            try:
                price_elements = parent.find_elements(By.CSS_SELECTOR, 'p[data-test="cartItem-price"]')
                if not price_elements:
                    price_elements = parent.find_elements(By.CSS_SELECTOR, 'span[data-test="cartItem-price"]')
                if not price_elements:
                    price_elements = parent.find_elements(By.CSS_SELECTOR, '[data-test="cartItem-price"]')
            except:
                try:
                    price_elements = parent.find_elements(By.XPATH, './/*[@data-test="cartItem-price"]')
                except:
                    price_elements = []
            
            if price_elements:
                price_text = price_elements[0].text.strip()
                price_match = re.search(r'\$?(\d+\.?\d*)', price_text)
                if price_match:
                    price_per_item = float(price_match.group(1))
                    total_price = price_per_item * current_qty
                    print(f"Product '{product_name}' already in cart: {current_qty} x ${price_per_item:.2f} = ${total_price:.2f}")
                    return (True, current_qty, price_per_item, total_price)
        except:
            pass
        
        print(f"Product '{product_name}' already in cart: quantity {current_qty} (price not found)")
        return (True, current_qty, None, None)
    except:
        pass
    
    return (False, 0, None, None)

def get_small_product_price(sb, product_name):
    # Get small product price from search results or product page
    try:
        price_selector = 'span[data-test="product-price"]'
        if is_element_visible_with_timeout(sb, price_selector, timeout=3):
            price_element = sb.find_element(price_selector, timeout=3)
            price_text = price_element.text.strip()
            price_match = re.search(r'\$?(\d+\.?\d*)', price_text)
            if price_match:
                return float(price_match.group(1))
    except:
        pass
    
    try:
        price_selectors = [
            'span[data-test="product-price"]',
            'span[class*="price"]',
            'div[class*="price"]'
        ]
        for selector in price_selectors:
            try:
                if is_element_visible_with_timeout(sb, selector, timeout=2):
                    price_element = sb.find_element(selector, timeout=2)
                    price_text = price_element.text.strip()
                    price_match = re.search(r'\$?(\d+\.?\d*)', price_text)
                    if price_match:
                        return float(price_match.group(1))
            except:
                continue
    except:
        pass
    
    return None

def search_and_add_small_product(sb, product_name, quantity=1):
    # Search and add small product with specific quantity
    try:
        search_selectors = [
            'input[type="search"]',
            'input[placeholder*="Search"]',
            'input[name*="search"]'
        ]
        search_box = None
        
        for selector in search_selectors:
            try:
                if is_element_visible_with_timeout(sb, selector, timeout=3):
                    search_box = sb.find_element(selector, timeout=3)
                    break
            except:
                continue
        
        if not search_box:
            print("Search box not found.")
            return (False, None)
        
        search_box.clear()
        search_box.send_keys(product_name)
        
        try:
            search_button = sb.find_element('button[type="submit"]', timeout=1)
            search_button.click()
        except:
            search_box.send_keys(Keys.RETURN)
        
        try:
            sb.wait_for_element_present('div:contains("' + product_name + '"), a:contains("' + product_name + '")', timeout=2)
        except:
            pass
        
        try:
            product_selector = f'div:contains("{product_name}")'
            if not is_element_visible_with_timeout(sb, product_selector, timeout=3):
                print(f"Product '{product_name}' not found in search results.")
                return (False, None)
            sb.click(product_selector)
            try:
                sb.wait_for_element_present('button[data-test="addToCartButton"], button:contains("Add to cart")', timeout=2)
            except:
                pass
        except:
            try:
                product_selector = f'a:contains("{product_name}")'
                if is_element_visible_with_timeout(sb, product_selector, timeout=3):
                    sb.click(product_selector)
                    try:
                        sb.wait_for_element_present('button[data-test="addToCartButton"], button:contains("Add to cart")', timeout=2)
                    except:
                        pass
                else:
                    return (False, None)
            except:
                return (False, None)
        
        price = get_small_product_price(sb, product_name)
        if price is None:
            print(f"Could not get price for product '{product_name}'.")
            return (False, None)
        
        if quantity > 1:
            try:
                qty_selectors = [
                    'select[data-test="quantitySelect"]',
                    'select[name*="quantity"]',
                    'input[type="number"][name*="quantity"]'
                ]
                qty_set = False
                
                for selector in qty_selectors:
                    try:
                        if is_element_visible_with_timeout(sb, selector, timeout=3):
                            qty_element = sb.find_element(selector, timeout=3)
                            if qty_element.tag_name == 'select':
                                select = Select(qty_element)
                                select.select_by_value(str(quantity))
                            else:
                                qty_element.clear()
                                qty_element.send_keys(str(quantity))
                            qty_set = True
                            break
                    except:
                        continue
                
                if not qty_set:
                    print(f"Could not set quantity to {quantity}. Using default quantity.")
            except Exception as e:
                print(f"Error setting quantity: {e}")
        
        try:
            add_button_selectors = [
                'button[data-test="addToCartButton"]',
                'button:contains("Add to cart")',
                'button:contains("Add")'
            ]
            added = False
            
            for selector in add_button_selectors:
                try:
                    if is_element_visible_with_timeout(sb, selector, timeout=2):
                        sb.click(selector)
                        try:
                            sb.wait_for_element_visible('a[href="/cart"]', timeout=1)
                        except:
                            pass
                        added = True
                        break
                except:
                    continue
            
            if not added:
                print("Add to cart button not found.")
                return (False, price)
        except Exception as e:
            print(f"Error clicking Add to cart: {e}")
            return (False, price)
        
        print(f"Added {quantity} x '{product_name}' (${price:.2f} each) to cart.")
        return (True, price)
    except Exception as e:
        print(f"Error searching and adding product: {e}")
        return (False, None)

def try_add_small_products_with_calculation(sb, product_main_name, product_smalls_list, main_price, threshold=35.00):
    # Try adding small products from backup list with calculation
    needed = threshold - main_price
    if needed <= 0:
        print("Free shipping threshold already met.")
        return True
    
    print(f"Need ${needed:.2f} more to reach free shipping threshold.")
    
    for product in product_smalls_list:
        product_name = product["name"]
        print(f"Trying product: {product_name}")
        
        in_cart, existing_qty, existing_price, existing_total = check_small_product_in_cart(sb, product_name)
        
        if in_cart:
            if existing_price is not None:
                current_cart_total = main_price + existing_total
                still_needed = threshold - current_cart_total
                if still_needed <= 0:
                    print(f"Free shipping threshold already met with existing {existing_qty} x {product_name}.")
                    return True
                
                additional_needed = math.ceil(still_needed / existing_price)
                if additional_needed > 0:
                    print(f"Product already in cart ({existing_qty} items). Need {additional_needed} more to reach threshold.")
                    try:
                        title_selectors = [
                            f'div[data-test="cartItem-title"]:contains("{product_name}")',
                            f'span[data-test="cartItem-title"]:contains("{product_name}")'
                        ]
                        title_element = None
                        
                        for selector in title_selectors:
                            try:
                                if is_element_visible_with_timeout(sb, selector, timeout=3):
                                    title_element = sb.find_element(selector, timeout=3)
                                    break
                            except:
                                continue
                        
                        if title_element:
                            parent = title_element.find_element('xpath=ancestor::div[@data-test="cartItem"]')
                            qty_element = parent.find_element('xpath=.//select[@data-test="cartItem-qty"]')
                            select = Select(qty_element)
                            new_qty = existing_qty + additional_needed
                            
                            try:
                                select.select_by_value(str(new_qty))
                                print(f"Updated quantity to {new_qty}")
                            except:
                                max_option = select.options[-1].get_attribute('value')
                                select.select_by_value(max_option)
                                print(f"Updated quantity to maximum available: {max_option}")
                    except Exception as e:
                        print(f"Could not update quantity in cart: {e}")
                        print("Trying to add via search instead...")
                        for i in range(additional_needed):
                            add_success, _ = search_and_add_small_product(sb, product_name, quantity=1)
                            if not add_success:
                                break
                else:
                    print(f"Product already in cart, no additional quantity needed.")
            else:
                print(f"Product already in cart but price not found. Verifying cart total...")
        else:
            search_success, price = search_and_add_small_product(sb, product_name, quantity=1)
            if not search_success or price is None:
                print(f"Product '{product_name}' not available or price not found. Trying next product.")
                continue
            
            current_total_after_add = main_price + price
            still_needed = threshold - current_total_after_add
            if still_needed <= 0:
                print("Free shipping threshold met with this product.")
                return True
            
            if still_needed > 0:
                additional_qty = math.ceil(still_needed / price)
                if additional_qty > 0:
                    print(f"Need {additional_qty} more of this product. Adding more...")
                    for i in range(additional_qty):
                        add_success, _ = search_and_add_small_product(sb, product_name, quantity=1)
                        if not add_success:
                            print(f"Failed to add additional quantity. Current quantity may be sufficient.")
                            break
        
        updated_cart_data = get_cart_api_data(sb)
        if updated_cart_data and 'summary' in updated_cart_data:
            final_subtotal = updated_cart_data['summary'].get('total_product_amount', 0)
            if final_subtotal >= threshold:
                print(f"Free shipping threshold met! Final subtotal: ${final_subtotal:.2f}")
                return True
            else:
                print(f"Threshold not met yet. Current subtotal: ${final_subtotal:.2f}")
        else:
            print("Could not verify cart total from XHR API")
    
    print("Failed to add any small products that meet the threshold.")
    return False

def remove_small_product_from_cart(sb, product_name):
    # Remove small product from cart if main product already meets threshold
    try:
        title_elements = sb.driver.find_elements(By.CSS_SELECTOR, 'div[data-test="cartItem-title"]')
        title_element = None
        
        for elem in title_elements:
            try:
                text = elem.text.strip()
                if product_name in text:
                    title_element = elem
                    break
            except:
                continue
        
        if not title_element:
            print(f"Product '{product_name}' not found in cart to remove.")
            return False
        
        try:
            parent = title_element.find_element(By.XPATH, 'ancestor::div[@data-test="cartItem"]')
            delete_button = None
            
            try:
                delete_button = parent.find_element(By.CSS_SELECTOR, 'button[data-test="cartItem-deleteBtn"]')
            except:
                try:
                    delete_button = parent.find_element(By.XPATH, './/button[@data-test="cartItem-deleteBtn"]')
                except:
                    try:
                        delete_button = parent.find_element(By.XPATH, f'.//button[contains(@aria-label, "{product_name}")]')
                    except:
                        pass
            
            if not delete_button:
                print(f"Delete button not found for '{product_name}'.")
                return False
            
            try:
                sb.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", delete_button)
            except:
                pass
            
            delete_button.click()
            try:
                sb.wait_for_element_not_visible(title_element, timeout=1)
            except:
                pass
            print(f"Removed '{product_name}' from cart.")
            return True
        except Exception as e:
            print(f"Could not remove product: {e}")
            return False
    except Exception as e:
        print(f"Error removing product: {e}")
        return False

def check_cart_and_ensure_free_shipping(sb, product_main, product_smalls, threshold=35.00):
    # Main function to check and ensure free shipping using XHR API
    cart_data = get_cart_api_data(sb)
    if not cart_data or 'cart_items' not in cart_data:
        print("Could not get cart data from XHR API. Skipping free shipping check.")
        print("WARNING: Free shipping threshold may not be met.")
        return False
    
    items = cart_data['cart_items']
    main_product = None
    small_products = []
    
    for item in items:
        is_add_on = item.get('item_indicators', {}).get('is_add_on', False)
        if is_add_on:
            small_products.append(item)
        else:
            main_product = item
    
    if not main_product and items:
        main_product = items[0]
        small_products = items[1:] if len(items) > 1 else []
    
    if not main_product:
        print("No main product found in cart.")
        return False
    
    main_total = main_product.get('item_summary', {}).get('total_product', 0)
    print(f"Main product total: ${main_total:.2f}")
    
    if main_total >= threshold:
        print(f"--> Sản phẩm main đã > ${threshold:.2f} xóa sản phẩm small")
        
        if small_products:
            for item in small_products:
                desc = item.get('item_attributes', {}).get('description', 'N/A')
                desc = desc.replace('&#39;', "'")
                print(f"Deleting {desc}")
                
                deleted = remove_small_product_from_cart(sb, desc)
                if deleted:
                    print(f"✓ Deleted: {desc}")
                else:
                    print(f"✗ Failed to delete: {desc}")
            print("Deleted")
        else:
            print("No small products to delete")
        return True
    
    small_total = sum(item.get('item_summary', {}).get('total_product', 0) for item in small_products)
    combined_total = main_total + small_total
    
    if combined_total >= threshold:
        print(f"--> Vừa đủ ${threshold:.2f} để free ship không cần xóa sản phẩm small")
        return True
    
    needed = threshold - main_total
    print(f"Free shipping threshold not met (${main_total:.2f} < ${threshold:.2f}). Need ${needed:.2f} more.")
    
    success = try_add_small_products_with_calculation(sb, product_main["name"], product_smalls, main_total, threshold)
    if success:
        updated_cart_data = get_cart_api_data(sb)
        if updated_cart_data and 'summary' in updated_cart_data:
            final_total = updated_cart_data['summary'].get('total_product_amount', 0)
            print(f"Final cart subtotal: ${final_total:.2f}")
        return True
    else:
        print("Failed to add small products to meet threshold")
        return False

# ============================================================================
# STEP 5: CHECKOUT
# ============================================================================

def click_checkout_button(sb):
    # Click "Check out" button from cart page
    print("Clicking Check out button...")
    
    try:
        checkout_buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="checkout-button"]')
        for button in checkout_buttons:
            try:
                if button.is_displayed() and button.is_enabled():
                    sb.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    button.click()
                    try:
                        sb.wait_for_element_present('title[data-test="checkout-title"], h1:contains("Checkout")', timeout=2)
                    except:
                        pass
                    print("Checkout button clicked (fast method).")
                    return True
            except:
                continue
    except Exception as e:
        print(f"Fast method failed: {e}")
    
    try:
        if is_element_visible_with_timeout(sb, 'button[data-test="checkout-button"]', timeout=2):
            sb.click('button[data-test="checkout-button"]')
            try:
                sb.wait_for_element_present('title[data-test="checkout-title"], h1:contains("Checkout")', timeout=2)
            except:
                pass
            print("Checkout button clicked using SeleniumBase.")
            return True
    except:
        pass
    
    try:
        all_buttons = sb.driver.find_elements(By.TAG_NAME, 'button')
        for button in all_buttons:
            try:
                if button.text.strip() == "Check out" and button.is_displayed() and button.is_enabled():
                    button.click()
                    try:
                        sb.wait_for_element_present('title[data-test="checkout-title"], h1:contains("Checkout")', timeout=2)
                    except:
                        pass
                    print("Checkout button clicked using text search.")
                    return True
            except:
                continue
    except:
        pass
    
    print("Checkout button not found.")
    return False

def verify_checkout_page(sb):
    # Verify checkout page loaded
    print("Verifying checkout page...")
    try:
        current_url = sb.get_current_url()
        if "/checkout" in current_url.lower():
            print("On checkout page.")
            if is_element_visible_with_timeout(sb, 'title[data-test="checkout-title"]', timeout=5) or is_element_visible_with_timeout(sb, "text=Checkout", timeout=5):
                print("Checkout page verified.")
                return True
        else:
            print("Not on checkout page.")
            return False
    except Exception as e:
        print(f"Error verifying checkout page: {e}")
        return False

def click_place_order_button(sb):
    # Click "Place Order" button and enter CVV
    print("Clicking Place Order button...")
    try:
        try:
            place_order_buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="placeOrderButton"]')
            for button in place_order_buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    print("Place Order button clicked (fast method).")
                    break
        except:
            if is_element_visible_with_timeout(sb, 'button[data-test="placeOrderButton"]', timeout=3):
                sb.click('button[data-test="placeOrderButton"]')
        
        # Wait for CVV input field to appear after clicking Place Order
        print("Waiting for CVV input field to appear...")
        cvv_input_selector = 'input#enter-cvv'
        cvv_input_alt = 'input[name="enter-cvv"]'
        cvv_found = False
        
        try:
            # Wait for CVV field to appear (by ID)
            sb.wait_for_element_visible(cvv_input_selector, timeout=10)
            cvv_found = True
            print("CVV input field found (by id).")
        except:
            try:
                # Wait for CVV field to appear (by name)
                sb.wait_for_element_visible(cvv_input_alt, timeout=10)
                cvv_input_selector = cvv_input_alt
                cvv_found = True
                print("CVV input field found (by name).")
            except:
                print("CVV input field not found after waiting.")
                return False
        
        if cvv_found:
        print("Entering CVV...")
        try:
                # Scroll into view
                try:
                    element = sb.find_element(cvv_input_selector, timeout=2)
                    sb.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                    time.sleep(0.3)
                except:
                    pass
                
                sb.type(cvv_input_selector, '325')
                print("CVV entered: 325")
        except Exception as e:
            print(f"Error entering CVV: {e}")
            return False
            else:
                return False
        
        # Step 6.3b: Click Confirm button (COMMENTED FOR TESTING)
        # print("Clicking Confirm button...")
        # try:
        #     confirm_button_selector = 'button[data-test="confirm-button"]'
        #     if is_element_visible_with_timeout(sb, confirm_button_selector, timeout=3):
        #         sb.click(confirm_button_selector)
        #         print("Confirm button clicked.")
        #         return True
        #     else:
        #         print("Confirm button not found.")
        #         return False
        # except Exception as e:
        #     print(f"Error clicking Confirm button: {e}")
        #     return False
        print("Confirm button click is COMMENTED for testing.")
        return True
    except Exception as e:
        print(f"Error clicking place order button: {e}")
        return False

def checkout_and_place_order(sb):
    # Main function to checkout and place order
    print("Clicking Check out button to proceed to payment...")
    if not click_checkout_button(sb):
        print("Failed to click checkout button.")
        return False
    
    try:
        sb.wait_for_element_present('button[data-test="placeOrderButton"]', timeout=2)
    except:
        pass
    
    if not click_place_order_button(sb):
        print("Failed to click place order button.")
        return False
    
    print("Payment process completed (order confirmation check is COMMENTED for testing).")
    return True

# ============================================================================
# STEP 6: MAIN WORKFLOW
# ============================================================================

def run_bot():
    # Main workflow function to run entire bot
    print("=" * 60)
    print("Starting Target Bot - Automated Purchase Workflow")
    print("=" * 60)
    sb = None
    
    try:
        print("\n[Step 1] Initializing session...")
        sb = initialize_session(EMAIL, PASSWORD)
        if not sb:
            print("ERROR: Failed to initialize session.")
            return False
        
        print("\n[Step 2] Navigating to product...")
        sub_name = product_main.get("sub_name") if "sub_name" in product_main else None
        if not navigate_to_product(sb, product_main["name"], sub_name=None):
            print("ERROR: Failed to navigate to product.")
            return False
        
        print("\n[Step 3] Adding main product to cart (waiting for availability)...")
        if not add_main_product_to_cart(sb, product_main, max_wait_minutes=10080):
            print("ERROR: Failed to add main product to cart.")
            return False
        
        print("\n[Step 4] Checking Skittles and ensuring free shipping...")
        if not check_cart_and_ensure_free_shipping(sb, product_main, product_smalls, FREE_SHIPPING_THRESHOLD):
            print("WARNING: Free shipping threshold may not be met.")
        
        print("\n[Step 5] Proceeding to payment and placing order...")
        if not checkout_and_place_order(sb):
            print("ERROR: Failed to complete checkout.")
            return False
        
        print("\n" + "=" * 60)
        print("SUCCESS: Bot completed successfully!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\nERROR: Unexpected error in main workflow: {e}")
        return False
    finally:
        if sb:
            print("\nClosing browser...")
            try:
                if hasattr(sb, 'driver'):
                    sb.driver.quit()
                elif hasattr(sb, 'quit'):
                    sb.quit()
            except:
                pass

# ============================================================================
# TEST MODE: Direct product testing
# ============================================================================

def test_mode():
    # Test mode: Direct access to product page and test add to cart logic
    print("=" * 60)
    print("TEST MODE: Direct Product Testing")
    print("=" * 60)
    
    # Test product URL
    TEST_PRODUCT_URL = "https://www.target.com/p/pok-233-mon-trading-card-game-mega-evolutions-phantasmal-flames-9-pocket-portfolio/-/A-95045259#lnk=sametab"
    TEST_QUANTITY = 2
    
    sb = None
    
    try:
        print("\n[TEST] Opening browser...")
        sb_context = SB(uc=True, incognito=True)
        sb = sb_context.__enter__()
        if not hasattr(sb, '_context_manager'):
            sb._context_manager = sb_context
        print("Browser opened successfully!")
        
        print(f"\n[TEST] Navigating directly to product page...")
        print(f"URL: {TEST_PRODUCT_URL}")
        sb.uc_open_with_reconnect(TEST_PRODUCT_URL, reconnect_time=3)
        sb.sleep(3)
        
        try:
            current_url = sb.get_current_url()
            print(f"Current URL: {current_url}")
        except Exception as e:
            print(f"Warning: Could not get current URL: {e}")
        
        print("\n[TEST] Step 1: Waiting for Add to cart button to become available...")
        if not wait_for_add_to_cart_button_available(sb, max_wait_minutes=10080, check_interval=0.5):
            print("ERROR: Button did not become available.")
            return False
        
        print("\n[TEST] Step 2: Selecting quantity and clicking Add to cart...")
        if not click_preorder_button(sb, quantity=TEST_QUANTITY):
            print("ERROR: Failed to click Add to cart button.")
            return False
        
        print("\n[TEST] Step 3: Verifying product in cart via XHR API...")
        cart_data = get_cart_api_data(sb)
        if cart_data and 'cart_items' in cart_data:
            items = cart_data['cart_items']
            if items:
                main_item = items[0]
                item_qty = None
                if 'quantity' in main_item:
                    if isinstance(main_item['quantity'], dict):
                        item_qty = main_item['quantity'].get('value', 0)
                    else:
                        item_qty = main_item['quantity']
                elif 'item_summary' in main_item and 'quantity' in main_item['item_summary']:
                    item_qty = main_item['item_summary']['quantity']
                
                if item_qty is not None:
                    print(f"✓ Verified: Product quantity in cart = {item_qty}")
                    if item_qty == TEST_QUANTITY:
                        print("✓ Quantity verified correctly!")
                    else:
                        print(f"⚠ Quantity mismatch. Expected {TEST_QUANTITY}, found {item_qty}")
                else:
                    print("⚠ Could not extract quantity from API, but product is in cart")
        else:
            print("⚠ Could not verify cart via XHR API")
        
        print("\n[TEST] Step 4: Testing cart and free shipping check...")
        test_product_main = {
            "name": "Pokémon Trading Card Game: Mega Evolutions- Phantasmal Flames 9-Pocket Portfolio"
        }
        check_cart_and_ensure_free_shipping(sb, test_product_main, product_smalls, FREE_SHIPPING_THRESHOLD)
        
        print("\n" + "=" * 60)
        print("TEST COMPLETED!")
        print("=" * 60)
        print("\nPress ENTER to close browser...")
        input()
        
        return True
    except Exception as e:
        print(f"\nERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if sb:
            print("\nClosing browser...")
            try:
                if hasattr(sb, 'driver'):
                    sb.driver.quit()
                elif hasattr(sb, 'quit'):
                    sb.quit()
            except:
                pass

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_mode()
    else:
    run_bot()

