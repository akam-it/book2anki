#!/opt/venv/bin/python3

import os
import re
import csv
import cv2
import nltk
import curses
import pytesseract
import numpy as np

from pathlib import Path
from pdf2image import convert_from_path
from nltk.corpus import words
from deep_translator import GoogleTranslator


# Path to the PDF file
PDF_FILE = "Geronimo Stilton Spacemice - Book 3 - Ice Planet Adventure.pdf"
PAGES_RANGES = [range(16, 242)]

# File paths
KNOWN_WORDS_FILE = ".KNOWN_WORDS.txt"
UNKNOWN_WORDS_FILE = f"{os.path.splitext(os.path.basename(PDF_FILE))[0]}.csv"

# Download NTLK words if not already downloaded
nltk.download("words")
english_words = set(words.words())


# PDF Processing Functions
def read_cached_text(cache_file):
    """Read text from the cache file if it exists."""
    if os.path.exists(cache_file):
        with open(cache_file, "r") as file:
            return file.read()
    return None


def save_text_to_cache(text, cache_file):
    """Save extracted text to a cache file."""
    with open(cache_file, "w") as file:
        file.write(text)


def preprocess_image(image):
    """Preprocess the image to improve OCR accuracy."""
    # Convert to grayscale
    gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    # Apply binary thresholding (adaptive method or fixed threshold)
    _, thresholded_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY_INV)
    # Optional: apply Gaussian blur to reduce noise
    blurred_image = cv2.GaussianBlur(thresholded_image, (5, 5), 0)
    return blurred_image


def extract_text_with_pytesseract(pdf_file):
    """Extract text from a PDF file using OCR with improved accuracy."""
    cnt = 0
    text = ""
    images = convert_from_path(pdf_file)

    for img in images:
        cnt += 1
        skip = False
        if PAGES_RANGES:
            for PAGE_RANGE in PAGES_RANGES:
                if cnt not in PAGE_RANGE:
                    skip = True
        if skip:
            continue
        print(f"Extracting text from page {cnt}")
        # Preprocess the image to enhance OCR accuracy
        processed_image = preprocess_image(img)
        # Using custom config for OCR
        custom_config = r'--oem 3 --psm 6'  # OCR engine mode and page segmentation mode
        page_text = pytesseract.image_to_string(processed_image, config=custom_config, lang='eng')
        text += page_text

    return text


def extract_text(pdf_file):
    """Extract text from a PDF file or read from cache."""
    base_filename = os.path.splitext(os.path.basename(pdf_file))[0]
    cache_file = f"{base_filename}.txt"
    cached_text = read_cached_text(cache_file)
    if cached_text:
        print(f"Using cached text file {cache_file}.")
        return cached_text
    print("Extracting text from PDF...")
    text = extract_text_with_pytesseract(pdf_file)
    save_text_to_cache(text, cache_file)
    return text


# Function to clean up sentence
def clean_sentence(sentence):
    """Clean a sentence by removing extra spaces and newlines."""
    sentence = re.sub(r'\s+', ' ', sentence)
    return sentence.replace("\n", " ").replace("\r", " ").strip()


def clean_word(word):
    """Clean a word by removing punctuation and special characters."""
    return re.sub(r"[^\w\s]", "", word)


def is_valid_word(word):
    number_words = {
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen", "twenty"
    }
    """Check if a word meets the criteria for a valid English word."""
    return (
        len(word) >= 4
        and not word[0].isdigit()
        and not word[-1].isdigit()
        and word not in number_words
        and not re.search(r"(.)\1{3,}", word)
        and re.match(r"^[a-zA-Z]+$", word)
        and not word.istitle()
        and word in english_words
    )


def extract_unique_words(text):
    """Extract unique English words from text."""
    unique_words = {}
    sentences = re.split(r"[.!?]", text)

    for sentence in sentences:
        cleaned_sentence = clean_sentence(sentence)
        for word in cleaned_sentence.split():
            word_cleaned = clean_word(word)
            if is_valid_word(word_cleaned):
                if word_cleaned not in unique_words:
                    unique_words[word_cleaned.lower()] = {"sentence": cleaned_sentence}

    return unique_words


# Word Classification Functions
def load_known_words(file_path):
    known_words = set()
    """Load known words from a file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            known_words.update(line.strip() for line in file)
    return known_words


def load_otherbook_words(file_path):
    otherbook_words = set()
    # Check other `.words` files in the current directory
    for other_file in Path(".").glob("*.words"):
        if other_file.name != Path(file_path).name:  # Avoid reloading the same file
            with open(other_file, "r") as file:
                lines = file.readlines()
                line_count = len(lines)  # Count the number of lines
                print(f"Found {line_count} words from other file: {other_file.name}")
                otherbook_words.update(line.strip() for line in lines)
    print("\n")
    return otherbook_words


def save_known_words(file_path, known_words):
    """Save known words to a file."""
    sorted_known_words = sorted(known_words)
    with open(file_path, "w") as file:
        for word in sorted_known_words:
            file.write(f"{word}\n")


def load_unknown_words(file_path):
    """Load unknown words from a headerless CSV file."""
    unknown_words = {}
    if os.path.exists(file_path):
        with open(file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                # Ensure the row has exactly 3 elements: word, translation, and sentence
                if len(row) >= 3:
                    word, translation, sentence = row[0], row[1], row[2]
                    unknown_words[word] = {
                        "translation": translation,
                        "sentence": sentence
                    }
    return unknown_words


def save_unknown_words(file_path, unknown_words):
    """Save unknown words to a CSV file."""
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["word", "translation", "sentence"], quoting=csv.QUOTE_ALL)
        for word, details in unknown_words.items():
            writer.writerow({"word": word, "translation": details["translation"], "sentence": details["sentence"]})
    sorted_unknown_words = sorted(unknown_words)
    words_file = os.path.splitext(os.path.basename(file_path))[0]
    with open(f"{words_file}.words", "w", newline="", encoding="utf-8") as file:
        for word in sorted_unknown_words:  
            file.write(f"{word}\n")


def classify_words(wordlist, stdscr):
    """Classify words as known or unknown."""
    curses.endwin()
    known_words = load_known_words(KNOWN_WORDS_FILE)
    unknown_words = load_unknown_words(UNKNOWN_WORDS_FILE)
    otherbook_words = load_otherbook_words(UNKNOWN_WORDS_FILE)
    input("Press Enter to continue")
    curses.initscr()

    # remove already proccessed words
    newlist = {}
    for word in wordlist:
        if (
            word in known_words
            or word in unknown_words
            or word in otherbook_words
        ):
            continue
        newlist[word] = wordlist[word]

    try:
        cnt = 0
        total = len(newlist)
        for word, details in newlist.items():
            sentence = details.get("sentence", "")
            stdscr.clear()
            cnt += 1
            stdscr.addstr(f"{cnt} from {total}\n")
            stdscr.addstr(f"{word} = {sentence}\n")
            stdscr.addstr("\n\nPress LEFT if you know the word, RIGHT if you don't.\n")
            stdscr.refresh()

            # Wait for user input
            while True:
                key = stdscr.getch()
                if key == curses.KEY_LEFT:
                    known_words.add(word)  # Use `add` to add to a set
                    break
                elif key == curses.KEY_RIGHT:
                    unknown_words[word] = {"sentence": sentence, "translation": ""}
                    break

    except KeyboardInterrupt:
        # Handle user interruption gracefully
        stdscr.addstr("\nExiting and saving progress...\n")
        stdscr.refresh()
    finally:
        # Save progress to files
        save_known_words(KNOWN_WORDS_FILE, known_words)
        save_unknown_words(UNKNOWN_WORDS_FILE, unknown_words)
        curses.endwin()
        print("Progress saved to files.")

    return unknown_words


# Translation Functions
def translate_words(unknown_words):
    """Translate unknown words using an offline translation method."""
    for word, details in unknown_words.items():
        if not details["translation"]:
            try:
                # Offline translation for the word (Translate to Russian)
                details["translation"] = GoogleTranslator(source='auto', target='ru').translate(word)
                print(f"Translation {word} - {details['translation']}")
            except Exception as e:
                print(f"Error translating {word}: {e}")
    save_unknown_words(UNKNOWN_WORDS_FILE, unknown_words)


# Main Function
def main():
    text = extract_text(PDF_FILE)
    unique_words = extract_unique_words(text)
    unknown_words = curses.wrapper(lambda stdscr: classify_words(unique_words, stdscr))
    translate_words(unknown_words)


if __name__ == "__main__":
    main()


'''
Requirements:
/opt/venv/bin/pip install opencv-python deep-translator nltk pytesseract pdf2image
'''
