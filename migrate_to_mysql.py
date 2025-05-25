#!/usr/bin/env python
"""
Migration script to transfer data from SQLite to MySQL.
This script reads data from a SQLite database and inserts it into a MySQL database.
"""

import os
import sqlite3
import pymysql
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# SQLite database path
SQLITE_DB_PATH = Path(__file__).parent / 'freelance_projects.db'

# MySQL connection details from environment variables
MYSQL_HOST = os.getenv('DB_HOST')
MYSQL_PORT = int(os.getenv('DB_PORT', 3306))
MYSQL_DB = os.getenv('DB_NAME')
MYSQL_USER = os.getenv('DB_USER')
MYSQL_PASSWORD = os.getenv('DB_PASSWORD')

def create_mysql_tables(mysql_conn):
    """Create tables in MySQL if they don't exist."""
    cursor = mysql_conn.cursor()
    
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
    
    mysql_conn.commit()
    cursor.close()

def migrate_table(sqlite_conn, mysql_conn, table_name):
    """Migrate data from SQLite table to MySQL table."""
    print(f"Migrating {table_name} table...")
    
    # Read data from SQLite
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, sqlite_conn)
    
    # Count records
    total_records = len(df)
    print(f"Found {total_records} records in SQLite {table_name} table")
    
    if total_records == 0:
        print(f"No data to migrate for {table_name}")
        return
    
    # Prepare for MySQL insertion
    cursor = mysql_conn.cursor()
    
    # Insert data in batches
    batch_size = 1000
    for i in range(0, total_records, batch_size):
        batch = df.iloc[i:i+batch_size]
        
        # Prepare the values for insertion
        values = []
        for _, row in batch.iterrows():
            values.append((row['date'], row['category'], row['num'], row['href']))
        
        # Construct and execute the query with ON DUPLICATE KEY UPDATE
        query = f"""
        INSERT INTO {table_name} (date, category, num, href)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        num = VALUES(num),
        href = VALUES(href)
        """
        
        # Execute many for batch insertion
        cursor.executemany(query, values)
        
        mysql_conn.commit()
        
        print(f"Migrated batch {i//batch_size + 1}/{(total_records + batch_size - 1)//batch_size} for {table_name}")
    
    cursor.close()
    print(f"Migration of {table_name} completed successfully")

def main():
    """Main function to handle the migration process."""
    print("Starting migration from SQLite to MySQL...")
    
    try:
        # Connect to SQLite database
        print(f"Connecting to SQLite database: {SQLITE_DB_PATH}")
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        
        # Connect to MySQL database
        print(f"Connecting to MySQL database: {MYSQL_DB} on {MYSQL_HOST}")
        mysql_conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4'
        )
        
        # Create tables in MySQL if they don't exist
        create_mysql_tables(mysql_conn)
        
        # Migrate data for each table
        migrate_table(sqlite_conn, mysql_conn, 'projects')
        migrate_table(sqlite_conn, mysql_conn, 'freelances')
        
        # Close connections
        sqlite_conn.close()
        mysql_conn.close()
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    main()
