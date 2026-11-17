# SPDX-License-Identifier: Apache-2.0
# test_calib_results.py: re-derives every number in RESULTS-CALIB.md from the
# published per-replicate output of song-zipf-calib-v1 (stdlib only).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "calib_results.json")
TASKS = os.path.join(HERE, "results", "calib_tasks.jsonl")
MD = os.path.join(HERE, "RESULTS-CALIB.md")
ALPHA = 0.05
PRIORS = {"C1": 0.55, "C2": 0.65, "C3": 0.75, "C4": 0.70, "C5": 0.50, "C6": 0.40, "C7": 0.35}
EXPECTED = {"C1": True, "C2": True, "C3": True, "C4": True, "C5": True, "C6": True, "C7": False}
KEYS = {"C1": "C1_markov1_a0.2_mean_r2_ge_0.80",
        "C2": "C2_markov1_a0.2_pass_published_controls_ge_0.80",
        "C3": "C3_markov1_a0.2_markov1_null_rejects_le_0.15",
        "C4": "C4_markov2_a0.2_beyond_second_order_le_0.15",
        "C5": "C5_words_zipf_beyond_second_order_ge_0.50",
        "C6": "C6_words_uniform_mean_r2_ge_0.80",
        "C7": "C7_words_zipf_noise10_beyond_second_order_ge_0.50"}


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
        return "BEYOND_SECOND_ORDER"
    if r["nulls"]["markov1_pooled"]["p"] < ALPHA:
        return "EXPLAINED_BY_SECOND_ORDER"
    return "EXPLAINED_BY_FIRST_ORDER"


def frac(rs, f):
    return sum(1 for r in rs if f(r)) / len(rs)


class TestCalibResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res, cls.rows, cls.by = load()

    def test_complete(self):
        self.assertEqual(len(self.rows), 120)
        self.assertFalse(any(r.get("skipped") for r in self.rows))
        self.assertEqual(len(self.by), 6)
        for sc, rs in self.by.items():
            self.assertEqual(len(rs), 20, sc)
            self.assertEqual(sorted(r["rep"] for r in rs), list(range(20)))
        self.assertEqual(self.res["n_skipped"], 0)

    def test_labels_follow_rule(self):
        for r in self.rows:
            self.assertEqual(label(r), r["label"], (r["scenario"], r["rep"]))

    def test_aggregates_rederived(self):
        agg = self.res["aggregate"]
        for sc, rs in self.by.items():
            a = agg[sc]
            mean_r2 = sum(r["real_r2"] for r in rs) / len(rs)
            self.assertAlmostEqual(mean_r2, a["real_r2_mean"], places=9)
            both = frac(rs, lambda r: r["nulls"]["shuffle"]["p"] < ALPHA
                        and r["nulls"]["rotate"]["p"] < ALPHA)
            self.assertAlmostEqual(both, a["frac_pass_published_controls"], places=9)
            for name in ("shuffle", "markov1_pooled", "markov2_pooled", "rotate"):
                fr = frac(rs, lambda r: r["nulls"][name]["p"] < ALPHA)
                self.assertAlmostEqual(fr, a["nulls"][name]["frac_p_lt_alpha"], places=9)
            bso = frac(rs, lambda r: r["label"] == "BEYOND_SECOND_ORDER")
            self.assertAlmostEqual(bso, a["frac_beyond_second_order"], places=9)

    def test_headline_numbers(self):
        b = self.by
        m1 = b["markov1_a0.2"]
        self.assertEqual(sum(1 for r in m1 if r["nulls"]["shuffle"]["p"] < ALPHA
                             and r["nulls"]["rotate"]["p"] < ALPHA), 20)
        self.assertAlmostEqual(sum(r["real_r2"] for r in m1) / 20, 0.848, delta=0.0006)
        # every source passes both published controls in 20 of 20
        for sc, rs in b.items():
            self.assertEqual(sum(1 for r in rs if r["nulls"]["shuffle"]["p"] < ALPHA
                                 and r["nulls"]["rotate"]["p"] < ALPHA), 20, sc)
        self.assertAlmostEqual(sum(r["real_r2"] for r in b["words_uniform"]) / 20, 0.892,
                               delta=0.0006)
        noisy = [r["label"] for r in b["words_zipf_noise10"]]
        self.assertEqual(noisy.count("BEYOND_SECOND_ORDER"), 2)
        self.assertEqual(noisy.count("EXPLAINED_BY_SECOND_ORDER"), 18)
        first = b["markov1_a0.2"] + b["markov1_a1.0"]
        self.assertEqual(sum(1 for r in first if r["label"] == "BEYOND_SECOND_ORDER"), 0)
        words = b["words_uniform"] + b["words_zipf"]
        self.assertEqual(sum(1 for r in words if r["label"] == "BEYOND_SECOND_ORDER"), 40)
        m2 = b["markov2_a0.2"]
        self.assertEqual(sum(1 for r in m2 if r["label"] == "EXPLAINED_BY_FIRST_ORDER"), 18)
        self.assertTrue(all(r["d1_n_favour_order2"] == 30 for r in m2))

    def test_grades_and_brier(self):
        agg = self.res["aggregate"]
        got = {
            "C1": agg["markov1_a0.2"]["real_r2_mean"] >= 0.80,
            "C2": agg["markov1_a0.2"]["frac_pass_published_controls"] >= 0.80,
            "C3": agg["markov1_a0.2"]["nulls"]["markov1_pooled"]["frac_p_lt_alpha"] <= 0.15,
            "C4": agg["markov2_a0.2"]["frac_beyond_second_order"] <= 0.15,
            "C5": agg["words_zipf"]["frac_beyond_second_order"] >= 0.50,
            "C6": agg["words_uniform"]["real_r2_mean"] >= 0.80,
            "C7": agg["words_zipf_noise10"]["frac_beyond_second_order"] >= 0.50,
        }
        self.assertEqual(got, EXPECTED)
        for k, v in EXPECTED.items():
            self.assertEqual(self.res["grading"]["predictions"][KEYS[k]], v, k)
        rules = self.res["grading"]["rules"]
        self.assertFalse(rules["R1_size_caveat_on_beyond_second_order"])
        self.assertFalse(rules["R2_low_power_relabel_explained_as_not_distinguishable"])
        self.assertTrue(rules["R3_published_controls_do_not_separate_words_from_first_order_rules"])
        brier = sum((PRIORS[k] - (1.0 if EXPECTED[k] else 0.0)) ** 2 for k in PRIORS) / 7
        self.assertAlmostEqual(brier, 1.21 / 7, places=9)
        self.assertEqual(round(brier, 3), 0.173)

    def test_hand_check_rep0(self):
        r = [x for x in self.by["markov1_a0.2"] if x["rep"] == 0][0]
        self.assertEqual(r["seed"], 20261117)
        for name in ("shuffle", "rotate"):
            n = r["nulls"][name]
            z = (r["real_r2"] - n["null_mean"]) / n["null_sd"]
            self.assertAlmostEqual(z, n["z"], places=6)
            self.assertAlmostEqual(n["p"], 1 / 101, places=12)
        self.assertEqual(r["label"], "EXPLAINED_BY_FIRST_ORDER")

    def test_results_md_states_grades(self):
        with open(MD, encoding="utf-8") as f:
            md = f.read()
        self.assertIn("**0.173**", md)
        self.assertIn("| C7 |", md)
        self.assertIn("**FALSE** | 2/20", md)
        self.assertIn("**R3 holds**", md)


if __name__ == "__main__":
    unittest.main()
