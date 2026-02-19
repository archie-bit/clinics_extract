# Medical Lead Scraper

A containerized browser automation tool that extracts clinic information from Google Maps and uses the Gemini 2.5 Flash model to verify, categorize, and clean the data.

---

## 1. Setup & API Key
This project requires a **Google Gemini API Key** to process the extracted data and determine lead quality.

### How to get your Gemini API Key:
1.  Visit **[Google AI Studio](https://aistudio.google.com/)**.
2.  Sign in with your standard Google Account.
3.  Click on the **"Get API key"** button in the bottom-left sidebar.
4.  Click **"Create API key in new project"**.
5.  Copy your generated key.
6.  Create a file named `.env` in your project root and paste your key like this:
    ```env
    GEMINI_API_KEY=your_key_here
    LOG_LEVEL=INFO
    ```

---

## 2. How to Run
Everything is managed via Docker to handle dependencies like Playwright and Python environments automatically.

### Step 1: Build the Image
Run this whenever you change your `requirements.txt` or `Dockerfile`:
```
docker-compose build
```

### Step 2: Run with Default Query
To run the scraper with the default query ("Dentist in Maadi"):
```
docker-compose up
```

### step 3: Run with Custom Query
To run the scraper with custom query ("Clinic in Maadi")
```
docker-compose run scraper --query "Clinic in Maadi"
```

---

## 3. Sample Output
![Example Output](docs/example_output/leads.csv)


## 4. Project Layout

  * scripts/: Contains scrapper.py (automation) and processor.py (AI logic) and clean_phonenum.py (format phonenumber).

  * data/: Local folder where your CSV files will appear after the container finishes.

  * Dockerfile: Configures the Ubuntu/Playwright environment.

  * docker-compose.yml: Handles volume mapping and environment variables.
