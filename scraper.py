import feedparser
import requests
import hashlib
import sqlite3
import os
import time 
import logging
import re
import random

from dotenv import load_dotenv
from database import init_db
from transformers import pipeline
from config import RSS_SOURCES, USER_AGENTS, DB_NAME
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        articles = []
        max_retries = 3

        for attempt in range(max_retries):
            headers = {"User-Agent": random.choice(USER_AGENTS)}

            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()

                feed = feedparser.parse(response.text)

                for entry in feed.entries:
                    title = getattr(entry, 'title', None)
                    link = getattr(entry, 'link', None)

                    if not title or not link:
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
                break
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logging.warning(f"Attempt {attempt + 1} failed for {url}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Failed to fetch {url} after {max_retries} attempts: {e}")

        return articles

def load_sentiment_analyzer():
    logging.info('Loading sentiment analysis model...')
    return pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

def fetch_all_articles_concurrently(scraper : BaseScraper, urls: list[str], max_workers: int = 5) -> list[dict]:
    all_raw_articles = []
    logging.info(f"Starting concurrent scraping across {len(urls)} sources with {max_workers} workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scraper.scrape, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                articles = future.result()
                all_raw_articles.extend(articles)
            except Exception as e:
                logging.error(f"Error scraping {url} in thread: {e}")

    logging.info(f"Finished fetching feeds. Collected a total of {len(all_raw_articles)} raw entries.")
    return all_raw_articles

def process_and_save_articles(raw_data: list[dict], analyzer) -> list[dict]:
    new_articles = []

    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()

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

    raw_articles = fetch_all_articles_concurrently(current_scraper, RSS_SOURCES, max_workers=5)

    new_articles = process_and_save_articles(raw_articles, analyzer)
    logging.info(f"Scraping finished. Found {len(new_articles)} new articles.")

    send_telegram_notifications(new_articles)
    logging.info("Process completed successfully.")

if __name__ == "__main__":
    main()