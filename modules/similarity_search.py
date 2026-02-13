import faiss
import numpy as np
import pandas as pd
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import CSVLoader
from functools import lru_cache
import json
from tqdm import tqdm
from pathlib import Path

def extract_id(doc):
    # CSVLoader stores row fields in page_content as text,
    # and metadata may contain source info.
    # Safest: parse page_content
    for line in doc.page_content.splitlines():
        if line.lower().startswith("id"):
            return line.split(":", 1)[1].strip()
    return None

def generate_similarity_json(
    csv_path: str,
    top_k: int = 3,
    threshold: float = 0.75
):
    df = pd.read_csv(csv_path)

    json_file=Path(csv_path).stem+"similar_ids.json"
    json_path=Path("/Users/alwyndsouza/Documents/GitHub/stix-ai-dashboard/modules/similarity_jsons")/json_file
    json_path.parent.mkdir(parents=True, exist_ok=True)

    similarity_map = {}

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing objects"):
        incoming_id = row["id"]
        stix_type = row["type"]
        query_text = row["summary"]

        if pd.isna(query_text) or pd.isna(stix_type):
            continue

        try:
            matches = search_similar_objects(
                query_text=query_text,
                stix_type=stix_type,
                top_k=top_k,
                threshold=threshold
            )

            similar_ids = []
            for m in matches:
                sid = extract_id(m["document"])
                if sid and sid != incoming_id:
                    similar_ids.append(sid)

            if similar_ids:
                similarity_map[incoming_id] = list(set(similar_ids))  # dedupe

        except FileNotFoundError:
            continue

    # 🔥 Truncated JSON (compact)
    with open(json_path, "w") as f:
        json.dump(similarity_map, f, separators=(",", ":"))

    print(f"[✓] Similarity JSON written: {json_path}")
    print(f"[✓] Objects mapped: {len(similarity_map)}")
    return json_path


# =========================
# EMBEDDER
# =========================
embedder = OllamaEmbeddings(model="mxbai-embed-large:latest")

# =========================
# CACHE INDEXES (important)
# =========================
@lru_cache(maxsize=32)
def load_index(stix_type):
    index = faiss.read_index(f"/Users/alwyndsouza/Documents/GitHub/stix_normalizer/Threat_similarity_search_module/indexes/{stix_type}.faiss")
    loader = CSVLoader(
        f"/Users/alwyndsouza/Documents/GitHub/stix_normalizer/Threat_similarity_search_module/csv_files_with_summary_SDOs/{stix_type}.csv"
    )
    docs = loader.load()
    return index, docs

# =========================
# SEARCH FUNCTION
# =========================
# def search_similar_objects(
#     query_text: str,
#     stix_type: str,
#     top_k: int = 3
# ):
#     index, docs = load_index(stix_type)

#     query_embedding = embedder.embed_query(query_text)
#     query_embedding = np.array([query_embedding], dtype="float32")

#     faiss.normalize_L2(query_embedding)

#     scores, indices = index.search(query_embedding, top_k)

#     results = []
#     for rank, idx in enumerate(indices[0]):
#         results.append({
#             "rank": rank + 1,
#             "score": float(scores[0][rank]),
#             "document": docs[idx]
#         })

#     return results

def search_similar_objects(
    query_text: str,
    stix_type: str,
    top_k: int = 3,
    threshold: float = 0.80   # 👈 ADD THIS
):
    index, docs = load_index(stix_type)

    query_embedding = embedder.embed_query(query_text)
    query_embedding = np.array([query_embedding], dtype="float32")
    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(query_embedding, top_k)

    results = []
    for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
        if score < threshold:
            continue   # 👈 FILTER HERE

        results.append({
            "rank": rank + 1,
            "score": float(score),
            "document": docs[idx]
        })

    return results


def process_csv(csv_path, top_k=3):
    df = pd.read_csv(csv_path)

    for row_id, row in df.iterrows():
        stix_type = row["type"]
        query_text = row["summary"]

        print(f"\n==============================")
        print(f"ROW {row_id} | TYPE: {stix_type}")
        print(f"QUERY: {query_text[:120]}...")

        try:
            matches = search_similar_objects(
                query_text=query_text,
                stix_type=stix_type,
                top_k=top_k
            )

            for m in matches:
                print(f"\n---- MATCH {m['rank']} | score={m['score']:.4f} ----")
                print(m["document"])

        except FileNotFoundError:
            print(f"[!] No index found for type: {stix_type}")


# #testing 
#process_csv("/Users/alwyndsouza/Documents/GitHub/stix-ai-dashboard/modules/cleaned_files/stix_bundle-17.csv")

# generate_similarity_json("/Users/alwyndsouza/Documents/GitHub/stix_normalizer/cosine_sim/stix_bundle-18.csv")