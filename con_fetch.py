import os
import requests
import sqlite3
import html2text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Confluence API credentials
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
BASE_URL = "https://plivo-team.atlassian.net/wiki"
SPACE_KEY = "PSA"

# SQLite database file
DB_FILE = "confluence_data.db"

# Headers for Confluence API
HEADERS = {
    "Accept": "application/json"
}

# Convert HTML to plain text
def convert_html_to_text(html_content):
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = True
    return converter.handle(html_content)

# Create SQLite database and table
def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            article_id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Fetch articles from Confluence
def fetch_articles():
    url = f"{BASE_URL}/rest/api/space/{SPACE_KEY}/content?expand=body.storage"
    
    auth = (CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)
    response = requests.get(url, headers=HEADERS, auth=auth)

    if response.status_code == 200:
        data = response.json()
        articles = data.get("page", {}).get("results", [])
        return articles
    else:
        print(f"❌ Error fetching articles: {response.status_code} - {response.text}")
        return []

# Store articles in SQLite
def store_articles(articles):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for article in articles:
        article_id = article["id"]
        title = article["title"]
        html_content = article.get("body", {}).get("storage", {}).get("value", "")
        plain_text_content = convert_html_to_text(html_content)

        cursor.execute(
            "INSERT OR REPLACE INTO articles (article_id, title, content) VALUES (?, ?, ?)",
            (article_id, title, plain_text_content),
        )

    conn.commit()
    conn.close()
    print(f"✅ {len(articles)} articles stored successfully.")

# Main function
def main():
    print("🚀 Fetching articles from Confluence...")
    initialize_database()
    articles = fetch_articles()
    if articles:
        store_articles(articles)
    else:
        print("⚠️ No articles found.")

if __name__ == "__main__":
    main()
