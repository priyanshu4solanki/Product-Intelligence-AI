from scrapers.reddit_scraper import scrape_reddit
from scrapers.hackernews_scraper import scrape_hackernews
from scrapers.trustpilot_scraper import scrape_trustpilot
from scrapers.youtube_scraper import scrape_youtube
import re

def filter_reviews(reviews, product):
    filtered = []
    product = product.lower().replace(" ", "")  # remove spaces for better matching

    for review in reviews:
        text = review.get("review", "")
        text_lower = text.lower().replace(" ", "")

        # Keep if product name is a substring
        if product in text_lower:
            filtered.append(review)

    return filtered

def collect_reviews(product):
    reviews = []

    try:
        reviews += scrape_reddit(product)
    except Exception as e:
        print("Reddit scraper failed:", e)

    try:
        reviews += scrape_hackernews(product)
    except Exception as e:
        print("HackerNews scraper failed:", e)

    try:
        reviews += scrape_trustpilot(product)
    except Exception as e:
        print("Trustpilot scraper failed:", e)

    try:
        reviews += scrape_youtube(product)
    except Exception as e:
        print("ProductHunt scraper failed:", e)

    # FILTER REVIEWS
    reviews = filter_reviews(reviews, product)

    return reviews