print("Loading modules...")
print("Importing seleniumbase...")
from seleniumbase import SB
print("Importing other modules...")
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import re
import json
import time
print("All modules loaded successfully!")

# Product configuration for testing
PRODUCT_MAIN_NAME = "Pokémon Trading Card Game: Mega Evolutions- Phantasmal Flames 9-Pocket Portfolio"
PRODUCT_MAIN_QUANTITY = 2
FREE_SHIPPING_THRESHOLD = 35.00

# Helper function to normalize product names (remove special characters)
def normalize_product_name(name):
    # Remove parentheses and their contents, extra spaces, and normalize
    name = re.sub(r'\([^)]*\)', '', name)  # Remove (content)
    name = re.sub(r'\s+', ' ', name)  # Normalize spaces
    name = name.strip()
    return name

def is_element_visible_with_timeout(sb, selector, timeout=5):
    # Check if element is visible with timeout support
    try:
        sb.wait_for_element_visible(selector, timeout=timeout)
        return True
    except:
        return False

def get_cart_api_data(sb):
    # Get cart data from XHR API
    try:
        try:
            current_url = sb.get_current_url()
        except Exception as e:
            print(f"✗ Browser is not accessible: {e}")
            return None
        
        if '/cart' not in current_url:
            print("⚠ Not on cart page, navigating to cart...")
            sb.open("https://www.target.com/cart")
            sb.sleep(2)
        
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
                sb.sleep(3)
                
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

def remove_small_product_from_cart(sb, product_name):
    # Remove small product from cart using normalized name comparison
    try:
        normalized_search = normalize_product_name(product_name)
        
        title_elements = sb.driver.find_elements(By.CSS_SELECTOR, 'div[data-test="cartItem-title"]')
        title_element = None
        
        for elem in title_elements:
            try:
                text = elem.text.strip()
                normalized_text = normalize_product_name(text)
                # Compare normalized names
                if normalized_search.lower() in normalized_text.lower() or normalized_text.lower() in normalized_search.lower():
                    title_element = elem
                    break
            except:
                continue
        
        if not title_element:
            print(f"  Product '{product_name}' not found in cart to remove.")
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
                        delete_buttons = parent.find_elements(By.CSS_SELECTOR, 'button')
                        for btn in delete_buttons:
                            try:
                                aria_label = btn.get_attribute('aria-label') or ''
                                if 'remove' in aria_label.lower() or 'delete' in aria_label.lower():
                                    delete_button = btn
                                    break
                            except:
                                continue
                    except:
                        pass
            
            if not delete_button:
                print(f"  Delete button not found for '{product_name}'.")
                return False
            
            try:
                sb.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", delete_button)
                sb.sleep(0.5)
            except:
                pass
            
            delete_button.click()
            sb.sleep(2)
            print(f"  ✓ Removed '{product_name}' from cart.")
            return True
        except Exception as e:
            print(f"  Could not remove product: {e}")
            return False
    except Exception as e:
        print(f"  Error removing product: {e}")
        return False

# ============================================================================
# STEP 3: CHECK BUTTON STATUS AND ADD TO CART
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

def wait_for_add_to_cart_button_available(sb, max_wait_minutes=10080, check_interval=5):
    # Polling loop to wait for button available
    max_wait_seconds = max_wait_minutes * 60
    print_interval = 60
    start_time = time.time()
    last_print_time = start_time
    check_count = 0
    refresh_interval = 10
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
                    sb.wait_for_element_present('button[id^="addToCartButtonOrTextIdFor"], button[data-test="shippingButton"], button[data-test="preorderButtonDisabled"]', timeout=5)
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

# ============================================================================
# STEP 3: CHECK AND UPDATE CART QUANTITY
# ============================================================================

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
                        sb.sleep(2)
                        return True
                    
                    # Click button to open dropdown
                    button.click()
                    sb.sleep(0.5)
                    
                    # Select desired quantity
                    qty_option_selector = f'a[aria-label="{desired_quantity}"]'
                    if not is_element_visible_with_timeout(sb, qty_option_selector, timeout=2):
                        qty_option_selector = f'a[aria-label="{desired_quantity} - selected"]'
                    
                    if is_element_visible_with_timeout(sb, qty_option_selector, timeout=3):
                        sb.click(qty_option_selector)
                        sb.sleep(1)
                        print(f"Updated quantity from {current_qty} to {desired_quantity}")
                    else:
                        print(f"Could not find quantity option {desired_quantity}. Using current quantity.")
                    
                    # Navigate to cart
                    sb.open("https://www.target.com/cart")
                    sb.sleep(2)
                    return True
            except Exception as e:
                print(f"Error processing in-cart button: {e}")
                continue
    except Exception as e:
        print(f"Error checking cart quantity: {e}")
    
    return False

def click_preorder_button(sb, quantity=2):
    # Click Add to cart button immediately, then update quantity in cart page
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
    
    # Product not in cart, click Add to cart immediately (without selecting quantity)
    try:
        print("Clicking Add to cart button immediately (quantity will be updated in cart)...")
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
                            sb.sleep(1.5)
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
                                sb.sleep(1.5)
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
                                sb.sleep(1.5)
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
        
        # Navigate to cart page
        print("Navigating to cart page...")
        cart_navigated = False
        
        try:
            # Try to find and click "View cart" link in overlay
            cart_links = sb.driver.find_elements(By.CSS_SELECTOR, 'a[href="/cart"]')
            for link in cart_links:
                if link.is_displayed() and ("View cart" in link.text or "check out" in link.text.lower()):
                    link.click()
                    sb.sleep(1.5)
                    print("Check out link clicked (fast method).")
                    cart_navigated = True
                    break
        except:
            pass
        
        if not cart_navigated:
            try:
                checkout_link_selectors = [
                    'a:contains("View cart & check out")',
                    'a:contains("View cart")',
                    'a[href="/cart"]',
                    'a[href*="/cart"]'
                ]
                
                for selector in checkout_link_selectors:
                    try:
                        if is_element_visible_with_timeout(sb, selector, timeout=2):
                            sb.click(selector)
                            sb.sleep(1.5)
                            print(f"Check out link clicked using: {selector}")
                            cart_navigated = True
                            break
                    except:
                        continue
            except:
                pass
        
        if not cart_navigated:
            print("Check out link not found in overlay. Navigating to cart manually...")
            sb.open("https://www.target.com/cart")
            sb.sleep(2)
        
        # Now update quantity in cart page
        print(f"Updating quantity to {quantity} in cart page...")
        if check_and_update_cart_quantity(sb, desired_quantity=quantity):
            print(f"✓ Quantity updated to {quantity} in cart")
            return True
        else:
            print(f"⚠ Could not update quantity in cart, but product was added")
            return True
    except Exception as e:
        print(f"Error clicking Add to cart button: {e}")
        return False
        
# ============================================================================
# STEP 4: CHECK CART & ENSURE FREE SHIPPING
# ============================================================================

def check_cart_and_ensure_free_shipping(sb, product_main_name, threshold=35.00):
    # Main function to check and ensure free shipping using XHR API
    print("\n" + "="*60)
    print("[STEP 4] Checking cart and ensuring free shipping...")
    print("="*60)
    
    cart_data = get_cart_api_data(sb)
    if not cart_data or 'cart_items' not in cart_data:
        print("Could not get cart data from XHR API. Skipping free shipping check.")
        print("WARNING: Free shipping threshold may not be met.")
        return False
    
    items = cart_data['cart_items']
    main_product = None
    small_products = []
    
    # Normalize main product name for comparison
    normalized_main_name = normalize_product_name(product_main_name)
    
    for item in items:
        is_add_on = item.get('item_indicators', {}).get('is_add_on', False)
        if is_add_on:
            small_products.append(item)
        else:
            # Check if this is the main product by comparing normalized names
            desc = item.get('item_attributes', {}).get('description', 'N/A')
            desc = desc.replace('&#39;', "'")
            normalized_desc = normalize_product_name(desc)
            
            if normalized_main_name.lower() in normalized_desc.lower() or normalized_desc.lower() in normalized_main_name.lower():
                main_product = item
            elif main_product is None:
                # If no match found, use first non-add-on as main
                main_product = item
    
    if not main_product and items:
        main_product = items[0]
        small_products = items[1:] if len(items) > 1 else []
    
    if not main_product:
        print("No main product found in cart.")
        return False
    
    # Print main product info
    main_desc = main_product.get('item_attributes', {}).get('description', 'N/A')
    main_desc = main_desc.replace('&#39;', "'")
    main_qty = main_product.get('quantity', 0)
    main_total = main_product.get('item_summary', {}).get('total_product', 0)
    print(f"\nMain product: {main_desc}")
    print(f"  Quantity: {main_qty}")
    print(f"  Total: ${main_total:.2f}")
    
    # Print small products
    if small_products:
        print(f"\nSmall products ({len(small_products)}):")
        for idx, item in enumerate(small_products):
            desc = item.get('item_attributes', {}).get('description', 'N/A')
            desc = desc.replace('&#39;', "'")
            qty = item.get('quantity', 0)
            total_price = item.get('item_summary', {}).get('total_product', 0)
            print(f"  {idx + 1}. {desc} - Qty: {qty} - ${total_price:.2f}")
    
    if main_total >= threshold:
        print(f"\n--> Sản phẩm main đã > ${threshold:.2f} xóa sản phẩm small")
        
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
        print(f"\n--> Vừa đủ ${threshold:.2f} để free ship không cần xóa sản phẩm small")
        return True
    
    needed = threshold - main_total
    print(f"\nFree shipping threshold not met (${main_total:.2f} < ${threshold:.2f}). Need ${needed:.2f} more.")
    print("Note: Auto-adding small products is not implemented in test mode.")
    return False

# ============================================================================
# STEP 5: CHECKOUT
# ============================================================================

def click_checkout_button(sb):
    # Click "Check out" button from cart page
    print("\n" + "="*60)
    print("[STEP 5] Proceeding to checkout...")
    print("="*60)
    print("Clicking Check out button...")
    sb.sleep(1)
    
    try:
        checkout_buttons = sb.driver.find_elements(By.CSS_SELECTOR, 'button[data-test="checkout-button"]')
        for button in checkout_buttons:
            try:
                if button.is_displayed() and button.is_enabled():
                    sb.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    sb.sleep(0.2)
                    button.click()
                    sb.sleep(1.5)
                    print("Checkout button clicked (fast method).")
                    return True
            except:
                continue
    except Exception as e:
        print(f"Fast method failed: {e}")
    
    try:
        if is_element_visible_with_timeout(sb, 'button[data-test="checkout-button"]', timeout=3):
            sb.click('button[data-test="checkout-button"]')
            sb.sleep(1.5)
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
                    sb.sleep(1.5)
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

def checkout_and_place_order(sb):
    # Main function to checkout (skip CVV in test mode)
    print("Clicking Check out button to proceed to payment...")
    if not click_checkout_button(sb):
        print("Failed to click checkout button.")
        return False
    
    sb.sleep(3)
    
    if not verify_checkout_page(sb):
        print("Failed to verify checkout page.")
        return False
    
    print("\n✓ Checkout page reached successfully!")
    print("Note: CVV entry and place order are skipped in test mode.")
    return True

# ============================================================================
# MAIN TEST FUNCTION
# ============================================================================

def main():
    print("\n" + "="*60)
    print("TEST: Step 3, 4, 5 Logic Test")
    print("="*60)
    print("\nInstructions:")
    print("1. Browser will open Target.com")
    print("2. Please add small product(s) to cart manually")
    print("3. Navigate to main product page:")
    print(f"   '{PRODUCT_MAIN_NAME}'")
    print("4. Press ENTER in this terminal when ready")
    print("\nTest will execute:")
    print("  Step 3: Wait for button (optional) → Select quantity → Click Add to cart → Navigate to cart")
    print("  Step 4: Check cart and ensure free shipping (verify via XHR)")
    print("  Step 5: Proceed to checkout (CVV skipped)")
    print("="*60 + "\n")
    
    with SB(uc=True, incognito=True) as sb:
        print("Opening Target.com...")
        sb.open("https://www.target.com")
        sb.sleep(2)
        
        print("\n✓ Browser opened!")
        print(f"Please:")
        print("  1. Add small product(s) to cart")
        print(f"  2. Navigate to main product: '{PRODUCT_MAIN_NAME}'")
        print("  3. Press ENTER when ready to test...")
        
        # Wait for user to press Enter
        input()
        
        try:
            current_url = sb.get_current_url()
            print(f"\nCurrent URL: {current_url}")
        except Exception as e:
            print(f"⚠ Could not get current URL: {e}")
        
        # STEP 3: Wait for button (optional) → Select quantity → Click Add to cart button
        print("\n" + "="*60)
        print("[STEP 3] Waiting for Add to cart button and adding product...")
        print("="*60)
        
        # Ask if user wants to wait for button (for Pokemon preorder)
        print("\nDo you want to wait for 'Add to cart' button to become available?")
        print("(Useful for preorder products like Pokemon)")
        print("Enter 'y' to wait, or press ENTER to skip waiting:")
        wait_choice = input().strip().lower()
        
        if wait_choice == 'y':
            print("\nWaiting for Add to cart button to become available...")
            if not wait_for_add_to_cart_button_available(sb, max_wait_minutes=10080, check_interval=5):
                print("⚠ Button did not become available. Continuing anyway...")
        else:
            print("Skipping wait. Checking button status...")
            status = check_add_to_cart_button_status(sb)
            if status == "available":
                print("✓ Add to cart button is available")
            elif status == "disabled":
                print("⚠ Button is disabled (product may be out of stock)")
            else:
                print("⚠ Button status unknown")
        
        if click_preorder_button(sb, quantity=PRODUCT_MAIN_QUANTITY):
            print("✓ Step 3 completed: Product added/updated in cart")
            
            # Verify via XHR API
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
                    else:
                        item_qty = main_item.get('quantity', 0)
                    
                    if item_qty is not None:
                        print(f"Verified: Main product quantity in cart = {item_qty}")
        else:
            print("⚠ Step 3: Failed to add/update product in cart")
        
        # STEP 4: Check cart and ensure free shipping
        print("\n" + "="*60)
        print("[STEP 4] Checking cart and ensuring free shipping...")
        print("="*60)
        
        check_cart_and_ensure_free_shipping(sb, PRODUCT_MAIN_NAME, FREE_SHIPPING_THRESHOLD)
        
        # STEP 5: Checkout
        print("\n" + "="*60)
        print("[STEP 5] Proceeding to checkout...")
        print("="*60)
        
        # Make sure we're on cart page
        try:
            current_url = sb.get_current_url()
            if '/cart' not in current_url:
                print("Navigating to cart page...")
                sb.open("https://www.target.com/cart")
                sb.sleep(2)
        except:
            pass
        
        checkout_and_place_order(sb)
        
        print("\n" + "="*60)
        print("TEST COMPLETED!")
        print("="*60)
        print("\nPress ENTER to close browser...")
        input()
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
