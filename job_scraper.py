import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

jobserve_url0 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=78A9B33B42D9BA8B"
jobserve_url1 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=DC2CD21F55D1F339"
jobserve_url2 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=4D8DA2CE347175ED"
jobserve_url3 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=DE3E429DC7D11447"
jobserve_url4 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=AA6A02598408858D"
jobserve_url5 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=7A69F1D9B674924A"

def get_all_pages(url):
    """Fetch all pagination URLs from a search results page."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return [url]
    
    soup = BeautifulSoup(response.content, "html.parser")
    results = soup.find(id="cnt")
    
    if not results:
        return [url]
    
    pages = [url]
    pages_elements = results.find_all("span", class_="pages")
    
    for pages_element in pages_elements:
        for link_element in pages_element.find_all("a"):
            link = link_element.get('href')
            if link:
                pages.append("https://www.jobserve.com" + link)
    
    return pages

def scrape_jobs(page_urls):
    """Extract job listings from multiple pages."""
    job_list = []
    
    for page_url in page_urls:
        try:
            response = requests.get(page_url, timeout=10)
            response.raise_for_status()
            time.sleep(0.5)  # Rate limiting
        except requests.RequestException as e:
            print(f"Error fetching {page_url}: {e}")
            continue
        
        soup = BeautifulSoup(response.content, "html.parser")
        results = soup.find(id="cnt")
        
        if not results:
            continue
        
        summary_element = results.find("span", class_="searchval")
        summary = summary_element.text.strip() if summary_element else "N/A"
        
        for job_element in results.find_all("li"):
            title_element = job_element.find("span", class_="position")
            link_element = job_element.find("a")
            date_element = job_element.find("span", class_="etime")
            
            if not all([title_element, link_element, date_element]):
                continue
            
            job_entry = {
                "summary": summary,
                "title": title_element.text.strip(),
                "link": "https://www.jobserve.com" + link_element.get('href'),
                "date": date_element.text.strip()
            }
            job_list.append(job_entry)
    
    return job_list

def generate_html(jobs_data):
    """Generate index.html for GitHub Pages with embedded job data."""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Job Listings Dashboard - Automatically updated job postings">
    <title>Job Listings Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }

        .timestamp {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }

        .update-badge {
            display: inline-block;
            background: #51cf66;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            color: #666;
            margin-top: 5px;
        }

        .controls {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }

        .search-box {
            flex: 1;
            min-width: 250px;
            padding: 12px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        .search-box:focus {
            outline: none;
            border-color: #667eea;
        }

        .filter-group {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }

        select, button {
            padding: 10px 20px;
            border-radius: 20px;
            border: 2px solid #e0e0e0;
            background: white;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }

        button {
            background: #667eea;
            color: white;
            border-color: #667eea;
            font-weight: 600;
        }

        button:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }

        .job-list {
            display: grid;
            gap: 20px;
        }

        .job-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }

        .job-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .job-title {
            font-size: 1.4em;
            color: #333;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .job-summary {
            color: #666;
            margin-bottom: 10px;
            padding: 10px;
            background: #f8f9ff;
            border-radius: 5px;
            font-size: 0.9em;
        }

        .job-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }

        .job-date {
            color: #999;
            font-size: 0.9em;
        }

        .job-link {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 0.9em;
            transition: transform 0.3s;
            display: inline-block;
        }

        .job-link:hover {
            transform: scale(1.05);
        }

        .no-results {
            text-align: center;
            padding: 60px;
            background: white;
            border-radius: 15px;
            color: #999;
            font-size: 1.2em;
        }

        .footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
            opacity: 0.8;
        }

        .footer a {
            color: white;
            text-decoration: underline;
        }

        @media (max-width: 768px) {
            body {
                padding: 10px;
            }

            .header {
                padding: 20px;
            }

            h1 {
                font-size: 1.5em;
            }

            .stat-number {
                font-size: 2em;
            }

            .controls {
                flex-direction: column;
            }

            .search-box {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Job Listings Dashboard</h1>
            <div class="timestamp">
                🕒 Last Updated: ''' + timestamp + '''
                <span class="update-badge">Auto-Updated</span>
            </div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="totalJobs">0</div>
                <div class="stat-label">Total Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="uniqueSearches">0</div>
                <div class="stat-label">Unique Searches</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="filteredCount">0</div>
                <div class="stat-label">Showing</div>
            </div>
        </div>

        <div class="controls">
            <input type="text" class="search-box" id="searchBox" placeholder="🔍 Search jobs...">
            <div class="filter-group">
                <select id="searchFilter">
                    <option value="all">All Searches</option>
                </select>
                <select id="sortFilter">
                    <option value="newest">Newest First</option>
                    <option value="oldest">Oldest First</option>
                    <option value="title">By Title</option>
                </select>
                <button onclick="resetFilters()">Reset</button>
            </div>
        </div>

        <div class="job-list" id="jobList"></div>

        <div class="footer">
            <p>Automatically updated via GitHub Actions</p>
            <p><a href="https://github.com/yourusername/yourrepo" target="_blank">View Source on GitHub</a></p>
        </div>
    </div>

    <script>
        // Embedded job data
        const jobsData = ''' + json.dumps(jobs_data, indent=2) + ''';
        let filteredJobs = [...jobsData];

        const searchBox = document.getElementById('searchBox');
        const searchFilter = document.getElementById('searchFilter');
        const sortFilter = document.getElementById('sortFilter');
        const jobList = document.getElementById('jobList');

        // Initialize
        function init() {
            updateStats();
            populateSearchFilter();
            renderJobs();
        }

        // Update statistics
        function updateStats() {
            document.getElementById('totalJobs').textContent = jobsData.length;
            const uniqueSearches = new Set(jobsData.map(job => job.summary)).size;
            document.getElementById('uniqueSearches').textContent = uniqueSearches;
            document.getElementById('filteredCount').textContent = filteredJobs.length;
        }

        // Populate search filter dropdown
        function populateSearchFilter() {
            const searches = [...new Set(jobsData.map(job => job.summary))].sort();
            searchFilter.innerHTML = '<option value="all">All Searches</option>';
            searches.forEach(search => {
                const option = document.createElement('option');
                option.value = search;
                option.textContent = search;
                searchFilter.appendChild(option);
            });
        }

        // Filter and render
        function filterAndRender() {
            let results = [...jobsData];

            // Search filter
            const searchTerm = searchBox.value.toLowerCase();
            if (searchTerm) {
                results = results.filter(job => 
                    job.title.toLowerCase().includes(searchTerm) ||
                    job.summary.toLowerCase().includes(searchTerm)
                );
            }

            // Search type filter
            const selectedSearch = searchFilter.value;
            if (selectedSearch !== 'all') {
                results = results.filter(job => job.summary === selectedSearch);
            }

            // Sort
            const sortType = sortFilter.value;
            if (sortType === 'newest') {
                results.sort((a, b) => b.date.localeCompare(a.date));
            } else if (sortType === 'oldest') {
                results.sort((a, b) => a.date.localeCompare(b.date));
            } else if (sortType === 'title') {
                results.sort((a, b) => a.title.localeCompare(b.title));
            }

            filteredJobs = results;
            updateStats();
            renderJobs();
        }

        // Render jobs
        function renderJobs() {
            if (filteredJobs.length === 0) {
                jobList.innerHTML = '<div class="no-results">No jobs found matching your criteria</div>';
                return;
            }

            jobList.innerHTML = filteredJobs.map(job => `
                <div class="job-card">
                    <div class="job-title">${escapeHtml(job.title)}</div>
                    <div class="job-summary">${escapeHtml(job.summary)}</div>
                    <div class="job-meta">
                        <span class="job-date">📅 ${escapeHtml(job.date)}</span>
                        <a href="${escapeHtml(job.link)}" target="_blank" class="job-link" rel="noopener noreferrer">View Job →</a>
                    </div>
                </div>
            `).join('');
        }

        // Reset filters
        function resetFilters() {
            searchBox.value = '';
            searchFilter.value = 'all';
            sortFilter.value = 'newest';
            filterAndRender();
        }

        // Event listeners
        searchBox.addEventListener('input', filterAndRender);
        searchFilter.addEventListener('change', filterAndRender);
        sortFilter.addEventListener('change', filterAndRender);

        // Utility function
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Initialize on load
        init();
    </script>
</body>
</html>'''
    
    return html_template

def main():
    print("🚀 Starting job scraper for GitHub Pages...")
    
    search_urls = [
        jobserve_url0, jobserve_url1, jobserve_url2,
        jobserve_url3, jobserve_url4, jobserve_url5
    ]
    
    # Collect all pages
    print("📄 Collecting pages...")
    all_pages = []
    for search_url in search_urls:
        all_pages.extend(get_all_pages(search_url))
    
    # Remove duplicates
    unique_pages = list(dict.fromkeys(all_pages))
    print(f"✓ Found {len(unique_pages)} unique pages to scrape")
    
    # Scrape jobs
    print("🔍 Scraping jobs...")
    jobs = scrape_jobs(unique_pages)
    print(f"✓ Scraped {len(jobs)} jobs")
    
    # Generate HTML
    print("🎨 Generating index.html for GitHub Pages...")
    html_content = generate_html(jobs)
    
    # Write index.html (GitHub Pages default)
    with open('index_new.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ index.html generated successfully!")
    print(f"📊 Total jobs: {len(jobs)}")
    print(f"🌐 Ready for GitHub Pages deployment")
    
    # Also save JSON for reference/backup
    with open('jobs_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "total_jobs": len(jobs),
            "data": jobs
        }, f, indent=2)
    
    print(f"💾 JSON backup saved: jobs_data.json")

if __name__ == "__main__":
    main()