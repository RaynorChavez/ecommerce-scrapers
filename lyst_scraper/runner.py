# runner.py

import argparse
from scraper import scrape_website
from websites import websites

if __name__ == "__main__":
    # Initialize argument parser
    parser = argparse.ArgumentParser(description='Web scraper for Lyst e-commerce website.')
    parser.add_argument('-category', '--category', type=str, help='The specific category to scrape', choices=list(websites.keys()), default=None)
    parser.add_argument('-limit', '--limit', type=int, help='The maximum number of products to scrape', default=50000)
    parser.add_argument('-page', '--page', type=int, help='The page number to start scraping from', default=1)
    parser.add_argument('-filename', '--filename', type=str, help='The filename to save the scraped data to')
    args = parser.parse_args()

    if not args.category:
        print("Please choose a category from the following:")
        for key in websites.keys():
            print(key)
        args.category = input("Enter category: ")

    if not args.filename:
        print("Scraping to default filename: products.csv")
        print("Press enter to proceed, type a new filename to change it.")
        input_filename = input("Enter filename: ")
        if input_filename:
            args.filename = input_filename
        else:
            args.filename = "products.csv"

    categories_to_scrape = [args.category]

    for category in categories_to_scrape:
        for url in websites[category]:
            scrape_website(url, category, args.filename, args.limit, args.page)
