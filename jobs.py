import requests
from bs4 import BeautifulSoup
import datetime

URL0 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=78A9B33B42D9BA8B"
URL1 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=DC2CD21F55D1F339"
URL2 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=4D8DA2CE347175ED"
URL3 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=DE3E429DC7D11447"
URL4 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=AA6A02598408858D"
URL5 = "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=7A69F1D9B674924A"

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
    page0 = [pages[0]]
    pages.pop(0)
    page1 = sorted(pages, reverse=False)
    pageslist = page0 + page1
    # print (pageslist)
    return pageslist

def head ():

    print('<html>')

    head = """
        <head>
        <style>
        #customers {
        font-family: Arial, Helvetica, sans-serif;
        border-collapse: collapse;
        width: 100%;
        }

        #customers td, #customers th {
        border: 1px solid #ddd;
        padding: 8px;
        }

        #customers tr:nth-child(even){background-color: #f2f2f2;}

        #customers tr:hover {background-color: #ddd;}

        #customers th {
        padding-top: 12px;
        padding-bottom: 12px;
        text-align: left;
        background-color: #04AA6D;
        color: white;
        }
        </style>
        </head>
    """
    print(head)

    # print('<title>JobServe</title>')
    print('<a href="https://mars2380.github.io/new.html"_blank" rel="noopener noreferrer">NewPage</a>')
    print('<body>')
    # print('<h1>JobServe Table</h1>')
    print('<table id="customers">')

def search (urllist):
    URLS = page(urllist)

    now = datetime.datetime.now()

    for i in URLS:
        # print(i)
        request = requests.get(i, verify=False)
        soup = BeautifulSoup(request.content, "html.parser")
        results = soup.find(id="cnt")
        # print(results.prettify())

        summary_element = results.find("span", class_="searchval")
        summary = summary_element.text

        print('<tr><th>' + summary + ' - ' + i + '</th><th>' + str(now.strftime("%a %x %X")) + '</th></tr>')

        job_elements = results.find_all("li")
        for job_element in job_elements:
            title_element = job_element.find("span", class_="position")
            link_element = job_element.find("a")
            date_element = job_element.find("span", class_="etime")

            title = title_element.text.strip()
            link = "https://www.jobserve.com" + link_element.get('href')
            date = date_element.text.strip()

            print('<tr><td>' + '<a href="' + link + 'target="_blank" rel="noopener noreferrer">' + title + '</a>' + '</td> <td> ' + date + '</td></tr>')

            # jobdetails = jobinfos(link)
            # print('<tr><td>' + '<a href="' + link + '">' + title + '</a>' + '</td> <td> ' + date + '</td></tr>' + '</td> <td> ' + jobdetails + '</td></tr>')

            # employment_elements = results.find_all("div", class_="jobinfo")
            # for employment_element in employment_elements:
            #     perm_link_element = employment_element.find("a")
            #     employment = employment_element.text
            #     print(perm_link_element)
            
            #     print('<tr><td>' + '<a href="' + perm_link_element + '">' + title + '</a>' + '</td> <td> ' + date + '</td></tr>')

def jobinfos (link):

    request = requests.get(link, verify=False)
    soup = BeautifulSoup(request.content, "html.parser")
    results = soup.find(id="cnt")

    job = results.find_all("div", class_="jobinfo")
    job = results.prettify()

    # jobinfo = job.find("div", class_="jobinfo")

    # print(jobdetails.prettify())
    return job

def button ():

    print('</table>')
    print('</body>')
    print('</html>')

def main():

    urllists = [ URL0, URL1, URL2, URL3, URL4, URL5]
    # urllists = [ URL5 ]
    head ()
    for urllist in urllists:
        search(urllist)
    button ()

    # # ONLY for Testing
    # urllists = [ URL0 ]
    # for urllist in urllists:
    #     # page(urllist)
    #     search(urllist)

if __name__ == "__main__":
    main()