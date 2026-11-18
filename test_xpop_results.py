# SPDX-License-Identifier: Apache-2.0
# test_xpop_results.py: the grader for the independent-bird finch test (XPOP-PREREG.md, job
# song-zipf-xpop-v1), written and published BEFORE the job has run. With its own code it
# re-derives both reading gates, every label, the eleven graded predictions, rules X1-X3, the
# robustness flag, the provisional flag and the Brier score from the raw job output, checks
# every p value and z score for internal consistency, checks them against the job's own grading,
# and fixes now the exact lines RESULTS-XPOP.md must print (render_md_lines).
# Until results/xpop/xpop_results.json exists, the result tests are skipped; the toy-data tests
# run always. Stdlib only. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import hashlib
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "xpop", "xpop_results.json")
MD = os.path.join(HERE, "RESULTS-XPOP.md")
PREREG = os.path.join(HERE, "XPOP-PREREG.md")
ZIPFSEG = os.path.join(HERE, "zipfseg.py")
HAVE = os.path.exists(RES)

ALPHA = 0.05
VERSION = "xpop-1"
# sha256 of zipfseg.py at 742fd83 (the same file the English size curve pins)
ZIPFSEG_SHA256 = "25002193229e6d6568939856de5a1760a41c3b462582ea06b6d75ba6d84bddf5"
ORDER = ("K1", "K2", "K3", "K4", "K5", "K6", "K7", "N1", "N2", "S1", "S2")
PRIORS = {"K1": 0.80, "K2": 0.90, "K3": 0.85, "K4": 0.85, "K5": 0.50, "K6": 0.30,
          "K7": 0.90, "N1": 0.75, "N2": 0.45, "S1": 0.20, "S2": 0.70}
PRED_TEXT = {"K1": "K mean R^2 >= 0.80", "K2": "K beats shuffle and rotation",
             "K3": "K beats bigram_within", "K4": "K beats markov1", "K5": "K beats markov2",
             "K6": "K beats markov3", "K7": "D1 > 0 in at least 80% of K birds",
             "N1": "N beats bigram_within", "N2": "N beats markov2",
             "S1": "KS beats markov2", "S2": "KS beats bigram_within"}
FULL = ("shuffle", "rotate", "bigram_within", "markov1_pooled", "markov2_pooled",
        "markov3_pooled")
SMALL = ("shuffle", "rotate", "bigram_within", "markov1_pooled", "markov2_pooled")
# (data set, theta) -> (B, nulls, block id, optional)   (XPOP-PREREG.md section 4)
BLOCKS = {("K", "0.5"): (200, FULL, "K_0.5", False),
          ("N", "0.5"): (200, FULL, "N_0.5", False),
          ("KS", "0.5"): (1000, SMALL, "KS_0.5", False),
          ("NS", "0.5"): (1000, SMALL, "NS_0.5", False),
          ("K", "0.3"): (50, FULL, "K_0.3", True),
          ("K", "0.7"): (50, FULL, "K_0.7", True),
          ("N", "0.3"): (50, FULL, "N_0.3", True),
          ("N", "0.7"): (50, FULL, "N_0.7", True),
          ("Kraw", "0.5"): (50, FULL, "Kraw_0.5", True)}
HELDOUT = ("K", "N", "KS")
DATASETS = ("K", "Kraw", "N", "KS", "NS")
BSO, B3O, E3O = "BEYOND_SECOND_ORDER", "BEYOND_THIRD_ORDER", "EXPLAINED_BY_THIRD_ORDER"
ESO, EFO = "EXPLAINED_BY_SECOND_ORDER", "EXPLAINED_BY_FIRST_ORDER"


# --------------------------------------------------------------------------
# independent re-implementation of XPOP-PREREG.md sections 3 to 6
# --------------------------------------------------------------------------
def regate_k(stats):
    """Gate K: 11 birds; mean notes within 5% of 17,930.9; mean classes within 0.5 of 8.1."""
    n = len(stats)
    if n == 0:
        return False
    mn = sum(s["notes"] for s in stats) / n
    mc = sum(s["classes"] for s in stats) / n
    return n == 11 and abs(mn - 17930.9) <= 0.05 * 17930.9 and abs(mc - 8.1) <= 0.5


def regate_n(infos):
    """Gate N: 4 birds; each >= 5,000 syllables; <= 1% of files bad or unreadable."""
    files = sum(i["files"] for i in infos)
    bad = sum(i["bad_files"] + i["unreadable_files"] for i in infos)
    return (len(infos) == 4 and all(i["syllables"] >= 5000 for i in infos)
            and files > 0 and bad <= 0.01 * files)


def label(row):
    """Section 4 label from one theta row's p values."""
    p = {k: v["p"] for k, v in row["nulls"].items()}
    if "markov3_pooled" in p:
        if p["markov3_pooled"] < ALPHA:
            return B3O
        if p["markov2_pooled"] < ALPHA:
            return E3O
    elif p["markov2_pooled"] < ALPHA:
        return BSO
    if p["markov1_pooled"] < ALPHA:
        return ESO
    return EFO


def row_of(res, d, th="0.5"):
    return res.get(d, {}).get("by_theta", {}).get(th)


def beats(row, name):
    return None if row is None else row["nulls"][name]["p"] < ALPHA


def p_ok(p, n):
    """p = (1 + k) / (1 + n) for an integer 0 <= k <= n."""
    k = p * (n + 1) - 1
    return abs(k - round(k)) < 1e-6 and 0 <= round(k) <= n


def fmean(v):
    v = [a for a in v if a == a]
    return sum(v) / len(v) if v else float("nan")


def regrade(res, gate_k, gate_n):
    k, n, ks = row_of(res, "K"), row_of(res, "N"), row_of(res, "KS")
    hk = res.get("K", {}).get("heldout")
    g = {"K1": None if k is None else k["real_mean_r2"] >= 0.80,
         "K2": None if k is None else (beats(k, "shuffle") and beats(k, "rotate")),
         "K3": beats(k, "bigram_within"), "K4": beats(k, "markov1_pooled"),
         "K5": beats(k, "markov2_pooled"), "K6": beats(k, "markov3_pooled"),
         "K7": (None if hk is None else
                5 * hk["d1_n_favour_order2"] >= 4 * hk["n_recordings"]),
         "N1": beats(n, "bigram_within"), "N2": beats(n, "markov2_pooled"),
         "S1": beats(ks, "markov2_pooled"), "S2": beats(ks, "bigram_within")}
    graded = [x for x in ORDER if g[x] is not None]
    brier = (sum((PRIORS[x] - (1.0 if g[x] else 0.0)) ** 2 for x in graded) / len(graded)
             if graded else float("nan"))
    labels = {}
    for d, th in BLOCKS:
        row = row_of(res, d, th)
        if row is not None:
            labels.setdefault(d, {})[th] = label(row)

    def three(a, b, both, neither, mixed):
        if a is None or b is None:
            return "NOT_GRADED"
        if a and b:
            return both
        return neither if not (a or b) else mixed
    x1 = three(g["K3"], g["N1"], "ABOVE_BIGRAM_REPLICATES", "ABOVE_BIGRAM_FAILS",
               "ABOVE_BIGRAM_MIXED")
    x2 = three(g["K5"], g["N2"], "FINCH_ZIPF_BEYOND_SECOND_ORDER",
               "SECOND_ORDER_EXPLAINS_FINCH_ZIPF", "SECOND_ORDER_MIXED")
    if g["K5"] is None or g["S1"] is None:
        x3 = "NOT_GRADED"
    elif g["S1"]:
        x3 = "BEYOND_EVEN_AT_KIRBY_SIZE"
    elif g["K5"]:
        x3 = "SIZE_DEPENDENT"
    else:
        x3 = "NOT_BEYOND_AT_EITHER_SIZE"
    lk = labels.get("K", {})
    robust = all(t in lk for t in ("0.3", "0.5", "0.7")) and len(set(lk.values())) == 1
    return {"g": g, "graded": graded, "brier": brier, "labels": labels,
            "rules": {"X1": x1, "X2": x2, "X3": x3, "robust_K": robust},
            "provisional": not (gate_k and gate_n), "gates": {"K": gate_k, "N": gate_n}}


# --------------------------------------------------------------------------
# formats fixed before the result exists (RESULTS-XPOP.md must contain these lines)
# --------------------------------------------------------------------------
def yn(b):
    return "**yes**" if b else "**no**"


def describe_row(d, x):
    """| data | recordings (birds) | bouts | notes | transitions | longest bout |"""
    return "| {} | {} | {:,} | {:,} | {:,} | {} |".format(
        d, x["recordings"], x["bouts"], x["symbols"], x["transitions"], x["max_bout_length"])


def null_row(d, th, name, row):
    """| data | theta | null | real R^2 | null mean R^2 | gap | z | p | nulls |"""
    c = row["nulls"][name]
    return "| {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} | {:.2f} | {:.3f} | {} |".format(
        d, th, name, row["real_mean_r2"], c["null_mean"], row["real_mean_r2"] - c["null_mean"],
        c["z"], c["p"], c["n_null"])


def label_row(d, th, lab):
    return "| {} | {} | `{}` |".format(d, th, lab)


def heldout_row(d, h):
    """| data | D1 > 0 | mean D1 | D2 > 0 | mean D2 |"""
    n = h["n_recordings"]
    return "| {} | {} of {} | {:+.4f} | {} of {} | {:+.4f} |".format(
        d, h["d1_n_favour_order2"], n, fmean(h["d1_per_recording"]),
        h["d2_n_favour_order3"], n, fmean(h["d2_per_recording"]))


def pred_end(k, v):
    return "| {:.2f} | **{}** |".format(
        PRIORS[k], "not graded" if v is None else ("true" if v else "false"))


def required_strings(r, rg):
    need = ["Gate K: " + ("**pass**" if rg["gates"]["K"] else "**fail**"),
            "Gate N: " + ("**pass**" if rg["gates"]["N"] else "**fail**")]
    for d in DATASETS:
        if d in r.get("describe", {}):
            need.append(describe_row(d, r["describe"][d]))
    res = r["results"]
    for d, th in sorted(BLOCKS):
        row = row_of(res, d, th)
        if row is None:
            continue
        need.append(label_row(d, th, label(row)))
        for name in BLOCKS[(d, th)][1]:
            need.append(null_row(d, th, name, row))
    for d in HELDOUT:
        h = res.get(d, {}).get("heldout")
        if h:
            need.append(heldout_row(d, h))
    ntrue = sum(1 for x in rg["graded"] if rg["g"][x])
    need.append("%d of %d graded predictions true" % (ntrue, len(rg["graded"])))
    if rg["graded"]:
        need.append("Brier score **%.3f**" % rg["brier"])
    for x in ("X1", "X2", "X3"):
        need.append("%s: **`%s`**" % (x, rg["rules"][x]))
    need.append("K label robust across theta 0.3/0.5/0.7: " + yn(rg["rules"]["robust_K"]))
    need.append("Provisional (a reading gate failed): " + yn(rg["provisional"]))
    return need


def render_md_lines(r, rg):
    """Every fixed line, in one list (prediction rows included), for writing RESULTS-XPOP.md."""
    return required_strings(r, rg) + ["| %s | %s %s" % (k, PRED_TEXT[k], pred_end(k, rg["g"][k]))
                                      for k in ORDER]


def check_md(md, r, rg):
    """List of required lines missing from md (empty list = all present)."""
    missing = [s for s in required_strings(r, rg) if s not in md]
    lines = md.splitlines()
    for k in ORDER:
        hits = [ln for ln in lines if ln.startswith("| %s |" % k)]
        if len(hits) != 1 or not hits[0].rstrip().endswith(pred_end(k, rg["g"][k])):
            missing.append("prediction row " + k)
    return missing


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# --------------------------------------------------------------------------
# result tests (skipped until the job's output is published)
# --------------------------------------------------------------------------
@unittest.skipUnless(HAVE, "results/xpop/xpop_results.json not published yet")
class TestXpopResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        r = cls.r
        cls.gk = regate_k(r["koumura"]["stats"])
        cls.gn = regate_n(r["nicholson"]["birds"])
        cls.rg = regrade(r["results"], cls.gk, cls.gn)
        cls.md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""

    def test_status_registration_pipeline(self):
        r = self.r
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["version"], VERSION)
        self.assertTrue(r["registration"]["found"])
        if os.path.exists(PREREG):          # the job read exactly the published prereg
            self.assertEqual(r["registration"]["sha256"], sha256_file(PREREG))
        ok = {ZIPFSEG_SHA256}
        if os.path.exists(ZIPFSEG):
            ok.add(sha256_file(ZIPFSEG))
        self.assertIn(r["zipfseg_sha256"], ok)

    def test_gates_rederived(self):
        r = self.r
        stats = r["koumura"]["stats"]
        for s in stats:
            self.assertEqual(sum(s["label_counts"].values()), s["notes"], s["bird"])
            self.assertEqual(len(s["label_counts"]), s["classes"], s["bird"])
        g = r["gates"]["K"]
        self.assertEqual(g["birds"], len(stats))
        self.assertEqual(g["pass"], self.gk)
        if stats:
            self.assertAlmostEqual(g["notes_mean"], sum(s["notes"] for s in stats) / len(stats),
                                   places=6)
            self.assertAlmostEqual(g["classes_mean"],
                                   sum(s["classes"] for s in stats) / len(stats), places=9)
        birds = r["nicholson"]["birds"]
        for b in birds:
            self.assertEqual(sum(b["label_counts"].values()), b["syllables"], b["bird"])
            self.assertEqual(len(b["label_counts"]), b["classes"], b["bird"])
        self.assertEqual(r["gates"]["N"]["pass"], self.gn)

    def test_describe_matches_reading(self):
        r = self.r
        ds = r["describe"]
        stats = r["koumura"]["stats"]
        birds = [b for b in r["nicholson"]["birds"] if b["syllables"] > 0]
        for d in ("K", "Kraw"):
            self.assertEqual(ds[d]["recordings"], len(stats))
            self.assertEqual(ds[d]["symbols"], sum(s["notes"] for s in stats))
        self.assertEqual(ds["N"]["recordings"], len(birds))
        self.assertEqual(ds["N"]["symbols"], sum(b["syllables"] for b in birds))
        self.assertEqual(ds["KS"]["recordings"], ds["K"]["recordings"])
        self.assertEqual(ds["NS"]["recordings"], ds["N"]["recordings"])
        self.assertLessEqual(ds["KS"]["symbols"], ds["K"]["symbols"])
        self.assertLessEqual(ds["NS"]["symbols"], ds["N"]["symbols"])
        for d in DATASETS:
            x = ds[d]
            self.assertEqual(sum(x["symbols_per_recording"]), x["symbols"])
            self.assertEqual(len(x["alphabet_per_recording"]), x["recordings"])
            self.assertLessEqual(x["transitions"], x["symbols"])

    def test_blocks_complete_and_consistent(self):
        res = self.r["results"]
        for (d, th), (B, nulls, bid, optional) in BLOCKS.items():
            row = row_of(res, d, th)
            if row is None:
                self.assertTrue(optional, "required block %s missing" % bid)
                self.assertIn(bid, res.get(d, {}).get("not_run", {}), bid)
                continue
            self.assertEqual(sorted(row["nulls"]), sorted(nulls), bid)
            for name in nulls:
                c = row["nulls"][name]
                self.assertLessEqual(c["n_null"], B, (bid, name))
                self.assertGreaterEqual(c["n_null"], 0.9 * B, (bid, name))
                self.assertTrue(p_ok(c["p"], c["n_null"]), (bid, name, c["p"]))
                self.assertAlmostEqual(c["real"], row["real_mean_r2"], places=12)
                if c["null_sd"] > 0:
                    self.assertAlmostEqual(c["z"], (c["real"] - c["null_mean"]) / c["null_sd"],
                                           places=9)
        for d in res:
            for bid in res[d].get("not_run", {}):
                self.assertIn(bid, {v[2] for v in BLOCKS.values() if v[3]}, bid)
        for d in HELDOUT:
            h = res[d]["heldout"]
            n = self.r["describe"][d]["recordings"]
            self.assertEqual(h["n_recordings"], n)
            self.assertEqual(len(h["d1_per_recording"]), n)
            self.assertEqual(len(h["d2_per_recording"]), n)
            self.assertEqual(h["d1_n_favour_order2"], sum(1 for a in h["d1_per_recording"] if a > 0))
            self.assertEqual(h["d2_n_favour_order3"], sum(1 for a in h["d2_per_recording"] if a > 0))

    def test_grading_matches_regrade(self):
        gr = self.r["grading"]
        rg = self.rg
        self.assertEqual(gr["priors"], PRIORS)
        self.assertEqual(gr["predictions"], rg["g"])
        self.assertEqual(gr["graded"], rg["graded"])
        self.assertAlmostEqual(gr["brier"], rg["brier"], places=12)
        self.assertEqual(gr["labels"], rg["labels"])
        self.assertEqual(gr["rules"], rg["rules"])
        self.assertEqual(gr["provisional"], rg["provisional"])

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-XPOP.md not written yet")
    def test_md_lines(self):
        self.assertEqual(check_md(self.md, self.r, self.rg), [])


# --------------------------------------------------------------------------
# toy tests (always run; every expected value worked out by hand)
# --------------------------------------------------------------------------
def toy_row(real, ks, B):
    """ks: null name -> k (number of null sets >= real), so p = (1 + k) / (1 + B)."""
    return {"real_mean_r2": real,
            "nulls": {name: {"real": real, "null_mean": real - 0.01, "null_sd": 0.005, "z": 2.0,
                             "p": (1 + k) / (1 + B), "n_null": B} for name, k in ks.items()}}


def toy_results():
    k = toy_row(0.91, {"shuffle": 0, "rotate": 0, "bigram_within": 0, "markov1_pooled": 0,
                       "markov2_pooled": 29, "markov3_pooled": 119}, 200)
    n = toy_row(0.85, {"shuffle": 0, "rotate": 0, "bigram_within": 0, "markov1_pooled": 0,
                       "markov2_pooled": 4, "markov3_pooled": 49}, 200)
    ks = toy_row(0.83, {"shuffle": 0, "rotate": 0, "bigram_within": 2, "markov1_pooled": 1,
                        "markov2_pooled": 399}, 1000)
    hk = {"d1_per_recording": [0.1] * 9 + [-0.05, -0.05], "d1_n_favour_order2": 9,
          "d2_per_recording": [0.01] * 3 + [-0.01] * 8, "d2_n_favour_order3": 3,
          "n_recordings": 11}
    return {"K": {"by_theta": {"0.5": k, "0.3": k, "0.7": k}, "heldout": hk},
            "N": {"by_theta": {"0.5": n}}, "KS": {"by_theta": {"0.5": ks}}}


class TestToy(unittest.TestCase):
    def test_label(self):
        # K: p3 = 120/201, p2 = 30/201 (0.149), p1 = 1/201 -> second order explains it
        res = toy_results()
        self.assertEqual(label(res["K"]["by_theta"]["0.5"]), ESO)
        # N: p3 = 50/201 (0.249), p2 = 5/201 (0.0249) -> beyond 2nd, explained by 3rd
        self.assertEqual(label(res["N"]["by_theta"]["0.5"]), E3O)
        # KS (no markov3): p2 = 400/1001, p1 = 2/1001 -> second order explains it
        self.assertEqual(label(res["KS"]["by_theta"]["0.5"]), ESO)
        self.assertEqual(label(toy_row(0.9, {"markov1_pooled": 0, "markov2_pooled": 0}, 200)),
                         BSO)
        self.assertEqual(label(toy_row(0.9, {"markov1_pooled": 0, "markov2_pooled": 0,
                                             "markov3_pooled": 0}, 200)), B3O)
        self.assertEqual(label(toy_row(0.9, {"markov1_pooled": 50, "markov2_pooled": 60}, 200)),
                         EFO)

    def test_regrade(self):
        rg = regrade(toy_results(), True, False)
        g = rg["g"]
        # K5, K6 and S1 false; K7: 5 * 9 = 45 >= 4 * 11 = 44
        self.assertEqual([g[x] for x in ORDER],
                         [True, True, True, True, False, False, True, True, True, False, True])
        self.assertEqual(rg["graded"], list(ORDER))
        # .04 + .01 + .0225 + .0225 + .25 + .09 + .01 + .0625 + .3025 + .04 + .09 = .94
        self.assertAlmostEqual(rg["brier"], 0.94 / 11, places=12)
        self.assertEqual(rg["rules"], {"X1": "ABOVE_BIGRAM_REPLICATES", "X2": "SECOND_ORDER_MIXED",
                                       "X3": "NOT_BEYOND_AT_EITHER_SIZE", "robust_K": True})
        self.assertTrue(rg["provisional"])
        self.assertEqual(rg["labels"], {"K": {"0.5": ESO, "0.3": ESO, "0.7": ESO},
                                        "N": {"0.5": E3O}, "KS": {"0.5": ESO}})

    def test_regrade_missing_and_k7_edge(self):
        res = toy_results()
        del res["N"]
        del res["K"]["by_theta"]["0.7"]
        res["K"]["heldout"]["d1_n_favour_order2"] = 8      # 5 * 8 = 40 < 44
        rg = regrade(res, True, True)
        self.assertIsNone(rg["g"]["N1"])
        self.assertFalse(rg["g"]["K7"])
        self.assertEqual(len(rg["graded"]), 9)
        self.assertEqual(rg["rules"]["X1"], "NOT_GRADED")
        self.assertEqual(rg["rules"]["X2"], "NOT_GRADED")
        self.assertFalse(rg["rules"]["robust_K"])
        self.assertFalse(rg["provisional"])

    def test_gates(self):
        good = [{"notes": 18000, "classes": 8}] * 10 + [{"notes": 17209, "classes": 8}]
        self.assertTrue(regate_k(good))                    # mean 17,928.09, classes 8
        self.assertFalse(regate_k(good[:10]))
        self.assertFalse(regate_k([{"notes": 18000, "classes": 9}] * 11))
        self.assertFalse(regate_k([]))
        nb = [{"syllables": 20000, "files": 100, "bad_files": 0, "unreadable_files": 0}] * 4
        self.assertTrue(regate_n(nb))
        self.assertTrue(regate_n(nb[:3] + [{"syllables": 20000, "files": 100, "bad_files": 3,
                                            "unreadable_files": 1}]))   # 4 of 400 = 1%
        self.assertFalse(regate_n(nb[:3] + [{"syllables": 20000, "files": 100, "bad_files": 3,
                                             "unreadable_files": 2}]))  # 5 of 400
        self.assertFalse(regate_n(nb[:3]))

    def test_p_ok(self):
        self.assertTrue(p_ok(30 / 201, 200))
        self.assertTrue(p_ok(1 / 1001, 1000))
        self.assertFalse(p_ok(0.15, 200))                  # 0.15 * 201 - 1 = 29.15

    def test_formats(self):
        row = {"real_mean_r2": 0.91234,
               "nulls": {"markov2_pooled": {"real": 0.91234, "null_mean": 0.90011,
                                            "null_sd": 0.01, "z": 1.2345, "p": 30 / 201,
                                            "n_null": 200}}}
        self.assertEqual(null_row("K", "0.5", "markov2_pooled", row),
                         "| K | 0.5 | markov2_pooled | 0.912 | 0.900 | +0.012 | 1.23 | 0.149 | 200 |")
        self.assertEqual(describe_row("K", {"recordings": 11, "bouts": 1234, "symbols": 197209,
                                            "transitions": 195975, "max_bout_length": 87}),
                         "| K | 11 | 1,234 | 197,209 | 195,975 | 87 |")
        # mean D1 = 0.8 / 11 = 0.0727; mean D2 = -0.05 / 11 = -0.0045
        self.assertEqual(heldout_row("K", toy_results()["K"]["heldout"]),
                         "| K | 9 of 11 | +0.0727 | 3 of 11 | -0.0045 |")
        self.assertEqual(label_row("N", "0.5", E3O), "| N | 0.5 | `EXPLAINED_BY_THIRD_ORDER` |")
        self.assertEqual(pred_end("K5", False), "| 0.50 | **false** |")
        self.assertEqual(pred_end("S2", None), "| 0.70 | **not graded** |")

    def test_md_check(self):
        res = toy_results()
        r = {"results": res, "describe": {"K": {"recordings": 11, "bouts": 1234,
                                                "symbols": 197209, "transitions": 195975,
                                                "max_bout_length": 87}}}
        rg = regrade(res, True, False)
        lines = render_md_lines(r, rg)
        self.assertIn("Gate N: **fail**", lines)
        self.assertIn("8 of 11 graded predictions true", lines)
        self.assertIn("X2: **`SECOND_ORDER_MIXED`**", lines)
        self.assertIn("Provisional (a reading gate failed): **yes**", lines)
        self.assertIn("| K5 | K beats markov2 | 0.50 | **false** |", lines)
        md = "\n".join(lines)
        self.assertEqual(check_md(md, r, rg), [])
        no_x2 = "\n".join(ln for ln in lines if not ln.startswith("X2:"))
        self.assertEqual(check_md(no_x2, r, rg), ["X2: **`SECOND_ORDER_MIXED`**"])
        no_k5 = "\n".join(ln for ln in lines if not ln.startswith("| K5 |"))
        self.assertEqual(check_md(no_k5, r, rg), ["prediction row K5"])


if __name__ == "__main__":
    unittest.main()
