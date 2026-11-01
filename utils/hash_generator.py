import hashlib

def generate_review_hash(review_text):
    return hashlib.md5(review_text.encode("utf-8")).hexdigest()