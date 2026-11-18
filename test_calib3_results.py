# SPDX-License-Identifier: Apache-2.0
# test_calib3_results.py: re-derives every number in RESULTS-CALIB-3.md from the published
# per-replicate output of song-zipf-calib3-v1 (stdlib only).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "calib3_results.json")
TASKS = os.path.join(HERE, "results", "calib3_tasks.jsonl")
MD = os.path.join(HERE, "RESULTS-CALIB-3.md")
ALPHA = 0.05
Z_SIG = 4.42
PRIORS = {"P1": 0.85, "P2": 0.45, "P3": 0.50, "P4": 0.90, "P5": 0.60, "P6": 0.35,
          "P7": 0.40, "P8": 0.85, "P9": 0.80, "P10": 0.45}
EXPECTED = {"P1": True, "P2": False, "P3": True, "P4": True, "P5": True, "P6": True,
            "P7": False, "P8": True, "P9": True, "P10": False}


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


def sig_b(r):
    return r["real"]["wald_z"] <= -Z_SIG


def sig_a(r):
    return r["real"]["wald_z"] >= Z_SIG


def whale_pass(r):
    return (r["real"]["slope"] < 0 and r["nulls"]["shuffle"]["r2_p"] < ALPHA
            and r["nulls"]["rotate"]["r2_p"] < ALPHA)


class TestCalib3Results(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res, cls.rows, cls.by = load()
        cls.agg = cls.res["aggregate"]

    def test_complete(self):
        self.assertEqual(len(self.rows), 140)
        self.assertFalse(any(r.get("skipped") for r in self.rows))
        self.assertEqual(len(self.by), 7)
        for sc, rs in self.by.items():
            self.assertEqual(sorted(r["rep"] for r in rs), list(range(20)), sc)
        self.assertEqual(self.res["n_skipped"], 0)

    def test_aggregates_rederived(self):
        for sc, rs in self.by.items():
            a = self.agg[sc]
            self.assertAlmostEqual(sum(r["real"]["beta"] for r in rs) / 20, a["beta_mean"], places=9)
            self.assertAlmostEqual(count(rs, sig_b) / 20, a["frac_sig_brevity"], places=9)
            self.assertAlmostEqual(count(rs, sig_a) / 20, a["frac_sig_antibrevity"], places=9)
            self.assertAlmostEqual(count(rs, whale_pass) / 20, a["frac_pass_whale_controls"],
                                   places=9)
            for name, n in a["nulls"].items():
                self.assertAlmostEqual(count(rs, lambda r: r["nulls"][name]["beta_p"] < ALPHA) / 20,
                                       n["frac_beta_p_lt_alpha"], places=9)

    def test_table(self):
        exp = {  # scenario: (mean beta 3dp, sig brevity, sig anti, whale controls passed)
            "markov1_a0.2": (-0.111, 20, 0, 9),
            "markov2_a0.2": (-0.037, 20, 0, 20),
            "words_zipf": (-0.100, 20, 0, 12),
            "words_uniform": (-0.128, 20, 0, 20),
            "words_brevity": (-0.160, 20, 0, 20),
            "words_antibrevity": (-0.085, 20, 0, 5),
            "W_markov1_a0.2_V12": (-0.327, 20, 0, 18),
        }
        for sc, (b, nb, na, nw) in exp.items():
            rs = self.by[sc]
            self.assertEqual(round(sum(r["real"]["beta"] for r in rs) / 20, 3), b, sc)
            self.assertEqual(count(rs, sig_b), nb, sc)
            self.assertEqual(count(rs, sig_a), na, sc)
            self.assertEqual(count(rs, whale_pass), nw, sc)

    def test_headline_antibrevity(self):
        rs = self.by["words_antibrevity"]
        self.assertTrue(all(r["source"]["beta"] > 0 for r in rs))
        self.assertEqual(round(sum(r["source"]["beta"] for r in rs) / 20, 2), 0.66)
        self.assertEqual(round(sum(r["real"]["wald_z"] for r in rs) / 20, 1), -18.3)
        self.assertTrue(all(r["source"]["beta"] < 0 for r in self.by["words_brevity"]))
        m1 = self.agg["markov1_a0.2"]["nulls"]["shuffle"]["frac_null_sig_brevity_mean"]
        self.assertEqual(m1, 1.0)

    def test_markov_null_power(self):
        def nbeat(sc, null):
            return count(self.by[sc], lambda r: r["nulls"][null]["beta_p"] < ALPHA)
        self.assertEqual(nbeat("markov1_a0.2", "markov1_pooled"), 0)
        self.assertEqual(nbeat("words_brevity", "markov2_pooled"), 0)
        self.assertEqual(nbeat("words_brevity", "bigram_within"), 16)
        self.assertEqual(nbeat("words_antibrevity", "bigram_within"), 0)

    def test_grades_rules_brier(self):
        a = self.agg
        got = {
            "P1": a["markov1_a0.2"]["frac_sig_brevity"] >= 0.90,
            "P2": a["markov1_a0.2"]["frac_pass_whale_controls"] >= 0.80,
            "P3": a["W_markov1_a0.2_V12"]["frac_pass_whale_controls"] >= 0.80,
            "P4": a["words_brevity"]["frac_sig_brevity"] >= 0.90,
            "P5": a["words_uniform"]["frac_sig_brevity"] >= 0.50,
            "P6": a["words_antibrevity"]["frac_sig_brevity"] >= 0.50,
            "P7": a["words_antibrevity"]["frac_sig_antibrevity"] >= 0.50,
            "P8": a["markov1_a0.2"]["nulls"]["shuffle"]["frac_null_sig_brevity_mean"] >= 0.90,
            "P9": a["markov1_a0.2"]["nulls"]["markov1_pooled"]["frac_beta_p_lt_alpha"] <= 0.15,
            "P10": a["words_brevity"]["nulls"]["markov2_pooled"]["frac_beta_p_lt_alpha"] >= 0.50,
        }
        self.assertEqual(got, EXPECTED)
        self.assertEqual(self.res["grading"]["predictions"], EXPECTED)
        rules = self.res["grading"]["rules"]
        self.assertTrue(rules["BR1_glmm_brevity_uninformative"])
        self.assertEqual(rules["BR2_whale_brevity_controls"],
                         "BREVITY_CONTROLS_PASSED_BY_WORDLESS_SONG_AT_ONE_SIZE")
        self.assertTrue(rules["BR3_pipeline_reverses_true_relation"])
        self.assertFalse(rules["BR4_pipeline_tracks_source_sign"])
        self.assertTrue(rules["sanity"]["words_brevity_source_negative"])
        self.assertTrue(rules["sanity"]["words_antibrevity_source_positive"])
        brier = sum((PRIORS[k] - (1.0 if EXPECTED[k] else 0.0)) ** 2 for k in PRIORS) / 10
        self.assertAlmostEqual(brier, 0.14925, places=9)
        self.assertEqual(round(brier, 3), 0.149)

    def test_hand_check_rep0(self):
        r = [x for x in self.by["words_antibrevity"] if x["rep"] == 0][0]
        self.assertEqual(r["seed"], 20266119)
        self.assertAlmostEqual(r["real"]["beta"] / r["real"]["beta_se"], r["real"]["wald_z"],
                               places=6)
        self.assertTrue(sig_b(r))
        self.assertGreater(r["source"]["beta"], 0)

    def test_md_states_grades(self):
        with open(MD, encoding="utf-8") as f:
            md = f.read()
        for s in ("Brier score **0.149**", "**BR3 holds**", "**BR1 holds**",
                  "**significant brevity in 20 of 20 replicates**", "**TRUE (20/20)**"):
            self.assertIn(s, md)


if __name__ == "__main__":
    unittest.main()
