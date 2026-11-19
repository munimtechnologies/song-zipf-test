# SPDX-License-Identifier: Apache-2.0
# xpop_v2.py: runs the registered finch_xpop.py (commit 06460e4, fetched unchanged) as job
# song-zipf-xpop-v2, with the one reading change in XPOP-AMENDMENT-1.md: annotation members
# whose file name starts with "._" (macOS AppleDouble metadata that tar archives made on a Mac
# carry next to every real file) are not annotation files and are skipped, and counted, before
# Gate N is computed. Nothing else changes: same data, rules, nulls, seeds, gates, predictions.
# The job also waits until XPOP-AMENDMENT-1.md is public before anything is downloaded.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import hashlib
import os
import sys
import time

import finch_xpop as X

JOB = "song-zipf-xpop-v2"
AMEND_URL = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/main/"
             "XPOP-AMENDMENT-1.md")
AMEND_TAG = b"XPOP-AMENDMENT-1"
STATE = {"amendment": None}

_orig_bird = X.nicholson_bird
_orig_wait = X.wait_for_registration
_orig_dump = X.dump


def is_appledouble(name):
    return os.path.basename(name.replace("\\", "/")).startswith("._")


def nicholson_bird(bird, days, load_day, cap=X.CAP_N):
    """finch_xpop.nicholson_bird, with "._*" members removed from every day it reads."""
    skipped = []

    def load(b, d):
        csvs = load_day(b, d)
        keep = {}
        for name in csvs:
            if is_appledouble(name):
                skipped.append(name)
            else:
                keep[name] = csvs[name]
        return keep
    bouts, info = _orig_bird(bird, days, load, cap)
    info["appledouble_skipped"] = len(skipped)
    return bouts, info


def wait_for_amendment(max_minutes, fetcher=None):
    fetcher = fetcher or X.fetch
    t0 = time.time()
    tries = 0
    last = None
    while True:
        tries += 1
        try:
            blob = fetcher(AMEND_URL, timeout=60)
            if AMEND_TAG in blob:
                return {"found": True, "tries": tries, "url": AMEND_URL,
                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "sha256": hashlib.sha256(blob).hexdigest()}
        except Exception as e:                      # 404 until published
            last = repr(e)[:200]
        if time.time() - t0 > max_minutes * 60:
            return {"found": False, "tries": tries, "url": AMEND_URL, "last_error": last}
        time.sleep(60)


def wait_for_registration(max_minutes):
    """Amendment first, then the original XPOP-PREREG.md check (its result is what
    finch_xpop records as "registration", so the published grader's sha256 check holds)."""
    STATE["amendment"] = wait_for_amendment(max_minutes)
    if not STATE["amendment"]["found"]:
        return {"found": False, "tries": 0, "last_error": "XPOP-AMENDMENT-1.md not public"}
    return _orig_wait(max_minutes)


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def dump(obj, path):
    obj["job"] = JOB
    obj["amendment"] = {"file": "XPOP-AMENDMENT-1.md", "registration": STATE["amendment"],
                        "finch_xpop_sha256": _sha(X.__file__),
                        "xpop_v2_sha256": _sha(__file__)}
    _orig_dump(obj, path)


X.nicholson_bird = nicholson_bird
X.wait_for_registration = wait_for_registration
X.dump = dump

if __name__ == "__main__":
    sys.exit(X.main())
