import feedparser
import requests
import hashlib
import sqlite3
import os
import time 
import logging
import re

from dotenv import load_dotenv
from database import init_db
from transformers import pipeline
from config import RSS_SOURCES, HEADERS, DB_NAME
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class BaseScraper(ABC):

    @abstractmethod
    def scrape(self, url: str) -> list[dict]:
        pass

class RssScraper(BaseScraper):

    def scrape(self, url: str) -> list[dict]:
        logging.info(f'Scraping RSS source: {url}')
        articles = []
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.text)

                for entry in feed.entries:
                    title = getattr(entry, 'title', None)
                    link = getattr(entry, 'link', None)

                    if not title or not link:
                        logging.warning(f"Skipping an invalid entry in {url}: missing title or link.")
                        continue

                    raw_tags = getattr(entry, 'tags', [])
                    tags_list = [tag.get('term', '') for tag in raw_tags if tag.get('term')]
                    tags_str = ", ".join(tags_list[:3]) if tags_list else "AI News"

                    articles.append({
                        'title': title.strip(),
                        'link': link.strip(),
                        'summary': getattr(entry, 'summary', 'N/A'),
                        'published': getattr(entry, 'published', 'N/A'),
                        'source_url': url,
                        'tags' : tags_str
                    })
            else:
                logging.error(f"Failed to fetch {url}, status code: {response.status_code}")
        except Exception as e:
            logging.error(f"An error occurred while fetching {url}: {e}")
            
        return articles

def load_sentiment_analyzer():
    logging.info('Loading sentiment analysis model...')
    return pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

def process_and_save_articles(scraper : BaseScraper, urls: list, analyzer) -> list:
    new_articles = []

    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()

        for url in urls:
            raw_data = scraper.scrape(url)
            for article in raw_data:
                sentiment_score = 0.0
                try:
                    analysis_result = analyzer(article['title'][:512])[0]
                    label = analysis_result['label']
                    confidence = analysis_result['score']
                    sentiment_score = -float(confidence) if label == 'NEGATIVE' else float(confidence)
                except Exception as sentiment_error:
                    logging.error(f"Sentiment analysis error: {sentiment_error}")

                article_id = hashlib.sha256(article['link'].encode('utf-8')).hexdigest()

                cursor.execute("""
                    INSERT OR IGNORE INTO articles (id, title, link, summary, published_at, created_at, source, sentiment_score, tags)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?, ?)
                    """, (
                        article_id,
                        article['title'], 
                        article['link'], 
                        article['summary'], 
                        article['published'], 
                        article['source_url'],
                        sentiment_score,
                        article['tags']
                    ))

                if cursor.rowcount == 1:
                    logging.info(f"New article saved: {article['title'][:50]}... (Score: {sentiment_score:.4f})")
                    new_articles.append(
                        {
                            'title' : article['title'],
                            'link' : article['link'],
                            'sentiment_score' : sentiment_score,
                            'tags' : article['tags']
                        }
                    )

            connection.commit()   
       
    return new_articles

def send_telegram_notifications(articles):
    if not articles:
        return

    logging.info(f"Sending {len(articles)} notifications to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    for article in articles:
        score = article.get('sentiment_score', 0.0)
        sentiment_emoji = "🟢 Positive" if score >= 0.5 else "🔴 Negative" if score <= -0.5 else "⚪️ Neutral"

        raw_tags = article.get('tags', 'AINews').split(',')
        formatted_hashtags = " ".join([f"#{re.sub(r'[^a-zA-Z0-9]', '', tag.title())}" for tag in raw_tags if tag.strip()])

        message_text = (
            f"🚨 <b>New AI Article!</b>\n\n"
            f"<b>Title:</b> {article['title']}\n"
            f"<b>Sentiment:</b> {sentiment_emoji} (Score: {score:.2f})\n"
            f"<i>{formatted_hashtags}</i>"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text" : "🔗 Read Full Article",
                        "url" : article['link']
                    }
                ]
            ]
        }


        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message_text,
            'parse_mode': 'HTML',
            'reply_markup' : reply_markup
        }

        try:
            telegram_response = requests.post(url, json=payload)
            if telegram_response.status_code != 200:
                logging.error(f"Failed to send message: {telegram_response.text}")
        except Exception as e:
            logging.error(f"Error sending to Telegram: {e}")

        time.sleep(1.5)

def main():
    init_db()
    analyzer = load_sentiment_analyzer()

    current_scraper = RssScraper()

    new_articles = process_and_save_articles(current_scraper, RSS_SOURCES, analyzer)
    logging.info(f"Scraping finished. Found {len(new_articles)} new articles.")

    send_telegram_notifications(new_articles)
    logging.info("Process completed successfully.")

if __name__ == "__main__":
    main()