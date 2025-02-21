import os
import re
import pdfplumber
import pandas as pd
from tqdm import tqdm
import spacy
from nltk.tokenize import sent_tokenize
import nltk

# Download NLTK data (punkt tokenizer)
nltk.download('punkt')

# Load spaCy model for NLP tasks
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in tqdm(pdf.pages, desc="Extracting pages"):
            text += page.extract_text() or ""
    return text

def clean_text(text):
    """Clean the extracted text."""
    # Remove headers, footers, and page numbers
    text = re.sub(r"Page \d+ of \d+", "", text)
    text = re.sub(r"ARISTA\s+User Manual\s+Version \d+\.\d+\.\d+", "", text)
    text = re.sub(r"\n\s*\n", "\n", text)  # Remove extra newlines
    return text.strip()

def tokenize_text(text):
    """Tokenize text into sentences and paragraphs."""
    sentences = sent_tokenize(text)
    paragraphs = text.split("\n\n")
    return sentences, paragraphs

def extract_code_snippets(text):
    """Extract code snippets using regex."""
    code_pattern = re.compile(r"switch\(config\)#.*")
    code_snippets = code_pattern.findall(text)
    return code_snippets

def save_data(data, output_dir, filename):
    """Save data to a file."""
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
        if isinstance(data, list):
            f.write("\n".join(data))
        else:
            f.write(data)

def preprocess_pdf(pdf_path, output_dir):
    """Preprocess the entire PDF."""
    print(f"Processing {pdf_path}...")
    text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_text(text)
    sentences, paragraphs = tokenize_text(cleaned_text)
    code_snippets = extract_code_snippets(cleaned_text)

    # Save processed data
    save_data(cleaned_text, output_dir, "cleaned_text.txt")
    save_data(sentences, output_dir, "sentences.txt")
    save_data(paragraphs, output_dir, "paragraphs.txt")
    save_data(code_snippets, os.path.join(output_dir, "code_snippets"), "code_snippets.txt")

    print(f"Saved processed data to {output_dir}")

if __name__ == "__main__":
    # Path to the Arista manual PDF
    pdf_path = "data/raw/arista.pdf"
    output_dir = "data/processed"

    # Run preprocessing
    preprocess_pdf(pdf_path, output_dir)
