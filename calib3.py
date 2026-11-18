# SPDX-License-Identifier: Apache-2.0
# calib3.py: third synthetic calibration of the song-zipf test, for Zipf's LAW OF
# BREVITY (more frequent units are shorter). Registered in CALIB-3-PREREG.md before
# this code was run.
#
# Both song papers report that the chunks found by transitional-probability (TP)
# segmentation obey the law of brevity:
#  * Arnon et al. 2025 (Science 387:649, humpback whale): R^2 0.62 between chunk length
#    and log frequency, beating shuffled and rotated baselines.
#  * Kirby et al. 2026 (Sci. Adv. eaea3015, Bengalese finch): Poisson mixed-effects
#    regression of a chunk's frequency in a recording on its length in syllables,
#    beta = -0.04, P < 0.00001, with no baseline.
# Question: does the pipeline report brevity for song that has NO brevity in its units
# (words of equal frequency), for song with the REVERSE relation (longer words more
# frequent), and for song with no words at all (Markov chains)? And do the shuffle and
# rotation baselines separate those sources from song whose units truly obey brevity?
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

VERSION = "calib-3"
MASTER_SEED = 20261119
THETA = 0.5
ALPHA = 0.05
Z_SIG = 4.42          # |Wald z| >= 4.42 <=> two-sided P < 0.00001 (the finch paper's bar)
NULLS_USED = ("shuffle", "bigram_within", "markov1_pooled", "markov2_pooled")

SIZES = {
    "finch": {"n_rec": 30, "n_bouts": 10, "lmin": 40, "lmax": 96},
    "whale": {"n_rec": 8, "n_bouts": 6, "lmin": 700, "lmax": 1500},
}
_LEX = {"n_words": 12, "lmin": 3, "lmax": 7}
# (name, size, alphabet V, kind, params). Order is fixed: it sets the seeds.
SCENARIOS = [
    ("markov1_a0.2", "finch", 8, "markov1", {"alpha": 0.2}),
    ("markov2_a0.2", "finch", 8, "markov2", {"alpha": 0.2}),
    ("words_zipf", "finch", 8, "words", dict(_LEX, weights="zipf")),
    ("words_uniform", "finch", 8, "words", dict(_LEX, weights="uniform")),
    ("words_brevity", "finch", 8, "words", dict(_LEX, weights="brevity")),
    ("words_antibrevity", "finch", 8, "words", dict(_LEX, weights="antibrevity")),
    ("W_markov1_a0.2_V12", "whale", 12, "markov1", {"alpha": 0.2}),
]
SCENARIO_INDEX = {s[0]: i for i, s in enumerate(SCENARIOS)}
SCENARIO_DEF = {s[0]: s[1:] for s in SCENARIOS}

PRIORS = {"P1": 0.85, "P2": 0.45, "P3": 0.50, "P4": 0.90, "P5": 0.60,
          "P6": 0.35, "P7": 0.40, "P8": 0.85, "P9": 0.80, "P10": 0.45}


# --------------------------------------------------------------------------
# generators
# --------------------------------------------------------------------------
def word_weights(lexicon, mode):
    """Draw weights for the lexicon words.
    zipf: 1/(i+1) by lexicon position (independent of length); uniform: equal;
    brevity: 2^-(L-3) (each extra syllable halves the frequency);
    antibrevity: 2^(L-3) (each extra syllable doubles it)."""
    if mode == "zipf":
        return [1.0 / (i + 1) for i in range(len(lexicon))]
    if mode == "uniform":
        return [1.0] * len(lexicon)
    if mode == "brevity":
        return [2.0 ** -(len(w) - 3) for w in lexicon]
    if mode == "antibrevity":
        return [2.0 ** (len(w) - 3) for w in lexicon]
    raise ValueError(mode)


def gen_words_units(lexicon, weights, n, rng):
    """One bout of length n made of i.i.d. words; returns (bout, complete words used).
    The last word is dropped from the unit list when the bout truncates it."""
    seq, units = [], []
    while len(seq) < n:
        w = rng.choices(lexicon, weights=weights)[0]
        seq.extend(w)
        units.append(w)
    if len(seq) > n:
        units.pop()
    return seq[:n], units


def make_dataset(scenario, rng, n_rec=None):
    """(recordings, unit inventories). Each recording gets a fresh source. For word
    sources the unit inventory counts the complete true words in the recording; for
    Markov sources it is None."""
    size, V, kind, params = SCENARIO_DEF[scenario]
    s = SIZES[size]
    nr = s["n_rec"] if n_rec is None else n_rec
    recs, units = [], []
    for _ in range(nr):
        if kind == "words":
            lex = C.make_lexicon(params["n_words"], params["lmin"], params["lmax"], V, rng)
            w = word_weights(lex, params["weights"])
            bouts, inv = [], Counter()
            for _b in range(s["n_bouts"]):
                bout, us = gen_words_units(lex, w, rng.randint(s["lmin"], s["lmax"]), rng)
                bouts.append(bout)
                for u in us:
                    inv[u] += 1
            recs.append(bouts)
            units.append(inv)
        else:
            src = C.make_source(kind, params, V, rng)
            recs.append([src(rng.randint(s["lmin"], s["lmax"]), rng)
                         for _b in range(s["n_bouts"])])
            units.append(None)
    return recs, (units if kind == "words" else None)


# --------------------------------------------------------------------------
# brevity statistics
# --------------------------------------------------------------------------
def ols_r2_slope(inv):
    """Per recording: R^2 and OLS slope of log(count) on length over chunk types
    (whale-style). nan, nan when < 3 types or no variation in length or count."""
    if len(inv) < 3:
        return float("nan"), float("nan")
    x = [float(len(k)) for k in inv]
    y = [math.log(v) for v in inv.values()]
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return float("nan"), float("nan")
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy * sxy / (sxx * syy), sxy / sxx


def poisson_fe_slope(invs, max_iter=100):
    """Poisson regression of a type's count in a recording on its length, with one
    free intercept per recording (finch-style; the paper used random intercepts per
    bird). Observed types only, as in both papers. Returns (beta, Wald SE).
    Profile score: sum_r [sum_t L_t c_t - C_r * m_r(beta)], m_r = exp(beta*L)-weighted
    mean length over recording r's types; it decreases in beta, so Newton steps are
    kept inside a shrinking bracket. Recordings whose types all have one length carry
    no information and are skipped; (nan, nan) if none remain."""
    groups = []
    for inv in invs:
        if not inv:
            continue
        L = [float(len(k)) for k in inv]
        if len(set(L)) < 2:
            continue
        c = list(inv.values())
        groups.append((L, sum(c), sum(l * n for l, n in zip(L, c))))

    if not groups:
        return float("nan"), float("nan")

    def score_info(b):
        s = 0.0
        info = 0.0
        for L, Ctot, SLc in groups:
            mx = max(b * l for l in L)
            w = [math.exp(b * l - mx) for l in L]
            W = sum(w)
            m = sum(l * x for l, x in zip(L, w)) / W
            v = sum(l * l * x for l, x in zip(L, w)) / W - m * m
            s += SLc - Ctot * m
            info += Ctot * max(v, 0.0)
        return s, info

    lo, hi = -20.0, 20.0
    b = 0.0
    for _ in range(max_iter):
        s, info = score_info(b)
        if s == 0:
            break
        if s > 0:
            lo = b
        else:
            hi = b
        nb = b + s / info if info > 0 else (lo + hi) / 2
        if not (lo < nb < hi):
            nb = (lo + hi) / 2
        if abs(nb - b) < 1e-12:
            b = nb
            break
        b = nb
    s, info = score_info(b)
    se = 1.0 / math.sqrt(info) if info > 0 else float("nan")
    return b, se


def brevity_stats(invs):
    """Dataset statistics from per-recording chunk inventories."""
    r2s, slopes = [], []
    for inv in invs:
        r2, sl = ols_r2_slope(inv)
        if r2 == r2:
            r2s.append(r2)
            slopes.append(sl)
    beta, se = poisson_fe_slope(invs)
    wz = beta / se if (se == se and se > 0) else float("nan")
    return {"r2": sum(r2s) / len(r2s) if r2s else float("nan"),
            "slope": sum(slopes) / len(slopes) if slopes else float("nan"),
            "beta": beta, "beta_se": se, "wald_z": wz}


def _cmp(real, vals):
    """z (population SD) and one-sided p (null >= real, +1 correction), nan-safe."""
    v = [a for a in vals if a == a]
    if len(v) < 2 or real != real:
        return {"z": float("nan"), "p": float("nan"), "null_mean": float("nan"),
                "null_sd": float("nan"), "n_null": len(v)}
    m = sum(v) / len(v)
    sd = math.sqrt(sum((a - m) ** 2 for a in v) / len(v))
    z = (real - m) / sd if sd > 0 else float("nan")
    p = (1 + sum(1 for a in v if a >= real)) / (1 + len(v))
    return {"z": z, "p": p, "null_mean": m, "null_sd": sd, "n_null": len(v)}


def _null_summary(real, stats_list):
    """r2: real higher than null (whale-style fit). beta: real MORE NEGATIVE than null
    (stronger brevity); its z is (null mean - real)/sd and its p counts null <= real."""
    r2 = _cmp(real["r2"], [s["r2"] for s in stats_list])
    nb = _cmp(-real["beta"], [-s["beta"] for s in stats_list])
    sig = [s for s in stats_list if s["wald_z"] == s["wald_z"]]
    return {"r2_z": r2["z"], "r2_p": r2["p"], "r2_null_mean": r2["null_mean"],
            "beta_brevity_z": nb["z"], "beta_p": nb["p"],
            "beta_null_mean": -nb["null_mean"] if nb["null_mean"] == nb["null_mean"]
            else float("nan"),
            "frac_null_sig_brevity": (sum(1 for s in sig if s["wald_z"] <= -Z_SIG) / len(sig)
                                      if sig else float("nan"))}


# --------------------------------------------------------------------------
# one replicate
# --------------------------------------------------------------------------
def task_seed(scenario, rep):
    return MASTER_SEED + 1000 * SCENARIO_INDEX[scenario] + rep


def run_task(task):
    """task: dict(scenario, rep, B, deadline, n_rec (None = preset))."""
    sc, rep = task["scenario"], task["rep"]
    if time.time() > task["deadline"]:
        return {"scenario": sc, "rep": rep, "skipped": True}
    t0 = time.time()
    seed = task_seed(sc, rep)
    rng = random.Random(seed)
    recs, units = make_dataset(sc, rng, task.get("n_rec"))
    segrecs = [Z.segment_recording_bouts(r, THETA) for r in recs]
    invs = []
    for segs_by_bout in segrecs:
        inv = Counter()
        for segs in segs_by_bout:
            for s in segs:
                inv[s] += 1
        invs.append(inv)
    real = brevity_stats(invs)
    B = task["B"]
    nulls = {}
    for ni, name in enumerate(NULLS_USED):
        nrng = random.Random(seed * 1000 + ni * 10 + 5)
        st = []
        for _ in range(B):
            fake = [NULLS_FN(name, rec, nrng) for rec in recs]
            st.append(brevity_stats([Z.segment_recording(f, THETA) for f in fake]))
        nulls[name] = _null_summary(real, st)
    rrng = random.Random(seed * 1000 + 905)
    st = []
    for _ in range(B):
        rinvs = []
        for segs_by_bout in segrecs:
            inv = Counter()
            for segs in segs_by_bout:
                for s in Z.rotate_bout_segments(segs, rrng):
                    inv[s] += 1
            rinvs.append(inv)
        st.append(brevity_stats(rinvs))
    nulls["rotate"] = _null_summary(real, st)
    src = None
    if units is not None:
        sb, sse = poisson_fe_slope(units)
        src = {"beta": sb, "wald_z": sb / sse if (sse == sse and sse > 0) else float("nan")}
    n_chunks = sum(sum(inv.values()) for inv in invs)
    return {"scenario": sc, "rep": rep, "seed": seed, "skipped": False,
            "real": real, "source": src, "nulls": nulls,
            "n_rec": len(recs), "n_symbols": sum(len(b) for r in recs for b in r),
            "n_chunks": n_chunks, "n_types": sum(len(inv) for inv in invs),
            "mean_chunk_len": (sum(len(k) * v for inv in invs for k, v in inv.items())
                               / n_chunks if n_chunks else float("nan")),
            "seconds": round(time.time() - t0, 2)}


def NULLS_FN(name, rec, rng):
    return Z.NULLS[name](rec, rng)


# --------------------------------------------------------------------------
# aggregation and grading
# --------------------------------------------------------------------------
def _mean(v):
    v = [a for a in v if a == a]
    return sum(v) / len(v) if v else float("nan")


def whale_pass(r):
    """Whale-style brevity controls passed: brevity direction (mean OLS slope < 0) and
    an R^2 above both the shuffle and the rotation baselines (p < 0.05)."""
    return (r["real"]["slope"] < 0 and r["nulls"]["shuffle"]["r2_p"] < ALPHA
            and r["nulls"]["rotate"]["r2_p"] < ALPHA)


def aggregate(results):
    by = {}
    for r in results:
        if not r.get("skipped"):
            by.setdefault(r["scenario"], []).append(r)
    out = {}
    for sc, rs in by.items():
        n = len(rs)
        a = {"n_reps": n,
             "beta_mean": _mean([r["real"]["beta"] for r in rs]),
             "wald_z_mean": _mean([r["real"]["wald_z"] for r in rs]),
             "r2_mean": _mean([r["real"]["r2"] for r in rs]),
             "slope_mean": _mean([r["real"]["slope"] for r in rs]),
             "frac_sig_brevity": sum(1 for r in rs if r["real"]["wald_z"] <= -Z_SIG) / n,
             "frac_sig_antibrevity": sum(1 for r in rs if r["real"]["wald_z"] >= Z_SIG) / n,
             "frac_pass_whale_controls": sum(1 for r in rs if whale_pass(r)) / n,
             "mean_chunk_len": _mean([r["mean_chunk_len"] for r in rs]),
             "nulls": {}}
        srcs = [r["source"] for r in rs if r.get("source")]
        if srcs:
            a["source_beta_mean"] = _mean([s["beta"] for s in srcs])
            a["frac_source_beta_pos"] = sum(1 for s in srcs if s["beta"] > 0) / len(srcs)
            a["frac_source_beta_neg"] = sum(1 for s in srcs if s["beta"] < 0) / len(srcs)
        for name in rs[0]["nulls"]:
            ns = [r["nulls"][name] for r in rs]
            a["nulls"][name] = {
                "frac_r2_p_lt_alpha": sum(1 for x in ns if x["r2_p"] < ALPHA) / n,
                "frac_beta_p_lt_alpha": sum(1 for x in ns if x["beta_p"] < ALPHA) / n,
                "r2_z_mean": _mean([x["r2_z"] for x in ns]),
                "beta_brevity_z_mean": _mean([x["beta_brevity_z"] for x in ns]),
                "beta_null_mean": _mean([x["beta_null_mean"] for x in ns]),
                "frac_null_sig_brevity_mean": _mean([x["frac_null_sig_brevity"] for x in ns])}
        out[sc] = a
    return out


def grade(agg):
    """Registered predictions P1-P10 and rules BR1-BR4 (CALIB-3-PREREG.md).
    A scenario missing from agg grades as None."""
    def g(sc, f):
        return f(agg[sc]) if sc in agg else None
    m1, wm1 = "markov1_a0.2", "W_markov1_a0.2_V12"
    preds = {
        "P1": g(m1, lambda a: a["frac_sig_brevity"] >= 0.90),
        "P2": g(m1, lambda a: a["frac_pass_whale_controls"] >= 0.80),
        "P3": g(wm1, lambda a: a["frac_pass_whale_controls"] >= 0.80),
        "P4": g("words_brevity", lambda a: a["frac_sig_brevity"] >= 0.90),
        "P5": g("words_uniform", lambda a: a["frac_sig_brevity"] >= 0.50),
        "P6": g("words_antibrevity", lambda a: a["frac_sig_brevity"] >= 0.50),
        "P7": g("words_antibrevity", lambda a: a["frac_sig_antibrevity"] >= 0.50),
        "P8": g(m1, lambda a: a["nulls"]["shuffle"]["frac_null_sig_brevity_mean"] >= 0.90),
        "P9": g(m1, lambda a: a["nulls"]["markov1_pooled"]["frac_beta_p_lt_alpha"] <= 0.15),
        "P10": g("words_brevity",
                 lambda a: a["nulls"]["markov2_pooled"]["frac_beta_p_lt_alpha"] >= 0.50),
    }
    p = preds
    if p["P1"] is None or p["P8"] is None:
        br1 = None
    else:
        br1 = bool(p["P1"] and p["P8"])
    if p["P2"] is None and p["P3"] is None:
        br2 = None
    elif p["P2"] and p["P3"]:
        br2 = "BREVITY_CONTROLS_PASSED_BY_WORDLESS_SONG"
    elif p["P2"] or p["P3"]:
        br2 = "BREVITY_CONTROLS_PASSED_BY_WORDLESS_SONG_AT_ONE_SIZE"
    else:
        br2 = "BREVITY_CONTROLS_SEPARATE"
    # Sanity: the word sources must have the intended sign in their TRUE units.
    sane = {}
    if "words_brevity" in agg:
        sane["words_brevity_source_negative"] = agg["words_brevity"].get(
            "frac_source_beta_neg", 0.0) == 1.0
    if "words_antibrevity" in agg:
        sane["words_antibrevity_source_positive"] = agg["words_antibrevity"].get(
            "frac_source_beta_pos", 0.0) == 1.0
    rules = {
        "BR1_glmm_brevity_uninformative": br1,
        "BR2_whale_brevity_controls": br2,
        "BR3_pipeline_reverses_true_relation": (
            None if p["P6"] is None else bool(p["P6"]
                                              and sane.get("words_antibrevity_source_positive"))),
        "BR4_pipeline_tracks_source_sign": (
            None if (p["P4"] is None or p["P7"] is None) else bool(p["P4"] and p["P7"])),
        "sanity": sane,
    }
    graded = [k for k, v in preds.items() if v is not None]
    brier = (sum((PRIORS[k] - (1.0 if preds[k] else 0.0)) ** 2 for k in graded) / len(graded)
             if graded else None)
    return {"predictions": preds, "rules": rules, "priors": PRIORS, "brier": brier}


def build_tasks(reps, B, deadline, scenarios=None, n_rec=None):
    names = scenarios or [s[0] for s in SCENARIOS]
    # rep-major order so that a time-out still leaves every scenario covered
    return [dict(scenario=sc, rep=rep, B=B, deadline=deadline, n_rec=n_rec)
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
    tasks = build_tasks(a.reps, a.B, deadline)
    jl = os.path.join(a.out_dir, "calib3_tasks.jsonl")
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
                           for fn in ("zipfseg.py", "calib.py", "calib3.py")},
           "config": {"reps": a.reps, "B": a.B, "theta": THETA, "alpha": ALPHA,
                      "wald_z_threshold": Z_SIG, "sizes": SIZES,
                      "nulls": list(NULLS_USED) + ["rotate"],
                      "scenarios": {s[0]: {"size": s[1], "V": s[2], "kind": s[3], **s[4]}
                                    for s in SCENARIOS}},
           "n_tasks": len(tasks), "n_skipped": sum(1 for r in results if r.get("skipped")),
           "elapsed_s": round(time.time() - t0, 1),
           "aggregate": agg, "grading": grade(agg),
           "published_reference": {
               "whale_arnon2025_brevity": {"r2": 0.62, "z_shuffle": 37.57, "z_rotate": 13.92},
               "finch_kirby2026_brevity": {"beta": -0.04, "se": 0.0045, "p": "< 0.00001",
                                           "baselines": "none reported"}}}
    tmp = os.path.join(a.out_dir, "calib3_results.json.%d.part" % os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    os.replace(tmp, os.path.join(a.out_dir, "calib3_results.json"))
    print(json.dumps({"aggregate": agg, "grading": out["grading"],
                      "n_skipped": out["n_skipped"], "elapsed_s": out["elapsed_s"]}, indent=1))


if __name__ == "__main__":
    main()
