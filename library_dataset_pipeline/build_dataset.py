#!/usr/bin/env python3
"""
build_dataset.py
=================
Single-command pipeline runner.

    python build_dataset.py                # SEED MODE: builds the demo dataset
                                            # from data/seed_books.py (48 real books,
                                            # no internet/API key required)

    python build_dataset.py --isbns isbns.txt --google-api-key KEY
                                            # LIVE MODE (ISBN list): downloads +
                                            # enriches real metadata for every ISBN
                                            # in isbns.txt (one per line). Requires
                                            # internet and the `requests` package.

    python build_dataset.py --kaggle-csv books.csv --enrich-missing --google-api-key KEY
                                            # LIVE MODE (Kaggle dataset): ingests a
                                            # Kaggle books CSV (thousands of rows),
                                            # then backfills any missing description/
                                            # category/cover/subjects per book via
                                            # Google Books + Open Library. This is
                                            # the recommended path to reach 2,000-5,000
                                            # real books. Requires internet.

Either mode runs the same STEP 1-7 pipeline and produces the same CSV set in
output/.
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import download, preprocess, merge, enrichment, similarity, export
from pipeline.config import OUTPUT_DIR


def run(isbns_file=None, kaggle_csv=None, google_api_key=None, enrich_missing=False,
        top_n_similar=10):
    print("STEP 1: downloading raw records...")
    if kaggle_csv:
        raw = download.load_kaggle_csv(kaggle_csv)
        print(f"  loaded {len(raw)} raw records from Kaggle CSV (LIVE MODE)")
        if enrich_missing:
            print("STEP 1b: backfilling missing description/category/cover/subjects...")
            raw, n_enriched = download.enrich_missing_fields(raw, google_api_key=google_api_key)
            print(f"  backfilled fields on {n_enriched} records via Google Books / Open Library")
    elif isbns_file:
        with open(isbns_file) as f:
            isbn_list = [line.strip() for line in f if line.strip()]
        raw = download.download_by_isbn_list(isbn_list, google_api_key=google_api_key)
        print(f"  fetched {len(raw)} raw records for {len(isbn_list)} ISBNs (LIVE MODE)")
    else:
        raw = download.load_seed()
        print(f"  loaded {len(raw)} seed records (SEED MODE — no internet used)")

    print("STEP 2: normalizing + quality checks (incl. ISBN checksum validation)...")
    cleaned, dropped, isbn_flagged = preprocess.preprocess_all(raw)
    print(f"  {len(cleaned)} records kept, {dropped} corrupted records dropped, "
          f"{isbn_flagged} had an invalid ISBN checksum stripped")

    print("STEP 3-4: deduplicating + merging...")
    merged = merge.merge_records(cleaned)
    print(f"  {len(merged)} unique books after dedup (from {len(cleaned)} records)")

    merged = export.assign_ids(merged)

    print("STEP 5-ish: generating library + media fields...")
    merged = export.generate_library_fields(merged)
    merged = export.generate_media_fields(merged)

    print("STEP 6: generating AI-enriched metadata...")
    merged = enrichment.enrich_all(merged)

    print("STEP 6b: computing book-to-book similarity...")
    sim_rows = similarity.build_similarity_table(merged, top_n=top_n_similar)
    merged = similarity.attach_similar_titles(merged, sim_rows, top_n=5)

    print("STEP 7: exporting CSVs...")
    counts = export.export_all(merged, sim_rows)
    for name, n in counts.items():
        print(f"  {name}.csv: {n} rows")

    print(f"\nDone. Files written to: {OUTPUT_DIR}")
    return merged


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the AI-powered library master dataset.")
    parser.add_argument("--isbns", dest="isbns_file", default=None,
                         help="Path to a text file of ISBNs (one per line) for LIVE MODE.")
    parser.add_argument("--kaggle-csv", dest="kaggle_csv", default=None,
                         help="Path to a Kaggle books CSV for LIVE MODE bulk ingestion.")
    parser.add_argument("--enrich-missing", dest="enrich_missing", action="store_true",
                         help="Backfill missing description/category/cover/subjects via "
                              "Google Books + Open Library after Kaggle ingestion.")
    parser.add_argument("--google-api-key", dest="google_api_key", default=None,
                         help="Optional Google Books API key (higher rate limits).")
    parser.add_argument("--top-n-similar", type=int, default=10)
    args = parser.parse_args()
    run(isbns_file=args.isbns_file, kaggle_csv=args.kaggle_csv,
        google_api_key=args.google_api_key, enrich_missing=args.enrich_missing,
        top_n_similar=args.top_n_similar)
