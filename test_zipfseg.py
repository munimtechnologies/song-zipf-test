# SPDX-License-Identifier: Apache-2.0
# Offline tests for zipfseg (hand-traced; see comments). MV2, Munim, Inc.; made with AI agents.
import json
import math
import random
import unittest
from collections import defaultdict

import zipfseg as z

CYC = {("a", "b"), ("b", "c"), ("c", "a")}


def pairs(seq):
    return set(zip(seq, seq[1:]))


def codes1_segment(strings, ratio):
    """Literal transcription of Kirby et al. 2026 Code S1 (ngram_table,
    transition_data with forwards=True and n=2, cut_sequences_sliding) for one
    recording. Used only to check that zipfseg reproduces it exactly."""
    big = defaultdict(int)
    uni = defaultdict(int)
    for s in strings:
        for i in range(len(s) - 1):
            big[str(s[i:i + 2])] += 1
        for i in range(len(s)):
            uni[str(s[i:i + 1])] += 1
    sentences = []
    for s in strings:
        ts = [big[str(s[i:i + 2])] / uni[str(s[i:i + 1])] for i in range(len(s) - 1)]
        words = []
        word = s[0:1]
        last_tp = 0
        for j in range(len(ts)):
            if ts[j] < last_tp * ratio:
                words.append(word)
                word = []
            word.append(s[j + 1])
            last_tp = ts[j]
        words.append(word)
        sentences.append(words)
    return sentences


class TestTP(unittest.TestCase):
    def test_bigram_tp(self):
        # pairs ab, ba, ac; 'a' occurs twice, 'b' once
        tp = z.bigram_tp([["a", "b", "a", "c"]])
        self.assertEqual(tp, {("a", "b"): 0.5, ("b", "a"): 1.0, ("a", "c"): 0.5})

    def test_no_cross_bout_pairs_and_denominator(self):
        # 'a' occurs twice (once bout-final); pair ab once
        tp = z.bigram_tp([["a", "b"], ["c", "a"]])
        self.assertNotIn(("b", "c"), tp)
        self.assertEqual(tp[("a", "b")], 0.5)          # Code S1: n(ab)/n(a) = 1/2
        self.assertEqual(tp[("c", "a")], 1.0)
        tpf = z.bigram_tp([["a", "b"], ["c", "a"]], denominator="followed")
        self.assertEqual(tpf[("a", "b")], 1.0)         # n(ab)/n(a,.) = 1/1


class TestSegment(unittest.TestCase):
    def setUp(self):
        self.bout = ["a", "b", "a", "c"]
        self.tp = z.bigram_tp([self.bout])  # t = [0.5, 1.0, 0.5]

    def test_cut_strict(self):
        # i=2: 0.5 < 1.0*0.5 is false -> no cut
        self.assertEqual(z.segment_bout(self.bout, self.tp, 0.5), [("a", "b", "a", "c")])

    def test_cut(self):
        # i=2: 0.5 < 1.0*0.6 -> cut after the third symbol
        self.assertEqual(z.segment_bout(self.bout, self.tp, 0.6),
                         [("a", "b", "a"), ("c",)])

    def test_rule_reversed(self):
        # prev/cur: i=1: 0.5 < 1.0*0.6 -> cut between b and a; i=2: 1.0 < 0.3 no
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

    def test_matches_code_s1_exactly(self):
        rng = random.Random(2026)
        for trial in range(30):
            alpha = "abcdefgh"[: rng.randint(2, 8)]
            bouts = [[rng.choice(alpha) for _ in range(rng.randint(1, 40))]
                     for _ in range(rng.randint(1, 12))]
            for th in (0.3, 0.5, 0.7):
                ours = [[list(s) for s in segs]
                        for segs in z.segment_recording_bouts(bouts, th)]
                self.assertEqual(ours, codes1_segment(bouts, th))

    def test_inventory_total(self):
        inv = z.segment_recording([self.bout, ["a", "b"]], 0.6)
        self.assertEqual(sum(len(k) * v for k, v in inv.items()), 6)

    def test_cut_positions(self):
        self.assertEqual(z.cut_positions([("a", "b"), ("c",), ("d", "e")]), [2, 3])
        self.assertEqual(z.cut_positions([("a",)]), [])


class TestZipf(unittest.TestCase):
    def test_power_law(self):
        f = [1000, 500, 333, 250, 200, 167, 143, 125, 111, 100]
        self.assertGreater(z.zipf_r2(f), 0.999)

    def test_slope(self):
        f = [3600, 900, 400, 225]  # 3600 / r^2
        self.assertAlmostEqual(z.zipf_slope(f), -2.0, places=9)
        self.assertAlmostEqual(z.zipf_r2(f), 1.0, places=9)

    def test_degenerate(self):
        self.assertEqual(z.zipf_r2([5, 3]), 1.0)        # Code S1: 2 points, r = -1
        self.assertTrue(math.isnan(z.zipf_r2([7])))
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

    def test_rotate(self):
        rng = random.Random(9)
        segs = [("a", "b"), ("c",)]
        allowed = [[("a", "b"), ("c",)], [("b", "c"), ("a",)], [("c", "a"), ("b",)]]
        for _ in range(30):
            self.assertIn(z.rotate_bout_segments(segs, rng), allowed)
        self.assertEqual(z.rotate_bout_segments([], rng), [])


class TestStats(unittest.TestCase):
    def test_compare(self):
        # mean 2, population sd sqrt(2/3)
        c = z.compare(5.0, [1.0, 2.0, 3.0])
        self.assertAlmostEqual(c["z"], 3.0 / math.sqrt(2.0 / 3.0))
        self.assertAlmostEqual(c["p"], 0.25)
        self.assertEqual(c["null_frac_r2_ge_0.80"], 1.0)

    def test_heldout_order2_wins(self):
        # "aab" repeated: order 1 is ~-0.50 nats/symbol, order 2 ~-0.045
        rec = [list("aab" * 4) for _ in range(4)]
        d = z.heldout_ll(rec, 2) - z.heldout_ll(rec, 1)
        self.assertGreater(d, 0.2)

    def test_decision(self):
        def row(p1, p2):
            return {"nulls": {"markov1_pooled": {"p": p1}, "markov2_pooled": {"p": p2}}}
        self.assertEqual(z.decision(row(0.001, 0.01)), "BEYOND_SECOND_ORDER")
        self.assertEqual(z.decision(row(0.001, 0.2)), "EXPLAINED_BY_SECOND_ORDER")
        self.assertEqual(z.decision(row(0.3, 0.6)), "EXPLAINED_BY_FIRST_ORDER")

    def test_analyze_smoke_and_determinism(self):
        rng = random.Random(42)
        recs = [[[rng.choice("abcd") for _ in range(20)] for _ in range(5)] for _ in range(2)]
        a = z.analyze(recs, thetas=(0.5,), B=5, seed=1)
        b = z.analyze(recs, thetas=(0.5,), B=5, seed=1)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        row = a["by_theta"]["0.5"]
        self.assertEqual(set(row["nulls"]), set(z.NULLS) | {"rotate"})
        for c in row["nulls"].values():
            self.assertTrue(0 < c["p"] <= 1)
        self.assertEqual(len(a["heldout_ll_order2_minus_order1"]["per_recording"]), 2)


if __name__ == "__main__":
    unittest.main()
