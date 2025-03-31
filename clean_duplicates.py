import sqlite3

DB_NAME = "freelance_projects.db"

def clean_duplicates(table_name):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Delete duplicate rows, keeping only the one with the lowest ROWID
        delete_query = f"""
            DELETE FROM {table_name}
            WHERE ROWID NOT IN (
                SELECT MIN(ROWID)
                FROM {table_name}
                GROUP BY date, category
            );
        """
        
        cursor.execute(delete_query)
        conn.commit()

        # Vacuum the database to reclaim space
        cursor.execute("VACUUM;")

        print(f"Duplicates removed from {table_name}, and database optimized.")

if __name__ == "__main__":
    clean_duplicates("projects")
    clean_duplicates("freelances")
