import feedparser
import requests
import hashlib
import sqlite3
import os

from dotenv import load_dotenv
from database import init_db
from transformers import pipeline

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

init_db()

print('Loading sentiment analysis model...')
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

new_articles = []

rss_sources = [
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

                sentiment_score = 0.0
                try:
                    analysis_result = sentiment_analyzer(entry.title[:512])[0]
                    label = analysis_result['label']
                    confidence = analysis_result['score']

                    if label == 'NEGATIVE':
                        sentiment_score = -float(confidence)
                    else:
                        sentiment_score = float(confidence)
                except Exception as sentiment_error:
                    print(f"Sentiment analysis error: {sentiment_error}")

                print(f"Sentiment Score: {sentiment_score:.4f}")
                print('-' * 40)


                article_id = hashlib.sha256(entry.link.encode('utf-8')).hexdigest()

                cursor.execute("""
                    INSERT OR IGNORE INTO articles (id, title, link, summary, published_at, created_at, source, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?)
                    """, (
                        article_id,
                        entry.title, 
                        entry.link, 
                        getattr(entry, 'summary', 'N/A'), 
                        getattr(entry, 'published', 'N/A'), 
                        url,
                        sentiment_score
                    ))

                if cursor.rowcount == 1:
                    new_articles.append(
                        {
                            'title' : entry.title,
                            'link' : entry.link,
                            'sentiment_score' : sentiment_score
                        }
                    )

            connection.commit()   
        else:
            print(f"Failed to fetch {url}, status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred while fetching {url}: {e}")

connection.close()

print(f"Scraping finished. Found {len(new_articles)} new articles.")

if len(new_articles) > 0:
    print("Sending notifications to Telegram...")

    for article in new_articles:
        score = article.get('sentiment_score', 0.0)

        if score >= 0.5:
            sentiment_emoji = "🟢 Positive"
        elif score <= -0.5:
            sentiment_emoji = "🔴 Negative"
        else:
            sentiment_emoji = "⚪️ Neutral"

        message_text = (
            f"🚨 <b>New AI Article!</b>\n\n"
            f"<b>Title:</b> {article['title']}\n"
            f"<b>Sentiment:</b> {sentiment_emoji} (Score: {score:.2f})\n"
            f"<b>Link:</b> {article['link']}"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message_text,
            'parse_mode': 'HTML'
        }

        try:
            telegram_response = requests.post(url, json=payload)
            if telegram_response.status_code != 200:
                print(f"Failed to send message: {telegram_response.text}")
        except Exception as e:
            print(f"Error sending to Telegram: {e}")

print("Process completed successfully.")