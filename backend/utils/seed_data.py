"""Seed reference translation data from CSV files into the database."""

import csv
import os

from models import db, QuranTranslation, QuranArabicText

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# Primary reference: Malay translation (Juz 29) — sourced from approved translation dataset.
# Partners can add more CSV files to REFERENCE_CSV_FILES or use POST /api/quran/import-csv.
REFERENCE_CSV_FILES = [
    os.path.join(DATA_DIR, 'translation_malay_juzuk_29.csv'),
]

ARABIC_REFERENCE_CSV_FILES = [
    os.path.join(DATA_DIR, 'quranic_text_juzuk_30.csv'),
]


def seed_reference_translations(force: bool = False) -> dict:
    """
    Import reference translations from CSV if the table is empty (or force=True).
    Returns counts of inserted and skipped rows.
    """
    if not force and QuranTranslation.query.count() > 0:
        return {'inserted': 0, 'skipped': 0, 'message': 'Reference data already loaded.'}

    inserted = 0
    skipped = 0

    for csv_path in REFERENCE_CSV_FILES:
        if not os.path.exists(csv_path):
            continue

        with open(csv_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                continue

            for row in reader:
                try:
                    surah_number = int(row['surah_number'])
                    ayah_number = int(row['ayah_number'])
                    translation = row['translation'].strip()
                    if surah_number <= 0 or ayah_number <= 0 or not translation:
                        skipped += 1
                        continue

                    existing = QuranTranslation.query.filter_by(
                        surah_number=surah_number,
                        ayah_number=ayah_number,
                    ).first()

                    if existing:
                        if force:
                            existing.translation = translation
                            inserted += 1
                        else:
                            skipped += 1
                        continue

                    db.session.add(QuranTranslation(
                        surah_number=surah_number,
                        ayah_number=ayah_number,
                        translation=translation,
                    ))
                    inserted += 1
                except (KeyError, ValueError, TypeError):
                    skipped += 1

    db.session.commit()
    return {'inserted': inserted, 'skipped': skipped, 'message': 'Reference data seeded.'}


def build_reference_lookup() -> dict[tuple[int, int], str]:
    """Build a lookup dict from all reference translations in the database."""
    lookup: dict[tuple[int, int], str] = {}
    for row in QuranTranslation.query.all():
        lookup[(row.surah_number, row.ayah_number)] = row.translation
    return lookup


def seed_reference_arabic_text(force: bool = False) -> dict:
    """Import reference Quranic Arabic text from CSV if the table is empty."""
    if not force and QuranArabicText.query.count() > 0:
        return {'inserted': 0, 'skipped': 0, 'message': 'Arabic reference data already loaded.'}

    inserted = 0
    skipped = 0

    for csv_path in ARABIC_REFERENCE_CSV_FILES:
        if not os.path.exists(csv_path):
            continue

        with open(csv_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                continue

            for row in reader:
                try:
                    surah_number = int(row['surah_number'])
                    ayah_number = int(row['ayah_number'])
                    arabic_text = row['arabic_text'].strip()
                    juz_raw = row.get('juz_number')
                    juz_number = int(juz_raw) if juz_raw and str(juz_raw).strip() else None
                    surah_name = (row.get('surah_name') or '').strip() or None

                    if surah_number <= 0 or ayah_number <= 0 or not arabic_text:
                        skipped += 1
                        continue

                    existing = QuranArabicText.query.filter_by(
                        surah_number=surah_number,
                        ayah_number=ayah_number,
                    ).first()

                    if existing:
                        if force:
                            existing.arabic_text = arabic_text
                            existing.juz_number = juz_number
                            existing.surah_name = surah_name
                            inserted += 1
                        else:
                            skipped += 1
                        continue

                    db.session.add(QuranArabicText(
                        juz_number=juz_number,
                        surah_number=surah_number,
                        surah_name=surah_name,
                        ayah_number=ayah_number,
                        arabic_text=arabic_text,
                    ))
                    inserted += 1
                except (KeyError, ValueError, TypeError):
                    skipped += 1

    db.session.commit()
    return {'inserted': inserted, 'skipped': skipped, 'message': 'Arabic reference data seeded.'}


def build_arabic_reference_lookup() -> dict[tuple[int, int], str]:
    """Build a lookup dict from all reference Arabic text in the database."""
    lookup: dict[tuple[int, int], str] = {}
    for row in QuranArabicText.query.all():
        lookup[(row.surah_number, row.ayah_number)] = row.arabic_text
    return lookup
