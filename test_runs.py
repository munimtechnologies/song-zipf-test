# SPDX-License-Identifier: Apache-2.0
# Tests for runs.py (RUNS-PREREG.md). Standard library only; no data, no network.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import random
import unittest
from collections import Counter

import runs as R


class TestCollapse(unittest.TestCase):
    def test_by_hand(self):
        self.assertEqual(R.collapse(list("aaab")), ["a", "b"])
        self.assertEqual(R.collapse(list("ababc")), ["a", "b", "c"])
        self.assertEqual(R.collapse(list("abcabd")), list("abcabd"))
        self.assertEqual(R.collapse(list("abab" "ab")), ["a", "b"])
        self.assertEqual(R.collapse([]), [])

    def test_whale_like_cell(self):
        g, s = "gr(s)-dws(s)", "sq"
        self.assertEqual(R.collapse([g, s, s, s, g, s, s, s, g, s, s, s]), [g, s])

    def test_lmax(self):
        self.assertEqual(R.collapse(list("abcabc"), lmax=2), list("abcabc"))
        self.assertEqual(R.collapse(list("abcabc"), lmax=3), list("abc"))

    def test_square_free_and_idempotent(self):
        rng = random.Random(7)
        for _ in range(200):
            seq = [rng.choice("abc") for _ in range(rng.randint(0, 40))]
            out = R.collapse(seq, 4)
            self.assertFalse(R.has_square(out, 4))
            self.assertEqual(R.collapse(out, 4), out)
            self.assertLessEqual(len(out), len(seq))

    def test_has_square(self):
        self.assertTrue(R.has_square(list("xabab"), 2))
        self.assertFalse(R.has_square(list("xabcabc"), 2))
        self.assertTrue(R.has_square(list("xabcabc"), 3))

    def test_share_removed(self):
        # "aaab" -> "ab" (2 of 4 kept), "ab" kept: 4 of 6 kept
        self.assertAlmostEqual(R.share_removed([list("aaab"), list("ab")]), 2 / 6, places=12)
        self.assertEqual(R.share_removed([[]]), 0.0)


class TestNull(unittest.TestCase):
    def test_fit_chain(self):
        succ, starts, ws = R.fit_chain([list("abc"), list("abd")], 2)
        self.assertEqual(starts, [("a", "b"), ("a", "b")])
        self.assertEqual(dict(succ), {("a", "b"): ["c", "d"]})
        self.assertEqual(ws, [("a", "b"), ("a", "b")])

    def test_collapsed_markov_lengths_square_free_seeded(self):
        rng = random.Random(3)
        bouts = [R.collapse([rng.choice("abcd") for _ in range(rng.randint(1, 30))], 4)
                 for _ in range(10)]
        a = R.collapsed_markov(bouts, 2, random.Random(9), lmax=4)
        b = R.collapsed_markov(bouts, 2, random.Random(9), lmax=4)
        self.assertEqual(a, b)
        self.assertEqual(len(a), len(bouts))
        for x, y in zip(a, bouts):
            self.assertLessEqual(len(x), len(y))
            self.assertFalse(R.has_square(x, 4))

    def test_short_bouts_copied_and_cap(self):
        out = R.collapsed_markov([["a"], list("abc")], 2, random.Random(1), cap=0)
        self.assertEqual(out[0], ["a"])
        self.assertEqual(out[1], ["a", "b"])        # start k-gram only: no draws allowed

    def test_deterministic_chain_reaches_length(self):
        out = R.collapsed_markov([list("abcd")], 1, random.Random(2))
        self.assertEqual(out, [list("abcd")])


class TestStats(unittest.TestCase):
    def test_pval_cmp(self):
        self.assertEqual(R.pval(1.0, [0.0, 1.0, 2.0]), 0.75)
        self.assertEqual(R.pval(float("nan"), [0.0]), 1.0)
        c = R.cmp(2.0, [1.0, 3.0, float("nan")])
        self.assertEqual(c["n_null"], 2)
        self.assertEqual(c["null_mean"], 2.0)
        self.assertEqual(c["null_sd"], 1.0)
        self.assertEqual(c["z"], 0.0)
        self.assertAlmostEqual(c["p"], 2 / 3, places=12)
        self.assertEqual(R.cmp(1.0, [])["p"], 1.0)

    def test_motif(self):
        self.assertTrue(R.motif(("a", "a")))
        self.assertTrue(R.motif(("a", "b", "a")))
        self.assertTrue(R.motif(("a", "b", "c", "b")))
        self.assertFalse(R.motif(("a", "b", "c")))
        self.assertFalse(R.motif(("a",)))

    def test_top_chunks_and_count(self):
        inv = Counter({("b",): 3, ("a",): 3, ("c", "d"): 5, ("e",): 1})
        self.assertEqual(R.top_chunks(inv, 3), [("c", "d"), ("a",), ("b",)])
        inv2 = Counter({("x", "x"): 4, ("y", "z"): 2, ("y", "z", "y"): 1})
        self.assertEqual(R.motif_count([inv2, inv2], lambda rec: rec, top=2), 2)
        self.assertEqual(R.motif_count([inv2], lambda rec: rec, top=3), 2)

    def test_d1(self):
        vals = {("A", 1): -1.0, ("A", 2): -0.5, ("B", 1): -1.0, ("B", 2): -1.5}
        d = R.d1(["A", "B"], lambda rec, k: vals[(rec, k)])
        self.assertEqual(d["per_set"], [0.5, -0.5])
        self.assertEqual(d["n_favour_order2"], 1)
        self.assertFalse(d["majority"])


class TestTests(unittest.TestCase):
    def setUp(self):
        rng = random.Random(4)
        self.recs = [[R.collapse([rng.choice("abcde") for _ in range(25)]) for _ in range(4)]
                     for _ in range(2)]

    def test_t1_constant_statistic(self):
        out = R.t1(self.recs, 5, 1, lambda recs, th: 0.5, thetas=(0.3, 0.5))
        self.assertEqual(out["p_m1c"], 1.0)
        self.assertEqual(out["p_m2c"], 1.0)
        self.assertEqual(out["label"], "EXPLAINED_BY_FIRST_ORDER")
        self.assertEqual(len(out["nulls"]["m2c"]["by_theta"]), 2)
        self.assertLessEqual(out["nulls"]["m2c"]["length_ratio_mean"], 1.0)

    def test_t1_nan_statistic_never_beyond(self):
        out = R.t1(self.recs, 3, 1, lambda recs, th: float("nan"), thetas=(0.5,))
        self.assertEqual(out["p_m2c"], 1.0)
        self.assertNotEqual(out["label"], R.BSOC)

    def test_t1_label_from_length_statistic(self):
        # statistic = -(number of symbols): every null is at most as long as the real
        # set, so null >= real for all B and p = 1
        out = R.t1(self.recs, 4, 2,
                   lambda recs, th: -float(sum(len(b) for r in recs for b in r)),
                   thetas=(0.5,))
        self.assertEqual(out["p_m2c"], 1.0)

    def test_t2_identity_surrogate(self):
        recs = [[list("aab")], [list("abab"), list("c")]]
        out = R.t2(recs, 4, 1, lambda rec, rng: rec)
        self.assertAlmostEqual(out["per_set"][0], 1 / 3, places=12)
        self.assertAlmostEqual(out["per_set"][1], 2 / 5, places=12)
        self.assertAlmostEqual(out["real"], (1 / 3 + 2 / 5) / 2, places=12)
        self.assertEqual(out["p"], 1.0)
        self.assertEqual(out["label"], R.NB)

    def test_t3_surrogate_without_motifs(self):
        seg = lambda rec: Counter(tuple(b) for b in rec)
        recs = [[["x", "x"], ["x", "x"], ["y"]]]
        out = R.t3(recs, 3, 1, lambda rec, rng: [["p", "q"]], seg)
        self.assertEqual(out["real"], 1)
        self.assertEqual(out["n_top"], 2)
        self.assertEqual(out["null_mean"], 0.0)
        self.assertEqual(out["p"], 0.25)
        self.assertEqual(out["label"], R.NB)        # 0.25 >= 0.05: too few nulls
        self.assertEqual(out["top_chunks"], [["x x", "y"]])


def _set(t1_label, t2_label="NOT_BEYOND", t2_p=0.5, t2_real=0.1, t3_p=0.5, maj=False,
         r2=(0.8, 0.9, 0.95)):
    return {"t1": {"label": t1_label, "real_r2": list(r2)},
            "t2": {"label": t2_label, "p": t2_p, "real": t2_real},
            "t3": {"label": "x", "p": t3_p},
            "d1_collapsed": {"majority": maj}}


class TestGrade(unittest.TestCase):
    def _res(self, whale, e_labels, n_labels, e_t2=R.NB):
        return {"whale": whale,
                "english": [_set(l, t2_label=e_t2) for l in e_labels],
                "negative": [_set(l) for l in n_labels]}

    def test_all_true(self):
        w = _set(R.BSOC, R.REP, 0.004, 0.6, 0.01, True, (0.8, 0.9, 0.95))
        w["status"] = "ok"
        w["t3"]["label"] = R.MOT
        res = self._res(w, [R.BSOC] * 6, ["EXPLAINED_BY_SECOND_ORDER"] * 3)
        g = R.grade(res)
        self.assertTrue(all(g["predictions"][k] for k in R.PRIORS))
        self.assertEqual(g["rules"]["control"], "CONTROL_OK")
        self.assertEqual(g["rules"]["R3_zipf_after_collapse"], R.BSOC)
        self.assertEqual(g["rules"]["R1_repetition"], R.REP)
        self.assertEqual(g["rules"]["R2_top_chunk_motifs"], R.MOT)
        self.assertEqual(g["n_scored"], 9)
        # (0.1^2 + 0.4^2 + 0.5^2 + 0.5^2 + 0.7^2 + 0.25^2 + 0.2^2 + 0.65^2 + 0.3^2) / 9
        # = (0.01 + 0.16 + 0.25 + 0.25 + 0.49 + 0.0625 + 0.04 + 0.4225 + 0.09) / 9
        self.assertAlmostEqual(g["brier"], 1.775 / 9, places=12)

    def test_underpowered_and_powered(self):
        w = _set("EXPLAINED_BY_SECOND_ORDER", maj=False, r2=(0.8, 0.95, 0.9))
        w["status"] = "ok"
        res = self._res(w, [R.BSOC] * 4 + ["EXPLAINED_BY_SECOND_ORDER"] * 2,
                        [R.BSOC] + ["EXPLAINED_BY_FIRST_ORDER"] * 2)
        g = R.grade(res)
        self.assertEqual(g["rules"]["control"], "CONTROL_OK")
        self.assertEqual(g["rules"]["R3_zipf_after_collapse"],
                         "EXPLAINED_BY_SECOND_ORDER_UNDERPOWERED")
        self.assertFalse(g["predictions"]["P7"])
        self.assertFalse(g["predictions"]["P9"])    # 0.95 is not below 0.9303
        self.assertTrue(g["predictions"]["P2"])
        w["d1_collapsed"]["majority"] = True
        self.assertEqual(R.grade(res)["rules"]["R3_zipf_after_collapse"],
                         "EXPLAINED_BY_SECOND_ORDER_POWERED")

    def test_control_failed(self):
        w = _set(R.BSOC)
        w["status"] = "ok"
        res = self._res(w, [R.BSOC] * 3 + ["EXPLAINED_BY_SECOND_ORDER"] * 3,
                        ["EXPLAINED_BY_FIRST_ORDER"] * 3, e_t2=R.REP)
        g = R.grade(res)
        self.assertEqual(g["rules"]["control"], "CONTROL_FAILED")
        self.assertEqual(g["rules"]["R3_zipf_after_collapse"], "CONTROL_FAILED")
        self.assertFalse(g["predictions"]["P6"])
        self.assertFalse(g["predictions"]["P2"])

    def test_whale_missing_and_incomplete(self):
        res = self._res({"status": "missing"}, [R.BSOC] * 5, [])
        g = R.grade(res)
        self.assertEqual(g["rules"]["R3_zipf_after_collapse"], "WHALE_DATA_MISSING")
        self.assertEqual(g["rules"]["control"], "CALIBRATION_INCOMPLETE")
        self.assertIsNone(g["predictions"]["P2"])
        self.assertIsNone(g["predictions"]["P6"])
        self.assertIsNone(g["predictions"]["P7"])
        self.assertEqual(g["n_scored"], 0)
        self.assertIsNone(g["brier"])

    def test_whale_ok_calibration_incomplete(self):
        w = _set(R.BSOC)
        w["status"] = "ok"
        g = R.grade(self._res(w, [R.BSOC] * 6, [R.BSOC]))
        self.assertEqual(g["rules"]["R3_zipf_after_collapse"], "CALIBRATION_INCOMPLETE")
        self.assertIsNone(g["predictions"]["P7"])
        self.assertTrue(g["predictions"]["P6"])


if __name__ == "__main__":
    unittest.main()
