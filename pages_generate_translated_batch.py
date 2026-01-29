#!/usr/bin/env python3
"""
Generate translated words in batches (faster, language-specific).

Usage:
  python3 pages_generate_translated_batch.py fa   # Persian
  python3 pages_generate_translated_batch.py es   # Spanish
  etc.

This generates words_translated_<lang>.json files that can be merged.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List
import requests

def get_word_info(word: str) -> Dict[str, any]:
    """Get definition and examples"""
    try:
        res = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
            timeout=5
        )
        if res.status_code != 200:
            return {}
        data = res.json()
        entry = data[0] if data else {}
        meaning = entry.get('meanings', [{}])[0]
        def_item = meaning.get('definitions', [{}])[0]
        examples = [
            d.get('example', '')
            for d in meaning.get('definitions', [])[:3]
            if d.get('example')
        ]
        return {
            'pronunciation': entry.get('phonetics', [{}])[0].get('text', ''),
            'word_type': meaning.get('partOfSpeech', ''),
            'definition': def_item.get('definition', ''),
            'examples': examples[:2],
        }
    except Exception:
        return {}

def translate_word(word: str, target: str) -> str | None:
    """Translate using multiple free endpoints"""
    endpoints = [
        'https://libretranslate.de/translate',
        'https://translate.argosopentech.com/translate',
    ]
    
    for endpoint in endpoints:
        try:
            res = requests.post(
                endpoint,
                json={'q': word, 'source': 'en', 'target': target, 'format': 'text'},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            if res.status_code == 200:
                data = res.json()
                text = data.get('translatedText', '').strip()
                if text:
                    return text
        except Exception:
            continue
    return None

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 pages_generate_translated_batch.py <lang_code>")
        print("Example: python3 pages_generate_translated_batch.py fa")
        sys.exit(1)
    
    target_lang = sys.argv[1].lower()
    
    try:
        from wordfreq import top_n_list
    except Exception as e:
        raise SystemExit("wordfreq is required. Install with: pip install wordfreq") from e

    repo_root = Path(__file__).parent
    words_file = repo_root / "frontend" / "static" / "data" / "words.json"
    out_file = repo_root / "frontend" / "static" / "data" / f"words_translated_{target_lang}.json"
    
    if not words_file.exists():
        print(f"❌ {words_file} not found. Run pages_generate_words.py first.")
        return
    
    with open(words_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        words_list = data.get('words', [])[:20000]
    
    print(f"📖 Processing {len(words_list)} words for language: {target_lang}")
    print("⏳ This will take a while (rate-limited APIs)...")
    
    result: List[Dict[str, any]] = []
    
    for idx, word in enumerate(words_list, 1):
        if not isinstance(word, str) or not word.strip():
            continue
        
        word_lower = word.lower().strip()
        word_data: Dict[str, any] = {
            'word': word_lower,
            'translations': {},
        }
        
        # Get definition/examples
        info = get_word_info(word_lower)
        word_data.update(info)
        
        # Translate
        translated = translate_word(word_lower, target_lang)
        if translated:
            word_data['translations'][target_lang] = translated
        
        result.append(word_data)
        
        if idx % 100 == 0:
            print(f"📊 Progress: {idx}/{len(words_list)} ({idx*100//len(words_list)}%)")
            # Save intermediate progress
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump({'words': result}, f, ensure_ascii=False, indent=2)
        
        time.sleep(0.2)  # Rate limit
    
    # Final save
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({'words': result}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Wrote {len(result)} translated words to {out_file}")

if __name__ == "__main__":
    main()
