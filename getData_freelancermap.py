from bs4 import BeautifulSoup
from datetime import datetime
import time
import csv
import os
from playwright.sync_api import sync_playwright


now = datetime.now()
current_time = now.strftime("%Y-%m-%d")
print("Current Time =", current_time)

project_path = os.path.dirname(os.path.realpath(__file__)) + "/"


#GET PROJEKTE DATA
start_url = "https://www.freelancermap.de/projektboerse.html"
# all the data points are at this level
data = []


#header row
#data.append(["date","job_group","num_jobs", "href"])

# Define the URL you want to visit
url = 'https://www.freelancermap.de/projektboerse.html'

# Launch a browser (Chromium by default)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    
    # Create a new browser page
    page = browser.new_page()
    
    # Navigate to the URL
    page.goto(url)

    # Function to check if inner text of any element with class 'show-more-button' is 'weniger anzeigen'
    def check_inner_text(button):
        inner_text = button.inner_text()
        if inner_text.strip() == 'weniger anzeigen':
            return True
        return False
    
    # Click on all elements with class 'show-more-button' until inner text is 'weniger anzeigen'
    show_more_buttons = page.query_selector_all('.show-more-button')
    for button in show_more_buttons:
        while not check_inner_text(button):
            button.click()
            time.sleep(1)  # Wait 1 second between clicks

    # Print a message indicating that the process is done
    print("All 'show-more-button' elements have been clicked until 'weniger anzeigen'")
    
    # Get the page content
    page_content = page.content()
    
    time.sleep(10)
    # Close the browser
    browser.close()

#bs4 the page content
soup = BeautifulSoup(page_content, "html.parser")
    
# Find the element with id "project-search"
elements = soup.find_all('div', class_="checkbox-item")

for el in elements:
    count = el.find('span',class_='count').text.strip().replace(".","")
    item = el.find('span',class_='item-name').text.strip()
    data.append([current_time,item, count])

print(len(elements))


# Save data to CSV file
with open(project_path + 'freelancermap_project_data.csv', 'a', newline='', encoding='utf-8' ) as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=";")
    csvwriter.writerows(data)

