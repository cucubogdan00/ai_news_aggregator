import sqlite3

from config import DB_NAME

def init_db():

    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles(
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT NOT NULL UNIQUE,
                summary TEXT,
                published_at TEXT,
                created_at TEXT,
                source TEXT,
                sentiment_score REAL
                )       
            """)
        connection.commit()
        

if __name__ == "__main__":
    init_db()
