# SPDX-License-Identifier: Apache-2.0
# Tests for calib4.py (CALIB-4-PREREG.md). Stdlib only.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import math
import random
import time
import unittest
from collections import Counter

import calib4 as K

M1, M1B, M2 = "W_markov1_a0.2_V12", "W_markov1_a0.1_V24", "W_markov2_a0.2_V12"
WB, WU, WA = "W_words_brevity_V12", "W_words_uniform_V12", "W_words_antibrevity_V12"


class TestOls(unittest.TestCase):
    def test_exact_line(self):
        r2, sl = K.ols_points([(1, 2.0), (2, 1.0), (3, 0.0)])
        self.assertAlmostEqual(r2, 1.0, places=12)
        self.assertAlmostEqual(sl, -1.0, places=12)

    def test_degenerate(self):
        self.assertTrue(math.isnan(K.ols_points([(1, 1.0), (2, 0.0)])[0]))
        self.assertTrue(math.isnan(K.ols_points([(1, 1.0), (1, 0.0), (1, 2.0)])[0]))
        self.assertTrue(math.isnan(K.ols_points([(1, 1.0), (2, 1.0), (3, 1.0)])[1]))

    def test_pooled_closed_form(self):
        # pooled counts 1000, 100, 1 at lengths 1, 2, 3 -> points (1,3) (2,2) (3,0):
        # sxx = 2, sxy = -3, syy = 42/9 -> slope -1.5, R^2 = 9 / (2 * 42/9) = 81/84
        invs = [Counter({(0,): 100, (0, 1): 10}),
                Counter({(0,): 900, (1, 2, 3): 1, (0, 1): 90})]
        r2, sl = K.brevity_pooled(invs)
        self.assertAlmostEqual(sl, -1.5, places=9)
        self.assertAlmostEqual(r2, 81.0 / 84.0, places=9)

    def test_pool_and_year_on_identical_years(self):
        inv = Counter({(0,): 100, (0, 1): 10, (0, 1, 2): 1})
        st = K.stats([inv, Counter(inv)])
        self.assertEqual(set(st), {"r2_pool", "slope_pool", "r2_year", "slope_year"})
        for k in ("pool", "year"):
            self.assertAlmostEqual(st["r2_" + k], 1.0, places=9)
            self.assertAlmostEqual(st["slope_" + k], -1.0, places=9)


class TestCompare(unittest.TestCase):
    def test_cmp(self):
        c = K._cmp(5.0, [1.0, 2.0, 3.0, float("nan")])
        self.assertAlmostEqual(c["null_mean"], 2.0)
        self.assertAlmostEqual(c["null_sd"], math.sqrt(2.0 / 3.0))
        self.assertAlmostEqual(c["z"], 3.0 / math.sqrt(2.0 / 3.0))
        self.assertAlmostEqual(c["p"], 0.25)
        self.assertEqual(c["n_null"], 3)
        self.assertAlmostEqual(K._cmp(2.0, [1.0, 2.0, 3.0])["p"], 0.75)
        self.assertTrue(math.isnan(K._cmp(float("nan"), [1.0, 2.0])["z"]))

    def test_null_summary(self):
        nan = float("nan")
        real = {"r2_pool": 0.5, "slope_pool": -1.0, "r2_year": 0.4, "slope_year": -1.0}
        st = [{"r2_pool": 0.1, "slope_pool": -1.0, "r2_year": 0.1, "slope_year": 0.0},
              {"r2_pool": 0.3, "slope_pool": 1.0, "r2_year": 0.5, "slope_year": 0.0},
              {"r2_pool": nan, "slope_pool": nan, "r2_year": nan, "slope_year": nan}]
        s = K._null_summary(real, st)
        self.assertAlmostEqual(s["r2_pool"]["z"], 3.0, places=9)
        self.assertAlmostEqual(s["r2_pool"]["p"], 1.0 / 3.0)
        self.assertAlmostEqual(s["r2_year"]["z"], 0.5, places=9)
        self.assertAlmostEqual(s["r2_year"]["p"], 2.0 / 3.0)
        self.assertAlmostEqual(s["slope_pool_null_mean"], 0.0)
        self.assertAlmostEqual(s["frac_null_slope_pool_neg"], 0.5)


class TestGenerators(unittest.TestCase):
    def test_weights(self):
        lex = [(0, 0, 0), (0, 0, 0, 0, 0)]
        self.assertEqual(K.word_weights(lex, "brevity"), [1.0, 0.25])
        self.assertEqual(K.word_weights(lex, "antibrevity"), [1.0, 4.0])
        self.assertEqual(K.word_weights(lex, "uniform"), [1.0, 1.0])
        with self.assertRaises(ValueError):
            K.word_weights(lex, "zipf")

    def test_units_are_complete_prefix(self):
        lex = [(1, 2, 3), (4, 5, 6, 7)]
        for seed in range(10):
            seq, units = K.gen_words_units(lex, [1.0, 1.0], 20, random.Random(seed))
            self.assertEqual(len(seq), 20)
            flat = [s for u in units for s in u]
            self.assertEqual(flat, seq[:len(flat)])
            self.assertTrue(16 < len(flat) <= 20)

    def test_scenarios(self):
        names = [s[0] for s in K.SCENARIOS]
        self.assertEqual(names, [M1, M1B, M2, WU, WB, WA])
        seeds = {K.task_seed(n, r) for n in names for r in range(20)}
        self.assertEqual(len(seeds), 120)

    def test_make_dataset_words(self):
        recs, units = K.make_dataset(WA, random.Random(7), n_years=2, lmin=50, lmax=60)
        self.assertEqual(len(recs), 2)
        self.assertEqual(len(units), 2)
        for rec, inv in zip(recs, units):
            self.assertEqual(len(rec), 1)
            self.assertTrue(50 <= len(rec[0]) <= 60)
            self.assertTrue(all(0 <= s < 12 for s in rec[0]))
            used = sum(len(k) * v for k, v in inv.items())
            self.assertTrue(len(rec[0]) - 7 < used <= len(rec[0]))

    def test_make_dataset_markov(self):
        recs, units = K.make_dataset(M1B, random.Random(3), n_years=2, lmin=50, lmax=60)
        self.assertIsNone(units)
        self.assertTrue(all(0 <= s < 24 for r in recs for s in r[0]))
        a, _ = K.make_dataset(M2, random.Random(3), n_years=2, lmin=50, lmax=60)
        b, _ = K.make_dataset(M2, random.Random(3), n_years=2, lmin=50, lmax=60)
        self.assertEqual(a, b)
        self.assertTrue(all(0 <= s < 12 for r in a for s in r[0]))


class TestRunTask(unittest.TestCase):
    def _t(self, sc=WB, deadline_offset=600):
        return dict(scenario=sc, rep=0, B=2, deadline=time.time() + deadline_offset,
                    n_years=3, lmin=80, lmax=120)

    def test_tiny_task(self):
        r = K.run_task(self._t())
        self.assertFalse(r["skipped"])
        self.assertEqual(set(r["nulls"]), {"shuffle", "markov1_pooled", "markov2_pooled",
                                           "rotate"})
        self.assertEqual(r["n_years"], 3)
        self.assertIsNotNone(r["source"])
        self.assertTrue(r["n_chunks"] > 0)
        self.assertTrue(240 <= r["n_symbols"] <= 360)
        json.dumps(r)
        r2 = K.run_task(self._t())
        r.pop("seconds")
        r2.pop("seconds")
        self.assertEqual(json.dumps(r, sort_keys=True), json.dumps(r2, sort_keys=True))

    def test_markov_has_no_source(self):
        self.assertIsNone(K.run_task(self._t(M1))["source"])

    def test_deadline_skips(self):
        self.assertTrue(K.run_task(self._t(WB, -1))["skipped"])


def _nul(p):
    c = {"z": 2.0, "p": p, "null_mean": 0.3, "null_sd": 0.1, "n_null": 100}
    return {"r2_pool": dict(c), "r2_year": dict(c), "slope_pool_null_mean": -0.2,
            "frac_null_slope_pool_neg": 1.0}


def _row(sc, slope, p_sh, p_rot, src_slope):
    return {"scenario": sc, "rep": 0, "skipped": False,
            "real": {"r2_pool": 0.5, "slope_pool": slope, "r2_year": 0.4, "slope_year": slope},
            "source": {"r2_pool": 0.9, "slope_pool": src_slope},
            "nulls": {"shuffle": _nul(p_sh), "markov1_pooled": _nul(0.5),
                      "markov2_pooled": _nul(0.5), "rotate": _nul(p_rot)},
            "n_types_pool": 100, "mean_chunk_len": 4.0}


def _s(fp=0.0, r2=0.0, zsh=0.0, neg=0.0, m1=0.0, m2=0.0, src_pos=None, src_neg=None):
    a = {"frac_pass_pool": fp, "r2_pool_mean": r2, "frac_slope_pool_neg": neg,
         "nulls": {"shuffle": {"z_pool_mean": zsh},
                   "markov1_pooled": {"frac_p_pool_lt_alpha": m1},
                   "markov2_pooled": {"frac_p_pool_lt_alpha": m2}}}
    if src_pos is not None:
        a["frac_source_slope_pos"] = src_pos
        a["frac_source_slope_neg"] = src_neg
    return a


def _key(k):
    # statistic keys only ("frac_pass_pool", "z_pool_mean", ...), never "markov1_pooled"
    k = k.replace("_pool_", "_year_")
    return k[:-5] + "_year" if k.endswith("_pool") else k


def _rekey(x):
    if isinstance(x, dict):
        return {_key(k): _rekey(v) for k, v in x.items()}
    return x


class TestAggregateGrade(unittest.TestCase):
    def test_aggregate(self):
        rs = [_row(M1, -1.0, 0.01, 0.01, 0.5), _row(M1, -1.0, 0.01, 0.01, 0.5),
              _row(M1, -1.0, 0.5, 0.01, -0.5), _row(M1, 1.0, 0.01, 0.01, 0.5),
              {"scenario": M1, "rep": 9, "skipped": True}]
        a = K.aggregate(rs)[M1]
        self.assertEqual(a["n_reps"], 4)
        self.assertAlmostEqual(a["frac_pass_pool"], 0.5)
        self.assertAlmostEqual(a["frac_pass_year"], 0.5)
        self.assertAlmostEqual(a["frac_slope_pool_neg"], 0.75)
        self.assertAlmostEqual(a["r2_pool_mean"], 0.5)
        self.assertAlmostEqual(a["r2_year_mean"], 0.4)
        self.assertAlmostEqual(a["nulls"]["shuffle"]["frac_p_pool_lt_alpha"], 0.75)
        self.assertAlmostEqual(a["nulls"]["rotate"]["frac_p_pool_lt_alpha"], 1.0)
        self.assertAlmostEqual(a["nulls"]["markov1_pooled"]["frac_p_pool_lt_alpha"], 0.0)
        self.assertAlmostEqual(a["nulls"]["shuffle"]["z_pool_mean"], 2.0)
        self.assertAlmostEqual(a["nulls"]["shuffle"]["frac_null_slope_pool_neg_mean"], 1.0)
        self.assertAlmostEqual(a["frac_source_slope_pos"], 0.75)
        self.assertAlmostEqual(a["frac_source_slope_neg"], 0.25)
        self.assertAlmostEqual(a["source_slope_pool_mean"], 0.25)

    def _agg(self):
        return {M1: _s(fp=0.9, r2=0.5, zsh=12.0, m1=0.05), M1B: _s(fp=0.7), M2: _s(fp=0.8),
                WB: _s(fp=0.95, m2=0.2, src_pos=0.0, src_neg=1.0), WU: _s(fp=0.4),
                WA: _s(fp=0.55, neg=0.6, src_pos=1.0, src_neg=0.0)}

    def test_grade(self):
        g = K.grade(self._agg())
        p = g["predictions"]
        for k in ("Q1", "Q3", "Q5", "Q6", "Q8", "Q9", "Q10"):
            self.assertTrue(p[k], k)
        for k in ("Q2", "Q4", "Q7", "Q11"):
            self.assertFalse(p[k], k)
        r = g["rules"]
        self.assertEqual(r["BW1_wordless_song"], "WORDLESS_SONG_PASSES_WHALE_BREVITY_CONTROLS")
        self.assertEqual(r["BW1_scenarios"], [M1, M2])
        self.assertTrue(r["BW2_brevity_reported_for_reversed_units"])
        self.assertTrue(r["BW3_markov1_null_calibrated"])
        self.assertFalse(r["BW4_controls_informative"])
        self.assertAlmostEqual(g["brier"], 2.93 / 11.0, places=9)

    def test_grade_year_key(self):
        gp = K.grade(self._agg(), "pool")
        gy = K.grade(_rekey(self._agg()), "year")
        self.assertEqual(gy["key"], "year")
        self.assertEqual(gp["predictions"], gy["predictions"])
        self.assertAlmostEqual(gp["brier"], gy["brier"], places=12)

    def test_grade_other_branches(self):
        agg = self._agg()
        agg[M1]["frac_pass_pool"] = 0.1
        agg[M2]["frac_pass_pool"] = 0.1
        agg[WA]["frac_pass_pool"] = 0.1
        g = K.grade(agg)
        self.assertEqual(g["rules"]["BW1_wordless_song"],
                         "WHALE_BREVITY_CONTROLS_REJECT_WORDLESS_SONG")
        self.assertEqual(g["rules"]["BW1_scenarios"], [])
        self.assertFalse(g["rules"]["BW2_brevity_reported_for_reversed_units"])
        self.assertTrue(g["rules"]["BW4_controls_informative"])
        agg = self._agg()
        agg[WA]["frac_source_slope_pos"] = 0.9
        g = K.grade(agg)
        self.assertTrue(g["predictions"]["Q8"] and g["predictions"]["Q9"])
        self.assertFalse(g["rules"]["BW2_brevity_reported_for_reversed_units"])

    def test_grade_empty(self):
        g = K.grade({})
        self.assertTrue(all(v is None for v in g["predictions"].values()))
        self.assertIsNone(g["rules"]["BW1_wordless_song"])
        self.assertEqual(g["rules"]["BW1_scenarios"], [])
        self.assertIsNone(g["rules"]["BW2_brevity_reported_for_reversed_units"])
        self.assertIsNone(g["rules"]["BW3_markov1_null_calibrated"])
        self.assertIsNone(g["rules"]["BW4_controls_informative"])
        self.assertIsNone(g["brier"])


if __name__ == "__main__":
    unittest.main()
