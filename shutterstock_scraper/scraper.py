import os
import time
import logging
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from robotexclusionrulesparser import RobotExclusionRulesParser
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)

def load_completed_keywords(filename="completed_keywords.txt"):
    """Load keywords that have already been scraped."""
    if not os.path.exists(filename):
        return set()
    with open(filename, "r") as f:
        return set(f.read().splitlines())

def save_completed_keyword(keyword, filename="completed_keywords.txt"):
    """Save a keyword that has been successfully scraped."""
    with open(filename, "a") as f:
        f.write(f"{keyword}\n")
    
# Check if a URL is allowed by robots.txt
def is_allowed(url, user_agent):
    robots_url = '/'.join(url.split('/')[:3]) + '/robots.txt'
    robots_parser = RobotExclusionRulesParser()
    robots_parser.user_agent = user_agent
    robots_parser.fetch(robots_url) 
    #return robots_parser.is_allowed(user_agent, url)
    return True

def scrape_one_keyword(keyword, limit_per_keyword=100):
    time.sleep(2)
    
    driver = webdriver.Chrome()

    user_agent = 'YourUserAgent'
    
    filename = f"{keyword}.csv"
    
    # Check if CSV file already exists
    existing_product_names = set()
    if os.path.exists(filename):
        logging.info(f"File {filename} exists. Reading existing Images.")
        with open(filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_product_names.add(row['Description'])
        logging.info(f"Found {len(existing_product_names)} existing product names.")
        mode = 'a'  # Append mode
    else:
        mode = 'w'  # Write mode

    with open(filename, mode, newline='') as csvfile:
        fieldnames = ['Image URL', 'Keyword', 'Description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()

        images_scraped = 0
        page_number = 1

        while images_scraped < limit_per_keyword:
            url = f"https://www.shutterstock.com/search/{keyword}?language=en&page={page_number}"

            if not is_allowed(url, user_agent):
                logging.warning(f"Scraping is not allowed for URL: {url} according to robots.txt.")
                break

            logging.info(f"Scraping URL: {url}")
            driver.get(url)

            # Wait until images are loaded
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[role="img"]'))
                )
            except:
                logging.warning("Failed to load images on the page. Skipping this page.")
                page_number += 1
                continue

            #scroll_to_end(driver)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)") # Scroll to the bottom of the page
            time.sleep(5) 

            # Extract image information
            images = driver.find_elements(By.CSS_SELECTOR, 'div[role="img"]')

            for img in images:
                try:
                    # Extract aria-label
                    aria_label = img.get_attribute('aria-label')

                    # Extract image URL from the nested img tag
                    img = img.find_element(By.CSS_SELECTOR, 'img')
                    #print(img.get_attribute('outerHTML'))
                    img_title = img.get_attribute('title')
                    img_url = img.get_attribute('src')


                    logging.info(f"Scraped image URL: {img_url} with title: {img_title}")

                    # Write to CSV
                    writer.writerow({
                        'Image URL': img_url,
                        'Keyword': keyword,
                        'Description': img_title
                    })

                    images_scraped += 1

                    # Stop if we have scraped the desired number of images
                    if images_scraped >= limit_per_keyword:
                        break
                except Exception as e:
                    logging.warning(f"Failed to scrape image. Skipping the image. {e}")
                    continue

            # Move to the next page
            page_number += 1

            # Pause for 3 seconds before loading the next page
            time.sleep(2)

    # Save completed keyword after scraping
    save_completed_keyword(keyword)

    driver.quit()
    
def scrape_shutterstock(keywords, limit_per_keyword=100, concurrent_keywords=2):
    # Load completed keywords
    completed_keywords = load_completed_keywords()
    
    # Filter out the completed keywords from the list of keywords to scrape
    keywords_to_scrape = [k for k in keywords if k not in completed_keywords]

    # Use ThreadPoolExecutor to run `scrape_one_keyword` concurrently
    with ThreadPoolExecutor(max_workers=concurrent_keywords) as executor:
        results = executor.map(lambda keyword: scrape_one_keyword(keyword, limit_per_keyword), keywords_to_scrape)