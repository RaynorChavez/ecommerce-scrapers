from scraper import scrape_shutterstock
from keywords import keywords
import argparse

if __name__ == "__main__":
    # Initialize argument parser
    parser = argparse.ArgumentParser(description='Web scraper for Shutterstock images.')
    parser.add_argument('-limit', '--limit', type=int, help='The maximum number of images to scrape per keyword', default=100)
    parser.add_argument('-concurrent', '--concurrent', type=int, help='The number of keywords to scrape concurrently', default=2)
    args = parser.parse_args()

    scrape_shutterstock(keywords, args.limit, args.concurrent)