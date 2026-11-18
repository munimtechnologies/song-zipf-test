# SPDX-License-Identifier: Apache-2.0
# test_calib2_results.py: re-derives every number in RESULTS-CALIB-2.md from the published
# per-replicate output of song-zipf-calib2-v1 (stdlib only).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "calib2_results.json")
TASKS = os.path.join(HERE, "results", "calib2_tasks.jsonl")
MD = os.path.join(HERE, "RESULTS-CALIB-2.md")
ALPHA = 0.05
PRIORS = {"K1": 0.80, "K2": 0.55, "K3": 0.45, "K4": 0.80, "K5": 0.75, "K6": 0.80,
          "K7": 0.50, "K8": 0.65, "K9": 0.40, "K10": 0.70}
EXPECTED = {"K1": True, "K2": True, "K3": True, "K4": True, "K5": True, "K6": False,
            "K7": False, "K8": True, "K9": True, "K10": True}
BSO = "BEYOND_SECOND_ORDER"


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


def label(r):
    if r["nulls"]["markov2_pooled"]["p"] < ALPHA:
        return BSO
    if r["nulls"]["markov1_pooled"]["p"] < ALPHA:
        return "EXPLAINED_BY_SECOND_ORDER"
    return "EXPLAINED_BY_FIRST_ORDER"


def count(rs, f):
    return sum(1 for r in rs if f(r))


def both(r):
    return r["nulls"]["shuffle"]["p"] < ALPHA and r["nulls"]["rotate"]["p"] < ALPHA


class TestCalib2Results(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res, cls.rows, cls.by = load()

    def test_complete(self):
        self.assertEqual(len(self.rows), 140)
        self.assertFalse(any(r.get("skipped") for r in self.rows))
        self.assertEqual(len(self.by), 7)
        for sc, rs in self.by.items():
            self.assertEqual(sorted(r["rep"] for r in rs), list(range(20)), sc)
        self.assertEqual(self.res["n_skipped"], 0)

    def test_labels_follow_rule(self):
        for r in self.rows:
            self.assertEqual(label(r), r["label"], (r["scenario"], r["rep"]))

    def test_aggregates_rederived(self):
        agg = self.res["aggregate"]
        for sc, rs in self.by.items():
            a = agg[sc]
            self.assertAlmostEqual(sum(r["real_r2"] for r in rs) / 20, a["real_r2_mean"], places=9)
            self.assertAlmostEqual(count(rs, both) / 20, a["frac_pass_published_controls"],
                                   places=9)
            for name in ("shuffle", "bigram_within", "markov1_pooled", "markov2_pooled", "rotate"):
                fr = count(rs, lambda r: r["nulls"][name]["p"] < ALPHA) / 20
                self.assertAlmostEqual(fr, a["nulls"][name]["frac_p_lt_alpha"], places=9)
            self.assertAlmostEqual(count(rs, lambda r: r["label"] == BSO) / 20,
                                   a["frac_beyond_second_order"], places=9)
            self.assertAlmostEqual(count(rs, lambda r: r["real_r2"] >= 0.93) / 20,
                                   a["frac_real_r2_ge_0.93"], places=9)

    def test_table(self):
        b = self.by
        exp = {  # scenario: (mean R^2 3dp, pass both, BEYOND count, {label: count})
            "W_markov1_a0.2_V12": (0.917, 20, 0, {"EXPLAINED_BY_FIRST_ORDER": 20}),
            "W_markov1_a0.1_V24": (0.910, 20, 0, {"EXPLAINED_BY_FIRST_ORDER": 20}),
            "W_markov2_a0.2_V12": (0.692, 20, 0, {"EXPLAINED_BY_SECOND_ORDER": 18,
                                                  "EXPLAINED_BY_FIRST_ORDER": 2}),
            "W_words_zipf_V12": (0.916, 10, 0, {"EXPLAINED_BY_FIRST_ORDER": 11,
                                                "EXPLAINED_BY_SECOND_ORDER": 9}),
            "W_words_zipf_noise10_V12": (0.910, 20, 2, {"EXPLAINED_BY_SECOND_ORDER": 17,
                                                        "EXPLAINED_BY_FIRST_ORDER": 1, BSO: 2}),
            "F_words_zipf_noise02": (0.903, 20, 20, {BSO: 20}),
            "F_words_zipf_noise05": (0.868, 20, 17, {BSO: 17, "EXPLAINED_BY_SECOND_ORDER": 3}),
        }
        for sc, (r2, nb, nbso, labs) in exp.items():
            rs = b[sc]
            self.assertEqual(round(sum(r["real_r2"] for r in rs) / 20, 3), r2, sc)
            self.assertEqual(count(rs, both), nb, sc)
            self.assertEqual(count(rs, lambda r: r["label"] == BSO), nbso, sc)
            got = {}
            for r in rs:
                got[r["label"]] = got.get(r["label"], 0) + 1
            self.assertEqual(got, labs, sc)

    def test_headline_numbers(self):
        agg = self.res["aggregate"]
        m1 = self.by["W_markov1_a0.2_V12"]
        self.assertEqual(round(min(r["real_r2"] for r in m1), 3), 0.894)
        self.assertEqual(round(max(r["real_r2"] for r in m1), 3), 0.935)
        self.assertEqual(count(m1, lambda r: r["real_r2"] >= 0.93), 2)
        self.assertEqual(round(agg["W_markov1_a0.2_V12"]["nulls"]["shuffle"]["z_mean"], 1), 24.7)
        self.assertEqual(round(agg["W_markov1_a0.2_V12"]["nulls"]["rotate"]["z_mean"], 1), 21.4)
        self.assertEqual(count(m1, lambda r: r["nulls"]["bigram_within"]["p"] < ALPHA), 1)
        m1b = self.by["W_markov1_a0.1_V24"]
        self.assertEqual(count(m1b, lambda r: r["nulls"]["bigram_within"]["p"] < ALPHA), 0)
        w = agg["W_words_zipf_V12"]
        self.assertEqual(round(w["nulls"]["markov2_pooled"]["null_r2_mean"], 3), 0.946)
        self.assertEqual(round(w["real_r2_mean"], 3), 0.916)
        self.assertEqual(round(agg["W_markov1_a0.2_V12"]["cuts_per_recording_mean"]), 1699)

    def test_grades_rules_brier(self):
        agg = self.res["aggregate"]
        m1, m1b, m2 = "W_markov1_a0.2_V12", "W_markov1_a0.1_V24", "W_markov2_a0.2_V12"
        got = {
            "K1": agg[m1]["frac_pass_published_controls"] >= 0.80,
            "K2": agg[m1]["real_r2_mean"] >= 0.80,
            "K3": agg[m1b]["frac_pass_published_controls"] >= 0.80
            and agg[m1b]["real_r2_mean"] >= 0.80,
            "K4": agg[m1]["nulls"]["markov1_pooled"]["frac_p_lt_alpha"] <= 0.15,
            "K5": agg[m2]["frac_beyond_second_order"] <= 0.15,
            "K6": agg["W_words_zipf_V12"]["frac_beyond_second_order"] >= 0.50,
            "K7": agg["W_words_zipf_noise10_V12"]["frac_beyond_second_order"] >= 0.50,
            "K8": agg["F_words_zipf_noise02"]["frac_beyond_second_order"] >= 0.50,
            "K9": agg["F_words_zipf_noise05"]["frac_beyond_second_order"] >= 0.50,
            "K10": agg[m1]["nulls"]["bigram_within"]["frac_p_lt_alpha"] <= 0.15,
        }
        self.assertEqual(got, EXPECTED)
        self.assertEqual(self.res["grading"]["predictions"], EXPECTED)
        rules = self.res["grading"]["rules"]
        self.assertEqual(rules["WR1_whale_controls"], "CONTROLS_PASSED_BY_WORDLESS_SONG")
        self.assertTrue(rules["WR2_whale_low_power_relabel"])
        self.assertFalse(rules["WR3_whale_size_caveat"])
        self.assertEqual(rules["WR4_finch_noise_level_power_below_half"], 0.1)
        brier = sum((PRIORS[k] - (1.0 if EXPECTED[k] else 0.0)) ** 2 for k in PRIORS) / 10
        self.assertAlmostEqual(brier, 0.211, places=9)
        self.assertAlmostEqual(self.res["grading"]["brier"], 0.211, places=9)

    def test_hand_check_rep0(self):
        r = [x for x in self.by["W_markov1_a0.2_V12"] if x["rep"] == 0][0]
        self.assertEqual(r["seed"], 20261118)
        for name in ("shuffle", "rotate"):
            n = r["nulls"][name]
            self.assertAlmostEqual((r["real_r2"] - n["null_mean"]) / n["null_sd"], n["z"], places=6)
            self.assertAlmostEqual(n["p"], 1 / 101, places=12)
        self.assertEqual(r["label"], "EXPLAINED_BY_FIRST_ORDER")

    def test_md_states_grades(self):
        with open(MD, encoding="utf-8") as f:
            md = f.read()
        for s in ("Brier score **0.211**", "| K6 |", "**FALSE** (0/20)", "**20 of 20**",
                  "`CONTROLS_PASSED_BY_WORDLESS_SONG`", "`NOT_DISTINGUISHABLE`"):
            self.assertIn(s, md)


if __name__ == "__main__":
    unittest.main()
