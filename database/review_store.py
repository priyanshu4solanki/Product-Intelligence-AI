from database.db_connection import get_db
from utils.hash_generator import generate_review_hash

db = get_db()

def save_review(review):

    review_hash = generate_review_hash(review["review"])

    existing = db.reviews.find_one({"hash": review_hash})

    if existing:
        return False

    review["hash"] = review_hash

    db.reviews.insert_one(review)

    return True