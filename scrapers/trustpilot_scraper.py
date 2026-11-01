from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time


def scrape_trustpilot(company_input, max_reviews=100):

    company_slug = company_input.strip().lower()
    company_slug = company_slug.replace("https://", "").replace("http://", "")
    company_slug = company_slug.replace("www.", "")

    if "." not in company_slug:
        company_slug += ".com"

    company_slug = f"www.{company_slug}"

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    wait = WebDriverWait(driver, 30)

    reviews = []
    page = 1

    while len(reviews) < max_reviews:

        url = f"https://www.trustpilot.com/review/{company_slug}?page={page}"
        print(f"Scraping Trustpilot page {page}: {url}")

        driver.get(url)

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Accept cookies once
        if page == 1:
            try:
                cookie_btn = wait.until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                cookie_btn.click()
                print("Cookies accepted")
            except:
                pass

        time.sleep(4)

        # Scroll to load lazy reviews
        for _ in range(5):
            driver.execute_script("window.scrollBy(0,1500)")
            time.sleep(2)

        review_blocks = driver.find_elements(
            By.CSS_SELECTOR,
            "article[data-service-review-card-paper]"
        )

        print("Found review blocks:", len(review_blocks))

        if not review_blocks:
            break

        for block in review_blocks:

            if len(reviews) >= max_reviews:
                break

            try:
                try:
                    text = block.find_element(
                        By.CSS_SELECTOR,
                        "p[data-service-review-text-typography]"
                    ).text
                except:
                    text = block.find_element(
                        By.CSS_SELECTOR,
                        "a[data-review-title-typography]"
                    ).text

                rating = block.find_element(
                    By.CSS_SELECTOR,
                    "div[data-service-review-rating]"
                ).get_attribute("data-service-review-rating")

                reviews.append({
                    "product": company_input,
                    "review": text,
                    "rating": rating,
                    "source": "trustpilot"
                })

            except:
                continue

        page += 1

    driver.quit()

    if not reviews:
        print("Trustpilot: no reviews extracted")

    return reviews