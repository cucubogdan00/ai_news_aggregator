import feedparser
import requests
import hashlib
import sqlite3
import os
import time 

from dotenv import load_dotenv
from database import init_db
from transformers import pipeline
from config import RSS_SOURCES, HEADERS

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def load_sentiment_analyzer():
    print('Loading sentiment analysis model...')
    return pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

def fetch_and_analyze_articles(analyzer):
    new_articles = []

    with sqlite3.connect('news.db') as connection:
        cursor = connection.cursor()

        for url in RSS_SOURCES:
            print(f'Fetching source: {url}')
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    feed = feedparser.parse(response.text)
                    
                    for entry in feed.entries:
                        print('Title: ' , entry.title)
                        print('Link: ', entry.link)
                        print('Published at: ', getattr(entry, 'published', 'N/A'))

                        sentiment_score = 0.0
                        try:
                            analysis_result = analyzer(entry.title[:512])[0]
                            label = analysis_result['label']
                            confidence = analysis_result['score']
                            sentiment_score = -float(confidence) if label == 'NEGATIVE' else float(confidence)
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

        return new_articles

def send_telegram_notifications(articles):
    if not articles:
        return

    print("Sending notifications to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    for article in articles:
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

    new_articles = fetch_and_analyze_articles(analyzer)
    print(f"Scraping finished. Found {len(new_articles)} new articles.")

    send_telegram_notifications(new_articles)
    print("Process completed successfully.")

if __name__ == "__main__":
    main()