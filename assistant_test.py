from openai import OpenAI
import os
import pandas as pd
import csv
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time

# Load API Keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI Assistant ID
assistant_id = "asst_3wdSmJAfchbWa6sjoQs2KpCV"

#Initialize open AI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Load CSV Database (Local File)
CSV_FILE = "cleaned_confluence_data.csv"
if not os.path.exists(CSV_FILE):
    print("⚠️ CSV file not found! Please ensure 'cleaned_confluence_data.csv' exists.")
    exit()

articles_df = pd.read_csv(CSV_FILE)

# Extract text data
article_texts = articles_df["Content_Chunks"].fillna("")

# Initialize TF-IDF vectorizer for local text search
vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = vectorizer.fit_transform(article_texts)

#  Classify input message using OpenAI Assistant
def classify_message(user_input):
    # Step 1: Create a thread
    thread = client.beta.threads.create()

    # Step 2: Add message to the thread with a strict classification prompt
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"""
        You are a classification assistant. Your only job is to classify the input message into one of the following categories:
        - "simple notification"
        - "process update"
        - "Product release/enhancement"
        - "SOP change"

        DO NOT search any database or documents. Just return the category.

        Message: {user_input}

        Respond with only the category name.
        """
    )

    # Step 3: Run the Assistant on the thread
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # Step 4: Polling until the run completes
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status in ["completed", "failed"]:
            break
        time.sleep(1)  # Wait before checking again

    # Step 5: Get response message
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    assistant_response = messages.data[0].content[0].text.value.strip().lower()
    
    return assistant_response

# Search for the most relevant Confluence article in the CSV
def find_related_article(user_input):
    user_vector = vectorizer.transform([user_input])
    similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
    best_match_index = similarities.argmax()
    best_match_title = articles_df.iloc[best_match_index]["Title"]
    return best_match_title if similarities[best_match_index] > 0.2 else None  # Adjust threshold if needed

# Process an incoming message
def process_message(user_input):
    category = classify_message(user_input)
    print(f"🔍 Message Category: {category}")

    if category in ["process update", "product release/enhancement"]:
        article_title = find_related_article(user_input)
        if article_title:
            print(f"✅ Recommended Confluence article to update: {article_title}")
        else:
            print("⚠️ No relevant article found. Consider creating a new one.")
    else:
        print("✅ No Confluence update needed.")

# Test the system
if __name__ == "__main__":
    user_input = input("Enter a message: ")
    process_message(user_input)
