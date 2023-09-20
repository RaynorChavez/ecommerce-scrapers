# scraper2.py

import os
import time
import logging
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from robotexclusionrulesparser import RobotExclusionRulesParser

logging.basicConfig(level=logging.INFO)

def scroll_to_end(driver, scroll_pause_time=1):
    # Get initial scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    retries = 4  # Number of retries before accepting the end of the page

    while retries > 0:
        # Scroll down by a fraction of the page's view height
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.7);")
        
        # Wait to load the page
        time.sleep(scroll_pause_time)
        
        # Calculate new scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # If heights are same, decrement retries
        if new_height == last_height:
            retries -= 1
        else:
            # Reset retries if new content was loaded
            retries = 4
        
        # Update the last_height for next iteration
        last_height = new_height
    
# Check if a URL is allowed by robots.txt
def is_allowed(url, user_agent):
    robots_url = '/'.join(url.split('/')[:3]) + '/robots.txt'
    robots_parser = RobotExclusionRulesParser()
    robots_parser.user_agent = user_agent
    robots_parser.fetch(robots_url) 
    return robots_parser.is_allowed(user_agent, url)

def scrape_website(url, category, filename, limit=300, page=1):
    driver = webdriver.Chrome()
    start_page = page

    user_agent = 'YourUserAgent'
    filename = f"{category}.csv"

    # Check if CSV file already exists
    existing_product_names = set()
    if os.path.exists(filename):
        logging.info(f"File {filename} exists. Reading existing product names.")
        with open(filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_product_names.add(row['Product Name'])
        logging.info(f"Found {len(existing_product_names)} existing product names.")
        mode = 'a'  # Append mode
    else:
        mode = 'w'  # Write mode

    with open(filename, mode, newline='') as csvfile:
        fieldnames = ['Product Name', 'Price', 'Brand', 'Category', 'Source', 'Sale', 'Image URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()

        if is_allowed(url, user_agent):
            products_scraped = 0
            page_number = start_page
            skipped_pages_count = 0  # Counter for skipped pages

            while products_scraped < limit:
                current_url = f"{url}?page={page_number}"
                logging.info(f"Scraping URL: {current_url}")
                driver.get(current_url)

                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.kah5ce0.kah5ce2'))
                    )
                    skipped_pages_count = 0  # Reset skipped pages counter
                except:
                    logging.warning("Failed to load product boxes in the page. Skipping this page.")
                    page_number += 1
                    skipped_pages_count += 1
                    if skipped_pages_count == 5:
                        logging.warning("Skipped 5 consecutive pages. Terminating the scraper.")
                        break  # Terminate the loop after 5 skipped pages
                    continue

                scroll_to_end(driver)

                # Extract product information
                products = driver.find_elements(By.CSS_SELECTOR, '.kah5ce0.kah5ce2')

                MAX_RETRIES = 3
                for product in products:
                    # Skip if this product div has the class "UbaIK"
                    if "UbaIK" in product.get_attribute("class"):
                        continue
                    try:
                        # Extract details
                        product_name = product.find_element(By.CSS_SELECTOR, '._1b08vvh1o._1b08vvhk2.vjlibs5.vjlibs2').text
                        # Skip product if it's already in the existing product names set
                        if product_name in existing_product_names:
                            logging.info(f"Product {product_name} already exists. Skipping.")
                            continue

                        prices = [price.text for price in product.find_elements(By.CSS_SELECTOR, '._1b08vvhk6')]
                        try:
                            brand = product.find_element(By.CSS_SELECTOR, '._1b08vvh1o._1b08vvhka.vjlibs5.vjlibs2').text
                        except:
                            brand = "N/A"
                        try:
                            source = product.find_element(By.CSS_SELECTOR, '._1fcx6l23').text
                        except:
                            source = "N/A"
                        sale = 'Sale' if product.find_elements(By.CSS_SELECTOR, 'span._1b08vvh1q._1b08vvhkq.vjlibs6.vjlibs2') else 'No Sale'
                        product_image = product.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')

                        retries = 0
                        while "http://www.w3.org/2000/svg" in product_image and retries < MAX_RETRIES:
                            logging.info(f"Reloading product image of: {product_name}")
                            
                            # Scroll the product into view
                            driver.execute_script("arguments[0].scrollIntoView();", product)
                            
                            # Wait for the image to potentially load
                            time.sleep(3)  # Adjust as needed
                            
                            # Re-fetch the product image
                            product_image = product.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                            
                            retries += 1

                        if "http://www.w3.org/2000/svg" in product_image:
                            logging.warning(f"Failed to reload product image of: {product_name}. Skipping the product")
                            continue

                        logging.info(f"Scraped product: {product_name} - Price: {prices} - Brand: {brand}")

                        # Write to CSV
                        writer.writerow({
                            'Product Name': product_name,
                            'Price': ', '.join(prices),
                            'Image URL': product_image,
                            'Brand': brand,
                            'Category': category,
                            'Source': source,
                            'Sale': sale
                        })

                        products_scraped += 1

                        # Stop if we have scraped 50,000 products
                        if products_scraped >= limit:
                            break
                    except:
                        logging.warning("Failed to scrape product. Skipping the product.")
                        continue

                # Move to the next page
                page_number += 1

                # Pause for 3 seconds before loading the next page
                time.sleep(2)
        else:
            logging.warning("Scraping is not allowed according to robots.txt.")

    driver.quit()
