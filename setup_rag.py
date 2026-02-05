#!/usr/bin/env python3
"""
RAG System Setup Script
Run this once to initialize the RAG system and build the vector index.
"""

import os
import sys
import logging
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from modules.rag_engine import RAGEngine

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'chromadb', 'sentence_transformers', 'beautifulsoup4', 
        'pandas', 'requests', 'ollama'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements_rag.txt")
        return False
    
    print("✅ All dependencies installed")
    return True

def check_knowledge_base():
    """Check if knowledge base exists and has data"""
    kb_path = Path("knowledge_base")
    
    if not kb_path.exists():
        print("❌ Knowledge base directory not found")
        return False
    
    mitre_path = kb_path / "mitre_attack"
    schema_path = kb_path / "stix_schemas"
    
    mitre_files = list(mitre_path.glob("*.json")) + list(mitre_path.glob("*.csv")) if mitre_path.exists() else []
    schema_files = list(schema_path.glob("*.html")) if schema_path.exists() else []
    
    print(f"📁 Found {len(mitre_files)} MITRE files")
    print(f"📁 Found {len(schema_files)} STIX schema files")
    
    if not mitre_files and not schema_files:
        print("❌ No data files found in knowledge base")
        return False
    
    return True

def test_ollama():
    """Test Ollama connection"""
    try:
        import ollama
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[{'role': 'user', 'content': 'Hello'}]
        )
        print("✅ Ollama connection successful")
        return True
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("Make sure Ollama is running and llama3.1:8b is installed")
        print("Run: ollama pull llama3.1:8b")
        return False

def initialize_rag():
    """Initialize RAG system and build index"""
    print("🚀 Initializing RAG system...")
    
    try:
        rag_engine = RAGEngine()
        print("✅ RAG engine initialized")
        
        print("📚 Building vector index...")
        rag_engine.build_index()
        
        stats = rag_engine.get_stats()
        doc_count = stats['vector_store_info']['document_count']
        print(f"✅ Index built successfully with {doc_count} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 Setting up STIX RAG System...")
    print("=" * 50)
    
    setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check knowledge base
    if not check_knowledge_base():
        return False
    
    # Test Ollama (optional)
    print("\n🔌 Testing Ollama connection...")
    ollama_ok = test_ollama()
    if not ollama_ok:
        print("⚠️  Ollama not available - RAG will work but responses will fail")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Initialize RAG
    print("\n🚀 Initializing RAG system...")
    if not initialize_rag():
        return False
    
    print("\n" + "=" * 50)
    print("✅ RAG System Setup Complete!")
    print("\nNext steps:")
    print("1. Run: streamlit run dashboard.py")
    print("2. Navigate to 'RAG Chat' in the sidebar")
    print("3. Start asking questions!")
    print("\nExample questions:")
    print("- What is a STIX indicator?")
    print("- Explain MITRE ATT&CK technique T1566")
    print("- How do I convert STIX 1.x to 2.1?")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)