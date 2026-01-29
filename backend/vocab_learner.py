#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vocabulary Learning System
Download word list + POS data, translate, create Anki deck
"""

import pandas as pd
from googletrans import Translator
from pathlib import Path
import genanki
import time
from typing import List, Dict, Optional
import json
import requests


class VocabularyLearner:
    def __init__(
        self,
        target_language: str = "fa",
        max_words: int = 20000,
        base_dir: Optional[Path] = None,
        word_list_url: str = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english.txt",  # 10k most common English words from Google's Trillion Word Corpus
    ):
        self.words_df = None
        self.target_language = target_language
        self.max_words = int(max_words) if max_words else 0
        self.translator = Translator()

        # Resolve paths relative to project root (not cwd)
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)

        # Word list (GitHub raw)
        self.word_list_url = word_list_url
        self.word_list_file = self.data_dir / "word_list.txt"

        # POS dictionary (GitHub raw CSV)
        self.pos_dict: Dict[str, Dict[str, str]] = {}
        self._load_pos_dictionary()
        
    def _download_file(self, url: str, dest: Path, timeout: int = 30) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        dest.write_bytes(resp.content)

    def download_dataset(self):
        """
        Backward-compat shim (old code called Kaggle download).
        We now fetch from GitHub word list, so nothing to do here.
        """
        return str(self.word_list_file)
    
    def load_words(self):
        """Load words from a GitHub-hosted word list (cached locally)."""
        print("📖 Loading words...")

        if not self.word_list_file.exists():
            print("📥 Downloading word list from GitHub...")
            self._download_file(self.word_list_url, self.word_list_file, timeout=30)
            print(f"✅ Word list downloaded: {self.word_list_file}")

        words: List[str] = []
        seen = set()
        with self.word_list_file.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                w = line.strip()
                if not w:
                    continue
                lw = w.lower()
                if lw in seen:
                    continue
                seen.add(lw)
                words.append(w)
                if self.max_words and self.max_words > 0 and len(words) >= self.max_words:
                    break

        if not words:
            raise ValueError(f"Word list is empty: {self.word_list_file}")

        self.words_df = pd.DataFrame({"word": words})
        print(f"✅ Loaded {len(self.words_df)} words")
        return self.words_df

    def _load_pos_dictionary(self) -> None:
        """Load POS dictionary from GitHub dataset (cached locally)."""
        dict_file = self.data_dir / "english_dictionary.csv"

        if not dict_file.exists():
            try:
                print("📥 Downloading English dictionary with POS tags from GitHub...")
                url = "https://raw.githubusercontent.com/benjihillard/English-Dictionary-Database/main/english%20Dictionary.csv"
                self._download_file(url, dict_file, timeout=60)
                print(f"✅ Dictionary downloaded: {dict_file}")
            except Exception as e:
                print(f"⚠️ Error downloading dictionary: {e}")
                return

        try:
            print("📖 Loading POS dictionary...")
            df = pd.read_csv(dict_file, encoding="utf-8", on_bad_lines="skip")

            word_col = None
            pos_col = None
            def_col = None

            for col in df.columns:
                c = str(col).lower()
                if word_col is None and "word" in c:
                    word_col = col
                elif pos_col is None and ("pos" in c or "part" in c or "speech" in c):
                    pos_col = col
                elif def_col is None and ("def" in c or "meaning" in c):
                    def_col = col

            if not word_col or not pos_col:
                print(f"⚠️ Could not find word/POS columns. Available: {df.columns.tolist()}")
                return

            preferred = {"noun", "verb", "adjective", "adverb", "pronoun"}

            for _, row in df.iterrows():
                word = str(row.get(word_col, "")).strip().lower()
                if not word:
                    continue
                pos = str(row.get(pos_col, "")).strip()
                definition = str(row.get(def_col, "")).strip() if def_col else ""

                if word not in self.pos_dict:
                    self.pos_dict[word] = {"pos": pos, "definition": definition}
                    continue

                cur = (self.pos_dict[word].get("pos") or "").strip().lower()
                new = (pos or "").strip().lower()
                if new in preferred and cur not in preferred:
                    self.pos_dict[word] = {"pos": pos, "definition": definition}

            print(f"✅ Loaded {len(self.pos_dict)} words with POS tags")
        except Exception as e:
            print(f"⚠️ Error loading POS dictionary: {e}")
    
    def get_word_info(self, word: str) -> Dict:
        """Get detailed word information: definition, type, examples, pronunciation"""
        info = {
            'definition': '',
            'word_type': '',
            'examples': [],
            'pronunciation': ''
        }

        word_lower = word.lower().strip()

        # Prefer local POS dictionary for POS + definition
        if word_lower in self.pos_dict:
            d = self.pos_dict[word_lower]
            info["word_type"] = d.get("pos", "") or ""
            info["definition"] = d.get("definition", "") or ""

        try:
            # Use Free Dictionary API for word information
            api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word_lower}"
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    entry = data[0]
                    
                    # Get pronunciation
                    if 'phonetics' in entry and len(entry['phonetics']) > 0:
                        info['pronunciation'] = entry['phonetics'][0].get('text', '')
                    
                    # Get meanings (definitions, examples, part of speech)
                    if 'meanings' in entry and len(entry['meanings']) > 0:
                        meaning = entry['meanings'][0]
                        
                        # Word type (part of speech) only if local dict didn't provide
                        if not info["word_type"]:
                            info['word_type'] = meaning.get('partOfSpeech', '')
                        
                        # Definition and examples
                        if 'definitions' in meaning and len(meaning['definitions']) > 0:
                            definition = meaning['definitions'][0]
                            if not info["definition"]:
                                info['definition'] = definition.get('definition', '')
                            
                            # Get examples
                            examples = []
                            for def_item in meaning['definitions'][:3]:  # Get up to 3 examples
                                if 'example' in def_item:
                                    examples.append(def_item['example'])
                            info['examples'] = examples[:2]  # Max 2 examples
                            
        except Exception as e:
            print(f"⚠️ Error fetching word info for '{word}': {e}")
        
        return info
    
    def translate_words(self, batch_size: int = 50, delay: float = 0.5, include_details: bool = True):
        """Translate words to target language with rate limiting and optional details"""
        if self.words_df is None:
            self.load_words()
        
        if 'translation' in self.words_df.columns:
            print("⚠️ Translations already exist")
            return self.words_df
        
        print(f"🌐 Translating {len(self.words_df)} words to {self.target_language}...")
        print("⏳ This may take several minutes...")
        
        translations = []
        definitions = []
        word_types = []
        examples_list = []
        pronunciations = []
        
        total = len(self.words_df)
        
        for idx, word in enumerate(self.words_df['word'], 1):
            translation_success = False
            max_retries = 3
            retry_delay = 2.0

            for retry in range(max_retries):
                try:
                    if idx > 1:
                        time.sleep(0.2)

                    result = self.translator.translate(word, src="en", dest=self.target_language)
                    translation = result.text if result and result.text else ""
                    if not translation.strip():
                        raise ValueError("Empty translation received")

                    translations.append(translation)
                    translation_success = True
                    break
                except Exception as e:
                    msg = str(e).lower()
                    if retry < max_retries - 1:
                        if "429" in msg or "rate limit" in msg or "quota" in msg or "too many requests" in msg:
                            time.sleep(retry_delay * (retry + 1))
                            continue
                        if "service unavailable" in msg or "503" in msg or "502" in msg or "timed out" in msg:
                            time.sleep(retry_delay * (retry + 1))
                            continue
                        time.sleep(1)
                        continue

                    print(f"⚠️ Error translating '{word}' after {max_retries} attempts: {e}")
                    translations.append("")

            if not translation_success and len(translations) < idx:
                translations.append("")

            # Get detailed info if requested
            try:
                if include_details:
                    info = self.get_word_info(word)
                    definitions.append(info['definition'])
                    word_types.append(info['word_type'])
                    examples_list.append(json.dumps(info['examples']))
                    pronunciations.append(info['pronunciation'])
                else:
                    definitions.append('')
                    word_types.append('')
                    examples_list.append('[]')
                    pronunciations.append('')
            except Exception:
                definitions.append("")
                word_types.append("")
                examples_list.append("[]")
                pronunciations.append("")

            if idx % 10 == 0:
                translated_count = sum(1 for t in translations if t)
                print(f"📊 Progress: {idx}/{total} ({idx*100//total}%) | Translated: {translated_count}/{idx}")

            if idx % batch_size == 0:
                time.sleep(delay)
                print(f"⏸️  Pausing {delay}s after {idx} words to avoid rate limits...")
        
        self.words_df['translation'] = translations
        if include_details:
            self.words_df['definition'] = definitions
            self.words_df['word_type'] = word_types
            self.words_df['examples'] = examples_list
            self.words_df['pronunciation'] = pronunciations
        
        print("✅ Translation completed")
        return self.words_df
    
    def save_csv(self, output_file: str = "vocab_translated.csv"):
        """Save translated words to CSV"""
        if self.words_df is None or 'translation' not in self.words_df.columns:
            print("⚠️ Translation must be done first")
            return
        
        self.words_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✅ CSV file saved: {output_file}")
    
    def create_anki_deck(self, deck_name: str = "English Vocabulary 10000", 
                        output_file: str = "vocab_deck.apkg"):
        """Create Anki deck from translated words"""
        if self.words_df is None or 'translation' not in self.words_df.columns:
            print("⚠️ Translation must be done first")
            return
        
        print("🃏 Creating Anki deck...")
        
        # Create enhanced card model
        has_details = 'definition' in self.words_df.columns
        
        if has_details:
            my_model = genanki.Model(
                1607392319,
                'Enhanced Vocabulary Model',
                fields=[
                    {'name': 'English'},
                    {'name': 'Translation'},
                    {'name': 'Definition'},
                    {'name': 'Type'},
                    {'name': 'Examples'},
                    {'name': 'Pronunciation'},
                ],
                templates=[
                    {
                        'name': 'Card 1',
                        'qfmt': '<div style="font-size: 32px; text-align: center; margin: 20px;">{{English}}</div>',
                        'afmt': '''{{FrontSide}}<hr id="answer">
                        <div style="padding: 20px;">
                            <div style="font-size: 24px; color: #6366f1; margin-bottom: 10px;"><b>{{Translation}}</b></div>
                            <div style="color: #64748b; margin-bottom: 10px;"><i>{{Type}}</i></div>
                            <div style="margin-bottom: 10px;">{{Pronunciation}}</div>
                            <div style="margin-bottom: 15px;">{{Definition}}</div>
                            <div style="color: #10b981;">{{Examples}}</div>
                        </div>''',
                    },
                ])
        else:
            my_model = genanki.Model(
                1607392319,
                'Simple Vocabulary Model',
                fields=[
                    {'name': 'English'},
                    {'name': 'Translation'},
                ],
                templates=[
                    {
                        'name': 'Card 1',
                        'qfmt': '{{English}}',
                        'afmt': '{{FrontSide}}<hr id="answer">{{Translation}}',
                    },
                ])
        
        # Create deck
        my_deck = genanki.Deck(
            2059400110,
            deck_name
        )
        
        # Add cards
        for _, row in self.words_df.iterrows():
            word = str(row['word']).strip()
            translation = str(row['translation']).strip()
            
            if word and translation:
                if has_details:
                    definition = str(row.get('definition', '')).strip()
                    word_type = str(row.get('word_type', '')).strip()
                    examples = str(row.get('examples', '[]')).strip()
                    pronunciation = str(row.get('pronunciation', '')).strip()
                    
                    note = genanki.Note(
                        model=my_model,
                        fields=[word, translation, definition, word_type, examples, pronunciation]
                    )
                else:
                    note = genanki.Note(
                        model=my_model,
                        fields=[word, translation]
                    )
                my_deck.add_note(note)
        
        # Save deck
        genanki.Package(my_deck).write_to_file(output_file)
        print(f"✅ Anki deck created: {output_file}")
        print(f"📊 Total cards: {len(self.words_df)}")
        print(f"💡 To use: Import {output_file} in Anki")


def main():
    """Main function"""
    print("=" * 50)
    print("🚀 English Vocabulary Learning System")
    print("=" * 50)
    
    learner = VocabularyLearner(target_language='fa')
    
    try:
        # 1. Load words (download/cached)
        learner.load_words()
        
        # 2. Translate words with details
        learner.translate_words(include_details=True)
        
        # 3. Save CSV
        learner.save_csv("vocab_translated.csv")
        
        # 4. Create Anki deck
        learner.create_anki_deck("English Vocabulary 10000", "vocab_deck.apkg")
        
        print("\n" + "=" * 50)
        print("✅ All done!")
        print("=" * 50)
        print("\n📝 Generated files:")
        print("  - vocab_translated.csv (words with translation)")
        print("  - vocab_deck.apkg (Anki deck for import)")
        print("\n💡 To use Anki:")
        print("  1. Open Anki")
        print("  2. File > Import")
        print("  3. Select vocab_deck.apkg")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
