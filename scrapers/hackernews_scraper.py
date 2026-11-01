import requests
import time


def scrape_hackernews(product, max_reviews=500):

    headers = {
        "User-Agent": "ProductIntelligenceBot/1.0"
    }

    reviews = []
    page = 0

    while len(reviews) < max_reviews:

        url = (
            f"https://hn.algolia.com/api/v1/search"
            f"?query={product}&tags=comment&hitsPerPage=100&page={page}"
        )

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            break

        data = response.json()

        hits = data.get("hits", [])

        if not hits:
            break

        for item in hits:

            text = item.get("comment_text")

            if text and len(text) > 40:

                reviews.append({
                    "product": product,
                    "review": text,
                    "rating": None,
                    "source": "hackernews"
                })

            if len(reviews) >= max_reviews:
                break

        page += 1

        # small delay to avoid rate limits
        time.sleep(0.5)

    return reviews