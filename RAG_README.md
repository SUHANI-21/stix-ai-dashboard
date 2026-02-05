# STIX RAG System

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements_complete.txt
```

### 2. Install Ollama & Model
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.1:8b
```

### 3. Setup Knowledge Base
Your knowledge base should be structured as:
```
knowledge_base/
├── mitre_attack/
│   ├── attack_pattern_all.json
│   ├── malware_all.json
│   ├── *.csv files
│   └── ... (other MITRE files)
├── stix_schemas/
│   ├── stix-v2.1-cs02.html
│   ├── stix-v2.0-part1-core.html
│   └── ... (other STIX docs)
└── embeddings/ (auto-created)
```

### 4. Initialize RAG System
```bash
python setup_rag.py
```

### 5. Run Dashboard
```bash
streamlit run dashboard.py
```

## Usage

1. Navigate to **"RAG Chat"** in the sidebar
2. Ask questions like:
   - "What is a STIX indicator?"
   - "Explain MITRE ATT&CK technique T1566"
   - "How do I convert STIX 1.x to 2.1?"
   - "What malware uses spearphishing?"

## Features

- **Semantic Search**: Finds relevant information from your knowledge base
- **Source Citations**: Shows which documents were used for answers
- **STIX Expertise**: Understands STIX formats and MITRE ATT&CK
- **Local LLM**: Uses Ollama for privacy and control
- **Extensible**: Easy to add more data sources

## Troubleshooting

**Ollama Connection Issues:**
- Make sure Ollama is running: `ollama serve`
- Check model is installed: `ollama list`

**Empty Responses:**
- Rebuild index: Click "🔄 Rebuild Index" in sidebar
- Check knowledge base has data files

**Slow Performance:**
- First query is slower (loading embeddings)
- Consider using smaller model for faster responses