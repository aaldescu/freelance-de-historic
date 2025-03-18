# freelance_spider.py
import scrapy
import sqlite3
import pandas as pd
from datetime import datetime
import time
from scrapy_impersonate.middleware import ImpersonateMiddleware

class FreelanceSpider(scrapy.Spider):
    name = 'freelance'
    allowed_domains = ['freelance.de']
    start_urls = ['https://www.freelance.de']
    
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_impersonate.middleware.ImpersonateMiddleware': 950,
        },
        'IMPERSONATE_BROWSER': 'chrome',  # Use Chrome browser for impersonation
    }
    
    def __init__(self, *args, **kwargs):
        super(FreelanceSpider, self).__init__(*args, **kwargs)
        self.jobs_data = []
        self.freelancers_data = []
    
    def parse(self, response):
        # Handle cookie consent if present
        if response.css('#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll'):
            yield scrapy.FormRequest.from_response(
                response,
                formxpath='//button[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]',
                callback=self.after_cookie_consent
            )
        else:
            yield from self.after_cookie_consent(response)
    
    def after_cookie_consent(self, response):
        # Start with jobs data
        yield scrapy.Request(
            url='https://www.freelance.de/projekte',
            callback=self.parse_jobs_main,
            meta={'data_type': 'jobs'}
        )
    
    def parse_jobs_main(self, response):
        # Check if "Alle anzeigen" button is present and follow it
        show_all = response.css('a.badge:contains("Alle anzeigen")::attr(href)').get()
        if show_all:
            yield response.follow(show_all, self.parse_jobs_categories, meta={'data_type': 'jobs'})
        else:
            yield from self.parse_jobs_categories(response)
    
    def parse_jobs_categories(self, response):
        # Extract main categories
        main_categories = self.extract_data(response, 'jobs')
        for item in main_categories:
            self.jobs_data.append(item)
            if item['href']:
                yield response.follow(
                    item['href'],
                    callback=self.parse_subcategories,
                    meta={'data_type': 'jobs'}
                )
        
        # After processing all job categories, move to freelancers
        yield scrapy.Request(
            url='https://www.freelance.de/Freelancer',
            callback=self.parse_freelancers_main,
            meta={'data_type': 'freelancers'}
        )
    
    def parse_freelancers_main(self, response):
        # Check if "Alle anzeigen" button is present and follow it
        show_all = response.css('a.badge:contains("Alle anzeigen")::attr(href)').get()
        if show_all:
            yield response.follow(show_all, self.parse_freelancers_categories, meta={'data_type': 'freelancers'})
        else:
            yield from self.parse_freelancers_categories(response)
    
    def parse_freelancers_categories(self, response):
        # Extract main categories
        main_categories = self.extract_data(response, 'freelancers')
        for item in main_categories:
            self.freelancers_data.append(item)
            if item['href']:
                yield response.follow(
                    item['href'],
                    callback=self.parse_subcategories,
                    meta={'data_type': 'freelancers'}
                )
    
    def parse_subcategories(self, response):
        data_type = response.meta.get('data_type', 'jobs')
        # Check if "Alle anzeigen" button is present and follow it
        show_all = response.css('a.badge:contains("Alle anzeigen")::attr(href)').get()
        if show_all:
            yield response.follow(
                show_all, 
                self.extract_subcategory_data, 
                meta={'data_type': data_type}
            )
        else:
            yield from self.extract_subcategory_data(response)
    
    def extract_subcategory_data(self, response):
        data_type = response.meta.get('data_type', 'jobs')
        subcategory_data = self.extract_data(response, data_type)
        
        if data_type == 'jobs':
            self.jobs_data.extend(subcategory_data)
        else:
            self.freelancers_data.extend(subcategory_data)
    
    def extract_data(self, response, data_type='jobs'):
        data = []
        
        if data_type == 'jobs':
            list_items = response.xpath("//div[@class='mt-2']//ul[contains(@class, 'list-inline')]//li")
            for item in list_items:
                anchor = item.xpath('./a')
                if anchor:
                    text = anchor.xpath('./text()').get('').strip()
                    text = text.split('(')[0].strip()
                    href = anchor.xpath('./@href').get('')
                    count = item.xpath('./span[@class="ms-2"]/text()').get('0')
                    count = count.strip('()')
                    
                    data.append({
                        'category': text,
                        'href': href,
                        'num_jobs': count,
                        'date': datetime.now().strftime("%Y-%m-%d")
                    })
        else:
            list_items = response.xpath("//div[@class='row margin-top-xs']//ul//li")
            for item in list_items:
                anchor = item.xpath('./a')
                if anchor:
                    text = anchor.xpath('./text()').get('').strip()
                    href = anchor.xpath('./@href').get('')
                    count = item.xpath('./span/text()').get('0')
                    count = count.strip().strip('[]')
                    
                    data.append({
                        'category': text,
                        'href': href,
                        'num_freelancers': count,
                        'date': datetime.now().strftime("%Y-%m-%d")
                    })
        
        return data
    
    def closed(self, reason):
        """Save data to database when spider is closed"""
        self.save_to_db(self.jobs_data, 'projects')
        self.save_to_db(self.freelancers_data, 'freelances')
        self.logger.info("Data has been saved to database")
    
    def save_to_db(self, data, table_name):
        conn = sqlite3.connect('freelance_projects.db')
        cursor = conn.cursor()
        
        # Convert data to pandas DataFrame
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Write to database - append instead of replace
            df.to_sql(table_name, conn, if_exists='append', index=False)
            
            # Create indices if they don't exist
            if table_name == 'projects':
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON projects(date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON projects(category)')
            else:
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_freelance_date ON freelances(date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_freelance_category ON freelances(category)')
            
            # Get count of records inserted
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE date = ?", (df['date'].iloc[0].strftime("%Y-%m-%d"),))
            count = cursor.fetchone()[0]
            self.logger.info(f"Added {len(df)} records to {table_name}. Total records for today: {count}")
        else:
            self.logger.warning(f"No data to save for {table_name}")
        
        conn.commit()
        conn.close()