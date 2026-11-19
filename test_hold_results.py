# SPDX-License-Identifier: Apache-2.0
# test_hold_results.py: the grader for the held-out prediction test (HOLD-PREREG.md, job
# song-zipf-hold-v1), written and published BEFORE the job has produced any result.
# With its own code (it does not import hold.py) it re-derives every label, the detection
# rates, rules R1-R4, predictions H1-H9 and the Brier score from the raw job output; checks
# every gain, best order, mean, p value, seed and size for internal consistency; checks them
# against the job's own grading; and fixes now the exact lines RESULTS-HOLD.md must print
# (render_md_lines). Until results/hold/hold_results.json exists, the result tests are
# skipped; the toy-data tests always run. Stdlib only; reads files only if they exist and
# writes nothing.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import hashlib
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "hold", "hold_results.json")
MD = os.path.join(HERE, "RESULTS-HOLD.md")
PREREG = os.path.join(HERE, "HOLD-PREREG.md")
HOLD = os.path.join(HERE, "hold.py")
HAVE = os.path.exists(RES)

VERSION = "hold-1"
ALPHA = 0.05
K_MAX = 5
SEED = 20261119
B_CDS = 100
B_WHALE = 200
N_REC = 8
N_YEARS = 8
DESIGN = ((70, 5), (140, 5), (280, 4), (600, 2), (1200, 1))
SIZES = tuple(u for u, _ in DESIGN)
WHALE_SIZE = 5720
# sha256 of zipfseg.py at 742fd83 (the same file every earlier test pins)
ZIPFSEG_SHA256 = "25002193229e6d6568939856de5a1760a41c3b462582ea06b6d75ba6d84bddf5"
# Replicates the Zipf-vs-Markov-2 test detected (theta 0.5), per size U, as graded in
# RESULTS-CDS-SIZE.md (commit a54379f): 0 of 5, 1 of 5, 4 of 4, 2 of 2, 1 of 1.
ZIPF_DETECTED = {70: (), 140: (1,), 280: (0, 1, 2, 3), 600: (0, 1), 1200: (0,)}
ZIPF_COUNT = {u: (len(ZIPF_DETECTED[u]), n) for u, n in DESIGN}
BSO = "BEYOND_SECOND_ORDER_HELDOUT"
ND = "NOT_DETECTED"
STATUSES = ("ok", "timeout_partial", "cds_gate_fail_or_no_data")
ORDER = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9")
PRIORS = {"H1": 0.45, "H2": 0.80, "H3": 0.55, "H4": 0.85, "H5": 0.85, "H6": 0.60,
          "H7": 0.60, "H8": 0.90, "H9": 0.60}
PRED_TEXT = {"H1": "HOLD detects English in >= 3 of 5 replicates at U = 70",
             "H2": "HOLD detects every replicate at U = 280, 600 and 1200",
             "H3": "R1 is HOLD_MORE_POWERFUL",
             "H4": "at most 2 of the 17 English negative controls detected",
             "H5": "whale song BEYOND_SECOND_ORDER_HELDOUT (pooled p < 0.05)",
             "H6": "at least 6 of the 8 whale years have p < 0.05",
             "H7": "best order of the year-averaged whale entropy is 3 or more",
             "H8": "the whale negative control is NOT_DETECTED",
             "H9": "year-averaged whale H_2 < H_1 (Witten-Bell)"}


# --------------------------------------------------------------------------
# independent re-implementation of HOLD-PREREG.md sections 5 to 7
# --------------------------------------------------------------------------
def lab(ts):
    return BSO if ts["p"] < ALPHA else ND


def amin(v):
    """Index of the smallest value; ties go to the lowest index."""
    best = 0
    for i in range(1, len(v)):
        if v[i] < v[best]:
            best = i
    return best


def power(det, zp):
    """R1 from (detected, replicates) counts per size."""
    if any(u not in det for u in SIZES):
        return "INCOMPLETE"
    diff = [det[u][0] * zp[u][1] - zp[u][0] * det[u][1] for u in SIZES]
    if all(d == 0 for d in diff):
        return "HOLD_EQUAL"
    if all(d >= 0 for d in diff):
        return "HOLD_MORE_POWERFUL"
    if all(d <= 0 for d in diff):
        return "HOLD_LESS_POWERFUL"
    return "MIXED"


def regrade(r):
    rows = r.get("replicates") or []
    want = sorted((u, i) for u, n in DESIGN for i in range(n))
    complete = sorted((x["u"], x["rep"]) for x in rows) == want
    det = {}
    for u in SIZES:
        rs = [x for x in rows if x["u"] == u]
        if rs:
            det[u] = (sum(1 for x in rs if lab(x["real"]) == BSO), len(rs))
    n_neg = sum(1 for x in rows if lab(x["neg"]) == BSO)
    ustar = ppr = None
    if complete:
        for u in SIZES:
            if 2 * det[u][0] >= det[u][1]:
                ustar = u
                break
        if ustar is not None:
            v = [x["phonemes_per_recording"] for x in rows if x["u"] == ustar]
            ppr = sum(v) / len(v)
    r1 = power(det, ZIPF_COUNT) if complete else "INCOMPLETE"
    r3 = "INCOMPLETE" if not complete else ("CONTROL_OK" if n_neg <= 2 else "CONTROL_FAILED")
    g = dict.fromkeys(ORDER)
    if complete:
        g["H1"] = det[70][0] >= 3
        g["H2"] = all(det[u][0] == det[u][1] for u in (280, 600, 1200))
        g["H3"] = r1 == "HOLD_MORE_POWERFUL"
        g["H4"] = n_neg <= 2
    w = r.get("whale") or {}
    mh = None
    if w.get("status") == "ok":
        per = w["real"]["per_recording"]
        mh = [sum(x["H"][k] for x in per) / len(per) for k in range(K_MAX + 1)]
        g["H5"] = lab(w["real"]) == BSO
        g["H6"] = sum(1 for x in per if x["p"] < ALPHA) >= 6
        g["H7"] = amin(mh) >= 3
        g["H8"] = lab(w["neg"]) != BSO
        g["H9"] = mh[2] < mh[1]
        if r3 == "INCOMPLETE":
            r4 = "CALIBRATION_INCOMPLETE"
        elif r3 == "CONTROL_FAILED":
            r4 = "CONTROL_FAILED"
        elif lab(w["real"]) == BSO:
            r4 = BSO
        elif ppr is not None and ppr <= WHALE_SIZE:
            r4 = "NOT_DETECTED_WITH_POWER"
        else:
            r4 = "NOT_DETECTED_UNDERPOWERED"
    else:
        r4 = "WHALE_DATA_MISSING"
    scored = [k for k in ORDER if g[k] is not None]
    brier = (sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in scored) / len(scored)
             if scored else None)
    return {"complete": complete, "det": det, "n_rows": len(rows), "n_neg": n_neg,
            "detect_hold": {str(u): k / n for u, (k, n) in det.items()},
            "detect_zipf": {str(u): k / n for u, (k, n) in ZIPF_COUNT.items()},
            "predictions": g, "brier": brier, "n_scored": len(scored), "whale_mean_H": mh,
            "rules": {"R1_power_vs_zipf": r1, "R2_threshold_utterances": ustar,
                      "R2_threshold_phonemes_per_recording": ppr,
                      "R3_negative_control": r3, "R3_negative_positives": n_neg,
                      "R4_whale": r4}}


# --------------------------------------------------------------------------
# internal consistency of the raw output
# --------------------------------------------------------------------------
def close(a, b, tol=1e-9):
    if a is None or b is None:
        return a is None and b is None
    if a != a and b != b:
        return True
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def p_ok(p, n):
    """p = (1 + k) / (1 + n) for an integer 0 <= k <= n."""
    k = p * (n + 1) - 1
    return abs(k - round(k)) < 1e-6 and 0 <= round(k) <= n


def check_set(ts, B, seed, n_rec, tag):
    bad = []

    def need(cond, what):
        if not cond:
            bad.append("%s: %s" % (tag, what))

    need(ts.get("B") == B, "B")
    need(ts.get("seed") == seed, "seed")
    need(ts.get("kmax") == K_MAX, "kmax")
    per = ts.get("per_recording") or []
    need(len(per) == n_rec, "number of recordings")
    shapes_ok = True
    for i, x in enumerate(per):
        H = x["H"]
        if len(H) != K_MAX + 1:
            need(False, "H length, recording %d" % i)
            shapes_ok = False
            continue
        need(all(h > 0 for h in H), "H > 0, recording %d" % i)
        need(close(x["gain"], H[2] - min(H[3:])), "gain, recording %d" % i)
        need(x["best_order"] == amin(H), "best order, recording %d" % i)
        need(p_ok(x["p"], B), "p, recording %d" % i)
        need(x["bouts"] > 0 and x["symbols"] >= x["bouts"], "sizes, recording %d" % i)
        need(x["null_sd"] >= 0, "null sd, recording %d" % i)
    if per and shapes_ok:
        need(close(ts["mean_gain"], sum(x["gain"] for x in per) / len(per)), "mean gain")
        need(len(ts["mean_H"]) == K_MAX + 1, "mean_H length")
        for k in range(min(len(ts["mean_H"]), K_MAX + 1)):
            need(close(ts["mean_H"][k], sum(x["H"][k] for x in per) / len(per)), "mean H%d" % k)
    need(p_ok(ts["p"], B), "p")
    need(ts.get("label") == lab(ts), "label")
    need(ts.get("null_sd", -1) >= 0, "null sd")
    return bad


def sizes(ts):
    return [(x["symbols"], x["bouts"]) for x in ts.get("per_recording") or []]


def check_result(r):
    bad = []
    rows = r.get("replicates") or []
    if len(set((x["u"], x["rep"]) for x in rows)) != len(rows):
        bad.append("duplicate replicates")
    for x in rows:
        u, rep = x["u"], x["rep"]
        tag = "U=%d rep=%d" % (u, rep)
        if u not in ZIPF_DETECTED:
            bad.append(tag + ": size not in design")
            continue
        s = SEED + 10000 * rep + u
        bad += check_set(x["real"], B_CDS, s, N_REC, tag + " real")
        bad += check_set(x["neg"], B_CDS, s + 7000000, N_REC, tag + " neg")
        if x["start_utt"] != rep * N_REC * u:
            bad.append(tag + ": start utterance")
        if x["zipf_bso"] != (rep in ZIPF_DETECTED[u]):
            bad.append(tag + ": Zipf label transcription")
        pr = x["real"].get("per_recording") or []
        if pr and not close(x["phonemes_per_recording"],
                            sum(a["symbols"] for a in pr) / len(pr)):
            bad.append(tag + ": phonemes per recording")
        if sizes(x["real"]) != sizes(x["neg"]):
            bad.append(tag + ": negative control sizes differ")
    w = r.get("whale") or {}
    if w.get("status") == "ok":
        n = len(w.get("years") or [])
        if n != N_YEARS:
            bad.append("whale: %d years" % n)
        if not (w.get("gate_a") or {}).get("pass"):
            bad.append("whale: gate A not passed but status ok")
        bad += check_set(w["real"], B_WHALE, SEED + 1, n, "whale real")
        bad += check_set(w["neg"], B_WHALE, SEED + 3, n, "whale neg")
        if sizes(w["real"]) != sizes(w["neg"]):
            bad.append("whale: negative control sizes differ")
    return bad


EXPECTED_CONFIG = {"kmax": K_MAX, "alpha": ALPHA, "seed": SEED, "b_cds": B_CDS,
                   "b_whale": B_WHALE, "design": [list(d) for d in DESIGN], "n_rec": N_REC}


def check_meta(r, prereg_sha=None, hold_sha=None):
    bad = []
    if r.get("version") != VERSION:
        bad.append("version")
    if r.get("status") not in STATUSES:
        bad.append("status %r" % r.get("status"))
    reg = r.get("registration") or {}
    if not reg.get("found"):
        bad.append("registration not found")
    if prereg_sha and reg.get("sha256") != prereg_sha:
        bad.append("registration sha256 differs from HOLD-PREREG.md")
    cs = r.get("code_sha256") or {}
    if cs.get("zipfseg.py") != ZIPFSEG_SHA256:
        bad.append("zipfseg.py sha256")
    if hold_sha and cs.get("hold.py") != hold_sha:
        bad.append("hold.py sha256 differs from the published hold.py")
    if r.get("config") != EXPECTED_CONFIG:
        bad.append("config")
    if "grading" not in r:
        bad.append("no grading")
    if r.get("status") == "ok" and not regrade(r)["complete"]:
        bad.append("status ok but calibration incomplete")
    return bad


def compare_grading(gr, rg):
    """Mismatches between the job's own grading and the regrade (empty list = agree)."""
    bad = []
    if gr.get("complete") != rg["complete"]:
        bad.append("complete")
    for key in ("detect_hold", "detect_zipf"):
        a, b = gr.get(key) or {}, rg[key]
        if sorted(a) != sorted(b) or any(not close(a[k], b[k]) for k in b):
            bad.append(key)
    if gr.get("predictions") != rg["predictions"]:
        bad.append("predictions")
    if gr.get("priors") != PRIORS:
        bad.append("priors")
    if not close(gr.get("brier"), rg["brier"]):
        bad.append("brier")
    if gr.get("n_scored") != rg["n_scored"]:
        bad.append("n_scored")
    a, b = gr.get("rules") or {}, rg["rules"]
    if sorted(a) != sorted(b):
        bad.append("rule names")
    for k in b:
        if k == "R2_threshold_phonemes_per_recording":
            if not close(a.get(k), b[k]):
                bad.append(k)
        elif a.get(k) != b[k]:
            bad.append(k)
    return bad


# --------------------------------------------------------------------------
# formats fixed before the result exists (RESULTS-HOLD.md must contain these lines)
# --------------------------------------------------------------------------
def f4(x):
    return "{:.4f}".format(x)


def size_row(u, det):
    """| U | HOLD detected | Zipf detected |"""
    return "| {} | {} of {} | {} of {} |".format(u, det[u][0], det[u][1], ZIPF_COUNT[u][0],
                                                 ZIPF_COUNT[u][1])


def eng_row(x):
    """| U | rep | phonemes per recording | mean gain | null mean gain | p | HOLD label |
    Zipf detected | negative control mean gain | negative control p | negative control label |"""
    re_, ng = x["real"], x["neg"]
    return ("| {} | {} | {:,.0f} | {:+.4f} | {:+.4f} | {:.3f} | `{}` | {} | {:+.4f} | {:.3f} "
            "| `{}` |").format(x["u"], x["rep"], x["phonemes_per_recording"], re_["mean_gain"],
                               re_["null_mean"], re_["p"], lab(re_),
                               "yes" if x["rep"] in ZIPF_DETECTED[x["u"]] else "no",
                               ng["mean_gain"], ng["p"], lab(ng))


def h_row(first, H):
    """| <first cells> | H0 | H1 | H2 | H3 | H4 | H5 | best order |"""
    return "| {} | {} | {} |".format(first, " | ".join(f4(h) for h in H), amin(H))


def eng_h_row(x):
    return h_row("{} | {}".format(x["u"], x["rep"]), x["real"]["mean_H"])


def year_row(year, rec):
    """| year | recordings | elements | H0 .. H5 | best order | gain | null mean gain | p |"""
    return "| {} | {} | {:,} | {} | {} | {:+.4f} | {:+.4f} | {:.3f} |".format(
        year, rec["bouts"], rec["symbols"], " | ".join(f4(h) for h in rec["H"]), amin(rec["H"]),
        rec["gain"], rec["null_mean"], rec["p"])


def set_line(name, ts):
    return ("{}: mean gain **{:+.4f}** bits per symbol, null mean {:+.4f} (sd {:.4f}), "
            "p = **{:.4f}**, label **`{}`**").format(name, ts["mean_gain"], ts["null_mean"],
                                                     ts["null_sd"], ts["p"], lab(ts))


def r2_line(rg):
    if not rg["complete"]:
        return "R2 threshold: **not graded** (calibration incomplete)"
    u = rg["rules"]["R2_threshold_utterances"]
    if u is None:
        return ("R2 threshold: **none** (HOLD detected fewer than half the replicates at "
                "every size)")
    return "R2 threshold: **U = {}** ({:,.0f} phonemes per recording)".format(
        u, rg["rules"]["R2_threshold_phonemes_per_recording"])


def pred_end(k, v):
    return "| {:.2f} | **{}** |".format(
        PRIORS[k], "not graded" if v is None else ("true" if v else "false"))


def required_strings(r, rg):
    w = r.get("whale") or {}
    need = ["Job status: `%s`; whale data status: `%s`" % (r.get("status"), w.get("status"))]
    rows = sorted(r.get("replicates") or [], key=lambda x: (x["u"], x["rep"]))
    for u in SIZES:
        if u in rg["det"]:
            need.append(size_row(u, rg["det"]))
    need += [eng_row(x) for x in rows]
    need += [eng_h_row(x) for x in rows]
    if w.get("status") == "ok":
        need.append(set_line("Whale song", w["real"]))
        need.append(set_line("Whale negative control", w["neg"]))
        for y, rec in zip(w["years"], w["real"]["per_recording"]):
            need.append(year_row(y, rec))
        need.append(h_row("all years (mean) | |", rg["whale_mean_H"]))
    need.append("R1 power vs Zipf: **`%s`**" % rg["rules"]["R1_power_vs_zipf"])
    need.append(r2_line(rg))
    need.append("R3 negative control: **`%s`** (%d of %d English negative controls detected)"
                % (rg["rules"]["R3_negative_control"], rg["n_neg"], rg["n_rows"]))
    need.append("R4 whale: **`%s`**" % rg["rules"]["R4_whale"])
    scored = [k for k in ORDER if rg["predictions"][k] is not None]
    ntrue = sum(1 for k in scored if rg["predictions"][k])
    need.append("%d of %d graded predictions true" % (ntrue, len(scored)))
    if scored:
        need.append("Brier score **%.3f**" % rg["brier"])
    return need


def render_md_lines(r, rg):
    """Every fixed line, in one list (prediction rows included), for writing RESULTS-HOLD.md."""
    return required_strings(r, rg) + [
        "| %s | %s %s" % (k, PRED_TEXT[k], pred_end(k, rg["predictions"][k])) for k in ORDER]


def check_md(md, r, rg):
    """List of required lines missing from md (empty list = all present)."""
    missing = [s for s in required_strings(r, rg) if s not in md]
    lines = md.splitlines()
    for k in ORDER:
        hits = [ln for ln in lines if ln.startswith("| %s |" % k)]
        if len(hits) != 1 or not hits[0].rstrip().endswith(pred_end(k, rg["predictions"][k])):
            missing.append("prediction row " + k)
    return missing


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# --------------------------------------------------------------------------
# result tests (skipped until the job's output is published)
# --------------------------------------------------------------------------
@unittest.skipUnless(HAVE, "results/hold/hold_results.json not published yet")
class TestHoldResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        cls.rg = regrade(cls.r)
        cls.md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""

    def test_meta(self):
        self.assertEqual(check_meta(
            self.r, sha256_file(PREREG) if os.path.exists(PREREG) else None,
            sha256_file(HOLD) if os.path.exists(HOLD) else None), [])

    def test_consistency(self):
        self.assertEqual(check_result(self.r), [])

    def test_grading_matches_regrade(self):
        self.assertEqual(compare_grading(self.r["grading"], self.rg), [])

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-HOLD.md not written yet")
    def test_md_lines(self):
        self.assertEqual(check_md(self.md, self.r, self.rg), [])


# --------------------------------------------------------------------------
# toy tests (always run; every expected value worked out by hand)
# --------------------------------------------------------------------------
TH = [5.0, 4.0, 3.5, 3.25, 3.375, 3.5]      # gain 0.25, best order 3
WH = [4.0, 3.0, 2.5, 2.25, 2.375, 2.5]      # gain 0.25, best order 3, H2 < H1
TOY_DET = {70: (0, 1, 2), 140: (0, 3), 280: (0, 1, 2, 3), 600: (0, 1), 1200: (0,)}


def toy_rec(H, k, B, bouts, symbols):
    return {"H": list(H), "gain": H[2] - min(H[3:]), "p": (1 + k) / (1 + B),
            "null_mean": 0.01, "null_sd": 0.005, "best_order": amin(H),
            "symbols": symbols, "bouts": bouts}


def toy_set(recs, k, B, seed):
    p = (1 + k) / (1 + B)
    return {"B": B, "seed": seed, "kmax": K_MAX,
            "mean_gain": sum(x["gain"] for x in recs) / len(recs), "p": p,
            "label": BSO if p < ALPHA else ND, "null_mean": 0.0, "null_sd": 0.01,
            "mean_H": [sum(x["H"][j] for x in recs) / len(recs) for j in range(K_MAX + 1)],
            "per_recording": recs}


def toy_row(u, rep, k_real, k_neg):
    s = SEED + 10000 * rep + u
    recs = [toy_rec(TH, 50, B_CDS, 10, 650 + rep) for _ in range(N_REC)]
    nrecs = [toy_rec(TH, 50, B_CDS, 10, 650 + rep) for _ in range(N_REC)]
    return {"u": u, "rep": rep, "start_utt": rep * N_REC * u,
            "phonemes_per_recording": float(650 + rep), "zipf_bso": rep in ZIPF_DETECTED[u],
            "real": toy_set(recs, k_real, B_CDS, s),
            "neg": toy_set(nrecs, k_neg, B_CDS, s + 7000000)}


def toy_result(det=None, negs=((140, 4),), whale_k=0):
    det = TOY_DET if det is None else det
    rows = [toy_row(u, i, 0 if i in det[u] else 50, 0 if (u, i) in negs else 50)
            for u, n in DESIGN for i in range(n)]
    # years 2010-2015 per-year p = 1/201; 2016, 2017 p = 101/201
    wrecs = [toy_rec(WH, 0 if y < 6 else 100, B_WHALE, 7, 5720) for y in range(N_YEARS)]
    nrecs = [toy_rec(WH, 100, B_WHALE, 7, 5720) for _ in range(N_YEARS)]
    whale = {"status": "ok", "years": [str(2010 + y) for y in range(N_YEARS)],
             "gate_a": {"pass": True, "reasons": []},
             "real": toy_set(wrecs, whale_k, B_WHALE, SEED + 1),
             "neg": toy_set(nrecs, 50, B_WHALE, SEED + 3)}
    return {"version": VERSION, "status": "ok",
            "registration": {"found": True, "sha256": "aa"},
            "code_sha256": {"zipfseg.py": ZIPFSEG_SHA256, "hold.py": "bb"},
            "config": json.loads(json.dumps(EXPECTED_CONFIG)), "whale": whale,
            "replicates": rows}


class TestToy(unittest.TestCase):
    def test_amin_power(self):
        self.assertEqual(amin([3.0, 2.0, 2.0, 2.5]), 1)
        self.assertEqual(amin(TH), 3)
        z = ZIPF_COUNT
        self.assertEqual(power({70: (3, 5), 140: (2, 5), 280: (4, 4), 600: (2, 2),
                                1200: (1, 1)}, z), "HOLD_MORE_POWERFUL")
        self.assertEqual(power(dict(z), z), "HOLD_EQUAL")
        self.assertEqual(power({70: (0, 5), 140: (0, 5), 280: (4, 4), 600: (2, 2),
                                1200: (1, 1)}, z), "HOLD_LESS_POWERFUL")
        self.assertEqual(power({70: (3, 5), 140: (1, 5), 280: (3, 4), 600: (2, 2),
                                1200: (1, 1)}, z), "MIXED")
        self.assertEqual(power({70: (3, 5)}, z), "INCOMPLETE")

    def test_regrade_all_true(self):
        r = toy_result()
        rg = regrade(r)
        self.assertTrue(rg["complete"])
        self.assertEqual(rg["det"], {70: (3, 5), 140: (2, 5), 280: (4, 4), 600: (2, 2),
                                     1200: (1, 1)})
        self.assertEqual(rg["detect_hold"], {"70": 0.6, "140": 0.4, "280": 1.0, "600": 1.0,
                                             "1200": 1.0})
        self.assertEqual(rg["detect_zipf"], {"70": 0.0, "140": 0.2, "280": 1.0, "600": 1.0,
                                             "1200": 1.0})
        self.assertEqual(rg["rules"], {
            "R1_power_vs_zipf": "HOLD_MORE_POWERFUL", "R2_threshold_utterances": 70,
            "R2_threshold_phonemes_per_recording": 652.0,      # (650 + ... + 654) / 5
            "R3_negative_control": "CONTROL_OK", "R3_negative_positives": 1, "R4_whale": BSO})
        self.assertEqual([rg["predictions"][k] for k in ORDER], [True] * 9)
        # .3025 + .04 + .2025 + .0225 + .0225 + .16 + .16 + .01 + .16 = 1.08
        self.assertAlmostEqual(rg["brier"], 1.08 / 9, places=12)
        self.assertEqual(rg["n_scored"], 9)
        self.assertEqual(rg["whale_mean_H"], WH)
        self.assertEqual(check_result(r), [])
        self.assertEqual(check_meta(r, "aa", "bb"), ["no grading"])
        r["grading"] = dict(rg, priors=PRIORS)
        self.assertEqual(check_meta(r, "aa", "bb"), [])
        self.assertEqual(check_meta(r, "cc", "bb"),
                         ["registration sha256 differs from HOLD-PREREG.md"])
        self.assertEqual(compare_grading(json.loads(json.dumps(r["grading"])), rg), [])

    def test_regrade_other_outcomes(self):
        # 3 negative controls detected -> control failed; whale label then CONTROL_FAILED
        rg = regrade(toy_result(negs=((70, 0), (140, 4), (1200, 0))))
        self.assertEqual(rg["rules"]["R3_negative_control"], "CONTROL_FAILED")
        self.assertEqual(rg["rules"]["R4_whale"], "CONTROL_FAILED")
        self.assertFalse(rg["predictions"]["H4"])
        # a missing replicate -> calibration incomplete, H1-H4 not graded
        r = toy_result()
        r["replicates"].pop()
        rg = regrade(r)
        self.assertFalse(rg["complete"])
        self.assertEqual(rg["rules"]["R1_power_vs_zipf"], "INCOMPLETE")
        self.assertEqual(rg["rules"]["R4_whale"], "CALIBRATION_INCOMPLETE")
        self.assertIsNone(rg["rules"]["R2_threshold_utterances"])
        self.assertEqual([rg["predictions"][k] for k in ORDER], [None] * 4 + [True] * 5)
        # .0225 + .16 + .16 + .01 + .16 = .5125
        self.assertAlmostEqual(rg["brier"], 0.5125 / 5, places=12)
        r["status"] = "ok"
        r["grading"] = {}
        self.assertIn("status ok but calibration incomplete", check_meta(r))
        # whale missing -> H5-H9 not graded
        r = toy_result()
        r["whale"] = {"status": "missing", "dir": "/data/song/whale"}
        rg = regrade(r)
        self.assertEqual(rg["rules"]["R4_whale"], "WHALE_DATA_MISSING")
        self.assertEqual(rg["n_scored"], 4)
        # .3025 + .04 + .2025 + .0225 = .5675
        self.assertAlmostEqual(rg["brier"], 0.5675 / 4, places=12)
        self.assertIsNone(rg["whale_mean_H"])
        self.assertEqual(check_result(r), [])
        # whale not detected (p = 31/201): threshold 652 <= 5720 -> with power
        rg = regrade(toy_result(whale_k=30))
        self.assertEqual(rg["rules"]["R4_whale"], "NOT_DETECTED_WITH_POWER")
        self.assertFalse(rg["predictions"]["H5"])
        # nothing detected in English -> no threshold -> underpowered; HOLD less powerful
        none = {u: () for u in SIZES}
        rg = regrade(toy_result(det=none, whale_k=30))
        self.assertEqual(rg["rules"]["R4_whale"], "NOT_DETECTED_UNDERPOWERED")
        self.assertEqual(rg["rules"]["R1_power_vs_zipf"], "HOLD_LESS_POWERFUL")
        self.assertEqual([rg["predictions"][k] for k in ("H1", "H2", "H3")],
                         [False, False, False])
        # threshold at U = 140 when U = 70 has 2 of 5 (2 * 2 < 5) and U = 140 has 3 of 5
        det = dict(TOY_DET)
        det.update({70: (0, 1), 140: (0, 1, 2)})
        rg = regrade(toy_result(det=det))
        self.assertEqual(rg["rules"]["R2_threshold_utterances"], 140)
        self.assertEqual(rg["rules"]["R2_threshold_phonemes_per_recording"], 652.0)
        self.assertFalse(rg["predictions"]["H1"])

    def test_consistency_catches_errors(self):
        r = toy_result()
        r["replicates"][0]["real"]["per_recording"][0]["gain"] += 0.1
        r["replicates"][3]["real"]["p"] = 0.03         # rep 3 is not detected: label ND
        r["replicates"][2]["neg"]["label"] = BSO
        r["replicates"][4]["zipf_bso"] = True
        r["whale"]["neg"]["per_recording"][0]["symbols"] = 5719
        bad = check_result(r)
        self.assertIn("U=70 rep=0 real: gain, recording 0", bad)
        self.assertIn("U=70 rep=0 real: mean gain", bad)
        self.assertIn("U=70 rep=3 real: p", bad)       # 0.03 * 101 - 1 = 2.03
        self.assertIn("U=70 rep=3 real: label", bad)   # 0.03 < .05 but label says ND
        self.assertIn("U=70 rep=2 neg: label", bad)
        self.assertIn("U=70 rep=4: Zipf label transcription", bad)
        self.assertIn("whale: negative control sizes differ", bad)
        self.assertEqual(len(bad), 7)

    def test_p_ok_close(self):
        self.assertTrue(p_ok(1 / 101, 100))
        self.assertTrue(p_ok(101 / 201, 200))
        self.assertFalse(p_ok(0.15, 200))            # 0.15 * 201 - 1 = 29.15
        self.assertFalse(p_ok(1.5, 100))             # k = 150.5
        self.assertTrue(close(None, None))
        self.assertFalse(close(None, 1.0))
        self.assertTrue(close(float("nan"), float("nan")))

    def test_formats(self):
        r = toy_result()
        x = r["replicates"][0]                        # U 70 rep 0: detected, Zipf no
        self.assertEqual(eng_row(x),
                         "| 70 | 0 | 650 | +0.2500 | +0.0000 | 0.010 | `" + BSO + "` | no | "
                         "+0.2500 | 0.505 | `NOT_DETECTED` |")
        self.assertEqual(eng_h_row(x),
                         "| 70 | 0 | 5.0000 | 4.0000 | 3.5000 | 3.2500 | 3.3750 | 3.5000 | 3 |")
        rg = regrade(r)
        self.assertEqual(size_row(140, rg["det"]), "| 140 | 2 of 5 | 1 of 5 |")
        w = r["whale"]
        self.assertEqual(year_row("2010", w["real"]["per_recording"][0]),
                         "| 2010 | 7 | 5,720 | 4.0000 | 3.0000 | 2.5000 | 2.2500 | 2.3750 | "
                         "2.5000 | 3 | +0.2500 | +0.0100 | 0.005 |")
        # 101 / 201 = 0.50249
        self.assertTrue(year_row("2017", w["real"]["per_recording"][7]).endswith(
            " | +0.2500 | +0.0100 | 0.502 |"))
        self.assertEqual(set_line("Whale song", w["real"]),
                         "Whale song: mean gain **+0.2500** bits per symbol, null mean +0.0000 "
                         "(sd 0.0100), p = **0.0050**, label **`" + BSO + "`**")
        # 51 / 201 = 0.25373
        self.assertTrue(set_line("Whale negative control", w["neg"]).endswith(
            "(sd 0.0100), p = **0.2537**, label **`NOT_DETECTED`**"))
        self.assertEqual(r2_line(rg), "R2 threshold: **U = 70** (652 phonemes per recording)")
        self.assertEqual(pred_end("H3", True), "| 0.55 | **true** |")
        self.assertEqual(pred_end("H9", None), "| 0.60 | **not graded** |")

    def test_md_check(self):
        r = toy_result()
        rg = regrade(r)
        lines = render_md_lines(r, rg)
        self.assertIn("Job status: `ok`; whale data status: `ok`", lines)
        self.assertIn("R1 power vs Zipf: **`HOLD_MORE_POWERFUL`**", lines)
        self.assertIn("R3 negative control: **`CONTROL_OK`** (1 of 17 English negative "
                      "controls detected)", lines)
        self.assertIn("R4 whale: **`" + BSO + "`**", lines)
        self.assertIn("9 of 9 graded predictions true", lines)
        self.assertIn("Brier score **0.120**", lines)
        self.assertIn("| all years (mean) | | | 4.0000 | 3.0000 | 2.5000 | 2.2500 | 2.3750 | "
                      "2.5000 | 3 |", lines)
        self.assertIn("| H4 | at most 2 of the 17 English negative controls detected | 0.85 | "
                      "**true** |", lines)
        # 1 status + 5 size rows + 17 + 17 English rows + 2 whale lines + 8 years + 1 mean
        # + 4 rules + 2 score lines + 9 predictions
        self.assertEqual(len(lines), 66)
        md = "\n".join(lines)
        self.assertEqual(check_md(md, r, rg), [])
        no_r4 = "\n".join(ln for ln in lines if not ln.startswith("R4 whale"))
        self.assertEqual(check_md(no_r4, r, rg), ["R4 whale: **`" + BSO + "`**"])
        no_h6 = "\n".join(ln for ln in lines if not ln.startswith("| H6 |"))
        self.assertEqual(check_md(no_h6, r, rg), ["prediction row H6"])
        # whale missing: no whale lines, 4 of 4 graded
        r["whale"] = {"status": "missing"}
        rg = regrade(r)
        lines = render_md_lines(r, rg)
        self.assertEqual(len(lines), 66 - 11)
        self.assertIn("Job status: `ok`; whale data status: `missing`", lines)
        self.assertIn("4 of 4 graded predictions true", lines)
        self.assertIn("| H5 | whale song BEYOND_SECOND_ORDER_HELDOUT (pooled p < 0.05) | 0.85 | "
                      "**not graded** |", lines)


if __name__ == "__main__":
    unittest.main()
