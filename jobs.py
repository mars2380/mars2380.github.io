import requests
from bs4 import BeautifulSoup
import csv

def page (URL):
    page = requests.get(URL, verify=False)
    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find(id="cnt")

    URLS = [URL]

    pages_elements = results.find_all("span", class_="pages")    
    for pages_element in pages_elements:     
        link_elements = pages_element.find_all("a")
        for link_element in link_elements:
            link=link_element.get('href')
            URLS.append("https://www.jobserve.com" + link)

    pages = set(URLS)
    pages = sorted(pages, reverse=True)
    # print (pages)
    return pages

def search ():
    URLS = page(URL)
    for i in URLS:
        print(i)
        request = requests.get(i, verify=False)
        soup = BeautifulSoup(request.content, "html.parser")
        results = soup.find(id="cnt")
        # print(results.prettify())

        job_elements = results.find_all("li")
        for job_element in job_elements:
            title_element = job_element.find("span", class_="position")
            link_element = job_element.find("a")
            date_element = job_element.find("span", class_="etime")

            title = title_element.text.strip()
            link = "https://www.jobserve.com" + link_element.get('href')
            date = date_element.text.strip()
            
            print(title)
            print(link)
            print(date)
            print()
        print("---------" * 10 )
        print()
    print("=========" * 10 )
    print()

def cvs ():
    with open('jobs.csv', 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow([title, link, date])

URL1 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=DC2CD21F55D1F339"
URL2 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=4D8DA2CE347175ED"
URL3 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=DE3E429DC7D11447"
URL4 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=AA6A02598408858D"
URL5 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=E2FB1B9115F1CBEC"

URLALL = [ URL1, URL2, URL3, URL4, URL5]
# URLALL = [ URL1 ]
for URL in URLALL:
    # page(URL)
    search()