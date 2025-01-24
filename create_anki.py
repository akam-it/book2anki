#!/opt/venv/bin/python3


import csv
import os
import sys
import genanki
import hashlib


def generate_unique_id(name):
    """Generate a unique 32-bit integer ID based on a string (e.g., filename)."""
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


def create_anki_deck_from_csv(csv_file):
    """Create an Anki deck from a given CSV file."""
    # Extract deck name and output file name from CSV file name
    deck_name = os.path.splitext(os.path.basename(csv_file))[0]
    deck_id = generate_unique_id(deck_name + "deck")
    model_id = generate_unique_id(deck_name + "model")
    output_file = f"{deck_name}.apkg"

    # Define the Anki card model with dynamic IDs
    model = genanki.Model(
        model_id,
        f"{deck_name} Model",
        fields=[
            {"name": "Word"},
            {"name": "Translation"},
            {"name": "Sentence"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": """
                    <div class="card">
                      <div class="word">{{Word}}</div>
                    </div>
                """,  # Front of the card
                "afmt": """
                    <div class="card">
                      <div class="word">{{FrontSide}}</div>
                      <hr id="answer">
                      <div class="translation">{{Translation}}</div>
                      <div class="sentence"><i>{{Sentence}}</i></div>
                    </div>
                """,  # Back of the card
            },
        ],
        css="""
            .card {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100%;
                font-family: Arial, sans-serif;
            }
            .word {
                font-size: 48px;
                font-weight: bold;
                color: white;
            }
            .translation {
                font-size: 32px;
                color: white;
            }
            .sentence {
                font-size: 24px;
                color: white;
            }
        """,  # CSS for styling
    )

    # Create the Anki deck
    deck = genanki.Deck(deck_id, deck_name)

    # Read the CSV file and populate the deck
    with open(csv_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) < 3:
                continue  # Skip rows with insufficient data
            word, translation, sentence = row[0], row[1], row[2]
            note = genanki.Note(
                model=model,
                fields=[word, translation, sentence],
            )
            deck.add_note(note)

    # Export the deck to an .apkg file
    genanki.Package(deck).write_to_file(output_file)
    print(f"Anki deck created: {output_file}")


# Main script execution
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_anki_deck.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' does not exist.")
        sys.exit(1)

    create_anki_deck_from_csv(csv_file)
