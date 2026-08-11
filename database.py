import sqlite3

def init_db():

    connection = sqlite3.connect('news.db')
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
    connection.close()

if __name__ == "__main__":
    init_db()
