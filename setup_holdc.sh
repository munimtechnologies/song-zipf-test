#!/bin/sh
# Setup for song-zipf-holdc-v1 (python:3.12). MV2, Munim, Inc.; made with AI agents. Apache-2.0.
# Every already-published module is fetched unchanged and checked by SHA-256 before use:
# zipfseg.py at 742fd83, cds_job.py at 83de8fd, whale_run.py at c9f3d12 (as for HOLD and
# RUNS), hold.py at 4e73d8a (the code that produced RESULTS-HOLD.md) and runs.py at bdd0203
# (the code that produced RESULTS-RUNS.md). If a pinned commit cannot be fetched, main is
# tried; either way the file must have the SHA-256 the earlier jobs recorded.
set -e
python - <<'EOF'
import hashlib
import sys
import urllib.request
REPO = "https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/"
FILES = (("742fd83cb0386f6ce4868a35db46a5fd657393a0", "zipfseg.py",
          "25002193229e6d6568939856de5a1760a41c3b462582ea06b6d75ba6d84bddf5"),
         ("83de8fd878681abd14f5e89c64db3c1dec4ce7c1", "cds_job.py",
          "a1564f8d48145642bd4dbf09488fd7e086f152e1a0fe4e15dc9775f0ba00c55d"),
         ("c9f3d129efb33cf31de390ba1217c373be2676cc", "whale_run.py",
          "b1e128e0eb5f6a211335aa1f402124e94517f751450adf574dd4e742e46211a0"),
         ("4e73d8a53809c4ce8058f756c52f923252d6fc89", "hold.py",
          "6ac8be4474968be23da2b42c76de2427dfe9d0177d32026b329ada0d63e02e4c"),
         ("bdd02037a5d32fd60aab05d0d0185f788b7fc7ca", "runs.py",
          "82d4fbfce43dd24addfb9bd00eb827f650ca9af502785b6e3d119db73f618052"))
for sha, f, want in FILES:
    got = None
    for ref in (sha, "main"):
        try:
            with urllib.request.urlopen(REPO + ref + "/" + f, timeout=120) as r:
                data = r.read()
        except Exception as e:
            print("fetch failed", f, "at", ref[:7], repr(e)[:120])
            continue
        got = hashlib.sha256(data).hexdigest()
        print("fetched", f, "at", ref[:7], len(data), "bytes", got)
        if got == want:
            open(f, "wb").write(data)
            break
    else:
        sys.exit("no copy of %s with SHA-256 %s" % (f, want))
EOF
python -c "import zipfseg, cds_job, whale_run, hold, runs; print('imports ok')"
ls -la /data/song/whale /data/cds 2>/dev/null || true
