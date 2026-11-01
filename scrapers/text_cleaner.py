import re
from bs4 import BeautifulSoup

def clean_text(text):

    # remove html tags
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text()

    # remove urls
    text = re.sub(r'http\S+', '', text)

    # remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()