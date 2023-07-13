
from django.shortcuts import render
from django import forms
from requests_html import HTMLSession
from urllib.parse import urljoin
from validate_email_address import validate_email
import csv
import os
import requests.exceptions
import time

visited_urls = set()
email_addresses = []
csv_data = []

anchor_texts = [
    "Contact Us",
    "About",
    "About Us",
    "about",
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

class CSVUploadForm(forms.Form):
    file = forms.FileField()

def process_url(url, main_url):
    email_found = False

    try:
        session = HTMLSession()
        response = session.get(url, timeout=40)
        response.raise_for_status()

        elements = response.html.find('*')
        for element in elements:
            email = element.text.strip()

            # Check if email matches the desired formats
            if validate_email(email) or email.startswith('mailto:'):
                # Extract the email address from the mailto: format if necessary
                if email.startswith('mailto:'):
                    email = email.replace('mailto:', '')

                email_addresses.append(email)
                email_found = True
                break

        if email_found:
            if main_url == url or not any(entry[0] == main_url for entry in csv_data):
                update_csv_data(main_url, email)
        else:
            links = response.html.find('a')

            # Check if any link anchor text matches the desired texts
            priority_links = [link for link in links if any(text in link.text for text in anchor_texts)]
            remaining_links = [link for link in links if link not in priority_links]

            for link in priority_links:
                link_url = urljoin(url, link.attrs.get('href', ''))
                if link_url not in visited_urls:
                    visited_urls.add(link_url)
                    process_url(link_url, main_url)

        if not email_found and main_url == url and not any(entry[0] == main_url for entry in csv_data):
            update_csv_data(main_url, "No email found")

    except requests.exceptions.Timeout:
        print(f"Timeout: Skipping URL: {url}")
        update_csv_data(url, "Timeout")

    except requests.exceptions.RequestException as e:
        print(f"Error processing URL: {url}")
        print(e)
        update_csv_data(url, str(e))



def update_csv_data(url, email):
    csv_data[:] = [entry for entry in csv_data if entry[0] != url]
    csv_data.append([url, email])

def process_csv(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        urls = [row[0] for row in reader]

    start_time = time.time()
    for url in urls:
        if time.time() - start_time > 40:
            print(f"Timeout: Skipping URL: {url}")
            update_csv_data(url, "Timeout")
            continue

        try:
            visited_urls.clear()
            visited_urls.add(url)
            process_url(url, url)

        except requests.exceptions.RequestException as e:
            print(f"Error processing URL: {url}")
            print(e)
            update_csv_data(url, str(e))
            continue

    if not email_addresses and len(csv_data) > 1:
        print(f"No email scraped for any URL in the website")
        update_csv_data(csv_data[1][0], "No email found")

    return email_addresses

def save_to_csv(data, file_path):
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            # Save the uploaded file temporarily
            file_path = '/tmp/' + csv_file.name
            with open(file_path, 'wb') as file:
                for chunk in csv_file.chunks():
                    file.write(chunk)

            # Process the CSV file
            email_addresses = process_csv(file_path)

            # Save email addresses and URLs to a CSV file
            save_to_csv(csv_data, '/Users/Khalid/Desktop/results.csv')

            # Delete the temporary file
            os.remove(file_path)

            # Pass the email addresses to the template for display
            return render(request, 'app/results.html', {'email_addresses': email_addresses})
    else:
        form = CSVUploadForm()
    return render(request, 'app/upload.html', {'form': form})

