# 🤖 AI & Tech News Aggregator

An automated, intelligent news aggregator built in Python that crawls top AI and technology RSS feeds, evaluates article sentiment using a Hugging Face Transformer model, prevents duplicates via cryptographic hashing, stores data in SQLite, and pushes real-time alerts directly to Telegram. It runs autonomously using GitHub Actions and an external cron trigger.

---

## 🚀 Key Features

* **Multi-Source RSS Scraping:** Collects the latest articles from top industry sources (OpenAI, Google DeepMind, Hugging Face, TechCrunch, MIT Tech Review, MarkTechPost, Ars Technica, Wired, etc.)
* **Smart Deduplication:** Utilizes SHA-256 hashing on article links to ensure zero duplicates are ever inserted into the database.
* **AI Sentiment Analysis:** Integrates a pre-trained Hugging Face NLP model (`distilbert-base-uncased-finetuned-sst-2-english`) to score the sentiment of every fetched article title.
* **Telegram Integration:** Sends formatted, real-time push notifications using HTML parse mode and status emojis (🟢 Positive, 🔴 Negative, ⚪️ Neutral).
* **Cloud Automation & Persistence:** Scheduled to run seamlessly via GitHub Actions and external cron scheduling, with automatic state persistence (SQLite database version control).

---

## 🛠️ Tech Stack

* **Language:** Python 3.12
* **Parsing & Networking:** `feedparser`, `requests`
* **Database:** SQLite3 (with unique constraints and rowcount logic)
* **Machine Learning / NLP:** PyTorch & Hugging Face `transformers`
* **Environment & Config:** `python-dotenv`
* **CI/CD & Automation:** GitHub Actions & `cron-job.org`

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/cucubogdan00/ai_news_aggregator.git
cd ai_news_aggregator
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate 

# On Windows use:
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a .env file in the root directory and add your Telegram credentials
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

### 5. 🕹️ Usage
```bash
python scraper.py
```

--- 

## 🔄 Automation (CI/CD)

The project runs completely autonomously via **GitHub Actions** and an external scheduler (**cron-job.org**):

1. **Trigger:** An external cron job pings the GitHub repository dispatch API.
2. **Execution:** GitHub Actions spins up an ephemeral runner, installs dependencies, and executes `scraper.py`.
3. **Persistence:** The updated `news.db` file (containing historical state memory) is automatically committed and pushed back to the repository by the bot.

---

## Author
Bogdan Cucu - https://github.com/cucubogdan00

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.