import os
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- Configuration ---
BASE = "https://www.nirfindia.org"
CATEGORIES = {
    "Overall": "/Rankings/2025/OverallRanking.html",
    "Engineering": "/Rankings/2025/EngineeringRanking.html",
    "University": "/Rankings/2025/UniversityRanking.html",
    "Law": "/Rankings/2025/LawRanking.html",
    "Research": "/Rankings/2025/ResearchRanking.html",
} #Add/remove categories and their links

# This list will hold data scraped from the Research HTML table
research_data_list = []

print("--- Starting Hybrid NIRF Scraper ---")

print("--- Starting Hybrid NIRF Scraper ---")

for category, ranking_path in CATEGORIES.items():
    url = urljoin(BASE, ranking_path)
    print(f"\nProcessing Category: {category}")
    print(f"URL: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # --- SPECIAL LOGIC: Deeply scrape HTML table ONLY for "Research" category ---
        if category == "Research":
            # Find the main table by its specific ID
            main_table = soup.find('table', id='tbl_overall')
            if main_table:
                print("-> HTML table found for Research category. Scraping data...")
                # Find all data rows within the main table's body
                main_rows = main_table.find('tbody').find_all('tr') if main_table.find('tbody') else [] # type: ignore

                for row in main_rows:
                    main_cols = row.find_all('td', recursive=False)
                    if len(main_cols) < 6: continue

                    # Precisely extract the institute name, ignoring nested tags
                    institute_name = main_cols[1].find(text=True, recursive=False).strip()
                    if not institute_name: continue

                    # Find the hidden sub-table within the row
                    hidden_div = main_cols[1].find('div', class_='tbl_hidden')
                    if not hidden_div: continue
                    
                    nested_table = hidden_div.find('table')
                    if not nested_table: continue

                    # Extract the score values from the nested table
                    nested_cols = nested_table.find('tbody').find_all('td') if nested_table.find('tbody') else []
                    
                    if len(nested_cols) < 5: continue

                    # Create a dictionary with all required fields from both tables
                    research_entry = {
                        "rank": main_cols[5].text.strip(),
                        "institute_name": institute_name,
                        "nirf_id": main_cols[0].text.strip(),
                        "category": category,
                        "qnr_100": nested_cols[0].text.strip(),
                        "qlr_100": nested_cols[1].text.strip(),
                        "sfc_100": nested_cols[2].text.strip(),
                        "oi_100": nested_cols[3].text.strip(),
                        "perception_100": nested_cols[4].text.strip()
                    }
                    research_data_list.append(research_entry)
                print(f"  -> Successfully scraped {len(research_data_list)} entries from the complex table.")
            else:
                print("  -> Warning: Could not find an HTML table with id='tbl_overall' on the Research page.")
                
        # --- STANDARD LOGIC: Download PDFs for ALL OTHER categories ---
        else:
            category_dir = os.path.join("nirf_reports", category)
            if not os.path.exists(category_dir):
                os.makedirs(category_dir)
            
            pdf_links = [urljoin(url, a['href']) for a in soup.find_all("a", href=True) if a['href'].endswith(".pdf")] # type: ignore
            
            print(f"-> Found {len(pdf_links)} PDF(s) to download.")
            for i, pdf_url in enumerate(pdf_links):
                try:
                    pdf_response = requests.get(pdf_url)
                    filename = os.path.join(category_dir, pdf_url.split("/")[-1])
                    with open(filename, "wb") as f:
                        f.write(pdf_response.content)
                    if (i + 1) % 10 == 0 or (i + 1) == len(pdf_links):
                        print(f"  -> Downloaded {i + 1}/{len(pdf_links)} PDFs...")
                except requests.exceptions.RequestException as e:
                    print(f"    -> Error downloading {pdf_url}: {e}")
            print(f"  -> Finished downloading all PDFs for {category}.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching page for {category}: {e}")

# --- Save the Scraped Research Data to its own JSON file ---
if research_data_list:
    final_research_json = {"Research": research_data_list}
    
    with open("research_data.json", "w") as f:
        json.dump(final_research_json, f, indent=4)
    print("\nSuccessfully saved scraped table data to research_data.json")

print("\n--- Scraper Finished ---")