import streamlit as st
import requests
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")


def get_city_areas(city):
    return [
        f"{city}",
        f"near me {city}",
        f"city center {city}",
        f"industrial area {city}",
        f"sector {city}",
        f"downtown {city}"
    ]


def generate_queries(niche, location):
    return [
        f"{niche} in {location}",
        f"{niche} centre in {location}",
        f"{niche} institute in {location}",
        f"{niche} academy in {location}",
        f"best {niche} in {location}"
    ]


def fetch_businesses(query):
    api_key = os.getenv("SERPAPI_KEY") or st.secrets["SERPAPI_KEY"]

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_maps",
        "q": query,
        "api_key": api_key
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("local_results", [])


def extract_fast_data(businesses):
    leads = []

    for biz in businesses:
        name = biz.get("title")
        address = biz.get("address")
        phone = biz.get("phone")

        website = None
        if "website" in biz:
            website = biz.get("website")
        elif "links" in biz:
            website = biz["links"].get("website")

        if website and phone:
            leads.append({
                "name": name,
                "address": address,
                "phone": phone,
                "website": website
            })

    return leads


# UI

st.title("🚀 AI Lead Agent (FAST MODE)")

niche = st.text_input("Enter Niche")
cities_input = st.text_input("Enter Cities (comma separated)")

if st.button("Generate Leads (Fast)"):

    if not niche or not cities_input:
        st.warning("Enter all fields")
    else:
        cities = [c.strip() for c in cities_input.split(",")]

        all_leads = []

        for city in cities:
            st.write(f"Processing {city}...")

            locations = get_city_areas(city)

            for location in locations:
                queries = generate_queries(niche, location)

                for q in queries:
                    businesses = fetch_businesses(q)
                    leads = extract_fast_data(businesses)
                    all_leads.extend(leads)

        df = pd.DataFrame(all_leads)
        df = df.drop_duplicates(subset=["phone"])

        st.success(f"Generated {len(df)} leads (FAST)")

        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button("Download CSV", csv, "fast_leads.csv", "text/csv")
