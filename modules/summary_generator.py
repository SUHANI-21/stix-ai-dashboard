import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import ollama
from pathlib import Path

# =========================
# CONFIG
# =========================
# CSV_FILE = "input.csv"   # <-- change this
MAX_WORKERS = 4
SUMMARY_COLUMN = "summary"

# =========================
# SUMMARY GENERATOR
# =========================
def generate_summary(row):
    prompt = f"""
Generate a detailed summary of the following data:
{row.to_dict()}

Ignore metadata fields such as timestamps and IDs.
Write in full sentences (no bullet points).
Start with: "The object contains..."
"""
    response = ollama.generate(
        model="llama3.2:latest",
        prompt=prompt
    )
    return response["response"].strip()

# =========================
# MAIN
# =========================
def summarize_csv(csv_path):
    df = pd.read_csv(csv_path)

    csv_file=Path(csv_path).stem+".csv"
    csv_file_path=Path("E:/college/NITK Internship/stix_normalizer/stix_normalizer/stix_intelligence_analyzer/modules/Summarized_files")/csv_file
    csv_file_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [row for _, row in df.iterrows()]

    summaries = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for summary in tqdm(
            executor.map(generate_summary, rows),
            total=len(rows),
            desc="Generating summaries"
        ):
            summaries.append(summary)

    df[SUMMARY_COLUMN] = summaries

    # overwrite same CSV
    df.to_csv(csv_file_path, index=False)
    print(f"Updated CSV written to: {csv_file_path}")
    return csv_file_path

# =========================
# RUN
# =========================
# summarize_csv("/Users/alwyndsouza/Documents/GitHub/stix_normalizer/cosine_sim/stix_bundle-18.csv")
