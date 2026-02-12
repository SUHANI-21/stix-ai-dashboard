import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Dict, List
import logging

class WebSearchEnricher:
    """Fetch information from online sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def is_mitre_technique(self, text: str) -> Optional[str]:
        """Check if text contains MITRE technique ID (ATT&CK or ATLAS)"""
        # ATT&CK: T1234 or T1234.001
        match = re.search(r'\b(T\d{4}(?:\.\d{3})?)\b', text, re.IGNORECASE)
        if match:
            return ('attack', match.group(1).upper())
        
        # ATLAS: AML.T0001 or similar
        match = re.search(r'\b(AML\.T\d{4})\b', text, re.IGNORECASE)
        if match:
            return ('atlas', match.group(1).upper())
        
        return None
    
    def fetch_mitre_technique(self, technique_id: str) -> Optional[Dict]:
        """Fetch technique from MITRE ATT&CK website"""
        try:
            technique_id = technique_id.upper().replace('.', '/')
            url = f"https://attack.mitre.org/techniques/{technique_id}/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            name = soup.find('h1')
            name = name.text.strip() if name else "Unknown"
            
            desc_div = soup.find('div', class_='description-body')
            description = desc_div.text.strip() if desc_div else ""
            
            tactics = []
            tactics_section = soup.find('div', class_='tactics')
            if tactics_section:
                for link in tactics_section.find_all('a'):
                    tactics.append(link.text.strip())
            
            platforms = []
            platforms_section = soup.find('div', class_='platforms')
            if platforms_section:
                platforms = [p.strip() for p in platforms_section.text.split(',')]
            
            return {
                'id': technique_id.replace('/', '.'),
                'name': name,
                'description': description[:1000],
                'tactics': tactics,
                'platforms': platforms,
                'url': url,
                'framework': 'ATT&CK'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to fetch MITRE technique: {e}")
            return None
    
    def fetch_atlas_technique(self, technique_id: str) -> Optional[Dict]:
        """Fetch technique from MITRE ATLAS website"""
        try:
            url = f"https://atlas.mitre.org/techniques/{technique_id}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            name = soup.find('h1')
            name = name.text.strip() if name else "Unknown"
            
            desc = soup.find('div', class_='description')
            description = desc.text.strip() if desc else ""
            
            tactics = []
            tactic_section = soup.find('div', class_='tactics')
            if tactic_section:
                for link in tactic_section.find_all('a'):
                    tactics.append(link.text.strip())
            
            return {
                'id': technique_id,
                'name': name,
                'description': description[:1000],
                'tactics': tactics,
                'url': url,
                'framework': 'ATLAS'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to fetch ATLAS technique: {e}")
            return None
    
    def enrich_with_web_search(self, question: str) -> Optional[str]:
        """Enrich context with web-scraped information"""
        result = self.is_mitre_technique(question)
        if not result:
            return None
        
        framework, tech_id = result
        
        if framework == 'attack':
            technique = self.fetch_mitre_technique(tech_id)
        else:
            technique = self.fetch_atlas_technique(tech_id)
        
        if not technique:
            return None
        
        enriched = f"""
=== MITRE {technique['framework']} Technique {technique['id']} (from official source) ===

Name: {technique['name']}

Tactics: {', '.join(technique['tactics']) if technique['tactics'] else 'N/A'}

{f"Platforms: {', '.join(technique['platforms'])}" if technique.get('platforms') else ''}

Description:
{technique['description']}

Official URL: {technique['url']}

===
"""
        return enriched
