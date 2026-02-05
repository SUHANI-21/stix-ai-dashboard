import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import streamlit as st
INDEX = None
DOCS = []
MODEL = None


MODEL = SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_resource
def load_knowledge_base(folder="knowledge_base"):
    global INDEX, DOCS, MODEL

    if MODEL is None:
        MODEL = SentenceTransformer("all-MiniLM-L6-v2")

    texts = []

    for file in os.listdir(folder):
        if file.endswith(".json"):
            with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                objects = data.get("objects", [])
                for obj in objects:
                    texts.append(json.dumps(obj))

    if not texts:
        INDEX = None
        DOCS = []
        return

    embeddings = MODEL.encode(texts, batch_size=32, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]
    INDEX = faiss.IndexFlatL2(dimension)
    INDEX.add(embeddings)

    DOCS = texts
    print(f"📚 Knowledge Base Loaded with {len(DOCS)} threat records")


    # 🔹 Batch embedding to avoid memory spikes
    embeddings = []
    batch_size = 256

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        emb = MODEL.encode(batch)
        embeddings.append(emb)

    embeddings = np.vstack(embeddings)
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index, texts


def get_rag_credibility(threat_description):
    global INDEX, DOCS

    if not threat_description or not isinstance(threat_description, str):
        return 30, "Low Trust", "No meaningful description found."

    if INDEX is None:
        load_knowledge_base()

    query_embedding = MODEL.encode([threat_description])
    distances, indices = INDEX.search(np.array(query_embedding), k=5)

    matched_docs = [DOCS[i] for i in indices[0] if i < len(DOCS)]
    similarity_hits = len(matched_docs)

    # ---------- SIGNAL 1: Similarity ----------
    similarity_score = similarity_hits * 10   # max 50

    # ---------- SIGNAL 2: Description Quality ----------
    length_score = min(len(threat_description) / 50, 1) * 15

    # ---------- SIGNAL 3: Suspicious Words ----------
    suspicious_words = ["test", "fake", "unknown", "example", "demo"]
    penalty = 0
    for word in suspicious_words:
        if word in threat_description.lower():
            penalty += 10

    # ---------- SIGNAL 4: Known Trusted Sources ----------
    trusted_sources = ["mitre", "cisa", "kaspersky", "crowdstrike", "microsoft"]
    trust_bonus = 0
    for source in trusted_sources:
        if source in threat_description.lower():
            trust_bonus += 10

    # ---------- FINAL SCORE ----------
    raw_score = similarity_score + length_score + trust_bonus - penalty
    score = int(max(20, min(95, raw_score)))

    # ---------- LEVEL ----------
    if score >= 75:
        level = "High Trust"
    elif score >= 45:
        level = "Medium Trust"
    else:
        level = "Low Trust"

    explanation = (
        f"{similarity_hits} similar records found. "
        f"Description richness contributed {int(length_score)} points. "
        f"{'Trusted sources detected. ' if trust_bonus else ''}"
        f"{'Suspicious wording lowered credibility.' if penalty else ''}"
    )

    return score, level, explanation




