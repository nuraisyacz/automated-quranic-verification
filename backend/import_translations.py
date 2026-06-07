import csv
import os
from app import app
from models import db, QuranTranslation

CSV_FILE_PATH = "data/translation_malay_juzuk_29.csv"

def import_translations():
    print("Starting translation import...")

    if not os.path.exists(CSV_FILE_PATH):
        print(f"CSV file not found: {CSV_FILE_PATH}")
        return

    inserted = 0
    skipped = 0
    invalid = 0

    with app.app_context():
        db.create_all()

        with open(CSV_FILE_PATH, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            print("CSV columns found:", reader.fieldnames)

            required_columns = {"surah_number", "ayah_number", "translation"}

            if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
                print("Required columns:", required_columns)
                print("CSV file does not have the required columns.")
                return

            for row in reader:
                try:
                    surah_number = int(row["surah_number"])
                    ayah_number = int(row["ayah_number"])
                    translation = row["translation"].strip()

                    if surah_number <= 0 or ayah_number <= 0 or not translation:
                        invalid += 1
                        continue

                    existing = QuranTranslation.query.filter_by(
                        surah_number=surah_number,
                        ayah_number=ayah_number
                    ).first()

                    if existing:
                        skipped += 1
                        continue

                    new_translation = QuranTranslation(
                        surah_number=surah_number,
                        ayah_number=ayah_number,
                        translation=translation
                    )

                    db.session.add(new_translation)
                    inserted += 1

                except Exception as e:
                    print("Invalid row skipped:", row)
                    print("Reason:", e)
                    invalid += 1

            db.session.commit()

    print("Import completed.")
    print(f"Inserted rows: {inserted}")
    print(f"Skipped duplicate rows: {skipped}")
    print(f"Invalid rows: {invalid}")

if __name__ == "__main__":
    import_translations()
