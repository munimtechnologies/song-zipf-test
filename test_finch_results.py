# SPDX-License-Identifier: Apache-2.0
# test_finch_results.py: re-derives every number in RESULTS-FINCH.md from the published
# derived output of job song-zipf-finch-v2 (results/finch/) and the calibration output
# (results/calib_results.json, results/calib2_results.json). Stdlib only.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import unittest

import grade_final

HERE = os.path.dirname(os.path.abspath(__file__))
FINCH = os.path.join(HERE, "results", "finch", "results_finch.json")
VALID = os.path.join(HERE, "results", "finch", "validation.json")
CALIB = os.path.join(HERE, "results", "calib_results.json")
CALIB2 = os.path.join(HERE, "results", "calib2_results.json")
MD = os.path.join(HERE, "RESULTS-FINCH.md")
ALPHA = 0.05
PRIORS = {"S-F": 0.60, "F1": 0.85, "F2": 0.80, "F3": 0.35, "F4": 0.35, "F5": 0.60, "F6": 0.75}
EXPECTED = {"S-F": True, "F1": True, "F2": True, "F3": False, "F4": False, "F5": True,
            "F6": True}


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


class TestFinchResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = _load(FINCH)
        cls.v = _load(VALID)
        cls.c = _load(CALIB)
        cls.c2 = _load(CALIB2)
        cls.main = cls.f["main"]
        cls.n5 = cls.main["by_theta"]["0.5"]["nulls"]

    def test_gate_exact(self):
        self.assertEqual(self.f["gate"], "PASS_EXACT")
        self.assertEqual(self.v["gate"], "PASS_EXACT")
        val = self.v["configs"][0]["validation"]
        self.assertEqual(val["recordings_found"], 30)
        self.assertEqual(val["bouts"], 299)
        self.assertEqual(val["transitions"], 19990)
        self.assertEqual(val["pipeline_cuts"], 3205)
        self.assertEqual(val["pipeline_types"], 1043)
        self.assertEqual(val["cut_agreement"]["both"], 3098)
        self.assertEqual(val["cut_agreement"]["pipeline_only"], 0)
        self.assertEqual(val["cut_agreement"]["printed_only"], 0)
        self.assertEqual(val["cut_agreement"]["bouts_identical"], 299)
        self.assertTrue(all(val["exact"].values()))
        g = self.v["glyph"]
        self.assertEqual(g["name_solutions"], 1)
        self.assertEqual(g["day_solutions"], 1)
        self.assertEqual(g["n_classes"], 42)
        for sg in ("2.0", "2.5"):
            self.assertEqual(self.v["space_gap_sensitivity"][sg]["gate"], "PASS_EXACT")

    def test_sums(self):
        pr = self.f["per_recording"]
        self.assertEqual(len(pr), 30)
        syl = sum(r["syllables"] for r in pr)
        bouts = sum(r["bouts"] for r in pr)
        self.assertEqual(syl, 20289)
        self.assertEqual(bouts, 299)
        self.assertEqual(syl - bouts, 19990)
        self.assertEqual(sum(r["types_0.5"] for r in pr), 1043)
        mean_r2 = sum(r["r2_0.5"] for r in pr) / 30
        self.assertAlmostEqual(mean_r2, self.main["by_theta"]["0.5"]["real_mean_r2"], places=9)
        lpb = self.v["configs"][0]["validation"]["letters_per_bird"]
        self.assertEqual(sum(sum(d.values()) for d in lpb.values()), 20289)

    def test_reproduction_table(self):
        by = self.main["by_theta"]
        self.assertEqual(round(by["0.3"]["real_mean_r2"], 3), 0.751)
        self.assertEqual(round(by["0.5"]["real_mean_r2"], 3), 0.889)
        self.assertEqual(round(by["0.7"]["real_mean_r2"], 3), 0.899)
        self.assertEqual(round(self.n5["shuffle"]["z"], 2), 16.69)
        self.assertEqual(round(self.n5["bigram_within"]["z"], 2), 6.94)
        self.assertEqual(round(self.n5["rotate"]["z"], 2), 15.07)
        b7 = by["0.7"]["nulls"]["bigram_within"]
        self.assertEqual(round(b7["z"], 2), 1.89)
        self.assertEqual(round(b7["p"], 3), 0.027)

    def test_main_table(self):
        n = self.n5
        exp = {"shuffle": (0.583, 16.69, 0.001), "rotate": (0.710, 15.07, 0.001),
               "bigram_within": (0.791, 6.94, 0.001), "markov1_pooled": (0.804, 6.52, 0.001),
               "trigram_within": (0.878, 1.27, 0.096), "markov2_pooled": (0.879, 1.07, 0.137)}
        for k, (m, z, p) in exp.items():
            self.assertEqual(round(n[k]["null_mean"], 3), m, k)
            self.assertEqual(round(n[k]["z"], 2), z, k)
            self.assertEqual(round(n[k]["p"], 3), p, k)
            self.assertEqual(n[k]["n_null"], 1000, k)
        self.assertEqual(n["markov2_pooled"]["null_frac_r2_ge_0.80"], 1.0)
        # hand check: z and p by definition
        s = n["shuffle"]
        self.assertAlmostEqual((s["real"] - s["null_mean"]) / s["null_sd"], s["z"], places=6)
        self.assertAlmostEqual(n["markov2_pooled"]["p"], 137 / 1001, places=12)
        self.assertAlmostEqual(n["markov1_pooled"]["p"], 1 / 1001, places=12)

    def test_d1(self):
        d = self.main["heldout_ll_order2_minus_order1"]
        self.assertEqual(len(d["per_recording"]), 30)
        self.assertEqual(sum(1 for x in d["per_recording"] if x > 0), 30)
        self.assertEqual(d["n_favour_order2"], 30)

    def test_grades_and_brier(self):
        got = {
            "S-F": abs(self.main["by_theta"]["0.5"]["real_mean_r2"] - 0.89) <= 0.03,
            "F1": self.n5["bigram_within"]["p"] < ALPHA,
            "F2": self.n5["markov1_pooled"]["p"] < ALPHA,
            "F3": self.n5["trigram_within"]["p"] < ALPHA,
            "F4": self.n5["markov2_pooled"]["p"] < ALPHA,
            "F5": self.n5["markov2_pooled"]["null_mean"] >= 0.80,
            "F6": self.main["heldout_ll_order2_minus_order1"]["n_favour_order2"] >= 20,
        }
        self.assertEqual(got, EXPECTED)
        self.assertEqual(self.f["machine_grades"], EXPECTED)
        brier = sum((PRIORS[k] - (1.0 if EXPECTED[k] else 0.0)) ** 2 for k in PRIORS) / 7
        self.assertAlmostEqual(brier, 0.69 / 7, places=9)
        self.assertEqual(round(brier, 3), 0.099)

    def test_final_label_mechanical(self):
        res = grade_final.final_label(self.f, self.c)
        self.assertEqual(res["label"], "EXPLAINED_BY_SECOND_ORDER")
        self.assertEqual(res["base_label"], "EXPLAINED_BY_SECOND_ORDER")
        self.assertTrue(res["headline"])
        self.assertFalse(res["robust"])
        self.assertFalse(res["provisional"])
        self.assertEqual(res["caveats"], [])
        self.assertEqual(res["labels_by_theta"], {"0.3": "EXPLAINED_BY_SECOND_ORDER",
                                                  "0.5": "EXPLAINED_BY_SECOND_ORDER",
                                                  "0.7": "EXPLAINED_BY_FIRST_ORDER"})
        self.assertTrue(res["grades"]["A1-R1"])
        self.assertEqual(res["calibration"]["status"], "complete")
        self.assertFalse(res["calibration"]["A2-R2"])
        self.assertEqual(res["grade_mismatch_with_job"], [])
        self.assertEqual(self.f["labels_robustness"]["rule_prev_over_cur"],
                         "EXPLAINED_BY_SECOND_ORDER")
        self.assertEqual(self.f["labels_robustness"]["tp_denominator_followed"],
                         "EXPLAINED_BY_SECOND_ORDER")
        self.assertEqual(round(self.main["by_theta"]["0.3"]["nulls"]["markov2_pooled"]["p"], 3),
                         0.106)
        self.assertEqual(round(self.main["by_theta"]["0.7"]["nulls"]["markov1_pooled"]["p"], 3),
                         0.060)

    def test_wr4_power_caveat(self):
        r = self.c2["grading"]["rules"]
        self.assertEqual(r["WR4_finch_noise_level_power_below_half"], 0.1)
        self.assertEqual(r["WR4_finch_power_by_noise"],
                         {"0.0": 1.0, "0.02": 1.0, "0.05": 0.85, "0.1": 0.1})

    def test_md_states_result(self):
        with open(MD, encoding="utf-8") as f:
            md = f.read()
        for s in ("**`EXPLAINED_BY_SECOND_ORDER`**", "Brier score **0.099**", "**24 of 24 matched.**",
                  "**30 of\n30**", "NOT robust", "degraded by 10% noise"):
            self.assertIn(s, md)


if __name__ == "__main__":
    unittest.main()
