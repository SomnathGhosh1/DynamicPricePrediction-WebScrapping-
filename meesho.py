# -*- coding: utf-8 -*-
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium_stealth import stealth
# Recommended: Use webdriver-manager for easier chromedriver handling
# Uncomment the next line and install with: pip install webdriver-manager
# from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
USE_WEBDRIVER_MANAGER = False # Set to True to use webdriver-manager

# Option 1: Use webdriver-manager (Recommended)
if USE_WEBDRIVER_MANAGER:
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = ChromeService(ChromeDriverManager().install())
        print("Using webdriver-manager.")
    except ImportError:
        print("webdriver-manager not installed. Falling back to explicit path.")
        print("Install with: pip install webdriver-manager")
        USE_WEBDRIVER_MANAGER = False # Force fallback
    except Exception as e:
        print(f"Error initializing webdriver-manager: {e}")
        exit()

# Option 2: Use explicit path (Fallback or if USE_WEBDRIVER_MANAGER is False)
if not USE_WEBDRIVER_MANAGER:
    # !!! UPDATE THIS PATH IF NEEDED !!!
    CHROME_DRIVER_PATH = r"C:\ALL IN ONE\dynamic pricing\chromedriver.exe" # Use raw string r"..."
    try:
        service = ChromeService(executable_path=CHROME_DRIVER_PATH)
        print(f"Using chromedriver from explicit path: {CHROME_DRIVER_PATH}")
    except Exception as e:
        print(f"Error initializing ChromeService with explicit path: {e}")
        print(f"Path tried: {CHROME_DRIVER_PATH}")
        print("Please ensure chromedriver.exe is at the specified path and compatible with your Chrome browser.")
        if not USE_WEBDRIVER_MANAGER: # Only suggest if not already tried
             print("Consider setting USE_WEBDRIVER_MANAGER = True to use webdriver-manager for automatic management.")
        exit()

options = ChromeOptions()
options.add_argument("--start-maximized")
# Important: Make sure this User-Agent is current or matches your browser
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36") # Example, update if needed
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
# options.add_argument('--headless') # Uncomment for headless mode (runs without UI)
# options.add_argument('--disable-blink-features=AutomationControlled') # Another stealth option


# --- Data Storage ---
scraped_product_details = [] # Store dictionaries
scraped_product_links = set() # Keep track of scraped product links for uniqueness

# --- !!! CRITICAL: SELECTOR DEFINITIONS !!! ---
# ** YOU MUST INSPECT THE MEESHO PAGE (F12) AND VERIFY/UPDATE THESE **
# ** IF THE SCRIPT FAILS TO FIND ELEMENTS. Websites change frequently! **

PRODUCT_CONTAINER_SELECTOR = (By.CSS_SELECTOR, "div[class*='NewProductCardstyled__CardStyled']") # Check this
PRODUCT_LINK_SELECTOR = (By.TAG_NAME, "a") # Usually the container or a child is the link
PRODUCT_NAME_SELECTOR = (By.CSS_SELECTOR, "p[class*='NewProductCardstyled__StyledDesktopProductTitle']") # Check this too

# --- RATING SELECTORS UPDATED ---
# Strategy: Find the "Total Ratings" span first, then find the preceding sibling span which usually holds the rating value.
TOTAL_RATING_SELECTOR = (By.CSS_SELECTOR, "span[class*='NewProductCardstyled__RatingCount']") # Check this pattern remains valid
# Relative XPath: Find the total rating span (based on its class pattern) within the container, then get its preceding sibling span.
RATING_VALUE_SELECTOR = (By.XPATH, ".//span[contains(@class, 'NewProductCardstyled__RatingCount')]/preceding-sibling::span")
# --- Alternative RATING selectors (if above fails, uncomment ONE and test): ---
# RATING_VALUE_SELECTOR = (By.CSS_SELECTOR, "div[class*='Rating__StyledRating'] span:first-of-type") # Find rating div, get first span
# RATING_VALUE_SELECTOR = (By.XPATH, ".//div[contains(@class, 'Rating__StyledRating')]//span[contains(text(), '.')]") # Find span containing '.' inside rating div

# --- PRICE SELECTOR ---
# Strategy: Find an h5 tag *within the container* that contains the Rupee symbol '₹'.
PRICE_SELECTOR = (By.XPATH, ".//h5[contains(text(), '₹')]")
# --- Alternative PRICE Selectors (if above fails, uncomment ONE and test): ---
# PRICE_SELECTOR = (By.CSS_SELECTOR, "h5[class*='PriceRow']")
# PRICE_SELECTOR = (By.CSS_SELECTOR, ".sc-eDvSVe.dwCrSh")

# --- End of Selector Definitions ---


# --- Initialize Browser ---
try:
    print("Initializing WebDriver...")
    browser = webdriver.Chrome(service=service, options=options)
    print("WebDriver initialized.")
except Exception as e:
    print(f"Error initializing webdriver.Chrome: {e}")
    print("Check if chromedriver/browser version mismatch or other configuration issues.")
    exit()

# Apply stealth settings
print("Applying stealth settings...")
try:
    stealth(driver=browser,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    print("Stealth settings applied.")
except Exception as e:
    print(f"Warning: Error applying stealth settings: {e}")

# --- Navigation and Search ---
SEARCH_TERM = "Womens Beauty Products" # Or change to your desired search term
try:
    print(f"Navigating to Meesho...")
    browser.get("https://www.meesho.com/")

    print("Waiting for search input...")
    search_input_xpath = "//input[contains(@placeholder, 'Try Saree, Kurti or Search by Product Code')]"
    try:
        search = WebDriverWait(browser, 20).until(
            EC.element_to_be_clickable((By.XPATH, search_input_xpath))
        )
    except TimeoutException:
        print("Primary search input not found. Trying alternative (less reliable)...")
        search_input_xpath_alt = "/html/body/div/div[2]/div[1]/div/div[2]/div/input"
        try:
            search = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, search_input_xpath_alt))
             )
        except TimeoutException:
             print("FATAL: Search input not found using multiple selectors. Website structure may have changed significantly.")
             browser.quit()
             exit()

    print(f"Search input found. Searching for: '{SEARCH_TERM}'")
    search.send_keys(SEARCH_TERM)
    search.send_keys(Keys.RETURN)

    print("Search submitted. Waiting for initial results page load...")
    try:
        WebDriverWait(browser, 25).until(
            EC.presence_of_element_located(PRODUCT_CONTAINER_SELECTOR)
        )
        print("Initial product containers detected.")
    except TimeoutException:
        print("Warning: Did not detect initial product containers after search within 25 seconds.")
        print("Possible reasons: Slow load, incorrect PRODUCT_CONTAINER_SELECTOR, or anti-bot page.")

except TimeoutException as e:
    print(f"Timeout error during navigation or search: {e}")
    browser.quit()
    exit()
except Exception as e:
    print(f"An unexpected error occurred during navigation or search: {e}")
    browser.quit()
    exit()


# --- Scraping Function ---
def scrape_products_from_view():
    """Finds product containers on the current view, extracts data, and prints details."""
    new_products_found_count = 0
    product_containers = []

    try:
        WebDriverWait(browser, 15).until(
            EC.presence_of_all_elements_located(PRODUCT_CONTAINER_SELECTOR)
        )
        product_containers = browser.find_elements(*PRODUCT_CONTAINER_SELECTOR)
    except TimeoutException:
        return 0
    except Exception as e:
        print(f"An error occurred waiting for or finding product containers: {e}")
        return 0

    for product_container in product_containers:
        original_total_rating_text = "N/A"
        original_price_text = "N/A"
        rating_value = "N/A" # Initialize rating specific variable

        product_details = {
            "Product Name": "N/A",
            "Rating": "N/A", # This will store the final rating value
            "Total Ratings": "N/A", # Stores cleaned number for DataFrame
            "Price": "N/A",       # Stores cleaned number for DataFrame
            "Link": "N/A"
        }
        product_link = None

        # 1. Get Unique Identifier (Link)
        try:
            link_element = product_container.find_element(*PRODUCT_LINK_SELECTOR)
            product_link = link_element.get_attribute('href')
            if product_link and product_link in scraped_product_links:
                continue
            product_details["Link"] = product_link
        except NoSuchElementException:
            pass
        except Exception as e:
            print(f"Warning: Error getting product link: {e}")

        temp_link_seen = False
        if product_link and product_link not in scraped_product_links:
            temp_link_seen = True

        # 2. Extract Product Name (relative to container)
        try:
            product_name_element = product_container.find_element(*PRODUCT_NAME_SELECTOR)
            product_details["Product Name"] = product_name_element.text.strip()
        except NoSuchElementException:
            continue
        except Exception as e:
            print(f"Warning: Error getting product name: {e}")
            continue

        if temp_link_seen:
            scraped_product_links.add(product_link)

        # 3. Extract Rating Value (relative to container - USING UPDATED XPATH SELECTOR)
        try:
            # Find rating element relative to the product_container using the new XPath
            rating_element = product_container.find_element(*RATING_VALUE_SELECTOR)
            rating_value = rating_element.text.strip() # Store raw value found
            # Basic validation: check if it looks like a rating (e.g., contains a digit)
            if any(char.isdigit() for char in rating_value):
                 product_details["Rating"] = rating_value
            else:
                 # If text doesn't look like a rating, keep N/A but log warning
                 print(f"Warning: Found rating text '{rating_value}' for '{product_details['Product Name']}' which doesn't look like a number. Storing as N/A.")
                 rating_value = "N/A" # Reset for printing consistency
        except NoSuchElementException:
            # This is expected if the selector fails or product has no rating
            # print(f"Debug: Rating value not found using selector '{RATING_VALUE_SELECTOR}' for '{product_details['Product Name']}'.")
            pass
        except Exception as e:
            print(f"Warning: Error getting rating value for '{product_details['Product Name']}': {e}")

        # 4. Extract Total Ratings Count (relative to container)
        try:
            total_rating_element = product_container.find_element(*TOTAL_RATING_SELECTOR)
            original_total_rating_text = total_rating_element.text.strip()
            total_rating_cleaned = ''.join(filter(str.isdigit, original_total_rating_text))
            if total_rating_cleaned:
                 product_details["Total Ratings"] = total_rating_cleaned
        except NoSuchElementException:
             # Expected if product has no ratings count
             pass
        except Exception as e:
            print(f"Warning: Error getting/cleaning total rating for '{product_details['Product Name']}': {e}")

        # 5. Extract Price (relative to container)
        try:
            price_element = product_container.find_element(*PRICE_SELECTOR)
            original_price_text = price_element.text.strip()
            price_cleaned = original_price_text.replace('₹', '').replace(',', '').strip()
            product_details["Price"] = price_cleaned
        except NoSuchElementException:
            print(f"Warning: Price not found using selector '{PRICE_SELECTOR}' for '{product_details['Product Name']}'.")
            pass
        except Exception as e:
            print(f"Warning: Error getting/cleaning price for '{product_details['Product Name']}': {e}")

        # --- Add to list and PRINT details ---
        scraped_product_details.append(product_details)
        new_products_found_count += 1

        # Print details in the desired format
        print(f"Product Name: {product_details.get('Product Name', 'N/A')}")
        # Use the rating_value variable captured during scraping for printing consistency
        print(f"Rating: {rating_value}") # Print the value found, even if deemed invalid for the DataFrame
        if original_total_rating_text != 'N/A':
            if not (original_total_rating_text.startswith('(') and original_total_rating_text.endswith(')')):
                 print(f"Total Ratings: ({original_total_rating_text})")
            else:
                 print(f"Total Ratings: {original_total_rating_text}")
        else:
            print(f"Total Ratings: N/A")
        if original_price_text != 'N/A':
             if not original_price_text.startswith('₹'):
                 print(f"Price: ₹{original_price_text}")
             else:
                 print(f"Price: {original_price_text}")
        else:
            print(f"Price: N/A")
        print("-" * 40) # Separator

    return new_products_found_count


# --- Scrolling and Scraping Loop ---
print("\nStarting scroll and scrape loop...")
SCROLL_PAUSE_TIME = 3.0
MAX_SCROLL_ATTEMPTS_WITHOUT_NEW_PRODUCTS = 4
MAX_TOTAL_PRODUCTS = 500 # Optional limit

last_height = browser.execute_script("return document.body.scrollHeight")
no_new_products_streak = 0

while True:
    current_total = len(scraped_product_details)
    if current_total >= MAX_TOTAL_PRODUCTS:
         print(f"\nStopping: Reached maximum desired product count ({MAX_TOTAL_PRODUCTS}).")
         break

    newly_scraped_count = scrape_products_from_view()

    if newly_scraped_count > 0:
        print(f"Scraped {newly_scraped_count} new products in this pass. Total unique: {len(scraped_product_details)}")
        no_new_products_streak = 0
    else:
        no_new_products_streak += 1
        print(f"No new products found in this pass (Streak: {no_new_products_streak}/{MAX_SCROLL_ATTEMPTS_WITHOUT_NEW_PRODUCTS}).")

    if no_new_products_streak >= MAX_SCROLL_ATTEMPTS_WITHOUT_NEW_PRODUCTS:
        print(f"\nStopping: No new products found after {MAX_SCROLL_ATTEMPTS_WITHOUT_NEW_PRODUCTS} consecutive scroll attempts.")
        break

    # --- Scroll Down ---
    try:
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    except Exception as e:
        print(f"Error executing scroll script: {e}. Stopping.")
        break

    time.sleep(SCROLL_PAUSE_TIME)

    try:
        new_height = browser.execute_script("return document.body.scrollHeight")
    except Exception as e:
        print(f"Error getting new scroll height: {e}")
        new_height = last_height

    if new_height == last_height and newly_scraped_count == 0:
        pass

    last_height = new_height


# --- Data Processing and Saving ---
print("\n----------------------------------------")
print("Scraping finished.")
print(f"Total unique products scraped: {len(scraped_product_details)}")
print("----------------------------------------")

if scraped_product_details:
    print("\nCreating DataFrame...")
    df = pd.DataFrame(scraped_product_details)

    print("Converting data types for DataFrame analysis...")
    try:
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        # Use errors='coerce' for Rating as well, in case invalid text was stored
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        df['Total Ratings'] = pd.to_numeric(df['Total Ratings'], errors='coerce').astype('Int64')
    except Exception as e:
        print(f"Warning: Error during DataFrame data type conversion: {e}")

    print("\n--- Final Scraped Data Summary (DataFrame) ---")
    try:
        print(df.to_string())
    except Exception as e:
        print(f"Error printing DataFrame: {e}. Printing head instead.")
        print(df.head())

    try:
        output_filename = 'Meesho_Scraped_Data_Final.csv'
        print(f"\nSaving data to {output_filename}...")
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"Data successfully saved.")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")
else:
    print("\nNo product data was successfully scraped.")
    print("Please check:")
    print("1. Internet connection.")
    print("2. If the Meesho website structure has changed significantly.")
    print("3. **Verify ALL CSS/XPath selectors** (especially RATING_VALUE_SELECTOR and TOTAL_RATING_SELECTOR) at the top of the script using browser developer tools (F12).")
    print("4. If anti-bot measures are blocking the script.")


# --- Cleanup ---
print("\nClosing browser...")
browser.quit()
print("Script finished.")