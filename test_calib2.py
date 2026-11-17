# SPDX-License-Identifier: Apache-2.0
# Tests for calib2.py (CALIB-2-PREREG.md). MV2, Munim, Inc. Made with AI agents.
import random
import time
import unittest

import calib2 as K


def _fake(sc, p_shuffle, p_rotate, p_bigram, p_m1, p_m2, r2, label):
    def n(p):
        return {"z": 1.0, "p": p, "null_mean": 0.5, "null_sd": 0.1}
    return {"scenario": sc, "rep": 0, "skipped": False, "real_r2": r2,
            "cuts_per_bout": 10.0, "n_symbols": 100, "label": label,
            "d1_n_favour_order2": 0,
            "nulls": {"shuffle": n(p_shuffle), "bigram_within": n(p_bigram),
                      "markov1_pooled": n(p_m1), "markov2_pooled": n(p_m2),
                      "rotate": n(p_rotate)}}


class TestScenarios(unittest.TestCase):
    def test_table(self):
        names = [s[0] for s in K.SCENARIOS]
        self.assertEqual(len(names), 7)
        self.assertEqual(len(set(names)), 7)
        for name, size, V, kind, params in K.SCENARIOS:
            self.assertIn(size, K.SIZES)
            self.assertIn(kind, ("markov1", "markov2", "words"))
            self.assertTrue(V >= 8)

    def test_seeds_distinct(self):
        seeds = {K.task_seed(s[0], r) for s in K.SCENARIOS for r in range(20)}
        self.assertEqual(len(seeds), 7 * 20)

    def test_dataset_size_and_determinism(self):
        a = K.make_dataset("W_markov1_a0.2_V12", random.Random(5), n_rec=2)
        b = K.make_dataset("W_markov1_a0.2_V12", random.Random(5), n_rec=2)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 2)
        for rec in a:
            self.assertEqual(len(rec), 6)
            for bout in rec:
                self.assertTrue(700 <= len(bout) <= 1500)
                self.assertTrue(all(0 <= s < 12 for s in bout))
        f = K.make_dataset("F_words_zipf_noise05", random.Random(1), n_rec=3)
        self.assertEqual(len(f), 3)
        self.assertTrue(all(len(r) == 10 for r in f))
        self.assertTrue(all(40 <= len(bt) <= 96 for r in f for bt in r))
        self.assertTrue(all(0 <= s < 8 for r in f for bt in r for s in bt))

    def test_preset_recording_counts(self):
        w = K.make_dataset("W_words_zipf_V12", random.Random(2))
        self.assertEqual(len(w), 8)


class TestRunTask(unittest.TestCase):
    def test_tiny_task(self):
        t = dict(scenario="W_words_zipf_V12", rep=0, B=2, theta=0.5,
                 deadline=time.time() + 600, n_rec=1)
        r = K.run_task(t)
        self.assertFalse(r["skipped"])
        self.assertEqual(set(r["nulls"]),
                         {"shuffle", "bigram_within", "markov1_pooled", "markov2_pooled", "rotate"})
        self.assertIn(r["label"], ("BEYOND_SECOND_ORDER", "EXPLAINED_BY_SECOND_ORDER",
                                   "EXPLAINED_BY_FIRST_ORDER"))
        self.assertTrue(0.0 <= r["real_r2"] <= 1.0)
        self.assertEqual(r["n_rec"], 1)

    def test_deadline_skips(self):
        t = dict(scenario="W_words_zipf_V12", rep=0, B=2, theta=0.5,
                 deadline=time.time() - 1, n_rec=1)
        self.assertTrue(K.run_task(t)["skipped"])


class TestAggregateAndGrade(unittest.TestCase):
    def test_aggregate_extras(self):
        sc = "W_markov1_a0.2_V12"
        rs = [_fake(sc, 0.01, 0.01, 0.01, 0.5, 0.5, 0.95, "EXPLAINED_BY_FIRST_ORDER"),
              _fake(sc, 0.01, 0.01, 0.50, 0.5, 0.5, 0.85, "EXPLAINED_BY_FIRST_ORDER"),
              _fake(sc, 0.01, 0.50, 0.01, 0.5, 0.5, 0.85, "EXPLAINED_BY_FIRST_ORDER"),
              _fake(sc, 0.01, 0.01, 0.01, 0.5, 0.5, 0.75, "EXPLAINED_BY_FIRST_ORDER")]
        a = K.aggregate(rs)[sc]
        self.assertAlmostEqual(a["frac_pass_published_controls"], 0.75)
        self.assertAlmostEqual(a["frac_pass_finch_controls"], 0.5)
        self.assertAlmostEqual(a["frac_real_r2_ge_0.93"], 0.25)
        self.assertAlmostEqual(a["cuts_per_recording_mean"], 60.0)

    def _agg(self):
        def s(pass_pub, r2, m1=0.0, big=0.0, bso=0.0):
            return {"frac_pass_published_controls": pass_pub, "real_r2_mean": r2,
                    "frac_beyond_second_order": bso,
                    "nulls": {"markov1_pooled": {"frac_p_lt_alpha": m1},
                              "bigram_within": {"frac_p_lt_alpha": big}}}
        return {"W_markov1_a0.2_V12": s(1.0, 0.85),
                "W_markov1_a0.1_V24": s(0.9, 0.82),
                "W_markov2_a0.2_V12": s(1.0, 0.6, bso=0.0),
                "W_words_zipf_V12": s(1.0, 0.9, bso=1.0),
                "W_words_zipf_noise10_V12": s(1.0, 0.8, bso=0.6),
                "F_words_zipf_noise02": s(1.0, 0.9, bso=0.9),
                "F_words_zipf_noise05": s(1.0, 0.85, bso=0.2)}

    def test_grade_all(self):
        g = K.grade(self._agg())
        p = g["predictions"]
        for k in ("K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K10"):
            self.assertTrue(p[k], k)
        self.assertFalse(p["K9"])
        self.assertEqual(g["rules"]["WR1_whale_controls"], "CONTROLS_PASSED_BY_WORDLESS_SONG")
        self.assertFalse(g["rules"]["WR2_whale_low_power_relabel"])
        self.assertFalse(g["rules"]["WR3_whale_size_caveat"])
        self.assertEqual(g["rules"]["WR4_finch_noise_level_power_below_half"], 0.05)
        self.assertAlmostEqual(g["brier"], 0.131, places=6)

    def test_grade_controls_separate_and_missing(self):
        agg = self._agg()
        agg["W_markov1_a0.2_V12"]["frac_pass_published_controls"] = 0.5
        g = K.grade(agg)
        self.assertEqual(g["rules"]["WR1_whale_controls"], "CONTROLS_SEPARATE_AT_WHALE_SIZE")
        agg["W_markov1_a0.2_V12"]["frac_pass_published_controls"] = 0.9
        agg["W_markov1_a0.2_V12"]["real_r2_mean"] = 0.7
        g = K.grade(agg)
        self.assertEqual(g["rules"]["WR1_whale_controls"], "CONTROLS_PASSED_BUT_LESS_ZIPFIAN")
        del agg["F_words_zipf_noise02"]
        del agg["F_words_zipf_noise05"]
        g = K.grade(agg)
        self.assertIsNone(g["predictions"]["K8"])
        self.assertEqual(g["rules"]["WR4_finch_noise_level_power_below_half"], 0.1)
        g = K.grade({})
        self.assertIsNone(g["rules"]["WR1_whale_controls"])
        self.assertIsNone(g["brier"])


if __name__ == "__main__":
    unittest.main()
