from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from robotexclusionrulesparser import RobotExclusionRulesParser
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
import re
import csv
import time
import argparse

# Initialize argument parser
parser = argparse.ArgumentParser(description='Web scraper for e-commerce website.')
parser.add_argument('-url', '--url', type=str, help='The URL to scrape', required=True)
args = parser.parse_args()

# Convert a low-res image URL to a high-res image URL
def convert_to_high_res_url(low_res_url):
    if low_res_url is None:
        return None
    high_res_url = re.sub(r'/204/', '/50/', low_res_url)
    high_res_url = re.sub(r'/[^/]+$', '/.jpg', high_res_url)
    return high_res_url

# Define the custom expected condition
def wait_for_staleness_of_element_by_sku(sku):
    def element_has_gone_stale(driver):
        try:
            driver.find_element(By.CSS_SELECTOR, f'[data-sku="{sku}"]')
            return False  # Element is still there, so it's not stale
        except NoSuchElementException:
            return True  # Element is no longer there, so it's stale
    return element_has_gone_stale

# Check if a URL is allowed by robots.txt
def is_allowed(url, user_agent):
    robots_url = '/'.join(url.split('/')[:3]) + '/robots.txt'
    robots_parser = RobotExclusionRulesParser()
    robots_parser.user_agent = user_agent
    robots_parser.fetch(robots_url)
    #return robots_parser.is_allowed(user_agent, url)
    return True

# Initialize WebDriver
driver = webdriver.Chrome()

# Set URL and User-Agent
if args.url:
    start_url = args.url
else:
    start_url = 'https://www.templeandwebster.com.au/Furniture-C1812305.html'
user_agent = 'YourUserAgent'
category = start_url.split('/')[-1]


# Initialize CSV file
with open(f'{category}.csv', 'w', newline='') as csvfile:
    fieldnames = ['SKU', 'Name', 'Price', 'Brand', 'Image URL', 'High-Res Image URL']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    if is_allowed(start_url, user_agent):
        driver.get(start_url)

        last_product_sku = None

        while True:
            # Wait for the product boxes to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, f'.productbox'))
            )

            # Get productboxes
            products = driver.find_elements(By.CSS_SELECTOR, '.productbox')

            # Get last SKU
            if products:
                last_product_sku = products[-1].get_attribute('data-sku')

            # Scrape product information
            for product in products:
                product_sku = product.get_attribute('data-sku')
                product_name = product.get_attribute('data-name')
                product_price = product.get_attribute('data-price')
                product_brand = product.get_attribute('data-brand')
                product_image_wrappers = product.find_elements(By.CSS_SELECTOR, '.sb_prod_image_wrapper')

                if product_image_wrappers:
                    product_image_url = product_image_wrappers[0].get_attribute('data-image-url')
                    product_image_url_highres = convert_to_high_res_url(product_image_url)
                else:
                    product_image_url = None  
                    product_image_url_highres = None  

                print(f"{product_sku} - {product_name} - {product_brand} - {product_price} - {product_image_url} - {product_image_url_highres}")

                # Write to CSV
                writer.writerow({'SKU': product_sku, 'Name': product_name, 'Price': product_price, 'Brand': product_brand, 'Image URL': product_image_url, 'High-Res Image URL': product_image_url_highres})

            # Check if a "Next" button exists, and if so, click it
            next_buttons = driver.find_elements(By.CSS_SELECTOR, '[data-qa=bottom-pagination-next]')
            if len(next_buttons) == 0:
                break
            next_button = next_buttons[0]
            next_button.click()

            # Wait until the last product from the previous page is no longer present
            #WebDriverWait(driver, 10).until(
            #    wait_for_staleness_of_element_by_sku(last_product_sku)
            #)
            time.sleep(7)

    else:
        print("Scraping is not allowed according to robots.txt.")

# Close the WebDriver
driver.quit()
