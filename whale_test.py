# SPDX-License-Identifier: Apache-2.0
# whale_test.py: the registered real-data whale test of song-zipf-test
# (PREREG.md whale part, PREREG-AMENDMENT-1.md, and PREREG-AMENDMENT-3.md).
#
# Do the "language-like" laws found in eight years of humpback whale song (Arnon et al.
# 2025, Science 387:649: Zipf rank-frequency mean R^2 0.93; law of brevity R^2 0.62) survive
# null models that keep the song's own sound-element transition rules (pooled first- and
# second-order Markov chains fitted to each year), not only the paper's shuffle and
# rotation baselines?
#
# As PREREG.md registered for the whale data: one "recording" = one year (TPs pooled within
# the year); one "bout" = one recording's sound-element sequence (no transition crosses a
# recording boundary). Forward TPs, cut rule and Zipf R^2 exactly as zipfseg.py (Code S1 of
# the finch paper; the whale Code S1 is read later and any difference is logged).
# Uses zipfseg.py (munimtechnologies/song-zipf-test, commit e976e63) unchanged.
# Registered and published BEFORE the whale data files were opened.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import json
import math
import os
import random
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zipfseg as Z  # noqa: E402
import whale_read as R  # noqa: E402

VERSION = "whale-test-1"
SEED = 20261117                  # PREREG.md
ALPHA = 0.05
# (theta, rule, B). 0.5 primary (B 1000, PREREG); 0.3/0.7 = PREREG robustness;
# 0.25/0.75 = the paper's own robustness thresholds; reversed rule = PREREG sensitivity.
RUNS = ((0.5, "cur_over_prev", 1000), (0.3, "cur_over_prev", 200),
        (0.7, "cur_over_prev", 200), (0.25, "cur_over_prev", 200),
        (0.75, "cur_over_prev", 200), (0.5, "prev_over_cur", 200))
NULL_ORDER = ("shuffle", "rotate", "markov1_pooled", "markov2_pooled",
              "bigram_within", "trigram_within")
STATS = ("zipf", "brev_pool", "brev_year")
PUBLISHED = {"zipf_r2": 0.93, "zipf_z_shuffle": 23.09, "zipf_z_rotate": 14.43,
             "brev_r2": 0.62, "brev_z_shuffle": 37.57, "brev_z_rotate": 13.92}
# Table S2 of the paper: most frequent sub-sequences per year (theta 0.5) and counts
# (2010: two only, the third place is a tie).
TABLE_S2 = {
    2010: [(("gr", "gr", "m"), 31), (("m", "ac", "ac", "ac"), 17)],
    2011: [(("ba", "p(l)", "ba"), 37), (("dws", "m"), 33), (("m(s)", "dws"), 28)],
    2012: [(("w", "gr", "w"), 52), (("gr", "ba"), 46), (("gr(pul)", "m(pul)", "gr"), 45)],
    2013: [(("lb", "sn", "lb", "sn", "hs(pul)", "ba", "lb"), 68), (("aws(s)", "sq"), 52),
           (("lb",), 30)],
    2014: [(("agr(pul-s)", "w"), 167), (("agr(pul)", "w"), 110), (("ac", "be", "ac"), 107)],
    2015: [(("gr(s)-dws(s)", "sq", "sq", "sq"), 204),
           (("gr(s)-dws(s)", "gr", "gr(s)-dws(s)", "sq", "sq", "sq"), 74),
           (("gr(s)-dws(s)",), 67)],
    2016: [(("dm(l)", "dm"), 129), (("gr(s)",), 98), (("hsq", "w"), 73)],
    2017: [(("gw(low)", "gr"), 125), (("ns", "ns"), 120), (("dhq", "w"), 113)],
}
# PREREG.md whale priors (S-W, W1-W6) and PREREG-AMENDMENT-3 priors (N1-N6).
PRIORS = {"S-W": 0.85, "W1": 0.70, "W2": 0.70, "W3": 0.45, "W4": 0.45, "W5": 0.50,
          "W6": 0.70, "N1": 0.60, "N2": 0.90, "N3": 0.45, "N4": 0.85, "N5": 0.40,
          "N6": 0.25}
NAN = float("nan")


def run_key(theta, rule):
    return str(theta) if rule == "cur_over_prev" else "%s_reversed" % theta


# --------------------------------------------------------------------------
# statistics on one segmented data set (list of per-year inventories)
# --------------------------------------------------------------------------
def ols_points(points):
    """R^2 and OLS slope of y on x (same as calib4.ols_points)."""
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


def stats(invs):
    """zipf: mean over years of the per-year rank-frequency R^2 (zipfseg.zipf_r2);
    brev_pool: one point per chunk type, counts summed over years (calib4 'pool');
    brev_year: one point per (year, chunk type) (calib4 'year')."""
    zipf = Z.nanmean([Z.zipf_r2(inv.values()) for inv in invs])
    pool = Counter()
    for inv in invs:
        pool.update(inv)
    r2p, slp = ols_points([(len(k), math.log10(v)) for k, v in pool.items() if v > 0])
    r2y, sly = ols_points([(len(k), math.log10(v)) for inv in invs for k, v in inv.items()
                           if v > 0])
    return {"zipf": zipf, "brev_pool": r2p, "brev_pool_slope": slp,
            "brev_year": r2y, "brev_year_slope": sly}


def inventories(segyears):
    out = []
    for segrec in segyears:
        inv = Counter()
        for segs in segrec:
            for s in segs:
                inv[s] += 1
        out.append(inv)
    return out


def segment_years(years, theta, rule="cur_over_prev"):
    """years: list (one per year) of lists of recordings -> per year, per recording,
    list of sub-sequences. TPs estimated per year over all its recordings."""
    return [Z.segment_recording_bouts(recs, theta, rule) for recs in years]


def compare(real, vals):
    """z (population SD) and one-sided p (null >= real, +1 correction)."""
    v = [a for a in vals if a == a]
    if len(v) < 2 or real != real:
        return {"real": real, "z": NAN, "p": NAN, "null_mean": NAN, "null_sd": NAN,
                "n_null": len(v)}
    m = sum(v) / len(v)
    sd = math.sqrt(sum((a - m) ** 2 for a in v) / len(v))
    return {"real": real, "z": (real - m) / sd if sd > 0 else NAN,
            "p": (1 + sum(1 for a in v if a >= real)) / (1 + len(v)),
            "null_mean": m, "null_sd": sd, "n_null": len(v)}


def null_stats(name, years, segyears, theta, rule, rng):
    if name == "rotate":
        return stats(inventories([[Z.rotate_bout_segments(segs, rng) for segs in sr]
                                  for sr in segyears]))
    fake = [Z.NULLS[name](recs, rng) for recs in years]
    return stats(inventories(segment_years(fake, theta, rule)))


def run_theta(years, theta, B, deadline, seed=SEED, rule="cur_over_prev"):
    segyears = segment_years(years, theta, rule)
    invs = inventories(segyears)
    real = stats(invs)
    n_chunks = sum(sum(inv.values()) for inv in invs)
    row = {"theta": theta, "rule": rule, "real": real, "n_chunks": n_chunks,
           "n_cuts": n_chunks - sum(len(y) for y in years),
           "n_types_per_year": [len(inv) for inv in invs], "nulls": {}}
    off = 0 if rule == "cur_over_prev" else 5
    for ni, name in enumerate(NULL_ORDER):
        rng = random.Random(seed * 1000 + ni * 10 + off + int(round(theta * 100)) * 100)
        vals = []
        for _ in range(B):
            if time.time() > deadline:
                break
            vals.append(null_stats(name, years, segyears, theta, rule, rng))
        d = {s: compare(real[s], [v[s] for v in vals]) for s in STATS}
        sl = [v["brev_pool_slope"] for v in vals if v["brev_pool_slope"] == v["brev_pool_slope"]]
        d["frac_null_brev_pool_slope_neg"] = (sum(1 for a in sl if a < 0) / len(sl)) if sl else NAN
        d["B_done"] = len(vals)
        row["nulls"][name] = d
    return row, invs


# --------------------------------------------------------------------------
# Table S2 reproduction check
# --------------------------------------------------------------------------
def table_s2_check(year_list, invs):
    """Per year: is the paper's most frequent sub-sequence also ours, with a count within
    10% (or 3)? Also how many of the listed items are in our inventory with such a count."""
    def close(a, b):
        return abs(a - b) <= max(3, 0.10 * b)
    out = {}
    for y, inv in zip(year_list, invs):
        if y not in TABLE_S2:
            continue
        ours = inv.most_common(1)[0] if inv else ((), 0)
        top_seq, top_n = TABLE_S2[y][0]
        out[str(y)] = {
            "paper_top": [list(top_seq), top_n], "our_top": [list(ours[0]), ours[1]],
            "top1_match": ours[0] == top_seq and close(ours[1], top_n),
            "listed_found": sum(1 for s, n in TABLE_S2[y] if close(inv.get(s, 0), n)),
            "listed": len(TABLE_S2[y])}
    n_match = sum(1 for v in out.values() if v["top1_match"])
    return {"per_year": out, "n_years_top1_match": n_match, "reproduced": n_match >= 6}


def heldout(years):
    """D1: leave-one-recording-out log-likelihood per element, order 2 minus order 1."""
    d = [Z.heldout_ll(recs, 2) - Z.heldout_ll(recs, 1) for recs in years]
    return {"per_year": d, "n_favour_order2": sum(1 for a in d if a > 0)}


# --------------------------------------------------------------------------
# registered grading
# --------------------------------------------------------------------------
def beats(row, stat, null):
    p = row["nulls"][null][stat]["p"]
    return p == p and p < ALPHA


def label(row, stat):
    """PREREG section 5 labels on one statistic. For brevity the real slope must be
    negative (frequent chunks shorter) for the real data to count as beating a null."""
    ok = True
    if stat.startswith("brev"):
        s = row["real"][stat + "_slope"]
        ok = s == s and s < 0
    if ok and beats(row, stat, "markov2_pooled"):
        return "BEYOND_SECOND_ORDER"
    if ok and beats(row, stat, "markov1_pooled"):
        return "EXPLAINED_BY_SECOND_ORDER"
    return "EXPLAINED_BY_FIRST_ORDER"


def grade(rows, s2, ho, brev_key="brev_pool"):
    m = rows["0.5"]
    r = m["real"]
    nm = m["nulls"]
    slope = r[brev_key + "_slope"]
    slope_neg = slope == slope and slope < 0
    m2mean = nm["markov2_pooled"]["zipf"]["null_mean"]
    preds = {
        "S-W": beats(m, "zipf", "shuffle") and abs(r["zipf"] - PUBLISHED["zipf_r2"]) <= 0.03,
        "W1": beats(m, "zipf", "bigram_within"),
        "W2": beats(m, "zipf", "markov1_pooled"),
        "W3": beats(m, "zipf", "trigram_within"),
        "W4": beats(m, "zipf", "markov2_pooled"),
        "W5": m2mean == m2mean and m2mean >= 0.80,
        "W6": ho["n_favour_order2"] >= 6,
        "N1": bool(s2["reproduced"]),
        "N2": beats(m, "zipf", "rotate"),
        "N3": abs(r[brev_key] - PUBLISHED["brev_r2"]) <= 0.10,
        "N4": slope_neg and beats(m, brev_key, "shuffle") and beats(m, brev_key, "rotate"),
        "N5": slope_neg and beats(m, brev_key, "markov1_pooled"),
        "N6": slope_neg and beats(m, brev_key, "markov2_pooled"),
    }
    brier = sum((PRIORS[k] - (1.0 if v else 0.0)) ** 2 for k, v in preds.items()) / len(preds)
    zl = label(m, "zipf") if preds["S-W"] else "REPRODUCTION_FAILED"
    bl = label(m, brev_key) if preds["N4"] else "REPRODUCTION_FAILED"
    by = {k: {"zipf": label(v, "zipf"), "brevity": label(v, brev_key)}
          for k, v in rows.items()}
    robust = {s: (all(k in by for k in ("0.3", "0.5", "0.7"))
                  and len({by[k][s] for k in ("0.3", "0.5", "0.7")}) == 1)
              for s in ("zipf", "brevity")}
    caveats = []
    if not preds["N1"]:
        caveats.append("Table S2 not reproduced (top sub-sequence in < 6 of 8 years): our "
                       "pipeline differs in detail from the authors'; no headline until "
                       "Code S1 explains the difference (PREREG-AMENDMENT-3 5.2)")
    if not preds["W6"]:
        caveats.append("overfit caveat (D1): order 2 does not generalise better in >= 6 of 8 "
                       "years")
    return {"brev_key": brev_key, "predictions": preds, "priors": PRIORS, "brier": brier,
            "labels": {"zipf": zl, "brevity": bl}, "labels_by_run": by, "robust": robust,
            "caveats": caveats}


def final_reading(g, calib2=None, calib4=None):
    """PREREG-AMENDMENT-3 section 5: apply the calibration conditions. calib2 / calib4 are
    dicts of graded prediction ids (CALIB-2: K5, K6; CALIB-4: Q10, Q11) -> True/False/None;
    None or a missing dict = not yet measured."""
    c2 = calib2 or {}
    c4 = calib4 or {}
    out = {}
    for stat, beyond_ok, explained_ok, src in (
            ("zipf", c2.get("K5"), c2.get("K6"), "CALIB-2 K5/K6"),
            ("brevity", c4.get("Q10"), c4.get("Q11"), "CALIB-4 Q10/Q11")):
        lab = g["labels"][stat]
        headline = lab != "REPRODUCTION_FAILED" and g["predictions"]["N1"]
        notes = []
        final = lab
        if lab == "BEYOND_SECOND_ORDER":
            if beyond_ok is None:
                headline = False
                notes.append("pending: size of the null not yet measured (%s)" % src)
            elif not beyond_ok:
                headline = False
                notes.append("size caveat (%s): not a headline" % src)
        if lab.startswith("EXPLAINED_BY"):
            if explained_ok is None:
                headline = False
                notes.append("pending: power against word-like song not yet measured (%s)"
                             % src)
            elif not explained_ok:
                final = "NOT_DISTINGUISHABLE"
                notes.append("low power (%s): reported as NOT_DISTINGUISHABLE" % src)
        out[stat] = {"label": final, "base_label": lab, "headline": headline, "notes": notes}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--max-minutes", type=float, default=150)
    ap.add_argument("--b-scale", type=float, default=1.0,
                    help="multiply every B (tests only; the registered run uses 1.0)")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    data, rep = R.read_songs(a.data_dir)
    with open(os.path.join(a.out_dir, "whale_read_report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    if data is None:
        print("READING GATE NOT PASSED (n_distinct_passing=%d): no statistic computed."
              % rep["n_distinct_passing"])
        return 0
    year_list = sorted(data)
    years = [data[y] for y in year_list]
    deadline = t0 + 60 * a.max_minutes
    rows = {}
    s2 = None
    for th, rule, B in RUNS:
        row, invs = run_theta(years, th, max(1, int(round(B * a.b_scale))), deadline,
                              rule=rule)
        rows[run_key(th, rule)] = row
        if th == 0.5 and rule == "cur_over_prev":
            s2 = table_s2_check(year_list, invs)
            top = {str(y): [[list(k), v] for k, v in inv.most_common(15)]
                   for y, inv in zip(year_list, invs)}
            with open(os.path.join(a.out_dir, "whale_top15_theta0.5.json"), "w",
                      encoding="utf-8") as f:
                json.dump(top, f, indent=1)
    ho = heldout(years)
    g = grade(rows, s2, ho, "brev_pool")
    out = {"version": VERSION, "python": sys.version.split()[0], "reader": rep["chosen"],
           "years": year_list, "n_recordings": [len(y) for y in years],
           "n_elements": [sum(len(r) for r in y) for y in years],
           "config": {"runs": [list(x) for x in RUNS], "b_scale": a.b_scale, "seed": SEED,
                      "nulls": list(NULL_ORDER)},
           "by_theta": rows, "table_s2": s2, "heldout_order2_minus_order1": ho,
           "grading": g, "grading_alternate_year": grade(rows, s2, ho, "brev_year"),
           "final_reading_before_calibrations": final_reading(g),
           "published": PUBLISHED, "elapsed_s": round(time.time() - t0, 1)}
    tmp = os.path.join(a.out_dir, "whale_results.json.%d.part" % os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    os.replace(tmp, os.path.join(a.out_dir, "whale_results.json"))
    print(json.dumps({"labels": g["labels"], "predictions": g["predictions"],
                      "table_s2_top1_years": s2["n_years_top1_match"],
                      "elapsed_s": out["elapsed_s"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
