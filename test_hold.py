# SPDX-License-Identifier: Apache-2.0
# Tests for hold.py (HOLD-PREREG.md). Standard library only; no data, no network.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import math
import random
import unittest

import hold as H


def _rows(real_bso, neg_bso):
    """17 CDS replicates in DESIGN order; real_bso/neg_bso: sets of (u, rep) labelled BSO."""
    rows = []
    for u, n in H.DESIGN:
        for r in range(n):
            rows.append({"u": u, "rep": r, "phonemes_per_recording": u * 10.0,
                         "real": {"label": H.BSO if (u, r) in real_bso else H.ND},
                         "neg": {"label": H.BSO if (u, r) in neg_bso else H.ND}})
    return rows


ALL = set(H.ZIPF_BSO)


class TestCounts(unittest.TestCase):
    def test_counts_by_hand(self):
        F = H.ngram_counts([["a", "b", "a"]], 2)
        self.assertEqual(dict(F[()]), {"a": 2, "b": 1})
        self.assertEqual(dict(F[("a",)]), {"b": 1})
        self.assertEqual(dict(F[("b",)]), {"a": 1})
        self.assertEqual(dict(F[("a", "b")]), {"a": 1})
        self.assertEqual(len(F), 4)

    def test_contexts_do_not_cross_bouts(self):
        F = H.ngram_counts([["a"], ["b"]], 2)
        self.assertEqual(set(F), {()})


class TestWittenBell(unittest.TestCase):
    def test_two_identical_bouts_by_hand(self):
        # held out ["a","b"], trained on ["a","b"]: V=2, base 1/3;
        # P0 = (1 + 2/3)/(2 + 2) = 5/12; P1(b|a) = (1 + 5/12)/(1 + 1) = 17/24
        h = H.heldout_entropy([["a", "b"], ["a", "b"]], 1)
        self.assertAlmostEqual(h[0], math.log2(12 / 5), places=12)
        self.assertAlmostEqual(h[1], (math.log2(12 / 5) + math.log2(24 / 17)) / 2,
                               places=12)

    def test_unseen_symbol_by_hand(self):
        # held out ["a"], trained on ["b"]: V=1, base 1/2; P0(a) = (0 + 1/2)/(1 + 1)
        h = H.heldout_entropy([["a"], ["b"]], 0)
        self.assertAlmostEqual(h[0], 2.0, places=12)

    def test_probabilities_sum_to_one(self):
        rng = random.Random(5)
        bouts = [[rng.choice("abc") for _ in range(rng.randint(3, 9))] for _ in range(12)]
        F = H.ngram_counts(bouts, 3)
        st = H.Stats(F, H.ngram_counts([bouts[0]], 3))
        train = [s for s in F[()] if st.count((), s) > 0]
        self.assertEqual(len(train), st.V)
        for hist in [(), ("a",), ("a", "b"), ("c", "c", "a"), ("b", "b", "b")]:
            tot = [0.0] * 4
            for s in train + ["<unseen>"]:
                for k, p in enumerate(H.probs_all_orders(s, hist, 3, st)):
                    tot[k] += p
            for k in range(4):
                self.assertAlmostEqual(tot[k], 1.0, places=12)

    def test_leave_out_matches_refit(self):
        rng = random.Random(11)
        bouts = [[rng.choice("abcd") for _ in range(rng.randint(2, 8))] for _ in range(9)]
        F = H.ngram_counts(bouts, 2)
        st = H.Stats(F, H.ngram_counts([bouts[3]], 2))
        G = H.ngram_counts(bouts[:3] + bouts[4:], 2)
        st2 = H.Stats(G, {})
        self.assertEqual(st.V, st2.V)
        for hist in [(), ("a",), ("b", "c"), ("d", "d")]:
            for s in "abcdz":
                a = H.probs_all_orders(s, hist, 2, st)
                b = H.probs_all_orders(s, hist, 2, st2)
                for x, y in zip(a, b):
                    self.assertAlmostEqual(x, y, places=12)

    def test_order3_structure_gives_gain(self):
        # 'aaab' repeated: after (a,a) comes a or b (1 bit); (a,a,a)->b, (b,a,a)->a
        h = H.heldout_entropy([list("aaab" * 5) for _ in range(20)], 5)
        self.assertGreater(H.gain(h), 0.1)
        self.assertGreaterEqual(H.argmin(h), 3)


class TestSetAndHelpers(unittest.TestCase):
    def test_identity_surrogate_gives_p_one(self):
        rng = random.Random(3)
        recs = [[[rng.choice("ab") for _ in range(6)] for _ in range(5)] for _ in range(2)]
        out = H.test_set(recs, 3, 1, lambda rec, r: rec, kmax=3)
        self.assertEqual(out["p"], 1.0)
        self.assertEqual(out["label"], H.ND)
        for r in out["per_recording"]:
            self.assertEqual(r["p"], 1.0)
        self.assertAlmostEqual(out["null_sd"], 0.0, places=12)
        self.assertEqual(len(out["mean_H"]), 4)

    def test_pval_argmin_sd(self):
        self.assertEqual(H.pval(1.0, [0.0, 1.0, 2.0]), 0.75)
        self.assertEqual(H.argmin([3.0, 1.0, 1.0, 2.0]), 1)
        self.assertEqual(H.sd([1.0, 3.0]), 1.0)
        self.assertEqual(H.seed_for(70, 2), 20261119 + 20070)

    def test_neg_dataset_seeds(self):
        seen = []
        H.neg_dataset([["x"], ["y"]], 4, lambda rec, rng: seen.append(rng.random()) or rec)
        self.assertEqual(seen, [random.Random(400).random(), random.Random(401).random()])


class TestGrading(unittest.TestCase):
    def test_zipf_detect(self):
        self.assertEqual(H.zipf_detect(), {70: 0.0, 140: 0.2, 280: 1.0, 600: 1.0, 1200: 1.0})

    def test_power_label(self):
        z = H.zipf_detect()
        self.assertEqual(H.power_label({70: 0.2, 140: 0.2, 280: 1.0, 600: 1.0, 1200: 1.0}, z),
                         "HOLD_MORE_POWERFUL")
        self.assertEqual(H.power_label(dict(z), z), "HOLD_EQUAL")
        self.assertEqual(H.power_label({70: 0.0, 140: 0.0, 280: 1.0, 600: 1.0, 1200: 1.0}, z),
                         "HOLD_LESS_POWERFUL")
        self.assertEqual(H.power_label({70: 0.2, 140: 0.0, 280: 1.0, 600: 1.0, 1200: 1.0}, z),
                         "MIXED")
        self.assertEqual(H.power_label({70: 0.2}, z), "INCOMPLETE")

    def test_grade_all_true(self):
        real = ALL - {(70, 0), (70, 1)}
        whale = {"status": "ok",
                 "real": {"p": 0.004975, "label": H.BSO,
                          "per_recording": [{"p": 0.01}] * 7 + [{"p": 0.2}],
                          "mean_H": [3.0, 2.0, 1.9, 1.5, 1.6, 1.7]},
                 "neg": {"p": 0.4, "label": H.ND}}
        g = H.grade(_rows(real, {(600, 1)}), whale)
        self.assertTrue(g["complete"])
        self.assertEqual(g["detect_hold"]["70"], 0.6)
        self.assertTrue(all(g["predictions"][k] for k in H.PRIORS))
        self.assertEqual(g["rules"]["R1_power_vs_zipf"], "HOLD_MORE_POWERFUL")
        self.assertEqual(g["rules"]["R2_threshold_utterances"], 70)
        self.assertEqual(g["rules"]["R2_threshold_phonemes_per_recording"], 700.0)
        self.assertEqual(g["rules"]["R3_negative_control"], "CONTROL_OK")
        self.assertEqual(g["rules"]["R3_negative_positives"], 1)
        self.assertEqual(g["rules"]["R4_whale"], H.BSO)
        self.assertEqual(g["n_scored"], 9)
        self.assertAlmostEqual(g["brier"], 1.08 / 9, places=12)

    def test_grade_whale_missing(self):
        g = H.grade(_rows(ALL - {(70, 0), (70, 1)}, set()), {"status": "missing"})
        self.assertEqual(g["rules"]["R4_whale"], "WHALE_DATA_MISSING")
        self.assertIsNone(g["predictions"]["H5"])
        self.assertEqual(g["n_scored"], 4)
        self.assertAlmostEqual(g["brier"], 0.5675 / 4, places=12)

    def test_grade_control_failed(self):
        whale = {"status": "ok",
                 "real": {"p": 0.01, "label": H.BSO, "per_recording": [{"p": 0.01}] * 8,
                          "mean_H": [3.0, 2.0, 1.9, 1.5, 1.6, 1.7]},
                 "neg": {"p": 0.4, "label": H.ND}}
        g = H.grade(_rows(ALL, {(70, 0), (70, 1), (140, 0)}), whale)
        self.assertEqual(g["rules"]["R3_negative_control"], "CONTROL_FAILED")
        self.assertEqual(g["rules"]["R4_whale"], "CONTROL_FAILED")
        self.assertFalse(g["predictions"]["H4"])

    def test_grade_underpowered(self):
        whale = {"status": "ok",
                 "real": {"p": 0.3, "label": H.ND, "per_recording": [{"p": 0.3}] * 8,
                          "mean_H": [3.0, 2.0, 2.1, 2.2, 2.3, 2.4]},
                 "neg": {"p": 0.5, "label": H.ND}}
        g = H.grade(_rows(set(), set()), whale)
        self.assertEqual(g["rules"]["R1_power_vs_zipf"], "HOLD_LESS_POWERFUL")
        self.assertIsNone(g["rules"]["R2_threshold_utterances"])
        self.assertEqual(g["rules"]["R4_whale"], "NOT_DETECTED_UNDERPOWERED")
        self.assertFalse(g["predictions"]["H5"])
        self.assertFalse(g["predictions"]["H7"])
        self.assertFalse(g["predictions"]["H9"])

    def test_grade_incomplete(self):
        rows = _rows(ALL, set())[:-1]
        whale = {"status": "ok",
                 "real": {"p": 0.3, "label": H.ND, "per_recording": [{"p": 0.3}] * 8,
                          "mean_H": [3.0, 2.0, 2.1, 2.2, 2.3, 2.4]},
                 "neg": {"p": 0.5, "label": H.ND}}
        g = H.grade(rows, whale)
        self.assertFalse(g["complete"])
        self.assertEqual(g["rules"]["R1_power_vs_zipf"], "INCOMPLETE")
        self.assertEqual(g["rules"]["R4_whale"], "CALIBRATION_INCOMPLETE")
        self.assertIsNone(g["predictions"]["H1"])
        self.assertEqual(g["n_scored"], 5)


if __name__ == "__main__":
    unittest.main()
