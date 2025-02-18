import os
import requests
import csv
import html2text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Confluence API credentials
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
BASE_URL = "https://plivo-team.atlassian.net/wiki"
SPACE_KEY = "PSA"

# Headers for Confluence API
HEADERS = {
    "Accept": "application/json"
}

# CSV file name
CSV_FILE = "confluence_articles.csv"

# Convert HTML to plain text
def convert_html_to_text(html_content):
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = True
    return converter.handle(html_content)

# Fetch articles from Confluence
def fetch_articles():
    url = url = f"{BASE_URL}/rest/api/content?spaceKey={SPACE_KEY}&expand=body.storage"


    auth = (CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)
    response = requests.get(url, headers=HEADERS, auth=auth)

    if response.status_code == 200:
        data = response.json()
        articles = data.get("results", [])
        return articles
    else:
        print(f"❌ Error fetching articles: {response.status_code} - {response.text}")
        return []

# Save articles to CSV
def save_articles_to_csv(articles):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write header row
        writer.writerow(["Article ID", "Title", "Content"])

        for article in articles:
            article_id = article["id"]
            title = article["title"]
            html_content = article.get("body", {}).get("storage", {}).get("value", "")
            plain_text_content = convert_html_to_text(html_content)

            # Write row
            writer.writerow([article_id, title, plain_text_content])

    print(f"✅ {len(articles)} articles saved to {CSV_FILE}.")

# Main function
def main():
    print("🚀 Fetching articles from Confluence...")
    articles = fetch_articles()
    
    if articles:
        save_articles_to_csv(articles)
    else:
        print("⚠️ No articles found.")

if __name__ == "__main__":
    main()
