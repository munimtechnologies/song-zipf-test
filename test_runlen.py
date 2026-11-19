# SPDX-License-Identifier: Apache-2.0
# Tests for runlen.py (RUNLEN-PREREG.md, song-zipf-test). Standard library only; runlen.py
# imports hold/zipfseg/whale_run only inside main(), so these tests need no other module.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import random
import unittest

import runlen as RL


def T(s):
    return tuple(s)


class TestTokenize(unittest.TestCase):
    def test_examples(self):
        self.assertEqual(RL.tokenize(list("aabaab")), [[T("aab"), 2]])
        self.assertEqual(RL.tokenize(list("xababa")),
                         [[T("x"), 1], [T("ab"), 2], [T("a"), 1]])
        self.assertEqual(RL.tokenize(list("aaaa")), [[T("a"), 4]])
        self.assertEqual(RL.tokenize([]), [])
        self.assertEqual(RL.tokenize(list("abc")), [[T("a"), 1], [T("b"), 1], [T("c"), 1]])
        self.assertEqual(RL.tokenize(list("abababx")), [[T("ab"), 3], [T("x"), 1]])
        self.assertEqual(RL.tokenize(list("abab"), lmax=1),
                         [[T("a"), 1], [T("b"), 1], [T("a"), 1], [T("b"), 1]])

    def test_lossless_and_shape(self):
        for seed in range(300):
            rng = random.Random(seed)
            seq = [rng.choice("abc") for _ in range(rng.randint(0, 60))]
            toks = RL.tokenize(seq)
            self.assertEqual(RL.expand(toks), seq)
            for cell, r in toks:
                self.assertTrue(1 <= len(cell) <= RL.LMAX)
                self.assertTrue(r >= 1)
                if r == 1:
                    self.assertEqual(len(cell), 1)

    def test_rec(self):
        rec = [list("aab"), list("cc"), []]
        t = RL.tokenize_rec(rec)
        self.assertEqual(t, [[[T("a"), 2], [T("b"), 1]], [[T("c"), 2]], []])
        self.assertEqual(RL.expand_rec(t), rec)
        self.assertEqual(RL.n_sym([rec]), [5])


def trec_a():
    return [[[T("ab"), 2], [T("c"), 1], [T("ab"), 3]],
            [[T("ab"), 4], [T("de"), 2], [T("c"), 5]]]


def elements(trec):
    return sum(len(c) * r for toks in trec for c, r in toks)


class TestPermutations(unittest.TestCase):
    def test_counts_by_cell(self):
        orig = trec_a()
        for seed in range(50):
            new, n, moved = RL.shuffle_counts(orig, random.Random(seed), "cell")
            self.assertEqual(orig, trec_a())                      # input not changed
            self.assertEqual(n, 5)
            self.assertIn(moved, (0, 2, 3))
            self.assertEqual([[c for c, _ in toks] for toks in new],
                             [[c for c, _ in toks] for toks in orig])
            self.assertEqual(sorted([new[0][0][1], new[0][2][1], new[1][0][1]]), [2, 3, 4])
            self.assertEqual(new[1][1][1], 2)
            self.assertEqual(new[0][1][1], 1)
            self.assertEqual(new[1][2][1], 5)

    def test_counts_by_length(self):
        orig = trec_a()
        seen_moved = set()
        for seed in range(50):
            new, n, moved = RL.shuffle_counts(orig, random.Random(seed), "length")
            self.assertEqual(n, 5)
            self.assertEqual(elements(new), 28)
            self.assertEqual(sorted([new[0][0][1], new[0][2][1], new[1][0][1],
                                     new[1][1][1]]), [2, 2, 3, 4])
            self.assertEqual(new[0][1][1], 1)
            self.assertEqual(new[1][2][1], 5)
            seen_moved.add(moved)
        self.assertTrue(max(seen_moved) > 0)

    def test_cells(self):
        orig = [[[T("ab"), 2], [T("c"), 3], [T("de"), 4]],
                [[T("fgh"), 2], [T("xy"), 1]]]
        for seed in range(50):
            new, n, moved = RL.shuffle_cells(orig, random.Random(seed))
            self.assertEqual(n, 3)
            self.assertIn(moved, (0, 2))
            self.assertEqual([[r for _, r in toks] for toks in new], [[2, 3, 4], [2, 1]])
            self.assertEqual(sorted([new[0][0][0], new[0][2][0]]), [T("ab"), T("de")])
            self.assertEqual(new[0][1][0], T("c"))
            self.assertEqual(new[1][0][0], T("fgh"))
            self.assertEqual(new[1][1][0], T("xy"))
            self.assertEqual(elements(new), 23)

    def test_permute_set(self):
        recs, n, moved = RL.permute_set([trec_a()], "M2", 1)
        self.assertEqual(n, 5)
        self.assertEqual(RL.n_sym(recs), [28])
        self.assertEqual(RL.permute_set([trec_a()], "M2", 1), (recs, n, moved))
        for k in RL.KINDS:
            r2, n2, _ = RL.permute_set([trec_a()], k, 3)
            self.assertEqual(len(r2), 1)
            self.assertEqual(len(r2[0]), 2)
        with self.assertRaises(ValueError):
            RL.permute(trec_a(), "M9", random.Random(0))


class TestStatistics(unittest.TestCase):
    def test_cond_info(self):
        ab, cd = T("ab"), T("cd")
        self.assertAlmostEqual(RL.cond_info([(ab, 2), (ab, 2), (cd, 3), (cd, 3)]), 1.0,
                               places=12)
        self.assertAlmostEqual(RL.cond_info([(ab, 2), (ab, 3), (cd, 2), (cd, 3)]), 0.0,
                               places=12)
        self.assertAlmostEqual(RL.cond_info([(T("a"), 2), (T("a"), 2), (cd, 3), (cd, 3)]),
                               0.0, places=12)
        self.assertEqual(RL.cond_info([]), 0.0)

    def test_count_specificity(self):
        spec = [[[[T("ab"), 2], [T("cd"), 4]] * 20]]
        cs = RL.count_specificity(spec, b=200, seed=1)
        self.assertAlmostEqual(cs["real"], 40.0, places=9)
        self.assertLess(cs["p"], 0.05)
        self.assertEqual(cs["label"], "COUNTS_CELL_SPECIFIC")
        flat = [[[[T("ab"), 2], [T("ab"), 4], [T("cd"), 2], [T("cd"), 4]] * 10]]
        cs2 = RL.count_specificity(flat, b=200, seed=1)
        self.assertEqual(cs2["p"], 1.0)
        self.assertEqual(cs2["label"], "NO_CELL_SPECIFIC_COUNTS")

    def test_pval_tol(self):
        self.assertEqual(RL.pval_tol(1.0, [1.0, 0.5, 1.0 - 1e-12]), 0.75)

    def test_describe(self):
        tr = [[[T("ab"), 2], [T("c"), 1], [T("ab"), 3]], [[T("ab"), 3], [T("de"), 2]]]
        d = RL.describe(tr)
        self.assertEqual(d["elements"], 21)
        self.assertEqual(d["runs"], 5)
        self.assertEqual(d["repeated_runs"], 4)
        self.assertAlmostEqual(d["share_elements_in_repeated_runs"], 20 / 21)
        self.assertEqual(d["distinct_repeated_cells"], 2)
        self.assertEqual(d["repeated_runs_of_recurring_cells"], 3)
        self.assertEqual(d["repeated_runs_by_cell_length"], {"2": 4})
        self.assertAlmostEqual(d["mean_copies"], 2.5)
        self.assertEqual(d["max_copies"], 3)
        self.assertAlmostEqual(d["share_at_modal_count"], 0.75)


def make_res(dets, neg_p=1.0, m0_gain=RL.HOLD_GAIN, m0_p=RL.HOLD_P, moved=None,
             cs_p=0.001, drop_last=None):
    moved = moved or {"M1": 5, "M2": 5, "M3": 5}
    rows = []
    for kind, nd in zip(RL.KINDS, dets):
        for i in range(RL.N_SHUF):
            if drop_last == kind and i == RL.N_SHUF - 1:
                continue
            rows.append({"kind": kind, "i": i, "runs_in_groups": 10, "moved": moved[kind],
                         "test": {"p": 0.01 if i < nd else 0.5, "mean_gain": -0.06}})
    return {"whale_status": "ok",
            "m0": {"lossless": True, "test": {"p": m0_p, "mean_gain": m0_gain}},
            "neg": {"test": {"p": neg_p, "mean_gain": -0.1}},
            "count_specificity": {"p": cs_p, "label": ("COUNTS_CELL_SPECIFIC" if cs_p < 0.05
                                                       else "NO_CELL_SPECIFIC_COUNTS")},
            "permuted": rows}


class TestGrade(unittest.TestCase):
    def rules(self, res):
        return RL.grade(res)["rules"]

    def test_all_survive(self):
        g = RL.grade(make_res((5, 5, 5)))
        r = g["rules"]
        self.assertEqual(r["pipeline"], "PIPELINE_OK")
        self.assertEqual(r["control"], "CONTROL_OK")
        self.assertEqual(r["R1_copy_counts"], "COUNTS_NOT_NEEDED")
        self.assertEqual(r["R2_placement"], "PLACEMENT_NOT_NEEDED")
        self.assertEqual(r["R3_count_specificity"], "COUNTS_CELL_SPECIFIC")
        self.assertEqual(r["detected"], {"M1": 5, "M2": 5, "M3": 5})
        self.assertAlmostEqual(r["moved_share"]["M1"], 0.5)
        self.assertEqual(g["predictions"], {"Q1": True, "Q2": True, "Q3": True, "Q4": True,
                                            "Q5": True, "Q6": True, "Q7": True})
        self.assertEqual(g["n_scored"], 7)
        self.assertAlmostEqual(g["brier"], 0.75 / 7)

    def test_cell_specific(self):
        r = self.rules(make_res((3, 1, 0)))
        self.assertEqual(r["R1_copy_counts"], "CELL_SPECIFIC_COUNTS_CARRY_IT")
        self.assertEqual(r["R2_placement"], "PLACEMENT_CARRIES_IT")

    def test_context_specific_and_mixed(self):
        r = self.rules(make_res((1, 5, 2)))
        self.assertEqual(r["R1_copy_counts"], "CONTEXT_SPECIFIC_COUNTS_CARRY_IT")
        self.assertEqual(r["R2_placement"], "MIXED")
        self.assertEqual(self.rules(make_res((2, 5, 5)))["R1_copy_counts"], "MIXED")

    def test_inert(self):
        r = self.rules(make_res((5, 1, 5), moved={"M1": 1, "M2": 5, "M3": 5}))
        self.assertEqual(r["R1_copy_counts"], "COUNTS_CARRY_IT_M1_INERT")
        self.assertEqual(r["R2_placement"], "PLACEMENT_NOT_NEEDED")
        r = self.rules(make_res((5, 5, 5), moved={"M1": 1, "M2": 5, "M3": 1}))
        self.assertEqual(r["R1_copy_counts"], "COUNTS_NOT_NEEDED")
        self.assertEqual(r["R2_placement"], "M3_INERT")

    def test_controls(self):
        g = RL.grade(make_res((5, 5, 5), neg_p=0.01))
        self.assertEqual(g["rules"]["control"], "CONTROL_FAILED")
        self.assertEqual(g["rules"]["R1_copy_counts"], "CONTROL_FAILED")
        self.assertEqual(g["rules"]["R2_placement"], "CONTROL_FAILED")
        self.assertFalse(g["predictions"]["Q6"])
        g = RL.grade(make_res((5, 5, 5), m0_gain=-0.03))
        self.assertEqual(g["rules"]["pipeline"], "PIPELINE_FAILED")
        self.assertEqual(g["rules"]["R1_copy_counts"], "PIPELINE_FAILED")
        self.assertFalse(g["predictions"]["Q1"])
        self.assertEqual(self.rules(make_res((5, 5, 5), m0_p=0.2))["pipeline"],
                         "PIPELINE_FAILED")
        self.assertEqual(self.rules(make_res((5, 5, 5), cs_p=0.3))["R3_count_specificity"],
                         "NO_CELL_SPECIFIC_COUNTS")

    def test_incomplete(self):
        g = RL.grade(make_res((5, 5, 5), drop_last="M2"))
        self.assertEqual(g["rules"]["R1_copy_counts"], "INCOMPLETE")
        self.assertIsNone(g["predictions"]["Q4"])
        self.assertIsNone(g["predictions"]["Q7"])
        self.assertEqual(g["n_scored"], 5)

    def test_missing(self):
        g = RL.grade({"whale_status": "missing"})
        self.assertEqual(g["rules"]["pipeline"], "WHALE_DATA_MISSING")
        self.assertEqual(g["rules"]["R1_copy_counts"], "WHALE_DATA_MISSING")
        self.assertEqual(g["rules"]["R3_count_specificity"], "WHALE_DATA_MISSING")
        self.assertEqual(g["n_scored"], 0)
        self.assertIsNone(g["brier"])


class TestConfig(unittest.TestCase):
    def test_seeds_distinct(self):
        seeds = [RL.perm_seed(k, i) for k in RL.KINDS for i in range(RL.N_SHUF)]
        tests = [s + 1 for s in seeds]
        others = [RL.SEED + 5, RL.SEED + 7, RL.SEED + 8, RL.SEED + 9, RL.HOLD_SEED]
        allv = seeds + tests + others
        self.assertEqual(len(set(allv)), len(allv))

    def test_constants(self):
        self.assertEqual(sorted(RL.PRIORS), ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7"])
        self.assertEqual(RL.HOLD_P, 1.0 / 201)
        self.assertEqual(RL.HOLD_SEED, 20261120)
        self.assertFalse(hasattr(RL, "H"))


if __name__ == "__main__":
    unittest.main()
