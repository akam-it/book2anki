# book2anki
Export unknown words from a PDF book to anki deck to learn/review them before read a book

# How to use
1. Edit pdf2words.py:
   - Set your PDF filename in PDF_FILE variable
   - Set what pages to export in PAGES_RANGES, comment variable if all pages to export
2. The pdf2words.py script will:
   - convert PDF file to images and use py-tesseract to try to recognize English words
   - export/cache recognized text into text file with extension .txt
   - ask user to classify found unique words as known/unknown and save them to text files.
     .KNOWN_WORDS.txt contains known words and will be used as ignore list
     CSV file contains unknown words with translation and sentence example from the book
     WORDS file contains just an unknown word list
3. The create_anki.py script will create a very simple Anki deck with unknown words from the first script
