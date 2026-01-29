#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vocabulary Learning System
Download dataset, translate to target language, and create Anki deck
"""

import kagglehub
import pandas as pd
from deep_translator import GoogleTranslator
from pathlib import Path
import genanki
import time
from typing import List, Dict, Optional
import json
import requests

class VocabularyLearner:
    def __init__(
        self,
        dataset_name: str = "yk1598/479k-english-words",
        target_language: str = "fa",
        max_words: int = 20000,
    ):
        self.dataset_name = dataset_name
        self.dataset_path = None
        self.words_df = None
        self.target_language = target_language
        self.max_words = max_words
        self.translator = GoogleTranslator(source='en', target=target_language)
        
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
                        # De-duplicate and cap size
                        self.words_df = self.words_df.drop_duplicates(subset=['word'])
                        if self.max_words and self.max_words > 0:
                            self.words_df = self.words_df.head(self.max_words)
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
            # De-duplicate and cap size
            seen = set()
            unique_words = []
            for w in words:
                lw = w.lower()
                if lw in seen:
                    continue
                seen.add(lw)
                unique_words.append(w)
                if self.max_words and self.max_words > 0 and len(unique_words) >= self.max_words:
                    break
            self.words_df = pd.DataFrame({'word': unique_words})
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
            try:
                # Translate
                translation = self.translator.translate(word)
                translations.append(translation)
                
                # Get detailed info if requested
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
                
                if idx % 10 == 0:
                    print(f"📊 Progress: {idx}/{total} ({idx*100//total}%)")
                
                # Delay to prevent rate limiting
                if idx % batch_size == 0:
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"⚠️ Error translating '{word}': {e}")
                translations.append("")
                definitions.append("")
                word_types.append("")
                examples_list.append("[]")
                pronunciations.append("")
        
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
