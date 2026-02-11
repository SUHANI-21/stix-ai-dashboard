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
    threshold: float = 0.3
):
    df = pd.read_csv(csv_path)
    print(f"[DEBUG] Processing {len(df)} objects from {csv_path}")

    json_file=Path(csv_path).stem+"similar_ids.json"
    json_path=Path("similarity_jsons")/json_file
    json_path.parent.mkdir(parents=True, exist_ok=True)

    similarity_map = {}
    processed_count = 0
    found_similarities = 0

    # Group by type for internal similarity search
    type_groups = df.groupby('type')
    
    for stix_type, group_df in type_groups:
        if len(group_df) < 2:
            continue
            
        print(f"[DEBUG] Processing {len(group_df)} objects of type {stix_type}")
        
        # Get embeddings for all summaries in this type
        summaries = group_df['summary'].fillna('').tolist()
        if not any(summaries):
            continue
            
        embeddings = []
        for summary in summaries:
            if summary.strip():
                embedding = embedder.embed_query(summary)
                embeddings.append(embedding)
            else:
                embeddings.append([0.0] * 1024)  # Zero vector for empty summaries
        
        embeddings = np.array(embeddings, dtype="float32")
        
        # Normalize embeddings
        faiss.normalize_L2(embeddings)
        
        # Calculate cosine similarity
        similarity_matrix = np.dot(embeddings, embeddings.T)
        
        for i, (_, row) in enumerate(group_df.iterrows()):
            obj_id = row['id']
            similarities = similarity_matrix[i]
            
            # Get top similar objects (excluding self)
            similar_indices = np.argsort(similarities)[::-1][1:top_k+1]
            similar_scores = similarities[similar_indices]
            
            similar_ids = []
            for idx, score in zip(similar_indices, similar_scores):
                if score > threshold:
                    similar_ids.append(group_df.iloc[idx]['id'])
            
            if similar_ids:
                similarity_map[obj_id] = similar_ids
                found_similarities += 1
                print(f"[DEBUG] Found {len(similar_ids)} similar objects for {obj_id}")
        
        processed_count += len(group_df)

    with open(json_path, "w") as f:
        json.dump(similarity_map, f, separators=(",", ":"))

    print(f"[✓] Similarity JSON written: {json_path}")
    print(f"[✓] Objects processed: {processed_count}")
    print(f"[✓] Objects with similarities: {found_similarities}")
    print(f"[✓] Total similarity mappings: {len(similarity_map)}")
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
    # Try both possible paths
    paths_to_try = [
        ("indexes/{}.faiss".format(stix_type), "csv_files_with_summary_SDOs/{}.csv".format(stix_type)),
        ("modules/indexes/{}.faiss".format(stix_type), "modules/csv_files_with_summary_SDOs/{}.csv".format(stix_type))
    ]
    
    for index_path, csv_path in paths_to_try:
        try:
            index = faiss.read_index(index_path)
            loader = CSVLoader(csv_path, encoding="utf-8")
            docs = loader.load()
            return index, docs
        except (FileNotFoundError, RuntimeError):
            continue
    
    raise FileNotFoundError(f"Index or CSV file not found for {stix_type}")

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
    threshold: float = 0.3   # Lowered default threshold
):
    try:
        index, docs = load_index(stix_type)
        print(f"[DEBUG] Loaded index for {stix_type} with {len(docs)} documents")
    except FileNotFoundError as e:
        print(f"[DEBUG] Failed to load index for {stix_type}: {e}")
        raise

    query_embedding = embedder.embed_query(query_text)
    query_embedding = np.array([query_embedding], dtype="float32")
    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(query_embedding, top_k)
    print(f"[DEBUG] Search scores for {stix_type}: {scores[0]}")

    results = []
    for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
        print(f"[DEBUG] Match {rank+1}: score={score:.4f}, threshold={threshold}")
        if score < threshold:
            print(f"[DEBUG] Skipping match {rank+1}: score {score:.4f} < threshold {threshold}")
            continue   # 👈 FILTER HERE

        results.append({
            "rank": rank + 1,
            "score": float(score),
            "document": docs[idx]
        })

    print(f"[DEBUG] Returning {len(results)} results for {stix_type}")
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
# process_csv("/Users/alwyndsouza/Documents/GitHub/stix-ai-dashboard/modules/cleaned_files/stix_bundle-17.csv")

# generate_similarity_json("/Users/alwyndsouza/Documents/GitHub/stix_normalizer/cosine_sim/stix_bundle-18.csv")