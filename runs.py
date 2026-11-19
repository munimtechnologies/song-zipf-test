# SPDX-License-Identifier: Apache-2.0
# runs.py: is the "language-like" Zipf law of humpback whale song made by the repetition
# of phrase cells? (RUNS-PREREG.md, song-zipf-test). Every within-recording tandem repeat
# (a cell of 1-8 elements sung twice in a row) is collapsed to one copy, and three
# registered tests are run on the 8 years of song of Arnon et al. 2025 (Science 387:649):
#   T1  the Zipf test (TP-cut chunks, mean R^2) of the COLLAPSED song against first- and
#       second-order Markov chains fitted to the collapsed song and generated under the
#       same collapse rule (so the nulls are square-free too);
#   T2  the share of elements removed by collapsing, against second-order Markov
#       surrogates of the original song;
#   T3  how many of each year's ten most frequent TP chunks contain an immediate repeat
#       (x x) or an alternation (x y x), against second-order Markov surrogates.
# Positive control: child-directed English (Brent-Ratner, 6 replicates of CDS-SIZE at
# 2,745 and 5,874 phonemes per recording). Negative control: Markov-2 surrogates of the
# whale years. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
"""Core functions are pure standard-library Python; the pipeline modules (zipfseg.py,
cds_job.py, whale_run.py, fetched at pinned commits by setup_runs.sh) are imported only
inside main(), so the tests run anywhere."""
import argparse
import hashlib
import json
import math
import os
import random
import sys
import time
from collections import defaultdict

VERSION = "runs-1"
LMAX = 8
CAP = 50
ALPHA = 0.05
SEED = 20261120
THETAS = (0.3, 0.5, 0.7)
THETA = 0.5
TOP = 10
N_REC = 8
CDS_DESIGN = ((280, 4), (600, 2))      # CDS-SIZE replicates that Zipf detected 6 of 6
N_NEG = 3
B_T1_WHALE = 1000
B_T1_NEG = 200
B_T1_CDS = 100
B_T23 = 200
B_T23_SMALL = 100
WHALE_ORIGINAL_R2 = 0.9302888665216728  # RESULTS-WHALE.md, theta 0.5
BSOC = "BEYOND_SECOND_ORDER_AFTER_COLLAPSE"
REP = "REPETITION_BEYOND_SECOND_ORDER"
MOT = "MOTIFS_BEYOND_SECOND_ORDER"
NB = "NOT_BEYOND"
PRIORS = {"P1": 0.90, "P2": 0.60, "P3": 0.50, "P4": 0.50, "P5": 0.30, "P6": 0.75,
          "P7": 0.80, "P8": 0.35, "P9": 0.70}
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/main/"
              "RUNS-PREREG.md")


# --------------------------------------------------------------------------
# collapsing tandem repeats
# --------------------------------------------------------------------------
def push(out, s, lmax=LMAX):
    """Append s; then, while the sequence ends in a tandem repeat u u with
    1 <= |u| <= lmax, delete the second copy (shortest period first)."""
    out.append(s)
    while True:
        n = len(out)
        for L in range(1, min(lmax, n // 2) + 1):
            if out[n - L:] == out[n - 2 * L:n - L]:
                del out[n - L:]
                break
        else:
            return out


def collapse(seq, lmax=LMAX):
    """Online tandem-repeat collapse. The output has no square of period <= lmax
    (every prefix of it was checked when its last symbol was appended)."""
    out = []
    for s in seq:
        push(out, s, lmax)
    return out


def collapse_rec(bouts, lmax=LMAX):
    return [collapse(b, lmax) for b in bouts]


def has_square(seq, lmax=LMAX):
    n = len(seq)
    for L in range(1, lmax + 1):
        for i in range(0, n - 2 * L + 1):
            if seq[i:i + L] == seq[i + L:i + 2 * L]:
                return True
    return False


def share_removed(bouts, lmax=LMAX):
    tot = sum(len(b) for b in bouts)
    if tot == 0:
        return 0.0
    return 1.0 - sum(len(collapse(b, lmax)) for b in bouts) / tot


# --------------------------------------------------------------------------
# collapse-consistent Markov nulls
# --------------------------------------------------------------------------
def fit_chain(bouts, k):
    """As zipfseg.markov_recording: start k-grams, successors with multiplicity,
    and the k-grams that have a successor (for reseeding)."""
    succ = defaultdict(list)
    starts = []
    with_succ = []
    for b in bouts:
        b = list(b)
        if len(b) >= k:
            starts.append(tuple(b[:k]))
        for i in range(len(b) - k):
            ctx = tuple(b[i:i + k])
            succ[ctx].append(b[i + k])
            with_succ.append(ctx)
    return succ, starts, with_succ


def collapsed_markov(bouts, k, rng, lmax=LMAX, cap=CAP):
    """Pooled order-k chain fitted to the (collapsed) bouts, generated with the
    online collapse applied, until each bout reaches its own length or cap*n
    symbols have been drawn. Bouts of length <= k are copied unchanged."""
    succ, starts, with_succ = fit_chain(bouts, k)
    out = []
    for b in bouts:
        n = len(b)
        if n <= k or not with_succ:
            out.append(list(b))
            continue
        seq = []
        for s in rng.choice(starts):
            push(seq, s, lmax)
        draws = 0
        while len(seq) < n and draws < cap * n:
            draws += 1
            nxt = succ.get(tuple(seq[-k:])) if len(seq) >= k else None
            if nxt:
                push(seq, rng.choice(nxt), lmax)
            else:
                for s in rng.choice(with_succ):
                    push(seq, s, lmax)
        out.append(seq[:n])
    return out


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


def pval(real, nulls):
    """One-sided empirical p (null >= real) with +1 correction; nan real -> 1."""
    if real != real:
        return 1.0
    return (1 + sum(1 for a in nulls if a >= real)) / (1 + len(nulls))


def cmp(real, nulls):
    v = [a for a in nulls if a == a]
    m = mean(v)
    s = sd(v)
    z = (real - m) / s if (v and s > 0 and real == real) else float("nan")
    return {"real": real, "null_mean": m, "null_sd": s, "z": z,
            "p": pval(real, v), "n_null": len(v)}


def motif(c):
    """True if the chunk contains x x or x y x."""
    return (any(c[i] == c[i + 1] for i in range(len(c) - 1)) or
            any(c[i] == c[i + 2] for i in range(len(c) - 2)))


def top_chunks(inv, top=TOP):
    return [c for c, _ in sorted(inv.items(), key=lambda kv: (-kv[1], kv[0]))[:top]]


def motif_count(recordings, segfn, top=TOP):
    return sum(sum(1 for c in top_chunks(segfn(rec), top) if motif(c)) for rec in recordings)


def t1(recordings, B, seed, r2fn, lmax=LMAX, thetas=THETAS):
    """Zipf test of collapsed song against collapse-consistent order-1/2 chains."""
    real = [r2fn(recordings, th) for th in thetas]
    n_real = sum(len(b) for rec in recordings for b in rec)
    out = {"B": B, "seed": seed, "thetas": list(thetas), "real_r2": real, "nulls": {}}
    for k in (1, 2):
        rng = random.Random(seed * 10 + k)
        vals = [[] for _ in thetas]
        ratios = []
        for _ in range(B):
            fake = [collapsed_markov(rec, k, rng, lmax) for rec in recordings]
            ratios.append(sum(len(b) for rec in fake for b in rec) / n_real if n_real else 1.0)
            for j, th in enumerate(thetas):
                vals[j].append(r2fn(fake, th))
        out["nulls"]["m%dc" % k] = {
            "by_theta": [cmp(real[j], vals[j]) for j in range(len(thetas))],
            "length_ratio_mean": mean(ratios),
            "length_ratio_min": min(ratios) if ratios else float("nan")}
    j = list(thetas).index(THETA)
    p1 = out["nulls"]["m1c"]["by_theta"][j]["p"]
    p2 = out["nulls"]["m2c"]["by_theta"][j]["p"]
    out["p_m1c"] = p1
    out["p_m2c"] = p2
    out["label"] = (BSOC if p2 < ALPHA else
                    ("EXPLAINED_BY_SECOND_ORDER" if p1 < ALPHA else "EXPLAINED_BY_FIRST_ORDER"))
    return out


def t2(recordings, B, seed, surrogate, lmax=LMAX):
    """Mean share of elements removed by collapsing vs order-2 surrogates."""
    per = [share_removed(rec, lmax) for rec in recordings]
    real = mean(per)
    rng = random.Random(seed)
    nulls = [mean([share_removed(surrogate(rec, rng), lmax) for rec in recordings])
             for _ in range(B)]
    c = cmp(real, nulls)
    c.update({"per_set": per, "B": B, "label": REP if c["p"] < ALPHA else NB})
    return c


def t3(recordings, B, seed, surrogate, segfn, top=TOP):
    """Top-chunk repetition motifs vs order-2 surrogates."""
    real = motif_count(recordings, segfn, top)
    rng = random.Random(seed)
    nulls = [motif_count([surrogate(rec, rng) for rec in recordings], segfn, top)
             for _ in range(B)]
    tops = [top_chunks(segfn(rec), top) for rec in recordings]
    c = cmp(real, nulls)
    c.update({"n_top": sum(len(t) for t in tops), "B": B,
              "top_chunks": [[" ".join(str(s) for s in ch) for ch in t] for t in tops],
              "label": MOT if c["p"] < ALPHA else NB})
    return c


def d1(recordings, llfn):
    """Held-out log-likelihood per element, order 2 minus order 1, per set."""
    d = [llfn(rec, 2) - llfn(rec, 1) for rec in recordings]
    n = sum(1 for a in d if a > 0)
    return {"per_set": d, "n_favour_order2": n, "majority": n > len(d) / 2}


def analyse_set(recs, b_t1, b_t23, seed, Z, lmax=LMAX):
    """All registered statistics for one data set (list of recordings of bouts)."""
    def sur(rec, rng):
        return Z.markov_recording(rec, 2, rng)

    def seg(rec):
        return Z.segment_recording(rec, THETA)

    col = [collapse_rec(rec, lmax) for rec in recs]
    out = {"elements": [sum(len(b) for b in rec) for rec in recs],
           "elements_collapsed": [sum(len(b) for b in rec) for rec in col],
           "r2_original": [Z.dataset_r2(recs, th) for th in THETAS],
           "t2": t2(recs, b_t23, seed + 1, sur, lmax),
           "t3": t3(recs, b_t23, seed + 2, sur, seg),
           "d1_original": d1(recs, Z.heldout_ll),
           "d1_collapsed": d1(col, Z.heldout_ll)}
    out["t1"] = t1(col, b_t1, seed + 3, Z.dataset_r2, lmax)
    return out


# --------------------------------------------------------------------------
# grading (RUNS-PREREG.md sections 6 and 7)
# --------------------------------------------------------------------------
def grade(res):
    w = res.get("whale") or {}
    ok = w.get("status") == "ok"
    eng = res.get("english") or []
    neg = res.get("negative") or []
    n_eng = sum(n for _, n in CDS_DESIGN)
    complete = len(eng) == n_eng and len(neg) == N_NEG
    e_bso = sum(1 for r in eng if r["t1"]["label"] == BSOC)
    n_bso = sum(1 for r in neg if r["t1"]["label"] == BSOC)
    if not complete:
        control = "CALIBRATION_INCOMPLETE"
    elif e_bso >= 4 and n_bso <= 1:
        control = "CONTROL_OK"
    else:
        control = "CONTROL_FAILED"
    g = {"P2": (sum(1 for r in eng if r["t2"]["label"] == NB) >= 4)
         if len(eng) == n_eng else None,
         "P6": e_bso >= 4 if len(eng) == n_eng else None,
         "P7": n_bso == 0 if len(neg) == N_NEG else None}
    if ok:
        r2c = w["t1"]["real_r2"][list(THETAS).index(THETA)]
        g["P1"] = w["t2"]["p"] < ALPHA
        g["P3"] = w["t2"]["real"] >= 0.5
        g["P4"] = w["t3"]["p"] < ALPHA
        g["P5"] = w["t1"]["label"] == BSOC
        g["P8"] = bool(w["d1_collapsed"]["majority"])
        g["P9"] = r2c < WHALE_ORIGINAL_R2
        if control != "CONTROL_OK":
            r3 = control
        elif w["t1"]["label"] == BSOC:
            r3 = BSOC
        else:
            r3 = w["t1"]["label"] + ("_POWERED" if w["d1_collapsed"]["majority"]
                                     else "_UNDERPOWERED")
        r1 = w["t2"]["label"]
        r2 = w["t3"]["label"]
    else:
        for k in ("P1", "P3", "P4", "P5", "P8", "P9"):
            g[k] = None
        r1 = r2 = r3 = "WHALE_DATA_MISSING"
    scored = [k for k in sorted(PRIORS) if g.get(k) is not None]
    brier = (sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in scored) / len(scored)
             if scored else None)
    return {"rules": {"R1_repetition": r1, "R2_top_chunk_motifs": r2,
                      "R3_zipf_after_collapse": r3, "control": control,
                      "english_bso": e_bso, "negative_bso": n_bso},
            "predictions": g, "priors": PRIORS, "brier": brier, "n_scored": len(scored)}


# --------------------------------------------------------------------------
# job
# --------------------------------------------------------------------------
def wait_for_registration(max_minutes, fetcher):
    t0 = time.time()
    tries = 0
    last = None
    while True:
        tries += 1
        try:
            blob = fetcher(PREREG_URL)
            if b"RUNS-PREREG" in blob:
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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cds-dir", default="/data/cds")
    ap.add_argument("--whale-dir", default="/data/song/whale")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--wait-minutes", type=float, default=60)
    ap.add_argument("--max-minutes", type=float, default=240)
    a = ap.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import zipfseg as Z
    import cds_job as C
    import whale_run as WR
    os.makedirs(a.out_dir, exist_ok=True)
    out_path = os.path.join(a.out_dir, "runs_results.json")
    out = {"version": VERSION, "python": sys.version.split()[0],
           "code_sha256": {m: sha_file(os.path.join(here, m)) for m in
                           ("runs.py", "zipfseg.py", "cds_job.py", "whale_run.py")
                           if os.path.exists(os.path.join(here, m))},
           "config": {"lmax": LMAX, "cap": CAP, "alpha": ALPHA, "seed": SEED,
                      "thetas": list(THETAS), "theta": THETA, "top": TOP,
                      "b_t1_whale": B_T1_WHALE, "b_t1_neg": B_T1_NEG, "b_t1_cds": B_T1_CDS,
                      "b_t23": B_T23, "b_t23_small": B_T23_SMALL,
                      "cds_design": [list(d) for d in CDS_DESIGN], "n_neg": N_NEG},
           "english": [], "negative": []}

    def save():
        tmp = out_path + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
        os.replace(tmp, out_path)

    reg = wait_for_registration(a.wait_minutes, C.fetch)
    out["registration"] = reg
    if not reg["found"]:
        out["status"] = "not_run_unregistered"
        save()
        print("RUNS-PREREG.md not public; nothing analysed")
        return 4
    t0 = time.time()

    # ---- whale (main test) ----
    w = out["whale"] = {}
    path = WR.find_s2(a.whale_dir)
    years = None
    if path is None:
        w["status"] = "missing"
    else:
        with open(path, encoding="utf-8-sig") as f:
            data, rep = WR.parse_s2(f.read())
        okg, why = WR.gate_a(data, rep)
        w.update({"data_sha256": sha_file(path), "gate_a": {"pass": okg, "reasons": why},
                  "recordings": rep.get("recordings"), "elements_by_year": rep.get("elements")})
        if not okg:
            w["status"] = "gate_fail"
        else:
            w["years"] = sorted(data)
            years = [data[y] for y in sorted(data)]
            w.update(analyse_set(years, B_T1_WHALE, B_T23, SEED, Z))
            w["status"] = "ok"
    save()
    if w.get("status") == "ok":
        print("WHALE removed %.3f (null %.3f, p %.4f) | motifs %d/%d (null %.1f, p %.4f) | "
              "collapsed R2 %s p_m2c %.4f %s | D1c %d/8 (%.0f s)" % (
                  w["t2"]["real"], w["t2"]["null_mean"], w["t2"]["p"], w["t3"]["real"],
                  w["t3"]["n_top"], w["t3"]["null_mean"], w["t3"]["p"],
                  [round(x, 4) for x in w["t1"]["real_r2"]], w["t1"]["p_m2c"],
                  w["t1"]["label"], w["d1_collapsed"]["n_favour_order2"],
                  time.time() - t0), flush=True)
    else:
        print("WHALE status:", w.get("status"), flush=True)

    # ---- negative controls: Markov-2 surrogates of the whale years ----
    if years is not None:
        for i in range(N_NEG):
            if time.time() - t0 > a.max_minutes * 60:
                break
            s = SEED + 100 * (i + 1)
            fake = [Z.markov_recording(rec, 2, random.Random(s * 100 + j))
                    for j, rec in enumerate(years)]
            row = {"i": i, "seed": s}
            row.update(analyse_set(fake, B_T1_NEG, B_T23_SMALL, s, Z))
            out["negative"].append(row)
            save()
            print("NEG %d removed %.3f p %.3f | collapsed p_m2c %.4f %s" % (
                i, row["t2"]["real"], row["t2"]["p"], row["t1"]["p_m2c"],
                row["t1"]["label"]), flush=True)

    # ---- positive control: child-directed English ----
    utts, info = C.load_corpus(a.cds_dir)
    out["corpus"] = info
    if utts is None:
        out["status"] = "cds_gate_fail_or_no_data"
    else:
        out["status"] = "running"
        for u, n_rep in CDS_DESIGN:
            for r in range(n_rep):
                if time.time() - t0 > a.max_minutes * 60:
                    out["status"] = "timeout_partial"
                    break
                recs = [C.to_recording(bl) for bl in C.blocks(utts, r * N_REC * u, N_REC, u)]
                s = SEED + 10000 * r + u
                row = {"u": u, "rep": r, "start_utt": r * N_REC * u,
                       "phonemes_per_recording": mean([sum(len(x) for x in rec)
                                                       for rec in recs])}
                row.update(analyse_set(recs, B_T1_CDS, B_T23_SMALL, s, Z))
                row["seconds_since_start"] = round(time.time() - t0, 1)
                out["english"].append(row)
                save()
                print("CDS u=%d rep=%d removed %.3f p %.3f | collapsed p_m2c %.4f %s (%.0f s)"
                      % (u, r, row["t2"]["real"], row["t2"]["p"], row["t1"]["p_m2c"],
                         row["t1"]["label"], row["seconds_since_start"]), flush=True)
        if out["status"] == "running":
            out["status"] = "ok"
    out["grading"] = grade(out)
    out["seconds"] = round(time.time() - t0, 1)
    save()
    print(json.dumps({"status": out["status"], "grading": out["grading"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
