import pandas as pd
from pathlib import Path

COLUMNS_TO_DROP = [
    "created_by",
    "created_by_ref",
    "first_seen",
    "last_seen",
    "created",
    "modified",
    "spec_version",
    # "type",
]

def clean_csv(input_csv_path):
    df = pd.read_csv(input_csv_path)

    csv_file=Path(input_csv_path).stem+".csv"
    csv_path=Path("/Users/alwyndsouza/Documents/GitHub/stix-ai-dashboard/modules/cleaned_files")/csv_file
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Drop unwanted columns if they exist
    df = df.drop(columns=COLUMNS_TO_DROP, errors="ignore")

    # Keep only required columns
    df = df[["summary", "id", "type"]]

    # Rewrite the same CSV
    df.to_csv(csv_path, index=False)

    print(f"Cleaned and overwritten: {csv_path}")
    return csv_path


