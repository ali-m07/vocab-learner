#!/usr/bin/env python3
"""
Generate a static word list for GitHub Pages (no backend required).

This uses `wordfreq` to create a top-N English word list and writes it to:
  frontend/static/data/words.json
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    try:
        from wordfreq import top_n_list
    except Exception as e:  # pragma: no cover
        raise SystemExit(
            "wordfreq is required. Install with: pip install wordfreq"
        ) from e

    repo_root = Path(__file__).parent
    out_path = repo_root / "frontend" / "static" / "data" / "words.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    words = top_n_list("en", 20000)
    # Ensure plain strings only
    words = [w for w in words if isinstance(w, str) and w.strip()]

    out_path.write_text(json.dumps({"words": words}, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Wrote {len(words)} words to {out_path}")


if __name__ == "__main__":
    main()

