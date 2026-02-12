#!/usr/bin/env python3
"""
Process STIX PDFs and chunk by sections using table of contents
"""
import PyPDF2
import re
import json
import os
from pathlib import Path

PDF_DIR = "knowledge_base/stix_pdfs"
OUTPUT_DIR = "knowledge_base/pdf_chunks"

def extract_toc(pdf_reader):
    """Extract table of contents to identify sections"""
    toc = []
    try:
        outlines = pdf_reader.outline
        for item in outlines:
            if isinstance(item, dict):
                toc.append({
                    'title': item.get('/Title', ''),
                    'page': pdf_reader.get_destination_page_number(item) if hasattr(item, 'page') else None
                })
    except:
        pass
    return toc

def extract_version_from_filename(filename):
    """Extract STIX/TAXII version from filename"""
    # Match patterns like v2.0, v2.1, v1.2, etc.
    version_match = re.search(r'v(\d+\.\d+(?:\.\d+)?)', filename.lower())
    if version_match:
        return version_match.group(1)
    return None

def chunk_by_headers(text, filename):
    """Chunk text by section headers"""
    # Match common header patterns
    sections = re.split(r'\n(?=\d+\.?\d*\s+[A-Z][^\n]{10,}|Appendix [A-Z]|Chapter \d+)', text)
    
    # Extract version from filename
    version = extract_version_from_filename(filename)
    
    chunks = []
    for i, section in enumerate(sections):
        section = section.strip()
        if len(section) > 100:  # Skip tiny sections
            # Extract title (first line)
            lines = section.split('\n', 1)
            title = lines[0][:100] if lines else f"Section {i}"
            
            metadata = {
                'source': filename,
                'type': 'stix_pdf',
                'section': title,
                'chunk_id': i
            }
            
            # Add version if found
            if version:
                metadata['stix_version'] = version
            
            chunks.append({
                'content': section[:2000],  # Limit chunk size
                'metadata': metadata
            })
    return chunks

def process_pdf(filepath):
    """Process single PDF file"""
    filename = os.path.basename(filepath)
    print(f"Processing {filename}...")
    
    chunks = []
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            # Extract all text
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Chunk by sections
            chunks = chunk_by_headers(text, filename)
            print(f"  Created {len(chunks)} chunks")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    return chunks

def main():
    pdf_dir = Path(PDF_DIR)
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not pdf_dir.exists():
        print(f"Creating {PDF_DIR}/ - place your STIX PDFs there")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        return
    
    all_chunks = []
    
    for pdf_file in pdf_dir.glob("*.pdf"):
        chunks = process_pdf(pdf_file)
        all_chunks.extend(chunks)
    
    if all_chunks:
        output_file = output_dir / "pdf_chunks.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=2)
        
        print(f"\n✅ Processed {len(all_chunks)} total chunks")
        print(f"📁 Saved to {output_file}")
        print("\nNext: Rebuild RAG index to include these chunks")
    else:
        print("No PDFs found or processed")

if __name__ == "__main__":
    main()
