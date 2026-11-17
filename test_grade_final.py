# SPDX-License-Identifier: Apache-2.0
# Tests for grade_final.py (no real data; synthetic result files only).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import json
import os
import shutil
import tempfile
import unittest

import grade_final as G

PUB_Z = {"shuffle": 17.0, "bigram_within": 6.8, "rotate": 15.7}


def row(p1, p2, real=0.89, z=None, m2_mean=0.85):
    z = dict(PUB_Z if z is None else z)
    return {"real_mean_r2": real, "nulls": {
        "shuffle": {"p": 0.001, "z": z["shuffle"], "null_mean": 0.5},
        "bigram_within": {"p": 0.001, "z": z["bigram_within"], "null_mean": 0.6},
        "rotate": {"p": 0.001, "z": z["rotate"], "null_mean": 0.5},
        "trigram_within": {"p": 0.3, "z": 1.0, "null_mean": 0.86},
        "markov1_pooled": {"p": p1, "z": 3.0, "null_mean": 0.7},
        "markov2_pooled": {"p": p2, "z": 1.0, "null_mean": m2_mean}}}


def finch(p1=0.001, p2=0.4, d1=25, gate="PASS_EXACT", real=0.89, z=None, rows=None):
    by = {"0.3": row(p1, p2), "0.5": row(p1, p2, real, z), "0.7": row(p1, p2)}
    by.update(rows or {})
    return {"status": "ok", "gate": gate,
            "main": {"by_theta": by, "heldout_ll_order2_minus_order1": {"n_favour_order2": d1}}}


def calib(r1=False, r2=False, r3=True, skipped=0):
    return {"n_skipped": skipped, "grading": {"rules": {
        "R1_size_caveat_on_beyond_second_order": r1,
        "R2_low_power_relabel_explained_as_not_distinguishable": r2,
        "R3_published_controls_do_not_separate_words_from_first_order_rules": r3}}}


class TestDecision(unittest.TestCase):
    def test_decision_matches_prereg(self):
        self.assertEqual(G.decision(row(0.001, 0.01)), "BEYOND_SECOND_ORDER")
        self.assertEqual(G.decision(row(0.001, 0.05)), "EXPLAINED_BY_SECOND_ORDER")
        self.assertEqual(G.decision(row(0.05, 0.5)), "EXPLAINED_BY_FIRST_ORDER")


class TestFinalLabel(unittest.TestCase):
    def test_second_order_with_power(self):
        r = G.final_label(finch(), calib())
        self.assertEqual(r["label"], "EXPLAINED_BY_SECOND_ORDER")
        self.assertTrue(r["headline"])
        self.assertTrue(r["robust"])
        self.assertFalse(r["provisional"])
        self.assertTrue(r["grades"]["A1-R1"])
        self.assertTrue(r["grades"]["F5"])
        self.assertFalse(r["grades"]["F4"])
        self.assertEqual(r["caveats"], [])

    def test_low_power_relabels(self):
        r = G.final_label(finch(), calib(r2=True))
        self.assertEqual(r["label"], "NOT_DISTINGUISHABLE")
        self.assertEqual(r["base_label"], "EXPLAINED_BY_SECOND_ORDER")
        self.assertTrue(any("low power" in c for c in r["caveats"]))

    def test_first_order_low_power_relabels(self):
        r = G.final_label(finch(p1=0.2, p2=0.5), calib(r2=True))
        self.assertEqual(r["label"], "NOT_DISTINGUISHABLE")

    def test_beyond_with_size_caveat(self):
        r = G.final_label(finch(p2=0.01), calib(r1=True))
        self.assertEqual(r["label"], "BEYOND_SECOND_ORDER")
        self.assertFalse(r["headline"])
        self.assertTrue(any("size caveat" in c for c in r["caveats"]))

    def test_beyond_clean(self):
        r = G.final_label(finch(p2=0.01), calib(r2=True))   # R2 does not touch BEYOND
        self.assertEqual(r["label"], "BEYOND_SECOND_ORDER")
        self.assertTrue(r["headline"])

    def test_calibration_missing(self):
        for f in (finch(), finch(p2=0.01)):
            r = G.final_label(f, None)
            self.assertFalse(r["headline"])
            self.assertTrue(any("pending calibration" in c for c in r["caveats"]))
            self.assertEqual(r["calibration"]["status"], "missing")

    def test_calibration_partial(self):
        r = G.final_label(finch(), calib(skipped=3))
        self.assertEqual(r["calibration"]["status"], "partial")
        self.assertTrue(any("3 replicate" in c for c in r["caveats"]))

    def test_sanity_fails(self):
        r = G.final_label(finch(real=0.80), calib())
        self.assertEqual(r["label"], "REPRODUCTION_FAILED")
        self.assertFalse(r["headline"])
        self.assertFalse(r["robust"])

    def test_sanity_nan(self):
        r = G.final_label(finch(real=float("nan")), calib())
        self.assertEqual(r["label"], "REPRODUCTION_FAILED")

    def test_z_reproduction(self):
        bad = dict(PUB_Z, rotate=10.0)
        self.assertFalse(G.final_label(finch(z=bad), calib())["grades"]["A1-R1"])
        nan = dict(PUB_Z, shuffle=float("nan"))
        self.assertFalse(G.final_label(finch(z=nan), calib())["grades"]["A1-R1"])
        edge = {"shuffle": 17.05 * 1.24, "bigram_within": 6.77 * 0.76, "rotate": 15.69}
        self.assertTrue(G.final_label(finch(z=edge), calib())["grades"]["A1-R1"])

    def test_not_robust(self):
        r = G.final_label(finch(rows={"0.7": row(0.001, 0.01)}), calib())
        self.assertFalse(r["robust"])
        self.assertEqual(r["labels_by_theta"]["0.7"], "BEYOND_SECOND_ORDER")
        self.assertEqual(r["label"], "EXPLAINED_BY_SECOND_ORDER")

    def test_overfit_caveat(self):
        r = G.final_label(finch(d1=10), calib())
        self.assertFalse(r["grades"]["F6"])
        self.assertTrue(any("overfit" in c for c in r["caveats"]))

    def test_provisional(self):
        r = G.final_label(finch(gate="PASS_APPROX"), calib())
        self.assertTrue(r["provisional"])
        self.assertTrue(any("provisional" in c for c in r["caveats"]))

    def test_not_run(self):
        r = G.final_label({"status": "not_run", "gate": "FAIL"}, calib())
        self.assertEqual(r["label"], "NOT_RUN")
        self.assertFalse(r["headline"])
        self.assertEqual(G.final_label(None, None)["label"], "NOT_RUN")

    def test_mismatch_flagged(self):
        f = finch()
        f["machine_grades"] = {"S-F": True, "F1": True, "F2": True, "F3": True,
                               "F4": True, "F5": True, "F6": True}
        r = G.final_label(f, calib())
        self.assertEqual(r["grade_mismatch_with_job"], ["F3", "F4"])


class TestMain(unittest.TestCase):
    def test_main_writes_files(self):
        d = tempfile.mkdtemp()
        try:
            fp = os.path.join(d, "results_finch.json")
            cp = os.path.join(d, "calib_results.json")
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(finch(), f)
            with open(cp, "w", encoding="utf-8") as f:
                json.dump(calib(), f)
            res = G.main(["--finch", fp, "--calib", cp, "--out-dir", d])
            self.assertEqual(res["label"], "EXPLAINED_BY_SECOND_ORDER")
            with open(os.path.join(d, "final_grades.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f)["label"], "EXPLAINED_BY_SECOND_ORDER")
            with open(os.path.join(d, "FINAL-LABEL.md"), encoding="utf-8") as f:
                md = f.read()
            self.assertIn("**EXPLAINED_BY_SECOND_ORDER**", md)
            G.main(["--finch", os.path.join(d, "missing.json"), "--out-dir", d])
            with open(os.path.join(d, "FINAL-LABEL.md"), encoding="utf-8") as f:
                self.assertIn("**NOT_RUN**", f.read())
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
