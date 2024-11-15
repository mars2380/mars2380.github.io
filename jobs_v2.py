import requests
from bs4 import BeautifulSoup
import datetime
import json

URL0 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=78A9B33B42D9BA8B"

def page (url):
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find(id="cnt")

    urls = [url]

    pages_elements = results.find_all("span", class_="pages")    
    for pages_element in pages_elements:     
        link_elements = pages_element.find_all("a")
        for link_element in link_elements:
            link=link_element.get('href')
            urls.append("https://www.jobserve.com" + link)

    pages = set(urls)
    pages = sorted(pages, reverse=True)
    page0 = [pages[0]]
    pages.pop(0)
    page1 = sorted(pages, reverse=False)
    urls = page0 + page1

    for i in urls:
        request = requests.get(i, verify=False)
        soup = BeautifulSoup(request.content, "html.parser")
        results = soup.find(id="cnt")
        # print(results.prettify())

        summary_element = results.find("span", class_="searchval")
        summary = summary_element.text

        job_elements = results.find_all("li")
        for job_element in job_elements:
            title_element = job_element.find("span", class_="position")
            link_element = job_element.find("a")
            date_element = job_element.find("span", class_="etime")

            title = title_element.text.strip()
            link = "https://www.jobserve.com" + link_element.get('href')
            date = date_element.text.strip()

            # print(summary, link, title, date)
            x = summary, link, title, date
            y = json.dumps(x)
            print(y)

def main():
    # urllists = [ URL0, URL1, URL2, URL3, URL4, URL5]
    urllists = [ URL0 ]
    for urllist in urllists:
        page(urllist)

if __name__ == "__main__":
    main()