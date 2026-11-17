# SPDX-License-Identifier: Apache-2.0
# calib.py: synthetic calibration of the song-zipf test (PREREG-AMENDMENT-2.md).
#
# Question: can the published controls (shuffle, rotation) and our pre-registered
# pooled Markov nulls tell song made of word-like chunks apart from song made by
# plain syllable-transition rules (first- or second-order Markov chains) that
# contain no words at all? Every synthetic dataset is matched in size to the
# Bengalese finch data of Kirby et al. 2026 (30 recordings x 10 bouts, bouts of
# 40-96 syllables, mean ~68 as in the real 20,289 syllables / 299 bouts).
# No real song data are used here.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import json
import math
import os
import random
import sys
import time
from collections import Counter

import zipfseg as Z

VERSION = "calib-1"
MASTER_SEED = 20261117
NULLS_USED = ("shuffle", "markov1_pooled", "markov2_pooled")

# name -> (kind, params). Order is fixed: it sets the seeds.
SCENARIOS = [
    ("markov1_a0.2", "markov1", {"alpha": 0.2}),
    ("markov1_a1.0", "markov1", {"alpha": 1.0}),
    ("markov2_a0.2", "markov2", {"alpha": 0.2}),
    ("words_uniform", "words", {"n_words": 12, "lmin": 3, "lmax": 7, "zipf": False, "noise": 0.0}),
    ("words_zipf", "words", {"n_words": 12, "lmin": 3, "lmax": 7, "zipf": True, "noise": 0.0}),
    ("words_zipf_noise10", "words", {"n_words": 12, "lmin": 3, "lmax": 7, "zipf": True, "noise": 0.1}),
]
SCENARIO_INDEX = {s[0]: i for i, s in enumerate(SCENARIOS)}
SCENARIO_DEF = {s[0]: (s[1], s[2]) for s in SCENARIOS}


# --------------------------------------------------------------------------
# generators
# --------------------------------------------------------------------------
def dirichlet(k, alpha, rng):
    """k weights from a symmetric Dirichlet(alpha); never all zero."""
    g = [rng.gammavariate(alpha, 1.0) for _ in range(k)]
    s = sum(g)
    if not s > 0:
        g = [0.0] * k
        g[rng.randrange(k)] = 1.0
        s = 1.0
    return [x / s for x in g]


def gen_markov1(P, n, rng):
    """One bout of length n from first-order transition rows P[a] (lists)."""
    V = len(P)
    seq = [rng.randrange(V)]
    while len(seq) < n:
        seq.append(rng.choices(range(V), weights=P[seq[-1]])[0])
    return seq[:n]


def gen_markov2(P2, V, n, rng):
    """One bout of length n from second-order rows P2[(a, b)]."""
    seq = [rng.randrange(V), rng.randrange(V)]
    while len(seq) < n:
        seq.append(rng.choices(range(V), weights=P2[(seq[-2], seq[-1])])[0])
    return seq[:n]


def gen_words(lexicon, weights, n, rng, noise=0.0, V=8):
    """One bout of length n: words drawn i.i.d. with the given weights and
    concatenated, truncated to n; then each symbol is replaced by a uniform
    random symbol with probability `noise`."""
    seq = []
    while len(seq) < n:
        seq.extend(rng.choices(lexicon, weights=weights)[0])
    seq = seq[:n]
    if noise > 0:
        seq = [rng.randrange(V) if rng.random() < noise else s for s in seq]
    return seq


def make_lexicon(n_words, lmin, lmax, V, rng):
    """n_words distinct words (tuples) with lengths uniform in [lmin, lmax]."""
    words = []
    seen = set()
    while len(words) < n_words:
        w = tuple(rng.randrange(V) for _ in range(rng.randint(lmin, lmax)))
        if w not in seen:
            seen.add(w)
            words.append(w)
    return words


def make_source(kind, params, V, rng):
    """Draw one recording's source (fresh parameters, like a new bird-day);
    returns a function bout(n, rng) -> list of ints."""
    if kind == "markov1":
        P = [dirichlet(V, params["alpha"], rng) for _ in range(V)]
        return lambda n, r: gen_markov1(P, n, r)
    if kind == "markov2":
        P2 = {(a, b): dirichlet(V, params["alpha"], rng) for a in range(V) for b in range(V)}
        return lambda n, r: gen_markov2(P2, V, n, r)
    if kind == "words":
        lex = make_lexicon(params["n_words"], params["lmin"], params["lmax"], V, rng)
        if params["zipf"]:
            w = [1.0 / (i + 1) for i in range(len(lex))]
        else:
            w = [1.0] * len(lex)
        noise = params["noise"]
        return lambda n, r: gen_words(lex, w, n, r, noise, V)
    raise ValueError(kind)


def make_dataset(scenario, rng, n_rec=30, n_bouts=10, lmin=40, lmax=96, V=8):
    kind, params = SCENARIO_DEF[scenario]
    recs = []
    for _ in range(n_rec):
        src = make_source(kind, params, V, rng)
        recs.append([src(rng.randint(lmin, lmax), rng) for _ in range(n_bouts)])
    return recs


# --------------------------------------------------------------------------
# one replicate
# --------------------------------------------------------------------------
def task_seed(scenario, rep):
    return MASTER_SEED + 1000 * SCENARIO_INDEX[scenario] + rep


def run_task(task):
    """task: dict(scenario, rep, B, n_rec, n_bouts, lmin, lmax, V, theta, deadline)."""
    sc, rep = task["scenario"], task["rep"]
    if time.time() > task["deadline"]:
        return {"scenario": sc, "rep": rep, "skipped": True}
    t0 = time.time()
    seed = task_seed(sc, rep)
    rng = random.Random(seed)
    recs = make_dataset(sc, rng, task["n_rec"], task["n_bouts"], task["lmin"],
                        task["lmax"], task["V"])
    th = task["theta"]
    try:
        res = Z.analyze(recs, thetas=(th,), B=task["B"], seed=seed, nulls=NULLS_USED,
                        rotation=True, heldout=True)
    except ZeroDivisionError as e:   # every null dataset undefined (tiny test sizes only)
        return {"scenario": sc, "rep": rep, "seed": seed, "skipped": True,
                "error": repr(e)}
    row = res["by_theta"][str(th)]
    nulls = {k: {"z": v["z"], "p": v["p"], "null_mean": v["null_mean"],
                 "null_sd": v["null_sd"]} for k, v in row["nulls"].items()}
    ho = res["heldout_ll_order2_minus_order1"]
    return {"scenario": sc, "rep": rep, "seed": seed, "skipped": False,
            "real_r2": row["real_mean_r2"], "cuts_per_bout": row["cuts_per_bout"],
            "n_types_total": row["n_types_total"], "nulls": nulls,
            "label": Z.decision(row),
            "d1_n_favour_order2": ho["n_favour_order2"], "d1_mean": ho["mean"],
            "n_rec": task["n_rec"], "seconds": round(time.time() - t0, 2)}


# --------------------------------------------------------------------------
# aggregation
# --------------------------------------------------------------------------
def _median(v):
    v = sorted(v)
    n = len(v)
    if n == 0:
        return float("nan")
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def _sd(v):
    if len(v) < 2:
        return float("nan")
    m = sum(v) / len(v)
    return math.sqrt(sum((a - m) ** 2 for a in v) / (len(v) - 1))


def aggregate(results, alpha=0.05):
    out = {}
    by = {}
    for r in results:
        if r.get("skipped"):
            continue
        by.setdefault(r["scenario"], []).append(r)
    for sc, rs in by.items():
        r2 = [r["real_r2"] for r in rs]
        agg = {"n_reps": len(rs),
               "real_r2_mean": sum(r2) / len(r2), "real_r2_sd": _sd(r2),
               "real_r2_min": min(r2), "real_r2_max": max(r2),
               "frac_real_r2_ge_0.80": sum(1 for a in r2 if a >= 0.80) / len(rs),
               "cuts_per_bout_mean": sum(r["cuts_per_bout"] for r in rs) / len(rs),
               "nulls": {}}
        for name in rs[0]["nulls"]:
            zs = [r["nulls"][name]["z"] for r in rs if r["nulls"][name]["z"] == r["nulls"][name]["z"]]
            ps = [r["nulls"][name]["p"] for r in rs]
            agg["nulls"][name] = {
                "z_mean": sum(zs) / len(zs) if zs else float("nan"),
                "z_median": _median(zs),
                "frac_p_lt_alpha": sum(1 for p in ps if p < alpha) / len(rs),
                "null_r2_mean": sum(r["nulls"][name]["null_mean"] for r in rs) / len(rs)}
        both = [r for r in rs if r["nulls"]["shuffle"]["p"] < alpha and r["nulls"]["rotate"]["p"] < alpha]
        agg["frac_pass_published_controls"] = len(both) / len(rs)
        labels = Counter(r["label"] for r in rs)
        agg["labels"] = dict(labels)
        agg["frac_beyond_second_order"] = labels.get("BEYOND_SECOND_ORDER", 0) / len(rs)
        agg["d1_n_favour_order2_mean"] = sum(r["d1_n_favour_order2"] for r in rs) / len(rs)
        out[sc] = agg
    return out


def grade(agg):
    """Pre-registered calibration predictions C1-C7 and rules R1-R3
    (PREREG-AMENDMENT-2.md). Missing scenarios grade as None."""
    def g(sc, f):
        return f(agg[sc]) if sc in agg else None
    preds = {
        "C1_markov1_a0.2_mean_r2_ge_0.80": g("markov1_a0.2", lambda a: a["real_r2_mean"] >= 0.80),
        "C2_markov1_a0.2_pass_published_controls_ge_0.80": g(
            "markov1_a0.2", lambda a: a["frac_pass_published_controls"] >= 0.80),
        "C3_markov1_a0.2_markov1_null_rejects_le_0.15": g(
            "markov1_a0.2", lambda a: a["nulls"]["markov1_pooled"]["frac_p_lt_alpha"] <= 0.15),
        "C4_markov2_a0.2_beyond_second_order_le_0.15": g(
            "markov2_a0.2", lambda a: a["frac_beyond_second_order"] <= 0.15),
        "C5_words_zipf_beyond_second_order_ge_0.50": g(
            "words_zipf", lambda a: a["frac_beyond_second_order"] >= 0.50),
        "C6_words_uniform_mean_r2_ge_0.80": g("words_uniform", lambda a: a["real_r2_mean"] >= 0.80),
        "C7_words_zipf_noise10_beyond_second_order_ge_0.50": g(
            "words_zipf_noise10", lambda a: a["frac_beyond_second_order"] >= 0.50),
    }
    rules = {
        "R1_size_caveat_on_beyond_second_order": (
            None if preds["C4_markov2_a0.2_beyond_second_order_le_0.15"] is None
            else not preds["C4_markov2_a0.2_beyond_second_order_le_0.15"]),
        "R2_low_power_relabel_explained_as_not_distinguishable": (
            None if preds["C5_words_zipf_beyond_second_order_ge_0.50"] is None
            else not preds["C5_words_zipf_beyond_second_order_ge_0.50"]),
        "R3_published_controls_do_not_separate_words_from_first_order_rules": (
            None if "markov1_a0.2" not in agg else
            (agg["markov1_a0.2"]["frac_pass_published_controls"] >= 0.80
             and agg["markov1_a0.2"]["real_r2_mean"] >= 0.80)),
    }
    return {"predictions": preds, "rules": rules}


# --------------------------------------------------------------------------
def build_tasks(reps, B, n_rec, n_bouts, lmin, lmax, V, theta, deadline, scenarios=None):
    names = scenarios or [s[0] for s in SCENARIOS]
    # rep-major order so that a time-out still leaves every scenario covered
    return [dict(scenario=sc, rep=rep, B=B, n_rec=n_rec, n_bouts=n_bouts, lmin=lmin,
                 lmax=lmax, V=V, theta=theta, deadline=deadline)
            for rep in range(reps) for sc in names]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--max-minutes", type=float, default=140)
    ap.add_argument("--n-rec", type=int, default=30)
    ap.add_argument("--n-bouts", type=int, default=10)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    deadline = t0 + 60 * a.max_minutes
    tasks = build_tasks(a.reps, a.B, a.n_rec, a.n_bouts, 40, 96, 8, 0.5, deadline)
    jl = os.path.join(a.out_dir, "calib_tasks.jsonl")
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
    out = {"version": VERSION, "python": sys.version.split()[0],
           "config": {"reps": a.reps, "B": a.B, "n_rec": a.n_rec, "n_bouts": a.n_bouts,
                      "bout_len": [40, 96], "alphabet": 8, "theta": 0.5,
                      "nulls": list(NULLS_USED) + ["rotate"],
                      "scenarios": {s[0]: {"kind": s[1], **s[2]} for s in SCENARIOS}},
           "n_tasks": len(tasks), "n_skipped": sum(1 for r in results if r.get("skipped")),
           "elapsed_s": round(time.time() - t0, 1),
           "aggregate": agg, "grading": grade(agg),
           "published_finch_reference": {"real_r2_0.5": 0.89, "z_shuffle": 17.05,
                                         "z_rotate": 15.69, "z_bigram": 6.77}}
    tmp = os.path.join(a.out_dir, "calib_results.json.%d.part" % os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    os.replace(tmp, os.path.join(a.out_dir, "calib_results.json"))
    print(json.dumps({"aggregate": agg, "grading": out["grading"],
                      "n_skipped": out["n_skipped"], "elapsed_s": out["elapsed_s"]}, indent=1))


if __name__ == "__main__":
    main()
