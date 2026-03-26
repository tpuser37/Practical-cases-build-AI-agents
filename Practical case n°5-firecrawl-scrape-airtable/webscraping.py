import os
import json
import requests
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp
import streamlit as st

# -------------------------
# CONFIGURATION AIRTABLE
# -------------------------
AIRTABLE_API_KEY = 'patxS3ePKxhOpUw2U.7abb8894c52039234fc13f4799d4d0e88be9dc4c68bd593d73a978bcc4aa0002'
AIRTABLE_BASE_ID = 'appyPIMk8w66fs1BM'
AIRTABLE_TABLE_ID = 'tblF9eip2LbAxCZY7'

# -------------------------
# INITIALISATION FIRECRAWL
# -------------------------
firecrawl = FirecrawlApp(api_key="fc-37aef7ac75e14c5c8e12866c7b404c92")

# -------------------------
# FONCTION DE PARSING
# -------------------------
def simple_parse(text):
    listings = text.split("Ref :")
    records = []

    for listing in listings[1:]:
        lines = listing.strip().split('\n')
        record = {}
        record['ref'] = lines[0].strip()
        price_line = next((l for l in lines if '€' in l), '')
        record['price'] = price_line.strip() if price_line else ''
        location_line = next((l for l in lines if 'PARIS' in l.upper()), '')
        record['location'] = location_line.strip() if location_line else ''
        try:
            price_index = lines.index(price_line)
            detail_index = lines.index(next(l for l in lines if 'Voir le détail du bien' in l))
            description = ' '.join(line.strip() for line in lines[price_index+1:detail_index])
            record['description'] = description
        except StopIteration:
            record['description'] = ''
        records.append(record)

    return records

# -------------------------
# FONCTION D'AJOUT AIRTABLE
# -------------------------
def add_to_airtable(record):
    response = requests.post(
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}",
        headers={
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        },
        json={"fields": record}
    )
    if response.status_code == 200 or response.status_code == 201:
        return True
    else:
        st.error(f"Erreur Airtable pour {record['ref']}: {response.status_code} - {response.text}")
        return False

# -------------------------
# STREAMLIT INTERFACE
# -------------------------
st.title("Scraper Century21 et Airtable")
url_input = st.text_input("Entrez l'URL à scraper:", "https://www.century21.fr/annonces/f/achat/v-paris/")

if st.button("Lancer le scraping"):
    st.info("Scraping en cours...")
    scrape_result = firecrawl.scrape(url_input, formats=["html"])
    soup = BeautifulSoup(scrape_result.html, "html.parser")
    plain_text = soup.get_text()
    records = simple_parse(plain_text)

    st.success(f"{len(records)} records extraits.")

    # Affichage des records
    for record in records:
        st.write(record)

    # Ajout à Airtable
    st.info("Ajout des records à Airtable...")
    added_count = 0
    for record in records:
        if add_to_airtable(record):
            added_count += 1

    st.success(f"{added_count}/{len(records)} records ajoutés avec succès à Airtable.")
