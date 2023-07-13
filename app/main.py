from requests_html import AsyncHTMLSession
from urllib.parse import urljoin
from validate_email_address import validate_email
import csv
import asyncio
import requests.exceptions
from bs4 import BeautifulSoup
import requests

visited_urls = set()
email_addresses = []

csv_file = '/Users/Khalid/Desktop/test.csv'

sitemap_url = 'https://example.com/sitemap.xml'  # Replace with the actual sitemap URL

anchor_texts = [
    "Contact Us",
    "Contact",
    "about",
    "email",
    "advertise",
    "Reach Us",
    "Get in Touch",
    "Message Us",
    "Email Us",
    "Write to Us",
    "Contact Our Team",
    "Contact Our Support",
    "Speak to Us",
    "Drop Us a Line",
    "Get in Touch with Us Today",
    "Let's Talk",
    "We're Here to Help",
    "Contact Us for More Information",
    "Contact Us for a Quote",
    "Contact Us to Get Started",
    "Contact Us to Learn More",
    "Hire a Business Consultant",
    "Book a Consultation",
    "Request a Quote",
    "Get a Free Estimate",
    "Send Us Your Questions",
    "Let Us Help You",
    "We'd Love to Hear from You",
    "We're Always Here for You",
    "Contact Us Anytime"
]

with open(csv_file, 'r') as file:
    reader = csv.reader(file)
    urls = [row[0] for row in reader]

def extract_urls_from_sitemap(sitemap_url):
    response = requests.get(sitemap_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    urls = [url.text for url in soup.find_all('loc')]
    return urls

async def process_url(session, url):
    try:
        response = await session.get(url, timeout=20)  # Adjust the timeout value as needed
        await response.html.arender()  # Render JavaScript if required
        response.raise_for_status()  # Raise an exception if there's an HTTP error
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP error occurred for URL: {url}")
        print(e)
        return
    except requests.exceptions.Timeout:
        print(f"Error: Timeout exceeded for URL: {url}")
        return
    except Exception as e:
        print(f"Error fetching URL: {url}")
        print(e)
        return

    elements = response.html.find('a')

    for element in elements:
        anchor_text = element.text.strip()
        if anchor_text in anchor_texts:
            email = element.attrs.get('href')
            if email.startswith('mailto:'):
                email = email[7:]
                if validate_email(email):
                    email_addresses.append(email)
                    return

    links = response.html.absolute_links
    for link in links:
        if link not in visited_urls:
            visited_urls.add(link)
            await process_url(session, link)

async def main():
    session = AsyncHTMLSession()

    # Extract URLs from the XML sitemap
    sitemap_urls = extract_urls_from_sitemap(sitemap_url)

    # Prioritize URLs containing contact-related keywords
    prioritized_urls = []
    for url in sitemap_urls:
        for anchor_text in anchor_texts:
            if anchor_text in url:
                prioritized_urls.append(url)
                break

    tasks = []
    for url in prioritized_urls:
        tasks.append(process_url(session, url))

    await asyncio.gather(*tasks)

    # Crawl remaining URLs
    remaining_urls = set(sitemap_urls) - visited_urls
    for url in remaining_urls:
        await process_url(session, url)

    await session.close()

# Run the main function
asyncio.run(main())

# Print all the scraped email addresses
for email in email_addresses:
    print(email)
