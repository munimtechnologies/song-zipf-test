#!/bin/sh
# Setup for song-zipf-xpop-v2 (python:3.12). MV2, Munim, Inc.; made with AI agents. Apache-2.0.
# Fetches the registered code unchanged from the public repository at fixed commits:
#   zipfseg.py at 742fd83 (the pipeline), finch_xpop.py and test_finch_xpop.py at 06460e4
#   (the code registered with XPOP-PREREG.md). xpop_v2.py (XPOP-AMENDMENT-1.md) only wraps them.
set -e
python - <<'EOF'
import hashlib
import urllib.request
R = "https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/"
PINS = (("742fd83cb0386f6ce4868a35db46a5fd657393a0", "zipfseg.py"),
        ("06460e40a0c7b2c8470c5a6a276491d7e12bf247", "finch_xpop.py"),
        ("06460e40a0c7b2c8470c5a6a276491d7e12bf247", "test_finch_xpop.py"))
for sha, f in PINS:
    with urllib.request.urlopen(R + sha + "/" + f, timeout=120) as r:
        data = r.read()
    open(f, "wb").write(data)
    print("fetched", f, "@", sha[:7], len(data), "bytes", hashlib.sha256(data).hexdigest())
EOF
