import sqlite3

from config.settings import DB_NAME

def init_db():

    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()

        # Write-Ahead Logging
        cursor.execute("PRAGMA journal_mode=WAL;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles(
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT NOT NULL UNIQUE,
                summary TEXT,
                published_at TEXT,
                created_at TEXT,
                source TEXT,
                sentiment_score REAL,
                tags TEXT
                )       
            """)

        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN tags TEXT DEFAULT 'AI News'")
        except sqlite3.OperationalError:
            pass
        
        connection.commit()
        

if __name__ == "__main__":
    init_db()
