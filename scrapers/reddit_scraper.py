import requests
import time


def scrape_reddit(product, max_reviews=200):

    headers = {
        "User-Agent": "ProductIntelligenceBot/1.0"
    }

    base_url = "https://www.reddit.com/search.json"

    reviews = []
    after = None

    while len(reviews) < max_reviews:

        params = {
            "q": product,
            "limit": 100,
            "sort": "relevance",
            "t": "all",
            "after": after
        }

        r = requests.get(base_url, headers=headers, params=params)

        if r.status_code != 200:
            break

        data = r.json()["data"]

        posts = data["children"]

        if not posts:
            break

        for post in posts:

            post_data = post["data"]

            title = post_data.get("title", "")
            body = post_data.get("selftext", "")
            post_id = post_data.get("id")

            text = f"{title}. {body}".strip()

            if len(text) > 40:

                reviews.append({
                    "product": product,
                    "review": text,
                    "rating": None,
                    "source": "reddit"
                })

            # ----- fetch comments -----

            if post_id and len(reviews) < max_reviews:

                comment_url = f"https://www.reddit.com/comments/{post_id}.json"

                cr = requests.get(comment_url, headers=headers)

                if cr.status_code == 200:

                    comments_data = cr.json()[1]["data"]["children"]

                    for c in comments_data:

                        comment = c["data"].get("body", "")

                        if len(comment) > 40:

                            reviews.append({
                                "product": product,
                                "review": comment,
                                "rating": None,
                                "source": "reddit"
                            })

                        if len(reviews) >= max_reviews:
                            break

            if len(reviews) >= max_reviews:
                break

        after = data.get("after")

        if not after:
            break

        time.sleep(1)

    return reviews