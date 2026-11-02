from scrapers.reddit_scraper import scrape_reddit
from scrapers.hackernews_scraper import scrape_hackernews
from scrapers.youtube_scraper import scrape_youtube
import os
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
        reviews += scrape_reddit(product, max_reviews=60)
    except Exception as e:
        print("Reddit scraper failed:", e)

    try:
        reviews += scrape_hackernews(product, max_reviews=100)
    except Exception as e:
        print("HackerNews scraper failed:", e)

    if os.getenv("ENABLE_TRUSTPILOT", "false").lower() == "true":
        try:
            from scrapers.trustpilot_scraper import scrape_trustpilot
            reviews += scrape_trustpilot(product, max_reviews=50)
        except Exception as e:
            print("Trustpilot scraper failed:", e)
    else:
        print("Trustpilot scraper disabled for this deployment.")

    try:
        reviews += scrape_youtube(product)
    except Exception as e:
        print("ProductHunt scraper failed:", e)

    # FILTER REVIEWS
    reviews = filter_reviews(reviews, product)

    return reviews