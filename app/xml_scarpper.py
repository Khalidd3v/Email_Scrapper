# import requests
# from bs4 import BeautifulSoup

# def scrape_sitemap_urls(sitemap_url):
#     response = requests.get(sitemap_url)
#     soup = BeautifulSoup(response.content, 'lxml', features='xml')
#     urls = [url.text for url in soup.find_all('loc')]
#     return urls

# def find_contact_links(urls):
#     contact_links = []
    
#     for url in urls:
#         sub_urls = scrape_sitemap_urls(url)
#         xml_links = [sub_url for sub_url in sub_urls if 'xml' in sub_url]
        
#         if xml_links:
#             for xml_link in xml_links:
#                 xml_urls = scrape_sitemap_urls(xml_link)
#                 contact_urls = [contact_url for contact_url in xml_urls if any(word in contact_url.lower() for word in ['contact', 'reach us', 'email us',])]
#                 contact_links.extend(contact_urls)
#         else:
#             contact_urls = [contact_url for contact_url in sub_urls if any(word in contact_url.lower() for word in ['contact', 'reach us', 'email us'])]
#             contact_links.extend(contact_urls)
    
#     return contact_links

# # Example usage
# sitemap_url = 'https://www.pcmag.com/sitemap-index.xml'  # Replace with the actual sitemap URL
# sitemap_urls = scrape_sitemap_urls(sitemap_url)
# contact_links = find_contact_links(sitemap_urls)

# if contact_links:
#     for link in contact_links:
#         print(link)
# else:
#     print("Contact link not found.")

import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from urllib.parse import urljoin
from validate_email_address import validate_email
import csv
import os
import requests.exceptions

visited_urls = set()
session = HTMLSession()
email_addresses = []

def scrape_sitemap_urls(sitemap_url):
    response = requests.get(sitemap_url)
    soup = BeautifulSoup(response.content, 'lxml-xml')
    urls = [url.text for url in soup.find_all('loc')]
    return urls

def find_contact_links(urls):
    contact_links = []

    for url in urls:
        sub_urls = scrape_sitemap_urls(url)
        xml_links = [sub_url for sub_url in sub_urls if 'xml' in sub_url]

        if xml_links:
            for xml_link in xml_links:
                xml_urls = scrape_sitemap_urls(xml_link)
                contact_urls = [contact_url for contact_url in xml_urls if any(word in contact_url.lower() for word in ['contact', 'about', 'reach us', 'email us'])]
                contact_links.extend(contact_urls)
        else:
            contact_urls = [contact_url for contact_url in sub_urls if any(word in contact_url.lower() for word in ['contact', 'about', 'reach us', 'email us'])]
            contact_links.extend(contact_urls)

    return contact_links

def process_email_urls(urls):
    email_list = []

    for url in urls:
        try:
            response = session.get(url, timeout=40)  # Use requests_html library
            response.raise_for_status()  # Raise an exception if there's an HTTP error

            elements = response.html.find('*')

            for element in elements:
                email = element.text.strip()

                # Check if email matches the desired formats
                if validate_email(email) or email.startswith('mailto:'):
                    # Extract the email address from the mailto: format if necessary
                    if email.startswith('mailto:'):
                        email = email.replace('mailto:', '')

                    email_list.append(email)

        except requests.exceptions.RequestException as e:
            print(f"Error processing URL: {url}")
            print(e)
            continue

    return email_list

def process_csv(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        urls = [row[0] for row in reader]

    contact_links = find_contact_links(urls)

    email_addresses = process_email_urls(contact_links)

    if not email_addresses:
        print("No email addresses found.")

    return email_addresses

# Example usage
csv_file = '/Users/Khalid/Desktop/test.csv'
email_addresses = process_csv(csv_file)

for email in email_addresses:
    print(email)

