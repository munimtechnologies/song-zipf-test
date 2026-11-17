# SPDX-License-Identifier: Apache-2.0
# calib2.py: second synthetic calibration of the song-zipf test
# (CALIB-2-PREREG.md, registered 2026-11-17 before this code was run).
#
# Questions:
#  (1) At the size of the humpback whale data of Arnon et al. 2025 (8 years, one
#      pooled transition table per year, about 1,500 cuts per year), do song
#      sequences made by first-order syllable rules with NO words pass the two
#      controls that paper used (shuffle, rotation), and how Zipfian do they look?
#  (2) Does the finch paper's extra control (within-bout bigram resampling, Kirby
#      et al. 2026) keep its size at whale scale?
#  (3) How fast does our second-order test lose power when word-like song is
#      degraded by syllable noise (finch size: 2% and 5%; calib-1 had 0% and 10%)?
# Uses zipfseg.py and calib.py from munimtechnologies/song-zipf-test unchanged.
# No real song data are used.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import hashlib
import json
import os
import random
import sys
import time

import calib as C
import zipfseg as Z

VERSION = "calib-2"
MASTER_SEED = 20261118
NULLS_USED = ("shuffle", "bigram_within", "markov1_pooled", "markov2_pooled")
ALPHA = 0.05

# Size presets. WHALE: 8 "recordings" (= years, TPs pooled within a year), each with
# 6 concatenated sequences of 700-1500 elements (mean 1,100; about 6,600 per year).
# FINCH: as calib-1 (30 bird-days x 10 bouts of 40-96 syllables).
SIZES = {
    "whale": {"n_rec": 8, "n_bouts": 6, "lmin": 700, "lmax": 1500},
    "finch": {"n_rec": 30, "n_bouts": 10, "lmin": 40, "lmax": 96},
}

_W = {"n_words": 12, "lmin": 3, "lmax": 7, "zipf": True}
# (name, size, alphabet V, kind, params). Order is fixed: it sets the seeds.
SCENARIOS = [
    ("W_markov1_a0.2_V12", "whale", 12, "markov1", {"alpha": 0.2}),
    ("W_markov1_a0.1_V24", "whale", 24, "markov1", {"alpha": 0.1}),
    ("W_markov2_a0.2_V12", "whale", 12, "markov2", {"alpha": 0.2}),
    ("W_words_zipf_V12", "whale", 12, "words", dict(_W, noise=0.0)),
    ("W_words_zipf_noise10_V12", "whale", 12, "words", dict(_W, noise=0.10)),
    ("F_words_zipf_noise02", "finch", 8, "words", dict(_W, noise=0.02)),
    ("F_words_zipf_noise05", "finch", 8, "words", dict(_W, noise=0.05)),
]
SCENARIO_INDEX = {s[0]: i for i, s in enumerate(SCENARIOS)}
SCENARIO_DEF = {s[0]: s[1:] for s in SCENARIOS}

# Registered predictions: id -> (scenario, description, prior). Graded in grade().
PRIORS = {"K1": 0.80, "K2": 0.55, "K3": 0.45, "K4": 0.80, "K5": 0.75,
          "K6": 0.80, "K7": 0.50, "K8": 0.65, "K9": 0.40, "K10": 0.70}


def make_dataset(scenario, rng, n_rec=None):
    """List of recordings; each recording is a list of bouts (lists of ints).
    Every recording gets a fresh source (new year / bird-day)."""
    size, V, kind, params = SCENARIO_DEF[scenario]
    s = SIZES[size]
    nr = s["n_rec"] if n_rec is None else n_rec
    recs = []
    for _ in range(nr):
        src = C.make_source(kind, params, V, rng)
        recs.append([src(rng.randint(s["lmin"], s["lmax"]), rng) for _ in range(s["n_bouts"])])
    return recs


def task_seed(scenario, rep):
    return MASTER_SEED + 1000 * SCENARIO_INDEX[scenario] + rep


def run_task(task):
    """task: dict(scenario, rep, B, theta, deadline, n_rec (None = preset))."""
    sc, rep = task["scenario"], task["rep"]
    if time.time() > task["deadline"]:
        return {"scenario": sc, "rep": rep, "skipped": True}
    t0 = time.time()
    seed = task_seed(sc, rep)
    rng = random.Random(seed)
    recs = make_dataset(sc, rng, task.get("n_rec"))
    th = task["theta"]
    try:
        res = Z.analyze(recs, thetas=(th,), B=task["B"], seed=seed, nulls=NULLS_USED,
                        rotation=True, heldout=True)
    except ZeroDivisionError as e:
        return {"scenario": sc, "rep": rep, "seed": seed, "skipped": True, "error": repr(e)}
    row = res["by_theta"][str(th)]
    nulls = {k: {"z": v["z"], "p": v["p"], "null_mean": v["null_mean"],
                 "null_sd": v["null_sd"]} for k, v in row["nulls"].items()}
    ho = res["heldout_ll_order2_minus_order1"]
    n_sym = sum(len(b) for r in recs for b in r)
    return {"scenario": sc, "rep": rep, "seed": seed, "skipped": False,
            "real_r2": row["real_mean_r2"], "cuts_per_bout": row["cuts_per_bout"],
            "n_symbols": n_sym, "n_types_total": row["n_types_total"], "nulls": nulls,
            "label": Z.decision(row),
            "d1_n_favour_order2": ho["n_favour_order2"], "d1_mean": ho["mean"],
            "n_rec": len(recs), "seconds": round(time.time() - t0, 2)}


def aggregate(results):
    """calib.aggregate plus the calib-2 extras."""
    agg = C.aggregate(results, alpha=ALPHA)
    by = {}
    for r in results:
        if not r.get("skipped"):
            by.setdefault(r["scenario"], []).append(r)
    for sc, rs in by.items():
        n = len(rs)
        a = agg[sc]
        a["frac_pass_finch_controls"] = sum(
            1 for r in rs if all(r["nulls"][k]["p"] < ALPHA
                                 for k in ("shuffle", "rotate", "bigram_within"))) / n
        a["frac_real_r2_ge_0.93"] = sum(1 for r in rs if r["real_r2"] >= 0.93) / n
        a["cuts_per_recording_mean"] = sum(
            r["cuts_per_bout"] * SIZES[SCENARIO_DEF[sc][0]]["n_bouts"] for r in rs) / n
        a["n_symbols_mean"] = sum(r.get("n_symbols", 0) for r in rs) / n
    return agg


def grade(agg):
    """Registered predictions K1-K10 and rules WR1-WR4 (CALIB-2-PREREG.md).
    A scenario missing from agg grades as None."""
    def g(sc, f):
        return f(agg[sc]) if sc in agg else None
    m1, m1b, m2 = "W_markov1_a0.2_V12", "W_markov1_a0.1_V24", "W_markov2_a0.2_V12"
    preds = {
        "K1": g(m1, lambda a: a["frac_pass_published_controls"] >= 0.80),
        "K2": g(m1, lambda a: a["real_r2_mean"] >= 0.80),
        "K3": g(m1b, lambda a: a["frac_pass_published_controls"] >= 0.80
                and a["real_r2_mean"] >= 0.80),
        "K4": g(m1, lambda a: a["nulls"]["markov1_pooled"]["frac_p_lt_alpha"] <= 0.15),
        "K5": g(m2, lambda a: a["frac_beyond_second_order"] <= 0.15),
        "K6": g("W_words_zipf_V12", lambda a: a["frac_beyond_second_order"] >= 0.50),
        "K7": g("W_words_zipf_noise10_V12", lambda a: a["frac_beyond_second_order"] >= 0.50),
        "K8": g("F_words_zipf_noise02", lambda a: a["frac_beyond_second_order"] >= 0.50),
        "K9": g("F_words_zipf_noise05", lambda a: a["frac_beyond_second_order"] >= 0.50),
        "K10": g(m1, lambda a: a["nulls"]["bigram_within"]["frac_p_lt_alpha"] <= 0.15),
    }
    # WR1: what may be said about the whale paper's two controls at whale size.
    if preds["K1"] is None:
        wr1 = None
    elif preds["K1"] and preds["K2"]:
        wr1 = "CONTROLS_PASSED_BY_WORDLESS_SONG"
    elif preds["K1"]:
        wr1 = "CONTROLS_PASSED_BUT_LESS_ZIPFIAN"
    else:
        wr1 = "CONTROLS_SEPARATE_AT_WHALE_SIZE"
    # WR4: noise tolerance at finch size, from calib-1 (0.00 -> 1.00, 0.10 -> 0.10)
    # and calib-2 (0.02, 0.05): the smallest noise level with power < 0.50.
    power = {0.0: 1.0, 0.10: 0.10}
    for lvl, sc in ((0.02, "F_words_zipf_noise02"), (0.05, "F_words_zipf_noise05")):
        if sc in agg:
            power[lvl] = agg[sc]["frac_beyond_second_order"]
    failing = sorted(l for l, p in power.items() if p < 0.50)
    rules = {
        "WR1_whale_controls": wr1,
        "WR2_whale_low_power_relabel": None if preds["K6"] is None else (not preds["K6"]),
        "WR3_whale_size_caveat": None if preds["K5"] is None else (not preds["K5"]),
        "WR4_finch_power_by_noise": {str(k): power[k] for k in sorted(power)},
        "WR4_finch_noise_level_power_below_half": failing[0] if failing else None,
    }
    graded = [k for k, v in preds.items() if v is not None]
    brier = (sum((PRIORS[k] - (1.0 if preds[k] else 0.0)) ** 2 for k in graded) / len(graded)
             if graded else None)
    return {"predictions": preds, "rules": rules, "priors": PRIORS, "brier": brier}


def build_tasks(reps, B, theta, deadline, scenarios=None, n_rec=None):
    names = scenarios or [s[0] for s in SCENARIOS]
    return [dict(scenario=sc, rep=rep, B=B, theta=theta, deadline=deadline, n_rec=n_rec)
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
    ap.add_argument("--max-minutes", type=float, default=150)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    deadline = t0 + 60 * a.max_minutes
    tasks = build_tasks(a.reps, a.B, 0.5, deadline)
    jl = os.path.join(a.out_dir, "calib2_tasks.jsonl")
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
                           for fn in ("zipfseg.py", "calib.py", "calib2.py")},
           "config": {"reps": a.reps, "B": a.B, "theta": 0.5, "sizes": SIZES,
                      "nulls": list(NULLS_USED) + ["rotate"],
                      "scenarios": {s[0]: {"size": s[1], "V": s[2], "kind": s[3], **s[4]}
                                    for s in SCENARIOS}},
           "n_tasks": len(tasks), "n_skipped": sum(1 for r in results if r.get("skipped")),
           "elapsed_s": round(time.time() - t0, 1),
           "aggregate": agg, "grading": grade(agg),
           "published_reference": {
               "whale_arnon2025": {"mean_r2": 0.93, "z_shuffle": 23.09, "z_rotate": 14.43,
                                   "cuts_per_year": 1562},
               "finch_kirby2026": {"mean_r2": 0.89, "z_shuffle": 17.05, "z_rotate": 15.69,
                                   "z_bigram": 6.77}}}
    tmp = os.path.join(a.out_dir, "calib2_results.json.%d.part" % os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    os.replace(tmp, os.path.join(a.out_dir, "calib2_results.json"))
    print(json.dumps({"aggregate": agg, "grading": out["grading"],
                      "n_skipped": out["n_skipped"], "elapsed_s": out["elapsed_s"]}, indent=1))


if __name__ == "__main__":
    main()
