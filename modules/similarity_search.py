# import faiss
# import numpy as np
# import pandas as pd
# from langchain_ollama import OllamaEmbeddings
# from langchain_community.document_loaders import CSVLoader
# from functools import lru_cache
# import json
# from tqdm import tqdm
# from pathlib import Path

# def extract_id(doc):
#     # CSVLoader stores row fields in page_content as text,
#     # and metadata may contain source info.
#     # Safest: parse page_content
#     for line in doc.page_content.splitlines():
#         if line.lower().startswith("id"):
#             return line.split(":", 1)[1].strip()
#     return None

# def generate_similarity_json(
#     csv_path: str,
#     top_k: int = 3,
#     threshold: float = 0.8
# ):
#     df = pd.read_csv(csv_path)
#     print(f"[DEBUG] Processing {len(df)} objects from {csv_path}")

#     json_file=Path(csv_path).stem+"similar_ids.json"
#     json_path=Path("similarity_jsons")/json_file
#     json_path.parent.mkdir(parents=True, exist_ok=True)

#     similarity_map = {}
#     processed_count = 0
#     found_similarities = 0

#     for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing objects"):
#         incoming_id = row["id"]
#         stix_type = row["type"]
#         query_text = row["summary"]
#         processed_count += 1

#         if pd.isna(query_text) or pd.isna(stix_type):
#             print(f"[DEBUG] Skipping {incoming_id}: missing summary or type")
#             continue

#         try:
#             matches = search_similar_objects(
#                 query_text=query_text,
#                 stix_type=stix_type,
#                 top_k=top_k,
#                 threshold=threshold
#             )

#             similar_ids = []
#             for m in matches:
#                 sid = extract_id(m["document"])
#                 if sid and sid != incoming_id:
#                     similar_ids.append(sid)

#             if similar_ids:
#                 similarity_map[incoming_id] = list(set(similar_ids))
#                 found_similarities += 1
#                 print(f"[DEBUG] Found {len(similar_ids)} similar objects for {incoming_id}")

#         except FileNotFoundError as e:
#             print(f"[DEBUG] No index found for type {stix_type}: {e}")
#             continue
#         except Exception as e:
#             print(f"[DEBUG] Error processing {incoming_id}: {e}")
#             continue

#     with open(json_path, "w") as f:
#         json.dump(similarity_map, f, separators=(",", ":"))

#     print(f"[✓] Similarity JSON written: {json_path}")
#     print(f"[✓] Objects processed: {processed_count}")
#     print(f"[✓] Objects with similarities: {found_similarities}")
#     print(f"[✓] Total similarity mappings: {len(similarity_map)}")
#     return json_path


# # =========================
# # EMBEDDER
# # =========================
# embedder = OllamaEmbeddings(model="mxbai-embed-large:latest")

# # =========================
# # CACHE INDEXES (important)
# # =========================
# @lru_cache(maxsize=32)
# def load_index(stix_type):
#     try:
#         index = faiss.read_index(f"indexes/{stix_type}.faiss")
#         loader = CSVLoader(
#             f"csv_files_with_summary_SDOs/{stix_type}.csv",
#             encoding="utf-8"
#         )
#         docs = loader.load()
#         return index, docs
#     except (FileNotFoundError, RuntimeError):
#         raise FileNotFoundError(f"Index or CSV file not found for {stix_type}")

# # =========================
# # SEARCH FUNCTION
# # =========================
# # def search_similar_objects(
# #     query_text: str,
# #     stix_type: str,
# #     top_k: int = 3
# # ):
# #     index, docs = load_index(stix_type)

# #     query_embedding = embedder.embed_query(query_text)
# #     query_embedding = np.array([query_embedding], dtype="float32")

# #     faiss.normalize_L2(query_embedding)

# #     scores, indices = index.search(query_embedding, top_k)

# #     results = []
# #     for rank, idx in enumerate(indices[0]):
# #         results.append({
# #             "rank": rank + 1,
# #             "score": float(scores[0][rank]),
# #             "document": docs[idx]
# #         })

# #     return results

# def search_similar_objects(
#     query_text: str,
#     stix_type: str,
#     top_k: int = 3,
#     threshold: float = 0.3  # Lower threshold for better results
# ):
#     try:
#         index, docs = load_index(stix_type)
#         print(f"[DEBUG] Loaded index for {stix_type} with {len(docs)} documents")
#     except FileNotFoundError as e:
#         print(f"[DEBUG] Failed to load index for {stix_type}: {e}")
#         raise

#     query_embedding = embedder.embed_query(query_text)
#     query_embedding = np.array([query_embedding], dtype="float32")
#     faiss.normalize_L2(query_embedding)

#     scores, indices = index.search(query_embedding, top_k)
#     print(f"[DEBUG] Search scores for {stix_type}: {scores[0]}")

#     results = []
#     for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
#         print(f"[DEBUG] Match {rank+1}: score={score:.4f}, threshold={threshold}")
#         if score < threshold:
#             print(f"[DEBUG] Skipping match {rank+1}: score {score:.4f} < threshold {threshold}")
#             continue

#         results.append({
#             "rank": rank + 1,
#             "score": float(score),
#             "document": docs[idx]
#         })

#     print(f"[DEBUG] Returning {len(results)} results for {stix_type}")
#     return results


# def process_csv(csv_path, top_k=3):
#     df = pd.read_csv(csv_path)

#     for row_id, row in df.iterrows():
#         stix_type = row["type"]
#         query_text = row["summary"]

#         print(f"\n==============================")
#         print(f"ROW {row_id} | TYPE: {stix_type}")
#         print(f"QUERY: {query_text[:120]}...")

#         try:
#             matches = search_similar_objects(
#                 query_text=query_text,
#                 stix_type=stix_type,
#                 top_k=top_k
#             )

#             for m in matches:
#                 print(f"\n---- MATCH {m['rank']} | score={m['score']:.4f} ----")
#                 print(m["document"])

#         except FileNotFoundError:
#             print(f"[!] No index found for type: {stix_type}")


# # #testing 
# # process_csv("/Users/alwyndsouza/Documents/GitHub/stix-ai-dashboard/modules/cleaned_files/stix_bundle-17.csv")

# # generate_similarity_json("/Users/alwyndsouza/Documents/GitHub/stix_normalizer/cosine_sim/stix_bundle-18.csv")





#UPDATED ON 13TH OF FEB, BY ALWYN D SOUZA
import faiss
import numpy as np
import pandas as pd
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import CSVLoader
from functools import lru_cache
import json
from tqdm import tqdm
from pathlib import Path

# =============================================================================
# CONFIG – SINGLE SOURCE OF TRUTH
# =============================================================================
DEFAULT_TOP_K = 3
DEFAULT_THRESHOLD = 0.8  # cosine similarity threshold

# =============================================================================
# EMBEDDINGS
# =============================================================================
embedder = OllamaEmbeddings(model="mxbai-embed-large:latest")

# =============================================================================
# FAISS INDEX LOADER (CACHED)
# =============================================================================
@lru_cache(maxsize=32)
def load_index(stix_type: str):
    index_path = f"indexes/{stix_type}.faiss"
    csv_path = f"csv_files_with_summary_SDOs/{stix_type}.csv"

    if not Path(index_path).exists():
        raise FileNotFoundError(f"Missing FAISS index: {index_path}")

    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Missing CSV file: {csv_path}")

    index = faiss.read_index(index_path)

    loader = CSVLoader(csv_path, encoding="utf-8")
    docs = loader.load()

    return index, docs

# =============================================================================
# SIMILARITY SEARCH (NO DEFAULTS, NO AMBIGUITY)
# =============================================================================
def search_similar_objects(
    *,
    query_text: str,
    stix_type: str,
    top_k: int,
    threshold: float
):
    index, docs = load_index(stix_type)

    query_embedding = embedder.embed_query(query_text)
    query_embedding = np.array([query_embedding], dtype="float32")
    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(query_embedding, top_k)

    results = []
    for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1):
        if score < threshold:
            continue

        doc = docs[idx]
        doc_id = doc.metadata.get("id")

        if not doc_id:
            continue

        results.append({
            "rank": rank,
            "score": float(score),
            "id": doc_id
        })

    return results

# =============================================================================
# MAIN PIPELINE – GENERATE SIMILARITY JSON
# =============================================================================
def generate_similarity_json(
    csv_path: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = DEFAULT_THRESHOLD
):
    df = pd.read_csv(csv_path)

    required_cols = {"id", "type", "summary"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {required_cols}")

    output_path = Path("similarity_jsons")
    output_path.mkdir(parents=True, exist_ok=True)

    json_file = Path(csv_path).stem + "_similar_ids.json"
    json_path = output_path / json_file

    similarity_map = {}
    processed = 0
    with_similarities = 0

    print(f"[INFO] Processing {len(df)} objects")
    print(f"[INFO] top_k={top_k}, threshold={threshold}")

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing objects"):
        incoming_id = row["id"]
        stix_type = row["type"]
        summary = row["summary"]

        processed += 1
        similarity_map[incoming_id] = []  # ALWAYS INITIALIZE

        if pd.isna(summary) or pd.isna(stix_type):
            continue

        try:
            matches = search_similar_objects(
                query_text=summary,
                stix_type=stix_type,
                top_k=top_k,
                threshold=threshold
            )
        except FileNotFoundError:
            continue

        for m in matches:
            if m["id"] != incoming_id:
                similarity_map[incoming_id].append(m["id"])

        # de-duplicate
        similarity_map[incoming_id] = list(set(similarity_map[incoming_id]))

        if similarity_map[incoming_id]:
            with_similarities += 1

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(similarity_map, f, indent=2)

    print(f"[✓] Similarity JSON written: {json_path}")
    print(f"[✓] Objects processed: {processed}")
    print(f"[✓] Objects with similarities: {with_similarities}")
    print(f"[✓] Total objects in map: {len(similarity_map)}")

    return json_path
