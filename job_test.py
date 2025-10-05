import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Set up headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Open JobServe page
url = "https://www.jobserve.com/gb/en/JobSearch.aspx?shid=FA5FC4FA61B523B4824B"
driver.get(url)

# Wait for the page to fully render
time.sleep(5)

# Parse the page source
soup = BeautifulSoup(driver.page_source, "html.parser")

# Close browser
driver.quit()

# Extract job postings
jobs = []

# Adjust these selectors based on actual page structure
for job_card in soup.find_all("article", class_="job"):
    title_elem = job_card.find("a", class_="jobTitle")
    company_elem = job_card.find("div", class_="company")
    location_elem = job_card.find("div", class_="location")
    summary_elem = job_card.find("div", class_="summary")

    job_data = {
        "title": title_elem.text.strip() if title_elem else None,
        "company": company_elem.text.strip() if company_elem else None,
        "location": location_elem.text.strip() if location_elem else None,
        "summary": summary_elem.text.strip() if summary_elem else None,
        "link": "https://www.jobserve.com" + title_elem['href'] if title_elem and title_elem.get('href') else None
    }

    jobs.append(job_data)

# Save to JSON
with open("jobserve_jobs.json", "w", encoding="utf-8") as f:
    json.dump(jobs, f, indent=2, ensure_ascii=False)

print(f"Scraped {len(jobs)} jobs and saved to jobserve_jobs.json.")
