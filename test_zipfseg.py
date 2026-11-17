# SPDX-License-Identifier: Apache-2.0
# Offline tests for zipfseg (hand-traced; see comments). MV2, Munim, Inc.; made with AI agents.
import json
import math
import random
import unittest

import zipfseg as z

CYC = {("a", "b"), ("b", "c"), ("c", "a")}


def pairs(seq):
    return set(zip(seq, seq[1:]))


class TestTP(unittest.TestCase):
    def test_bigram_tp(self):
        # pairs ab, ba, ac; 'a' starts 2 pairs, 'b' starts 1
        tp = z.bigram_tp([["a", "b", "a", "c"]])
        self.assertEqual(tp, {("a", "b"): 0.5, ("b", "a"): 1.0, ("a", "c"): 0.5})

    def test_no_cross_bout_pairs(self):
        tp = z.bigram_tp([["a", "b"], ["c", "a"]])
        self.assertNotIn(("b", "c"), tp)
        self.assertEqual(tp[("a", "b")], 1.0)


class TestSegment(unittest.TestCase):
    def setUp(self):
        self.bout = ["a", "b", "a", "c"]
        self.tp = z.bigram_tp([self.bout])  # t = [0.5, 1.0, 0.5]

    def test_cut_strict(self):
        # i=2: 0.5/1.0 = 0.5, not < 0.5 -> no cut
        self.assertEqual(z.segment_bout(self.bout, self.tp, 0.5), [("a", "b", "a", "c")])

    def test_cut(self):
        # i=2: 0.5 < 0.6 -> cut after the third symbol
        self.assertEqual(z.segment_bout(self.bout, self.tp, 0.6),
                         [("a", "b", "a"), ("c",)])

    def test_rule_reversed(self):
        # prev/cur: i=1: 0.5/1.0 = 0.5 < 0.6 -> cut between b and a
        self.assertEqual(z.segment_bout(self.bout, self.tp, 0.6, "prev_over_cur"),
                         [("a", "b"), ("a", "c")])

    def test_concatenation(self):
        rng = random.Random(1)
        bouts = [[rng.choice("abcd") for _ in range(rng.randint(1, 30))] for _ in range(20)]
        tp = z.bigram_tp(bouts)
        for rule in z.RULES:
            for th in (0.3, 0.5, 0.7):
                for b in bouts:
                    segs = z.segment_bout(b, tp, th, rule)
                    self.assertEqual(tuple(s for seg in segs for s in seg), tuple(b))

    def test_inventory_total(self):
        inv = z.segment_recording([self.bout, ["a", "b"]], 0.6)
        self.assertEqual(sum(len(k) * v for k, v in inv.items()), 6)


class TestZipf(unittest.TestCase):
    def test_power_law(self):
        f = [1000, 500, 333, 250, 200, 167, 143, 125, 111, 100]
        self.assertGreater(z.zipf_r2(f), 0.999)

    def test_slope(self):
        f = [3600, 900, 400, 225]  # 3600 / r^2
        self.assertAlmostEqual(z.zipf_slope(f), -2.0, places=9)
        self.assertAlmostEqual(z.zipf_r2(f), 1.0, places=9)

    def test_degenerate(self):
        self.assertTrue(math.isnan(z.zipf_r2([5, 3])))
        self.assertTrue(math.isnan(z.zipf_r2([4, 4, 4])))
        self.assertTrue(math.isnan(z.nanmean([float("nan")])))
        self.assertEqual(z.nanmean([1.0, float("nan"), 3.0]), 2.0)


class TestNulls(unittest.TestCase):
    def test_resample_cyclic(self):
        rng = random.Random(7)
        t = list("abcabcabc")
        for k in (1, 2):
            for _ in range(50):
                o = z.resample_bout(t, k, rng)
                self.assertEqual(len(o), 9)
                self.assertTrue(pairs(o) <= CYC)

    def test_resample_reseed(self):
        rng = random.Random(3)
        for _ in range(50):
            o = z.resample_bout(["a", "b"], 1, rng)
            self.assertEqual(len(o), 2)
            self.assertTrue(set(o) <= {"a", "b"})

    def test_markov_cyclic(self):
        rng = random.Random(11)
        rec = [list("abcabc"), list("bcabca")]
        for k in (1, 2):
            for _ in range(50):
                out = z.markov_recording(rec, k, rng)
                self.assertEqual([len(b) for b in out], [6, 6])
                for b in out:
                    self.assertTrue(pairs(b) <= CYC)

    def test_markov_short_bout_copied(self):
        out = z.markov_recording([["x"], list("abcabc")], 2, random.Random(0))
        self.assertEqual(out[0], ["x"])

    def test_shuffle_multiset(self):
        rng = random.Random(5)
        rec = [list("aabbc"), list("cd")]
        out = z.shuffle_recording(rec, rng)
        self.assertEqual([sorted(b) for b in out], [sorted(b) for b in rec])


class TestStats(unittest.TestCase):
    def test_compare(self):
        c = z.compare(5.0, [1.0, 2.0, 3.0])
        self.assertAlmostEqual(c["z"], 3.0)
        self.assertAlmostEqual(c["p"], 0.25)
        self.assertEqual(c["null_frac_r2_ge_0.80"], 1.0)

    def test_heldout_order2_wins(self):
        # "aab" repeated: order 1 is ~-0.50 nats/symbol, order 2 ~-0.045
        rec = [list("aab" * 4) for _ in range(4)]
        d = z.heldout_ll(rec, 2) - z.heldout_ll(rec, 1)
        self.assertGreater(d, 0.2)

    def test_analyze_smoke_and_determinism(self):
        rng = random.Random(42)
        recs = [[[rng.choice("abcd") for _ in range(20)] for _ in range(5)] for _ in range(2)]
        a = z.analyze(recs, thetas=(0.5,), B=5, seed=1)
        b = z.analyze(recs, thetas=(0.5,), B=5, seed=1)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        row = a["by_theta"]["0.5"]
        self.assertEqual(set(row["nulls"]), set(z.NULLS))
        for c in row["nulls"].values():
            self.assertTrue(0 < c["p"] <= 1)
        self.assertEqual(len(a["heldout_ll_order2_minus_order1"]["per_recording"]), 2)


if __name__ == "__main__":
    unittest.main()
