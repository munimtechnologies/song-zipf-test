# SPDX-License-Identifier: Apache-2.0
# test_cds_size_results.py: the grader for the English size curve (CDS-SIZE-PREREG.md, job
# song-zipf-cdssize-v1), written and published BEFORE the job has run. It re-derives, with its
# own code, every label, aggregate, graded prediction, reading rule and the Brier score from the
# raw per-replicate output, checks them against the job's own grading, and checks that every
# table row in RESULTS-CDS-SIZE.md is printed from the data in the formats fixed below.
# Until results/cds-size/cds_size_results.json exists, every test is skipped. Stdlib only.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "cds-size", "cds_size_results.json")
MD = os.path.join(HERE, "RESULTS-CDS-SIZE.md")
HAVE = os.path.exists(RES)

ALPHA = 0.05
N_REC = 8
B = 100
DESIGN = ((70, 5), (140, 5), (280, 4), (600, 2), (1200, 1))
SIZES = tuple(u for u, _ in DESIGN)
THETAS = ("0.3", "0.5", "0.7")
SEED = 20261118
PRIORS = {"Z1": 0.75, "Z2": 0.75, "Z3": 0.75, "Z4": 0.50, "Z5": 0.85, "Z6": 0.85, "Z7": 0.40}
WHALE = 5720
FINCH = 676
BSO = "BEYOND_SECOND_ORDER"
ESO = "EXPLAINED_BY_SECOND_ORDER"
EFO = "EXPLAINED_BY_FIRST_ORDER"
ZIPFSEG_SHA256 = "25002193229e6d6568939856de5a1760a41c3b462582ea06b6d75ba6d84bddf5"
# commit 52b82ef (CDS-SIZE-PREREG.md) landed on GitHub at this time
PREREG_COMMIT_UTC = "2026-11-18T13:27:07Z"


# ---- formats fixed before the result exists (RESULTS-CDS-SIZE.md must use them) ----
def size_row(u, n, ppr, d3, d5, d7, dm, zmean, f1mean):
    """| U | replicates | phonemes per recording | detected 0.3 | **detected 0.5** |
    detected 0.7 | D1 majority | mean second-order z (0.5) | mean boundary F1 (0.5) |"""
    return "| {:,} | {} | {:,.0f} | {} of {} | **{} of {}** | {} of {} | {} of {} | {:.2f} | {:.3f} |".format(
        u, n, ppr, d3, n, d5, n, d7, n, dm, n, zmean, f1mean)


def rep_row(x, lab):
    """| U | rep | phonemes | label at 0.5 | second-order z | second-order p | D1 |
    published controls pass at 0.5 | boundary F1 |"""
    pub = all(p < ALPHA for p in x["published_controls_p"]["0.5"])
    return "| {:,} | {} | {:,} | `{}` | {:.2f} | {:.3f} | {} of 8 | {} | {:.3f} |".format(
        x["u"], x["rep"], x["phonemes"], lab, x["m2"]["0.5"]["z"], x["m2"]["0.5"]["p"],
        x["d1_n_favour"], "yes" if pub else "no", x["boundary_f1_0.5"])


def label(x, th):
    """PREREG.md section 5 decision (zipfseg.decision), from the stored p values."""
    if x["m2"][th]["p"] < ALPHA:
        return BSO
    if x["m1_p"][th] < ALPHA:
        return ESO
    return EFO


def regrade(reps):
    """Independent re-implementation of CDS-SIZE-PREREG.md sections 3 and 4."""
    by = {u: [x for x in reps if x["u"] == u] for u in SIZES}
    det = {u: sum(1 for x in by[u] if label(x, "0.5") == BSO) / len(by[u]) for u in SIZES}
    d1 = {u: sum(1 for x in by[u] if 2 * x["d1_n_favour"] > N_REC) / len(by[u]) for u in SIZES}
    ustar = next((u for u in SIZES if det[u] >= 0.5), None)
    ppr = None
    if ustar is not None:
        ppr = sum(x["phonemes"] / N_REC for x in by[ustar]) / len(by[ustar])
    g = {"Z1": det[70] <= 0.2, "Z2": det[600] >= 0.5, "Z3": det[1200] == 1.0,
         "Z4": all(det[SIZES[i]] <= det[SIZES[i + 1]] for i in range(len(SIZES) - 1)),
         "Z5": d1[70] == 0.0, "Z6": d1[600] == 1.0 and d1[1200] == 1.0,
         "Z7": ustar is not None and ustar <= 280}
    yes = [x for x in reps if 2 * x["d1_n_favour"] > N_REC]
    no = [x for x in reps if not 2 * x["d1_n_favour"] > N_REC]
    if yes and no:
        ry = sum(1 for x in yes if label(x, "0.5") == BSO) / len(yes)
        rn = sum(1 for x in no if label(x, "0.5") == BSO) / len(no)
        t2 = "D1_TRACKS_DETECTION" if (ry >= 0.5 and rn <= 0.2) else "D1_DOES_NOT_TRACK"
    else:
        ry = rn = None
        t2 = "UNDETERMINED"
    brier = sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in PRIORS) / 7
    return {"det": det, "d1": d1, "ustar": ustar, "ppr": ppr, "g": g, "t2": t2, "ry": ry,
            "rn": rn, "brier": brier, "by": by}


@unittest.skipUnless(HAVE, "results/cds-size/cds_size_results.json not published yet")
class TestCdsSizeResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        cls.reps = cls.r["replicates"]
        cls.rg = regrade(cls.reps)
        cls.md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""

    def test_status_registration_pipeline(self):
        r = self.r
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["version"], "cds-size-1")
        self.assertTrue(r["registration"]["found"])
        # the job read the public prereg only after it was committed
        self.assertLess(PREREG_COMMIT_UTC, r["registration"]["utc"])
        self.assertEqual(r["zipfseg_sha256"], ZIPFSEG_SHA256)
        d = r["design"]
        self.assertEqual((d["n_rec"], d["B"], d["seed"]), (N_REC, B, SEED))
        self.assertEqual([tuple(x) for x in d["design"]], list(DESIGN))
        self.assertEqual(d["thetas"], [0.3, 0.5, 0.7])

    def test_reading_gate_same_corpus_as_cds(self):
        c = self.r["corpus"]
        n = c["counts"]
        self.assertEqual((n["utterances"], n["phonemes"], n["words"]), (9790, 95809, 33399))
        self.assertTrue(all(c["gate"].values()))
        self.assertTrue(c["sha256"].startswith("b76e44c4"))

    def test_replicates_complete_and_consistent(self):
        want = sorted((u, r) for u, n in DESIGN for r in range(n))
        got = sorted((x["u"], x["rep"]) for x in self.reps)
        self.assertEqual(got, want)
        self.assertEqual(len(self.reps), 17)
        for x in self.reps:
            u, r = x["u"], x["rep"]
            self.assertEqual(x["seed"], SEED + 10000 * r + u)
            self.assertEqual(x["start_utt"], r * N_REC * u)
            self.assertEqual(x["B"], B)
            self.assertAlmostEqual(x["phonemes_per_recording"], x["phonemes"] / N_REC, places=9)
            self.assertEqual(x["d1_majority"], 2 * x["d1_n_favour"] > N_REC)
            self.assertTrue(0 <= x["d1_n_favour"] <= N_REC)
            self.assertTrue(0.0 <= x["boundary_f1_0.5"] <= 1.0)
            for th in THETAS:
                self.assertEqual(x["labels"][th], label(x, th))
                ps = [x["m2"][th]["p"], x["m1_p"][th]] + list(x["published_controls_p"][th])
                for p in ps:
                    k = p * (B + 1) - 1          # p = (1 + k) / (1 + B), k null sets >= real
                    self.assertAlmostEqual(k, round(k), places=6)
                    self.assertTrue(0 <= round(k) <= B)

    def test_aggregate_matches_regrade(self):
        agg = self.r["grading"]["aggregate"]
        for u in SIZES:
            a = agg[str(u)]
            xs = self.rg["by"][u]
            self.assertEqual(a["n_rep"], len(xs))
            self.assertAlmostEqual(a["detect"]["0.5"], self.rg["det"][u], places=12)
            self.assertAlmostEqual(a["d1_majority_rate"], self.rg["d1"][u], places=12)
            for th in THETAS:
                d = sum(1 for x in xs if label(x, th) == BSO) / len(xs)
                self.assertAlmostEqual(a["detect"][th], d, places=12)
            self.assertAlmostEqual(a["phonemes_per_recording_mean"],
                                   sum(x["phonemes"] / N_REC for x in xs) / len(xs), places=6)
            self.assertAlmostEqual(a["m2_z_mean_0.5"],
                                   sum(x["m2"]["0.5"]["z"] for x in xs) / len(xs), places=9)

    def test_predictions_rules_brier_match_regrade(self):
        gr = self.r["grading"]
        rg = self.rg
        self.assertEqual(gr["predictions"], rg["g"])
        self.assertEqual(gr["priors"], PRIORS)
        self.assertAlmostEqual(gr["brier"], rg["brier"], places=12)
        ru = gr["rules"]
        self.assertEqual(ru["T1_threshold_utterances"], rg["ustar"])
        self.assertEqual(ru["T1_label"],
                         "NO_THRESHOLD_IN_RANGE" if rg["ustar"] is None else "THRESHOLD_FOUND")
        if rg["ppr"] is None:
            self.assertIsNone(ru["T1_threshold_phonemes_per_recording"])
        else:
            self.assertAlmostEqual(ru["T1_threshold_phonemes_per_recording"], rg["ppr"], places=6)
        self.assertEqual(ru["T2"], rg["t2"])
        for key, val in (("T2_detect_rate_d1_majority", rg["ry"]),
                         ("T2_detect_rate_d1_minority", rg["rn"])):
            if val is None:
                self.assertIsNone(ru[key])
            else:
                self.assertAlmostEqual(ru[key], val, places=12)
        self.assertEqual(ru["T3_whale_size_within_detecting_range"],
                         rg["ppr"] is not None and rg["ppr"] <= WHALE)
        self.assertEqual(ru["T3_finch_size_within_detecting_range"],
                         rg["ppr"] is not None and rg["ppr"] <= FINCH)

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-CDS-SIZE.md not written yet")
    def test_md_tables(self):
        for u, n in DESIGN:
            xs = self.rg["by"][u]
            cnt = {th: sum(1 for x in xs if label(x, th) == BSO) for th in THETAS}
            dm = sum(1 for x in xs if 2 * x["d1_n_favour"] > N_REC)
            line = size_row(u, n, sum(x["phonemes"] / N_REC for x in xs) / n,
                            cnt["0.3"], cnt["0.5"], cnt["0.7"], dm,
                            sum(x["m2"]["0.5"]["z"] for x in xs) / n,
                            sum(x["boundary_f1_0.5"] for x in xs) / n)
            self.assertIn(line, self.md)
        for x in self.reps:
            self.assertIn(rep_row(x, label(x, "0.5")), self.md)

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-CDS-SIZE.md not written yet")
    def test_md_grades(self):
        rg = self.rg
        lines = self.md.splitlines()
        for k, prior in PRIORS.items():
            end = "| {:.2f} | **{}** |".format(prior, "true" if rg["g"][k] else "false")
            hits = [ln for ln in lines if ln.startswith("| %s |" % k)]
            self.assertEqual(len(hits), 1, k)
            self.assertTrue(hits[0].rstrip().endswith(end), hits[0])
        ntrue = sum(1 for v in rg["g"].values() if v)
        self.assertIn("%d of 7 true" % ntrue, self.md)
        self.assertIn("Brier score **%.3f**" % rg["brier"], self.md)
        t1 = "NO_THRESHOLD_IN_RANGE" if rg["ustar"] is None else "THRESHOLD_FOUND"
        self.assertIn("**`%s`**" % t1, self.md)
        self.assertIn("**`%s`**" % rg["t2"], self.md)
        if rg["ustar"] is not None:
            self.assertIn("U = {:,}".format(rg["ustar"]), self.md)
            self.assertIn("{:,.0f} phonemes per recording".format(rg["ppr"]), self.md)
        yn = lambda b: "**yes**" if b else "**no**"
        self.assertIn("whale size within the detecting range: " +
                      yn(rg["ppr"] is not None and rg["ppr"] <= WHALE), self.md)
        self.assertIn("finch size within the detecting range: " +
                      yn(rg["ppr"] is not None and rg["ppr"] <= FINCH), self.md)


class TestFormatsOnToyRows(unittest.TestCase):
    """Runs always: the fixed formats and the regrade on a hand-worked toy set."""

    def toy(self, u, r, p2, d1n):
        return {"u": u, "rep": r, "phonemes": 1000 * u // 10, "m2": {"0.5": {"z": 2.347, "p": p2}},
                "m1_p": {"0.5": 1 / 101}, "d1_n_favour": d1n,
                "published_controls_p": {"0.5": [1 / 101, 1 / 101]}, "boundary_f1_0.5": 0.5}

    def test_rows(self):
        x = self.toy(1200, 0, 1 / 101, 8)
        self.assertEqual(rep_row(x, label(x, "0.5")),
                         "| 1,200 | 0 | 120,000 | `BEYOND_SECOND_ORDER` | 2.35 | 0.010 | 8 of 8 "
                         "| yes | 0.500 |")
        self.assertEqual(size_row(70, 5, 646.66, 1, 0, 0, 0, -0.123, 0.5291),
                         "| 70 | 5 | 647 | 1 of 5 | **0 of 5** | 0 of 5 | 0 of 5 | -0.12 | 0.529 |")

    def test_regrade_toy(self):
        # detected only at 600 and 1200 (p2 = 1/101); D1 majority exactly there
        reps = []
        for u, n in DESIGN:
            for r in range(n):
                big = u >= 600
                reps.append(self.toy(u, r, 1 / 101 if big else 50 / 101, 8 if big else 2))
        rg = regrade(reps)
        self.assertEqual(rg["ustar"], 600)
        self.assertEqual(rg["ppr"], 60000 / 8)              # phonemes 60,000 / 8 recordings
        self.assertEqual(rg["t2"], "D1_TRACKS_DETECTION")   # 3 of 3 vs 0 of 14
        self.assertEqual((rg["ry"], rg["rn"]), (1.0, 0.0))
        g = rg["g"]
        self.assertEqual((g["Z1"], g["Z2"], g["Z3"], g["Z4"], g["Z5"], g["Z6"], g["Z7"]),
                         (True, True, True, True, True, True, False))
        # (.0625 * 3 + .25 + .0225 * 2 + .16) / 7 = .6425 / 7
        self.assertAlmostEqual(rg["brier"], 0.6425 / 7, places=12)


if __name__ == "__main__":
    unittest.main()
