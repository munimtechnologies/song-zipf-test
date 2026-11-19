# SPDX-License-Identifier: Apache-2.0
# runlen.py: what in humpback song's repetition carries its structure beyond second order?
# (RUNLEN-PREREG.md, song-zipf-test). HOLD found whale song beyond a second-order chain on
# held-out song (gain -0.0490 against -0.0783, p = 0.005); HOLDC found nothing beyond second
# order once the tandem repeats are collapsed, while random repetition of random cells did not
# fool HOLD. So the signal lives in HOW the whale repeats. This job parses every bout into
# runs (a cell of 1-8 elements and how many times it is sung in a row), then runs HOLD,
# unchanged, on three registered permutations of the whale's own runs:
#   M1  copy counts permuted among repeated runs of the SAME cell (keeps which cells are
#       repeated, where, and each cell's count distribution; breaks the link between a count
#       and its place in the song);
#   M2  copy counts permuted among repeated runs of cells of the same LENGTH (also breaks
#       any cell-specific count);
#   M3  repeated cells of 2-8 elements permuted among runs of the same length, counts left in
#       place (keeps the repertoire of repeated phrases; breaks which phrase is repeated where).
# Plus a permutation test of whether copy counts are cell-specific beyond cell length.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
"""Core functions are pure standard-library Python with no project imports; hold.py (4e73d8a),
zipfseg.py (742fd83) and whale_run.py (c9f3d12), fetched and SHA-256-checked by
setup_runlen.sh, are imported only inside main(), so the tests run anywhere."""
import argparse
import hashlib
import json
import math
import os
import random
import sys
import time
import urllib.request
from collections import Counter

VERSION = "runlen-1"
SEED = 20261122
LMAX = 8
ALPHA = 0.05
B = 200
N_SHUF = 5
B_CS = 2000
KINDS = ("M1", "M2", "M3")
DET_MIN = 3        # SURVIVES if detected in at least 3 of 5 permuted data sets
NOT_MAX = 1        # DESTROYED if detected in at most 1 of 5
MIN_MOVED = 0.20   # a permutation that changes fewer than 20% of repeated runs is INERT
HOLD_GAIN = -0.04904373293734671    # results/hold/hold_results.json, whale.real.mean_gain
HOLD_P = 1.0 / 201                  # the same file, whale.real.p (B = 200)
HOLD_SEED = 20261120                # hold.SEED + 1, the seed HOLD used for the whale
TOL = 1e-9
PRIORS = {"Q1": 0.95, "Q2": 0.75, "Q3": 0.70, "Q4": 0.60, "Q5": 0.45, "Q6": 0.90,
          "Q7": 0.65}
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/main/"
              "RUNLEN-PREREG.md")


# --------------------------------------------------------------------------
# runs: a cell and how many times it is sung in a row
# --------------------------------------------------------------------------
def tokenize(seq, lmax=LMAX):
    """Greedy left-to-right parse into runs [cell, copies]. At each position the cell of
    length 1..lmax whose consecutive copies (at least 2) cover the most elements is taken,
    ties going to the shortest cell; a position with no adjacent copy gives a one-element
    cell sung once."""
    seq = list(seq)
    n = len(seq)
    out = []
    i = 0
    while i < n:
        best_l, best_r, best_cov = 1, 1, 1
        for L in range(1, lmax + 1):
            if i + 2 * L > n:
                break
            cell = seq[i:i + L]
            r = 1
            while i + (r + 1) * L <= n and seq[i + r * L:i + (r + 1) * L] == cell:
                r += 1
            if r >= 2 and L * r > best_cov:
                best_l, best_r, best_cov = L, r, L * r
        out.append([tuple(seq[i:i + best_l]), best_r])
        i += best_l * best_r
    return out


def expand(tokens):
    out = []
    for cell, r in tokens:
        out.extend(list(cell) * r)
    return out


def tokenize_rec(rec, lmax=LMAX):
    return [tokenize(b, lmax) for b in rec]


def expand_rec(trec):
    return [expand(t) for t in trec]


def n_sym(recs):
    return [sum(len(b) for b in rec) for rec in recs]


# --------------------------------------------------------------------------
# the three registered permutations (within one recording = one year)
# --------------------------------------------------------------------------
def _groups(trec, keyfn):
    """{key: [(bout, run), ...]} over runs sung at least twice, keys in order of first
    appearance; runs whose key is None are left out."""
    g = {}
    for bi, toks in enumerate(trec):
        for ti, (cell, r) in enumerate(toks):
            if r >= 2:
                k = keyfn(cell)
                if k is not None:
                    g.setdefault(k, []).append((bi, ti))
    return g


def _copy(trec):
    return [[[c, r] for c, r in toks] for toks in trec]


def shuffle_counts(trec, rng, by):
    """M1 (by='cell') or M2 (by='length'): permute the copy counts of repeated runs within
    groups of the same cell or of the same cell length. Returns (runs, n repeated runs in
    the groups, n whose count changed)."""
    keyfn = (lambda c: c) if by == "cell" else (lambda c: len(c))
    new = _copy(trec)
    n = moved = 0
    for idx in _groups(trec, keyfn).values():
        vals = [trec[bi][ti][1] for bi, ti in idx]
        rng.shuffle(vals)
        for (bi, ti), r in zip(idx, vals):
            n += 1
            if r != trec[bi][ti][1]:
                moved += 1
            new[bi][ti][1] = r
    return new, n, moved


def shuffle_cells(trec, rng):
    """M3: permute the cells of repeated runs whose cell has 2 or more elements, within
    groups of the same cell length; every copy count stays where it was. Returns (runs, n
    repeated runs in the groups, n whose cell changed)."""
    new = _copy(trec)
    n = moved = 0
    for idx in _groups(trec, lambda c: len(c) if len(c) >= 2 else None).values():
        vals = [trec[bi][ti][0] for bi, ti in idx]
        rng.shuffle(vals)
        for (bi, ti), c in zip(idx, vals):
            n += 1
            if c != trec[bi][ti][0]:
                moved += 1
            new[bi][ti][0] = c
    return new, n, moved


def permute(trec, kind, rng):
    if kind == "M1":
        return shuffle_counts(trec, rng, "cell")
    if kind == "M2":
        return shuffle_counts(trec, rng, "length")
    if kind == "M3":
        return shuffle_cells(trec, rng)
    raise ValueError(kind)


def permute_set(trecs, kind, seed):
    """One permuted data set (all years) with one Random(seed)."""
    rng = random.Random(seed)
    recs = []
    n = moved = 0
    for t in trecs:
        nt, a, m = permute(t, kind, rng)
        recs.append(expand_rec(nt))
        n += a
        moved += m
    return recs, n, moved


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------
def mean(v):
    return sum(v) / len(v) if v else float("nan")


def sd(v):
    if not v:
        return float("nan")
    m = mean(v)
    return math.sqrt(sum((a - m) ** 2 for a in v) / len(v))


def pval_tol(real, nulls, tol=TOL):
    """One-sided empirical p (null >= real - tol) with +1 correction."""
    return (1 + sum(1 for a in nulls if a >= real - tol)) / (1 + len(nulls))


def entropy(counter):
    n = sum(counter.values())
    if n == 0:
        return 0.0
    return -sum(v / n * math.log2(v / n) for v in counter.values() if v)


def cond_info(pairs):
    """I(cell; copies | cell length) in bits over (cell, copies) pairs, as
    H(copies | length) - H(copies | cell) (a cell fixes its length)."""
    n = len(pairs)
    if n == 0:
        return 0.0
    by_len, by_cell = {}, {}
    for c, r in pairs:
        by_len.setdefault(len(c), Counter())[r] += 1
        by_cell.setdefault(c, Counter())[r] += 1
    hl = sum(sum(v.values()) / n * entropy(v) for v in by_len.values())
    hc = sum(sum(v.values()) / n * entropy(v) for v in by_cell.values())
    return hl - hc


def repeated_pairs(trec):
    return [(c, r) for toks in trec for c, r in toks if r >= 2]


def cs_stat(trecs):
    """Sum over recordings of (repeated runs) x I(cell; copies | length)."""
    tot = 0.0
    for t in trecs:
        p = repeated_pairs(t)
        tot += len(p) * cond_info(p)
    return tot


def count_specificity(trecs, b=B_CS, seed=SEED + 5):
    """Are copy counts cell-specific beyond cell length? cs_stat against the same statistic
    after M2 (counts permuted within recording and cell length), B times."""
    real = cs_stat(trecs)
    rng = random.Random(seed)
    nulls = [cs_stat([shuffle_counts(t, rng, "length")[0] for t in trecs]) for _ in range(b)]
    p = pval_tol(real, nulls)
    return {"real": real, "null_mean": mean(nulls), "null_sd": sd(nulls), "p": p, "B": b,
            "seed": seed, "label": ("COUNTS_CELL_SPECIFIC" if p < ALPHA
                                    else "NO_CELL_SPECIFIC_COUNTS")}


def describe(trec):
    """Descriptive numbers for one recording's runs (not used by any rule)."""
    toks = [t for b in trec for t in b]
    rep = [t for t in toks if t[1] >= 2]
    el = sum(len(c) * r for c, r in toks)
    el_rep = sum(len(c) * r for c, r in rep)
    cells = Counter(c for c, _ in rep)
    by_cell = {}
    for c, r in rep:
        by_cell.setdefault(c, Counter())[r] += 1
    modal = sum(max(v.values()) for v in by_cell.values())
    return {"elements": el, "runs": len(toks), "repeated_runs": len(rep),
            "share_elements_in_repeated_runs": el_rep / el if el else float("nan"),
            "distinct_repeated_cells": len(cells),
            "repeated_runs_of_recurring_cells": sum(v for v in cells.values() if v >= 2),
            "repeated_runs_by_cell_length": {str(k): v for k, v in
                                             sorted(Counter(len(c) for c, _ in rep).items())},
            "mean_copies": mean([r for _, r in rep]),
            "max_copies": max([r for _, r in rep]) if rep else 0,
            "share_at_modal_count": modal / len(rep) if rep else float("nan")}


# --------------------------------------------------------------------------
# grading (RUNLEN-PREREG.md sections 6 and 7)
# --------------------------------------------------------------------------
def det(t):
    return t["p"] < ALPHA


def kind_rows(res, kind):
    return [r for r in (res.get("permuted") or []) if r["kind"] == kind]


def verdict(rows):
    if len(rows) < N_SHUF:
        return "INCOMPLETE"
    d = sum(1 for r in rows if det(r["test"]))
    if d >= DET_MIN:
        return "SURVIVES"
    if d <= NOT_MAX:
        return "DESTROYED"
    return "MIXED"


def moved_share(rows):
    n = sum(r["runs_in_groups"] for r in rows)
    return sum(r["moved"] for r in rows) / n if n else 0.0


def grade(res):
    ok = res.get("whale_status") == "ok"
    m0 = res.get("m0") or {}
    neg = res.get("neg")
    cs = res.get("count_specificity")
    v = {k: verdict(kind_rows(res, k)) for k in KINDS}
    ms = {k: moved_share(kind_rows(res, k)) for k in KINDS}
    inert = {k: ms[k] < MIN_MOVED for k in KINDS}
    nd = {k: sum(1 for r in kind_rows(res, k) if det(r["test"])) for k in KINDS}
    if not ok or "test" not in m0:
        pipeline = "WHALE_DATA_MISSING"
    elif (m0.get("lossless") and det(m0["test"])
          and abs(m0["test"]["mean_gain"] - HOLD_GAIN) < 5e-5):
        pipeline = "PIPELINE_OK"
    else:
        pipeline = "PIPELINE_FAILED"
    neg_det = det(neg["test"]) if neg and "test" in neg else None
    if pipeline != "PIPELINE_OK":
        control = pipeline
    elif neg_det is None:
        control = "CALIBRATION_INCOMPLETE"
    elif neg_det:
        control = "CONTROL_FAILED"
    else:
        control = "CONTROL_OK"
    if control != "CONTROL_OK":
        r1 = r2 = control
    else:
        a, b2 = v["M1"], v["M2"]
        if "INCOMPLETE" in (a, b2):
            r1 = "INCOMPLETE"
        elif inert["M1"]:
            r1 = {"SURVIVES": "COUNTS_NOT_NEEDED", "DESTROYED": "COUNTS_CARRY_IT_M1_INERT",
                  "MIXED": "MIXED"}[b2]
        elif a == "DESTROYED":
            r1 = "CONTEXT_SPECIFIC_COUNTS_CARRY_IT"
        elif a == "SURVIVES" and b2 == "DESTROYED":
            r1 = "CELL_SPECIFIC_COUNTS_CARRY_IT"
        elif a == "SURVIVES" and b2 == "SURVIVES":
            r1 = "COUNTS_NOT_NEEDED"
        else:
            r1 = "MIXED"
        c3 = v["M3"]
        if c3 == "INCOMPLETE":
            r2 = "INCOMPLETE"
        elif inert["M3"]:
            r2 = "M3_INERT"
        else:
            r2 = {"SURVIVES": "PLACEMENT_NOT_NEEDED", "DESTROYED": "PLACEMENT_CARRIES_IT",
                  "MIXED": "MIXED"}[c3]
    r3 = cs["label"] if (ok and cs) else "WHALE_DATA_MISSING"
    g = dict.fromkeys(sorted(PRIORS))
    if ok and "test" in m0:
        g["Q1"] = pipeline == "PIPELINE_OK"
    if ok and cs:
        g["Q2"] = cs["p"] < ALPHA
    for q, k in (("Q3", "M1"), ("Q4", "M2"), ("Q5", "M3")):
        if v[k] != "INCOMPLETE":
            g[q] = v[k] == "SURVIVES"
    if neg_det is not None:
        g["Q6"] = not neg_det
    if "test" in m0 and v["M2"] != "INCOMPLETE":
        g["Q7"] = (mean([r["test"]["mean_gain"] for r in kind_rows(res, "M2")])
                   < m0["test"]["mean_gain"])
    scored = [k for k in sorted(PRIORS) if g[k] is not None]
    brier = (sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in scored) / len(scored)
             if scored else None)
    return {"rules": {"pipeline": pipeline, "control": control, "negative_detected": neg_det,
                      "R1_copy_counts": r1, "R2_placement": r2,
                      "R3_count_specificity": r3, "verdicts": v, "detected": nd,
                      "moved_share": ms, "inert": inert},
            "predictions": g, "priors": dict(PRIORS), "brier": brier,
            "n_scored": len(scored)}


# --------------------------------------------------------------------------
# job
# --------------------------------------------------------------------------
def fetch(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def wait_for_registration(max_minutes, fetcher=fetch):
    t0 = time.time()
    tries = 0
    last = None
    while True:
        tries += 1
        try:
            blob = fetcher(PREREG_URL)
            if b"RUNLEN-PREREG" in blob:
                return {"found": True, "tries": tries,
                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "sha256": hashlib.sha256(blob).hexdigest()}
        except Exception as e:                      # 404 until published
            last = repr(e)[:200]
        if time.time() - t0 > max_minutes * 60:
            return {"found": False, "tries": tries, "last_error": last}
        time.sleep(60)


def sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def perm_seed(kind, i):
    return SEED + 1000 * (KINDS.index(kind) + 1) + 10 * (i + 1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--whale-dir", default="/data/song/whale")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--wait-minutes", type=float, default=60)
    ap.add_argument("--max-minutes", type=float, default=300)
    a = ap.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import hold as H
    import zipfseg as Z
    import whale_run as WR
    os.makedirs(a.out_dir, exist_ok=True)
    out_path = os.path.join(a.out_dir, "runlen_results.json")
    out = {"version": VERSION, "python": sys.version.split()[0],
           "code_sha256": {m: sha_file(os.path.join(here, m)) for m in
                           ("runlen.py", "hold.py", "zipfseg.py", "whale_run.py")
                           if os.path.exists(os.path.join(here, m))},
           "config": {"seed": SEED, "lmax": LMAX, "alpha": ALPHA, "b": B, "n_shuf": N_SHUF,
                      "b_cs": B_CS, "det_min": DET_MIN, "not_max": NOT_MAX,
                      "min_moved": MIN_MOVED, "hold_seed": HOLD_SEED, "kmax": H.K_MAX},
           "permuted": []}

    def save():
        tmp = out_path + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
        os.replace(tmp, out_path)

    reg = wait_for_registration(a.wait_minutes)
    out["registration"] = reg
    if not reg["found"]:
        out["status"] = "not_run_unregistered"
        save()
        print("RUNLEN-PREREG.md not public; nothing analysed")
        return 4
    t0 = time.time()

    def sur2(rec, rng):
        return Z.markov_recording(rec, 2, rng)

    path = WR.find_s2(a.whale_dir)
    if path is None:
        out["whale_status"] = "missing"
        out["status"] = "whale_missing"
        out["grading"] = grade(out)
        save()
        return 0
    with open(path, encoding="utf-8-sig") as f:
        data, rep = WR.parse_s2(f.read())
    okg, why = WR.gate_a(data, rep)
    out["data_sha256"] = sha_file(path)
    out["gate_a"] = {"pass": okg, "reasons": why}
    if not okg:
        out["whale_status"] = "gate_fail"
        out["status"] = "whale_gate_fail"
        out["grading"] = grade(out)
        save()
        return 0
    out["whale_status"] = "ok"
    out["years"] = sorted(data)
    years = [data[y] for y in sorted(data)]
    trecs = [tokenize_rec(rec) for rec in years]
    lossless = all(expand_rec(t) == [list(b) for b in rec] for t, rec in zip(trecs, years))
    out["describe"] = [describe(t) for t in trecs]
    out["elements"] = n_sym(years)

    # ---- count specificity (cheap) ----
    out["count_specificity"] = count_specificity(trecs)
    save()
    cs = out["count_specificity"]
    print("CS real %.3f null %.3f (sd %.3f) p %.4f %s" % (cs["real"], cs["null_mean"],
          cs["null_sd"], cs["p"], cs["label"]), flush=True)

    # ---- M0: HOLD on the unpermuted song, as in RESULTS-HOLD.md ----
    m0 = {"lossless": lossless, "test": H.test_set(years, B, HOLD_SEED, sur2)}
    m0["exact_match"] = (abs(m0["test"]["mean_gain"] - HOLD_GAIN) < 1e-12
                         and abs(m0["test"]["p"] - HOLD_P) < 1e-12)
    out["m0"] = m0
    save()
    print("M0 lossless %s gain %.4f null %.4f p %.4f exact %s (%.0f s)" % (
        lossless, m0["test"]["mean_gain"], m0["test"]["null_mean"], m0["test"]["p"],
        m0["exact_match"], time.time() - t0), flush=True)

    # ---- negative control: M3 applied to one Markov-2 surrogate of the whale ----
    neg_years = H.neg_dataset(years, SEED + 7, sur2)
    nrecs, nn, nm = permute_set([tokenize_rec(r) for r in neg_years], "M3", SEED + 8)
    out["neg"] = {"runs_in_groups": nn, "moved": nm, "elements": n_sym(nrecs),
                  "test": H.test_set(nrecs, B, SEED + 9, sur2)}
    save()
    print("NEG gain %.4f p %.4f (%.0f s)" % (out["neg"]["test"]["mean_gain"],
          out["neg"]["test"]["p"], time.time() - t0), flush=True)

    # ---- the permuted whale, interleaved so a timeout leaves balanced partial results ----
    complete = True
    for i in range(N_SHUF):
        for kind in KINDS:
            if time.time() - t0 > a.max_minutes * 60:
                complete = False
                break
            s = perm_seed(kind, i)
            recs, n, moved = permute_set(trecs, kind, s)
            row = {"kind": kind, "i": i, "seed": s, "runs_in_groups": n, "moved": moved,
                   "elements": n_sym(recs), "test": H.test_set(recs, B, s + 1, sur2),
                   "seconds_since_start": round(time.time() - t0, 1)}
            out["permuted"].append(row)
            save()
            print("%s %d moved %d/%d gain %.4f null %.4f p %.4f (%.0f s)" % (
                kind, i, moved, n, row["test"]["mean_gain"], row["test"]["null_mean"],
                row["test"]["p"], row["seconds_since_start"]), flush=True)
        if not complete:
            break
    out["status"] = "ok" if complete else "timeout_partial"
    out["grading"] = grade(out)
    out["seconds"] = round(time.time() - t0, 1)
    save()
    print(json.dumps({"status": out["status"], "grading": out["grading"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
