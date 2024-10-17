import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .models import Order

def bot_automation(order_id):
    # Retrieve order details from the database
    order = Order.query.filter_by(order_id=order_id).first()

    if not order or not order.big_link or not order.password:
        print("Order not found or missing big_link/password")
        return

    big_link = order.big_link
    print(big_link)
    password = order.password
    print(password)

    # Retrieve access code from the customer record
    access_order = Order.query.filter_by(order_id=order_id, role='customer').first()

    if not access_order or not access_order.access_code:
        print("Customer order not found or missing access_code")
        return

    access_code = access_order.access_code
    print(f"Access Code: {access_code}")

    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "localhost:9222")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    # Set up the Chrome service and driver
    driver_path = ChromeDriverManager().install()
    s = ChromeService(driver_path)
    driver = webdriver.Chrome(service=s, options=options)
    print('\nDriver: ', driver)

    # Open the website (using the existing logged-in session)
    driver.get("https://accounts.nintendo.com")
    print("\nURL opened with your existing Chrome session")

    # Clear cookies
    driver.delete_all_cookies()
    cookies = json.loads(big_link)
    print("\nLoaded Cookies: ", cookies)

    for cookie in cookies:
        expiration = int(cookie['expirationDate'])
        cookie_dict = {
            "domain": cookie['domain'],
            "name": cookie['name'],
            "value": cookie['value'],
            "path": cookie['path'],
            "secure": cookie['secure'],
            "httpOnly": cookie['httpOnly'],
            "expiry": expiration,
        }
        driver.add_cookie(cookie_dict)
    print("\nCookies added successfully")

    # Refresh to apply cookies
    driver.refresh()

    # Attempt to find CSRF token
    try:
        csrf_token = driver.find_element(By.NAME, 'csrf-token').get_attribute('content')
        print(f"CSRF Token found: {csrf_token}")
    except:
        print("CSRF Token not found in meta tag. Trying in hidden form field...")
        try:
            csrf_token = driver.find_element(By.XPATH, '//input[@name="csrf-token"]').get_attribute('value')
            print(f"CSRF Token found: {csrf_token}")
        except:
            print("CSRF Token not found.")

    # Generate the target URL
    target_url = f"https://accounts.nintendo.com/login/device?access_key={access_code}"
    driver.get(target_url)

    # Enter password
    password_field = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "reauthenticate-form_pc_input_0"))
    )
    password_field.send_keys(password)
    print("Password entered successfully!")

    # Optional: Pass CSRF token if needed
    try:
        csrf_token_field = driver.find_element(By.NAME, 'csrf-token')
        csrf_token_field.send_keys(csrf_token)
        print("CSRF Token passed successfully!")
    except:
        print("CSRF Token field not found or not needed.")

    # Click the OK button
    ok_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "reauthenticate-form_pc_button_0"))
    )
    ok_button.click()
    print("OK button clicked!")

    # Optionally select account if the button is available
    try:
        select_account_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "choose-connect-button"))
        )
        select_account_button.click()
        print("Select this account button clicked!")
    except:
        print("Select this account button not found, proceeding to extract 5-digit code...")

    # Wait for the 5-digit code to appear
    try:
        code_element = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".DeviceLoginPincodeShow_pincode_data"))
        )

        # Extract the 5-digit code text
        four_digit_code = code_element.text
        print(f"5-digit code is: {four_digit_code}")

        print("5-digit code saved successfully!")
    except:
        print("5-digit code not found.")

    # Close the driver after the operation
    driver.quit()
