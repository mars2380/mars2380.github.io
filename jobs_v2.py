import requests
from bs4 import BeautifulSoup
import datetime
import json

jobserve_url0 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=78A9B33B42D9BA8B"
jobserve_url1 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=DC2CD21F55D1F339"
jobserve_url2 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=4D8DA2CE347175ED"
jobserve_url3 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=DE3E429DC7D11447"
jobserve_url4 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=AA6A02598408858D"
jobserve_url5 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=7A69F1D9B674924A"


def page (url):
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find(id="cnt")

    pages = []
    pages.append(url)
    pages_elements = results.find_all("span", class_="pages")  

    for pages_element in pages_elements:
        link_elements = pages_element.find_all("a")

        for link_element in link_elements:
            link = link_element.get('href')

            pages.append("https://www.jobserve.com" + link)

    return pages


def job (pages):
    job_list = {'data': []}

    for i in pages:
        request = requests.get(i, verify=False)
        soup = BeautifulSoup(request.content, "html.parser")
        results = soup.find(id="cnt")
        # print(results.prettify())

        summary = results.find("span", class_="searchval").text
        
        job_elements = results.find_all("li")
        for job_element in job_elements:
            title_element = job_element.find("span", class_="position")
            link_element = job_element.find("a")
            date_element = job_element.find("span", class_="etime")

            title = title_element.text.strip()
            link = "https://www.jobserve.com" + link_element.get('href')
            date = date_element.text.strip()

            job = summary, title, link, date
            job_list["data"].append(job)

    json_data = json.dumps(job_list)
    # print(json_data)
    return json_data


def main():
    jobserve_urls_lists = [ jobserve_url0, jobserve_url1, jobserve_url2, jobserve_url3, jobserve_url4, jobserve_url5]
    # jobserve_urls_lists = [ jobserve_url0, jobserve_url1]

    pages = []
    for jobserve_url in jobserve_urls_lists:
        pages.append(page(jobserve_url))

    pages_list = list(set(sum(pages, [])))
    print(job(pages_list))

if __name__ == "__main__":
    main()