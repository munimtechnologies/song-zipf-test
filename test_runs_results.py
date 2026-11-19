# SPDX-License-Identifier: Apache-2.0
# test_runs_results.py: the grader for the repeat-collapse test (RUNS-PREREG.md, job
# song-zipf-runs-v1), written and published BEFORE the job has produced any result.
# With its own code (it does not import runs.py) it re-derives every label, rules
# Control/R1-R3, predictions P1-P9 and the Brier score from the raw job output; checks
# every share, motif count (recounted from the printed top chunks), p value, seed, size,
# D1 count and null length ratio for internal consistency; checks that the original whale
# R^2 reproduces RESULTS-WHALE.md; checks all of it against the job's own grading; and fixes
# now the exact lines RESULTS-RUNS.md must print (render_md_lines). Until
# results/runs/runs_results.json exists, the result tests are skipped; the toy-data tests
# always run. Stdlib only; reads files only if they exist and writes nothing.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import hashlib
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "runs", "runs_results.json")
MD = os.path.join(HERE, "RESULTS-RUNS.md")
PREREG = os.path.join(HERE, "RUNS-PREREG.md")
RUNS = os.path.join(HERE, "runs.py")
HAVE = os.path.exists(RES)

VERSION = "runs-1"
LMAX = 8
CAP = 50
ALPHA = 0.05
SEED = 20261120
THETAS = (0.3, 0.5, 0.7)
J = 1                                   # index of the deciding theta, 0.5
TOP = 10
N_REC = 8
YEARS = list(range(2010, 2018))
CDS_DESIGN = ((280, 4), (600, 2))
N_NEG = 3
B_T1_WHALE = 1000
B_T1_NEG = 200
B_T1_CDS = 100
B_T23 = 200
B_T23_SMALL = 100
WHALE_ORIGINAL_R2 = 0.9302888665216728  # RESULTS-WHALE.md, theta 0.5
# sha256 of zipfseg.py at 742fd83 (the same file every earlier test pins)
ZIPFSEG_SHA256 = "25002193229e6d6568939856de5a1760a41c3b462582ea06b6d75ba6d84bddf5"
BSOC = "BEYOND_SECOND_ORDER_AFTER_COLLAPSE"
EBSO = "EXPLAINED_BY_SECOND_ORDER"
EBFO = "EXPLAINED_BY_FIRST_ORDER"
REP = "REPETITION_BEYOND_SECOND_ORDER"
MOT = "MOTIFS_BEYOND_SECOND_ORDER"
NB = "NOT_BEYOND"
MISSING = "WHALE_DATA_MISSING"
STATUSES = ("ok", "timeout_partial", "cds_gate_fail_or_no_data")
ORDER = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9")
PRIORS = {"P1": 0.90, "P2": 0.60, "P3": 0.50, "P4": 0.50, "P5": 0.30, "P6": 0.75,
          "P7": 0.80, "P8": 0.35, "P9": 0.70}
PRED_TEXT = {"P1": "whale T2 is REPETITION_BEYOND_SECOND_ORDER",
             "P2": "English T2 is NOT_BEYOND in at least 4 of 6 replicates",
             "P3": "collapsing removes at least half of the whale's elements (mean share >= 0.5)",
             "P4": "whale T3 is MOTIFS_BEYOND_SECOND_ORDER",
             "P5": "whale T1 is BEYOND_SECOND_ORDER_AFTER_COLLAPSE",
             "P6": "English T1 is BEYOND_SECOND_ORDER_AFTER_COLLAPSE in at least 4 of 6 "
                   "replicates",
             "P7": "none of the 3 negative controls is BEYOND_SECOND_ORDER_AFTER_COLLAPSE",
             "P8": "D1 favours order 2 in 5 or more of the 8 collapsed whale years",
             "P9": "the collapsed whale R^2 at theta 0.5 is below the original 0.9303"}


# --------------------------------------------------------------------------
# independent re-implementation of RUNS-PREREG.md sections 5 to 7
# --------------------------------------------------------------------------
def lab_t2(t):
    return REP if t["p"] < ALPHA else NB


def lab_t3(t):
    return MOT if t["p"] < ALPHA else NB


def t1_p(t, k):
    """p of the order-k collapse-consistent null at theta 0.5, read from by_theta."""
    return t["nulls"]["m%dc" % k]["by_theta"][J]["p"]


def lab_t1(t):
    if t1_p(t, 2) < ALPHA:
        return BSOC
    return EBSO if t1_p(t, 1) < ALPHA else EBFO


def is_motif(tokens):
    """True if the chunk contains x x or x y x."""
    return (any(tokens[i] == tokens[i + 1] for i in range(len(tokens) - 1)) or
            any(tokens[i] == tokens[i + 2] for i in range(len(tokens) - 2)))


def motifs_in(top):
    """Motif chunks among one set's printed top chunks (symbols joined by spaces; no
    whale element code or English phoneme contains a space)."""
    return sum(1 for c in top if is_motif(c.split(" ")))


def d1_count(d):
    return sum(1 for a in d.get("per_set") or [] if a > 0)


def d1_majority(d):
    return d1_count(d) > len(d.get("per_set") or []) / 2


def regrade(r):
    w = r.get("whale") or {}
    ok = w.get("status") == "ok"
    eng = r.get("english") or []
    neg = r.get("negative") or []
    want = sorted((u, i) for u, n in CDS_DESIGN for i in range(n))
    eng_complete = sorted((x["u"], x["rep"]) for x in eng) == want
    neg_complete = sorted(x["i"] for x in neg) == list(range(N_NEG))
    e_bso = sum(1 for x in eng if lab_t1(x["t1"]) == BSOC)
    n_bso = sum(1 for x in neg if lab_t1(x["t1"]) == BSOC)
    if not (eng_complete and neg_complete):
        control = "CALIBRATION_INCOMPLETE"
    elif e_bso >= 4 and n_bso <= 1:
        control = "CONTROL_OK"
    else:
        control = "CONTROL_FAILED"
    g = dict.fromkeys(ORDER)
    if eng_complete:
        g["P2"] = sum(1 for x in eng if lab_t2(x["t2"]) == NB) >= 4
        g["P6"] = e_bso >= 4
    if neg_complete:
        g["P7"] = n_bso == 0
    if ok:
        t1 = w["t1"]
        wl = lab_t1(t1)
        g["P1"] = lab_t2(w["t2"]) == REP
        g["P3"] = w["t2"]["real"] >= 0.5
        g["P4"] = lab_t3(w["t3"]) == MOT
        g["P5"] = wl == BSOC
        g["P8"] = d1_majority(w["d1_collapsed"])
        g["P9"] = t1["real_r2"][J] < WHALE_ORIGINAL_R2
        if control != "CONTROL_OK":
            r3 = control
        elif wl == BSOC:
            r3 = BSOC
        else:
            r3 = wl + ("_POWERED" if d1_majority(w["d1_collapsed"]) else "_UNDERPOWERED")
        r1, r2 = lab_t2(w["t2"]), lab_t3(w["t3"])
    else:
        r1 = r2 = r3 = MISSING
    scored = [k for k in ORDER if g[k] is not None]
    brier = (sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in scored) / len(scored)
             if scored else None)
    return {"rules": {"R1_repetition": r1, "R2_top_chunk_motifs": r2,
                      "R3_zipf_after_collapse": r3, "control": control,
                      "english_bso": e_bso, "negative_bso": n_bso},
            "predictions": g, "priors": dict(PRIORS), "brier": brier,
            "n_scored": len(scored), "eng_complete": eng_complete,
            "neg_complete": neg_complete, "n_eng": len(eng), "n_neg": len(neg)}


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


def check_set(s, b_t1, b_t23, t1_seed, tag):
    """One analysed data set (whale, a negative control or an English replicate)."""
    bad = []

    def need(cond, what):
        if not cond:
            bad.append("%s: %s" % (tag, what))

    e = s.get("elements") or []
    ec = s.get("elements_collapsed") or []
    need(len(e) == N_REC and len(ec) == N_REC, "number of sets")
    for i, (a, b) in enumerate(zip(e, ec)):
        need(0 < b <= a, "collapsed length, set %d" % i)
    need(len(s.get("r2_original") or []) == len(THETAS), "r2_original length")
    # T2
    t2 = s["t2"]
    need(t2.get("B") == b_t23 and t2.get("n_null") == b_t23, "t2 B")
    need(p_ok(t2["p"], b_t23), "t2 p")
    per = t2.get("per_set") or []
    need(len(per) == N_REC, "t2 per_set length")
    for i, (x, a, b) in enumerate(zip(per, e, ec)):
        need(close(x, 1.0 - b / a), "t2 share, set %d" % i)
    if per:
        need(close(t2["real"], sum(per) / len(per)), "t2 mean")
    need(t2.get("null_sd", -1) >= 0, "t2 null sd")
    need(t2.get("label") == lab_t2(t2), "t2 label")
    # T3
    t3 = s["t3"]
    need(t3.get("B") == b_t23 and t3.get("n_null") == b_t23, "t3 B")
    need(p_ok(t3["p"], b_t23), "t3 p")
    tops = t3.get("top_chunks") or []
    need(len(tops) == N_REC and all(len(t) <= TOP for t in tops), "t3 top chunk lists")
    need(t3.get("n_top") == sum(len(t) for t in tops), "t3 n_top")
    need(t3.get("real") == sum(motifs_in(t) for t in tops), "t3 motif recount")
    need(t3.get("null_sd", -1) >= 0, "t3 null sd")
    need(t3.get("label") == lab_t3(t3), "t3 label")
    # T1
    t1 = s["t1"]
    need(t1.get("B") == b_t1, "t1 B")
    need(t1.get("seed") == t1_seed, "t1 seed")
    need(t1.get("thetas") == list(THETAS), "t1 thetas")
    rr = t1.get("real_r2") or []
    shapes = len(rr) == len(THETAS)
    need(shapes, "t1 real_r2 length")
    for k in ("m1c", "m2c"):
        nm = (t1.get("nulls") or {}).get(k) or {}
        bt = nm.get("by_theta") or []
        if len(bt) != len(THETAS) or not shapes:
            need(False, "t1 %s by_theta length" % k)
            shapes = False
            continue
        for j, th in enumerate(THETAS):
            c = bt[j]
            need(close(c["real"], rr[j]), "t1 %s real, theta %.1f" % (k, th))
            need(0 <= c["n_null"] <= b_t1 and p_ok(c["p"], c["n_null"]),
                 "t1 %s p, theta %.1f" % (k, th))
        lm, ln = nm.get("length_ratio_mean"), nm.get("length_ratio_min")
        need(lm is not None and ln is not None and 0 < ln <= lm <= 1 + 1e-9,
             "t1 %s length ratios" % k)
    if shapes:
        need(close(t1.get("p_m1c"), t1_p(t1, 1)), "t1 p_m1c")
        need(close(t1.get("p_m2c"), t1_p(t1, 2)), "t1 p_m2c")
        need(t1.get("label") == lab_t1(t1), "t1 label")
    # D1
    for name in ("d1_original", "d1_collapsed"):
        d = s[name]
        need(len(d.get("per_set") or []) == N_REC, "%s length" % name)
        need(d.get("n_favour_order2") == d1_count(d), "%s count" % name)
        need(d.get("majority") == d1_majority(d), "%s majority" % name)
    return bad


def check_result(r):
    bad = []
    w = r.get("whale") or {}
    ok = w.get("status") == "ok"
    if ok:
        if w.get("years") != YEARS:
            bad.append("whale: years %r" % (w.get("years"),))
        if not (w.get("gate_a") or {}).get("pass"):
            bad.append("whale: gate A not passed but status ok")
        bad += check_set(w, B_T1_WHALE, B_T23, SEED + 3, "whale")
        eby = w.get("elements_by_year") or {}
        if [eby.get(str(y)) for y in YEARS] != w.get("elements"):
            bad.append("whale: elements differ from elements_by_year")
        ro = w.get("r2_original") or []
        if len(ro) != len(THETAS) or not close(ro[J], WHALE_ORIGINAL_R2):
            bad.append("whale: original R^2 does not reproduce RESULTS-WHALE.md")
    neg = r.get("negative") or []
    if len(set(x["i"] for x in neg)) != len(neg):
        bad.append("duplicate negative controls")
    if neg and not ok:
        bad.append("negative controls without whale data")
    for x in neg:
        i = x["i"]
        tag = "negative %d" % i
        if not 0 <= i < N_NEG:
            bad.append(tag + ": index not in design")
            continue
        s = SEED + 100 * (i + 1)
        if x.get("seed") != s:
            bad.append(tag + ": seed")
        bad += check_set(x, B_T1_NEG, B_T23_SMALL, s + 3, tag)
        if ok and x.get("elements") != w.get("elements"):
            bad.append(tag + ": elements differ from whale")
    eng = r.get("english") or []
    if len(set((x["u"], x["rep"]) for x in eng)) != len(eng):
        bad.append("duplicate English replicates")
    design = dict(CDS_DESIGN)
    for x in eng:
        u, rep = x["u"], x["rep"]
        tag = "U=%d rep=%d" % (u, rep)
        if u not in design or not 0 <= rep < design[u]:
            bad.append(tag + ": not in design")
            continue
        if x.get("start_utt") != rep * N_REC * u:
            bad.append(tag + ": start utterance")
        e = x.get("elements") or []
        if not e or not close(x.get("phonemes_per_recording"), sum(e) / len(e)):
            bad.append(tag + ": phonemes per recording")
        bad += check_set(x, B_T1_CDS, B_T23_SMALL, SEED + 10000 * rep + u + 3, tag)
    return bad


EXPECTED_CONFIG = {"lmax": LMAX, "cap": CAP, "alpha": ALPHA, "seed": SEED,
                   "thetas": list(THETAS), "theta": THETAS[J], "top": TOP,
                   "b_t1_whale": B_T1_WHALE, "b_t1_neg": B_T1_NEG, "b_t1_cds": B_T1_CDS,
                   "b_t23": B_T23, "b_t23_small": B_T23_SMALL,
                   "cds_design": [list(d) for d in CDS_DESIGN], "n_neg": N_NEG}


def check_meta(r, prereg_sha=None, runs_sha=None):
    bad = []
    if r.get("version") != VERSION:
        bad.append("version")
    if r.get("status") not in STATUSES:
        bad.append("status %r" % r.get("status"))
    reg = r.get("registration") or {}
    if not reg.get("found"):
        bad.append("registration not found")
    if prereg_sha and reg.get("sha256") != prereg_sha:
        bad.append("registration sha256 differs from RUNS-PREREG.md")
    cs = r.get("code_sha256") or {}
    if cs.get("zipfseg.py") != ZIPFSEG_SHA256:
        bad.append("zipfseg.py sha256")
    if runs_sha and cs.get("runs.py") != runs_sha:
        bad.append("runs.py sha256 differs from the published runs.py")
    if r.get("config") != EXPECTED_CONFIG:
        bad.append("config")
    if "grading" not in r:
        bad.append("no grading")
    if r.get("status") == "ok" and not regrade(r)["eng_complete"]:
        bad.append("status ok but English calibration incomplete")
    return bad


def compare_grading(gr, rg):
    """Mismatches between the job's own grading and the regrade (empty list = agree)."""
    bad = []
    if gr.get("rules") != rg["rules"]:
        bad.append("rules")
    if gr.get("predictions") != rg["predictions"]:
        bad.append("predictions")
    if gr.get("priors") != PRIORS:
        bad.append("priors")
    if not close(gr.get("brier"), rg["brier"]):
        bad.append("brier")
    if gr.get("n_scored") != rg["n_scored"]:
        bad.append("n_scored")
    return bad


# --------------------------------------------------------------------------
# formats fixed before the result exists (RESULTS-RUNS.md must contain these lines)
# --------------------------------------------------------------------------
def by(t1, k, j=J):
    return t1["nulls"]["m%dc" % k]["by_theta"][j]


def t2_line(t2):
    return ("Whale T2: **{:.4f}** of elements removed by collapsing (null mean {:.4f}, sd "
            "{:.4f}), p = **{:.4f}**, label **`{}`**").format(
        t2["real"], t2["null_mean"], t2["null_sd"], t2["p"], lab_t2(t2))


def t3_line(t3):
    return ("Whale T3: **{} of {}** top-ten chunks contain x x or x y x (null mean {:.2f}, sd "
            "{:.2f}), p = **{:.4f}**, label **`{}`**").format(
        t3["real"], t3["n_top"], t3["null_mean"], t3["null_sd"], t3["p"], lab_t3(t3))


def t1_line(t1):
    return ("Whale T1 (theta 0.5): collapsed R^2 **{:.4f}**; order-1 null mean {:.4f}, p = "
            "{:.4f}; order-2 null mean {:.4f}, p = **{:.4f}**; label **`{}`**").format(
        t1["real_r2"][J], by(t1, 1)["null_mean"], by(t1, 1)["p"], by(t1, 2)["null_mean"],
        by(t1, 2)["p"], lab_t1(t1))


def d1_line(w):
    dc, do = w["d1_collapsed"], w["d1_original"]
    return ("Whale D1 (order 2 minus order 1, held out) favours order 2 in **{} of {}** "
            "collapsed years and {} of {} original years").format(
        d1_count(dc), len(dc["per_set"]), d1_count(do), len(do["per_set"]))


def length_line(t1):
    a, b = t1["nulls"]["m1c"], t1["nulls"]["m2c"]
    return ("Null lengths as a share of the real collapsed length: order 1 mean {:.4f} (min "
            "{:.4f}), order 2 mean {:.4f} (min {:.4f})").format(
        a["length_ratio_mean"], a["length_ratio_min"], b["length_ratio_mean"],
        b["length_ratio_min"])


def year_row(w, i):
    """| year | elements | after collapsing | share removed | D1 original | D1 collapsed |
    motif chunks in top ten |"""
    top = w["t3"]["top_chunks"][i]
    return "| {} | {:,} | {:,} | {:.4f} | {:+.4f} | {:+.4f} | {} of {} |".format(
        w["years"][i], w["elements"][i], w["elements_collapsed"][i], w["t2"]["per_set"][i],
        w["d1_original"]["per_set"][i], w["d1_collapsed"]["per_set"][i], motifs_in(top),
        len(top))


def theta_row(w, j):
    """| theta | original R^2 | collapsed R^2 | order-1 null mean | p | order-2 null mean |
    p |"""
    t1 = w["t1"]
    return "| {:.1f} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:.4f} |".format(
        THETAS[j], w["r2_original"][j], t1["real_r2"][j], by(t1, 1, j)["null_mean"],
        by(t1, 1, j)["p"], by(t1, 2, j)["null_mean"], by(t1, 2, j)["p"])


def top_row(w, i):
    """| year | ten most frequent chunks of the original song (theta 0.5) |"""
    return "| {} | {} |".format(w["years"][i],
                                "; ".join("`%s`" % c for c in w["t3"]["top_chunks"][i]))


def neg_row(x):
    """| negative control | share removed | T2 p | T2 label | collapsed R^2 | p order 1 |
    p order 2 | T1 label | D1 collapsed favours order 2 |"""
    t1 = x["t1"]
    return ("| {} | {:.4f} | {:.4f} | `{}` | {:.4f} | {:.4f} | {:.4f} | `{}` | {} of {} "
            "|").format(x["i"], x["t2"]["real"], x["t2"]["p"], lab_t2(x["t2"]),
                        t1["real_r2"][J], t1_p(t1, 1), t1_p(t1, 2), lab_t1(t1),
                        d1_count(x["d1_collapsed"]), len(x["d1_collapsed"]["per_set"]))


def eng_row(x):
    """| U | rep | phonemes per recording | share removed | null share | T2 p | T2 label |
    collapsed R^2 | p order 1 | p order 2 | T1 label | D1 collapsed favours order 2 |"""
    t1 = x["t1"]
    return ("| {} | {} | {:,.0f} | {:.4f} | {:.4f} | {:.4f} | `{}` | {:.4f} | {:.4f} | {:.4f} "
            "| `{}` | {} of {} |").format(
        x["u"], x["rep"], x["phonemes_per_recording"], x["t2"]["real"], x["t2"]["null_mean"],
        x["t2"]["p"], lab_t2(x["t2"]), t1["real_r2"][J], t1_p(t1, 1), t1_p(t1, 2), lab_t1(t1),
        d1_count(x["d1_collapsed"]), len(x["d1_collapsed"]["per_set"]))


def pred_end(k, v):
    return "| {:.2f} | **{}** |".format(
        PRIORS[k], "not graded" if v is None else ("true" if v else "false"))


def required_strings(r, rg):
    w = r.get("whale") or {}
    need = ["Job status: `%s`; whale data status: `%s`" % (r.get("status"), w.get("status"))]
    if w.get("status") == "ok":
        need += [t2_line(w["t2"]), t3_line(w["t3"]), t1_line(w["t1"]), d1_line(w),
                 length_line(w["t1"])]
        need += [year_row(w, i) for i in range(len(w["years"]))]
        need += [theta_row(w, j) for j in range(len(THETAS))]
        need += [top_row(w, i) for i in range(len(w["years"]))]
    need += [neg_row(x) for x in sorted(r.get("negative") or [], key=lambda x: x["i"])]
    need += [eng_row(x) for x in sorted(r.get("english") or [],
                                        key=lambda x: (x["u"], x["rep"]))]
    ru = rg["rules"]
    need.append(("Control: **`{}`** (English beyond second order after collapsing in {} of {} "
                 "replicates; negative controls {} of {})").format(
        ru["control"], ru["english_bso"], rg["n_eng"], ru["negative_bso"], rg["n_neg"]))
    need.append("R1 whale repetition (T2): **`%s`**" % ru["R1_repetition"])
    need.append("R2 whale top-chunk motifs (T3): **`%s`**" % ru["R2_top_chunk_motifs"])
    need.append("R3 whale Zipf after collapsing (T1): **`%s`**" % ru["R3_zipf_after_collapse"])
    scored = [k for k in ORDER if rg["predictions"][k] is not None]
    ntrue = sum(1 for k in scored if rg["predictions"][k])
    need.append("%d of %d graded predictions true" % (ntrue, len(scored)))
    if scored:
        need.append("Brier score **%.3f**" % rg["brier"])
    return need


def render_md_lines(r, rg):
    """Every fixed line, in one list (prediction rows included), for writing RESULTS-RUNS.md."""
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
@unittest.skipUnless(HAVE, "results/runs/runs_results.json not published yet")
class TestRunsResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        cls.rg = regrade(cls.r)
        cls.md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""

    def test_meta(self):
        self.assertEqual(check_meta(
            self.r, sha256_file(PREREG) if os.path.exists(PREREG) else None,
            sha256_file(RUNS) if os.path.exists(RUNS) else None), [])

    def test_consistency(self):
        self.assertEqual(check_result(self.r), [])

    def test_grading_matches_regrade(self):
        self.assertEqual(compare_grading(self.r["grading"], self.rg), [])

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-RUNS.md not written yet")
    def test_md_lines(self):
        self.assertEqual(check_md(self.md, self.r, self.rg), [])


# --------------------------------------------------------------------------
# toy tests (always run; every expected value worked out by hand)
# --------------------------------------------------------------------------
TOY_TOP = ["a a", "b", "c d c", "e f", "g", "h", "i", "j", "k", "l"]   # 2 motif chunks


def toy_set(b_t1, b_t23, t1_seed, k2=0, k3=0, k1=(0, 0), d1o=2, d1c=5, ec=2288,
            rr=(0.90, 0.88, 0.86)):
    """A consistent analysed set: 8 sets of 5,720 elements, ec after collapsing."""
    e = [5720] * N_REC
    per = [1.0 - ec / 5720 for _ in range(N_REC)]
    p2 = (1 + k2) / (1 + b_t23)
    p3 = (1 + k3) / (1 + b_t23)
    nulls = {}
    for k, kk, nm in ((1, k1[0], 0.80), (2, k1[1], 0.84)):
        nulls["m%dc" % k] = {
            "by_theta": [{"real": rr[j], "null_mean": nm, "null_sd": 0.02, "z": 0.0,
                          "p": (1 + kk) / (1 + b_t1), "n_null": b_t1} for j in range(3)],
            "length_ratio_mean": 0.99, "length_ratio_min": 0.95}
    t1 = {"B": b_t1, "seed": t1_seed, "thetas": list(THETAS), "real_r2": list(rr),
          "nulls": nulls, "p_m1c": (1 + k1[0]) / (1 + b_t1), "p_m2c": (1 + k1[1]) / (1 + b_t1)}
    t1["label"] = lab_t1(t1)
    t2 = {"real": sum(per) / N_REC, "null_mean": 0.3, "null_sd": 0.05, "z": 6.0, "p": p2,
          "n_null": b_t23, "per_set": per, "B": b_t23}
    t2["label"] = lab_t2(t2)
    t3 = {"real": 16, "null_mean": 9.5, "null_sd": 2.0, "z": 3.25, "p": p3, "n_null": b_t23,
          "n_top": 80, "B": b_t23, "top_chunks": [list(TOY_TOP) for _ in range(N_REC)]}
    t3["label"] = lab_t3(t3)
    return {"elements": e, "elements_collapsed": [ec] * N_REC,
            "r2_original": [0.95, WHALE_ORIGINAL_R2, 0.91], "t1": t1, "t2": t2, "t3": t3,
            "d1_original": {"per_set": [0.01] * d1o + [-0.01] * (N_REC - d1o),
                            "n_favour_order2": d1o, "majority": d1o > N_REC / 2},
            "d1_collapsed": {"per_set": [0.01] * d1c + [-0.01] * (N_REC - d1c),
                             "n_favour_order2": d1c, "majority": d1c > N_REC / 2}}


def toy_result(over=None):
    """Default: every prediction true. over maps "whale", ("neg", i) or ("eng", u, rep) to
    toy_set keyword overrides."""
    over = over or {}
    kw = dict(k2=0, k3=0, k1=(0, 0), d1o=2, d1c=5)
    kw.update(over.get("whale", {}))
    whale = toy_set(B_T1_WHALE, B_T23, SEED + 3, **kw)
    whale.update({"status": "ok", "years": list(YEARS), "gate_a": {"pass": True, "reasons": []},
                  "data_sha256": "dd", "recordings": {str(y): 7 for y in YEARS},
                  "elements_by_year": {str(y): 5720 for y in YEARS}})
    negs = []
    for i in range(N_NEG):
        s = SEED + 100 * (i + 1)
        kw = dict(k2=50, k3=50, k1=(0, 50), d1o=2, d1c=2)
        kw.update(over.get(("neg", i), {}))
        row = {"i": i, "seed": s}
        row.update(toy_set(B_T1_NEG, B_T23_SMALL, s + 3, **kw))
        negs.append(row)
    eng = []
    for u, n in CDS_DESIGN:
        for rep in range(n):
            kw = dict(k2=50, k3=50, k1=(0, 0), d1o=5, d1c=5)
            kw.update(over.get(("eng", u, rep), {}))
            row = {"u": u, "rep": rep, "start_utt": rep * N_REC * u,
                   "phonemes_per_recording": 5720.0, "seconds_since_start": 1.0}
            row.update(toy_set(B_T1_CDS, B_T23_SMALL, SEED + 10000 * rep + u + 3, **kw))
            eng.append(row)
    return {"version": VERSION, "status": "ok", "registration": {"found": True, "sha256": "aa"},
            "code_sha256": {"zipfseg.py": ZIPFSEG_SHA256, "runs.py": "bb"},
            "config": json.loads(json.dumps(EXPECTED_CONFIG)), "whale": whale,
            "negative": negs, "english": eng}


def job_grading(rg):
    return {k: rg[k] for k in ("rules", "predictions", "priors", "brier", "n_scored")}


class TestToy(unittest.TestCase):
    def test_motif(self):
        self.assertTrue(is_motif(["a", "a"]))
        self.assertTrue(is_motif(["c", "d", "c"]))
        self.assertFalse(is_motif(["e", "f", "g"]))
        self.assertFalse(is_motif(["b"]))
        self.assertEqual(motifs_in(TOY_TOP), 2)
        self.assertEqual(motifs_in(["gr(s)-dws(s) sq sq", "dm sq hq sq", "w hq"]), 2)

    def test_regrade_all_true(self):
        r = toy_result()
        rg = regrade(r)
        self.assertEqual(rg["rules"], {"R1_repetition": REP, "R2_top_chunk_motifs": MOT,
                                       "R3_zipf_after_collapse": BSOC, "control": "CONTROL_OK",
                                       "english_bso": 6, "negative_bso": 0})
        self.assertEqual([rg["predictions"][k] for k in ORDER], [True] * 9)
        # .01 + .16 + .25 + .25 + .49 + .0625 + .04 + .4225 + .09 = 1.775
        self.assertAlmostEqual(rg["brier"], 1.775 / 9, places=12)
        self.assertEqual(rg["n_scored"], 9)
        self.assertEqual(check_result(r), [])
        self.assertEqual(check_meta(r, "aa", "bb"), ["no grading"])
        r["grading"] = job_grading(rg)
        self.assertEqual(check_meta(r, "aa", "bb"), [])
        self.assertEqual(check_meta(r, "cc", "bb"),
                         ["registration sha256 differs from RUNS-PREREG.md"])
        self.assertEqual(check_meta(r, "aa", "cc"),
                         ["runs.py sha256 differs from the published runs.py"])
        self.assertEqual(compare_grading(json.loads(json.dumps(r["grading"])), rg), [])
        g = json.loads(json.dumps(r["grading"]))
        g["rules"]["R3_zipf_after_collapse"] = EBSO + "_POWERED"
        g["brier"] = 0.2
        self.assertEqual(compare_grading(g, rg), ["rules", "brier"])

    def test_whale_t1_outcomes(self):
        # order-2 p = 101/1001 >= .05, order-1 p = 1/1001 < .05; D1 4 of 8 (no majority)
        rg = regrade(toy_result({"whale": {"k1": (0, 100), "d1c": 4}}))
        self.assertEqual(rg["rules"]["R3_zipf_after_collapse"], EBSO + "_UNDERPOWERED")
        self.assertFalse(rg["predictions"]["P5"])
        self.assertFalse(rg["predictions"]["P8"])
        # .8625 (the 7 true ones) + .09 (P5) + .1225 (P8) = 1.075
        self.assertAlmostEqual(rg["brier"], 1.075 / 9, places=12)
        rg = regrade(toy_result({"whale": {"k1": (0, 100), "d1c": 5}}))
        self.assertEqual(rg["rules"]["R3_zipf_after_collapse"], EBSO + "_POWERED")
        rg = regrade(toy_result({"whale": {"k1": (100, 100), "d1c": 5}}))
        self.assertEqual(rg["rules"]["R3_zipf_after_collapse"], EBFO + "_POWERED")
        self.assertEqual(rg["rules"]["control"], "CONTROL_OK")

    def test_whale_t2_t3_p3_p9(self):
        # T2 p = 101/201, T3 p = 21/201: both NOT_BEYOND
        rg = regrade(toy_result({"whale": {"k2": 100, "k3": 20}}))
        self.assertEqual(rg["rules"]["R1_repetition"], NB)
        self.assertEqual(rg["rules"]["R2_top_chunk_motifs"], NB)
        self.assertFalse(rg["predictions"]["P1"])
        self.assertFalse(rg["predictions"]["P4"])
        # share 1 - 3432/5720 = 0.4 < 0.5; collapsed R^2 0.95 >= 0.9303
        r = toy_result({"whale": {"ec": 3432, "rr": (0.96, 0.95, 0.94)}})
        rg = regrade(r)
        self.assertFalse(rg["predictions"]["P3"])
        self.assertFalse(rg["predictions"]["P9"])
        self.assertEqual(check_result(r), [])

    def test_controls(self):
        # two negative controls beyond second order -> control failed
        rg = regrade(toy_result({("neg", 0): {"k1": (0, 0)}, ("neg", 1): {"k1": (0, 0)}}))
        self.assertEqual(rg["rules"]["control"], "CONTROL_FAILED")
        self.assertEqual(rg["rules"]["negative_bso"], 2)
        self.assertEqual(rg["rules"]["R3_zipf_after_collapse"], "CONTROL_FAILED")
        self.assertFalse(rg["predictions"]["P7"])
        # one is allowed by the control, but P7 says none
        rg = regrade(toy_result({("neg", 0): {"k1": (0, 0)}}))
        self.assertEqual(rg["rules"]["control"], "CONTROL_OK")
        self.assertEqual(rg["rules"]["R3_zipf_after_collapse"], BSOC)
        self.assertFalse(rg["predictions"]["P7"])
        # English beyond second order in only 3 of 6 -> control failed, P6 false
        o = {("eng", 280, i): {"k1": (0, 100)} for i in range(3)}
        rg = regrade(toy_result(o))
        self.assertEqual(rg["rules"]["english_bso"], 3)
        self.assertEqual(rg["rules"]["control"], "CONTROL_FAILED")
        self.assertFalse(rg["predictions"]["P6"])
        # English T2 beyond second order in 3 of 6 -> NOT_BEYOND 3 < 4, P2 false; 2 -> true
        o = {("eng", 280, i): {"k2": 0} for i in range(3)}
        self.assertFalse(regrade(toy_result(o))["predictions"]["P2"])
        o = {("eng", 280, i): {"k2": 0} for i in range(2)}
        self.assertTrue(regrade(toy_result(o))["predictions"]["P2"])

    def test_incomplete_and_missing(self):
        r = toy_result()
        r["english"].pop()
        rg = regrade(r)
        self.assertEqual(rg["rules"]["control"], "CALIBRATION_INCOMPLETE")
        self.assertEqual(rg["rules"]["R3_zipf_after_collapse"], "CALIBRATION_INCOMPLETE")
        self.assertIsNone(rg["predictions"]["P2"])
        self.assertIsNone(rg["predictions"]["P6"])
        self.assertTrue(rg["predictions"]["P7"])
        # .01 + .25 + .25 + .49 + .04 + .4225 + .09 = 1.5525
        self.assertAlmostEqual(rg["brier"], 1.5525 / 7, places=12)
        self.assertEqual(rg["n_scored"], 7)
        r["grading"] = job_grading(rg)
        self.assertEqual(check_meta(r), ["status ok but English calibration incomplete"])
        r["status"] = "timeout_partial"
        self.assertEqual(check_meta(r), [])
        # whale missing: the job runs no negative controls, English still runs
        r = toy_result()
        r["whale"] = {"status": "missing"}
        r["negative"] = []
        rg = regrade(r)
        self.assertEqual(rg["rules"], {"R1_repetition": MISSING, "R2_top_chunk_motifs": MISSING,
                                       "R3_zipf_after_collapse": MISSING,
                                       "control": "CALIBRATION_INCOMPLETE",
                                       "english_bso": 6, "negative_bso": 0})
        self.assertEqual([k for k in ORDER if rg["predictions"][k] is not None], ["P2", "P6"])
        # .16 + .0625 = .2225
        self.assertAlmostEqual(rg["brier"], 0.2225 / 2, places=12)
        self.assertEqual(check_result(r), [])
        r["grading"] = job_grading(rg)
        self.assertEqual(check_meta(r), [])

    def test_consistency_catches_errors(self):
        r = toy_result()
        w = r["whale"]
        w["t2"]["per_set"][0] = 0.5
        w["t3"]["real"] = 15
        r["negative"][1]["t1"]["label"] = BSOC
        r["english"][0]["start_utt"] = 5
        w["t1"]["nulls"]["m2c"]["by_theta"][1]["p"] = 0.03     # 0.03 * 1001 - 1 = 29.03
        w["d1_original"]["n_favour_order2"] = 3                # per_set has 2 positive
        w["r2_original"][1] = 0.93
        bad = check_result(r)
        for msg in ("whale: t2 share, set 0", "whale: t2 mean", "whale: t3 motif recount",
                    "negative 1: t1 label", "U=280 rep=0: start utterance",
                    "whale: t1 m2c p, theta 0.5", "whale: t1 p_m2c",
                    "whale: d1_original count",
                    "whale: original R^2 does not reproduce RESULTS-WHALE.md"):
            self.assertIn(msg, bad)
        self.assertEqual(len(bad), 9)
        r = toy_result()
        r["negative"][2]["seed"] = 1
        r["english"][5]["phonemes_per_recording"] = 5000.0
        r["whale"]["years"] = YEARS[:7]
        self.assertEqual(sorted(check_result(r)),
                         sorted(["negative 2: seed", "U=600 rep=1: phonemes per recording",
                                 "whale: years %r" % (YEARS[:7],)]))

    def test_p_ok_close(self):
        self.assertTrue(p_ok(1 / 1001, 1000))
        self.assertTrue(p_ok(51 / 201, 200))
        self.assertTrue(p_ok(1.0, 0))
        self.assertFalse(p_ok(0.03, 1000))
        self.assertFalse(p_ok(1.5, 100))
        self.assertTrue(close(None, None))
        self.assertFalse(close(None, 1.0))
        self.assertTrue(close(float("nan"), float("nan")))

    def test_formats(self):
        r = toy_result()
        w = r["whale"]
        self.assertEqual(t2_line(w["t2"]),
                         "Whale T2: **0.6000** of elements removed by collapsing (null mean "
                         "0.3000, sd 0.0500), p = **0.0050**, label **`" + REP + "`**")
        self.assertEqual(t3_line(w["t3"]),
                         "Whale T3: **16 of 80** top-ten chunks contain x x or x y x (null mean "
                         "9.50, sd 2.00), p = **0.0050**, label **`" + MOT + "`**")
        self.assertEqual(t1_line(w["t1"]),
                         "Whale T1 (theta 0.5): collapsed R^2 **0.8800**; order-1 null mean "
                         "0.8000, p = 0.0010; order-2 null mean 0.8400, p = **0.0010**; label "
                         "**`" + BSOC + "`**")
        self.assertEqual(d1_line(w), "Whale D1 (order 2 minus order 1, held out) favours order "
                                     "2 in **5 of 8** collapsed years and 2 of 8 original years")
        self.assertEqual(length_line(w["t1"]),
                         "Null lengths as a share of the real collapsed length: order 1 mean "
                         "0.9900 (min 0.9500), order 2 mean 0.9900 (min 0.9500)")
        self.assertEqual(year_row(w, 0),
                         "| 2010 | 5,720 | 2,288 | 0.6000 | +0.0100 | +0.0100 | 2 of 10 |")
        self.assertEqual(year_row(w, 7),
                         "| 2017 | 5,720 | 2,288 | 0.6000 | -0.0100 | -0.0100 | 2 of 10 |")
        self.assertEqual(theta_row(w, 1),
                         "| 0.5 | 0.9303 | 0.8800 | 0.8000 | 0.0010 | 0.8400 | 0.0010 |")
        self.assertEqual(theta_row(w, 0),
                         "| 0.3 | 0.9500 | 0.9000 | 0.8000 | 0.0010 | 0.8400 | 0.0010 |")
        self.assertEqual(top_row(w, 3), "| 2013 | `a a`; `b`; `c d c`; `e f`; `g`; `h`; `i`; "
                                        "`j`; `k`; `l` |")
        self.assertEqual(neg_row(r["negative"][0]),
                         "| 0 | 0.6000 | 0.5050 | `NOT_BEYOND` | 0.8800 | 0.0050 | 0.2537 | `"
                         + EBSO + "` | 2 of 8 |")
        self.assertEqual(eng_row(r["english"][0]),
                         "| 280 | 0 | 5,720 | 0.6000 | 0.3000 | 0.5050 | `NOT_BEYOND` | 0.8800 | "
                         "0.0099 | 0.0099 | `" + BSOC + "` | 5 of 8 |")
        self.assertEqual(pred_end("P5", True), "| 0.30 | **true** |")
        self.assertEqual(pred_end("P9", None), "| 0.70 | **not graded** |")

    def test_md_check(self):
        r = toy_result()
        rg = regrade(r)
        lines = render_md_lines(r, rg)
        self.assertIn("Job status: `ok`; whale data status: `ok`", lines)
        self.assertIn("Control: **`CONTROL_OK`** (English beyond second order after collapsing "
                      "in 6 of 6 replicates; negative controls 0 of 3)", lines)
        self.assertIn("R1 whale repetition (T2): **`" + REP + "`**", lines)
        self.assertIn("R3 whale Zipf after collapsing (T1): **`" + BSOC + "`**", lines)
        self.assertIn("9 of 9 graded predictions true", lines)
        self.assertIn("Brier score **0.197**", lines)
        self.assertIn("| P7 | none of the 3 negative controls is BEYOND_SECOND_ORDER_AFTER_COLLAPSE"
                      " | 0.80 | **true** |", lines)
        # 1 status + 5 whale lines + 8 years + 3 thetas + 8 top-chunk rows + 3 negative
        # + 6 English + 4 rules + 2 score lines + 9 predictions
        self.assertEqual(len(lines), 49)
        md = "\n".join(lines)
        self.assertEqual(check_md(md, r, rg), [])
        no_r3 = "\n".join(ln for ln in lines if not ln.startswith("R3 whale"))
        self.assertEqual(check_md(no_r3, r, rg),
                         ["R3 whale Zipf after collapsing (T1): **`" + BSOC + "`**"])
        no_p6 = "\n".join(ln for ln in lines if not ln.startswith("| P6 |"))
        self.assertEqual(check_md(no_p6, r, rg), ["prediction row P6"])
        # whale missing (and so no negative controls): 49 - 24 - 3 lines
        r["whale"] = {"status": "missing"}
        r["negative"] = []
        rg = regrade(r)
        lines = render_md_lines(r, rg)
        self.assertEqual(len(lines), 22)
        self.assertIn("Job status: `ok`; whale data status: `missing`", lines)
        self.assertIn("Control: **`CALIBRATION_INCOMPLETE`** (English beyond second order after "
                      "collapsing in 6 of 6 replicates; negative controls 0 of 0)", lines)
        self.assertIn("2 of 2 graded predictions true", lines)
        self.assertIn("| P5 | whale T1 is BEYOND_SECOND_ORDER_AFTER_COLLAPSE | 0.30 | "
                      "**not graded** |", lines)


if __name__ == "__main__":
    unittest.main()
