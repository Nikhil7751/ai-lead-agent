import streamlit as st
import requests
import os
import pandas as pd
import re
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")


def create_search_query(niche, city):
    return f"{niche} in {city}"


# 🔥 PAGINATED FETCH
def fetch_businesses(query, max_results=100):
    api_key = os.getenv("SERPAPI_KEY") or st.secrets["SERPAPI_KEY"]

    url = "https://serpapi.com/search.json"

    all_results = []
    start = 0

    while len(all_results) < max_results:
        params = {
            "engine": "google_maps",
            "q": query,
            "start": start,
            "api_key": api_key
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            st.error("Error fetching data")
            break

        data = response.json()
        results = data.get("local_results", [])

        if not results:
            break

        all_results.extend(results)

        start += 20  # next page

    return all_results[:max_results]


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

    junk = ["info@", "support@", "admin@", "contact@", "help@"]

    for j in junk:
        if j in email:
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


# ---------------- UI ---------------- #

st.title("🚀 AI Lead Agent (Pro Max)")

niche = st.text_input("Enter Niche")
cities_input = st.text_input("Enter Cities (comma separated)")
max_results = st.slider("Number of leads to fetch", 20, 200, 100)

if st.button("Generate Leads"):

    if not niche or not cities_input:
        st.warning("Enter all fields")
    else:
        cities = [c.strip() for c in cities_input.split(",")]

        all_leads = []

        for city in cities:
            st.write(f"Processing {city}...")

            query = create_search_query(niche, city)

            businesses = fetch_businesses(query, max_results)

            leads = extract_data(businesses)
            all_leads.extend(leads)

        df = pd.DataFrame(all_leads)

        # 🔥 REMOVE DUPLICATES
        df = df.drop_duplicates(subset=["email"])

        st.success(f"Generated {len(df)} leads")

        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download CSV",
            csv,
            "leads.csv",
            "text/csv"
        )
