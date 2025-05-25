#!/usr/bin/env python
"""
Database utility functions for connecting to MySQL and performing common operations.
"""

import os
import pymysql
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MySQL connection details from environment variables
MYSQL_HOST = os.getenv('DB_HOST')
MYSQL_PORT = int(os.getenv('DB_PORT', 3306))
MYSQL_DB = os.getenv('DB_NAME')
MYSQL_USER = os.getenv('DB_USER')
MYSQL_PASSWORD = os.getenv('DB_PASSWORD')

def get_mysql_connection():
    """
    Get a connection to the MySQL database using environment variables.
    """
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to MySQL database: {e}")
        raise

def ensure_tables_exist(conn):
    """
    Ensure that the required tables exist in the MySQL database.
    """
    cursor = conn.cursor()
    
    # Create projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        date DATE,
        category VARCHAR(255),
        num INTEGER,
        href TEXT,
        PRIMARY KEY (date, category)
    )
    """)
    
    # Create freelances table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS freelances (
        date DATE,
        category VARCHAR(255),
        num INTEGER,
        href TEXT,
        PRIMARY KEY (date, category)
    )
    """)
    
    conn.commit()
    cursor.close()

def save_to_mysql(data, table_name):
    """
    Save data to MySQL database.
    
    Args:
        data: List of dictionaries or DataFrame with data to save
        table_name: Name of the table to save data to ('projects' or 'freelances')
    """
    # Convert to DataFrame if it's a list
    if isinstance(data, list):
        if isinstance(data[0], dict):
            df = pd.DataFrame(data)
        else:
            # Assume it's a list of lists with [date, category, num] format
            df = pd.DataFrame(data, columns=['date', 'category', 'num'])
            df['href'] = ''  # Add empty href column if not present
    else:
        df = data
    
    # Standardize date format
    df['date'] = pd.to_datetime(df['date']).dt.strftime("%Y-%m-%d")
    
    # Connect to MySQL
    conn = get_mysql_connection()
    
    try:
        # Ensure tables exist
        ensure_tables_exist(conn)
        
        # Insert data in batches
        cursor = conn.cursor()
        batch_size = 1000
        total_records = len(df)
        records_added = 0
        
        for i in range(0, total_records, batch_size):
            batch = df.iloc[i:i+batch_size]
            
            # Prepare the values for insertion
            values = []
            for _, row in batch.iterrows():
                values.append((
                    row['date'], 
                    row['category'], 
                    int(row['num']) if isinstance(row['num'], str) and row['num'].isdigit() else row['num'],
                    row.get('href', '')
                ))
            
            # Insert with ON DUPLICATE KEY UPDATE
            query = f"""
            INSERT INTO {table_name} (date, category, num, href)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            num = VALUES(num),
            href = VALUES(href)
            """
            
            cursor.executemany(query, values)
            conn.commit()
            records_added += len(batch)
            
        # Count records for today
        today_str = df['date'].iloc[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE date = %s", (today_str,))
        count = cursor.fetchone()[0]
        
        print(f"Added/updated {records_added} records in {table_name}. Total records for today: {count}")
        
    finally:
        conn.close()
