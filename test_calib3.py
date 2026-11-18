# SPDX-License-Identifier: Apache-2.0
# Tests for calib3.py (CALIB-3-PREREG.md). MV2, Munim, Inc. Made with AI agents.
import json
import math
import random
import time
import unittest
from collections import Counter

import calib3 as K


class TestPoissonSlope(unittest.TestCase):
    def test_closed_form_brevity(self):
        # types of length 1 (count 4) and 2 (count 1): sigma(b) = 0.2 -> b = ln 0.25
        b, se = K.poisson_fe_slope([Counter({(0,): 4, (0, 1): 1})])
        self.assertAlmostEqual(b, math.log(0.25), places=6)
        self.assertAlmostEqual(se, 1 / math.sqrt(0.8), places=6)

    def test_closed_form_antibrevity(self):
        b, se = K.poisson_fe_slope([Counter({(0,): 1, (0, 1): 4})])
        self.assertAlmostEqual(b, math.log(4.0), places=6)

    def test_two_groups_cancel(self):
        b, se = K.poisson_fe_slope([Counter({(0,): 4, (0, 1): 1}),
                                    Counter({(2,): 1, (2, 3): 4})])
        self.assertAlmostEqual(b, 0.0, places=9)
        self.assertAlmostEqual(se, 1 / math.sqrt(2.5), places=6)

    def test_single_length_groups_skipped(self):
        b, se = K.poisson_fe_slope([Counter({(0,): 3, (1,): 2}), Counter()])
        self.assertTrue(math.isnan(b))
        self.assertTrue(math.isnan(se))


class TestOls(unittest.TestCase):
    def test_exact_line(self):
        r2, sl = K.ols_r2_slope(Counter({(0,): 4, (0, 1): 2, (0, 1, 2): 1}))
        self.assertAlmostEqual(r2, 1.0, places=9)
        self.assertAlmostEqual(sl, -math.log(2.0), places=9)

    def test_degenerate(self):
        self.assertTrue(math.isnan(K.ols_r2_slope(Counter({(0,): 1, (0, 1): 2}))[0]))
        self.assertTrue(math.isnan(K.ols_r2_slope(Counter({(0,): 2, (1,): 3, (2,): 1}))[0]))
        self.assertTrue(math.isnan(K.ols_r2_slope(Counter({(0,): 2, (1, 2): 2, (3,): 2}))[0]))

    def test_brevity_stats_keys(self):
        st = K.brevity_stats([Counter({(0,): 4, (0, 1): 2, (0, 1, 2): 1})])
        self.assertEqual(set(st), {"r2", "slope", "beta", "beta_se", "wald_z"})
        self.assertLess(st["beta"], 0)
        self.assertLess(st["wald_z"], 0)


class TestGenerators(unittest.TestCase):
    def test_weights(self):
        lex = [(0, 0, 0), (0, 0, 0, 0, 0)]
        self.assertEqual(K.word_weights(lex, "brevity"), [1.0, 0.25])
        self.assertEqual(K.word_weights(lex, "antibrevity"), [1.0, 4.0])
        self.assertEqual(K.word_weights(lex, "uniform"), [1.0, 1.0])
        self.assertEqual(K.word_weights(lex, "zipf"), [1.0, 0.5])

    def test_units_are_complete_prefix(self):
        lex = [(1, 2, 3), (4, 5, 6, 7)]
        for seed in range(10):
            bout, units = K.gen_words_units(lex, [1.0, 1.0], 20, random.Random(seed))
            self.assertEqual(len(bout), 20)
            flat = [s for u in units for s in u]
            self.assertEqual(flat, bout[:len(flat)])
            self.assertTrue(16 < len(flat) <= 20)

    def test_scenarios(self):
        names = [s[0] for s in K.SCENARIOS]
        self.assertEqual(len(names), 7)
        self.assertEqual(len(set(names)), 7)
        seeds = {K.task_seed(n, r) for n in names for r in range(20)}
        self.assertEqual(len(seeds), 140)

    def test_make_dataset(self):
        recs, units = K.make_dataset("words_antibrevity", random.Random(7), n_rec=2)
        self.assertEqual(len(recs), 2)
        self.assertEqual(len(units), 2)
        for rec, inv in zip(recs, units):
            self.assertEqual(len(rec), 10)
            self.assertTrue(all(40 <= len(b) <= 96 for b in rec))
            self.assertTrue(all(0 <= s < 8 for b in rec for s in b))
            self.assertLessEqual(sum(len(k) * v for k, v in inv.items()),
                                 sum(len(b) for b in rec))
        recs, units = K.make_dataset("W_markov1_a0.2_V12", random.Random(7), n_rec=1)
        self.assertIsNone(units)
        self.assertEqual(len(recs[0]), 6)
        self.assertTrue(all(700 <= len(b) <= 1500 for b in recs[0]))
        self.assertTrue(all(0 <= s < 12 for b in recs[0] for s in b))
        a, _ = K.make_dataset("markov1_a0.2", random.Random(3), n_rec=2)
        b, _ = K.make_dataset("markov1_a0.2", random.Random(3), n_rec=2)
        self.assertEqual(a, b)


class TestRunTask(unittest.TestCase):
    def _t(self, deadline_offset=600):
        return dict(scenario="words_brevity", rep=0, B=2,
                    deadline=time.time() + deadline_offset, n_rec=2)

    def test_tiny_task(self):
        r = K.run_task(self._t())
        self.assertFalse(r["skipped"])
        self.assertEqual(set(r["nulls"]), {"shuffle", "bigram_within", "markov1_pooled",
                                           "markov2_pooled", "rotate"})
        self.assertEqual(r["n_rec"], 2)
        self.assertIsNotNone(r["source"])
        self.assertTrue(r["n_chunks"] > 0)
        json.dumps(r)
        r2 = K.run_task(self._t())
        r.pop("seconds")
        r2.pop("seconds")
        self.assertEqual(json.dumps(r, sort_keys=True), json.dumps(r2, sort_keys=True))

    def test_markov_has_no_source(self):
        t = self._t()
        t["scenario"] = "markov1_a0.2"
        r = K.run_task(t)
        self.assertIsNone(r["source"])

    def test_deadline_skips(self):
        self.assertTrue(K.run_task(self._t(-1))["skipped"])


def _row(sc, wz, slope, r2p_sh, r2p_rot):
    nulls = {}
    for name in K.NULLS_USED + ("rotate",):
        nulls[name] = {"r2_z": 1.0, "r2_p": 0.5, "r2_null_mean": 0.3, "beta_brevity_z": 1.0,
                       "beta_p": 0.5, "beta_null_mean": -0.1, "frac_null_sig_brevity": 1.0}
    nulls["shuffle"]["r2_p"] = r2p_sh
    nulls["rotate"]["r2_p"] = r2p_rot
    return {"scenario": sc, "rep": 0, "skipped": False,
            "real": {"r2": 0.5, "slope": slope, "beta": -0.3, "beta_se": 0.05, "wald_z": wz},
            "source": None, "nulls": nulls, "mean_chunk_len": 3.0}


class TestAggregateGrade(unittest.TestCase):
    def test_aggregate(self):
        sc = "markov1_a0.2"
        rs = [_row(sc, -10.0, -1.0, 0.01, 0.01), _row(sc, -10.0, -1.0, 0.01, 0.01),
              _row(sc, -3.0, -1.0, 0.5, 0.01), _row(sc, 5.0, 1.0, 0.01, 0.01),
              {"scenario": sc, "rep": 9, "skipped": True}]
        a = K.aggregate(rs)[sc]
        self.assertEqual(a["n_reps"], 4)
        self.assertAlmostEqual(a["frac_sig_brevity"], 0.5)
        self.assertAlmostEqual(a["frac_sig_antibrevity"], 0.25)
        self.assertAlmostEqual(a["frac_pass_whale_controls"], 0.5)
        self.assertAlmostEqual(a["nulls"]["shuffle"]["frac_r2_p_lt_alpha"], 0.75)
        self.assertAlmostEqual(a["nulls"]["shuffle"]["frac_null_sig_brevity_mean"], 1.0)

    @staticmethod
    def _s(sig=0.0, anti=0.0, whale=0.0, sh_null_sig=0.0, m1_bp=0.0, m2_bp=0.0,
           src_pos=None, src_neg=None):
        a = {"frac_sig_brevity": sig, "frac_sig_antibrevity": anti,
             "frac_pass_whale_controls": whale,
             "nulls": {"shuffle": {"frac_null_sig_brevity_mean": sh_null_sig},
                       "markov1_pooled": {"frac_beta_p_lt_alpha": m1_bp},
                       "markov2_pooled": {"frac_beta_p_lt_alpha": m2_bp}}}
        if src_pos is not None:
            a["frac_source_beta_pos"] = src_pos
            a["frac_source_beta_neg"] = src_neg
        return a

    def _agg(self):
        s = self._s
        return {"markov1_a0.2": s(sig=1.0, whale=0.9, sh_null_sig=0.95, m1_bp=0.05),
                "W_markov1_a0.2_V12": s(whale=0.5),
                "words_brevity": s(sig=0.95, m2_bp=0.6, src_pos=0.0, src_neg=1.0),
                "words_uniform": s(sig=0.7),
                "words_antibrevity": s(sig=0.6, anti=0.1, src_pos=1.0, src_neg=0.0)}

    def test_grade(self):
        g = K.grade(self._agg())
        p = g["predictions"]
        for k in ("P1", "P2", "P4", "P5", "P6", "P8", "P9", "P10"):
            self.assertTrue(p[k], k)
        for k in ("P3", "P7"):
            self.assertFalse(p[k], k)
        r = g["rules"]
        self.assertTrue(r["BR1_glmm_brevity_uninformative"])
        self.assertEqual(r["BR2_whale_brevity_controls"],
                         "BREVITY_CONTROLS_PASSED_BY_WORDLESS_SONG_AT_ONE_SIZE")
        self.assertTrue(r["BR3_pipeline_reverses_true_relation"])
        self.assertFalse(r["BR4_pipeline_tracks_source_sign"])
        self.assertAlmostEqual(g["brier"], 0.16925, places=9)

    def test_grade_other_branches(self):
        agg = self._agg()
        agg["markov1_a0.2"]["frac_pass_whale_controls"] = 0.1
        agg["words_antibrevity"]["frac_source_beta_pos"] = 0.9
        g = K.grade(agg)
        self.assertEqual(g["rules"]["BR2_whale_brevity_controls"], "BREVITY_CONTROLS_SEPARATE")
        self.assertTrue(g["predictions"]["P6"])
        self.assertFalse(g["rules"]["BR3_pipeline_reverses_true_relation"])
        agg["markov1_a0.2"]["frac_pass_whale_controls"] = 0.9
        agg["W_markov1_a0.2_V12"]["frac_pass_whale_controls"] = 0.85
        g = K.grade(agg)
        self.assertEqual(g["rules"]["BR2_whale_brevity_controls"],
                         "BREVITY_CONTROLS_PASSED_BY_WORDLESS_SONG")

    def test_grade_empty(self):
        g = K.grade({})
        self.assertTrue(all(v is None for v in g["predictions"].values()))
        self.assertIsNone(g["rules"]["BR1_glmm_brevity_uninformative"])
        self.assertIsNone(g["rules"]["BR2_whale_brevity_controls"])
        self.assertIsNone(g["rules"]["BR3_pipeline_reverses_true_relation"])
        self.assertIsNone(g["rules"]["BR4_pipeline_tracks_source_sign"])
        self.assertIsNone(g["brier"])


if __name__ == "__main__":
    unittest.main()
