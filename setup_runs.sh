#!/bin/sh
# Setup for song-zipf-runs-v1 (python:3.12). MV2, Munim, Inc.; made with AI agents. Apache-2.0.
# The already-published pipeline modules are fetched unchanged at fixed commits:
# zipfseg.py at 742fd83 (SHA-256 checked; TP segmentation, Zipf R^2, markov_recording,
# heldout_ll), cds_job.py at 83de8fd (Brent-Ratner reader, blocks, to_recording),
# whale_run.py at c9f3d12 (Data S2 reader and Gate A of the whale test).
set -e
python - <<'EOF'
import hashlib
import sys
import urllib.request
REPO = "https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/"
FILES = (("742fd83cb0386f6ce4868a35db46a5fd657393a0", "zipfseg.py",
          "25002193229e6d6568939856de5a1760a41c3b462582ea06b6d75ba6d84bddf5"),
         ("83de8fd878681abd14f5e89c64db3c1dec4ce7c1", "cds_job.py", None),
         ("c9f3d129efb33cf31de390ba1217c373be2676cc", "whale_run.py", None))
for sha, f, want in FILES:
    with urllib.request.urlopen(REPO + sha + "/" + f, timeout=120) as r:
        data = r.read()
    got = hashlib.sha256(data).hexdigest()
    print("fetched", f, "at", sha[:7], len(data), "bytes", got)
    if want and got != want:
        sys.exit("SHA-256 mismatch for " + f)
    open(f, "wb").write(data)
EOF
python -c "import zipfseg, cds_job, whale_run; print('imports ok')"
ls -la /data/song/whale /data/cds 2>/dev/null || true
