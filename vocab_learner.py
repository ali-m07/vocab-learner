#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vocabulary Learning System
Download dataset, translate to target language, and create Anki deck
"""

import kagglehub
import pandas as pd
from googletrans import Translator
from pathlib import Path
import genanki
import time
from typing import List, Dict, Optional
import json
import requests

class VocabularyLearner:
    def __init__(self, dataset_name: str = "nezahatkk/10-000-english-words-cerf-labelled", target_language: str = "fa"):
        self.dataset_name = dataset_name
        self.dataset_path = None
        self.words_df = None
        self.target_language = target_language
        self.translator = Translator()
        
    def download_dataset(self):
        """Download dataset from Kaggle"""
        print("📥 Downloading dataset...")
        try:
            self.dataset_path = kagglehub.dataset_download(self.dataset_name)
            print(f"✅ Dataset downloaded to: {self.dataset_path}")
            return self.dataset_path
        except Exception as e:
            print(f"❌ Error downloading dataset: {e}")
            raise
    
    def load_words(self):
        """Load words from dataset files"""
        if not self.dataset_path:
            self.download_dataset()
        
        print("📖 Loading words...")
        dataset_dir = Path(self.dataset_path)
        
        # Search for CSV or TXT files
        csv_files = list(dataset_dir.rglob("*.csv"))
        txt_files = list(dataset_dir.rglob("*.txt"))
        
        if csv_files:
            # Use first CSV file
            file_path = csv_files[0]
            print(f"📄 Found: {file_path}")
            
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    # Find word column
                    word_column = None
                    for col in df.columns:
                        if 'word' in col.lower() or 'text' in col.lower() or str(df[col].dtype) == 'object':
                            word_column = col
                            break
                    
                    if word_column:
                        self.words_df = df[[word_column]].copy()
                        self.words_df.columns = ['word']
                        self.words_df['word'] = self.words_df['word'].astype(str).str.strip()
                        self.words_df = self.words_df.dropna()
                        self.words_df = self.words_df[self.words_df['word'].str.len() > 0]
                        print(f"✅ Loaded {len(self.words_df)} words")
                        return self.words_df
                except Exception as e:
                    continue
            
        elif txt_files:
            # Read from TXT file
            file_path = txt_files[0]
            print(f"📄 Found: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
            self.words_df = pd.DataFrame({'word': words})
            print(f"✅ Loaded {len(self.words_df)} words")
            return self.words_df
        else:
            # List files for debugging
            all_files = list(dataset_dir.rglob("*"))
            print(f"❌ CSV or TXT file not found. Available files:")
            for f in all_files[:10]:
                print(f"  - {f}")
            raise FileNotFoundError("Word file not found")
    
    def get_word_info(self, word: str) -> Dict:
        """Get detailed word information: definition, type, examples, pronunciation"""
        info = {
            'definition': '',
            'word_type': '',
            'examples': [],
            'pronunciation': ''
        }
        
        try:
            # Use Free Dictionary API for word information
            api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}"
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
                        
                        # Word type (part of speech)
                        info['word_type'] = meaning.get('partOfSpeech', '')
                        
                        # Definition and examples
                        if 'definitions' in meaning and len(meaning['definitions']) > 0:
                            definition = meaning['definitions'][0]
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
                    # Small delay between requests to avoid rate limiting (Google Translate is free but has limits)
                    if idx > 1:
                        time.sleep(0.2)  # 200ms delay between requests
                    
                    # Translate with retry using Google Translate directly (free, no API key needed)
                    result = self.translator.translate(word, src='en', dest=self.target_language)
                    translation = result.text if result and result.text else ""
                    
                    if translation and translation.strip():
                        translations.append(translation)
                        translation_success = True
                        break
                    else:
                        raise ValueError("Empty translation received")
                        
                except Exception as e:
                    error_msg = str(e).lower()
                    if retry < max_retries - 1:
                        # Check if it's a rate limit or service error
                        if '429' in error_msg or 'rate limit' in error_msg or 'quota' in error_msg or 'too many requests' in error_msg:
                            wait_time = retry_delay * (retry + 1)
                            print(f"⏳ Rate limit hit. Waiting {wait_time}s before retry {retry + 1}/{max_retries}...")
                            time.sleep(wait_time)
                            continue
                        elif 'service unavailable' in error_msg or '503' in error_msg or '502' in error_msg or 'timed out' in error_msg:
                            wait_time = retry_delay * (retry + 1)
                            print(f"⏳ Service unavailable. Waiting {wait_time}s before retry {retry + 1}/{max_retries}...")
                            time.sleep(wait_time)
                            continue
                        else:
                            # For other errors, wait shorter time
                            time.sleep(1)
                            continue
                    else:
                        # Last retry failed
                        print(f"⚠️ Error translating '{word}' after {max_retries} attempts: {e}")
                        translations.append("")
                        break
            
            if not translation_success:
                translations.append("")
            
            # Get detailed info if requested (only if translation succeeded or we want to try anyway)
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
            except Exception as e:
                print(f"⚠️ Error getting word info for '{word}': {e}")
                definitions.append('')
                word_types.append('')
                examples_list.append('[]')
                pronunciations.append('')
            
            if idx % 10 == 0:
                translated_count = sum(1 for t in translations if t)
                print(f"📊 Progress: {idx}/{total} ({idx*100//total}%) | Translated: {translated_count}/{idx}")
            
            # Additional delay every batch to prevent rate limiting (Google Translate free tier)
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
        # 1. Download dataset
        learner.download_dataset()
        
        # 2. Load words
        learner.load_words()
        
        # 3. Translate words with details
        learner.translate_words(include_details=True)
        
        # 4. Save CSV
        learner.save_csv("vocab_translated.csv")
        
        # 5. Create Anki deck
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
