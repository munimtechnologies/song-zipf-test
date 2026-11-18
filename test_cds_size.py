# SPDX-License-Identifier: Apache-2.0
# Tests for cds_size.py (stdlib only; needs zipfseg.py and cds_job.py next to it). Expected
# values are worked out by hand in the comments. MV2, Munim, Inc. (mv2@munimtech.com).
# Made with AI agents.
import random
import unittest

import cds_size as S

BSO = "BEYOND_SECOND_ORDER"
ESO = "EXPLAINED_BY_SECOND_ORDER"


def fake(u, det, d1, ppr=None):
    return {"u": u, "labels": {"0.5": BSO if det else ESO}, "d1_majority": d1,
            "phonemes_per_recording": ppr if ppr is not None else u * 10.0,
            "m2": {"0.5": {"z": 1.0}}}


def scenario_threshold_280():
    rows = [fake(70, False, False) for _ in range(5)]
    rows += [fake(140, i == 0, False) for i in range(5)]          # 1 of 5 detected
    rows += [fake(280, True, True), fake(280, True, True),
             fake(280, False, False), fake(280, False, False)]     # 2 of 4
    rows += [fake(600, True, True) for _ in range(2)]
    rows += [fake(1200, True, True)]
    return rows


class TestDesign(unittest.TestCase):
    def test_fits_corpus(self):
        # largest: 600 x 8 x 2 = 9,600 and 1200 x 8 x 1 = 9,600 <= 9,790
        self.assertTrue(S.check_design(9790))
        self.assertFalse(S.check_design(9599))
        self.assertEqual(sum(r for _, r in S.DESIGN), 17)

    def test_seeds_distinct(self):
        seeds = [S.seed_for(u, r) for u, n in S.DESIGN for r in range(n)]
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertEqual(S.seed_for(70, 1), 20261118 + 10000 + 70)

    def test_replicate_blocks_do_not_overlap(self):
        utts = list(range(9790))
        b = S.replicate_blocks(utts, 70, 1)
        self.assertEqual(len(b), 8)
        self.assertEqual(b[0][0], 560)                 # 1 * 8 * 70
        self.assertEqual(b[-1][-1], 560 + 8 * 70 - 1)  # 1119
        for u, n in S.DESIGN:
            seen = set()
            for r in range(n):
                items = [x for blk in S.replicate_blocks(utts, u, r) for x in blk]
                self.assertEqual(len(items), 8 * u)
                self.assertFalse(seen & set(items))
                seen |= set(items)


class TestGrade(unittest.TestCase):
    def test_threshold_found(self):
        g = S.grade(scenario_threshold_280())
        agg = g["aggregate"]
        self.assertEqual(agg["140"]["detect"]["0.5"], 0.2)
        self.assertEqual(agg["280"]["detect"]["0.5"], 0.5)
        self.assertEqual(agg["280"]["d1_majority_rate"], 0.5)
        self.assertEqual(agg["280"]["phonemes_per_recording_mean"], 2800.0)
        self.assertEqual(g["predictions"], {k: True for k in S.PRIORS})
        r = g["rules"]
        self.assertEqual(r["T1_threshold_utterances"], 280)
        self.assertEqual(r["T1_threshold_phonemes_per_recording"], 2800.0)
        self.assertEqual(r["T1_label"], "THRESHOLD_FOUND")
        # D1-majority group: 2 (280) + 2 (600) + 1 (1200) = 5, all detected -> 1.0;
        # other group: 5 (70) + 5 (140) + 2 (280) = 12, 1 detected -> 1/12 <= 0.2
        self.assertEqual(r["T2"], "D1_TRACKS_DETECTION")
        self.assertEqual(r["T2_detect_rate_d1_majority"], 1.0)
        self.assertAlmostEqual(r["T2_detect_rate_d1_minority"], 1 / 12, places=12)
        self.assertTrue(r["T3_whale_size_within_detecting_range"])      # 2800 <= 5720
        self.assertFalse(r["T3_finch_size_within_detecting_range"])     # 2800 > 676
        # all true: .0625 * 3 + .25 + .0225 * 2 + .36 = .8425; / 7
        self.assertAlmostEqual(g["brier"], 0.8425 / 7, places=9)

    def test_no_threshold(self):
        rows = [fake(u, False, False) for u, n in S.DESIGN for _ in range(n)]
        g = S.grade(rows)
        p = g["predictions"]
        self.assertEqual((p["Z1"], p["Z2"], p["Z3"], p["Z4"], p["Z5"], p["Z6"], p["Z7"]),
                         (True, False, False, True, True, False, False))
        r = g["rules"]
        self.assertIsNone(r["T1_threshold_utterances"])
        self.assertIsNone(r["T1_threshold_phonemes_per_recording"])
        self.assertEqual(r["T1_label"], "NO_THRESHOLD_IN_RANGE")
        self.assertEqual(r["T2"], "UNDETERMINED")
        self.assertFalse(r["T3_whale_size_within_detecting_range"])

    def test_non_monotone(self):
        rows = scenario_threshold_280()
        rows[0] = fake(70, True, False)      # 70: 1 of 5 = 0.2; 140: 0.2 -> still monotone
        self.assertTrue(S.grade(rows)["predictions"]["Z4"])
        rows[1] = fake(70, True, False)      # 70: 0.4 > 140: 0.2 -> not monotone; Z1 false
        p = S.grade(rows)["predictions"]
        self.assertFalse(p["Z4"])
        self.assertFalse(p["Z1"])


class TestRunOne(unittest.TestCase):
    def test_tiny_corpus(self):
        # seeded random utterances of 2-4 words from a skewed lexicon, so chunk counts
        # are unequal and every Zipf R^2 is defined
        rng = random.Random(5)
        lex = ["ab"] * 6 + ["cde"] * 4 + ["fg"] * 3 + ["hij"] * 2 + ["k", "lm", "nop", "q"]
        utts = [[rng.choice(lex) for _ in range(rng.randint(2, 4))] for _ in range(80)]
        row = S.run_one(utts, 10, 0, b=2, thetas=(0.5,))
        self.assertEqual(row["start_utt"], 0)
        self.assertEqual(row["phonemes"], sum(len(w) for u in utts for w in u))
        self.assertEqual(row["phonemes_per_recording"], row["phonemes"] / 8)
        self.assertIn(row["labels"]["0.5"], (BSO, ESO, "EXPLAINED_BY_FIRST_ORDER"))
        self.assertIsInstance(row["d1_majority"], bool)
        self.assertEqual(set(row["m2"]["0.5"]), {"null_mean", "z", "p"})


class TestRegistration(unittest.TestCase):
    def test_found(self):
        r = S.wait_for_registration(0, fetcher=lambda url: b"# CDS-SIZE-PREREG: ...")
        self.assertTrue(r["found"])
        self.assertEqual(r["tries"], 1)

    def test_not_found(self):
        def fetcher(url):
            raise IOError("404")
        r = S.wait_for_registration(-1, fetcher=fetcher)
        self.assertFalse(r["found"])
        self.assertIn("404", r["last_error"])


if __name__ == "__main__":
    unittest.main()
