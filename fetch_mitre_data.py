#!/usr/bin/env python3
"""
Fetch latest MITRE ATT&CK data from official sources
"""
import requests
import json
from pathlib import Path

MITRE_URLS = {
    'enterprise': 'https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json',
    'mobile': 'https://raw.githubusercontent.com/mitre/cti/master/mobile-attack/mobile-attack.json',
    'ics': 'https://raw.githubusercontent.com/mitre/cti/master/ics-attack/ics-attack.json'
}

OUTPUT_DIR = Path("knowledge_base/mitre_attack")

def fetch_mitre_data():
    """Fetch MITRE ATT&CK STIX bundles"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for domain, url in MITRE_URLS.items():
        print(f"📥 Fetching {domain} ATT&CK data...")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            output_file = OUTPUT_DIR / f"mitre_{domain}_attack.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Count objects
            obj_count = len(data.get('objects', []))
            print(f"✅ Saved {obj_count} objects to {output_file.name}")
            
        except Exception as e:
            print(f"❌ Failed to fetch {domain}: {e}")

if __name__ == "__main__":
    print("🚀 Fetching MITRE ATT&CK data...")
    fetch_mitre_data()
    print("\n✅ Done! Run setup_rag.py to rebuild the index.")
