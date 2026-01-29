#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Vocabulary Review Script
Display a set number of words for daily learning
"""

import pandas as pd
import random
from pathlib import Path
from datetime import datetime

class DailyReview:
    def __init__(self, vocab_file: str = "vocab_translated.csv", words_per_day: int = 50):
        self.vocab_file = vocab_file
        self.words_per_day = words_per_day
        self.df = None
        
    def load_vocab(self):
        """Load vocabulary file"""
        if not Path(self.vocab_file).exists():
            print(f"❌ File {self.vocab_file} not found!")
            print("💡 Run vocab_learner.py first")
            return False
        
        try:
            self.df = pd.read_csv(self.vocab_file, encoding='utf-8-sig')
            print(f"✅ Loaded {len(self.df)} words")
            return True
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False
    
    def get_daily_words(self, shuffle: bool = True):
        """Get daily words"""
        if self.df is None:
            if not self.load_vocab():
                return None
        
        # Select words
        words = self.df.sample(n=min(self.words_per_day, len(self.df)), 
                              replace=False) if shuffle else self.df.head(self.words_per_day)
        
        return words
    
    def show_words(self, show_translation: bool = False):
        """Display words (for practice)"""
        words = self.get_daily_words()
        
        if words is None:
            return
        
        print("\n" + "=" * 60)
        print(f"📚 Today's Words ({datetime.now().strftime('%Y-%m-%d')})")
        print(f"📊 Count: {len(words)} words")
        print("=" * 60 + "\n")
        
        for idx, (_, row) in enumerate(words.iterrows(), 1):
            word = str(row['word']).strip()
            translation = str(row.get('translation', '')).strip() if 'translation' in row else ""
            definition = str(row.get('definition', '')).strip() if 'definition' in row else ""
            word_type = str(row.get('word_type', '')).strip() if 'word_type' in row else ""
            
            print(f"{idx:3d}. {word:20s}", end="")
            
            if show_translation:
                if translation:
                    print(f" → {translation}")
                if definition:
                    print(f"    Definition: {definition}")
                if word_type:
                    print(f"    Type: {word_type}")
            else:
                print()  # Show only word (for practice)
        
        print("\n" + "=" * 60)
        print("💡 Run with --show-translation to see translations")
        print("=" * 60)
    
    def save_daily_list(self, output_file: str = None):
        """Save today's word list"""
        words = self.get_daily_words()
        
        if words is None:
            return
        
        if output_file is None:
            date_str = datetime.now().strftime('%Y%m%d')
            output_file = f"daily_words_{date_str}.csv"
        
        words.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✅ Today's word list saved: {output_file}")


def main():
    import sys
    
    # Check arguments
    show_translation = '--show-translation' in sys.argv or '-t' in sys.argv
    
    # Daily word count (default 50)
    words_per_day = 50
    for arg in sys.argv:
        if arg.startswith('--words='):
            try:
                words_per_day = int(arg.split('=')[1])
            except:
                pass
    
    print("=" * 60)
    print("📖 Daily Vocabulary Review")
    print("=" * 60)
    
    review = DailyReview(words_per_day=words_per_day)
    review.show_words(show_translation=show_translation)
    
    # Save list
    review.save_daily_list()


if __name__ == "__main__":
    main()
