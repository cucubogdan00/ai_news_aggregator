import feedparser
import requests
import hashlib
import sqlite3
import os
import time 

from dotenv import load_dotenv
from database import init_db
from transformers import pipeline
from config import RSS_SOURCES, HEADERS, DB_NAME
from abc import ABC, abstractmethod

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class BaseScraper(ABC):

    @abstractmethod
    def scrape(self, url: str) -> list[dict]:
        pass

class RssScraper(BaseScraper):

    def scrape(self, url: str) -> list[dict]:
        print(f'Scraping RSS source: {url}')
        articles = []
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.text)

                for entry in feed.entries:
                    title = getattr(entry, 'title', None)
                    link = getattr(entry, 'link', None)

                    if not title or not link:
                        print(f"Skipping an invalid entry in {url}: missing title or link.")
                        continue

                    articles.append({
                        'title': title.strip(),
                        'link': link.strip(),
                        'summary': getattr(entry, 'summary', 'N/A'),
                        'published': getattr(entry, 'published', 'N/A'),
                        'source_url': url
                    })
            else:
                print(f"Failed to fetch {url}, status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred while fetching {url}: {e}")
            
        return articles

def load_sentiment_analyzer():
    print('Loading sentiment analysis model...')
    return pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

def process_and_save_articles(scraper : BaseScraper, urls: list, analyzer) -> list:
    new_articles = []

    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()

        for url in urls:
            raw_data = scraper.scrape(url)
            for article in raw_data:
                print(f"Title: {article['title']}")
                print(f"Link: {article['link']}")
                print(f"Published at: {article['published']}")

                sentiment_score = 0.0
                try:
                    analysis_result = analyzer(article['title'][:512])[0]
                    label = analysis_result['label']
                    confidence = analysis_result['score']
                    sentiment_score = -float(confidence) if label == 'NEGATIVE' else float(confidence)
                except Exception as sentiment_error:
                    print(f"Sentiment analysis error: {sentiment_error}")

                print(f"Sentiment Score: {sentiment_score:.4f}")
                print('-' * 40)


                article_id = hashlib.sha256(article['link'].encode('utf-8')).hexdigest()

                cursor.execute("""
                    INSERT OR IGNORE INTO articles (id, title, link, summary, published_at, created_at, source, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?)
                    """, (
                        article_id,
                        article['title'], 
                        article['link'], 
                        article['summary'], 
                        article['published'], 
                        article['source_url'],
                        sentiment_score
                    ))

                if cursor.rowcount == 1:
                    new_articles.append(
                        {
                            'title' : article['title'],
                            'link' : article['link'],
                            'sentiment_score' : sentiment_score
                        }
                    )

            connection.commit()   
       
    return new_articles

def send_telegram_notifications(articles):
    if not articles:
        return

    print("Sending notifications to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    for article in articles:
        score = article.get('sentiment_score', 0.0)

        sentiment_emoji = "🟢 Positive" if score >= 0.5 else "🔴 Negative" if score <= -0.5 else "⚪️ Neutral"

        message_text = (
            f"🚨 <b>New AI Article!</b>\n\n"
            f"<b>Title:</b> {article['title']}\n"
            f"<b>Sentiment:</b> {sentiment_emoji} (Score: {score:.2f})\n"
            f"<b>Link:</b> {article['link']}"
        )

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

        time.sleep(1.5)

def main():
    init_db()
    analyzer = load_sentiment_analyzer()

    current_scraper = RssScraper()

    new_articles = process_and_save_articles(current_scraper, RSS_SOURCES, analyzer)
    print(f"Scraping finished. Found {len(new_articles)} new articles.")

    send_telegram_notifications(new_articles)
    print("Process completed successfully.")

if __name__ == "__main__":
    main()