#!/bin/sh
# Setup for song-zipf-canary-v2 (python:3.12). MV2, Munim, Inc.; made with AI agents. Apache-2.0.
# Both analysis modules are fetched from the public repository at fixed commits, so the code that
# runs is byte-identical to what was published before any canary data were read:
#   zipfseg.py at 742fd83 (unchanged registered pipeline)
#   canary.py  at 86bf93b (published 2026-11-18 20:23 UTC with CANARY-PREREG.md)
# Only test_canary.py comes from this job's folder (one test fixed; see CANARY-AMENDMENT-1.md).
set -e
python - <<'EOF'
import hashlib
import urllib.request
REPO = "https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/"
PINS = (("742fd83cb0386f6ce4868a35db46a5fd657393a0", "zipfseg.py"),
        ("86bf93b7b656fc245da9d3bb40780f06f54d08de", "canary.py"))
for sha, f in PINS:
    with urllib.request.urlopen(REPO + sha + "/" + f, timeout=120) as r:
        data = r.read()
    open(f, "wb").write(data)
    print("fetched", f, "at", sha[:7], len(data), "bytes", hashlib.sha256(data).hexdigest())
EOF
