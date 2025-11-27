# NIRF Ranking Data Pipeline (2025)

An automated data pipeline that scrapes institutional ranking data from the **National Institutional Ranking Framework (NIRF)**, extracts unstructured financial and academic data from PDF reports using **Google Gemini AI**, and consolidates everything into a formatted **Google Sheet** for analysis.

## 🚀 Features

* **Hybrid Scraper (`nirf_scraper.py`):** * Scrapes complex HTML tables for the "Research" category.
    * Automatically downloads PDF reports for "Overall", "Engineering", "University", and "Law" categories.
* **AI-Powered Extraction (`pdf_extractor.py`):** * Uses **Google Gemini 2.5 Flash** to parse text from thousands of PDFs.
    * Extracts specific metrics (Student Strength, Financial Expenditure, Ph.D. counts, etc.) into structured JSON.
* **Automated Reporting (`dataframe_converter.py`):** * Merges scraped HTML data with AI-extracted PDF data.
    * Transposes data into a "Wide Format" (Metrics as rows, Institutes as columns).
    * Uploads directly to Google Sheets using the Google Sheets API.

## 📂 Project Structure

```text
├── nirf_scraper.py          # Step 1: Downloads PDFs and scrapes HTML tables
├── pdf_extractor.py         # Step 2: Extracts data from PDFs using Gemini AI
├── dataframe_converter.py   # Step 3: Processes JSONs and uploads to Google Sheets
├── requirements.txt         # List of dependencies
├── credentials.json         # (Required) Google Cloud Service Account Key
├── nirf_reports/            # (Auto-generated) Folder storing downloaded PDFs
├── nirf_data_2.json         # (Auto-generated) Intermediate extracted data
└── research_data.json       # (Auto-generated) Intermediate research data
```

## 🛠️ Prerequisites & Installation

**Python 3.8+** is required.

Install all dependencies:

```bash
pip install requests beautifulsoup4 google-generativeai PyPDF2 pandas gspread gspread-dataframe google-auth
```

## 🔑 Configuration & Setup

### 1. Google Gemini API Key

To extract data from PDFs, you need a free API key from **Google AI Studio**.

1. Go to **Google AI Studio**
2. Click **"Get API key"**
3. Open `pdf_extractor.py`
4. Replace the placeholder key in the script or set it as an environment variable:

```python
api_key = "YOUR_ACTUAL_GEMINI_API_KEY"
```

### 2. Google Sheets API (`credentials.json`)

This project requires a **Service Account** to write data to Google Sheets.

---

### **Step A: Create Project & Enable APIs**

1. Go to the **Google Cloud Console**
2. Create a new project (e.g., **"NIRF-Scraper"**)
3. In the search bar, enable the following APIs:
   - **Google Drive API**
   - **Google Sheets API**

---

### **Step B: Create Service Account**

1. Go to **IAM & Admin → Service Accounts**
2. Click **Create Service Account**
3. Name it (e.g., `nirf-bot`)
4. Click **Create and Continue**
5. Under *Role*, select:  
   **Basic → Editor**
6. Click **Done**

---

### **Step C: Generate JSON Key**

1. Click on the service account email you just created
2. Navigate to the **Keys** tab
3. Click **Add Key → Create new key**
4. Select **JSON → Create**
5. A JSON file will download automatically
6. Rename it to: `credentials.json`
7. Move this file into your project folder

---

### **Step D: Share the Google Sheet**

1. Open `credentials.json` in a text editor
2. Copy the `"client_email"`  
   *(e.g., `nirf-bot@project-name.iam.gserviceaccount.com`)*
3. Create a new Google Sheet titled: `NIRF Analysis 2025`

*(Or modify the `GOOGLE_SHEET_NAME` variable in `dataframe_converter.py`.)*

4. Click **Share** in the Google Sheet
5. Paste the copied client email
6. Give it **Editor** access

---

## 🏃‍♂️ Usage

Run the scripts **in the following order**:

---

### **Step 1: Scrape Data & PDFs**

Downloads the required reports from the NIRF website.

```bash
python nirf_scraper.py
```

### **Step 2: Extract Data with AI**

Processes all downloaded PDFs to extract structured fields such as:

- Intake  
- Financials  
- Publications  
- Citations  

> **Note:** This step takes time because PDFs are processed sequentially to avoid API rate limits.

```bash
python pdf_extractor.py
```

### **Step 3: Upload to Google Sheets**

Combines the extracted data and uploads it into your Google Sheet.

```bash
python dataframe_converter.py
```

## ⚠️ Disclaimer

This tool is intended for **educational and analytical purposes only**.  
Please respect:

- NIRF website **robots.txt**
- Terms of service

The extraction logic is based on the **2025 NIRF reporting format**.  
If the NIRF website structure changes in the future, the code may require updates.




