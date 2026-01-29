#!/usr/bin/env python3
"""
Generate translated word list for GitHub Pages (pre-translated, no runtime API calls).

This generates words_translated.json with translations for multiple languages.
Uses free APIs with rate limiting and caching.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Languages to translate to (most common)
TARGET_LANGUAGES = ['fa', 'es', 'fr', 'de', 'ar', 'tr', 'ru', 'zh', 'ja', 'ko']

def get_word_info(word: str) -> Dict[str, any]:
    """Get definition and examples from free dictionary API"""
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

def translate_word_libre(word: str, target: str) -> Optional[str]:
    """Translate using LibreTranslate (free, public endpoint)"""
    try:
        res = requests.post(
            'https://libretranslate.de/translate',
            json={'q': word, 'source': 'en', 'target': target, 'format': 'text'},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            return data.get('translatedText', '').strip()
    except Exception:
        pass
    return None

def main() -> None:
    try:
        from wordfreq import top_n_list
    except Exception as e:
        raise SystemExit("wordfreq is required. Install with: pip install wordfreq") from e

    repo_root = Path(__file__).parent
    words_file = repo_root / "frontend" / "static" / "data" / "words.json"
    out_file = repo_root / "frontend" / "static" / "data" / "words_translated.json"
    
    # Load base word list
    if not words_file.exists():
        print(f"❌ {words_file} not found. Run pages_generate_words.py first.")
        return
    
    with open(words_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        words_list = data.get('words', [])[:20000]  # Top 20k
    
    print(f"📖 Processing {len(words_list)} words...")
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
        
        # Get definition/examples (usage)
        info = get_word_info(word_lower)
        word_data.update(info)
        
        # Translate to common languages
        for lang in TARGET_LANGUAGES:
            translated = translate_word_libre(word_lower, lang)
            if translated:
                word_data['translations'][lang] = translated
            time.sleep(0.2)  # Rate limit: 5 req/sec
        
        result.append(word_data)
        
        if idx % 100 == 0:
            print(f"📊 Progress: {idx}/{len(words_list)} ({idx*100//len(words_list)}%)")
            # Save intermediate progress
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump({'words': result}, f, ensure_ascii=False, indent=2)
        
        time.sleep(0.1)  # Small delay between words
    
    # Final save
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({'words': result}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Wrote {len(result)} translated words to {out_file}")
    print(f"   Languages: {', '.join(TARGET_LANGUAGES)}")

if __name__ == "__main__":
    main()
