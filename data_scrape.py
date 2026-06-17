import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import random

session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def get_actual_price(isbn, title, author):
    """Fetches real-time INR price with a professional NULL fallback."""
    try:
        query = f"isbn:{isbn}" if isbn != "N/A" else f"intitle:{title} inauthor:{author}"
        api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&country=IN"
        response = requests.get(api_url, timeout=15).json()
        if "items" in response:
            for item in response["items"]:
                sale_info = item.get("saleInfo", {})
                if sale_info.get("saleability") == "FOR_SALE":
                    return sale_info["retailPrice"]["amount"]
    except: pass
    return None 

# --- PHASE 1: LINK COLLECTION ---
base_url = "https://www.goodreads.com/list/show/7.Best_Books_of_the_21st_Century"
all_links = []
print("Phase 1: Collecting 3500 links...")
for p in range(1, 51):
    retries = 3
    while retries > 0:
        try:
            r = session.get(f"{base_url}?page={p}", headers=headers, timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")
            links = ["https://www.goodreads.com" + a['href'] for a in soup.select("a.bookTitle")]
            all_links.extend(links)
            print(f"Page {p} links collected ({len(all_links)} total)...")
            time.sleep(2)
            break
        except Exception as e:
            print(f"Retry {4-retries} for Page {p} due to {e}")
            retries -= 1
            time.sleep(5)

# --- PHASE 2: RELIABLE SCRAPE ---
master_data = []
print(f"Phase 2: Scrapping {len(all_links)} books...")

for i, url in enumerate(all_links):
    success = False
    for attempt in range(3):
        try:
            r = session.get(url, headers=headers, timeout=30)
            if r.status_code != 200:
                raise Exception(f"Status Code {r.status_code}")
                
            b_soup = BeautifulSoup(r.text, "html.parser")
            
            # --- Extraction Logic ---
            title = b_soup.find("h1").get_text(strip=True) if b_soup.find("h1") else "N/A"
            author = b_soup.select_one("span.ContributorLink__name").text.strip() if b_soup.select_one("span.ContributorLink__name") else "N/A"
            
            # ISBN
            isbn_match = re.search(r'978\d{10}', r.text)
            isbn = isbn_match.group(0) if isbn_match else "N/A"
            
            # Real Price
            price = get_actual_price(isbn, title, author)
            
            # Publication Date (NEW)
            pub_info = b_soup.select_one("[data-testid='publicationInfo']")
            pub_date = pub_info.get_text(strip=True).replace("First published", "").strip() if pub_info else "N/A"
            
            # Description
            desc_box = b_soup.select_one("[data-testid='description'] .Formatted")
            full_description = desc_box.get_text(separator=" ", strip=True) if desc_box else "N/A"

            master_data.append({
                "Title": title,
                "Author": author,
                "Rating": b_soup.select_one("div.RatingStatistics__rating").text.strip() if b_soup.select_one("div.RatingStatistics__rating") else "0",
                "Rating_Count": re.sub(r'[^\d]', '', b_soup.select_one("[data-testid='ratingsCount']").text) if b_soup.select_one("[data-testid='ratingsCount']") else "0",
                "Review_Count": re.sub(r'[^\d]', '', b_soup.select_one("[data-testid='reviewsCount']").text) if b_soup.select_one("[data-testid='reviewsCount']") else "0",
                "Price_INR": price,
                "Pub_Date": pub_date,  # Added to the data
                "Page_Count": re.search(r'\d+', b_soup.select_one("[data-testid='pagesFormat']").text).group(0) if b_soup.select_one("[data-testid='pagesFormat']") else "0",
                "Genres": ", ".join([g.text.strip() for g in b_soup.select("[data-testid='genresList'] a.Button--tag")[:5]]),
                "ISBN": isbn,
                "Description": full_description
            })
            success = True
            break 
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(random.uniform(5, 10))

    if (i + 1) % 50 == 0:
        pd.DataFrame(master_data).to_csv("goodreads_3500_master.csv", index=False, encoding='utf-8-sig')
        print(f"Progress: {i+1} books saved...")

    time.sleep(random.uniform(2, 4))

pd.DataFrame(master_data).to_csv("goodreads_3500_master.csv", index=False, encoding='utf-8-sig')
print("Complete! 3500 book dataset generated with Publication Dates.")