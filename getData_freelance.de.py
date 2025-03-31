from playwright.sync_api import sync_playwright
from datetime import datetime
import time
import sqlite3
import pandas as pd

def extract_data(page, data_type='jobs'):
    data = []
    
    if data_type == 'jobs':
        list_items = page.query_selector_all("//div[@class='mt-2']//ul[contains(@class, 'list-inline')]//li")
        for item in list_items:
            anchor = item.query_selector('a')
            if anchor:
                text = anchor.text_content().strip()
                text = text.split('(')[0].strip()
                href = anchor.get_attribute('href')
                span = item.query_selector('span.ms-2')
                count = span.text_content().strip('()') if span else '0'
                
                data.append({
                    'category': text,
                    'href': href,
                    'num': count,
                    'date': datetime.now().strftime("%Y-%m-%d")
                })
    elif data_type == 'freelancers':
        list_items = page.query_selector_all("//div[@class='mt-2']//ul//li")
        for item in list_items:
            anchor = item.query_selector('a')
            if anchor:
                text = anchor.text_content().split('(')[0].strip()
                href = anchor.get_attribute('href')
                span = item.query_selector('span')
                count = span.text_content().strip().strip('()') if span else '0'
                
                data.append({
                    'category': text,
                    'href': href,
                    'num': count,
                    'date': datetime.now().strftime("%Y-%m-%d")
                })
    else :
        data.append({'error':'data_type case not found'})
    
    return data

def get_subcategory_data(page, url, data_type='jobs'):
    print(f"Accessing subcategory: {url}")
    page.goto(url)
    time.sleep(2)  # Wait for page to load
    
    try:
        # Click "Alle anzeigen" button if present
        show_all_button = page.query_selector('a.badge:has-text("Alle anzeigen")')
        if show_all_button:
            show_all_button.click()
            time.sleep(2)  # Wait for expanded list to load
    except Exception as e:
        print(f"Error clicking 'Alle anzeigen' button in subcategory: {e}")
    
    return extract_data(page, data_type)

def save_to_db(data, table_name):
    with sqlite3.connect('freelance_projects.db') as conn:
        cursor = conn.cursor()

        # Ensure the table exists with the updated schema
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                date TIMESTAMP,
                category TEXT,
                num INTEGER,
                href TEXT,
                UNIQUE(date, category)
            );
        """)

        # Ensure the composite index exists
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_date_category
            ON {table_name}(date, category);
        """)

        # Convert data to DataFrame and format the date
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date']).dt.strftime("%Y-%m-%d")  # Standardize date format

        # Insert data while preventing duplicates (ON CONFLICT IGNORE)
        insert_query = f"""
            INSERT OR IGNORE INTO {table_name} (date, category, num, href)
            VALUES (?, ?, ?, ?);
        """
        cursor.executemany(insert_query, df[['date', 'category', 'num', 'href']].values.tolist())

        # Count records added today
        today_str = df['date'].iloc[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE date = ?", (today_str,))
        count = cursor.fetchone()[0]

        print(f"Added {len(df)} new records (ignoring duplicates) to {table_name}. Total records for today: {count}")

        conn.commit()


def main():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)  # Set to True for headless mode
        page = browser.new_page()
        
        # Handle cookies only once at the start
        try:
            page.goto("https://www.freelance.de")
            cookie_button = page.locator('#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll')
            if cookie_button.is_visible(timeout=5000):
                cookie_button.click()
                time.sleep(2)
        except Exception as e:
            #print("Cookie popup not found or already accepted:", str(e))
            print("Cookie popup not found or already accepted. Continue ...")
                
        # Collect Jobs Data
        print("Collecting jobs data...")
        url = "https://www.freelance.de/projekte"
        page.goto(url)
        time.sleep(2)
        
        try:
            show_all_button = page.query_selector('a.badge:has-text("Alle anzeigen")')
            if show_all_button:
                show_all_button.click()
                time.sleep(2)
        except Exception as e:
            print(f"Error clicking 'Alle anzeigen' button: {e}")
        
        jobs_main_data = extract_data(page, 'jobs')
        all_jobs_data = []
        
        for item in jobs_main_data:
            all_jobs_data.append(item)
            if item['href']:
                subcategory_url = f"https://www.freelance.de{item['href']}"
                subcategory_data = get_subcategory_data(page, subcategory_url, 'jobs')
                all_jobs_data.extend(subcategory_data)
                
        # Collect Freelancers Data
        print("\nCollecting freelancers data...")
        url = "https://www.freelance.de/Freelancer"
        page.goto(url)
        time.sleep(2)
        
        try:
            show_all_button = page.query_selector('a.badge:has-text("Alle anzeigen")')
            if show_all_button:
                show_all_button.click()
                time.sleep(2)
        except Exception as e:
            print(f"Error clicking 'Alle anzeigen' button: {e}")
        
        freelancers_main_data = extract_data(page, 'freelancers')
        

        all_freelancers_data = []
        for item in freelancers_main_data:
            all_freelancers_data.append(item)
            if item['href']:
                subcategory_url = f"https://www.freelance.de{item['href']}"
                subcategory_data = get_subcategory_data(page, subcategory_url, 'freelancers')
                all_freelancers_data.extend(subcategory_data)
        
        
        # Save data to database
        print("\nSaving data to database...")
        save_to_db(all_jobs_data, 'projects')
        save_to_db(all_freelancers_data, 'freelances')
        
        print("Data has been saved to database")
        browser.close()

if __name__ == "__main__":
    main()
