#!/bin/bash
# Clean up old vocabulary CSV files to force regeneration from GitHub sources

echo "🧹 Cleaning up old vocabulary data..."

# Remove old CSV files
rm -f data/vocab_translated.csv
rm -f vocab_translated.csv

# Keep data directory structure
mkdir -p data
touch data/.gitkeep

echo "✅ Old vocabulary files removed"
echo "📝 Next time you click 'Download & Translate Dataset', it will use GitHub word list"
