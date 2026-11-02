import os
from dotenv import load_dotenv
import requests

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")


def search_review_videos(product, max_videos=5):

    search_query = f"{product} review"

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": search_query,
        "type": "video",
        "maxResults": max_videos,
        "key": API_KEY
    }

    r = requests.get(url, params=params)
    data = r.json()

    video_ids = []

    for item in data["items"]:
        video_ids.append(item["id"]["videoId"])

    return video_ids


def scrape_video_comments(video_id, product, max_comments=50):

    url = "https://www.googleapis.com/youtube/v3/commentThreads"

    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": 100,
        "textFormat": "plainText",
        "key": API_KEY
    }

    reviews = []

    while len(reviews) < max_comments:

        r = requests.get(url, params=params)
        data = r.json()

        for item in data["items"]:

            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]

            if len(text) > 30:
                reviews.append({
                    "product": product,
                    "review": text,
                    "rating": None,
                    "source": "youtube"
                })

        if "nextPageToken" not in data:
            break

        params["pageToken"] = data["nextPageToken"]

    return reviews


def scrape_youtube(product, max_videos=3):

    video_ids = search_review_videos(product, max_videos=max_videos)

    all_reviews = []

    for vid in video_ids:

        comments = scrape_video_comments(vid, product, max_comments=50)

        all_reviews.extend(comments)

    return all_reviews