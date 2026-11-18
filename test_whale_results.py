# SPDX-License-Identifier: Apache-2.0
# test_whale_results.py: re-derives every registered prediction, label, the Brier score, the
# calibration conditions (PREREG-AMENDMENT-3 section 5.3) and the Code S1 gate (PREREG-
# AMENDMENT-5 Gate B) from the published output of whale-test-v1, results/whale/
# whale_results.json, using only the numbers in that file (stdlib only).
# Written 2026-11-18 before the job finished, from whale_test.py @742fd83 and whale_run.py
# @c9f3d12, so the grading cannot be bent to the result.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import math
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "whale", "whale_results.json")
MD = os.path.join(HERE, "RESULTS-WHALE.md")
ALPHA = 0.05
# whale_test.py @742fd83 (PREREG.md / PREREG-AMENDMENT-3), whale_run.py @c9f3d12
PRIORS = {"S-W": 0.85, "W1": 0.70, "W2": 0.70, "W3": 0.45, "W4": 0.45, "W5": 0.50,
          "W6": 0.70, "N1": 0.60, "N2": 0.90, "N3": 0.45, "N4": 0.85, "N5": 0.40,
          "N6": 0.25}
PUBLISHED = {"zipf_r2": 0.93, "zipf_z_shuffle": 23.09, "zipf_z_rotate": 14.43,
             "brev_r2": 0.62, "brev_z_shuffle": 37.57, "brev_z_rotate": 13.92}
NULLS = ("shuffle", "rotate", "markov1_pooled", "markov2_pooled", "bigram_within",
         "trigram_within")
STATS = ("zipf", "brev_pool", "brev_year")
CODE_S1 = {"zipf_r2": 0.9302888665216734, "n_types": 3386, "tol": 1e-6}
G1_PRIOR = 0.70
PRIMARY = "brev_year"


def isnum(a):
    return isinstance(a, (int, float)) and not isinstance(a, bool) and a == a


def beats(row, stat, null):
    p = row["nulls"][null][stat]["p"]
    return isnum(p) and p < ALPHA


def label(row, stat):
    ok = True
    if stat.startswith("brev"):
        s = row["real"][stat + "_slope"]
        ok = isnum(s) and s < 0
    if ok and beats(row, stat, "markov2_pooled"):
        return "BEYOND_SECOND_ORDER"
    if ok and beats(row, stat, "markov1_pooled"):
        return "EXPLAINED_BY_SECOND_ORDER"
    return "EXPLAINED_BY_FIRST_ORDER"


def predictions(j, brev_key):
    m = j["by_theta"]["0.5"]
    r = m["real"]
    nm = m["nulls"]
    slope = r[brev_key + "_slope"]
    slope_neg = isnum(slope) and slope < 0
    m2mean = nm["markov2_pooled"]["zipf"]["null_mean"]
    return {
        "S-W": beats(m, "zipf", "shuffle") and abs(r["zipf"] - PUBLISHED["zipf_r2"]) <= 0.03,
        "W1": beats(m, "zipf", "bigram_within"),
        "W2": beats(m, "zipf", "markov1_pooled"),
        "W3": beats(m, "zipf", "trigram_within"),
        "W4": beats(m, "zipf", "markov2_pooled"),
        "W5": isnum(m2mean) and m2mean >= 0.80,
        "W6": j["heldout_order2_minus_order1"]["n_favour_order2"] >= 6,
        "N1": bool(j["table_s2"]["reproduced"]),
        "N2": beats(m, "zipf", "rotate"),
        "N3": isnum(r[brev_key]) and abs(r[brev_key] - PUBLISHED["brev_r2"]) <= 0.10,
        "N4": slope_neg and beats(m, brev_key, "shuffle") and beats(m, brev_key, "rotate"),
        "N5": slope_neg and beats(m, brev_key, "markov1_pooled"),
        "N6": slope_neg and beats(m, brev_key, "markov2_pooled"),
    }


def brier(preds):
    return sum((PRIORS[k] - (1.0 if v else 0.0)) ** 2 for k, v in preds.items()) / len(preds)


def final(labels, n1, calib2, calib4, gate_b):
    out = {}
    for stat, beyond_ok, explained_ok in (("zipf", calib2.get("K5"), calib2.get("K6")),
                                          ("brevity", calib4.get("Q10"), calib4.get("Q11"))):
        lab = labels[stat]
        headline = lab != "REPRODUCTION_FAILED" and n1
        fin = lab
        if lab == "BEYOND_SECOND_ORDER" and not beyond_ok:
            headline = False
        if lab.startswith("EXPLAINED_BY"):
            if explained_ok is None:
                headline = False
            elif not explained_ok:
                fin = "NOT_DISTINGUISHABLE"
        if not gate_b:
            headline = False
        out[stat] = (fin, lab, headline)
    return out


class TestWhaleResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.j = json.load(f)

    def test_registration_before_analysis(self):
        reg = self.j["registration"]
        self.assertTrue(reg["found"])
        # both are ISO 8601 UTC "YYYY-MM-DDTHH:MM:SSZ", so string order is time order
        self.assertLess(reg["utc"], reg["analysis_start_utc"])

    def test_gate_a(self):
        self.assertTrue(self.j["gate_a"]["pass"], self.j["gate_a"]["reasons"])
        self.assertEqual(self.j["years"], list(range(2010, 2018)))
        self.assertEqual(self.j["n_recordings"], [4, 6, 6, 6, 7, 13, 6, 7])
        self.assertLessEqual(abs(sum(self.j["n_elements"]) - 45760), 0.005 * 45760)

    def test_gate_b(self):
        gb = self.j["gate_b_code_s1"]
        ok = (isnum(gb["zipf_r2"]) and abs(gb["zipf_r2"] - CODE_S1["zipf_r2"]) <= CODE_S1["tol"]
              and gb["n_types"] == CODE_S1["n_types"])
        self.assertEqual(gb["pass"], ok)
        self.assertEqual(self.j["g1"]["outcome"], ok)
        # Gate B's R^2 is the primary run's real Zipf R^2 (same segmentation)
        self.assertAlmostEqual(gb["zipf_r2"], self.j["by_theta"]["0.5"]["real"]["zipf"], 12)
        self.assertEqual(gb["n_types"], sum(self.j["by_theta"]["0.5"]["n_types_per_year"]))

    def test_null_summaries_consistent(self):
        for key, row in self.j["by_theta"].items():
            for null in NULLS:
                d = row["nulls"][null]
                self.assertGreaterEqual(d["B_done"], 1, (key, null))
                for s in STATS:
                    c = d[s]
                    self.assertLessEqual(c["n_null"], d["B_done"])
                    if not isnum(c["p"]):
                        continue
                    self.assertGreaterEqual(c["p"], 1.0 / (1 + c["n_null"]) - 1e-12)
                    self.assertLessEqual(c["p"], 1.0)
                    # p = (1 + k) / (1 + n): (1 + n) * p is a whole number
                    k = c["p"] * (1 + c["n_null"]) - 1
                    self.assertAlmostEqual(k, round(k), 6)
                    if isnum(c["z"]) and c["null_sd"] > 0:
                        self.assertAlmostEqual(c["z"], (c["real"] - c["null_mean"])
                                               / c["null_sd"], 9)
                    self.assertAlmostEqual(c["real"], row["real"][s], 12)

    def test_table_s2_and_heldout(self):
        s2 = self.j["table_s2"]
        n = sum(1 for v in s2["per_year"].values() if v["top1_match"])
        self.assertEqual(s2["n_years_top1_match"], n)
        self.assertEqual(s2["reproduced"], n >= 6)
        ho = self.j["heldout_order2_minus_order1"]
        self.assertEqual(ho["n_favour_order2"], sum(1 for a in ho["per_year"] if a > 0))

    def _check_grading(self, g, brev_key):
        self.assertEqual(g["brev_key"], brev_key)
        preds = predictions(self.j, brev_key)
        self.assertEqual(g["predictions"], preds)
        self.assertAlmostEqual(g["brier"], brier(preds), 12)
        m = self.j["by_theta"]["0.5"]
        zl = label(m, "zipf") if preds["S-W"] else "REPRODUCTION_FAILED"
        bl = label(m, brev_key) if preds["N4"] else "REPRODUCTION_FAILED"
        self.assertEqual(g["labels"], {"zipf": zl, "brevity": bl})
        for k, row in self.j["by_theta"].items():
            self.assertEqual(g["labels_by_run"][k],
                             {"zipf": label(row, "zipf"), "brevity": label(row, brev_key)})
        by = g["labels_by_run"]
        for s in ("zipf", "brevity"):
            rob = (all(k in by for k in ("0.3", "0.5", "0.7"))
                   and len({by[k][s] for k in ("0.3", "0.5", "0.7")}) == 1)
            self.assertEqual(g["robust"][s], rob)
        return preds, zl, bl

    def test_grading_primary_and_alternate(self):
        self.assertEqual(self.j["config"]["primary_brevity_key"], PRIMARY)
        self._check_grading(self.j["grading"], PRIMARY)
        self._check_grading(self.j["grading_alternate_pool"], "brev_pool")

    def test_final_reading_and_brier_with_g1(self):
        preds, zl, bl = self._check_grading(self.j["grading"], PRIMARY)
        gb = self.j["gate_b_code_s1"]["pass"]
        fr = final({"zipf": zl, "brevity": bl}, preds["N1"], self.j["config"]["calib2"],
                   self.j["config"]["calib4"], gb)
        for stat, (fin, lab, head) in fr.items():
            got = self.j["final_reading"][stat]
            self.assertEqual((got["label"], got["base_label"], got["headline"]),
                             (fin, lab, head), stat)
        b13 = brier(preds)
        bg = (b13 * 13 + (G1_PRIOR - (1.0 if gb else 0.0)) ** 2) / 14
        self.assertAlmostEqual(self.j["brier_with_g1"], bg, 12)

    def test_results_md_matches(self):
        if not os.path.exists(MD):
            self.skipTest("RESULTS-WHALE.md not present")
        with open(MD, encoding="utf-8") as f:
            md = f.read()
        for stat in ("zipf", "brevity"):
            self.assertIn(self.j["final_reading"][stat]["label"], md)
        self.assertIn("%.3f" % self.j["brier_with_g1"], md)
        self.assertIn("%.4f" % self.j["gate_b_code_s1"]["zipf_r2"], md)


if __name__ == "__main__":
    unittest.main()
