from bs4 import BeautifulSoup
from datetime import datetime
import time
import sqlite3
import pandas as pd
import os
from playwright.sync_api import sync_playwright

# Get current date
current_time = datetime.now().strftime("%Y-%m-%d")
print("Current Time =", current_time)

def save_to_db(data):
    with sqlite3.connect('freelance_projects.db') as conn:
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                date TIMESTAMP,
                category TEXT,
                num INTEGER,
                href TEXT,
                UNIQUE(date, category)
            );
        """)

        # Ensure composite index exists
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_projects_date_category
            ON projects(date, category);
        """)

        # Convert data to DataFrame and format the date
        df = pd.DataFrame(data, columns=['date', 'category', 'num'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime("%Y-%m-%d")  # Standardize date format
        df['href'] = ''  # Ensure href column exists

        # Insert data while preventing duplicates (ON CONFLICT IGNORE)
        insert_query = """
            INSERT OR IGNORE INTO projects (date, category, num)
            VALUES (?, ?, ?);
        """
        cursor.executemany(insert_query, df[['date', 'category', 'num']].values.tolist())

        # Count records added today
        cursor.execute("SELECT COUNT(*) FROM projects WHERE date = ?", (current_time,))
        count = cursor.fetchone()[0]

        print(f"Added {len(df)} new records (ignoring duplicates) to projects. Total records for today: {count}")

        conn.commit()

#GET PROJEKTE DATA
start_url = "https://www.freelancermap.de/projektboerse.html"
data = []

# Define the URL you want to visit
url = 'https://www.freelancermap.de/projektboerse.html'

# Launch a browser (Chromium by default)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
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
    data.append([current_time, item, count])

print(f"Found {len(elements)} categories")

# Save data to database
print("\nSaving data to database...")
save_to_db(data)
print("Data has been saved to database")
