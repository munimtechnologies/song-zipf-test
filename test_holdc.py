# SPDX-License-Identifier: Apache-2.0
# Tests for holdc.py (HOLDC-PREREG.md). Standard library only; needs hold.py and runs.py
# (fetched unchanged by setup_holdc.sh); no data, no network.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import random
import unittest

import holdc as HC
import runs as R


class FakeRng:
    """random() always 0.0 (a repeat after every symbol); randint(a, b) always a."""

    def random(self):
        return 0.0

    def randint(self, a, b):
        return a


class TestInflate(unittest.TestCase):
    def test_never(self):
        self.assertEqual(HC.inflate(list("abc"), random.Random(1), q=0.0), list("abc"))

    def test_by_hand(self):
        # after each symbol: L = 1, r = 1 -> every symbol doubled
        self.assertEqual(HC.inflate(list("ab"), FakeRng()), list("aabb"))
        self.assertEqual(R.collapse(HC.inflate(list("ab"), FakeRng())), list("ab"))

    def test_collapse_of_inflated_square_free(self):
        rng = random.Random(5)
        for _ in range(100):
            base = R.collapse([rng.choice("abcde") for _ in range(rng.randint(1, 40))])
            inf = HC.inflate(base, rng)
            self.assertGreaterEqual(len(inf), len(base))
            col = R.collapse(inf)
            self.assertFalse(R.has_square(col, HC.LMAX))
            self.assertLessEqual(len(col), len(inf))

    def test_share_near_design(self):
        # expected extra symbols per symbol: q * 2.5 * 2 = 1.75, so the share removed by
        # collapsing should be well above a third on long square-free input
        rng = random.Random(11)
        base = R.collapse([rng.choice("abcdefgh") for _ in range(3000)])
        inf = HC.inflate(base, rng)
        self.assertGreater(1 - len(base) / len(inf), 0.4)


class TestSizeMatched(unittest.TestCase):
    def test_by_hand(self):
        utts = [["ab"], ["c"], ["de", "f"], [""], ["g"]]
        recs, pos = HC.size_matched(utts, 0, [2, 3])
        self.assertEqual(recs, [[["a", "b"]], [["c"], ["d", "e", "f"]]])
        self.assertEqual(pos, 3)
        recs, pos = HC.size_matched(utts, 0, [2, 3, 5])
        self.assertIsNone(recs)
        self.assertEqual(pos, 5)
        recs, pos = HC.size_matched(utts, 1, [1])
        self.assertEqual(recs, [[["c"]]])
        self.assertEqual(pos, 2)


class TestPipelineToy(unittest.TestCase):
    def setUp(self):
        rng = random.Random(3)
        self.years = [[[rng.choice("abcd") for _ in range(30)] for _ in range(3)]
                      for _ in range(2)]

    def test_surc_square_free(self):
        W = HC.collapse_all(self.years)
        out = HC.surc(W[0], random.Random(1))
        self.assertEqual(len(out), len(W[0]))
        for b in out:
            self.assertFalse(R.has_square(b, HC.LMAX))

    def test_run_whale_sets_and_rep_control(self):
        res, W = HC.run_whale_sets(self.years, b_real=3, b_neg=3)
        self.assertEqual(res["elements"], [90, 90])
        self.assertEqual(res["elements_collapsed"], HC.n_sym(W))
        self.assertEqual(res["real"]["B"], 3)
        self.assertIn(res["real"]["label"], (HC.BSO, "NOT_DETECTED"))
        self.assertEqual(len(res["real"]["mean_H"]), 6)
        sur2 = lambda rec, rng: HC.surc(rec, rng)
        row = HC.rep_control(W, 0, sur2, b=2)
        self.assertEqual(row["seed"], HC.SEED + 100)
        self.assertEqual(row["uncollapsed"]["B"], 2)
        self.assertTrue(0.0 <= row["share_removed"] < 1.0)
        self.assertTrue(0.0 <= row["bouts_recovered"] <= 1.0)
        a = HC.rep_control(W, 0, sur2, b=2)
        self.assertEqual(a["elements_inflated"], row["elements_inflated"])   # seeded

    def test_en_replicate(self):
        utts = [["ab", "c"], ["dab"]] * 40
        row = HC.en_replicate(utts, 0, [20, 20], b=2)
        self.assertEqual(row["status"], "ok")
        self.assertEqual(row["start_utt"], 0)
        self.assertEqual(row["phonemes"], [21, 21])
        self.assertEqual(row["real"]["B"], 2)
        row = HC.en_replicate(utts, 1, [20, 20], b=2)     # starts beyond the corpus
        self.assertEqual(row["status"], "corpus_exhausted")


def T(p, gain=0.0):
    return {"p": p, "mean_gain": gain}


def result(w_p=0.001, w_gain=0.01, w_neg=0.5, en=(0.01,) * 5, en_neg=(0.5,) * 5,
           rp_unc=(0.01,) * 3, rp_col=(0.5,) * 3):
    return {"whale": {"status": "ok", "real": T(w_p, w_gain), "neg": T(w_neg)},
            "english": [{"status": "ok", "real": T(a), "neg": T(b)}
                        for a, b in zip(en, en_neg)],
            "repetition": [{"uncollapsed": T(a), "collapsed": T(b)}
                           for a, b in zip(rp_unc, rp_col)]}


class TestGrade(unittest.TestCase):
    def test_all_true(self):
        g = HC.grade(result())
        self.assertEqual(g["rules"]["control"], "CONTROL_OK")
        self.assertEqual(g["rules"]["R1_whale_after_collapse"], HC.R1_BEYOND)
        self.assertEqual(g["rules"]["R2_repetition_alone"], HC.FOOLS)
        self.assertTrue(all(g["predictions"][k] for k in HC.PRIORS))
        # .2025 + .0225 + .0225 + .0225 + .04 + .0625 + .25 = .6225
        self.assertAlmostEqual(g["brier"], 0.6225 / 7, places=12)

    def test_not_detected_with_power(self):
        g = HC.grade(result(w_p=0.3, w_gain=-0.02))
        self.assertEqual(g["rules"]["R1_whale_after_collapse"], HC.R1_NOT)
        self.assertFalse(g["predictions"]["Q1"])
        self.assertFalse(g["predictions"]["Q7"])

    def test_controls(self):
        g = HC.grade(result(en=(0.01, 0.01, 0.01, 0.5, 0.5)))
        self.assertEqual(g["rules"]["control"], "CONTROL_FAILED")
        self.assertEqual(g["rules"]["R1_whale_after_collapse"], "CONTROL_FAILED")
        self.assertFalse(g["predictions"]["Q2"])
        g = HC.grade(result(rp_col=(0.01, 0.01, 0.5)))
        self.assertEqual(g["rules"]["control"], "CONTROL_FAILED")
        self.assertFalse(g["predictions"]["Q6"])
        g = HC.grade(result(rp_col=(0.01, 0.5, 0.5)))
        self.assertEqual(g["rules"]["control"], "CONTROL_OK")
        self.assertFalse(g["predictions"]["Q6"])
        g = HC.grade(result(w_neg=0.01))
        self.assertEqual(g["rules"]["control"], "CONTROL_FAILED")
        self.assertFalse(g["predictions"]["Q4"])
        g = HC.grade(result(rp_unc=(0.01, 0.5, 0.5)))
        self.assertEqual(g["rules"]["R2_repetition_alone"], HC.NOT_FOOLS)
        self.assertFalse(g["predictions"]["Q5"])

    def test_incomplete(self):
        r = result()
        r["english"][4] = {"status": "corpus_exhausted"}
        g = HC.grade(r)
        self.assertEqual(g["rules"]["control"], "CALIBRATION_INCOMPLETE")
        self.assertIsNone(g["predictions"]["Q2"])
        self.assertEqual(g["n_scored"], 5)
        r = result()
        r["whale"] = {"status": "missing"}
        g = HC.grade(r)
        self.assertEqual(g["rules"]["R1_whale_after_collapse"], "WHALE_DATA_MISSING")
        self.assertIsNone(g["rules"]["whale_negative_detected"])
        self.assertEqual(g["n_scored"], 4)


if __name__ == "__main__":
    unittest.main()
