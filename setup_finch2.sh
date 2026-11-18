#!/bin/sh
# Setup for song-zipf-finch-v2 (python:3.12, Debian). MV2, Munim, Inc.; made with AI agents. Apache-2.0.
# The unchanged registered code (zipfseg.py, finch_parse.py, job_analyze.py and its test) is
# fetched from the public repository at a fixed commit, so the analysis is byte-identical to
# what was published before this job was filed.
set -e
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends tesseract-ocr tesseract-ocr-eng >/dev/null
tesseract --version
pip install --no-cache-dir "pymupdf>=1.24,<1.27"
python - <<'EOF'
import urllib.request
BASE = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/"
        "742fd83cb0386f6ce4868a35db46a5fd657393a0/")
for f in ("zipfseg.py", "finch_parse.py", "job_analyze.py", "test_finch_parse.py"):
    with urllib.request.urlopen(BASE + f, timeout=120) as r:
        data = r.read()
    open(f, "wb").write(data)
    print("fetched", f, len(data), "bytes")
EOF
