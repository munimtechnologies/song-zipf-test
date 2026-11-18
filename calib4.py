# SPDX-License-Identifier: Apache-2.0
# calib4.py: fourth synthetic calibration of the song-zipf test, for the WHALE paper's
# law-of-brevity statistic exactly as its text defines it. Registered in CALIB-4-PREREG.md
# before this code was run.
#
# Arnon et al. 2025 (Science 387:649), Fig. 3A: "Each point in 3A is one sub-sequence ...
# the frequency distribution of all sub-sequences discovered by our segmentation method
# across the entire data set plotted by length". R^2 = 0.62 between length and log
# frequency; shuffled baseline z = 37.57, rotated baseline z = 13.92 (1000 each).
# Segmentation is run per year on ONE long sequence per year ("We created one file
# containing all the recordings from a given 'year'"), cutting ratio 0.5.
#
# Question: at that size and with that statistic, does song with NO words (first- and
# second-order syllable chains) pass the two published brevity controls? What does the
# pipeline report for word sources with no brevity and with REVERSED brevity?
# Primary statistic ("pool"): chunk counts summed over the 8 years, one point per chunk
# type. Alternate ("year"): one point per (year, type). Code S1 decides which one matches
# the paper; both are computed and graded here.
# Uses zipfseg.py and calib.py from munimtechnologies/song-zipf-test unchanged.
# No real song data are used.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import hashlib
import json
import math
import os
import random
import sys
import time
from collections import Counter

import calib as C
import zipfseg as Z

VERSION = "calib-4"
MASTER_SEED = 20261120
THETA = 0.5
ALPHA = 0.05
N_YEARS = 8
LMIN, LMAX = 5000, 8000          # elements per year (paper: ~1,562 cuts per year)
KEYS = ("pool", "year")
NULLS_USED = ("shuffle", "markov1_pooled", "markov2_pooled")
_LEX = {"n_words": 12, "lmin": 3, "lmax": 7}
# (name, alphabet V, kind, params). Order is fixed: it sets the seeds.
SCENARIOS = [
    ("W_markov1_a0.2_V12", 12, "markov1", {"alpha": 0.2}),
    ("W_markov1_a0.1_V24", 24, "markov1", {"alpha": 0.1}),
    ("W_markov2_a0.2_V12", 12, "markov2", {"alpha": 0.2}),
    ("W_words_uniform_V12", 12, "words", dict(_LEX, weights="uniform")),
    ("W_words_brevity_V12", 12, "words", dict(_LEX, weights="brevity")),
    ("W_words_antibrevity_V12", 12, "words", dict(_LEX, weights="antibrevity")),
]
SCENARIO_INDEX = {s[0]: i for i, s in enumerate(SCENARIOS)}
SCENARIO_DEF = {s[0]: s[1:] for s in SCENARIOS}

PRIORS = {"Q1": 0.50, "Q2": 0.50, "Q3": 0.50, "Q4": 0.35, "Q5": 0.30, "Q6": 0.85,
          "Q7": 0.50, "Q8": 0.30, "Q9": 0.25, "Q10": 0.80, "Q11": 0.45}
PUBLISHED = {"r2": 0.62, "z_shuffle": 37.57, "z_rotate": 13.92, "B": 1000}


# --------------------------------------------------------------------------
# generators
# --------------------------------------------------------------------------
def word_weights(lexicon, mode):
    """uniform: equal; brevity: 2^-(L-3); antibrevity: 2^(L-3)."""
    if mode == "uniform":
        return [1.0] * len(lexicon)
    if mode == "brevity":
        return [2.0 ** -(len(w) - 3) for w in lexicon]
    if mode == "antibrevity":
        return [2.0 ** (len(w) - 3) for w in lexicon]
    raise ValueError(mode)


def gen_words_units(lexicon, weights, n, rng):
    """One sequence of length n made of i.i.d. words; returns (sequence, complete words).
    The last word is dropped from the unit list when the sequence truncates it."""
    seq, units = [], []
    while len(seq) < n:
        w = rng.choices(lexicon, weights=weights)[0]
        seq.extend(w)
        units.append(w)
    if len(seq) > n:
        units.pop()
    return seq[:n], units


def make_dataset(scenario, rng, n_years=None, lmin=LMIN, lmax=LMAX):
    """(years, true-unit inventories). Each year is a recording with ONE sequence
    (a list holding one list of ints) and a fresh source, as song changes every year.
    Unit inventories (Counter of true words per year) for word sources, else None."""
    V, kind, params = SCENARIO_DEF[scenario]
    ny = N_YEARS if n_years is None else n_years
    recs, units = [], []
    for _ in range(ny):
        n = rng.randint(lmin, lmax)
        if kind == "words":
            lex = C.make_lexicon(params["n_words"], params["lmin"], params["lmax"], V, rng)
            seq, us = gen_words_units(lex, word_weights(lex, params["weights"]), n, rng)
            recs.append([seq])
            units.append(Counter(us))
        else:
            src = C.make_source(kind, params, V, rng)
            recs.append([src(n, rng)])
    return recs, (units if kind == "words" else None)


# --------------------------------------------------------------------------
# brevity statistics
# --------------------------------------------------------------------------
NAN = float("nan")


def ols_points(points):
    """R^2 and OLS slope of y on x. nan, nan when < 3 points or no variation."""
    n = len(points)
    if n < 3:
        return NAN, NAN
    mx = sum(p[0] for p in points) / n
    my = sum(p[1] for p in points) / n
    sxx = sum((p[0] - mx) ** 2 for p in points)
    syy = sum((p[1] - my) ** 2 for p in points)
    if sxx == 0 or syy == 0:
        return NAN, NAN
    sxy = sum((p[0] - mx) * (p[1] - my) for p in points)
    return sxy * sxy / (sxx * syy), sxy / sxx


def brevity_pooled(invs):
    """One point per chunk type, counts summed over years: (length, log10 count)."""
    pool = Counter()
    for inv in invs:
        pool.update(inv)
    return ols_points([(len(k), math.log10(v)) for k, v in pool.items() if v > 0])


def brevity_by_year(invs):
    """One point per (year, chunk type): (length, log10 count in that year)."""
    return ols_points([(len(k), math.log10(v)) for inv in invs for k, v in inv.items()
                       if v > 0])


def stats(invs):
    r2p, slp = brevity_pooled(invs)
    r2y, sly = brevity_by_year(invs)
    return {"r2_pool": r2p, "slope_pool": slp, "r2_year": r2y, "slope_year": sly}


def _cmp(real, vals):
    """z (population SD, as Code S1) and one-sided p (null >= real, +1 correction)."""
    v = [a for a in vals if a == a]
    if len(v) < 2 or real != real:
        return {"z": NAN, "p": NAN, "null_mean": NAN, "null_sd": NAN, "n_null": len(v)}
    m = sum(v) / len(v)
    sd = math.sqrt(sum((a - m) ** 2 for a in v) / len(v))
    z = (real - m) / sd if sd > 0 else NAN
    p = (1 + sum(1 for a in v if a >= real)) / (1 + len(v))
    return {"z": z, "p": p, "null_mean": m, "null_sd": sd, "n_null": len(v)}


def _null_summary(real, st):
    out = {"r2_" + k: _cmp(real["r2_" + k], [s["r2_" + k] for s in st]) for k in KEYS}
    sl = [s["slope_pool"] for s in st if s["slope_pool"] == s["slope_pool"]]
    out["slope_pool_null_mean"] = sum(sl) / len(sl) if sl else NAN
    out["frac_null_slope_pool_neg"] = (sum(1 for a in sl if a < 0) / len(sl)) if sl else NAN
    return out


def _inv(segs_by_bout):
    inv = Counter()
    for segs in segs_by_bout:
        for s in segs:
            inv[s] += 1
    return inv


# --------------------------------------------------------------------------
# one replicate
# --------------------------------------------------------------------------
def task_seed(scenario, rep):
    return MASTER_SEED + 1000 * SCENARIO_INDEX[scenario] + rep


def run_task(task):
    """task: dict(scenario, rep, B, deadline, n_years, lmin, lmax)."""
    sc, rep = task["scenario"], task["rep"]
    if time.time() > task["deadline"]:
        return {"scenario": sc, "rep": rep, "skipped": True}
    t0 = time.time()
    seed = task_seed(sc, rep)
    rng = random.Random(seed)
    recs, units = make_dataset(sc, rng, task.get("n_years"), task.get("lmin", LMIN),
                               task.get("lmax", LMAX))
    segrecs = [Z.segment_recording_bouts(r, THETA) for r in recs]
    invs = [_inv(s) for s in segrecs]
    real = stats(invs)
    B = task["B"]
    nulls = {}
    for ni, name in enumerate(NULLS_USED):
        nrng = random.Random(seed * 1000 + ni * 10 + 7)
        st = []
        for _ in range(B):
            st.append(stats([Z.segment_recording(Z.NULLS[name](rec, nrng), THETA)
                             for rec in recs]))
        nulls[name] = _null_summary(real, st)
    rrng = random.Random(seed * 1000 + 907)
    st = []
    for _ in range(B):
        st.append(stats([_inv([Z.rotate_bout_segments(segs, rrng) for segs in sr])
                         for sr in segrecs]))
    nulls["rotate"] = _null_summary(real, st)
    src = None
    if units is not None:
        r2s, sls = brevity_pooled(units)
        src = {"r2_pool": r2s, "slope_pool": sls}
    pool = Counter()
    for inv in invs:
        pool.update(inv)
    n_chunks = sum(pool.values())
    return {"scenario": sc, "rep": rep, "seed": seed, "skipped": False,
            "real": real, "source": src, "nulls": nulls, "n_years": len(recs),
            "n_symbols": sum(len(b) for r in recs for b in r), "n_chunks": n_chunks,
            "n_types_pool": len(pool),
            "mean_chunk_len": (sum(len(k) * v for k, v in pool.items()) / n_chunks
                               if n_chunks else NAN),
            "seconds": round(time.time() - t0, 2)}


# --------------------------------------------------------------------------
# aggregation and grading
# --------------------------------------------------------------------------
def _mean(v):
    v = [a for a in v if a == a]
    return sum(v) / len(v) if v else NAN


def whale_pass(r, key="pool"):
    """The whale paper's brevity controls passed: brevity direction (slope < 0) and an
    R^2 above both the shuffled and the rotated baselines (one-sided p < 0.05)."""
    return (r["real"]["slope_" + key] < 0
            and r["nulls"]["shuffle"]["r2_" + key]["p"] < ALPHA
            and r["nulls"]["rotate"]["r2_" + key]["p"] < ALPHA)


def aggregate(results):
    by = {}
    for r in results:
        if not r.get("skipped"):
            by.setdefault(r["scenario"], []).append(r)
    out = {}
    for sc, rs in by.items():
        n = len(rs)
        a = {"n_reps": n,
             "n_types_pool_mean": _mean([r.get("n_types_pool", NAN) for r in rs]),
             "mean_chunk_len": _mean([r.get("mean_chunk_len", NAN) for r in rs]),
             "nulls": {}}
        for k in KEYS:
            a["r2_%s_mean" % k] = _mean([r["real"]["r2_" + k] for r in rs])
            a["slope_%s_mean" % k] = _mean([r["real"]["slope_" + k] for r in rs])
            a["frac_slope_%s_neg" % k] = sum(1 for r in rs if r["real"]["slope_" + k] < 0) / n
            a["frac_pass_%s" % k] = sum(1 for r in rs if whale_pass(r, k)) / n
        for name in rs[0]["nulls"]:
            d = {}
            for k in KEYS:
                ns = [r["nulls"][name]["r2_" + k] for r in rs]
                d["frac_p_%s_lt_alpha" % k] = sum(1 for x in ns if x["p"] < ALPHA) / n
                d["z_%s_mean" % k] = _mean([x["z"] for x in ns])
                d["null_r2_%s_mean" % k] = _mean([x["null_mean"] for x in ns])
            d["frac_null_slope_pool_neg_mean"] = _mean(
                [r["nulls"][name]["frac_null_slope_pool_neg"] for r in rs])
            a["nulls"][name] = d
        srcs = [r["source"] for r in rs if r.get("source")]
        if srcs:
            a["source_slope_pool_mean"] = _mean([s["slope_pool"] for s in srcs])
            a["frac_source_slope_pos"] = sum(1 for s in srcs if s["slope_pool"] > 0) / len(srcs)
            a["frac_source_slope_neg"] = sum(1 for s in srcs if s["slope_pool"] < 0) / len(srcs)
        out[sc] = a
    return out


def grade(agg, key="pool"):
    """Registered predictions Q1-Q11 and rules BW1-BW4 (CALIB-4-PREREG.md) on statistic
    `key` ("pool" is primary). A scenario missing from agg grades as None."""
    def g(sc, f):
        return f(agg[sc]) if sc in agg else None
    m1, m1b, m2 = "W_markov1_a0.2_V12", "W_markov1_a0.1_V24", "W_markov2_a0.2_V12"
    wb, wu, wa = "W_words_brevity_V12", "W_words_uniform_V12", "W_words_antibrevity_V12"
    fp = "frac_pass_" + key
    preds = {
        "Q1": g(m1, lambda a: a[fp] >= 0.80),
        "Q2": g(m1b, lambda a: a[fp] >= 0.80),
        "Q3": g(m2, lambda a: a[fp] >= 0.80),
        "Q4": g(m1, lambda a: a["r2_%s_mean" % key] >= PUBLISHED["r2"]),
        "Q5": g(m1, lambda a: a["nulls"]["shuffle"]["z_%s_mean" % key] >= 10.0),
        "Q6": g(wb, lambda a: a[fp] >= 0.90),
        "Q7": g(wu, lambda a: a[fp] >= 0.50),
        "Q8": g(wa, lambda a: a["frac_slope_%s_neg" % key] >= 0.50),
        "Q9": g(wa, lambda a: a[fp] >= 0.50),
        "Q10": g(m1, lambda a: a["nulls"]["markov1_pooled"]["frac_p_%s_lt_alpha" % key]
                 <= 0.15),
        "Q11": g(wb, lambda a: a["nulls"]["markov2_pooled"]["frac_p_%s_lt_alpha" % key]
                 >= 0.50),
    }
    p = preds
    sane = {}
    if wb in agg:
        sane["words_brevity_source_negative"] = agg[wb].get("frac_source_slope_neg", 0.0) == 1.0
    if wa in agg:
        sane["words_antibrevity_source_positive"] = (
            agg[wa].get("frac_source_slope_pos", 0.0) == 1.0)
    wordless = [(sc, p[q]) for sc, q in ((m1, "Q1"), (m1b, "Q2"), (m2, "Q3"))]
    graded_wl = [(sc, v) for sc, v in wordless if v is not None]
    if not graded_wl:
        bw1, bw1_which = None, []
    elif any(v for _, v in graded_wl):
        bw1 = "WORDLESS_SONG_PASSES_WHALE_BREVITY_CONTROLS"
        bw1_which = [sc for sc, v in graded_wl if v]
    else:
        bw1, bw1_which = "WHALE_BREVITY_CONTROLS_REJECT_WORDLESS_SONG", []
    rules = {
        "BW1_wordless_song": bw1,
        "BW1_scenarios": bw1_which,
        "BW2_brevity_reported_for_reversed_units": (
            None if (p["Q8"] is None or p["Q9"] is None)
            else bool(p["Q8"] and p["Q9"] and sane.get("words_antibrevity_source_positive"))),
        "BW3_markov1_null_calibrated": None if p["Q10"] is None else bool(p["Q10"]),
        "BW4_controls_informative": (
            None if any(p[q] is None for q in ("Q1", "Q2", "Q3", "Q6", "Q9"))
            else bool(not p["Q1"] and not p["Q2"] and not p["Q3"] and p["Q6"]
                      and not p["Q9"] and sane.get("words_brevity_source_negative"))),
        "sanity": sane,
    }
    graded = [k for k, v in preds.items() if v is not None]
    brier = (sum((PRIORS[k] - (1.0 if preds[k] else 0.0)) ** 2 for k in graded) / len(graded)
             if graded else None)
    return {"key": key, "predictions": preds, "rules": rules, "priors": PRIORS,
            "brier": brier}


def build_tasks(reps, B, deadline, scenarios=None, n_years=None, lmin=LMIN, lmax=LMAX):
    names = scenarios or [s[0] for s in SCENARIOS]
    # rep-major order so that a time-out still leaves every scenario covered
    return [dict(scenario=sc, rep=rep, B=B, deadline=deadline, n_years=n_years,
                 lmin=lmin, lmax=lmax)
            for rep in range(reps) for sc in names]


def _sha256(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--max-minutes", type=float, default=170)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    deadline = t0 + 60 * a.max_minutes
    tasks = build_tasks(a.reps, a.B, deadline)
    jl = os.path.join(a.out_dir, "calib4_tasks.jsonl")
    results = []
    with open(jl, "w", encoding="utf-8") as f:
        if a.procs > 1:
            from multiprocessing import Pool
            with Pool(a.procs) as pool:
                for r in pool.imap_unordered(run_task, tasks):
                    results.append(r)
                    f.write(json.dumps(r) + "\n")
                    f.flush()
        else:
            for t in tasks:
                r = run_task(t)
                results.append(r)
                f.write(json.dumps(r) + "\n")
                f.flush()
    agg = aggregate(results)
    here = os.path.dirname(os.path.abspath(__file__))
    out = {"version": VERSION, "python": sys.version.split()[0],
           "code_sha256": {fn: _sha256(os.path.join(here, fn))
                           for fn in ("zipfseg.py", "calib.py", "calib4.py")},
           "config": {"reps": a.reps, "B": a.B, "theta": THETA, "alpha": ALPHA,
                      "n_years": N_YEARS, "year_len": [LMIN, LMAX],
                      "nulls": list(NULLS_USED) + ["rotate"],
                      "scenarios": {s[0]: {"V": s[1], "kind": s[2], **s[3]}
                                    for s in SCENARIOS}},
           "n_tasks": len(tasks), "n_skipped": sum(1 for r in results if r.get("skipped")),
           "elapsed_s": round(time.time() - t0, 1),
           "aggregate": agg,
           "grading": grade(agg, "pool"),
           "grading_alternate_year": grade(agg, "year"),
           "published_reference": {"whale_arnon2025_brevity": PUBLISHED}}
    tmp = os.path.join(a.out_dir, "calib4_results.json.%d.part" % os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    os.replace(tmp, os.path.join(a.out_dir, "calib4_results.json"))
    print(json.dumps({"aggregate": agg, "grading": out["grading"],
                      "grading_alternate_year": out["grading_alternate_year"],
                      "n_skipped": out["n_skipped"], "elapsed_s": out["elapsed_s"]},
                     indent=1))


if __name__ == "__main__":
    main()
