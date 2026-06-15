# STIX AI Dashboard

An AI-powered Cyber Threat Intelligence (CTI) platform for ingesting, validating, analyzing, and visualizing STIX threat intelligence bundles with integrated machine learning, RAG-based querying, semantic similarity search, and threat credibility assessment.

The platform combines:

* STIX/TAXII processing
* Malware classification
* MITRE ATT&CK mapping
* Threat assessment
* RAG-powered cybersecurity querying
* Semantic similarity search
* Canonical STIX normalization

into a unified analyst workflow.

---

# Features

| Feature                        | Description                                                                                               |
| ------------------------------ | --------------------------------------------------------------------------------------------------------- |
| Version Detection & Validation | Automatically detects STIX 1.x / 2.0 / 2.1 bundles in XML or JSON format and validates schema consistency |
| Auto Conversion                | Converts STIX 1.x and STIX 2.0 objects into normalized STIX 2.1 bundles                                   |
| Threat Graph Visualization     | Interactive relationship visualization using PyVis and NetworkX                                           |
| MITRE ATT&CK Mapping           | Maps indicators, malware, and attack patterns to ATT&CK techniques                                        |
| Malware Classification         | ML-assisted malware family prediction using TF-IDF vectorization and Mistral-7B                           |
| Threat Credibility Assessment  | Multi-factor credibility scoring with IOC enrichment and confidence analysis                              |
| STIX Chat Assistant            | RAG-powered chatbot for querying STIX, ATT&CK, and malware intelligence                                   |
| Similarity Search              | FAISS-based semantic similarity search and ego-graph exploration                                          |
| Canonical Output Generator     | Generates normalized STIX 2.1 bundles for interoperability                                                |
| File Browser                   | Browse, inspect, and manage uploaded STIX bundles                                                         |

---

# Overview

Cyber Threat Intelligence data often comes from multiple sources with inconsistent structures and varying STIX versions. Analysts typically rely on multiple disconnected tools for validation, enrichment, classification, and querying.

STIX AI Dashboard addresses this challenge by providing a unified platform capable of:

* validating STIX bundles,
* converting legacy STIX formats,
* analyzing relationships,
* classifying malware behavior,
* assessing threat credibility,
* and enabling natural-language querying over CTI knowledge bases.

The platform integrates AI, machine learning, vector similarity search, and retrieval-augmented generation (RAG) into a single cybersecurity analysis workflow.

---

# Core Modules

## 1. Version Detection & Validation Module

Handles automatic identification and validation of STIX bundles.

### Capabilities

* Detects STIX 1.x, 2.0, and 2.1 formats
* Supports XML and JSON bundles
* Validates object schemas
* Checks relationship consistency
* Identifies malformed or incomplete STIX objects

### Supported STIX Objects

* indicator
* malware
* attack-pattern
* campaign
* intrusion-set
* threat-actor
* relationship

---

## 2. STIX Conversion & Canonical Output Module

Transforms heterogeneous STIX bundles into a standardized STIX 2.1 representation.

### Functionalities

* STIX 1.x → 2.1 conversion
* Field normalization
* Relationship harmonization
* Attribute restructuring
* UUID consistency handling
* Canonical STIX bundle generation

### Benefits

* Improved interoperability
* Consistent downstream processing
* Better compatibility with ML pipelines
* Enhanced retrieval quality for RAG systems

---

## 3. Malware Classification Module

Predicts malware families and ATT&CK attack patterns from CTI descriptions.

### Processing Pipeline

#### Text Preprocessing

* Lowercasing
* Tokenization
* Stopword removal
* Noise filtering

#### Feature Extraction

* TF-IDF vectorization
* N-gram extraction
* Sparse feature vector creation

#### Model Training

* One-vs-Rest Logistic Regression
* Multi-class malware classification

#### Prediction

* Malware family identification
* ATT&CK technique association

### Evaluation Metrics

* Accuracy
* Precision
* Recall
* F1-score
* Confusion Matrix

---

# 4. Threat Credibility Assessment Module

Evaluates threat reliability and severity using contextual analysis.

### Factors Considered

* IOC reputation
* Source reliability
* Malware behavior severity
* ATT&CK sophistication
* Threat relationship density
* VirusTotal enrichment
* Confidence metadata

### Output

* Credibility score (0–100)
* Threat severity level
* Confidence assessment
* Contextual intelligence summary

### Risk Categories

* Low
* Medium
* High
* Critical

---

# 5. MITRE ATT&CK Mapping Module

Maps STIX indicators and malware behaviors to MITRE ATT&CK techniques.

### Capabilities

* Technique identification
* ATT&CK ID mapping
* TTP correlation
* Behavioral categorization
* ATT&CK relationship enrichment

### Example Techniques

* PowerShell Execution
* Credential Dumping
* Persistence
* Lateral Movement
* Command and Control

---

# 6. SDO Similarity Search Module

Performs semantic similarity search across STIX Domain Objects (SDOs).

### Workflow

* Generate embeddings for STIX objects
* Store embeddings in FAISS vector database
* Convert user query into embedding vector
* Perform nearest-neighbor similarity retrieval
* Expand related ego-graph relationships

### Benefits

* Discovery of related threats
* Contextual intelligence exploration
* Similar malware identification
* Semantic IOC clustering

### Technologies

* FAISS
* sentence-transformers
* NetworkX

---

# 7. STIX Chat Module

A Retrieval-Augmented Generation (RAG)-based cybersecurity assistant for querying threat intelligence knowledge.

### Knowledge Sources

* STIX documentation
* TAXII specifications
* MITRE ATT&CK
* Malware intelligence reports
* CTI references

### RAG Workflow

1. Documents are chunked into semantic sections
2. Embeddings are generated for each chunk
3. Embeddings stored in ChromaDB / FAISS
4. User query converted into embedding vector
5. Similar chunks retrieved using vector similarity
6. Retrieved context injected into LLM prompt
7. LLM generates grounded cybersecurity response

### Benefits

* Reduced hallucination
* Domain-specific CTI responses
* Dynamic knowledge updates
* Context-aware querying

---

# AI/ML Stack

| Component              | Technology                             |
| ---------------------- | -------------------------------------- |
| Sentence Embeddings    | sentence-transformers/all-MiniLM-L6-v2 |
| Malware Classification | One-vs-Rest Logistic Regression        |
| Local LLM              | mistralai/Mistral-7B-Instruct-v0.1     |
| Vector Search          | FAISS                                  |
| RAG Knowledge Store    | ChromaDB                               |
| Local LLM Inference    | Ollama                                 |
| Graph Visualization    | PyVis + NetworkX                       |
| Dashboard Framework    | Streamlit                              |

---

# Technologies Used

## Backend

* Python
* Streamlit

## Machine Learning

* scikit-learn
* TF-IDF Vectorizer
* sentence-transformers

## Threat Intelligence Standards

* STIX 2.x
* TAXII 2.x
* MITRE ATT&CK

## RAG & Vector Search

* FAISS
* ChromaDB
* LangChain
* Ollama

## Visualization

* Plotly
* PyVis
* NetworkX

---

# Project Structure

```bash
stix-ai-dashboard/
├── app.py
├── pages/
│   ├── 1_Dashboard.py
│   ├── Version_Detector_and_Validator.py
│   ├── SDO_Similarity_Search.py
│   ├── Attack_Mapping.py
│   ├── malware_classifier.py
│   ├── Credibility_Assessment_Module.py
│   ├── STIX_Chat.py
│   ├── Canonical_Output.py
│   └── file_browser.py
│
├── modules/
│   ├── enhanced_detector.py
│   ├── enhanced_validator.py
│   ├── converter.py
│   ├── similarity_search.py
│   ├── rag_engine.py
│   ├── credibility_assessor.py
│   ├── attack_type_mapper.py
│   ├── storage.py
│   └── ...
│
├── vector_db/
├── knowledge_base/
├── enterprise-attack.json
└── requirements.txt
```

---

# Future Enhancements

* Real-time TAXII streaming
* Graph database integration
* Transformer-based malware classifiers
* Multi-modal CTI support
* SOC/SIEM integrations
* Automated incident response recommendations
* Explainable AI threat reasoning

---

# Contributors

| Contributor  | GitHub                                                                        |
| ------------ | ----------------------------------------------------------------------------- |
| Prerika P    | [@PrerikaP1331](https://github.com/PrerikaP1331?utm_source=chatgpt.com)       |
| Alwyn Dsouza | [@dsouzalwyn14120](https://github.com/dsouzalwyn14120?utm_source=chatgpt.com) |
| Neha         | [@nehaapc](https://github.com/nehaapc?utm_source=chatgpt.com)                 |
| Romila M     | [@RomilaM](https://github.com/RomilaM?utm_source=chatgpt.com)                 |
| Suhani       | [@SUHANI-21](https://github.com/SUHANI-21?utm_source=chatgpt.com)             |

This project was collaboratively developed as part of a research initiative focused on AI-assisted Cyber Threat Intelligence (CTI), malware analysis, and intelligent cybersecurity automation.
