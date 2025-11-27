import pandas as pd
import json
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

# --- 1. Configuration ---
# IMPORTANT: Change this to the exact name of the Google Sheet you created and shared.
GOOGLE_SHEET_NAME = "NIRF Analysis 2025 - 51 to 100"
CREDENTIALS_FILE = 'credentials.json'
PDF_JSON_FILE = 'nirf_data_2.json'
RESEARCH_JSON_FILE = 'research_data.json'


# --- 2. Define the Final Structure and Mapping ---
# These are the exact row names you want in your final sheets, in order.
ROW_TEMPLATES = {
    "Overall": [
        "rank", "Name of the Institute", "Institute / University ID (as per NIRF)",
        "Category: Overall/Engineering/Law/Management, etc.,", "Approved Intake (UG)", "Approved Intake (PG)",
        "Approved Intake (PG-Integrated)", "Total Approved Intake", "No.of. Students UG Strength",
        "No.of. Students PG Strength", "No.of.students PG Integrated", "Total Students Strength (Excluding Ph.D)",
        "Ph.D Full-time", "Ph.D Part-time", "Number of students (including Ph.D. students) = SS=",
        "Number of faculty members", "Annual capital expenditure (2023-24)", "Annual capital expenditure (2022-23)",
        "Annual capital expenditure (2021-22)", "Annual operating expenditure (2023-24)",
        "Annual operating expenditure (2022-23)", "Annual operating expenditure (2021-22)", "Online education",
        "Number of students offered online courses", "Number of credits transferred", "Number of courses",
        "Number of students who are economically backward", "Number of students who are socially challenged",
        "Number of students who are not receiving full tuition fee reimbursement",
        "Number of full-time Ph.D. awarded in the last 3 years", "Number of part-time Ph.D. awarded in the last 3 years",
        "Publications (2023)", "Publications (2022)", "Publications (2021)",
        "Citations (2021-22)", "Citations (2020-21)", "Citations (2019-20)",
        "Sponsored projects - Total amount received (2023-24)", "Sponsored projects - Total amount received (2022-23)",
        "Sponsored projects - Total amount received (2021-22)", "Consultancy projects - Total amount received (2023-24)",
        "Consultancy projects - Total amount received (2022-23)", "Consultancy projects - Total amount received (2021-22)",
        "Earnings from Executive Development Programme (2023-24)", "Earnings from Executive Development Programme (2022-23)",
        "Earnings from Executive Development Programme (2021-22)", "Valid NBA Accrediatation", "Valid NAAC Accrediatation"
    ],
    "Research": [
        "rank", "Name of the Institute", "Institute / University ID (as per NIRF)",
        "Category: Overall/Engineering/Law/Management, etc.,", "QNR(100)", "QLR(100)",
        "SFC(100)", "OI(100)", "PERCEPTION(100)"
    ]
}
# Reuse the comprehensive 'Overall' template for other similar categories
ROW_TEMPLATES["University"] = ROW_TEMPLATES["Overall"]
ROW_TEMPLATES["Engineering"] = ROW_TEMPLATES["Overall"]
ROW_TEMPLATES["Law"] = ROW_TEMPLATES["Overall"]

# This dictionary maps the clean JSON keys to the final, user-friendly row names
JSON_TO_USER_MAPPING = {
    'rank': 'rank', 'institute_name': 'Name of the Institute', 'nirf_id': 'Institute / University ID (as per NIRF)',
    'category': 'Category: Overall/Engineering/Law/Management, etc.,', 'approved_intake_ug': 'Approved Intake (UG)',
    'approved_intake_pg': 'Approved Intake (PG)', 'approved_intake_pg_integrated': 'Approved Intake (PG-Integrated)',
    'total_approved_intake': 'Total Approved Intake', 'students_ug_strength': 'No.of. Students UG Strength',
    'students_pg_strength': 'No.of. Students PG Strength', 'students_pg_integrated': 'No.of.students PG Integrated',
    'total_students_strength_excluding_phd': 'Total Students Strength (Excluding Ph.D)',
    'phd_full_time': 'Ph.D Full-time', 'phd_part_time': 'Ph.D Part-time',
    'total_students_including_phd': 'Number of students (including Ph.D. students) = SS=',
    'total_faculty': 'Number of faculty members', 'capital_expenditure_23_24': 'Annual capital expenditure (2023-24)',
    'capital_expenditure_22_23': 'Annual capital expenditure (2022-23)',
    'capital_expenditure_21_22': 'Annual capital expenditure (2021-22)',
    'operating_expenditure_23_24': 'Annual operating expenditure (2023-24)',
    'operating_expenditure_22_23': 'Annual operating expenditure (2022-23)',
    'operating_expenditure_21_22': 'Annual operating expenditure (2021-22)',
    'online_education_offered': 'Online education', 'online_students_offered_courses': 'Number of students offered online courses',
    'online_credits_transferred': 'Number of credits transferred', 'online_courses_count': 'Number of courses',
    'students_economically_backward': 'Number of students who are economically backward',
    'students_socially_challenged': 'Number of students who are socially challenged',
    'students_not_receiving_reimbursement': 'Number of students who are not receiving full tuition fee reimbursement',
    'phd_awarded_full_time_last_3_years': 'Number of full-time Ph.D. awarded in the last 3 years',
    'phd_awarded_part_time_last_3_years': 'Number of part-time Ph.D. awarded in the last 3 years',
    'publications_2023': 'Publications (2023)', 'publications_2022': 'Publications (2022)', 'publications_2021': 'Publications (2021)',
    'citations_21_22': 'Citations (2021-22)', 'citations_20_21': 'Citations (2020-21)', 'citations_19_20': 'Citations (2019-20)',
    'sponsored_projects_23_24': 'Sponsored projects - Total amount received (2023-24)',
    'sponsored_projects_22_23': 'Sponsored projects - Total amount received (2022-23)',
    'sponsored_projects_21_22': 'Sponsored projects - Total amount received (2021-22)',
    'consultancy_projects_23_24': 'Consultancy projects - Total amount received (2023-24)',
    'consultancy_projects_22_23': 'Consultancy projects - Total amount received (2022-23)',
    'consultancy_projects_21_22': 'Consultancy projects - Total amount received (2021-22)',
    'edp_earnings_23_24': 'Earnings from Executive Development Programme (2023-24)',
    'edp_earnings_22_23': 'Earnings from Executive Development Programme (2022-23)',
    'edp_earnings_21_22': 'Earnings from Executive Development Programme (2021-22)',
    'nba_accreditation': 'Valid NBA Accrediatation', 'naac_accreditation': 'Valid NAAC Accrediatation',
    # Research specific fields
    'qnr_100': 'QNR(100)', 'qlr_100': 'QLR(100)', 'sfc_100': 'SFC(100)', 'oi_100': 'OI(100)', 'perception_100': 'PERCEPTION(100)'
}


# --- 3. Data Loading and Processing Function ---
def load_and_prepare_data():
    """Loads, merges, and transforms data from JSON files into the final 'wide' format."""
    print("--- Starting Data Processing ---")
    
    # Load data from PDF extraction
    try:
        with open(PDF_JSON_FILE, 'r') as f:
            all_data = json.load(f)
        print(f" Successfully loaded '{PDF_JSON_FILE}'")
    except FileNotFoundError:
        print(f" Warning: '{PDF_JSON_FILE}' not found. Starting with an empty dataset.")
        all_data = {}

    # Load and merge data from the Research HTML table scrape
    try:
        with open(RESEARCH_JSON_FILE, 'r') as f:
            research_data = json.load(f)
        if "Research" in research_data:
            all_data["Research"] = research_data["Research"]
            print(f" Successfully loaded and merged '{RESEARCH_JSON_FILE}'")
    except FileNotFoundError:
        print(f" Info: '{RESEARCH_JSON_FILE}' not found. Skipping merge.")
    
    # Process the merged data into the final format
    final_dataframes = {}
    for category, metric_order in ROW_TEMPLATES.items():
        if category in all_data and all_data.get(category):
            # Create a standard DataFrame (institutions are rows)
            tidy_df = pd.DataFrame(all_data[category])
            # Rename columns from simple JSON keys to final user-friendly names
            tidy_df.rename(columns=JSON_TO_USER_MAPPING, inplace=True)

            if 'Name of the Institute' in tidy_df.columns:
                # Set institute name as the index, transpose, and reorder to match the template
                tidy_df = tidy_df.set_index('Name of the Institute')
                wide_df = tidy_df.T
                final_df = wide_df.reindex(metric_order)
                final_dataframes[category] = final_df
                print(f" Created and structured DataFrame for '{category}'.")
    
    return final_dataframes

# --- 4. Main Upload Logic ---
if __name__ == "__main__":
    dataframes_to_upload = load_and_prepare_data()

    if not dataframes_to_upload:
        print("\n No data was processed. Halting upload.")
        exit()

    print("\n--- Authenticating with Google Sheets API ---")
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
        client = gspread.authorize(creds)
    except FileNotFoundError:
        print(f" FATAL ERROR: Credentials file '{CREDENTIALS_FILE}' not found.")
        print("Please complete the one-time API setup and place the file in the project folder.")
        exit()
    except Exception as e:
        print(f" FATAL ERROR: An issue occurred during authentication: {e}")
        exit()

    try:
        spreadsheet = client.open(GOOGLE_SHEET_NAME)
        print(f" Successfully opened Google Sheet: '{GOOGLE_SHEET_NAME}'")
    except gspread.SpreadsheetNotFound:
        print(f" FATAL ERROR: Spreadsheet named '{GOOGLE_SHEET_NAME}' not found in your Google Drive.")
        print("Please ensure the sheet exists and has been shared with the service account's email.")
        exit()

    print("\n--- Uploading Data to Google Sheets ---")
    for category, df in dataframes_to_upload.items():
        try:
            worksheet = spreadsheet.worksheet(category)
            print(f"Updating existing sub-sheet: '{category}'...")
        except gspread.WorksheetNotFound:
            print(f"Creating new sub-sheet: '{category}'...")
            worksheet = spreadsheet.add_worksheet(title=category, rows=500, cols=300)
        
        worksheet.clear()
        # 'include_index=True' is crucial for writing the metric names in the first column
        set_with_dataframe(worksheet, df, include_index=True)
        print(f" Successfully uploaded data for '{category}'.")

    print("\n Project Complete! Your Google Sheet has been populated.")