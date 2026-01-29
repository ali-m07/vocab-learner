#!/usr/bin/env python3
"""
Generate complete words_translated.json with all 10k words and correct POS from GitHub.
Translations are left empty (use backend API for translations).
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
    words_file = repo_root / "frontend" / "static" / "data" / "words.json"
    out_file = repo_root / "frontend" / "static" / "data" / "words_translated.json"
    
    # Load word list
    if not words_file.exists():
        print(f"❌ {words_file} not found. Run pages_generate_words.py first.")
        return
    
    with open(words_file, 'r', encoding='utf-8') as f:
        words_list = json.load(f).get('words', [])
    
    print(f"📖 Processing {len(words_list)} words...")
    
    # Load POS dictionary
    pos_dict = load_pos_dict()
    
    # Generate word data with POS tags
    result = []
    for word in words_list:
        word_lower = word.lower().strip()
        word_data = {
            'word': word_lower,
            'translations': {},  # Empty - use backend API for translations
            'pronunciation': '',
            'word_type': pos_dict.get(word_lower, ''),
            'definition': '',
            'examples': [],
        }
        result.append(word_data)
    
    # Save
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({'words': result}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Generated {len(result)} words with POS tags")
    
    # Test
    you_word = next((w for w in result if w.get('word') == 'you'), None)
    if you_word:
        print(f"\n🧪 Test: 'you' -> {you_word.get('word_type')}")

if __name__ == "__main__":
    main()
