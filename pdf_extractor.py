import os
import google.generativeai as genai
import json
import PyPDF2
import time

# --- 1. Configuration ---
try:
    # Configure the API key from environment variables for security
    api_key = "" #Enter the API Key
    genai.configure(api_key=api_key) # type: ignore
except KeyError:
    print(" Error: GEMINI_API_KEY environment variable not set.") 
    print("Please set it or paste your key directly into the script.")
    exit()

# --- 2. Define the JSON keys and fields for the prompt ---
# This dictionary is used to build the precise prompt for the LLM.
FIELD_TEMPLATES = {
    "Shared": {
        "rank": "Rank",
        "institute_name": "Name of the Institute",
        "nirf_id": "Institute / University ID",
        "category": "Category",
        "approved_intake_ug": "Approved Intake (UG)",
        "approved_intake_pg": "Approved Intake (PG)",
        "approved_intake_pg_integrated": "Approved Intake (PG-Integrated)",
        "total_approved_intake": "Total Approved Intake",
        "students_ug_strength": "No.of. Students UG Strength",
        "students_pg_strength": "No.of. Students PG Strength",
        "students_pg_integrated": "No.of.students PG Integrated",
        "total_students_strength_excluding_phd": "Total Students Strength (Excluding Ph.D)",
        "phd_full_time": "Ph.D Full-time",
        "phd_part_time": "Ph.D Part-time",
        "total_students_including_phd": "Number of students (including Ph.D. students)",
        "total_faculty": "Number of faculty members",
        "capital_expenditure_23_24": "Annual capital expenditure (2023-24)",
        "capital_expenditure_22_23": "Annual capital expenditure (2022-23)",
        "capital_expenditure_21_22": "Annual capital expenditure (2021-22)",
        "operating_expenditure_23_24": "Annual operating expenditure (2023-24)",
        "operating_expenditure_22_23": "Annual operating expenditure (2022-23)",
        "operating_expenditure_21_22": "Annual operating expenditure (2021-22)",
        "online_education_offered": "Online education",
        "online_students_offered_courses": "Number of students offered online courses",
        "online_credits_transferred": "Number of credits transferred",
        "online_courses_count": "Number of courses",
        "students_economically_backward": "Number of students who are economically backward",
        "students_socially_challenged": "Number of students who are socially challenged",
        "students_not_receiving_reimbursement": "Number of students who are not receiving full tuition fee reimbursement",
        "phd_awarded_full_time_last_3_years": "Number of full-time Ph.D. awarded in the last 3 years",
        "phd_awarded_part_time_last_3_years": "Number of part-time Ph.D. awarded in the last 3 years",
        "publications_2023": "Publications (2023)",
        "publications_2022": "Publications (2022)",
        "publications_2021": "Publications (2021)",
        "citations_21_22": "Citations (2021-22)",
        "citations_20_21": "Citations (2020-21)",
        "citations_19_20": "Citations (2019-20)",
        "sponsored_projects_23_24": "Sponsored projects - Total amount received (2023-24)",
        "sponsored_projects_22_23": "Sponsored projects - Total amount received (2022-23)",
        "sponsored_projects_21_22": "Sponsored projects - Total amount received (2021-22)",
        "consultancy_projects_23_24": "Consultancy projects - Total amount received (2023-24)",
        "consultancy_projects_22_23": "Consultancy projects - Total amount received (2022-23)",
        "consultancy_projects_21_22": "Consultancy projects - Total amount received (2021-22)",
        "edp_earnings_23_24": "Earnings from Executive Development Programme (2023-24)",
        "edp_earnings_22_23": "Earnings from Executive Development Programme (2022-23)",
        "edp_earnings_21_22": "Earnings from Executive Development Programme (2021-22)",
        "nba_accreditation": "Valid NBA Accreditation",
        "naac_accreditation": "Valid NAAC Accreditation"
    }
}
CATEGORIES_TO_PROCESS = ["Overall", "University", "Engineering"]

# --- 3. Helper Functions ---
def extract_text_from_pdf(pdf_path):
    """Safely extracts text from a PDF file."""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        print(f"  -> Error reading PDF {os.path.basename(pdf_path)}: {e}")
        return ""

def get_data_from_llm(text, category):
    """Builds a precise prompt and gets structured data from the Gemini model."""
    if not text:
        return None

    template_key = "Shared"
    fields_to_extract = FIELD_TEMPLATES[template_key]
    prompt_fields = "\n".join([f"- {json_key}: for the metric '{desc}'" for json_key, desc in fields_to_extract.items()])

    prompt = f"""
    From the text of the NIRF report for the '{category}' category, extract the data for the institution.
    CRITICAL INSTRUCTIONS:
    1. Extract values ONLY for the fields listed below.
    2. For any metric with multiple years (e.g., expenditures), extract data for the MOST RECENT available year ONLY.
    3. Your output MUST be a single, raw JSON object. Do not include explanations or markdown formatting like ```json ```.
    4. The keys in the JSON must exactly match the JSON keys provided below.
    5. If there're two UG/PG fields varying just in number of years, except Integrated ones, have to be added together for final value.
    

    FIELDS TO EXTRACT:
    {prompt_fields}

    TEXT TO ANALYZE:
    {text}
    """
    
    model = genai.GenerativeModel('gemini-2.5-flash') # type: ignore
    response = None
    try:
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"  -> An error occurred with the Gemini API: {e}")
        if response and response.text:
            print(f"  -> Raw Response Text (on error): {response.text[:100]}...")
        return None

# --- 4. Main Execution Logic ---
# This dictionary will hold the final data, structured by category.
all_data = {cat: [] for cat in CATEGORIES_TO_PROCESS}

for category in CATEGORIES_TO_PROCESS:
    category_dir = os.path.join("nirf_reports", category)
    if os.path.exists(category_dir):
        print(f"\n--- Processing category: {category} ---")
        
        # Get all PDF files in the directory
        pdf_files = [os.path.join(category_dir, f) for f in os.listdir(category_dir) if f.endswith(".pdf")]
        
        # **Sort the files by modification time (oldest first)**
        try:
            pdf_files.sort(key=os.path.getmtime)
            pdf_files = pdf_files[50:]
            print(f"Found {len(pdf_files)} PDF(s). Processing in order of download time.")
        except Exception as e:
            print(f"Could not sort files by time, processing in default order. Error: {e}")
        i = 50
        # Process the sorted list of files
        for pdf_path in pdf_files:
            if i <= 0:
                break
            print(f"Extracting data from: {os.path.basename(pdf_path)}")
            text = extract_text_from_pdf(pdf_path)
            
            # Add a 1-second delay to avoid overwhelming the API
            time.sleep(1) 
            
            data = get_data_from_llm(text, category)
            if data:
                # Append the extracted data to the list for the current category
                all_data[category].append(data)
            i -= 1

# --- 5. Save the final, clean, and structured JSON ---
with open("nirf_data_2.json", "w") as f:
    # The 'all_data' dictionary is already in the desired "primary key by category" format
    json.dump(all_data, f, indent=4)

print("\n Clean JSON data extraction complete. Output saved to nirf_data_2.json")