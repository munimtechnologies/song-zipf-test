# SPDX-License-Identifier: Apache-2.0
# Tests for calib.py (synthetic calibration, PREREG-AMENDMENT-2.md).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import json
import os
import random
import shutil
import tempfile
import time
import unittest

import calib as C

ALL_LABELS = {"BEYOND_SECOND_ORDER", "EXPLAINED_BY_SECOND_ORDER", "EXPLAINED_BY_FIRST_ORDER"}


class TestGenerators(unittest.TestCase):
    def test_dirichlet(self):
        rng = random.Random(1)
        for alpha in (0.01, 0.2, 1.0, 5.0):
            w = C.dirichlet(8, alpha, rng)
            self.assertEqual(len(w), 8)
            self.assertTrue(all(x >= 0 for x in w))
            self.assertAlmostEqual(sum(w), 1.0, places=9)

    def test_markov1_cycle(self):
        V = 4
        P = [[1.0 if b == (a + 1) % V else 0.0 for b in range(V)] for a in range(V)]
        seq = C.gen_markov1(P, 9, random.Random(2))
        self.assertEqual(len(seq), 9)
        for a, b in zip(seq, seq[1:]):
            self.assertEqual((b - a) % V, 1)

    def test_markov2_rule(self):
        V = 5
        P2 = {(a, b): [1.0 if c == (a + b) % V else 0.0 for c in range(V)]
              for a in range(V) for b in range(V)}
        seq = C.gen_markov2(P2, V, 12, random.Random(3))
        self.assertEqual(len(seq), 12)
        for i in range(2, 12):
            self.assertEqual(seq[i], (seq[i - 2] + seq[i - 1]) % V)

    def test_words_single_word(self):
        seq = C.gen_words([(0, 1, 2)], [1.0], 7, random.Random(4))
        self.assertEqual(seq, [0, 1, 2, 0, 1, 2, 0])

    def test_words_noise(self):
        seq = C.gen_words([(0, 1, 2)], [1.0], 50, random.Random(5), noise=1.0, V=8)
        self.assertEqual(len(seq), 50)
        self.assertTrue(all(0 <= s < 8 for s in seq))

    def test_lexicon(self):
        lex = C.make_lexicon(12, 3, 7, 8, random.Random(6))
        self.assertEqual(len(lex), 12)
        self.assertEqual(len(set(lex)), 12)
        self.assertTrue(all(3 <= len(w) <= 7 for w in lex))

    def test_dataset_shapes_and_determinism(self):
        for sc in C.SCENARIO_DEF:
            d1 = C.make_dataset(sc, random.Random(7), n_rec=3, n_bouts=4, lmin=20, lmax=20)
            d2 = C.make_dataset(sc, random.Random(7), n_rec=3, n_bouts=4, lmin=20, lmax=20)
            self.assertEqual(d1, d2)
            self.assertEqual(len(d1), 3)
            for rec in d1:
                self.assertEqual(len(rec), 4)
                for b in rec:
                    self.assertEqual(len(b), 20)
                    self.assertTrue(all(0 <= s < 8 for s in b))

    def test_seeds_distinct(self):
        seeds = {C.task_seed(sc, rep) for sc in C.SCENARIO_DEF for rep in range(20)}
        self.assertEqual(len(seeds), len(C.SCENARIO_DEF) * 20)


class TestTask(unittest.TestCase):
    def _task(self, sc="words_zipf"):
        return dict(scenario=sc, rep=0, B=4, n_rec=4, n_bouts=6, lmin=40, lmax=60, V=8,
                    theta=0.5, deadline=time.time() + 3600)

    def test_run_task(self):
        r = C.run_task(self._task())
        self.assertFalse(r["skipped"])
        self.assertIn(r["label"], ALL_LABELS)
        self.assertEqual(set(r["nulls"]), {"shuffle", "markov1_pooled", "markov2_pooled", "rotate"})
        self.assertTrue(0.0 <= r["real_r2"] <= 1.0)
        r2 = C.run_task(self._task())
        self.assertEqual(r["real_r2"], r2["real_r2"])
        self.assertEqual(json.dumps(r["nulls"], sort_keys=True),
                         json.dumps(r2["nulls"], sort_keys=True))

    def test_deadline_skips(self):
        t = self._task()
        t["deadline"] = time.time() - 1
        self.assertTrue(C.run_task(t)["skipped"])


def _fake(sc, rep, p_sh, p_rot, p1, p2, label, r2=0.9):
    nulls = {}
    for name, p in (("shuffle", p_sh), ("rotate", p_rot), ("markov1_pooled", p1),
                    ("markov2_pooled", p2)):
        nulls[name] = {"z": 3.0, "p": p, "null_mean": 0.5, "null_sd": 0.1}
    return {"scenario": sc, "rep": rep, "skipped": False, "real_r2": r2,
            "cuts_per_bout": 10.0, "n_types_total": 100, "nulls": nulls, "label": label,
            "d1_n_favour_order2": 20, "d1_mean": 0.1, "n_rec": 30, "seconds": 1.0}


class TestAggregate(unittest.TestCase):
    def test_aggregate_and_grade(self):
        res = [
            _fake("markov1_a0.2", 0, 0.01, 0.01, 0.5, 0.6, "EXPLAINED_BY_FIRST_ORDER", 0.85),
            _fake("markov1_a0.2", 1, 0.01, 0.20, 0.5, 0.6, "EXPLAINED_BY_FIRST_ORDER", 0.95),
            _fake("words_zipf", 0, 0.01, 0.01, 0.01, 0.01, "BEYOND_SECOND_ORDER"),
            _fake("words_zipf", 1, 0.01, 0.01, 0.01, 0.30, "EXPLAINED_BY_SECOND_ORDER"),
            {"scenario": "words_zipf", "rep": 2, "skipped": True},
        ]
        agg = C.aggregate(res)
        m = agg["markov1_a0.2"]
        self.assertEqual(m["n_reps"], 2)
        self.assertAlmostEqual(m["real_r2_mean"], 0.90)
        self.assertAlmostEqual(m["frac_pass_published_controls"], 0.5)
        self.assertAlmostEqual(m["nulls"]["markov1_pooled"]["frac_p_lt_alpha"], 0.0)
        w = agg["words_zipf"]
        self.assertEqual(w["n_reps"], 2)
        self.assertAlmostEqual(w["frac_beyond_second_order"], 0.5)
        g = C.grade(agg)
        self.assertTrue(g["predictions"]["C1_markov1_a0.2_mean_r2_ge_0.80"])
        self.assertFalse(g["predictions"]["C2_markov1_a0.2_pass_published_controls_ge_0.80"])
        self.assertTrue(g["predictions"]["C3_markov1_a0.2_markov1_null_rejects_le_0.15"])
        self.assertTrue(g["predictions"]["C5_words_zipf_beyond_second_order_ge_0.50"])
        self.assertIsNone(g["predictions"]["C4_markov2_a0.2_beyond_second_order_le_0.15"])
        self.assertFalse(g["rules"]["R2_low_power_relabel_explained_as_not_distinguishable"])
        self.assertFalse(g["rules"]["R3_published_controls_do_not_separate_words_from_first_order_rules"])
        self.assertIsNone(g["rules"]["R1_size_caveat_on_beyond_second_order"])

    def test_grade_empty(self):
        g = C.grade({})
        self.assertTrue(all(v is None for v in g["predictions"].values()))
        self.assertTrue(all(v is None for v in g["rules"].values()))


class TestMain(unittest.TestCase):
    def test_main_quick(self):
        d = tempfile.mkdtemp()
        try:
            C.main(["--out-dir", d, "--reps", "1", "--B", "2", "--procs", "1",
                    "--n-rec", "3", "--n-bouts", "5"])
            with open(os.path.join(d, "calib_results.json"), encoding="utf-8") as f:
                out = json.load(f)
            self.assertEqual(out["n_tasks"], len(C.SCENARIOS))
            self.assertIn("grading", out)
            with open(os.path.join(d, "calib_tasks.jsonl"), encoding="utf-8") as f:
                self.assertEqual(len(f.read().strip().splitlines()), len(C.SCENARIOS))
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
