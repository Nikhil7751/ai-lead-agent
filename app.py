import streamlit as st
import requests
import os
import pandas as pd
import re
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")


# ---------------- FUNCTIONS ---------------- #

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
        st.error("Error fetching data")
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

st.title("🚀 AI Lead Agent")

niche = st.text_input("Enter Niche (e.g., school, hospital)")
cities_input = st.text_input("Enter Cities (comma separated)")

if st.button("Generate Leads"):

    if not niche or not cities_input:
        st.warning("Please enter both niche and cities")
    else:
        cities = [c.strip() for c in cities_input.split(",")]

        all_leads = []

        st.write("Processing... please wait ⏳")

        for city in cities:
            st.write(f"Processing: {city}")

            query = create_search_query(niche, city)
            businesses = fetch_businesses(query)

            leads = extract_data(businesses)
            all_leads.extend(leads)

        df = pd.DataFrame(all_leads)
        df = df.drop_duplicates(subset=["email"])

        st.success(f"Found {len(df)} high-quality leads")

        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Download Leads CSV",
            data=csv,
            file_name="final_leads.csv",
            mime="text/csv"
        )