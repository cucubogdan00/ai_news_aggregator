import feedparser
import requests

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
        else:
            print(f"Failed to fetch {url}, status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred while fetching {url}: {e}")