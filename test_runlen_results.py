# SPDX-License-Identifier: Apache-2.0
# test_runlen_results.py: the grader for the repeat-permutation test on humpback song
# (RUNLEN-PREREG.md, job song-zipf-runlen-v1), written and published BEFORE the job has
# produced any result. With its own code (it imports neither runlen.py nor hold.py) it
# re-derives the pipeline and control labels, the verdicts of M1, M2 and M3, the share of
# repeated runs each permutation changed, R1-R3, predictions Q1-Q7 and the Brier score from
# the raw job output; checks every p value, label, seed, B, held-out gain, best order, mean
# entropy, null mean, bout count and size for internal consistency; checks the whale sizes,
# bouts and data hash against RESULTS-RUNS.md (results/runs/runs_results.json); checks the
# run counts each permutation acts on against the job's own description of the runs; checks
# it all against the job's own grading; and fixes now the exact lines RESULTS-RUNLEN.md must
# print (render_md_lines), including z = (gain - null mean) / null sd for every permuted data
# set. Until results/runlen/runlen_results.json exists the result tests are skipped; the
# toy-data tests always run. Stdlib only; reads files only if they exist and writes nothing.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import copy
import hashlib
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "runlen", "runlen_results.json")
MD = os.path.join(HERE, "RESULTS-RUNLEN.md")
PREREG = os.path.join(HERE, "RUNLEN-PREREG.md")
RUNLEN = os.path.join(HERE, "runlen.py")
HAVE = os.path.exists(RES)

VERSION = "runlen-1"
SEED = 20261122
HOLD_SEED = 20261120
LMAX = 8
ALPHA = 0.05
B = 200
B_CS = 2000
N_SHUF = 5
KINDS = ("M1", "M2", "M3")
DET_MIN = 3
NOT_MAX = 1
MIN_MOVED = 0.20
PIPE_TOL = 5e-5
KMAX = 5
N_REC = 8
YEARS = list(range(2010, 2018))
# results/hold/hold_results.json, whale.real (mean_gain, p with B = 200)
HOLD_GAIN = -0.04904373293734671
HOLD_P = 1.0 / 201
# From results/runs/runs_results.json (job song-zipf-runs-v1, the same Data S2 file)
WHALE_DATA_SHA256 = "755e4357ce50c672e961671598299c84d074514b4c66bd436ac0c71a3ea11cff"
WHALE_ELEMENTS = [1053, 2028, 3351, 2664, 5765, 14429, 7282, 9177]
WHALE_BOUTS = [4, 6, 6, 6, 7, 13, 6, 7]          # recordings per year = bouts
# SHA-256 of the modules runlen.py records (pinned in setup_runlen.sh)
PINNED = {"hold.py": "6ac8be4474968be23da2b42c76de2427dfe9d0177d32026b329ada0d63e02e4c",
          "zipfseg.py": "25002193229e6d6568939856de5a1760a41c3b462582ea06b6d75ba6d84bddf5",
          "whale_run.py": "b1e128e0eb5f6a211335aa1f402124e94517f751450adf574dd4e742e46211a0"}
BSO = "BEYOND_SECOND_ORDER_HELDOUT"
ND = "NOT_DETECTED"
MISSING = "WHALE_DATA_MISSING"
CS_YES = "COUNTS_CELL_SPECIFIC"
CS_NO = "NO_CELL_SPECIFIC_COUNTS"
STATUSES = ("ok", "timeout_partial", "whale_missing", "whale_gate_fail")
WHALE_STATUS_FOR = {"whale_missing": "missing", "whale_gate_fail": "gate_fail"}
LEN_KEYS = [str(n) for n in range(1, LMAX + 1)]
ORDER = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7")
PRIORS = {"Q1": 0.95, "Q2": 0.75, "Q3": 0.70, "Q4": 0.60, "Q5": 0.45, "Q6": 0.90,
          "Q7": 0.65}
PRED_TEXT = {"Q1": "the pipeline check passes (`PIPELINE_OK`)",
             "Q2": "copy counts are cell-specific beyond cell length (count specificity "
                   "p < 0.05)",
             "Q3": "M1 (copy counts within cell) SURVIVES",
             "Q4": "M2 (copy counts within cell length) SURVIVES",
             "Q5": "M3 (repeated phrases within cell length) SURVIVES",
             "Q6": "the negative control is not detected",
             "Q7": "the mean held-out gain of the five M2 data sets is below M0's"}
KIND_TEXT = {"M1": "copy counts within cell", "M2": "copy counts within cell length",
             "M3": "repeated phrases within cell length"}
EXPECTED_CONFIG = {"seed": SEED, "lmax": LMAX, "alpha": ALPHA, "b": B, "n_shuf": N_SHUF,
                   "b_cs": B_CS, "det_min": DET_MIN, "not_max": NOT_MAX,
                   "min_moved": MIN_MOVED, "hold_seed": HOLD_SEED, "kmax": KMAX}


def perm_seed(kind, i):
    """RUNLEN-PREREG.md section 4: SEED + 1000 k + 10 (i + 1), k = 1, 2, 3 for M1, M2, M3."""
    return SEED + 1000 * {"M1": 1, "M2": 2, "M3": 3}[kind] + 10 * (i + 1)


# --------------------------------------------------------------------------
# independent re-implementation of RUNLEN-PREREG.md sections 5 and 6
# --------------------------------------------------------------------------
def detected(t):
    return t["p"] < ALPHA


def lab(t):
    return BSO if detected(t) else ND


def rows_of(r, kind):
    return [x for x in (r.get("permuted") or []) if x.get("kind") == kind]


def n_detected(rows):
    return len([x for x in rows if detected(x["test"])])


def kind_verdict(rows):
    if len(rows) < N_SHUF:
        return "INCOMPLETE"
    d = n_detected(rows)
    return "SURVIVES" if d >= DET_MIN else ("DESTROYED" if d <= NOT_MAX else "MIXED")


def share_moved(rows):
    tot = sum(x["runs_in_groups"] for x in rows)
    if tot == 0:
        return 0.0
    return sum(x["moved"] for x in rows) / tot


def cs_label(p):
    return CS_YES if p < ALPHA else CS_NO


# R1 when M1 is not inert, by (M1 verdict, M2 verdict)
R1_TABLE = {("SURVIVES", "SURVIVES"): "COUNTS_NOT_NEEDED",
            ("SURVIVES", "DESTROYED"): "CELL_SPECIFIC_COUNTS_CARRY_IT",
            ("SURVIVES", "MIXED"): "MIXED"}
for _m2 in ("SURVIVES", "DESTROYED", "MIXED"):
    R1_TABLE[("DESTROYED", _m2)] = "CONTEXT_SPECIFIC_COUNTS_CARRY_IT"
    R1_TABLE[("MIXED", _m2)] = "MIXED"
R1_INERT = {"SURVIVES": "COUNTS_NOT_NEEDED", "DESTROYED": "COUNTS_CARRY_IT_M1_INERT",
            "MIXED": "MIXED"}
R2_TABLE = {"SURVIVES": "PLACEMENT_NOT_NEEDED", "DESTROYED": "PLACEMENT_CARRIES_IT",
            "MIXED": "MIXED"}


def regrade(r):
    ok = r.get("whale_status") == "ok"
    m0 = r.get("m0") or {}
    has_m0 = "test" in m0
    neg = r.get("neg") or {}
    cs = r.get("count_specificity")
    rows = {k: rows_of(r, k) for k in KINDS}
    v = {k: kind_verdict(rows[k]) for k in KINDS}
    nd = {k: n_detected(rows[k]) for k in KINDS}
    ms = {k: share_moved(rows[k]) for k in KINDS}
    inert = {k: ms[k] < MIN_MOVED for k in KINDS}
    if not (ok and has_m0):
        pipeline = MISSING
    elif (m0.get("lossless") is True and detected(m0["test"])
          and abs(m0["test"]["mean_gain"] - HOLD_GAIN) < PIPE_TOL):
        pipeline = "PIPELINE_OK"
    else:
        pipeline = "PIPELINE_FAILED"
    neg_det = detected(neg["test"]) if "test" in neg else None
    if pipeline != "PIPELINE_OK":
        control = pipeline
    elif neg_det is None:
        control = "CALIBRATION_INCOMPLETE"
    else:
        control = "CONTROL_FAILED" if neg_det else "CONTROL_OK"
    if control != "CONTROL_OK":
        r1 = r2 = control
    else:
        if v["M1"] == "INCOMPLETE" or v["M2"] == "INCOMPLETE":
            r1 = "INCOMPLETE"
        elif inert["M1"]:
            r1 = R1_INERT[v["M2"]]
        else:
            r1 = R1_TABLE[(v["M1"], v["M2"])]
        if v["M3"] == "INCOMPLETE":
            r2 = "INCOMPLETE"
        elif inert["M3"]:
            r2 = "M3_INERT"
        else:
            r2 = R2_TABLE[v["M3"]]
    r3 = cs_label(cs["p"]) if (ok and cs) else MISSING
    m2_mean = (sum(x["test"]["mean_gain"] for x in rows["M2"]) / len(rows["M2"])
               if rows["M2"] else None)
    g = dict.fromkeys(ORDER)
    if ok and has_m0:
        g["Q1"] = pipeline == "PIPELINE_OK"
    if ok and cs:
        g["Q2"] = cs["p"] < ALPHA
    for q, k in (("Q3", "M1"), ("Q4", "M2"), ("Q5", "M3")):
        if v[k] != "INCOMPLETE":
            g[q] = v[k] == "SURVIVES"
    if neg_det is not None:
        g["Q6"] = not neg_det
    if has_m0 and v["M2"] != "INCOMPLETE":
        g["Q7"] = m2_mean < m0["test"]["mean_gain"]
    scored = [k for k in ORDER if g[k] is not None]
    brier = (sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in scored) / len(scored)
             if scored else None)
    return {"rules": {"pipeline": pipeline, "control": control, "negative_detected": neg_det,
                      "R1_copy_counts": r1, "R2_placement": r2, "R3_count_specificity": r3,
                      "verdicts": v, "detected": nd, "moved_share": ms, "inert": inert},
            "predictions": g, "priors": dict(PRIORS), "brier": brier,
            "n_scored": len(scored), "m2_mean_gain": m2_mean,
            "n_rows": {k: len(rows[k]) for k in KINDS}}


# --------------------------------------------------------------------------
# internal consistency of the raw output
# --------------------------------------------------------------------------
def finite(x):
    return (isinstance(x, (int, float)) and not isinstance(x, bool) and x == x
            and abs(x) != float("inf"))


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


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


def argmin(v):
    """Index of the smallest value; the lowest index on ties."""
    best = 0
    for i in range(1, len(v)):
        if v[i] < v[best]:
            best = i
    return best


def check_test(t, Bn, seed, tag, symbols=None, bouts=None):
    """One held-out test (the output of hold.test_set over the 8 recordings)."""
    if not isinstance(t, dict):
        return [tag + ": missing"]
    bad = []

    def need(cond, what):
        if not cond:
            bad.append("%s: %s" % (tag, what))

    need(t.get("B") == Bn, "B")
    need(t.get("seed") == seed, "seed")
    need(t.get("kmax") == KMAX, "kmax")
    p = t.get("p")
    need(finite(p) and p_ok(p, Bn), "p")
    need(finite(p) and t.get("label") == lab(t), "label")
    per = t.get("per_recording") or []
    need(len(per) == N_REC, "number of recordings")
    gains, hs, nms = [], [], []
    for i, x in enumerate(per):
        H = x.get("H") or []
        g = x.get("gain")
        if len(H) != KMAX + 1 or not all(finite(h) for h in H) or not finite(g):
            need(False, "non-finite or missing H or gain, recording %d" % i)
            continue
        gains.append(g)
        hs.append(H)
        nms.append(x.get("null_mean"))
        need(close(g, H[2] - min(H[3:])), "gain, recording %d" % i)
        need(x.get("best_order") == argmin(H), "best order, recording %d" % i)
        need(finite(x.get("p")) and p_ok(x["p"], Bn), "p, recording %d" % i)
        need(finite(x.get("null_sd")) and x["null_sd"] >= 0, "null sd, recording %d" % i)
        nb = x.get("bouts")
        need(is_int(nb) and nb >= 2, "fewer than 2 bouts, recording %d" % i)
        if bouts is not None and i < len(bouts):
            need(nb == bouts[i], "bouts, recording %d" % i)
        if symbols is not None and i < len(symbols):
            need(x.get("symbols") == symbols[i], "symbols, recording %d" % i)
    if per and len(gains) == len(per):
        need(close(t.get("mean_gain"), sum(gains) / len(gains)), "mean gain")
        mh = t.get("mean_H") or []
        need(len(mh) == KMAX + 1 and
             all(close(mh[k], sum(h[k] for h in hs) / len(hs)) for k in range(KMAX + 1)),
             "mean H")
        need(all(finite(v) for v in nms) and
             close(t.get("null_mean"), sum(nms) / len(nms)), "null mean")
    need(finite(t.get("null_sd")) and t["null_sd"] >= 0, "null sd")
    return bad


def check_describe(d, i):
    """One year's description of its runs (runlen.describe)."""
    tag = "describe %d" % YEARS[i]
    if not isinstance(d, dict):
        return [tag + ": missing"]
    el, runs, rep = d.get("elements"), d.get("runs"), d.get("repeated_runs")
    if not (is_int(el) and is_int(runs) and is_int(rep)):
        return [tag + ": counts"]
    bad = []
    if el != WHALE_ELEMENTS[i]:
        bad.append(tag + ": elements")
    if not 0 <= rep <= runs <= el:
        bad.append(tag + ": runs")
    bl = d.get("repeated_runs_by_cell_length")
    if (not isinstance(bl, dict) or any(k not in LEN_KEYS for k in bl)
            or not all(is_int(x) and x > 0 for x in bl.values()) or sum(bl.values()) != rep):
        bad.append(tag + ": runs by cell length")
    dist, rec = d.get("distinct_repeated_cells"), d.get("repeated_runs_of_recurring_cells")
    if not (is_int(dist) and is_int(rec) and (0 < dist <= rep if rep else dist == 0)
            and 0 <= rec <= rep):
        bad.append(tag + ": distinct or recurring cells")
    # every run sung once is a single element, so the elements in repeated runs are
    # elements - (runs - repeated runs)
    sh = d.get("share_elements_in_repeated_runs")
    if not (finite(sh) and abs(sh * el - (el - runs + rep)) < 1e-6):
        bad.append(tag + ": runs and share")
    if rep:
        mc, mx, mo = d.get("mean_copies"), d.get("max_copies"), d.get("share_at_modal_count")
        if not (finite(mc) and is_int(mx) and 2 <= mc <= mx):
            bad.append(tag + ": copies")
        if not (finite(mo) and 0 < mo <= 1):
            bad.append(tag + ": modal share")
    return bad


def run_totals(desc):
    """Repeated runs, those of one-element cells, and those of recurring cells, summed over
    the years; None if the description is not usable."""
    if len(desc) != N_REC:
        return None
    tot = {"rep": 0, "len1": 0, "recur": 0}
    for d in desc:
        if not isinstance(d, dict):
            return None
        rep, rec = d.get("repeated_runs"), d.get("repeated_runs_of_recurring_cells")
        bl = d.get("repeated_runs_by_cell_length")
        if not (is_int(rep) and is_int(rec) and isinstance(bl, dict)
                and is_int(bl.get("1", 0))):
            return None
        tot["rep"] += rep
        tot["len1"] += bl.get("1", 0)
        tot["recur"] += rec
    return tot


def check_result(r):
    bad = []
    ok = r.get("whale_status") == "ok"
    rows = r.get("permuted") or []
    if not ok:
        if rows or r.get("m0") or r.get("neg") or r.get("count_specificity"):
            bad.append("results without whale data")
        return bad
    if [str(y) for y in (r.get("years") or [])] != [str(y) for y in YEARS]:
        bad.append("years %r" % (r.get("years"),))
    if not (r.get("gate_a") or {}).get("pass"):
        bad.append("gate A not passed but status ok")
    if r.get("data_sha256") != WHALE_DATA_SHA256:
        bad.append("data sha256 differs from RUNS")
    if r.get("elements") != WHALE_ELEMENTS:
        bad.append("sizes differ from RUNS")
    desc = r.get("describe") or []
    if len(desc) != N_REC:
        bad.append("describe: number of recordings")
    else:
        for i, d in enumerate(desc):
            bad += check_describe(d, i)
    tot = run_totals(desc)
    # M0
    m0 = r.get("m0") or {}
    if not isinstance(m0.get("lossless"), bool):
        bad.append("M0: lossless flag")
    t = m0.get("test")
    bad += check_test(t, B, HOLD_SEED, "M0", symbols=WHALE_ELEMENTS, bouts=WHALE_BOUTS)
    if isinstance(t, dict) and finite(t.get("mean_gain")) and finite(t.get("p")):
        em = abs(t["mean_gain"] - HOLD_GAIN) < 1e-12 and abs(t["p"] - HOLD_P) < 1e-12
        if m0.get("exact_match") is not em:
            bad.append("M0: exact match flag")
    # count specificity
    cs = r.get("count_specificity")
    if not isinstance(cs, dict):
        bad.append("count specificity: missing")
    else:
        if cs.get("B") != B_CS:
            bad.append("count specificity: B")
        if cs.get("seed") != SEED + 5:
            bad.append("count specificity: seed")
        p = cs.get("p")
        if not (finite(p) and p_ok(p, B_CS)):
            bad.append("count specificity: p")
        elif cs.get("label") != cs_label(p):
            bad.append("count specificity: label")
        if not (all(finite(cs.get(k)) for k in ("real", "null_mean", "null_sd"))
                and cs["real"] >= -1e-9 and cs["null_mean"] >= -1e-9 and cs["null_sd"] >= 0):
            bad.append("count specificity: statistic")
    # negative control
    neg = r.get("neg")
    if not isinstance(neg, dict):
        bad.append("negative control: missing")
    else:
        n, mv = neg.get("runs_in_groups"), neg.get("moved")
        if not (is_int(n) and is_int(mv) and 0 <= mv <= n):
            bad.append("negative control: moved")
        ne = neg.get("elements") or []
        if len(ne) != N_REC:
            bad.append("negative control: number of recordings")
        bad += check_test(neg.get("test"), B, SEED + 9, "negative control",
                          symbols=ne if len(ne) == N_REC else None, bouts=WHALE_BOUTS)
    # permuted data sets, interleaved M1, M2, M3 for replicate 0, then 1, ...
    want = [(k, i) for i in range(N_SHUF) for k in KINDS]
    got = [(x.get("kind"), x.get("i")) for x in rows]
    if got != want[:len(got)]:
        bad.append("permuted rows out of order")
    for x in rows:
        k, i = x.get("kind"), x.get("i")
        if k not in KINDS or not (is_int(i) and 0 <= i < N_SHUF):
            bad.append("row %s %s: not in design" % (k, i))
            continue
        tag = "%s %d" % (k, i)
        s = perm_seed(k, i)
        if x.get("seed") != s:
            bad.append(tag + ": seed")
        n, mv = x.get("runs_in_groups"), x.get("moved")
        if not (is_int(n) and is_int(mv) and 0 <= mv <= n):
            bad.append(tag + ": moved")
        elif tot is not None:
            if n != (tot["rep"] - tot["len1"] if k == "M3" else tot["rep"]):
                bad.append(tag + ": runs in groups")
            if k == "M1" and mv > tot["recur"]:
                bad.append(tag + ": moved more than recurring cells allow")
        if x.get("elements") != WHALE_ELEMENTS:
            bad.append(tag + ": elements")
        bad += check_test(x.get("test"), B, s + 1, tag + " test", symbols=WHALE_ELEMENTS,
                          bouts=WHALE_BOUTS)
    return bad


def check_meta(r, prereg_sha=None, runlen_sha=None):
    bad = []
    if r.get("version") != VERSION:
        bad.append("version")
    st = r.get("status")
    if st not in STATUSES:
        bad.append("status %r" % (st,))
    reg = r.get("registration") or {}
    if not reg.get("found"):
        bad.append("registration not found")
    if prereg_sha and reg.get("sha256") != prereg_sha:
        bad.append("registration sha256 differs from RUNLEN-PREREG.md")
    cs = r.get("code_sha256") or {}
    for m in sorted(PINNED):
        if cs.get(m) != PINNED[m]:
            bad.append("%s sha256" % m)
    if runlen_sha and cs.get("runlen.py") != runlen_sha:
        bad.append("runlen.py sha256 differs from the published runlen.py")
    if r.get("config") != EXPECTED_CONFIG:
        bad.append("config")
    if "grading" not in r:
        bad.append("no grading")
    n = len(r.get("permuted") or [])
    ws = r.get("whale_status")
    if st == "ok" and not (ws == "ok" and n == N_SHUF * len(KINDS)):
        bad.append("status ok but a part did not run")
    if st == "timeout_partial" and not (ws == "ok" and n < N_SHUF * len(KINDS)):
        bad.append("status timeout_partial does not match the rows")
    if st in WHALE_STATUS_FOR and ws != WHALE_STATUS_FOR[st]:
        bad.append("whale status does not match the job status")
    return bad


def compare_grading(gr, rg):
    """Mismatches between the job's own grading and the regrade (empty list = agree)."""
    bad = []
    a = dict(gr.get("rules") or {})
    b = dict(rg["rules"])
    ams = a.pop("moved_share", None)
    bms = b.pop("moved_share")
    if a != b:
        bad.append("rules")
    if not (isinstance(ams, dict) and sorted(ams) == sorted(bms)
            and all(close(ams[k], bms[k]) for k in bms)):
        bad.append("moved share")
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
# formats fixed before the result exists (RESULTS-RUNLEN.md must contain these lines)
# --------------------------------------------------------------------------
def yes_no(v):
    return "not run" if v is None else ("yes" if v else "no")


def zstr(t):
    s = t.get("null_sd")
    if not (finite(s) and s > 0):
        return "n/a"
    return "{:+.2f}".format((t["mean_gain"] - t["null_mean"]) / s)


def status_line(r):
    return "Job status: `{}`; whale data status: `{}`".format(r.get("status"),
                                                             r.get("whale_status"))


def m0_line(r, rg):
    m = r["m0"]
    t = m["test"]
    return ("M0, the unpermuted song with HOLD's seed: runs expand back to the song exactly: {}; "
            "mean held-out gain **{:+.4f}** bits per element against {:+.4f} (sd {:.4f}) for "
            "second-order surrogates (B = {:,}), p = **{:.4f}**; identical to RESULTS-HOLD.md's "
            "gain and p: {}; **`{}`**").format(
        yes_no(m.get("lossless")), t["mean_gain"], t["null_mean"], t["null_sd"], t["B"], t["p"],
        yes_no(m.get("exact_match")), rg["rules"]["pipeline"])


def neg_line(r):
    x = r["neg"]
    t = x["test"]
    return ("Negative control (M3 on one second-order surrogate of the whale): {:,} of {:,} "
            "repeated runs changed; mean gain {:+.4f} against {:+.4f} (B = {:,}), p = {:.4f}, "
            "label `{}`").format(x["moved"], x["runs_in_groups"], t["mean_gain"],
                                 t["null_mean"], t["B"], t["p"], lab(t))


def cs_line(r):
    c = r["count_specificity"]
    return ("Count specificity (cell and copy count given cell length, over repeated runs, "
            "summed over years): {:.3f} against {:.3f} (sd {:.3f}) after M2 permutations "
            "(B = {:,}), p = **{:.4f}**, **`{}`**").format(
        c["real"], c["null_mean"], c["null_sd"], c["B"], c["p"], cs_label(c["p"]))


def year_row(r, i):
    """| year | elements | runs | repeated runs | share of elements in repeated runs |
    distinct repeated cells | repeated runs of recurring cells | mean copies | max copies |
    share at a cell's modal count |"""
    d = r["describe"][i]
    return "| {} | {:,} | {:,} | {:,} | {:.4f} | {:,} | {:,} | {:.2f} | {} | {:.4f} |".format(
        r["years"][i], d["elements"], d["runs"], d["repeated_runs"],
        d["share_elements_in_repeated_runs"], d["distinct_repeated_cells"],
        d["repeated_runs_of_recurring_cells"], d["mean_copies"], d["max_copies"],
        d["share_at_modal_count"])


def perm_row(x):
    """| kind | replicate | seed | repeated runs changed | gain | null mean | z | p | label |"""
    t = x["test"]
    return "| {} | {} | {} | {:,} of {:,} | {:+.4f} | {:+.4f} | {} | {:.4f} | `{}` |".format(
        x["kind"], x["i"], x["seed"], x["moved"], x["runs_in_groups"], t["mean_gain"],
        t["null_mean"], zstr(t), t["p"], lab(t))


def kind_line(rg, k):
    ru = rg["rules"]
    return ("{} ({}): detected in {} of {} permuted data sets; share of repeated runs changed "
            "{:.4f}{}; verdict **`{}`**").format(
        k, KIND_TEXT[k], ru["detected"][k], rg["n_rows"][k], ru["moved_share"][k],
        " (INERT)" if ru["inert"][k] else "", ru["verdicts"][k])


def m2_line(r, rg):
    return "Mean held-out gain of the {} M2 data sets {:+.4f} against M0's {:+.4f}".format(
        rg["n_rows"]["M2"], rg["m2_mean_gain"], r["m0"]["test"]["mean_gain"])


def pred_end(k, v):
    return "| {:.2f} | **{}** |".format(
        PRIORS[k], "not graded" if v is None else ("true" if v else "false"))


def required_strings(r, rg):
    need = [status_line(r)]
    has_m0 = "test" in (r.get("m0") or {})
    if r.get("whale_status") == "ok":
        if has_m0:
            need.append(m0_line(r, rg))
        if "test" in (r.get("neg") or {}):
            need.append(neg_line(r))
        if r.get("count_specificity"):
            need.append(cs_line(r))
        need += [year_row(r, i) for i in range(len(r.get("describe") or []))]
    need += [perm_row(x) for x in (r.get("permuted") or [])]
    need += [kind_line(rg, k) for k in KINDS if rg["n_rows"][k]]
    if has_m0 and rg["m2_mean_gain"] is not None:
        need.append(m2_line(r, rg))
    ru = rg["rules"]
    need.append("Pipeline: **`{}`**; control: **`{}`** (negative control detected: {})".format(
        ru["pipeline"], ru["control"], yes_no(ru["negative_detected"])))
    need.append("R1 copy counts: **`%s`**" % ru["R1_copy_counts"])
    need.append("R2 placement of repeated phrases: **`%s`**" % ru["R2_placement"])
    need.append("R3 count specificity: **`%s`**" % ru["R3_count_specificity"])
    scored = [k for k in ORDER if rg["predictions"][k] is not None]
    ntrue = sum(1 for k in scored if rg["predictions"][k])
    need.append("%d of %d graded predictions true" % (ntrue, len(scored)))
    if scored:
        need.append("Brier score **%.3f**" % rg["brier"])
    return need


def render_md_lines(r, rg):
    """Every fixed line, in one list (prediction rows included), for writing RESULTS-RUNLEN.md."""
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
@unittest.skipUnless(HAVE, "results/runlen/runlen_results.json not published yet")
class TestRunlenResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        cls.rg = regrade(cls.r)
        cls.md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""

    def test_meta(self):
        self.assertEqual(check_meta(
            self.r, sha256_file(PREREG) if os.path.exists(PREREG) else None,
            sha256_file(RUNLEN) if os.path.exists(RUNLEN) else None), [])

    def test_consistency(self):
        self.assertEqual(check_result(self.r), [])

    def test_grading_matches_regrade(self):
        self.assertEqual(compare_grading(self.r["grading"], self.rg), [])

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-RUNLEN.md not written yet")
    def test_md_lines(self):
        self.assertEqual(check_md(self.md, self.r, self.rg), [])


# --------------------------------------------------------------------------
# toy tests (always run; every expected value worked out by hand)
# --------------------------------------------------------------------------
def mk_test(Bn, seed, g, k, symbols, bouts=None, null_mean=-0.08, null_sd=0.004):
    """A consistent held-out test: every recording has gain g (g > -0.1) and p (1+k)/(1+Bn)."""
    bouts = bouts or WHALE_BOUTS
    p = (1 + k) / (1 + Bn)
    per = []
    for i in range(N_REC):
        H = [3.0, 2.5, 2.0, 2.0 - g, 2.1, 2.2]
        per.append({"H": H, "gain": H[2] - min(H[3:]), "p": p, "null_mean": null_mean,
                    "null_sd": 0.01, "best_order": argmin(H), "symbols": symbols[i],
                    "bouts": bouts[i]})
    gains = [x["gain"] for x in per]
    return {"B": Bn, "seed": seed, "kmax": KMAX, "mean_gain": sum(gains) / len(gains), "p": p,
            "label": BSO if p < ALPHA else ND, "null_mean": null_mean, "null_sd": null_sd,
            "mean_H": [sum(x["H"][j] for x in per) / N_REC for j in range(KMAX + 1)],
            "per_recording": per}


def toy_describe(i):
    """100 repeated runs a year (40 of one-element cells), 600 elements in them."""
    el = WHALE_ELEMENTS[i]
    return {"elements": el, "runs": el - 500, "repeated_runs": 100,
            "share_elements_in_repeated_runs": 600 / el, "distinct_repeated_cells": 20,
            "repeated_runs_of_recurring_cells": 90,
            "repeated_runs_by_cell_length": {"1": 40, "2": 30, "3": 30},
            "mean_copies": 3.0, "max_copies": 9, "share_at_modal_count": 0.5}


def toy_result(over=None, n_rows=N_SHUF * len(KINDS)):
    """Default: every prediction true. over maps "m0", "neg", "cs", a kind ("M1") or a
    (kind, replicate) pair to overrides (g, k, moved; lossless for m0)."""
    over = over or {}
    m0kw = {"g": HOLD_GAIN, "k": 0}
    m0kw.update(over.get("m0", {}))
    lossless = m0kw.pop("lossless", True)
    t0 = mk_test(B, HOLD_SEED, symbols=WHALE_ELEMENTS, **m0kw)
    m0 = {"lossless": lossless, "test": t0,
          "exact_match": (abs(t0["mean_gain"] - HOLD_GAIN) < 1e-12
                          and abs(t0["p"] - HOLD_P) < 1e-12)}
    negkw = {"g": -0.08, "k": 100}
    negkw.update(over.get("neg", {}))
    neg = {"runs_in_groups": 300, "moved": 150, "elements": list(WHALE_ELEMENTS),
           "test": mk_test(B, SEED + 9, symbols=WHALE_ELEMENTS, **negkw)}
    cs = {"real": 50.0, "null_mean": 20.0, "null_sd": 5.0, "p": 1 / 2001, "B": B_CS,
          "seed": SEED + 5, "label": CS_YES}
    cs.update(over.get("cs", {}))
    rows = []
    for i, k in [(i, k) for i in range(N_SHUF) for k in KINDS][:n_rows]:
        s = perm_seed(k, i)
        kw = {"g": -0.06, "k": 0, "moved": 240 if k == "M3" else 400}
        kw.update(over.get(k, {}))
        kw.update(over.get((k, i), {}))
        moved = kw.pop("moved")
        rows.append({"kind": k, "i": i, "seed": s, "runs_in_groups": 480 if k == "M3" else 800,
                     "moved": moved, "elements": list(WHALE_ELEMENTS),
                     "test": mk_test(B, s + 1, symbols=WHALE_ELEMENTS, **kw),
                     "seconds_since_start": 1.0})
    code = dict(PINNED)
    code["runlen.py"] = "bb"
    return {"version": VERSION, "python": "3.12.0", "code_sha256": code,
            "config": dict(EXPECTED_CONFIG), "permuted": rows,
            "registration": {"found": True, "tries": 1, "sha256": "aa"},
            "data_sha256": WHALE_DATA_SHA256, "gate_a": {"pass": True, "reasons": []},
            "whale_status": "ok", "years": list(YEARS),
            "describe": [toy_describe(i) for i in range(N_REC)],
            "elements": list(WHALE_ELEMENTS), "count_specificity": cs, "m0": m0, "neg": neg,
            "status": "ok" if n_rows == N_SHUF * len(KINDS) else "timeout_partial"}


def toy_missing():
    r = toy_result()
    for key in ("data_sha256", "gate_a", "years", "describe", "elements", "count_specificity",
                "m0", "neg"):
        del r[key]
    r["permuted"] = []
    r["whale_status"] = "missing"
    r["status"] = "whale_missing"
    return r


def job_grading(rg):
    return {k: rg[k] for k in ("rules", "predictions", "priors", "brier", "n_scored")}


ALL3 = {"M1": 5, "M2": 5, "M3": 5}


class TestToy(unittest.TestCase):
    def test_regrade_all_true(self):
        r = toy_result()
        rg = regrade(r)
        self.assertEqual(rg["rules"], {
            "pipeline": "PIPELINE_OK", "control": "CONTROL_OK", "negative_detected": False,
            "R1_copy_counts": "COUNTS_NOT_NEEDED", "R2_placement": "PLACEMENT_NOT_NEEDED",
            "R3_count_specificity": CS_YES,
            "verdicts": {"M1": "SURVIVES", "M2": "SURVIVES", "M3": "SURVIVES"},
            "detected": ALL3, "moved_share": {"M1": 0.5, "M2": 0.5, "M3": 0.5},
            "inert": {"M1": False, "M2": False, "M3": False}})
        self.assertEqual([rg["predictions"][k] for k in ORDER], [True] * 7)
        # .0025 + .0625 + .09 + .16 + .3025 + .01 + .1225 = .75
        self.assertAlmostEqual(rg["brier"], 0.75 / 7, places=12)
        self.assertEqual(rg["n_scored"], 7)
        self.assertAlmostEqual(rg["m2_mean_gain"], -0.06, places=12)
        self.assertEqual(check_result(r), [])
        self.assertEqual(check_meta(r, "aa", "bb"), ["no grading"])
        r["grading"] = job_grading(rg)
        self.assertEqual(check_meta(r, "aa", "bb"), [])
        self.assertEqual(check_meta(r, "cc", "bb"),
                         ["registration sha256 differs from RUNLEN-PREREG.md"])
        self.assertEqual(check_meta(r, "aa", "cc"),
                         ["runlen.py sha256 differs from the published runlen.py"])
        r2 = copy.deepcopy(r)
        r2["code_sha256"]["hold.py"] = "x"
        r2["config"]["min_moved"] = 0.1
        self.assertEqual(check_meta(r2, "aa", "bb"), ["hold.py sha256", "config"])
        self.assertEqual(compare_grading(json.loads(json.dumps(r["grading"])), rg), [])
        g = json.loads(json.dumps(r["grading"]))
        g["rules"]["R1_copy_counts"] = "MIXED"
        g["rules"]["moved_share"]["M3"] = 0.4
        g["brier"] = 0.2
        self.assertEqual(compare_grading(g, rg), ["rules", "moved share", "brier"])

    def test_r1_branches(self):
        # M1 destroyed (p = 101/201 in all five): counts carry it in context
        rg = regrade(toy_result({"M1": {"k": 100}}))
        self.assertEqual(rg["rules"]["verdicts"]["M1"], "DESTROYED")
        self.assertEqual(rg["rules"]["R1_copy_counts"], "CONTEXT_SPECIFIC_COUNTS_CARRY_IT")
        self.assertFalse(rg["predictions"]["Q3"])
        # Q3 false costs .49 instead of .09
        self.assertAlmostEqual(rg["brier"], 1.15 / 7, places=12)
        # M1 survives, M2 destroyed
        rg = regrade(toy_result({"M2": {"k": 100}}))
        self.assertEqual(rg["rules"]["R1_copy_counts"], "CELL_SPECIFIC_COUNTS_CARRY_IT")
        self.assertFalse(rg["predictions"]["Q4"])
        self.assertTrue(rg["predictions"]["Q7"])
        # M2 detected in 2 of 5 -> MIXED
        rg = regrade(toy_result({("M2", 0): {"k": 100}, ("M2", 1): {"k": 100},
                                 ("M2", 2): {"k": 100}}))
        self.assertEqual(rg["rules"]["detected"]["M2"], 2)
        self.assertEqual(rg["rules"]["verdicts"]["M2"], "MIXED")
        self.assertEqual(rg["rules"]["R1_copy_counts"], "MIXED")
        # M1 detected in 3 of 5 still SURVIVES
        rg = regrade(toy_result({("M1", 0): {"k": 100}, ("M1", 4): {"k": 100}}))
        self.assertEqual(rg["rules"]["detected"]["M1"], 3)
        self.assertEqual(rg["rules"]["R1_copy_counts"], "COUNTS_NOT_NEEDED")
        # M1 in 2 of 5 -> MIXED, not inert -> R1 MIXED
        rg = regrade(toy_result({("M1", 0): {"k": 100}, ("M1", 1): {"k": 100},
                                 ("M1", 2): {"k": 100}}))
        self.assertEqual(rg["rules"]["verdicts"]["M1"], "MIXED")
        self.assertEqual(rg["rules"]["R1_copy_counts"], "MIXED")
        # M1 inert (500 of 4,000 = 0.125 changed): R1 is read from M2 alone
        rg = regrade(toy_result({"M1": {"moved": 100, "k": 100}}))
        self.assertTrue(rg["rules"]["inert"]["M1"])
        self.assertEqual(rg["rules"]["moved_share"]["M1"], 0.125)
        self.assertEqual(rg["rules"]["R1_copy_counts"], "COUNTS_NOT_NEEDED")
        rg = regrade(toy_result({"M1": {"moved": 100}, "M2": {"k": 100}}))
        self.assertEqual(rg["rules"]["R1_copy_counts"], "COUNTS_CARRY_IT_M1_INERT")
        rg = regrade(toy_result({"M1": {"moved": 100}, ("M2", 3): {"k": 100},
                                 ("M2", 4): {"k": 100}, ("M2", 2): {"k": 100}}))
        self.assertEqual(rg["rules"]["R1_copy_counts"], "MIXED")
        # exactly 20% changed (800 of 4,000) is not inert
        rg = regrade(toy_result({"M1": {"moved": 160, "k": 100}}))
        self.assertFalse(rg["rules"]["inert"]["M1"])
        self.assertEqual(rg["rules"]["R1_copy_counts"], "CONTEXT_SPECIFIC_COUNTS_CARRY_IT")

    def test_r2_branches(self):
        rg = regrade(toy_result({"M3": {"k": 100}}))
        self.assertEqual(rg["rules"]["R2_placement"], "PLACEMENT_CARRIES_IT")
        self.assertFalse(rg["predictions"]["Q5"])
        # 250 of 2,400 changed
        rg = regrade(toy_result({"M3": {"moved": 50}}))
        self.assertTrue(rg["rules"]["inert"]["M3"])
        self.assertEqual(rg["rules"]["R2_placement"], "M3_INERT")
        self.assertTrue(rg["predictions"]["Q5"])
        rg = regrade(toy_result({("M3", 0): {"k": 100}, ("M3", 1): {"k": 100},
                                 ("M3", 2): {"k": 100}}))
        self.assertEqual(rg["rules"]["R2_placement"], "MIXED")

    def test_controls(self):
        rg = regrade(toy_result({"neg": {"k": 0}}))
        self.assertIs(rg["rules"]["negative_detected"], True)
        self.assertEqual(rg["rules"]["control"], "CONTROL_FAILED")
        self.assertEqual(rg["rules"]["R1_copy_counts"], "CONTROL_FAILED")
        self.assertEqual(rg["rules"]["R2_placement"], "CONTROL_FAILED")
        self.assertEqual(rg["rules"]["R3_count_specificity"], CS_YES)
        self.assertFalse(rg["predictions"]["Q6"])
        self.assertTrue(rg["predictions"]["Q3"])
        # M0 off HOLD's gain
        rg = regrade(toy_result({"m0": {"g": -0.03}}))
        self.assertEqual(rg["rules"]["pipeline"], "PIPELINE_FAILED")
        self.assertEqual(rg["rules"]["control"], "PIPELINE_FAILED")
        self.assertEqual(rg["rules"]["R2_placement"], "PIPELINE_FAILED")
        self.assertFalse(rg["predictions"]["Q1"])
        self.assertTrue(rg["predictions"]["Q7"])           # -0.06 < -0.03
        self.assertEqual(regrade(toy_result({"m0": {"g": HOLD_GAIN + 4e-5}}))["rules"]
                         ["pipeline"], "PIPELINE_OK")
        self.assertEqual(regrade(toy_result({"m0": {"g": HOLD_GAIN + 6e-5}}))["rules"]
                         ["pipeline"], "PIPELINE_FAILED")
        self.assertEqual(regrade(toy_result({"m0": {"lossless": False}}))["rules"]
                         ["pipeline"], "PIPELINE_FAILED")
        self.assertEqual(regrade(toy_result({"m0": {"k": 100}}))["rules"]["pipeline"],
                         "PIPELINE_FAILED")
        # counts not cell-specific (p = 101/2001)
        r = toy_result({"cs": {"p": 101 / 2001, "label": CS_NO}})
        rg = regrade(r)
        self.assertEqual(rg["rules"]["R3_count_specificity"], CS_NO)
        self.assertFalse(rg["predictions"]["Q2"])
        self.assertEqual(check_result(r), [])
        # M2 gains above M0's
        rg = regrade(toy_result({"M2": {"g": -0.04}}))
        self.assertFalse(rg["predictions"]["Q7"])
        self.assertTrue(rg["predictions"]["Q4"])

    def test_incomplete_and_missing(self):
        r = toy_result(n_rows=7)
        rg = regrade(r)
        self.assertEqual(rg["rules"]["verdicts"], {"M1": "INCOMPLETE", "M2": "INCOMPLETE",
                                                   "M3": "INCOMPLETE"})
        self.assertEqual(rg["n_rows"], {"M1": 3, "M2": 2, "M3": 2})
        self.assertEqual(rg["rules"]["R1_copy_counts"], "INCOMPLETE")
        self.assertEqual(rg["rules"]["R2_placement"], "INCOMPLETE")
        for q in ("Q3", "Q4", "Q5", "Q7"):
            self.assertIsNone(rg["predictions"][q])
        self.assertEqual(rg["n_scored"], 3)
        # .0025 + .0625 + .01 = .075
        self.assertAlmostEqual(rg["brier"], 0.025, places=12)
        self.assertEqual(check_result(r), [])
        r["grading"] = job_grading(rg)
        self.assertEqual(check_meta(r, "aa", "bb"), [])
        self.assertEqual(len(render_md_lines(r, rg)), 36)
        r["status"] = "ok"
        self.assertEqual(check_meta(r, "aa", "bb"), ["status ok but a part did not run"])
        # whale missing: nothing runs
        r = toy_missing()
        rg = regrade(r)
        self.assertEqual(rg["rules"], {
            "pipeline": MISSING, "control": MISSING, "negative_detected": None,
            "R1_copy_counts": MISSING, "R2_placement": MISSING, "R3_count_specificity": MISSING,
            "verdicts": {"M1": "INCOMPLETE", "M2": "INCOMPLETE", "M3": "INCOMPLETE"},
            "detected": {"M1": 0, "M2": 0, "M3": 0},
            "moved_share": {"M1": 0.0, "M2": 0.0, "M3": 0.0},
            "inert": {"M1": True, "M2": True, "M3": True}})
        self.assertEqual(rg["n_scored"], 0)
        self.assertIsNone(rg["brier"])
        self.assertEqual(check_result(r), [])
        r["grading"] = job_grading(rg)
        self.assertEqual(check_meta(r, "aa", "bb"), [])
        r["whale_status"] = "gate_fail"
        self.assertEqual(check_meta(r, "aa", "bb"),
                         ["whale status does not match the job status"])
        r = toy_missing()
        r["permuted"] = toy_result()["permuted"]
        self.assertEqual(check_result(r), ["results without whale data"])

    def test_consistency_catches_errors(self):
        r = toy_result()
        rows = r["permuted"]
        rows[0]["seed"] = 1
        rows[1]["test"]["seed"] = 5
        rows[2]["moved"] = 481
        rows[3]["runs_in_groups"] = 799
        rows[4]["elements"][0] = 1054
        rows[6]["moved"] = 721
        r["count_specificity"]["label"] = CS_NO
        r["m0"]["exact_match"] = not r["m0"]["exact_match"]
        r["describe"][0]["runs"] = 554
        self.assertEqual(sorted(check_result(r)), sorted([
            "M1 0: seed", "M2 0 test: seed", "M3 0: moved", "M1 1: runs in groups",
            "M2 1: elements", "M1 2: moved more than recurring cells allow",
            "count specificity: label", "M0: exact match flag",
            "describe 2010: runs and share"]))
        # order, a nan gain, sizes and bouts
        r = toy_result()
        rows = r["permuted"]
        rows[0], rows[1] = rows[1], rows[0]
        r["neg"]["test"]["per_recording"][0]["gain"] = float("nan")
        r["m0"]["test"]["per_recording"][5]["bouts"] = 12
        r["m0"]["test"]["per_recording"][7]["symbols"] = 9178
        r["describe"][3]["repeated_runs_by_cell_length"]["9"] = 1
        self.assertEqual(sorted(check_result(r)), sorted([
            "permuted rows out of order",
            "negative control: non-finite or missing H or gain, recording 0",
            "M0: bouts, recording 5", "M0: symbols, recording 7",
            "describe 2013: runs by cell length"]))
        # M3 acts only on repeated runs of 2 or more elements: 8 x (100 - 40) = 480
        r = toy_result()
        for d in r["describe"]:
            d["repeated_runs_by_cell_length"] = {"1": 41, "2": 29, "3": 30}
        self.assertEqual(sorted(check_result(r)),
                         sorted("M3 %d: runs in groups" % i for i in range(N_SHUF)))

    def test_helpers(self):
        self.assertTrue(p_ok(1 / 201, 200))
        self.assertTrue(p_ok(101 / 2001, 2000))
        self.assertFalse(p_ok(0.03, 200))
        self.assertFalse(p_ok(1.5, 200))
        self.assertTrue(close(None, None))
        self.assertFalse(close(None, 1.0))
        self.assertEqual(argmin([3.0, 2.5, 2.0, 1.99, 2.1, 2.2]), 3)
        self.assertEqual(argmin([3.0, 2.5, 2.0, 2.0, 2.1, 2.2]), 2)
        self.assertFalse(finite(float("nan")))
        self.assertFalse(finite(True))
        self.assertEqual([perm_seed(k, i) for k, i in (("M1", 0), ("M2", 4), ("M3", 0))],
                         [20262132, 20263172, 20264132])
        self.assertEqual(zstr({"mean_gain": 0.0, "null_mean": 0.0, "null_sd": 0.0}), "n/a")

    def test_formats(self):
        r = toy_result()
        rg = regrade(r)
        self.assertEqual(m0_line(r, rg),
                         "M0, the unpermuted song with HOLD's seed: runs expand back to the song "
                         "exactly: yes; mean held-out gain **-0.0490** bits per element against "
                         "-0.0800 (sd 0.0040) for second-order surrogates (B = 200), p = "
                         "**0.0050**; identical to RESULTS-HOLD.md's gain and p: yes; "
                         "**`PIPELINE_OK`**")
        self.assertEqual(neg_line(r),
                         "Negative control (M3 on one second-order surrogate of the whale): 150 "
                         "of 300 repeated runs changed; mean gain -0.0800 against -0.0800 "
                         "(B = 200), p = 0.5025, label `NOT_DETECTED`")
        self.assertEqual(cs_line(r),
                         "Count specificity (cell and copy count given cell length, over "
                         "repeated runs, summed over years): 50.000 against 20.000 (sd 5.000) "
                         "after M2 permutations (B = 2,000), p = **0.0005**, "
                         "**`COUNTS_CELL_SPECIFIC`**")
        self.assertEqual(year_row(r, 0),
                         "| 2010 | 1,053 | 553 | 100 | 0.5698 | 20 | 90 | 3.00 | 9 | 0.5000 |")
        self.assertEqual(year_row(r, 5),
                         "| 2015 | 14,429 | 13,929 | 100 | 0.0416 | 20 | 90 | 3.00 | 9 | 0.5000 |")
        self.assertEqual(perm_row(r["permuted"][0]),
                         "| M1 | 0 | 20262132 | 400 of 800 | -0.0600 | -0.0800 | +5.00 | 0.0050 | `"
                         + BSO + "` |")
        self.assertEqual(perm_row(r["permuted"][2])[:40],
                         "| M3 | 0 | 20264132 | 240 of 480 | -0.06")
        self.assertEqual(kind_line(rg, "M1"),
                         "M1 (copy counts within cell): detected in 5 of 5 permuted data sets; "
                         "share of repeated runs changed 0.5000; verdict **`SURVIVES`**")
        self.assertEqual(m2_line(r, rg),
                         "Mean held-out gain of the 5 M2 data sets -0.0600 against M0's -0.0490")
        rg2 = regrade(toy_result({"M1": {"moved": 100}}))
        self.assertEqual(kind_line(rg2, "M1"),
                         "M1 (copy counts within cell): detected in 5 of 5 permuted data sets; "
                         "share of repeated runs changed 0.1250 (INERT); verdict **`SURVIVES`**")
        self.assertEqual(pred_end("Q1", True), "| 0.95 | **true** |")
        self.assertEqual(pred_end("Q5", None), "| 0.45 | **not graded** |")

    def test_md_check(self):
        r = toy_result()
        rg = regrade(r)
        lines = render_md_lines(r, rg)
        self.assertIn("Job status: `ok`; whale data status: `ok`", lines)
        self.assertIn("Pipeline: **`PIPELINE_OK`**; control: **`CONTROL_OK`** (negative "
                      "control detected: no)", lines)
        self.assertIn("R1 copy counts: **`COUNTS_NOT_NEEDED`**", lines)
        self.assertIn("R2 placement of repeated phrases: **`PLACEMENT_NOT_NEEDED`**", lines)
        self.assertIn("R3 count specificity: **`COUNTS_CELL_SPECIFIC`**", lines)
        self.assertIn("7 of 7 graded predictions true", lines)
        self.assertIn("Brier score **0.107**", lines)
        self.assertIn("| Q1 | the pipeline check passes (`PIPELINE_OK`) | 0.95 | **true** |",
                      lines)
        # 1 status + M0 + negative + CS + 8 years + 15 rows + 3 kinds + M2 mean + 4 rules
        # + 2 score lines + 7 predictions
        self.assertEqual(len(lines), 44)
        md = "\n".join(lines)
        self.assertEqual(check_md(md, r, rg), [])
        r1 = "R1 copy counts: **`COUNTS_NOT_NEEDED`**"
        self.assertEqual(check_md("\n".join(ln for ln in lines if ln != r1), r, rg), [r1])
        no_q6 = "\n".join(ln for ln in lines if not ln.startswith("| Q6 |"))
        self.assertEqual(check_md(no_q6, r, rg), ["prediction row Q6"])
        # whale missing: 13 lines
        r = toy_missing()
        rg = regrade(r)
        lines = render_md_lines(r, rg)
        self.assertEqual(len(lines), 13)
        self.assertIn("Job status: `whale_missing`; whale data status: `missing`", lines)
        self.assertIn("Pipeline: **`WHALE_DATA_MISSING`**; control: **`WHALE_DATA_MISSING`** "
                      "(negative control detected: not run)", lines)
        self.assertIn("0 of 0 graded predictions true", lines)
        self.assertIn("| Q7 | the mean held-out gain of the five M2 data sets is below M0's | "
                      "0.65 | **not graded** |", lines)


if __name__ == "__main__":
    unittest.main()
