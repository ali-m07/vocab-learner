# Vocabulary Learner 🚀

A modern, beautiful vocabulary learning application for mastering English words with support for multiple target languages.

## Features

- ✅ Automatic download of 10,000 English words dataset from Kaggle
- ✅ Multi-language translation support (40+ languages)
- ✅ Detailed word information: definitions, word types, examples, pronunciation
- ✅ Beautiful modern web UI with TypeScript
- ✅ Create Anki decks for spaced repetition
- ✅ Daily review system
- ✅ Search and filter functionality
- ✅ Docker and Kubernetes (Helm) support

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+ (for TypeScript compilation)
- Docker (optional)
- Kubernetes + Helm (optional)

### Method 1: Direct Python Usage

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies and build TypeScript
npm install
npm run build

# Run the application
python app.py
```

Then open `http://localhost:5000` in your browser.

### Method 2: Docker

```bash
# Build image
docker build -t vocab-learner .

# Run container
docker run -d -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/uploads:/app/uploads \
  vocab-learner
```

### Method 3: Docker Compose

```bash
docker-compose up -d
```

### Method 4: Kubernetes (Helm)

```bash
# Install
helm install vocab-learner ./helm/vocab-learner

# Upgrade
helm upgrade vocab-learner ./helm/vocab-learner

# Uninstall
helm uninstall vocab-learner
```

## Usage

### Web UI

1. Open your browser and go to `http://localhost:5000`
2. Select your target language from the dropdown
3. Click "Download & Translate Dataset" to download and translate words
4. Wait for the process to complete (may take several minutes)
5. Use the features:
   - **Search**: Search words in the vocabulary
   - **Filter**: Filter by word type (noun, verb, adjective, etc.)
   - **Flip Cards**: Click on word cards to see translations and details
   - **Daily Review**: Get a random set of words for daily practice
   - **Create Anki Deck**: Generate Anki deck for import

### CLI Usage

#### Download and Translate

```bash
python vocab_learner.py
```

#### Daily Review

```bash
# Show 50 words (default) without translation (for practice)
python daily_review.py

# Show with translation
python daily_review.py --show-translation

# Custom number of words (e.g., 200 words)
python daily_review.py --words=200
```

## Supported Languages

The application supports translation to 40+ languages including:

- Persian (fa)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)
- Arabic (ar)
- Turkish (tr)
- Hindi (hi)
- And many more...

## Word Information

Each word includes:

- **Translation**: Word translated to your target language
- **Definition**: English definition of the word
- **Word Type**: Part of speech (noun, verb, adjective, etc.)
- **Examples**: Example sentences showing usage
- **Pronunciation**: Phonetic pronunciation guide

## API Endpoints

- `GET /` - Main UI page
- `GET /health` - Health check
- `GET /api/languages` - Get supported languages
- `GET /api/stats` - Get overall statistics
- `GET /api/words?page=1&per_page=50&search=word&type=noun` - Get words with pagination and filters
- `GET /api/word/<word>` - Get detailed information about a specific word
- `GET /api/daily?count=50` - Get daily review words
- `POST /api/download` - Download and translate dataset
  ```json
  {
    "target_language": "fa",
    "include_details": true
  }
  ```
- `POST /api/create-anki` - Create Anki deck
- `GET /api/download-anki/<filename>` - Download Anki file

## Project Structure

```
.
├── app.py                 # Flask web application
├── vocab_learner.py       # Core vocabulary learning logic
├── daily_review.py        # Daily review script
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── package.json           # Node.js dependencies
├── tsconfig.json          # TypeScript configuration
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   └── index.html
├── static/               # Static files
│   ├── ts/               # TypeScript source
│   │   └── app.ts
│   ├── js/               # Compiled JavaScript
│   │   └── app.js
│   └── css/
│       └── style.css
└── helm/                  # Helm chart
    └── vocab-learner/
```

## Development

### TypeScript Development

```bash
# Watch mode for development
npm run watch

# Build once
npm run build
```

### Making Changes

1. Edit TypeScript files in `static/ts/`
2. Run `npm run build` to compile
3. Refresh browser to see changes

## Output Files

- `data/vocab_translated.csv`: Words with translations and details
- `uploads/vocab_deck_*.apkg`: Anki deck files for import

## Using Anki

1. Open Anki
2. File > Import
3. Select the `vocab_deck.apkg` file
4. Click Import

The Anki deck includes:
- English word (front)
- Translation, definition, type, examples, pronunciation (back)

## Configuration

### Helm Configuration

Edit `helm/vocab-learner/values.yaml` to configure:

- Replica count
- Resources (CPU/Memory)
- Persistent storage
- Ingress settings
- Auto-scaling

## Notes

- Translation may take several minutes (10,000 words)
- For better learning, focus on 20-50 words per day deeply
- Anki manages spaced repetition automatically
- **No API key required** - Uses free Google Translate directly via `googletrans` library
- Word details are fetched from Free Dictionary API
- Translation includes automatic retry mechanism and rate limit handling
- Small delays between requests to respect Google Translate's free tier limits

## Requirements

- Python 3.11+
- Node.js 18+
- Docker (optional)
- Kubernetes + Helm (optional)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
