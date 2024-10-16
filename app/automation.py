import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from .models import Order
from .email_utils import send_pin_email
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def bot_automation(order_id):
    # Retrieve order details from the database
    order = Order.query.filter_by(order_id=order_id).first()

    if not order or not order.big_link or not order.password:
        print("Order not found or missing big_link/password")
        return

    big_link = order.big_link
    password = order.password

    # Retrieve access code from the customer record
    access_order = Order.query.filter_by(order_id=order_id, role='customer').first()

    if not access_order or not access_order.access_code or not access_order.email:
        print("Customer order not found or missing access_code/email")
        return

    access_code = access_order.access_code
    email = access_order.email

    options = webdriver.ChromeOptions()
    # Run in headless mode for production environments
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # Optional: Disable GPU acceleration

    # Set up the Chrome service and driver
    driver_path = ChromeDriverManager().install()
    s = ChromeService(driver_path)
    driver = webdriver.Chrome(service=s, options=options)

    # Open the website
    driver.get("https://accounts.nintendo.com")
    
    # Clear cookies
    driver.delete_all_cookies()
    try:
        cookies = json.loads(big_link)
    except json.JSONDecodeError as e:
        print(f"Error loading cookies: {e}")
        driver.quit()
        return

    for cookie in cookies:
        expiration = int(cookie.get('expirationDate', 0))
        cookie_dict = {
            "domain": cookie.get('domain', ''),
            "name": cookie.get('name', ''),
            "value": cookie.get('value', ''),
            "path": cookie.get('path', ''),
            "secure": cookie.get('secure', False),
            "httpOnly": cookie.get('httpOnly', False),
            "expiry": expiration,
        }
        driver.add_cookie(cookie_dict)

    # Refresh to apply cookies
    driver.refresh()

    try:
        csrf_token = driver.find_element(By.NAME, 'csrf-token').get_attribute('content')
    except:
        csrf_token = None
        print("CSRF Token not found in meta tag. Trying in hidden form field...")
        try:
            csrf_token = driver.find_element(By.XPATH, '//input[@name="csrf-token"]').get_attribute('value')
        except:
            print("CSRF Token not found.")

    target_url = f"https://accounts.nintendo.com/login/device?access_key={access_code}"
    driver.get(target_url)

    time.sleep(1)

    # Enter password and CSRF token
    try:
        password_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "reauthenticate-form_pc_input_0"))
        )
        password_field.send_keys(password)

        if csrf_token:
            csrf_token_field = driver.find_element(By.NAME, 'csrf-token')
            csrf_token_field.send_keys(csrf_token)

        # Click the OK button
        ok_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "reauthenticate-form_pc_button_0"))
        )
        ok_button.click()

        # Check if the "Select this account" button is present and click it if found
        try:
            select_account_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "choose-connect-button"))
            )
            select_account_button.click()
        except:
            print("Select this account button not found, proceeding to extract 5-digit code...")

        # Wait for the 5-digit code to appear
        code_element = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".DeviceLoginPincodeShow_pincode_data"))
        )
        four_digit_code = code_element.text
        print(f"5-digit code is: {four_digit_code}")

        # Send the 5-digit pin email
        send_pin_email(email, four_digit_code, password)
        print("5-digit pin sent to the customer.")
        
    except Exception as e:
        print(f"An error occurred during the automation process: {e}")

    finally:
        # Close the driver after the operation
        driver.quit()

