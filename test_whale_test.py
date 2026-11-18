# SPDX-License-Identifier: Apache-2.0
# Tests for whale_read.py and whale_test.py (stdlib only; zipfseg.py from the same repo).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import json
import math
import os
import random
import shutil
import tempfile
import time
import unittest
from collections import Counter

import whale_read as R
import whale_test as W
import zipfseg as Z


def table_s1_data(rng, alphabet=("a", "b", "c", "d")):
    """Synthetic songs with exactly Table S1's recordings and elements per year;
    every recording has >= 10 elements."""
    data = {}
    for y, (nr, ne) in R.TABLE_S1.items():
        lens = [10] * (nr - 1) + [ne - 10 * (nr - 1)]
        data[y] = [[rng.choice(alphabet) for _ in range(n)] for n in lens]
    return data


def write_row_csv(path, data):
    with open(path, "w", encoding="utf-8") as f:
        for y in sorted(data):
            for i, rec in enumerate(data[y]):
                f.write('%d,rec%d,"%s"\n' % (y, i, ", ".join(rec)))


class TestReader(unittest.TestCase):
    def test_tokens(self):
        self.assertEqual(R.tokens("gr(s)-dws(s), sq, 'sq'"), ["gr(s)-dws(s)", "sq", "sq"])
        self.assertEqual(R.tokens("  [a;b\tc]  "), ["a", "b", "c"])
        self.assertEqual(R.tokens(""), [])

    def test_year_of(self):
        self.assertEqual(R.year_of("NC_2015_rec3"), 2015)
        self.assertEqual(R.year_of("2015.0"), 2015)
        self.assertIsNone(R.year_of("20150"))
        self.assertIsNone(R.year_of("2018"))
        self.assertIsNone(R.year_of("songs.csv"))

    def test_layout_row(self):
        rows = [["2010", "rec1", "a b c d e f g h i j"],
                ["2011", "r2", "a,b,c,d,e,f,g,h,i,j,k"],
                ["2011", "short", "a b"]]
        d = R.layout_row("t.csv", rows)
        self.assertEqual(sorted(d), [2010, 2011])
        self.assertEqual(len(d[2010][0]), 10)
        self.assertEqual(len(d[2011]), 1)
        self.assertEqual(len(d[2011][0]), 11)
        # year from the table name when no other cell has one
        d2 = R.layout_row("song_2013.txt", [["x " * 12]])
        self.assertEqual(list(d2), [2013])

    def test_layout_long(self):
        rows = [["Year", "Recording", "Element"], ["2010", "A", "x"], ["2010", "A", "y"],
                ["2010", "B", "z"], ["2011", "C", ""], ["2011", "C", "w"]]
        self.assertEqual(R.layout_long("t", rows), {2010: [["x", "y"], ["z"]], 2011: [["w"]]})
        self.assertEqual(R.layout_long("t", [["a", "b"], ["1", "2"]]), {})

    def test_layout_col(self):
        rows = [["2012_a", "2013_b", "notes"]] + [["x", "y", ""] for _ in range(10)]
        self.assertEqual(R.layout_col("t", rows), {2012: [["x"] * 10], 2013: [["y"] * 10]})
        rows = [["Recording 1", "ac"]] + [["x", "y"] for _ in range(10)]
        self.assertEqual(R.layout_col("songs_2014", rows), {2014: [["x"] * 10]})

    def test_layout_file(self):
        self.assertEqual(R.layout_file("S2/2011/r1.txt", [["a"]] * 10), {2011: [["a"] * 10]})
        self.assertEqual(R.layout_file("S2/2011/r1.txt", [["a"]] * 9), {})
        self.assertEqual(R.layout_file("S2/r1.txt", [["a"]] * 10), {})

    def test_read_songs_folder_per_year(self):
        tmp = tempfile.mkdtemp()
        try:
            data = table_s1_data(random.Random(4))
            for y, recs in data.items():
                d = os.path.join(tmp, "Data_S2", str(y))
                os.makedirs(d)
                for i, rec in enumerate(recs):
                    with open(os.path.join(d, "rec%02d.txt" % i), "w") as f:
                        f.write("\n".join(rec) + "\n")
            got, rep = R.read_songs(tmp)
            self.assertIsNotNone(got)
            self.assertTrue(rep["chosen"].startswith("file|GLOBAL"))
            self.assertEqual(got, {y: data[y] for y in sorted(data)})
        finally:
            shutil.rmtree(tmp)

    def test_gate(self):
        data = table_s1_data(random.Random(1))
        ok, rep = R.gate(data)
        self.assertTrue(ok)
        self.assertEqual(rep[2015]["recordings"], 12)
        self.assertEqual(rep[2015]["elements"], 13251)
        data[2016] = data[2016][:-1]
        ok, rep = R.gate(data)
        self.assertFalse(ok)
        self.assertFalse(rep[2016]["ok"])
        self.assertTrue(rep[2017]["ok"])
        # 2% element tolerance
        d = table_s1_data(random.Random(2))
        d[2010][-1] = d[2010][-1][:-21]          # 1053 - 21 = 1032 (within 2%: 21.06)
        self.assertTrue(R.gate(d)[0])
        d[2010][-1] = d[2010][-1][:-1]           # 1031: outside
        self.assertFalse(R.gate(d)[0])

    def test_read_songs_row_csv(self):
        tmp = tempfile.mkdtemp()
        try:
            data = table_s1_data(random.Random(3))
            write_row_csv(os.path.join(tmp, "songs.csv"), data)
            with open(os.path.join(tmp, "notes.txt"), "w") as f:
                f.write("theme frequencies\n")
            got, rep = R.read_songs(tmp)
            self.assertIsNotNone(got)
            self.assertTrue(rep["chosen"].startswith("row|"))
            self.assertEqual(got, {y: data[y] for y in sorted(data)})
        finally:
            shutil.rmtree(tmp)

    def test_read_songs_none(self):
        tmp = tempfile.mkdtemp()
        try:
            with open(os.path.join(tmp, "x.csv"), "w") as f:
                f.write("2010,a b c d e f g h i j k\n")
            got, rep = R.read_songs(tmp)
            self.assertIsNone(got)
            self.assertIsNone(rep["chosen"])
        finally:
            shutil.rmtree(tmp)


class TestStats(unittest.TestCase):
    def test_brevity_and_zipf(self):
        inv = Counter({("a",): 4, ("b", "c"): 2, ("d", "e", "f"): 1})
        s = W.stats([inv])
        self.assertAlmostEqual(s["brev_pool"], 1.0, places=12)
        self.assertAlmostEqual(s["brev_pool_slope"], -math.log10(2), places=12)
        self.assertAlmostEqual(s["brev_year"], 1.0, places=12)
        self.assertAlmostEqual(s["zipf"], Z.zipf_r2([4, 2, 1]), places=12)

    def test_pool_vs_year(self):
        # pooled: ("a",) 2+2=4, ("b","c") 1+1=2 -> 2 points only -> nan
        invs = [Counter({("a",): 2, ("b", "c"): 1}), Counter({("a",): 2, ("b", "c"): 1})]
        s = W.stats(invs)
        self.assertTrue(s["brev_pool"] != s["brev_pool"])
        # by year: 4 points (1, log2), (2, 0), (1, log2), (2, 0) -> R^2 1, slope -log10 2
        self.assertAlmostEqual(s["brev_year"], 1.0, places=12)
        self.assertAlmostEqual(s["brev_year_slope"], -math.log10(2), places=12)

    def test_compare(self):
        c = W.compare(1.0, [0.0, 0.5, 1.0])
        self.assertAlmostEqual(c["p"], 2 / 4)
        self.assertAlmostEqual(c["null_mean"], 0.5)
        self.assertTrue(W.compare(float("nan"), [1, 2])["p"] != W.compare(float("nan"), [1, 2])["p"])

    def test_table_s2_check(self):
        years = sorted(W.TABLE_S2)
        invs = []
        for i, y in enumerate(years):
            inv = Counter()
            for seq, n in W.TABLE_S2[y]:
                inv[seq] = n
            if i >= 6:                      # last two years: wrong top
                inv[("zz",)] = 1000
            invs.append(inv)
        c = W.table_s2_check(years, invs)
        self.assertEqual(c["n_years_top1_match"], 6)
        self.assertTrue(c["reproduced"])
        self.assertEqual(c["per_year"]["2015"]["listed_found"], 3)
        invs[5][("zz",)] = 1000
        self.assertFalse(W.table_s2_check(years, invs)["reproduced"])
        # count tolerance: 10% or 3
        inv = Counter({W.TABLE_S2[2010][0][0]: 34, W.TABLE_S2[2010][1][0]: 17})
        self.assertTrue(W.table_s2_check([2010], [inv])["per_year"]["2010"]["top1_match"])
        inv[W.TABLE_S2[2010][0][0]] = 35
        self.assertFalse(W.table_s2_check([2010], [inv])["per_year"]["2010"]["top1_match"])


def fake_row(p, slope=-0.1, null_mean=0.5):
    nulls = {n: {s: {"p": p.get(n, 0.5), "null_mean": null_mean} for s in W.STATS}
             for n in W.NULL_ORDER}
    return {"real": {"zipf": 0.93, "brev_pool": 0.62, "brev_pool_slope": slope,
                     "brev_year": 0.5, "brev_year_slope": slope}, "nulls": nulls}


class TestGrading(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(W.label(fake_row({"markov2_pooled": 0.01, "markov1_pooled": 0.01}),
                                 "zipf"), "BEYOND_SECOND_ORDER")
        self.assertEqual(W.label(fake_row({"markov1_pooled": 0.01}), "zipf"),
                         "EXPLAINED_BY_SECOND_ORDER")
        self.assertEqual(W.label(fake_row({}), "zipf"), "EXPLAINED_BY_FIRST_ORDER")
        self.assertEqual(W.label(fake_row({"markov2_pooled": 0.01}, slope=0.2), "brev_pool"),
                         "EXPLAINED_BY_FIRST_ORDER")

    def test_grade(self):
        row = fake_row({"shuffle": 0.001, "rotate": 0.001, "markov1_pooled": 0.01})
        rows = {"0.5": row, "0.3": row, "0.7": row}
        g = W.grade(rows, {"reproduced": True}, {"n_favour_order2": 7})
        p = g["predictions"]
        order = ("S-W", "W1", "W2", "W3", "W4", "W5", "W6", "N1", "N2", "N3", "N4", "N5", "N6")
        self.assertEqual(sorted(p), sorted(order))
        self.assertEqual([p[k] for k in order],
                         [True, False, True, False, False, False, True,
                          True, True, True, True, True, False])
        self.assertEqual(g["labels"], {"zipf": "EXPLAINED_BY_SECOND_ORDER",
                                       "brevity": "EXPLAINED_BY_SECOND_ORDER"})
        self.assertEqual(g["robust"], {"zipf": True, "brevity": True})
        self.assertEqual(g["caveats"], [])
        want = sum((W.PRIORS[k] - (1.0 if v else 0.0)) ** 2 for k, v in p.items()) / 13
        self.assertAlmostEqual(g["brier"], want)
        g2 = W.grade(rows, {"reproduced": False}, {"n_favour_order2": 5}, "brev_year")
        self.assertFalse(g2["predictions"]["N3"])     # 0.5 vs 0.62: outside 0.10
        self.assertFalse(g2["predictions"]["N1"])
        self.assertFalse(g2["predictions"]["W6"])
        self.assertEqual(len(g2["caveats"]), 2)
        # no reproduction of the published controls -> REPRODUCTION_FAILED
        g3 = W.grade({"0.5": fake_row({"markov2_pooled": 0.01})}, {"reproduced": True},
                     {"n_favour_order2": 8})
        self.assertEqual(g3["labels"], {"zipf": "REPRODUCTION_FAILED",
                                        "brevity": "REPRODUCTION_FAILED"})
        self.assertEqual(g3["robust"], {"zipf": False, "brevity": False})
        # W5 reads the markov2 null mean of the Zipf statistic
        hi = fake_row({"shuffle": 0.001}, null_mean=0.85)
        self.assertTrue(W.grade({"0.5": hi}, {"reproduced": True},
                                {"n_favour_order2": 0})["predictions"]["W5"])

    def test_final_reading(self):
        row = fake_row({"shuffle": 0.001, "rotate": 0.001, "markov1_pooled": 0.01})
        g = W.grade({"0.5": row}, {"reproduced": True}, {"n_favour_order2": 7})
        f = W.final_reading(g)
        self.assertEqual(f["zipf"]["label"], "EXPLAINED_BY_SECOND_ORDER")
        self.assertFalse(f["zipf"]["headline"])
        f = W.final_reading(g, {"K5": True, "K6": False}, {"Q10": True, "Q11": True})
        self.assertEqual(f["zipf"]["label"], "NOT_DISTINGUISHABLE")
        self.assertEqual(f["brevity"]["label"], "EXPLAINED_BY_SECOND_ORDER")
        self.assertTrue(f["brevity"]["headline"])
        rowb = fake_row({"shuffle": 0.001, "rotate": 0.001, "markov2_pooled": 0.01})
        gb = W.grade({"0.5": rowb}, {"reproduced": True}, {"n_favour_order2": 7})
        fb = W.final_reading(gb, {"K5": False, "K6": True}, {"Q10": True, "Q11": True})
        self.assertEqual(fb["zipf"]["label"], "BEYOND_SECOND_ORDER")
        self.assertFalse(fb["zipf"]["headline"])
        self.assertTrue(fb["brevity"]["headline"])
        gn = W.grade({"0.5": rowb}, {"reproduced": False}, {"n_favour_order2": 7})
        self.assertFalse(W.final_reading(gn, {"K5": True}, {"Q10": True})["zipf"]["headline"])


class TestRun(unittest.TestCase):
    def test_run_theta_small(self):
        rng = random.Random(5)
        years = [[[rng.choice("abcd") for _ in range(60)] for _ in range(3)] for _ in range(2)]
        far = time.time() + 600
        a, inv_a = W.run_theta(years, 0.5, 3, far)
        b, inv_b = W.run_theta(years, 0.5, 3, far)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertEqual(sorted(a["nulls"]), sorted(W.NULL_ORDER))
        for n in W.NULL_ORDER:
            self.assertEqual(a["nulls"][n]["B_done"], 3)
        self.assertEqual(sum(sum(i.values()) for i in inv_a), a["n_chunks"])
        self.assertEqual(sum(len(s) * v for i in inv_a for s, v in i.items()), 360)
        c, _ = W.run_theta(years, 0.5, 3, time.time() - 1)    # past deadline: no nulls
        self.assertEqual(c["nulls"]["shuffle"]["B_done"], 0)
        d, inv_d = W.run_theta(years, 0.5, 2, far, rule="prev_over_cur")
        self.assertEqual(d["rule"], "prev_over_cur")
        self.assertEqual(sum(len(s) * v for i in inv_d for s, v in i.items()), 360)
        self.assertEqual(d["nulls"]["rotate"]["B_done"], 2)

    def test_main_end_to_end(self):
        tmp = tempfile.mkdtemp()
        try:
            src = os.path.join(tmp, "data")
            os.makedirs(src)
            write_row_csv(os.path.join(src, "songs.csv"), table_s1_data(random.Random(7)))
            out = os.path.join(tmp, "out")
            rc = W.main(["--data-dir", src, "--out-dir", out, "--b-scale", "0.002"])
            self.assertEqual(rc, 0)
            with open(os.path.join(out, "whale_results.json")) as f:
                res = json.load(f)
            self.assertEqual(res["n_recordings"], [4, 6, 6, 6, 7, 12, 7, 7])
            self.assertEqual(sum(res["n_elements"]), 45760)
            self.assertEqual(sorted(res["by_theta"]),
                             ["0.25", "0.3", "0.5", "0.5_reversed", "0.7", "0.75"])
            self.assertEqual(res["by_theta"]["0.5"]["nulls"]["markov1_pooled"]["B_done"], 2)
            self.assertEqual(res["by_theta"]["0.25"]["nulls"]["rotate"]["B_done"], 1)
            self.assertFalse(res["table_s2"]["reproduced"])
            self.assertIn(res["grading"]["labels"]["zipf"],
                          ("BEYOND_SECOND_ORDER", "EXPLAINED_BY_SECOND_ORDER",
                           "EXPLAINED_BY_FIRST_ORDER", "REPRODUCTION_FAILED"))
            self.assertIn("zipf", res["final_reading_before_calibrations"])
            self.assertTrue(os.path.exists(os.path.join(out, "whale_top15_theta0.5.json")))
            # gate failure: nothing computed, report written, exit 0
            bad = os.path.join(tmp, "bad")
            os.makedirs(bad)
            out2 = os.path.join(tmp, "out2")
            self.assertEqual(W.main(["--data-dir", bad, "--out-dir", out2]), 0)
            self.assertTrue(os.path.exists(os.path.join(out2, "whale_read_report.json")))
            self.assertFalse(os.path.exists(os.path.join(out2, "whale_results.json")))
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
