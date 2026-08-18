import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(BASE_DIR, 'data', 'news.db') 

RSS_SOURCES = [
        "https://openai.com/news/rss.xml",
        "https://blog.google/technology/ai/rss/",
        "https://deepmind.google/blog/rss.xml",
        "https://huggingface.co/blog/feed.xml",
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://news.ycombinator.com/rss",
        "https://bair.berkeley.edu/blog/feed.xml",
        "https://thegradient.pub/rss/",
        "https://www.technologyreview.com/topic/artificial-intelligence/feed",
        "https://www.marktechpost.com/feed/",
        "https://www.kdnuggets.com/feed",
        "https://arstechnica.com/ai/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://www.wired.com/feed/tag/ai/latest/rss",
        "https://venturebeat.com/category/ai/feed/"
    ]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
]