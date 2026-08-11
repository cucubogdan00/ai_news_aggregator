import feedparser
import requests
import hashlib
import sqlite3


rss_sources = [
        "https://openai.com/news/rss.xml",
        "https://blog.google/technology/ai/rss/",
        "https://www.anthropic.com/news/rss.xml",
        "https://huggingface.co/blog/feed.xml",
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://news.ycombinator.com/rss",
        "https://news.mit.edu/rss/topic/artificial-intelligence",
        "https://paperswithcode.com/rss/latest",
        "https://thegradient.pub/rss/",
        "https://www.kdnuggets.com/feed",
        "https://arstechnica.com/tag/ai/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://www.wired.com/feed/tag/ai/latest/rss",
        "https://venturebeat.com/category/ai/feed/"
    ]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

connection = sqlite3.connect('news.db')
cursor = connection.cursor()

for url in rss_sources:
    print(f'Fetching source: {url}')
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries:
                print('Title: ' , entry.title)
                print('Link: ', entry.link)
                print('Published at: ', getattr(entry, 'published', 'N/A'))
                print('-' * 40)


                article_id = hashlib.sha256(entry.link.encode('utf-8')).hexdigest()

                cursor.execute("""
                    INSERT OR IGNORE INTO articles (id, title, link, summary, published_at, created_at, source)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
                    """, (article_id, entry.title, entry.link, getattr(entry, 'summary', 'N/A'), getattr(entry, 'published', 'N/A'), url))

            connection.commit()   
        else:
            print(f"Failed to fetch {url}, status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred while fetching {url}: {e}")

connection.close()