# SPDX-License-Identifier: Apache-2.0
# test_cds_results.py: re-derives every number, label, rule, graded prediction and the Brier
# score in RESULTS-CDS.md from the published output of job song-zipf-cds-v1 (stdlib only).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "cds", "results_cds.json")
MD = os.path.join(HERE, "RESULTS-CDS.md")
ALPHA = 0.05
NULLS = ("shuffle", "bigram_within", "trigram_within", "markov1_pooled", "markov2_pooled",
         "rotate")
PRIORS = {"H0": 0.65, "H1": 0.90, "H2": 0.50, "H3": 0.80, "H4": 0.40, "H5": 0.35,
          "H6": 0.85, "H7": 0.45}
EXPECTED = {"H0": True, "H1": True, "H2": True, "H3": True, "H4": False, "H5": True,
            "H6": False, "H7": True}
BSO = "BEYOND_SECOND_ORDER"
ESO = "EXPLAINED_BY_SECOND_ORDER"
EFO = "EXPLAINED_BY_FIRST_ORDER"
EXP_LABELS = {"F": {"0.3": BSO, "0.5": ESO, "0.7": ESO},
              "W": {"0.3": BSO, "0.5": BSO, "0.7": ESO}}
# registration commit of CDS-PREREG.md (0a01e07) on GitHub
PREREG_COMMIT_UTC = "2026-11-18T08:31:59Z"


def label(row):
    """PREREG.md section 5 decision (zipfseg.decision)."""
    p1 = row["nulls"]["markov1_pooled"]["p"]
    p2 = row["nulls"]["markov2_pooled"]["p"]
    if p2 < ALPHA:
        return BSO
    if p1 < ALPHA:
        return ESO
    return EFO


def n_ge(p, B):
    """p = (1 + k) / (1 + B) -> k, the number of null datasets >= real."""
    return int(round(p * (B + 1) - 1))


class TestCdsResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        with open(MD, encoding="utf-8") as f:
            cls.md = f.read()

    def row(self, key, th):
        return self.r[key]["by_theta"][th]

    def test_status_and_registration(self):
        r = self.r
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["version"], "cds-1")
        self.assertTrue(r["registration"]["found"])
        self.assertEqual(r["registration"]["utc"], "2026-11-18T12:48:22Z")
        self.assertLess(PREREG_COMMIT_UTC, r["registration"]["utc"])

    def test_reading_gate(self):
        c = self.r["corpus"]
        self.assertEqual(c["source"], "talkbank_zip")
        n = c["counts"]
        self.assertEqual((n["utterances"], n["phonemes"], n["words"]), (9790, 95809, 33399))
        self.assertEqual((n["phoneme_types"], n["word_types"]), (50, 1321))
        self.assertTrue(all(c["gate"].values()))
        # phonemes + spaces between words + one line end per utterance = file size
        spaces = n["words"] - n["utterances"]
        self.assertEqual(spaces, 23609)
        self.assertEqual(n["phonemes"] + spaces + n["utterances"], c["bytes"])
        self.assertEqual(c["bytes"], 129208)
        self.assertTrue(c["sha256"].startswith("b76e44c4"))
        self.assertTrue(c["sha256"].endswith("7c99"))

    def test_sizes(self):
        d = self.r["describe"]
        f, w = d["F"], d["W"]
        self.assertEqual((f["recordings"], f["utterances"], f["phonemes"], f["true_word_tokens"]),
                         (30, 2100, 19402, 6821))
        self.assertEqual((w["recordings"], w["utterances"], w["phonemes"], w["true_word_tokens"]),
                         (8, 4800, 49162, 17097))
        self.assertAlmostEqual(f["phonemes"] / 30, f["phonemes_per_recording_mean"], places=9)
        self.assertEqual(round(f["phonemes_per_recording_mean"], 1), 646.7)
        self.assertEqual(round(w["phonemes_per_recording_mean"]), 6145)
        self.assertEqual(round(f["true_word_zipf_r2_mean"], 3), 0.917)
        self.assertEqual(round(w["true_word_zipf_r2_mean"], 3), 0.943)
        self.assertEqual((self.r["F"]["B"], self.r["W"]["B"]), (1000, 200))

    def test_z_and_p_rederived(self):
        for key in ("F", "W"):
            B = self.r[key]["B"]
            for th, row in self.r[key]["by_theta"].items():
                for name in NULLS:
                    n = row["nulls"][name]
                    self.assertAlmostEqual(n["real"], row["real_mean_r2"], places=12)
                    self.assertAlmostEqual((n["real"] - n["null_mean"]) / n["null_sd"], n["z"],
                                           places=6)
                    self.assertEqual(n["n_null"], B)
                    k = n["p"] * (B + 1) - 1
                    self.assertAlmostEqual(k, round(k), places=6)
                    self.assertTrue(0 <= round(k) <= B)

    def test_labels_and_rules(self):
        got = {k: {th: label(row) for th, row in self.r[k]["by_theta"].items()}
               for k in ("F", "W")}
        self.assertEqual(got, EXP_LABELS)
        g = self.r["grading"]
        self.assertEqual(g["labels"], EXP_LABELS)
        rules = g["rules"]
        self.assertEqual(rules["L1"], "LANGUAGE_FAILS_AT_FINCH_SIZE")
        self.assertEqual(rules["L2"], "LANGUAGE_PASSES_AT_WHALE_SIZE")
        self.assertTrue(rules["L3_published_controls_passed_by_english"])
        self.assertFalse(rules["robust_F"])
        self.assertFalse(rules["robust_W"])
        self.assertEqual(len(set(got["F"].values())) == 1, rules["robust_F"])
        self.assertEqual(len(set(got["W"].values())) == 1, rules["robust_W"])

    def test_overfit_check_d1(self):
        f = self.r["F"]["heldout_ll_order2_minus_order1"]
        w = self.r["W"]["heldout_ll_order2_minus_order1"]
        self.assertEqual(len(f["per_recording"]), 30)
        self.assertEqual(len(w["per_recording"]), 8)
        nf = sum(1 for v in f["per_recording"] if v > 0)
        nw = sum(1 for v in w["per_recording"] if v > 0)
        self.assertEqual((nf, f["n_favour_order2"]), (1, 1))
        self.assertEqual((nw, w["n_favour_order2"]), (8, 8))
        self.assertAlmostEqual(sum(f["per_recording"]) / 30, f["mean"], places=9)
        self.assertAlmostEqual(sum(w["per_recording"]) / 8, w["mean"], places=9)
        self.assertEqual(round(f["mean"], 3), -0.150)
        self.assertEqual(round(w["mean"], 3), 0.213)
        # PREREG.md: EXPLAINED_BY_SECOND_ORDER gets the overfit caveat when order 2 does not
        # generalise better in most recordings
        self.assertEqual(EXP_LABELS["F"]["0.5"], ESO)
        self.assertTrue(2 * nf <= 30)
        self.assertTrue(2 * nw > 8)

    def test_headline_numbers(self):
        f5 = self.row("F", "0.5")
        w5 = self.row("W", "0.5")
        m2f = f5["nulls"]["markov2_pooled"]
        m2w = w5["nulls"]["markov2_pooled"]
        self.assertEqual(round(f5["real_mean_r2"], 4), 0.8955)
        self.assertEqual(round(m2f["null_mean"], 4), 0.8954)
        self.assertEqual(round(m2f["z"], 2), 0.01)
        self.assertEqual(round(m2f["p"], 2), 0.49)
        self.assertEqual(n_ge(m2f["p"], 1000), 490)
        self.assertEqual(m2f["null_frac_r2_ge_0.80"], 1.0)
        self.assertEqual(round(w5["real_mean_r2"], 3), 0.952)
        self.assertEqual(round(m2w["z"], 1), 5.6)
        self.assertEqual(round(m2w["p"], 3), 0.005)
        self.assertEqual(n_ge(m2w["p"], 200), 0)
        self.assertGreater(w5["real_mean_r2"], 0.93)
        self.assertEqual(round(self.row("F", "0.7")["nulls"]["markov2_pooled"]["z"], 2), -2.89)

    def test_main_table_in_md(self):
        names = (("shuffle", "shuffle (published)"), ("rotate", "rotation (published)"),
                 ("bigram_within", "within-bout bigram (finch paper)"),
                 ("trigram_within", "within-bout trigram"),
                 ("markov1_pooled", "pooled first-order chain"))
        f5 = self.row("F", "0.5")["nulls"]
        w5 = self.row("W", "0.5")["nulls"]
        for key, text in names:
            a, b = f5[key], w5[key]
            line = "| %s | %.3f | %.2f | %.3f | %.3f | %.2f | %.3f |" % (
                text, a["null_mean"], a["z"], a["p"], b["null_mean"], b["z"], b["p"])
            self.assertIn(line, self.md)
        a, b = f5["markov2_pooled"], w5["markov2_pooled"]
        line = ("| **pooled second-order chain** | **%.3f** | **%.2f** | **%.2f** | **%.3f** | "
                "**%.2f** | **%.3f** |" % (a["null_mean"], a["z"], a["p"], b["null_mean"],
                                          b["z"], b["p"]))
        self.assertIn(line, self.md)

    def test_threshold_table_in_md(self):
        rows = {th: (label(self.row("F", th)), self.row("F", th)["nulls"]["markov2_pooled"]["p"],
                     label(self.row("W", th)), self.row("W", th)["nulls"]["markov2_pooled"]["p"])
                for th in ("0.3", "0.5", "0.7")}
        l3 = rows["0.3"]
        self.assertIn("| 0.3 | `%s` | %.3f | `%s` | %.3f |" % l3, self.md)
        l5 = rows["0.5"]
        self.assertIn("| **0.5** | **`%s`** | **%.2f** | **`%s`** | **%.3f** |" % l5, self.md)
        l7 = rows["0.7"]
        self.assertIn("| 0.7 | `%s` | %.3f | `%s` | %.2f |" % l7, self.md)

    def test_boundary_scores(self):
        for key in ("boundary_scores_F", "boundary_scores_W"):
            for th, s in self.r[key].items():
                p = s["hits"] / s["n_cuts"]
                rc = s["hits"] / s["n_word_boundaries"]
                self.assertAlmostEqual(p, s["precision"], places=12)
                self.assertAlmostEqual(rc, s["recall"], places=12)
                self.assertAlmostEqual(2 * p * rc / (p + rc), s["f1"], places=12)
        bf, bw = self.r["boundary_scores_F"], self.r["boundary_scores_W"]
        self.assertEqual((bf["0.5"]["hits"], bf["0.5"]["n_cuts"], bf["0.5"]["n_word_boundaries"]),
                         (2420, 4424, 4721))
        for th in ("0.3", "0.7"):
            line = "| %s | %.3f | %.3f | %.3f | %.3f |" % (
                th, bf[th]["precision"], bf[th]["recall"], bf[th]["f1"], bw[th]["f1"])
            self.assertIn(line, self.md)
        line = "| 0.5 | %.3f | %.3f | **%.3f** | %.3f |" % (
            bf["0.5"]["precision"], bf["0.5"]["recall"], bf["0.5"]["f1"], bw["0.5"]["f1"])
        self.assertIn(line, self.md)

    def test_predictions_and_brier(self):
        f5 = self.row("F", "0.5")
        n = f5["nulls"]
        got = {
            "H0": f5["real_mean_r2"] >= 0.80,
            "H1": n["shuffle"]["p"] < ALPHA and n["rotate"]["p"] < ALPHA,
            "H2": n["bigram_within"]["p"] < ALPHA,
            "H3": n["markov1_pooled"]["p"] < ALPHA,
            "H4": n["markov2_pooled"]["p"] < ALPHA,
            "H5": self.row("W", "0.5")["nulls"]["markov2_pooled"]["p"] < ALPHA,
            "H6": self.r["F"]["heldout_ll_order2_minus_order1"]["n_favour_order2"] >= 20,
            "H7": self.r["boundary_scores_F"]["0.5"]["f1"] >= 0.50,
        }
        self.assertEqual(got, EXPECTED)
        self.assertEqual(self.r["grading"]["predictions"], EXPECTED)
        self.assertEqual(self.r["grading"]["priors"], PRIORS)
        self.assertEqual(sum(1 for v in got.values() if v), 6)
        brier = sum((PRIORS[k] - (1.0 if got[k] else 0.0)) ** 2 for k in PRIORS) / 8
        self.assertAlmostEqual(brier, 0.25375, places=9)
        self.assertAlmostEqual(self.r["grading"]["brier"], brier, places=9)
        self.assertEqual(round(brier, 3), 0.254)

    def test_md_states_grades(self):
        for s in ("**`LANGUAGE_FAILS_AT_FINCH_SIZE`**", "**`LANGUAGE_PASSES_AT_WHALE_SIZE`**",
                  "Brier score **0.254**", "**1 of 30**", "**8 of 8**", "overfit caveat",
                  "6 of 8 true", "0.8955", "0.8954", "z = 5.6"):
            self.assertIn(s, self.md)


if __name__ == "__main__":
    unittest.main()
