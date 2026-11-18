#!/bin/sh
# Setup for song-zipf-cds-v1 (python:3.12). MV2, Munim, Inc.; made with AI agents. Apache-2.0.
# The unchanged registered pipeline (zipfseg.py) is fetched from the public repository at a
# fixed commit, so the analysis is byte-identical to what was published before.
set -e
python - <<'EOF'
import hashlib
import urllib.request
BASE = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/"
        "742fd83cb0386f6ce4868a35db46a5fd657393a0/")
for f in ("zipfseg.py",):
    with urllib.request.urlopen(BASE + f, timeout=120) as r:
        data = r.read()
    open(f, "wb").write(data)
    print("fetched", f, len(data), "bytes", hashlib.sha256(data).hexdigest())
EOF
