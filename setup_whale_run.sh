#!/bin/sh
# setup.sh for whale-test-v1 (PREREG-AMENDMENT-5): fetch the unchanged, already-published
# analysis modules at pinned commits. MV2, Munim, Inc. Made with AI agents. Apache-2.0.
set -e
BASE=https://raw.githubusercontent.com/munimtechnologies/song-zipf-test
python -c "import urllib.request as u; u.urlretrieve('$BASE/742fd83/whale_test.py', 'whale_test.py'); u.urlretrieve('$BASE/742fd83/whale_read.py', 'whale_read.py'); u.urlretrieve('$BASE/e976e63af0cf0792a304c6dbc75fcd2745416367/zipfseg.py', 'zipfseg.py')"
python -c "import hashlib; [print(f, hashlib.sha256(open(f,'rb').read()).hexdigest()) for f in ('whale_test.py','whale_read.py','zipfseg.py','whale_run.py')]"
python -c "import whale_test, zipfseg; print('ok', whale_test.VERSION)"
ls -la /data/song/whale || true
