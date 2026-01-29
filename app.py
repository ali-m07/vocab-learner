#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web Application for Vocabulary Learning
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import pandas as pd
from pathlib import Path
import json
import os
from datetime import datetime
from vocab_learner import VocabularyLearner
from daily_review import DailyReview

app = Flask(__name__)
CORS(app)

# Settings
DATA_DIR = Path("data")
UPLOADS_DIR = Path("uploads")
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

VOCAB_FILE = DATA_DIR / "vocab_translated.csv"

# Supported languages for translation
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'fa': 'Persian',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'tr': 'Turkish',
    'hi': 'Hindi',
    'nl': 'Dutch',
    'pl': 'Polish',
    'sv': 'Swedish',
    'no': 'Norwegian',
    'da': 'Danish',
    'fi': 'Finnish',
    'cs': 'Czech',
    'ro': 'Romanian',
    'hu': 'Hungarian',
    'el': 'Greek',
    'he': 'Hebrew',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'uk': 'Ukrainian',
    'bg': 'Bulgarian',
    'hr': 'Croatian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'et': 'Estonian',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
}

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/api/languages')
def get_languages():
    """Get supported languages"""
    return jsonify({
        "languages": SUPPORTED_LANGUAGES,
        "default": "en"
    })

@app.route('/api/stats')
def stats():
    """Get overall statistics"""
    stats_data = {
        "total_words": 0,
        "translated_words": 0,
        "vocab_file_exists": VOCAB_FILE.exists()
    }
    
    if VOCAB_FILE.exists():
        try:
            df = pd.read_csv(VOCAB_FILE, encoding='utf-8-sig')
            stats_data["total_words"] = len(df)
            stats_data["translated_words"] = len(df[df['translation'].notna() & (df['translation'] != '')]) if 'translation' in df.columns else 0
        except:
            pass
    
    return jsonify(stats_data)

@app.route('/api/words')
def get_words():
    """Get words with pagination and search"""
    if not VOCAB_FILE.exists():
        return jsonify({
            "words": [],
            "total": 0,
            "page": 1,
            "per_page": 50,
            "total_pages": 0,
            "error": "Vocabulary file not found. Please click 'Download & Translate Dataset' to get started."
        }), 200
    
    try:
        df = pd.read_csv(VOCAB_FILE, encoding='utf-8-sig')
        
        # Search
        search = request.args.get('search', '').strip().lower()
        if search:
            mask = df['word'].str.lower().str.contains(search, na=False)
            if 'translation' in df.columns:
                mask = mask | df['translation'].str.contains(search, na=False)
            if 'definition' in df.columns:
                mask = mask | df['definition'].str.contains(search, na=False)
            df = df[mask]
        
        # Filter by word type
        word_type = request.args.get('type', '').strip()
        if word_type and 'word_type' in df.columns:
            df = df[df['word_type'].str.lower() == word_type.lower()]
        
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        total = len(df)
        start = (page - 1) * per_page
        end = start + per_page
        
        words = df.iloc[start:end].to_dict('records')
        
        # Parse examples JSON if exists
        for word in words:
            if 'examples' in word and word['examples']:
                try:
                    word['examples'] = json.loads(word['examples']) if isinstance(word['examples'], str) else word['examples']
                except:
                    word['examples'] = []
        
        return jsonify({
            "words": words,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/word/<word>')
def get_word_details(word):
    """Get detailed information about a specific word"""
    if not VOCAB_FILE.exists():
        return jsonify({"error": "Vocabulary file not found"}), 404
    
    try:
        df = pd.read_csv(VOCAB_FILE, encoding='utf-8-sig')
        word_df = df[df['word'].str.lower() == word.lower()]
        
        if word_df.empty:
            return jsonify({"error": "Word not found"}), 404
        
        word_data = word_df.iloc[0].to_dict()
        
        # Parse examples JSON
        if 'examples' in word_data and word_data['examples']:
            try:
                word_data['examples'] = json.loads(word_data['examples']) if isinstance(word_data['examples'], str) else word_data['examples']
            except:
                word_data['examples'] = []
        
        return jsonify(word_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/daily', methods=['GET'])
def get_daily_words():
    """Get daily words"""
    words_per_day = int(request.args.get('count', 50))
    
    try:
        review = DailyReview(str(VOCAB_FILE), words_per_day=words_per_day)
        if not review.load_vocab():
            return jsonify({"error": "Vocabulary file not found"}), 404
        
        words = review.get_daily_words()
        if words is None:
            return jsonify({"error": "Error loading words"}), 500
        
        words_dict = words.to_dict('records')
        
        # Parse examples JSON
        for word in words_dict:
            if 'examples' in word and word['examples']:
                try:
                    word['examples'] = json.loads(word['examples']) if isinstance(word['examples'], str) else word['examples']
                except:
                    word['examples'] = []
        
        return jsonify({
            "words": words_dict,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "count": len(words)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_dataset():
    """Download and translate dataset"""
    try:
        data = request.json or {}
        target_language = data.get('target_language', 'fa')
        include_details = data.get('include_details', True)
        
        if target_language not in SUPPORTED_LANGUAGES:
            return jsonify({"success": False, "error": f"Language '{target_language}' not supported"}), 400
        
        learner = VocabularyLearner(target_language=target_language)
        learner.download_dataset()
        learner.load_words()
        
        # Translate with better error handling
        try:
            learner.translate_words(include_details=include_details)
        except Exception as e:
            error_msg = str(e).lower()
            if 'rate limit' in error_msg or '429' in error_msg or 'quota' in error_msg:
                return jsonify({
                    "success": False,
                    "error": "Translation service rate limit exceeded. Please wait a few minutes and try again, or translate fewer words at once."
                }), 429
            elif 'service unavailable' in error_msg or '503' in error_msg or '502' in error_msg:
                return jsonify({
                    "success": False,
                    "error": "Translation service is temporarily unavailable. Please try again in a few minutes."
                }), 503
            else:
                # Save partial results if any translations succeeded
                translated_count = sum(1 for t in learner.words_df.get('translation', []) if t and t.strip())
                if translated_count > 0:
                    learner.save_csv(str(VOCAB_FILE))
                    return jsonify({
                        "success": False,
                        "error": f"Translation partially completed. {translated_count} words translated. Error: {str(e)}",
                        "partial_success": True,
                        "translated_count": translated_count
                    }), 206
                else:
                    return jsonify({
                        "success": False,
                        "error": f"Translation failed: {str(e)}"
                    }), 500
        
        learner.save_csv(str(VOCAB_FILE))
        
        # Count successful translations
        translated_count = sum(1 for t in learner.words_df.get('translation', []) if t and t.strip())
        
        return jsonify({
            "success": True,
            "message": f"✅ {len(learner.words_df)} words downloaded. {translated_count} words translated to {SUPPORTED_LANGUAGES[target_language]}",
            "total_words": len(learner.words_df),
            "translated_count": translated_count,
            "target_language": target_language
        })
    except Exception as e:
        error_msg = str(e).lower()
        if 'rate limit' in error_msg or '429' in error_msg:
            return jsonify({
                "success": False,
                "error": "Translation service rate limit exceeded. Please wait a few minutes and try again."
            }), 429
        elif 'service unavailable' in error_msg or '503' in error_msg:
            return jsonify({
                "success": False,
                "error": "Translation service is temporarily unavailable. Please try again later."
            }), 503
        else:
            return jsonify({"success": False, "error": f"Error: {str(e)}"}), 500

@app.route('/api/create-anki', methods=['POST'])
def create_anki():
    """Create Anki deck"""
    try:
        if not VOCAB_FILE.exists():
            return jsonify({"error": "Please download the dataset first"}), 400
        
        data = request.json or {}
        deck_name = data.get('deck_name', 'English Vocabulary 10000')
        output_file = UPLOADS_DIR / f"vocab_deck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.apkg"
        
        learner = VocabularyLearner()
        learner.words_df = pd.read_csv(VOCAB_FILE, encoding='utf-8-sig')
        learner.create_anki_deck(deck_name, str(output_file))
        
        return jsonify({
            "success": True,
            "message": "Anki deck created successfully",
            "filename": output_file.name
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/download-anki/<filename>')
def download_anki_file(filename):
    """Download Anki file"""
    file_path = UPLOADS_DIR / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
