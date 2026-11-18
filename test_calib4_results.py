# SPDX-License-Identifier: Apache-2.0
# test_calib4_results.py: re-derives every number in RESULTS-CALIB-4.md from the published
# per-replicate output of song-zipf-calib4-v1 (stdlib only).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "calib4_results.json")
TASKS = os.path.join(HERE, "results", "calib4_tasks.jsonl")
MD = os.path.join(HERE, "RESULTS-CALIB-4.md")
ALPHA = 0.05
PRIORS = {"Q1": 0.50, "Q2": 0.50, "Q3": 0.50, "Q4": 0.35, "Q5": 0.30, "Q6": 0.85,
          "Q7": 0.50, "Q8": 0.30, "Q9": 0.25, "Q10": 0.80, "Q11": 0.45}
EXPECTED = {"Q1": True, "Q2": True, "Q3": True, "Q4": False, "Q5": True, "Q6": True,
            "Q7": True, "Q8": True, "Q9": True, "Q10": True, "Q11": True}
M1, M1B, M2 = "W_markov1_a0.2_V12", "W_markov1_a0.1_V24", "W_markov2_a0.2_V12"
WU, WB, WA = "W_words_uniform_V12", "W_words_brevity_V12", "W_words_antibrevity_V12"


def load():
    with open(RES, encoding="utf-8") as f:
        res = json.load(f)
    rows = []
    with open(TASKS, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    by = {}
    for r in rows:
        by.setdefault(r["scenario"], []).append(r)
    return res, rows, by


def count(rs, f):
    return sum(1 for r in rs if f(r))


def whale_pass(r, key="pool"):
    return (r["real"]["slope_" + key] < 0
            and r["nulls"]["shuffle"]["r2_" + key]["p"] < ALPHA
            and r["nulls"]["rotate"]["r2_" + key]["p"] < ALPHA)


def beats(r, null, key="pool"):
    return r["nulls"][null]["r2_" + key]["p"] < ALPHA


def mean(v):
    return sum(v) / len(v)


class TestCalib4Results(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res, cls.rows, cls.by = load()
        cls.agg = cls.res["aggregate"]

    def test_complete(self):
        self.assertEqual(len(self.rows), 120)
        self.assertFalse(any(r.get("skipped") for r in self.rows))
        self.assertEqual(len(self.by), 6)
        for sc, rs in self.by.items():
            self.assertEqual(sorted(r["rep"] for r in rs), list(range(20)), sc)
        self.assertEqual(self.res["n_skipped"], 0)

    def test_aggregates_rederived(self):
        for sc, rs in self.by.items():
            a = self.agg[sc]
            for k in ("pool", "year"):
                self.assertAlmostEqual(mean([r["real"]["r2_" + k] for r in rs]),
                                       a["r2_%s_mean" % k], places=9)
                self.assertAlmostEqual(count(rs, lambda r: whale_pass(r, k)) / 20,
                                       a["frac_pass_%s" % k], places=9)
                self.assertAlmostEqual(count(rs, lambda r: r["real"]["slope_" + k] < 0) / 20,
                                       a["frac_slope_%s_neg" % k], places=9)
                for name, n in a["nulls"].items():
                    self.assertAlmostEqual(count(rs, lambda r: beats(r, name, k)) / 20,
                                           n["frac_p_%s_lt_alpha" % k], places=9)
                    self.assertAlmostEqual(mean([r["nulls"][name]["r2_" + k]["z"] for r in rs]),
                                           n["z_%s_mean" % k], places=9)

    def test_table(self):
        # scenario: (mean R^2 3dp, slope<0, pass, z shuffle 1dp, z rotate 1dp, beat m1, beat m2)
        exp = {
            M1: (0.168, 20, 20, 28.3, 14.4, 0, 0),
            M1B: (0.171, 20, 20, 46.8, 10.5, 1, 0),
            M2: (0.087, 20, 20, 85.5, 11.2, 6, 0),
            WU: (0.453, 20, 20, 163.4, 100.9, 20, 20),
            WB: (0.379, 20, 20, 104.9, 41.0, 20, 19),
            WA: (0.205, 20, 18, 52.0, 17.1, 13, 5),
        }
        for sc, (r2, nneg, npass, zs, zr, b1, b2) in exp.items():
            rs = self.by[sc]
            self.assertEqual(round(mean([r["real"]["r2_pool"] for r in rs]), 3), r2, sc)
            self.assertEqual(count(rs, lambda r: r["real"]["slope_pool"] < 0), nneg, sc)
            self.assertEqual(count(rs, whale_pass), npass, sc)
            self.assertEqual(round(mean([r["nulls"]["shuffle"]["r2_pool"]["z"] for r in rs]), 1),
                             zs, sc)
            self.assertEqual(round(mean([r["nulls"]["rotate"]["r2_pool"]["z"] for r in rs]), 1),
                             zr, sc)
            self.assertEqual(count(rs, lambda r: beats(r, "markov1_pooled")), b1, sc)
            self.assertEqual(count(rs, lambda r: beats(r, "markov2_pooled")), b2, sc)

    def test_year_key(self):
        exp = {M1: 19, M1B: 18, M2: 20, WU: 20, WB: 20, WA: 13}
        for sc, n in exp.items():
            self.assertEqual(count(self.by[sc], lambda r: whale_pass(r, "year")), n, sc)
        self.assertEqual(self.res["grading_alternate_year"]["predictions"], EXPECTED)

    def test_sources(self):
        wa = [r["source"]["slope_pool"] for r in self.by[WA]]
        self.assertTrue(all(s > 0 for s in wa))
        self.assertEqual(round(mean(wa), 2), 0.28)
        self.assertTrue(all(r["source"]["slope_pool"] < 0 for r in self.by[WB]))

    def test_grades_rules_brier(self):
        a = self.agg

        def fr(sc, null):
            return a[sc]["nulls"][null]["frac_p_pool_lt_alpha"]
        got = {
            "Q1": a[M1]["frac_pass_pool"] >= 0.80,
            "Q2": a[M1B]["frac_pass_pool"] >= 0.80,
            "Q3": a[M2]["frac_pass_pool"] >= 0.80,
            "Q4": a[M1]["r2_pool_mean"] >= 0.62,
            "Q5": a[M1]["nulls"]["shuffle"]["z_pool_mean"] >= 10.0,
            "Q6": a[WB]["frac_pass_pool"] >= 0.90,
            "Q7": a[WU]["frac_pass_pool"] >= 0.50,
            "Q8": a[WA]["frac_slope_pool_neg"] >= 0.50,
            "Q9": a[WA]["frac_pass_pool"] >= 0.50,
            "Q10": fr(M1, "markov1_pooled") <= 0.15,
            "Q11": fr(WB, "markov2_pooled") >= 0.50,
        }
        self.assertEqual(got, EXPECTED)
        self.assertEqual(self.res["grading"]["predictions"], EXPECTED)
        rules = self.res["grading"]["rules"]
        self.assertEqual(rules["BW1_wordless_song"], "WORDLESS_SONG_PASSES_WHALE_BREVITY_CONTROLS")
        self.assertEqual(sorted(rules["BW1_scenarios"]), sorted([M1, M1B, M2]))
        self.assertTrue(rules["BW2_brevity_reported_for_reversed_units"])
        self.assertTrue(rules["BW3_markov1_null_calibrated"])
        self.assertFalse(rules["BW4_controls_informative"])
        self.assertTrue(rules["sanity"]["words_brevity_source_negative"])
        self.assertTrue(rules["sanity"]["words_antibrevity_source_positive"])
        brier = sum((PRIORS[k] - (1.0 if EXPECTED[k] else 0.0)) ** 2 for k in PRIORS) / 11
        self.assertAlmostEqual(brier, 3.03 / 11, places=9)
        self.assertAlmostEqual(brier, self.res["grading"]["brier"], places=9)
        self.assertEqual(round(brier, 3), 0.275)

    def test_hand_check_rep0(self):
        r = [x for x in self.by[M1] if x["rep"] == 0][0]
        s = r["nulls"]["shuffle"]["r2_pool"]
        z = (r["real"]["r2_pool"] - s["null_mean"]) / s["null_sd"]
        self.assertAlmostEqual(z, s["z"], places=6)
        self.assertEqual(round(z, 2), 23.97)
        self.assertAlmostEqual(s["p"], 1 / 101, places=12)

    def test_md_states_grades(self):
        with open(MD, encoding="utf-8") as f:
            md = f.read()
        for s in ("Brier score **0.275**", "**BW2 also holds.**", "**BW3 holds:**",
                  "`WORDLESS_SONG_PASSES_WHALE_BREVITY_CONTROLS`", "10 of 11 true",
                  "| Q4 | first-order V12: mean R^2 >= 0.62 | 0.35 | **FALSE** (0.168) |"):
            self.assertIn(s, md)


if __name__ == "__main__":
    unittest.main()
