# SPDX-License-Identifier: Apache-2.0
# test_canary_results.py: the grader for the canary positive control (CANARY-PREREG.md and
# CANARY-AMENDMENT-1.md, job song-zipf-canary-v2), written and published BEFORE the job has run.
# With its own code (it does not import canary.py) it re-derives every reading gate, every label,
# the eight graded predictions, rules C1 and C2, the robustness flags, the provisional flag and
# the Brier score from the raw job output; checks every p value, z score, ladder and held-out
# number for internal consistency; checks them against the job's own grading; and fixes now the
# exact lines RESULTS-CANARY.md must print (render_md_lines).
# Until results/canary/canary_results.json exists, the result tests are skipped; the toy-data
# tests always run. Stdlib only; reads files only if they exist and writes nothing.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import hashlib
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "canary", "canary_results.json")
MD = os.path.join(HERE, "RESULTS-CANARY.md")
PREREG = os.path.join(HERE, "CANARY-PREREG.md")
ZIPFSEG = os.path.join(HERE, "zipfseg.py")
CANARY = os.path.join(HERE, "canary.py")
HAVE = os.path.exists(RES)

ALPHA = 0.05
VERSION = "canary-1"
# sha256 of zipfseg.py at 742fd83 (the same file every earlier test pins)
ZIPFSEG_SHA256 = "25002193229e6d6568939856de5a1760a41c3b462582ea06b6d75ba6d84bddf5"
BIRDS = ("llb11", "llb16", "llb3")
ORDER = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")
PRIORS = {"P1": 0.75, "P2": 0.45, "P3": 0.90, "P4": 0.70, "P5": 0.45, "P6": 0.30,
          "P7": 0.80, "P8": 0.20}
PRED_TEXT = {"P1": "G3 (order 3 beats order 2 held out) in >= 2 of 3 birds",
             "P2": "G4 (order 4 beats order 3) in >= 2 of 3 birds",
             "P3": "all 3 birds beat shuffle and rotate at theta 0.5",
             "P4": ">= 2 birds beat markov1_pooled",
             "P5": ">= 2 birds beat markov2_pooled",
             "P6": ">= 2 birds beat markov3_pooled",
             "P7": "all 3 birds have a D1 majority",
             "P8": ">= 2 birds beat markov2_pooled at Kirby size"}
NULLS = ("shuffle", "rotate", "bigram_within", "markov1_pooled", "markov2_pooled",
         "markov3_pooled")
B_BY_THETA = {"0.5": 200, "0.3": 100, "0.7": 100}
B_KIRBY = 200
THETAS = ("0.5", "0.3", "0.7")
ALPHAS = ("0.5", "0.1", "0.02", "0.005")
B3O, E3O, BSO = "BEYOND_THIRD_ORDER", "EXPLAINED_BY_THIRD_ORDER", "BEYOND_SECOND_ORDER"
ESO, EFO = "EXPLAINED_BY_SECOND_ORDER", "EXPLAINED_BY_FIRST_ORDER"


# --------------------------------------------------------------------------
# independent re-implementation of CANARY-PREREG.md sections 4 to 7
# --------------------------------------------------------------------------
def regate(st):
    """Section 4: rows > 0, bad rows <= 1%, >= 10 classes, summed song span >= 15,000 s."""
    if not st or st["rows"] <= 0:
        return False
    return (st["bad_rows"] / st["rows"] <= 0.01 and st["classes"] >= 10
            and st["song_span_s"] >= 15000.0)


def label(row):
    """Section 5 label from one row's p values."""
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


def positive(x):
    return None if x is None or x != x else x > 0


def beats(row, name):
    if not row or name not in row.get("nulls", {}):
        return None
    return row["nulls"][name]["p"] < ALPHA


def main_row(r):
    return (r.get("by_theta") or {}).get("0.5")


def bird_values(r):
    """Per-bird booleans (None = missing) for one bird's results, or all None."""
    keys = ("gt3", "gt4", "controls", "m1", "m2", "m3", "d1_majority", "kirby_m2")
    if r is None:
        return dict.fromkeys(keys)
    g = (r.get("ladder") or {}).get("gains")
    m = main_row(r)
    sh, ro = beats(m, "shuffle"), beats(m, "rotate")
    h = r.get("heldout_blocks") or {}
    n = h.get("n_recordings")
    return {"gt3": positive(g[1]) if g else None,
            "gt4": positive(g[2]) if g else None,
            "controls": None if sh is None or ro is None else (sh and ro),
            "m1": beats(m, "markov1_pooled"),
            "m2": beats(m, "markov2_pooled"),
            "m3": beats(m, "markov3_pooled"),
            "d1_majority": (2 * h["d1_n_favour_order2"] > n) if n else None,
            "kirby_m2": beats(r.get("kirby"), "markov2_pooled")}


def at_least(vals, n):
    return None if any(v is None for v in vals) else sum(1 for v in vals if v) >= n


def every(vals):
    return None if any(v is None for v in vals) else all(vals)


def regrade(res, gates):
    """res: the job's results dict; gates: {bird: bool} re-derived from the job's stats."""
    per = {b: bird_values(res.get(b)) for b in BIRDS}
    col = {k: [per[b][k] for b in BIRDS] for k in per[BIRDS[0]]}
    g = {"P1": at_least(col["gt3"], 2), "P2": at_least(col["gt4"], 2),
         "P3": every(col["controls"]), "P4": at_least(col["m1"], 2),
         "P5": at_least(col["m2"], 2), "P6": at_least(col["m3"], 2),
         "P7": every(col["d1_majority"]), "P8": at_least(col["kirby_m2"], 2)}
    graded = [x for x in ORDER if g[x] is not None]
    brier = (sum((PRIORS[x] - (1.0 if g[x] else 0.0)) ** 2 for x in graded) / len(graded)
             if graded else float("nan"))
    if any(v is None for v in col["gt3"] + col["m2"]):
        c1 = "NOT_GRADED"
    else:
        truth = [b for b in BIRDS if per[b]["gt3"]]
        seen = [b for b in truth if per[b]["m2"]]
        if len(truth) < 2:
            c1 = "NO_GROUND_TRUTH"
        elif len(seen) == len(truth):
            c1 = "TEST_SEES_REAL_SYNTAX"
        elif not seen:
            c1 = "TEST_BLIND_TO_REAL_SYNTAX"
        else:
            c1 = "TEST_MIXED"
    det = [b for b in BIRDS if per[b]["m2"]]
    if any(v is None for v in col["m2"]) or any(per[b]["kirby_m2"] is None for b in det):
        c2 = "NOT_GRADED"
    elif not det:
        c2 = "NOTHING_DETECTED_AT_FULL_SIZE"
    else:
        kept = [b for b in det if per[b]["kirby_m2"]]
        c2 = ("KEPT_AT_KIRBY_SIZE" if len(kept) == len(det) else
              "LOST_AT_KIRBY_SIZE" if not kept else "PARTLY_KEPT_AT_KIRBY_SIZE")
    labels = {b: {th: label(row) for th, row in res[b].get("by_theta", {}).items()}
              for b in BIRDS if b in res}
    robust = {b: len(v) == 3 and len(set(v.values())) == 1 for b, v in labels.items()}
    kirby_labels = {b: label(res[b]["kirby"]) for b in BIRDS
                    if b in res and res[b].get("kirby")}
    return {"g": g, "graded": graded, "brier": brier, "per_bird": per,
            "rules": {"C1": c1, "C2": c2}, "labels": labels, "robust": robust,
            "kirby_labels": kirby_labels, "gates": dict(gates),
            "provisional": not all(gates.get(b) for b in BIRDS)}


def p_ok(p, n):
    """p = (1 + k) / (1 + n) for an integer 0 <= k <= n."""
    k = p * (n + 1) - 1
    return abs(k - round(k)) < 1e-6 and 0 <= round(k) <= n


def fmean(v):
    v = [a for a in v if a == a]
    return sum(v) / len(v) if v else float("nan")


def isnum(x):
    return isinstance(x, (int, float)) and x == x


# --------------------------------------------------------------------------
# formats fixed before the result exists (RESULTS-CANARY.md must contain these lines)
# --------------------------------------------------------------------------
def yn(b):
    return "**yes**" if b else "**no**"


def stats_row(b, st):
    """| bird | syllables | classes | songs | phrases | phrase types | blocks | song span (s) |"""
    return "| {} | {:,} | {} | {:,} | {:,} | {} | {} | {:,.0f} |".format(
        b, st["syllables"], st["classes"], st["songs"], st["phrases"], st["phrase_types"],
        st["blocks"]["recordings"], st["song_span_s"])


def ladder_row(b, lad):
    """| bird | LL order 1 .. 5 | g_2 (order 3 - order 2) | g_3 (order 4 - order 3) |"""
    return "| {} | {} | {:+.4f} | {:+.4f} |".format(
        b, " | ".join("{:.4f}".format(x) for x in lad["best"]), lad["gains"][1], lad["gains"][2])


def heldout_row(b, h):
    """| bird | D1 > 0 | mean D1 | D2 > 0 | mean D2 |"""
    n = h["n_recordings"]
    return "| {} | {} of {} | {:+.4f} | {} of {} | {:+.4f} |".format(
        b, h["d1_n_favour_order2"], n, fmean(h["d1_per_recording"]),
        h["d2_n_favour_order3"], n, fmean(h["d2_per_recording"]))


def null_row(b, size, th, name, row):
    """| bird | size | theta | null | real R^2 | null mean R^2 | gap | z | p | nulls |"""
    c = row["nulls"][name]
    return "| {} | {} | {} | {} | {:.3f} | {:.3f} | {:+.3f} | {:.2f} | {:.3f} | {} |".format(
        b, size, th, name, row["real_mean_r2"], c["null_mean"],
        row["real_mean_r2"] - c["null_mean"], c["z"], c["p"], c["n_null"])


def label_row(b, size, th, lab):
    return "| {} | {} | {} | `{}` |".format(b, size, th, lab)


def pred_end(k, v):
    return "| {:.2f} | **{}** |".format(
        PRIORS[k], "not graded" if v is None else ("true" if v else "false"))


def row_lines(b, size, th, row):
    return [label_row(b, size, th, label(row))] + [
        null_row(b, size, th, name, row) for name in NULLS if name in row["nulls"]]


def required_strings(r, rg):
    need = ["Reading gate %s: %s" % (b, "**pass**" if rg["gates"].get(b) else "**fail**")
            for b in BIRDS]
    stats = r.get("stats", {})
    res = r["results"]
    for b in BIRDS:
        if b in stats:
            need.append(stats_row(b, stats[b]))
    for b in BIRDS:
        if b not in res:
            continue
        lad = res[b].get("ladder") or {}
        if "best" in lad:
            need.append(ladder_row(b, lad))
        h = res[b].get("heldout_blocks") or {}
        if h.get("n_recordings"):
            need.append(heldout_row(b, h))
        for th in THETAS:
            row = res[b].get("by_theta", {}).get(th)
            if row:
                need.extend(row_lines(b, "full", th, row))
        if res[b].get("kirby"):
            need.extend(row_lines(b, "Kirby", "0.5", res[b]["kirby"]))
    ntrue = sum(1 for x in rg["graded"] if rg["g"][x])
    need.append("%d of %d graded predictions true" % (ntrue, len(rg["graded"])))
    if rg["graded"]:
        need.append("Brier score **%.3f**" % rg["brier"])
    for x in ("C1", "C2"):
        need.append("%s: **`%s`**" % (x, rg["rules"][x]))
    for b in BIRDS:
        if b in rg["robust"]:
            need.append("Label robust across theta 0.3/0.5/0.7, %s: %s" % (b, yn(rg["robust"][b])))
    need.append("Provisional (a reading gate failed): " + yn(rg["provisional"]))
    return need


def render_md_lines(r, rg):
    """Every fixed line, in one list (prediction rows included), for writing RESULTS-CANARY.md."""
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


def gates_from(r):
    stats = r.get("stats", {})
    return {b: regate(stats.get(b)) for b in BIRDS}


# --------------------------------------------------------------------------
# result tests (skipped until the job's output is published)
# --------------------------------------------------------------------------
@unittest.skipUnless(HAVE, "results/canary/canary_results.json not published yet")
class TestCanaryResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        cls.gates = gates_from(cls.r)
        cls.rg = regrade(cls.r["results"], cls.gates)
        cls.md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""

    def test_status_registration_code(self):
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
        if os.path.exists(CANARY):          # the job ran the published canary.py
            self.assertEqual(r["canary_sha256"], sha256_file(CANARY))

    def test_stats_and_gates(self):
        r = self.r
        for b in BIRDS:
            self.assertIn(b, r["gates"])
            self.assertEqual(bool(r["gates"][b]["pass"]), self.gates[b], b)
            st = r["stats"].get(b)
            if st is None:
                self.assertNotIn(b, r["results"], b)
                continue
            self.assertEqual(sum(st["label_counts"].values()), st["syllables"], b)
            self.assertEqual(len(st["label_counts"]), st["classes"], b)
            self.assertEqual(sum(st["phrase_counts"].values()), st["phrases"], b)
            self.assertEqual(len(st["phrase_counts"]), st["phrase_types"], b)
            self.assertEqual(st["syllables"],
                             st["rows"] - st["bad_rows"] - st["duplicate_rows_dropped"], b)
            self.assertLessEqual(st["phrases"], st["syllables"], b)
            self.assertLessEqual(st["songs_with_6_or_more_phrases"], st["songs"], b)
            bl = st["blocks"]
            self.assertLessEqual(bl["recordings"], 8, b)
            self.assertEqual(len(bl["symbols_per_recording"]), bl["recordings"], b)
            self.assertTrue(all(x >= 3000 for x in bl["symbols_per_recording"]), b)
            self.assertEqual(sum(bl["symbols_per_recording"]), bl["symbols"], b)
            self.assertLessEqual(bl["symbols"], st["phrases"], b)
            self.assertEqual(bl["transitions"], bl["symbols"] - bl["bouts"], b)
            self.assertEqual(b in r["results"], bl["recordings"] > 0, b)

    def test_ladder_and_heldout(self):
        r = self.r
        for b, x in r["results"].items():
            lad = x["ladder"]
            if "error" not in lad:
                self.assertEqual(lad["skip"], 5)
                self.assertEqual(sorted(lad["by_alpha"]), sorted(ALPHAS))
                self.assertEqual(len(lad["best"]), 5)
                self.assertEqual(len(lad["gains"]), 4)
                self.assertGreater(lad["scored"], 0)
                for k in range(5):
                    vals = [lad["by_alpha"][a][k] for a in ALPHAS]
                    if all(isnum(v) for v in vals):
                        self.assertEqual(lad["best"][k], max(vals), (b, k))
                for i in range(4):
                    if isnum(lad["best"][i]) and isnum(lad["best"][i + 1]):
                        self.assertAlmostEqual(lad["gains"][i],
                                               lad["best"][i + 1] - lad["best"][i], places=12)
            h = x["heldout_blocks"]
            n = r["stats"][b]["blocks"]["recordings"]
            if "error" not in h:
                self.assertEqual(h["n_recordings"], n)
                self.assertEqual(len(h["d1_per_recording"]), n)
                self.assertEqual(len(h["d2_per_recording"]), n)
                self.assertEqual(h["d1_n_favour_order2"],
                                 sum(1 for a in h["d1_per_recording"] if a > 0))
                self.assertEqual(h["d2_n_favour_order3"],
                                 sum(1 for a in h["d2_per_recording"] if a > 0))
            kd = x["kirby_describe"]
            bl = r["stats"][b]["blocks"]
            self.assertEqual(kd["recordings"], bl["recordings"])
            for i in range(bl["recordings"]):
                self.assertLessEqual(kd["symbols_per_recording"][i],
                                     bl["symbols_per_recording"][i])

    def check_row(self, row, B, tag):
        self.assertEqual(sorted(row["nulls"]), sorted(NULLS), tag)
        for name in NULLS:
            c = row["nulls"][name]
            self.assertLessEqual(c["n_null"], B, (tag, name))
            self.assertGreaterEqual(c["n_null"], 0.9 * B, (tag, name))
            self.assertTrue(p_ok(c["p"], c["n_null"]), (tag, name, c["p"]))
            self.assertAlmostEqual(c["real"], row["real_mean_r2"], places=12)
            if c["null_sd"] > 0:
                self.assertAlmostEqual(c["z"], (c["real"] - c["null_mean"]) / c["null_sd"],
                                       places=9)

    def test_rows_complete_and_consistent(self):
        for b, x in self.r["results"].items():
            bt = x.get("by_theta", {})
            self.assertLessEqual(set(bt), set(THETAS), b)
            for th, row in bt.items():
                self.check_row(row, B_BY_THETA[th], (b, th))
            if "0.5" not in bt:
                self.assertIn("0.5", x.get("errors", {}), b)
            for th in ("0.3", "0.7"):
                if th not in bt:
                    self.assertTrue(("theta %s (time budget)" % th) in x.get("not_run", [])
                                    or th in x.get("errors", {}), (b, th))
            if x.get("kirby"):
                self.check_row(x["kirby"], B_KIRBY, (b, "kirby"))
            else:
                self.assertIn("kirby", x.get("errors", {}), b)

    def test_grading_matches_regrade(self):
        gr = self.r["grading"]
        rg = self.rg
        self.assertEqual(gr["priors"], PRIORS)
        self.assertEqual(gr["predictions"], rg["g"])
        self.assertEqual(gr["graded"], rg["graded"])
        if rg["graded"]:
            self.assertAlmostEqual(gr["brier"], rg["brier"], places=12)
        self.assertEqual(gr["per_bird"], {k: {b: rg["per_bird"][b][k] for b in BIRDS}
                                          for k in rg["per_bird"][BIRDS[0]]})
        self.assertEqual(gr["labels"], rg["labels"])
        self.assertEqual(gr["kirby_labels"], rg["kirby_labels"])
        self.assertEqual(gr["robust"], rg["robust"])
        self.assertEqual(gr["rules"], rg["rules"])
        self.assertEqual(gr["provisional"], rg["provisional"])

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-CANARY.md not written yet")
    def test_md_lines(self):
        self.assertEqual(check_md(self.md, self.r, self.rg), [])


# --------------------------------------------------------------------------
# toy tests (always run; every expected value worked out by hand)
# --------------------------------------------------------------------------
def toy_row(real, ks, B=200):
    """ks: null name -> k (number of null sets >= real), so p = (1 + k) / (1 + B)."""
    return {"real_mean_r2": real,
            "nulls": {name: {"real": real, "null_mean": real - 0.01, "null_sd": 0.005, "z": 2.0,
                             "p": (1 + k) / (1 + B), "n_null": B} for name, k in ks.items()}}


def ks(m1, m2, m3):
    return {"shuffle": 0, "rotate": 0, "bigram_within": 0, "markov1_pooled": m1,
            "markov2_pooled": m2, "markov3_pooled": m3}


def toy_heldout(n_pos, n=8):
    return {"d1_per_recording": [0.1] * n_pos + [-0.1] * (n - n_pos), "d1_n_favour_order2": n_pos,
            "d2_per_recording": [0.01] * 2 + [-0.01] * (n - 2), "d2_n_favour_order3": 2,
            "n_recordings": n}


def toy_results():
    # llb11: g_2 > 0 (G3), g_3 < 0; main p2 = 4/201 = .0199 (beaten), p3 = 41/201 = .204;
    #        D1 8 of 8; Kirby p2 = 31/201 = .154 (not beaten); same row at all 3 thetas
    m11 = toy_row(0.90, ks(0, 3, 40))
    r11 = {"ladder": {"gains": [0.3, 0.05, -0.01, -0.02]}, "heldout_blocks": toy_heldout(8),
           "by_theta": {"0.5": m11, "0.3": m11, "0.7": m11}, "kirby": toy_row(0.85, ks(0, 30, 100))}
    # llb16: no G3; main p2 = 61/201 = .303, p1 = 1/201; D1 5 of 8 (10 > 8); Kirby p2 = 81/201
    r16 = {"ladder": {"gains": [0.2, -0.01, -0.02, -0.03]}, "heldout_blocks": toy_heldout(5),
           "by_theta": {"0.5": toy_row(0.88, ks(0, 60, 90))},
           "kirby": toy_row(0.84, ks(0, 80, 120))}
    # llb3: G3 and G4; main p2 = 2/201, p3 = 6/201 = .0299 (both beaten); D1 4 of 8 (8 > 8 is
    #       false); Kirby p2 = 3/201 = .0149, p3 = 51/201; theta 0.3 row p2 = 31/201, p3 = 41/201
    m3 = toy_row(0.93, ks(0, 1, 5))
    r3 = {"ladder": {"gains": [0.25, 0.02, 0.01, -0.01]}, "heldout_blocks": toy_heldout(4),
          "by_theta": {"0.5": m3, "0.3": toy_row(0.86, ks(0, 30, 40)), "0.7": m3},
          "kirby": toy_row(0.87, ks(0, 2, 50))}
    return {"llb11": r11, "llb16": r16, "llb3": r3}


TOY_GATES = {"llb11": True, "llb16": False, "llb3": True}


class TestToy(unittest.TestCase):
    def test_label(self):
        self.assertEqual(label(toy_row(.9, ks(0, 0, 0))), B3O)
        self.assertEqual(label(toy_row(.9, ks(0, 3, 40))), E3O)
        self.assertEqual(label(toy_row(.9, ks(0, 60, 90))), ESO)
        self.assertEqual(label(toy_row(.9, ks(50, 60, 90))), EFO)
        two = toy_row(.9, {"markov1_pooled": 0, "markov2_pooled": 0})
        self.assertEqual(label(two), BSO)

    def test_regrade(self):
        rg = regrade(toy_results(), TOY_GATES)
        g = rg["g"]
        # P1 G3 in llb11, llb3 (2); P2 G4 only llb3; P3 all beat shuffle+rotate; P4 all beat m1;
        # P5 m2 beaten in llb11, llb3; P6 m3 only llb3; P7 llb3 has no D1 majority;
        # P8 Kirby m2 only llb3
        self.assertEqual([g[x] for x in ORDER], [True, False, True, True, True, False, False,
                                                 False])
        self.assertEqual(rg["graded"], list(ORDER))
        # .0625 + .2025 + .01 + .09 + .3025 + .09 + .64 + .04 = 1.4375
        self.assertAlmostEqual(rg["brier"], 1.4375 / 8, places=12)
        # G3 birds llb11, llb3 both beat m2; of those detected, llb3 keeps it at Kirby size
        self.assertEqual(rg["rules"], {"C1": "TEST_SEES_REAL_SYNTAX",
                                       "C2": "PARTLY_KEPT_AT_KIRBY_SIZE"})
        self.assertEqual(rg["labels"], {"llb11": {"0.5": E3O, "0.3": E3O, "0.7": E3O},
                                        "llb16": {"0.5": ESO},
                                        "llb3": {"0.5": B3O, "0.3": ESO, "0.7": B3O}})
        self.assertEqual(rg["robust"], {"llb11": True, "llb16": False, "llb3": False})
        self.assertEqual(rg["kirby_labels"], {"llb11": ESO, "llb16": ESO, "llb3": E3O})
        self.assertTrue(rg["provisional"])
        self.assertEqual(rg["per_bird"]["llb3"]["d1_majority"], False)
        self.assertEqual(rg["per_bird"]["llb16"]["d1_majority"], True)

    def test_rules_other_outcomes(self):
        res = toy_results()
        # llb11 no longer beats m2 -> of the G3 birds only llb3 does -> mixed;
        # detected: llb3 only, kept at Kirby size
        res["llb11"]["by_theta"]["0.5"] = toy_row(0.90, ks(0, 60, 90))
        rg = regrade(res, TOY_GATES)
        self.assertEqual(rg["rules"], {"C1": "TEST_MIXED", "C2": "KEPT_AT_KIRBY_SIZE"})
        # llb3 no longer beats m2 either -> blind; nothing detected
        res["llb3"]["by_theta"]["0.5"] = toy_row(0.93, ks(0, 60, 90))
        rg = regrade(res, TOY_GATES)
        self.assertEqual(rg["rules"], {"C1": "TEST_BLIND_TO_REAL_SYNTAX",
                                       "C2": "NOTHING_DETECTED_AT_FULL_SIZE"})
        # only one G3 bird -> no ground truth
        res["llb3"]["ladder"]["gains"] = [0.25, -0.02, 0.01, -0.01]
        rg = regrade(res, dict.fromkeys(BIRDS, True))
        self.assertEqual(rg["rules"]["C1"], "NO_GROUND_TRUTH")
        self.assertFalse(rg["provisional"])
        # llb11 detected and kept (Kirby p2 = 1/201), llb3 detected and lost (81/201) -> partly;
        # then llb11 lost too -> lost
        res = toy_results()
        res["llb11"]["kirby"] = toy_row(0.85, ks(0, 0, 100))
        res["llb3"]["kirby"] = toy_row(0.87, ks(0, 80, 100))
        self.assertEqual(regrade(res, TOY_GATES)["rules"]["C2"], "PARTLY_KEPT_AT_KIRBY_SIZE")
        res["llb11"]["kirby"] = toy_row(0.85, ks(0, 80, 100))
        self.assertEqual(regrade(res, TOY_GATES)["rules"]["C2"], "LOST_AT_KIRBY_SIZE")

    def test_missing_bird_and_errors(self):
        res = toy_results()
        del res["llb16"]
        res["llb3"]["ladder"] = {"error": "x"}
        rg = regrade(res, TOY_GATES)
        self.assertEqual(rg["graded"], [])               # every prediction needs all 3 birds
        self.assertEqual(rg["rules"], {"C1": "NOT_GRADED", "C2": "NOT_GRADED"})
        self.assertNotIn("llb16", rg["labels"])
        res = toy_results()
        res["llb11"]["heldout_blocks"] = {"error": "y"}
        del res["llb16"]["kirby"]
        rg = regrade(res, TOY_GATES)
        self.assertIsNone(rg["g"]["P7"])
        # P8: Kirby m2 missing for llb16 -> not graded; C2 still graded (llb16 not detected)
        self.assertIsNone(rg["g"]["P8"])
        self.assertEqual(rg["rules"]["C2"], "PARTLY_KEPT_AT_KIRBY_SIZE")
        self.assertEqual(len(rg["graded"]), 6)
        self.assertNotIn("llb16", rg["kirby_labels"])
        # a NaN gain counts as missing
        res = toy_results()
        res["llb16"]["ladder"]["gains"] = [0.2, float("nan"), -0.02, -0.03]
        self.assertIsNone(regrade(res, TOY_GATES)["g"]["P1"])

    def test_gates(self):
        good = {"rows": 1000, "bad_rows": 10, "classes": 10, "song_span_s": 15000.0}
        self.assertTrue(regate(good))
        self.assertFalse(regate(dict(good, bad_rows=11)))
        self.assertFalse(regate(dict(good, classes=9)))
        self.assertFalse(regate(dict(good, song_span_s=14999.0)))
        self.assertFalse(regate(dict(good, rows=0, bad_rows=0)))
        self.assertFalse(regate(None))

    def test_p_ok(self):
        self.assertTrue(p_ok(30 / 201, 200))
        self.assertTrue(p_ok(1 / 101, 100))
        self.assertFalse(p_ok(0.15, 200))                  # 0.15 * 201 - 1 = 29.15

    def test_formats(self):
        st = {"syllables": 123456, "classes": 27, "songs": 2345, "phrases": 34567,
              "phrase_types": 31, "song_span_s": 30123.4, "blocks": {"recordings": 8}}
        self.assertEqual(stats_row("llb3", st),
                         "| llb3 | 123,456 | 27 | 2,345 | 34,567 | 31 | 8 | 30,123 |")
        lad = {"best": [-2.1, -1.5, -1.45, -1.46, -1.5], "gains": [0.6, 0.05, -0.01, -0.04]}
        self.assertEqual(ladder_row("llb3", lad),
                         "| llb3 | -2.1000 | -1.5000 | -1.4500 | -1.4600 | -1.5000 | +0.0500 "
                         "| -0.0100 |")
        # mean D1 = (0.6 - 0.2) / 8 = 0.05; mean D2 = (0.02 - 0.06) / 8 = -0.005
        self.assertEqual(heldout_row("llb3", toy_heldout(6)),
                         "| llb3 | 6 of 8 | +0.0500 | 2 of 8 | -0.0050 |")
        row = {"real_mean_r2": 0.91234,
               "nulls": {"markov2_pooled": {"real": 0.91234, "null_mean": 0.90011,
                                            "null_sd": 0.01, "z": 1.2345, "p": 30 / 201,
                                            "n_null": 200}}}
        self.assertEqual(null_row("llb3", "full", "0.5", "markov2_pooled", row),
                         "| llb3 | full | 0.5 | markov2_pooled | 0.912 | 0.900 | +0.012 | 1.23 "
                         "| 0.149 | 200 |")
        self.assertEqual(label_row("llb11", "Kirby", "0.5", ESO),
                         "| llb11 | Kirby | 0.5 | `EXPLAINED_BY_SECOND_ORDER` |")
        self.assertEqual(pred_end("P5", True), "| 0.45 | **true** |")
        self.assertEqual(pred_end("P8", None), "| 0.20 | **not graded** |")

    def test_md_check(self):
        res = toy_results()
        st = {"syllables": 123456, "classes": 27, "songs": 2345, "phrases": 34567,
              "phrase_types": 31, "song_span_s": 30123.4, "blocks": {"recordings": 8}}
        r = {"results": res, "stats": {"llb3": st}}
        rg = regrade(res, TOY_GATES)
        lines = render_md_lines(r, rg)
        self.assertIn("Reading gate llb16: **fail**", lines)
        self.assertIn("Reading gate llb3: **pass**", lines)
        self.assertIn("| llb3 | 123,456 | 27 | 2,345 | 34,567 | 31 | 8 | 30,123 |", lines)
        self.assertIn("4 of 8 graded predictions true", lines)
        self.assertIn("Brier score **0.180**", lines)
        self.assertIn("C2: **`PARTLY_KEPT_AT_KIRBY_SIZE`**", lines)
        self.assertIn("| llb3 | full | 0.5 | `BEYOND_THIRD_ORDER` |", lines)
        self.assertIn("| llb11 | Kirby | 0.5 | `EXPLAINED_BY_SECOND_ORDER` |", lines)
        # llb16 mean D1 = (0.5 - 0.3) / 8 = 0.025
        self.assertIn("| llb16 | 5 of 8 | +0.0250 | 2 of 8 | -0.0050 |", lines)
        self.assertIn("Label robust across theta 0.3/0.5/0.7, llb11: **yes**", lines)
        self.assertIn("Label robust across theta 0.3/0.5/0.7, llb3: **no**", lines)
        self.assertIn("Provisional (a reading gate failed): **yes**", lines)
        self.assertIn("| P7 | all 3 birds have a D1 majority | 0.80 | **false** |", lines)
        # 3 birds x (label + 6 nulls) at theta 0.5 and Kirby, plus 2 x 7 rows for the extra
        # thetas of llb11 and llb3 each: 3*2*7 + 4*7 = 70 row lines
        self.assertEqual(sum(1 for ln in lines if " | full | " in ln or " | Kirby | " in ln), 70)
        md = "\n".join(lines)
        self.assertEqual(check_md(md, r, rg), [])
        no_c1 = "\n".join(ln for ln in lines if not ln.startswith("C1:"))
        self.assertEqual(check_md(no_c1, r, rg), ["C1: **`TEST_SEES_REAL_SYNTAX`**"])
        no_p5 = "\n".join(ln for ln in lines if not ln.startswith("| P5 |"))
        self.assertEqual(check_md(no_p5, r, rg), ["prediction row P5"])


if __name__ == "__main__":
    unittest.main()
