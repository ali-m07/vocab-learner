#!/usr/bin/env python3
"""
Update words_translated.json with correct POS tags from GitHub dictionary.
This script will be run via git commands to update the static frontend.
"""

import json
import csv
import requests
from pathlib import Path
from io import StringIO
from typing import Dict

# Increase CSV field size limit
csv.field_size_limit(10000000)

def load_pos_dict() -> Dict[str, str]:
    """Load POS dictionary from GitHub CSV"""
    pos_dict = {}
    
    print("📥 Downloading POS dictionary from GitHub...")
    url = "https://raw.githubusercontent.com/benjihillard/English-Dictionary-Database/main/english%20Dictionary.csv"
    
    try:
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            print(f"⚠️ Failed: HTTP {response.status_code}")
            return pos_dict
        
        print("📖 Parsing POS dictionary...")
        content = response.text
        reader = csv.DictReader(StringIO(content))
        
        # Map common POS variations to standard forms
        pos_map = {
            'dat. & obj.': 'pronoun',
            'dat.': 'pronoun',
            'obj.': 'pronoun',
            'pron.': 'pronoun',
            'n.': 'noun',
            'v.': 'verb',
            'a.': 'adjective',
            'adv.': 'adverb',
            'prep.': 'preposition',
            'conj.': 'conjunction',
            'interj.': 'interjection',
        }
        
        preferred = {"noun", "verb", "adjective", "adverb", "pronoun"}
        
        for row in reader:
            word_val = None
            pos_val = None
            
            for key, val in row.items():
                k = key.lower()
                if 'word' in k and not word_val:
                    word_val = str(val).strip().lower()
                elif ('pos' in k or 'part' in k or 'speech' in k) and not pos_val:
                    pos_val = str(val).strip()
            
            if word_val and pos_val:
                # Normalize POS
                pos_normalized = pos_val.lower()
                for old, new in pos_map.items():
                    if old in pos_normalized:
                        pos_normalized = new
                        break
                
                # Keep only if better than existing
                if word_val not in pos_dict:
                    pos_dict[word_val] = pos_normalized
                else:
                    cur = pos_dict[word_val].lower()
                    if pos_normalized in preferred and cur not in preferred:
                        pos_dict[word_val] = pos_normalized
        
        print(f"✅ Loaded {len(pos_dict)} POS tags")
    except Exception as e:
        print(f"⚠️ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return pos_dict

def main():
    repo_root = Path(__file__).parent
    json_file = repo_root / "frontend" / "static" / "data" / "words_translated.json"
    
    if not json_file.exists():
        print(f"❌ {json_file} not found")
        return
    
    # Load existing JSON
    print(f"📖 Loading {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        words = data.get('words', [])
    
    print(f"📝 Found {len(words)} words")
    
    # Load POS dictionary
    pos_dict = load_pos_dict()
    
    # Update POS tags
    updated = 0
    for word_data in words:
        word_lower = word_data.get('word', '').lower().strip()
        if word_lower in pos_dict:
            old_pos = word_data.get('word_type', '')
            new_pos = pos_dict[word_lower]
            if old_pos != new_pos:
                word_data['word_type'] = new_pos
                updated += 1
    
    # Save
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({'words': words}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Updated {updated} POS tags")
    
    # Test
    you_word = next((w for w in words if w.get('word') == 'you'), None)
    if you_word:
        print(f"\n🧪 Test: 'you' -> {you_word.get('word_type')} (was: verb)")

if __name__ == "__main__":
    main()
