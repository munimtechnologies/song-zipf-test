# SPDX-License-Identifier: Apache-2.0
# Tests for job song-zipf-xpop-v2 (XPOP-AMENDMENT-1.md). Reuses every test of the registered
# test_finch_xpop.py (commit 06460e4) unchanged except test_run_task_and_assemble, whose toy
# data were degenerate (see below), and adds tests for the wrapper xpop_v2.py.
# Stdlib only. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import json
import os
import shutil
import tempfile
import time
import unittest

import finch_xpop as X
import test_finch_xpop as T
import xpop_v2 as V


class TestKoumura(T.TestKoumura):
    pass


class TestNicholson(T.TestNicholson):
    pass


class TestAnalysis(T.TestAnalysis):
    def test_run_task_and_assemble(self):
        # In xpop-v1 the N block used uniform random 5-letter toy song (seed 8) at theta 0.3.
        # With no syllable rules there are almost no TP cuts, every chunk is a whole unique bout,
        # every inventory is all singletons, every R^2 (real and null) is nan, and the pinned
        # zipfseg.compare divides by zero on an empty list. run_task recorded that as an error,
        # exactly as designed; the test wrongly expected a result. Now: N gets the toy data of K
        # (theta 0.5 runs there, as K_0.5 shows), and the degenerate set ND must be recorded as
        # an error in not_run, never raised and never hidden.
        recs = {"K": T.rand_recs(7), "N": T.rand_recs(7), "ND": T.rand_recs(8), "KS": [],
                "NS": T.rand_recs(9, n_rec=1)}
        blocks = [("K_0.5", "K", 0.5, 3, X.FULL_NULLS, False),
                  ("K_heldout", "K", None, 0, None, False),
                  ("KS_0.5", "KS", 0.5, 3, X.SMALL_NULLS, False),
                  ("N_0.5", "N", 0.5, 3, X.FULL_NULLS, True),
                  ("ND_0.3", "ND", 0.3, 3, X.FULL_NULLS, True)]
        d = tempfile.mkdtemp()
        try:
            out = X.run_task((blocks, recs, d, time.time(), 3600))
            out2 = X.run_task(([("N_0.7", "N", 0.7, 3, X.FULL_NULLS, True)], recs, d,
                               time.time() - 3000, 3600))           # over 55% of budget
            res = X.assemble([out, out2])
            want = sorted(X.FULL_NULLS + ("rotate",))
            self.assertEqual(sorted(res["K"]["by_theta"]["0.5"]["nulls"]), want)
            self.assertEqual(res["K"]["heldout"]["n_recordings"], 2)
            self.assertIn("KS_0.5", res["KS"]["not_run"])
            self.assertEqual(sorted(res["N"]["by_theta"]["0.5"]["nulls"]), want)
            self.assertEqual(res["N"]["by_theta"]["0.5"]["n_types_total"],
                             res["K"]["by_theta"]["0.5"]["n_types_total"])
            self.assertIn("N_0.7", res["N"]["not_run"])
            self.assertIn("error", res["ND"]["not_run"]["ND_0.3"])
            self.assertNotIn("by_theta", res["ND"])
            with open(os.path.join(d, "blocks", "ND_0.3.json")) as f:
                self.assertIn("error", json.load(f))
        finally:
            shutil.rmtree(d)


class TestAmendment(unittest.TestCase):
    def test_patched(self):
        self.assertIs(X.nicholson_bird, V.nicholson_bird)
        self.assertIs(X.wait_for_registration, V.wait_for_registration)
        self.assertIs(X.dump, V.dump)

    def test_is_appledouble(self):
        self.assertTrue(V.is_appledouble("bird/day/._a.wav.csv"))
        self.assertTrue(V.is_appledouble("._a.wav.csv"))
        self.assertFalse(V.is_appledouble("bird/a._b.wav.csv"))
        self.assertFalse(V.is_appledouble("bird/._dir/a.wav.csv"))

    def test_appledouble_skipped_before_gate(self):
        days = {"d1": {"bird/a.wav.csv": "0.0,0.1,x\n0.2,0.3,y\n",       # gap .1: one bout
                       "bird/._a.wav.csv": "\x00\x05\x16\x07Mac OS X metadata",
                       "._b.wav.csv": "junk"}}
        bouts, info = X.nicholson_bird("b", ["d1"], lambda b, d: days[d], cap=100)
        self.assertEqual(bouts, [["x", "y"]])
        self.assertEqual(info["appledouble_skipped"], 2)
        self.assertEqual((info["files"], info["bad_files"], info["unreadable_files"]), (1, 0, 0))
        # without the amendment the junk member counts against Gate N
        bouts0, info0 = V._orig_bird("b", ["d1"], lambda b, d: days[d], cap=100)
        self.assertEqual(bouts0, [["x", "y"]])
        self.assertGreaterEqual(info0["unreadable_files"], 1)

    def test_wait_for_amendment(self):
        calls = []

        def ok(url, timeout=60):
            calls.append(url)
            return b"# XPOP-AMENDMENT-1: ..."
        r = V.wait_for_amendment(-1, fetcher=ok)
        self.assertTrue(r["found"])
        self.assertEqual(calls, [V.AMEND_URL])

        def missing(url, timeout=60):
            raise OSError("HTTP Error 404")
        r = V.wait_for_amendment(-1, fetcher=missing)
        self.assertFalse(r["found"])
        self.assertIn("404", r["last_error"])

    def test_dump_adds_provenance(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "x.json")
            X.dump({"version": X.VERSION}, p)
            with open(p, encoding="utf-8") as f:
                got = json.load(f)
            self.assertEqual(got["version"], "xpop-1")
            self.assertEqual(got["job"], "song-zipf-xpop-v2")
            self.assertEqual(got["amendment"]["file"], "XPOP-AMENDMENT-1.md")
            self.assertEqual(len(got["amendment"]["finch_xpop_sha256"]), 64)
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
