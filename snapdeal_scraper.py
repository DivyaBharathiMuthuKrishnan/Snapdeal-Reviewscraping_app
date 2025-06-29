import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_snapdeal_reviews(product_url_base, pages=5, delay=3):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }

    all_reviews = []

    for page_num in range(1, pages + 1):
        url = f"{product_url_base}?page={page_num}&sortBy=HELPFUL"
        print(f"Fetching page {page_num}: {url}")

        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"⚠️ Failed to fetch page {page_num}: Status {response.status_code}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            review_blocks = soup.find_all('div', class_='user-review')

            if not review_blocks:
                print(f"⚠️ No reviews found on page {page_num}.")
                continue

            for review in review_blocks:
                rating_div = review.find('div', class_='rating')
                rating = len(rating_div.find_all('i', class_='sd-icon sd-icon-star active')) if rating_div else None

                headline_div = review.find('div', class_='head')
                headline = headline_div.get_text(strip=True) if headline_div else ""

                user_div = review.find('div', class_='_reviewUserName')
                username = user_div.get('title') if user_div and user_div.has_attr('title') else user_div.get_text(strip=True) if user_div else ""

                review_text = ""
                p_tags = review.find_all('p')
                review_lines = [
                    p.get_text(strip=True)
                    for p in p_tags
                    if not p.parent.get('class') or 'verifiedname' not in p.parent.get('class', [])
                ]
                review_text = " ".join(review_lines)

                all_reviews.append({
                    'rating': rating,
                    'headline': headline,
                    'username': username,
                    'review_text': review_text
                })

            print(f"✅ Fetched {len(review_blocks)} reviews from page {page_num}.")
            time.sleep(delay)

        except Exception as e:
            print(f"❌ Error on page {page_num}: {e}")
            continue

    return all_reviews
