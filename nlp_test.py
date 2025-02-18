import re
import html
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize

# Ensure you have downloaded the stopwords and punkt tokenizer
nltk.download("stopwords")
nltk.download("punkt")

def clean_text(text):
    """Cleans and preprocesses Confluence article content."""
    if pd.isna(text):  # Handle NaN values
        return ""

    # Remove color codes or formatting characters (hex codes like #EAE6FF)
    text = re.sub(r'#\S+', '', text)

    # Convert HTML to plain text
    text = html.unescape(text)  # Convert HTML entities
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")  # Extract visible text

    # Normalize spaces and remove excessive newlines
    text = re.sub(r'\s+', ' ', text).strip()

    # Convert text to lowercase (if case insensitivity is required)
    text = text.lower()

    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    words = text.split()
    filtered_text = " ".join([word for word in words if word not in stop_words])

    return filtered_text

def segment_text(text, max_length=500):
    """
    Splits long articles into smaller chunks for better vector search retrieval.
    Each chunk will have a maximum length of max_length characters.
    """
    sentences = sent_tokenize(text)
    segments = []
    current_segment = ""

    for sentence in sentences:
        if len(current_segment) + len(sentence) <= max_length:
            current_segment += " " + sentence
        else:
            segments.append(current_segment.strip())
            current_segment = sentence

    # Append the last segment
    if current_segment:
        segments.append(current_segment.strip())

    return segments

# Example usage
import pandas as pd

# Load your CSV file
file_path = "test_data_con - Sheet1.csv"
df = pd.read_csv(file_path)

# Apply text cleaning
df["Cleaned_Content"] = df["Content"].apply(clean_text)

# Segment articles into smaller chunks
df["Content_Chunks"] = df["Cleaned_Content"].apply(segment_text)

# Expand segmented chunks into multiple rows
df_exploded = df.explode("Content_Chunks").reset_index(drop=True)

# Save the cleaned and structured data (optional)
df_exploded.to_csv("cleaned_confluence_data.csv", index=False)
