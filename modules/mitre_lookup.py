import requests
import re
import json
from typing import Optional, Dict, Any
import logging

class MITRELookup:
    """Direct lookup for MITRE ATT&CK techniques"""
    
    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.kb_path = knowledge_base_path
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self._load_local_data()
    
    def _load_local_data(self):
        """Load local MITRE data for offline lookup"""
        try:
            import os
            attack_file = os.path.join(self.kb_path, "mitre_attack", "attack_pattern_all.json")
            if os.path.exists(attack_file):
                with open(attack_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for obj in data.get('objects', []):
                        if obj.get('type') == 'attack-pattern':
                            for ref in obj.get('external_references', []):
                                if ref.get('source_name') == 'mitre-attack':
                                    tech_id = ref.get('external_id')
                                    if tech_id:
                                        self.cache[tech_id] = obj
                self.logger.info(f"Loaded {len(self.cache)} techniques from local data")
        except Exception as e:
            self.logger.warning(f"Could not load local MITRE data: {e}")
    
    def is_technique_id(self, text: str) -> Optional[str]:
        """Check if text contains a MITRE technique ID"""
        match = re.search(r'\b(T\d{4}(?:\.\d{3})?)\b', text, re.IGNORECASE)
        return match.group(1).upper() if match else None
    
    def lookup_technique(self, technique_id: str) -> Optional[Dict[str, Any]]:
        """Lookup technique details"""
        technique_id = technique_id.upper()
        
        # Try local cache first
        if technique_id in self.cache:
            return self._format_technique(self.cache[technique_id])
        
        # Try online lookup
        return self._fetch_online(technique_id)
    
    def _format_technique(self, obj: Dict) -> Dict[str, Any]:
        """Format STIX object into readable technique info"""
        tech_id = None
        url = None
        for ref in obj.get('external_references', []):
            if ref.get('source_name') == 'mitre-attack':
                tech_id = ref.get('external_id')
                url = ref.get('url')
                break
        
        return {
            'id': tech_id,
            'name': obj.get('name'),
            'description': obj.get('description'),
            'tactics': [phase['phase_name'] for phase in obj.get('kill_chain_phases', [])],
            'url': url,
            'platforms': obj.get('x_mitre_platforms', []),
            'data_sources': obj.get('x_mitre_data_sources', []),
            'detection': obj.get('x_mitre_detection', ''),
            'version': obj.get('x_mitre_version', ''),
            'created': obj.get('created', ''),
            'modified': obj.get('modified', '')
        }
    
    def _fetch_online(self, technique_id: str) -> Optional[Dict[str, Any]]:
        """Fetch from MITRE ATT&CK website (fallback)"""
        try:
            # MITRE ATT&CK TAXII server
            url = f"https://cti-taxii.mitre.org/stix/collections/95ecc380-afe9-11e4-9b6c-751b66dd541e/objects"
            headers = {"Accept": "application/taxii+json;version=2.1"}
            params = {"match[id]": f"attack-pattern--*", "match[external_references.external_id]": technique_id}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                objects = data.get('objects', [])
                if objects:
                    return self._format_technique(objects[0])
        except Exception as e:
            self.logger.debug(f"Online lookup failed: {e}")
        
        return None
    
    def enrich_context(self, question: str, context: str) -> str:
        """Enrich context with direct MITRE lookup if technique ID found"""
        tech_id = self.is_technique_id(question)
        if not tech_id:
            return context
        
        technique = self.lookup_technique(tech_id)
        if not technique:
            return context
        
        # Add technique details at the top of context
        enriched = f"""MITRE ATT&CK Technique {tech_id} (Direct Lookup):
ID: {technique['id']}
Name: {technique['name']}
Tactics: {', '.join(technique['tactics'])}
Description: {technique['description'][:500]}...
Platforms: {', '.join(technique['platforms'])}
URL: {technique['url']}

---
{context}"""
        
        return enriched
