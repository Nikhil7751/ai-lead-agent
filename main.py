import requests
import os
import pandas as pd
import re
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")


def get_user_input():
    niche = input("Enter niche (e.g., hospital, gym, school): ").strip()
    
    cities_input = input("Enter cities (comma separated): ")
    cities = [city.strip() for city in cities_input.split(",")]

    return niche, cities


def create_search_query(niche, city):
    return f"{niche} in {city}"


def fetch_businesses(query):
    api_key = os.getenv("SERPAPI_KEY")

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_maps",
        "q": query,
        "api_key": api_key
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print("Error fetching data:", response.text)
        return []

    data = response.json()
    return data.get("local_results", [])


def extract_emails_from_text(text):
    return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", text)


def extract_email_from_website(base_url):
    if not base_url:
        return None

    paths = ["", "/contact", "/contact-us", "/about"]

    for path in paths:
        try:
            url = base_url.rstrip("/") + path
            response = requests.get(url, timeout=5)

            emails = extract_emails_from_text(response.text)

            if emails:
                return emails[0]

        except:
            continue

    return None


def clean_email(email):
    if not email:
        return None

    email = email.lower().strip()

    junk_keywords = ["info@", "support@", "admin@", "contact@", "help@"]

    for junk in junk_keywords:
        if junk in email:
            return None

    return email


def is_high_quality(lead):
    return (
        lead["website"] is not None and
        lead["email"] is not None and
        lead["phone"] is not None
    )


def extract_data(businesses):
    leads = []

    for biz in businesses:
        name = biz.get("title")
        address = biz.get("address")
        phone = biz.get("phone")

        website = None
        if "website" in biz:
            website = biz.get("website")
        elif "links" in biz and isinstance(biz["links"], dict):
            website = biz["links"].get("website")

        print(f"Checking website: {website}")

        email = extract_email_from_website(website)
        email = clean_email(email)

        lead = {
            "name": name,
            "address": address,
            "phone": phone,
            "website": website,
            "email": email
        }

        if is_high_quality(lead):
            leads.append(lead)

    return leads


def main():
    print("=== AI Lead Agent (Pro Mode) ===")

    niche, cities = get_user_input()

    all_leads = []

    for city in cities:
        print(f"\n--- Processing {city} ---")

        query = create_search_query(niche, city)
        businesses = fetch_businesses(query)

        print(f"Found {len(businesses)} businesses")

        leads = extract_data(businesses)
        all_leads.extend(leads)

    df = pd.DataFrame(all_leads)

    df = df.drop_duplicates(subset=["email"])

    df.to_csv("final_leads.csv", index=False)

    print("\n✅ High-quality leads saved to final_leads.csv")


if __name__ == "__main__":
    main()