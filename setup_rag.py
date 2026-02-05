#!/usr/bin/env python3
"""
RAG System Setup - One-time initialization
Builds the vector index from knowledge base files
"""

import os
import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from modules.rag_engine import RAGEngine


def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def check_knowledge_base():
    """Check if knowledge base has data"""
    kb_path = Path("knowledge_base")
    
    if not kb_path.exists():
        print("❌ knowledge_base directory not found")
        return False
    
    mitre_path = kb_path / "mitre_attack"
    schema_path = kb_path / "stix_schemas"
    
    mitre_files = []
    if mitre_path.exists():
        mitre_files = list(mitre_path.glob("*.json")) + list(mitre_path.glob("*.csv"))
    
    schema_files = []
    if schema_path.exists():
        schema_files = list(schema_path.glob("*.html"))
    
    print(f"📁 Found {len(mitre_files)} MITRE files")
    print(f"📁 Found {len(schema_files)} STIX schema files")
    
    if not mitre_files and not schema_files:
        print("❌ No data files found")
        return False
    
    return True


def test_ollama():
    """Test Ollama is available"""
    try:
        import ollama
        print("✅ Ollama module available")
        return True
    except ImportError:
        print("⚠️  Ollama not installed (optional, install with: pip install ollama)")
        return False


def initialize_rag():
    """Initialize and build RAG index"""
    print("\n🚀 Initializing RAG system...")
    
    try:
        rag = RAGEngine()
        print("✅ RAG engine created")
        
        print("📚 Building vector index...")
        rag.build_index()
        
        stats = rag.get_stats()
        doc_count = stats['vector_store_info']['document_count']
        print(f"✅ Index built with {doc_count} documents")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main setup"""
    print("=" * 50)
    print("🔧 STIX RAG System Setup")
    print("=" * 50)
    
    setup_logging()
    
    # Check knowledge base
    print("\n📂 Checking knowledge base...")
    if not check_knowledge_base():
        return False
    
    # Check Ollama
    print("\n🔌 Checking Ollama...")
    test_ollama()
    
    # Initialize RAG
    print("\n🚀 Building RAG system...")
    if not initialize_rag():
        return False
    
    print("\n" + "=" * 50)
    print("✅ RAG System Setup Complete!")
    print("=" * 50)
    print("\n📝 Next steps:")
    print("1. Run: streamlit run dashboard.py")
    print("2. Go to 'RAG Chat' in the sidebar")
    print("3. Start asking questions!")
    print("\n💡 Example questions:")
    print("  - What is STIX?")
    print("  - Explain MITRE ATT&CK framework")
    print("  - How to convert STIX formats?")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
