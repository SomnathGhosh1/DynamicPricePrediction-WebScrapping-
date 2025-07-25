import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.service import Service as ChromeService

# Initialize lists to store data
product_names = []
ratings = []
total_ratings = []
prices = []

# Set up Chrome Service
service = ChromeService(executable_path="C:\ALL IN ONE\dynamic pricing\chromedriver.exe") # Ensure this path is correct
browser = webdriver.Chrome(service=service)

browser.get("https://www.flipkart.com/")

search = browser.find_element(By.CLASS_NAME, "Pke_EE")
search.send_keys("Home Decor")
search.send_keys(Keys.RETURN)
time.sleep(2)  # Added a short wait after search

def scrape():
    # Wait for the product elements to be loaded - using slAVV4 as container now
    WebDriverWait(browser, 10).until(EC.visibility_of_all_elements_located((By.XPATH, "//div[@class='slAVV4']")))

    # Find all the product container elements - using slAVV4
    products_details = browser.find_elements(By.XPATH, "//div[@class='slAVV4']")

    # Extract and print the details of each product
    for product in products_details:
        try:
            # Product Name - using wjcEIp class
            product_name = product.find_element(By.XPATH, ".//a[@class='wjcEIp']").text
        except:
            product_name = "N/A"
        product_names.append(product_name)

        try:
            # Rating - using XQDdHH class
            rating = product.find_element(By.XPATH, ".//div[@class='XQDdHH']").text
        except:
            rating = "N/A"
        ratings.append(rating)

        try:
            # Total Ratings - using Wphh3N class
            total_rating = product.find_element(By.XPATH, ".//span[@class='Wphh3N']").text
        except:
            total_rating = "N/A"
        total_ratings.append(total_rating)

        try:
            # Price - using Nx9bqj class
            price = product.find_element(By.XPATH, ".//div[@class='Nx9bqj']").text
        except:
            price = "N/A"
        prices.append(price)

        print("Product Name:", product_name)
        print("Rating:", rating)
        print("Total Ratings:", total_rating)
        print("Price:", price)
        print()

scrape()

for i in range(2, 3):
    time.sleep(2)
    # Once the page has loaded, fetch the URL
    current_url = browser.current_url
    # Method 1
    base_url = current_url.split('&page=')[0]
    next_page=base_url + "&page=" + str(i)
    # Method 2
    # next_page=f"{current_url}&page={i}"
    browser.get(next_page)
    print(next_page)
    time.sleep(2)
    scrape()
    time.sleep(2)

data = {'Product Name': product_names, 'Rating': ratings, 'Total Ratings':total_ratings, 'Price': prices}
df = pd.DataFrame(data)
print(df)

# Save DataFrame to a CSV file
df.to_csv('Flipkart_Data.csv', index=False)

# Quit the browser session
browser.quit()