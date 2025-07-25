import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions # Import ChromeOptions

# Initialize lists to store data
product_names = []
ratings = []
total_ratings = []
prices = []

# Set up Chrome Service and Options
service = ChromeService(executable_path="C:/Users/win11/Desktop/College-Final Year/Semester-08/chromedriver.exe") # Ensure this path is correct
options = ChromeOptions()
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36") # Example User-Agent
browser = webdriver.Chrome(service=service, options=options)

browser.get("https://www.meesho.com/")
time.sleep(5) # Increased initial wait

search = browser.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div/div[2]/div/input")
search.send_keys("Womens Beauty Products")
search.send_keys(Keys.RETURN)
time.sleep(5) # Increased wait after search

def scrape():
    # Wait for element visibility (you might need to adjust the XPath if still getting errors)
    try:
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div/div[3]/div/div[3]/div[2]/div[2]/div/div[1]/a/div/div[2]")))
        product_details_container = browser.find_element(By.XPATH, "/html/body/div/div[3]/div/div[3]/div[2]/div[2]/div/div[1]/a/div/div[2]")
    except TimeoutError:
        print("Timeout waiting for product container. Website might be blocking or element not found.")
        return # Exit scrape function if container not found

    # ... (rest of your scrape function - extracting product details as before, but you might need to adjust XPaths/ClassNames if still getting NoSuchElementException) ...
    try:
        product_name_element = product_details_container.find_element(By.XPATH, "./div[1]/span/p") # Relative XPath within product_details_container
        product_name = product_name_element.text
    except:
        product_name = "N/A"
    product_names.append(product_name)

    try:
        rating = product_details_container.find_element(By.CLASS_NAME, "sc-eDvSVe.laVOtN").get_attribute('textContent') # Relative search within container
    except:
        rating = "N/A"
    ratings.append(rating)

    try:
        total_rating_element = product_details_container.find_element(By.CLASS_NAME, "sc-eDvSVe.XndEO.NewProductCardstyled__RatingCount-sc-6y2tys-21.jZyLzI.NewProductCardstyled__RatingCount-sc-6y2tys-21.jZyLzI") # Relative search
        total_rating = total_rating_element.get_attribute('textContent')
    except:
        total_rating = "N/A"
    total_ratings.append(total_rating)

    try:
        price_element = product_details_container.find_element(By.CLASS_NAME, "sc-eDvSVe.dwCrSh") # Relative search
        price = price_element.text
    except:
        price = "N/A"
    prices.append(price)

    print("Product Name:", product_name)
    print("Rating:", rating)
    print("Total Ratings:", total_rating)
    print("Price:", price)


scrape() # Call scrape function only once in this version
# ... (rest of your code to create DataFrame and quit browser) ...

data = {'Product Name': product_names, 'Rating': ratings, 'Total Ratings': total_ratings, 'Price': prices}
df = pd.DataFrame(data)
print(df)

# Save DataFrame to a CSV file
df.to_csv('Meesho_Scraped_Data.csv', index=False)

# Quit the browser session
browser.quit()