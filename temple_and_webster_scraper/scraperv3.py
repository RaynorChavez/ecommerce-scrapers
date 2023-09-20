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
from urls import category_urls

# Initialize argument parser
parser = argparse.ArgumentParser(description='Web scraper for Temple and Webster website.')
parser.add_argument('-category', '--category', type=str, help='The Category to scrape', required=False)
parser.add_argument('-batch', '--batch', type=str, help='The Batch to scrape', required=False)
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

def scrape_category(URLs: list, category_name: str):

    SKUs = set()

    with open(f'{category_name}.csv', 'w', newline='') as csvfile:
        fieldnames = ['SKU', 'Name', 'Price', 'Brand', 'Image URL', 'High-Res Image URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for url in URLs:
            user_agent = 'YourUserAgent'
            start_url = url
            #category = start_url.split('/')[-1]


            if is_allowed(start_url, user_agent):
                driver.get(start_url)

                last_product_sku = None

                while True:
                    # Wait for the product boxes to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, f'.productbox'))
                    )
                    try: 
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

                            if product_sku in SKUs:
                                continue

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
                        time.sleep(10)
                    except:
                        continue

            else:
                print("Scraping is not allowed according to robots.txt.")

    # Close the WebDriver
    driver.quit()

def main():
    Batches = {}
    batch_index = 0
    max_categories_in_batch = 4

    # Create Batches
    for category in category_urls:
        if batch_index not in Batches:  # Check if the key doesn't exist
            Batches[batch_index] = []   # Initialize it with an empty list

        if len(Batches[batch_index]) < max_categories_in_batch:
            Batches[batch_index].append(category)
        else:
            batch_index += 1
            Batches[batch_index] = [category]  # Directly initialize with a list containing the category

    if args.batch:
        batch_num = int(args.batch)
        print(f"Scraping batch: {batch_num}")
        print(f"URLs in batch: {Batches[batch_num]}")

        for url in Batches[batch_num]:
            print(f"Scraping category: {url}")
            scrape_category(category_urls[category], category)

    else:
        print("Input Batch to scrape: ")

        # Pretty Print the batches
        for batch in Batches:
            print(f"Batch {batch}: {Batches[batch]}")

        batch = int(input("Enter Batch: " ))
        for category in Batches[batch]:
            print(f"Scraping category: {category}")
            scrape_category(category_urls[category], category)

    if args.category:
        scrape_category(category_urls[args.category], args.category)

main()