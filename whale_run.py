# SPDX-License-Identifier: Apache-2.0
# whale_run.py: the real whale test of song-zipf-test with the reading step of
# PREREG-AMENDMENT-5.md. Only the READING and its GATE change; the analysis, nulls,
# predictions and rules are those of PREREG-AMENDMENT-3.md, run by whale_test.py
# (commit 742fd83) and zipfseg.py (commit e976e63), both imported unchanged.
#
# Reading: Data S2 of Arnon et al. 2025 (Science 387:649), one row per recording, grouped
# by its `song_type` column, the grouping the authors' own Code S1 analyses ("song types
# ... are synonymous with years"). The song string is parsed with ast.literal_eval (Code S1
# uses eval on the same column).
# Gate A (data): every row parses; song types exactly 2010-2017; 55 recordings with the
#   per-type counts read by whale-stage0-v3; total elements within 0.5% of Table S1.
# Gate B (Code S1 reproduction): at theta 0.5 our mean sub-sequence Zipf R^2 equals the
#   value Code S1 prints, 0.9302888665216734 (within 1e-6), and the number of
#   (song type, sub-sequence) types equals the 3,386 observations of its brevity model.
#   If Gate B fails, everything is still computed and published as "our implementation on
#   their data", with no headline (PREREG-AMENDMENT-3 section 5.2).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import ast
import csv
import hashlib
import io
import json
import os
import sys
import time
from collections import Counter

VERSION = "whale-run-5"
S2_NAME = "science.adq7055_data_s2.csv"
SONG_TYPES = list(range(2010, 2018))
# recordings per song_type as read by whale-stage0-v3 (row layout of Data S2)
EXPECTED_RECS = {2010: 4, 2011: 6, 2012: 6, 2013: 6, 2014: 7, 2015: 13, 2016: 6, 2017: 7}
TABLE_S1 = {2010: (4, 1053), 2011: (6, 2028), 2012: (6, 3351), 2013: (6, 2664),
            2014: (7, 5765), 2015: (12, 13251), 2016: (7, 8469), 2017: (7, 9179)}
TABLE_S1_TOTAL_ELEMENTS = 45760
TOTAL_TOL = 0.005
CODE_S1 = {"zipf_r2": 0.9302888665216734, "n_types": 3386, "tol": 1e-6}
# graded calibration outcomes used by whale_test.final_reading (PREREG-AMENDMENT-3 5.3)
CALIB2 = {"K5": True, "K6": False}     # RESULTS-CALIB-2.md
CALIB4 = {"Q10": True, "Q11": True}    # RESULTS-CALIB-4.md
PRIMARY_BREVITY_KEY = "brev_year"      # Code S1: one row per (song type, sub-sequence)
G1_PRIOR = 0.70                        # PREREG-AMENDMENT-5: Gate B passes


def find_s2(root):
    """Path of the first file named S2_NAME under root (sorted walk), or None."""
    for dp, dns, fns in os.walk(root):
        dns.sort()
        if S2_NAME in fns:
            return os.path.join(dp, S2_NAME)
    return None


def parse_s2(text):
    """CSV text of Data S2 -> ({song_type: [recording, ...]}, report).
    A recording is the list of sound-element codes in its `string` cell."""
    csv.field_size_limit(1 << 27)
    data = {}
    rep = {"n_rows": 0, "bad_rows": 0, "length_column_mismatch": 0}
    for row in csv.DictReader(io.StringIO(text)):
        rep["n_rows"] += 1
        try:
            seq = ast.literal_eval(row["string"])
            y = int(str(row["song_type"]).strip())
        except Exception:
            rep["bad_rows"] += 1
            continue
        if not isinstance(seq, list) or not all(isinstance(s, str) for s in seq):
            rep["bad_rows"] += 1
            continue
        try:
            if int(str(row.get("length", "")).strip()) != len(seq):
                rep["length_column_mismatch"] += 1
        except ValueError:
            rep["length_column_mismatch"] += 1
        data.setdefault(y, []).append(seq)
    rep["recordings"] = {str(y): len(data[y]) for y in sorted(data)}
    rep["elements"] = {str(y): sum(len(r) for r in data[y]) for y in sorted(data)}
    rep["total_elements"] = sum(rep["elements"].values())
    return data, rep


def gate_a(data, rep):
    """Data gate (PREREG-AMENDMENT-5 section 2). Returns (ok, reasons)."""
    why = []
    if rep["bad_rows"]:
        why.append("%d rows did not parse" % rep["bad_rows"])
    if sorted(data) != SONG_TYPES:
        why.append("song types %s" % sorted(data))
    else:
        for y in SONG_TYPES:
            if len(data[y]) != EXPECTED_RECS[y]:
                why.append("%d: %d recordings, expected %d" % (y, len(data[y]),
                                                               EXPECTED_RECS[y]))
    tot = sum(len(r) for recs in data.values() for r in recs)
    if abs(tot - TABLE_S1_TOTAL_ELEMENTS) > TOTAL_TOL * TABLE_S1_TOTAL_ELEMENTS:
        why.append("total elements %d, Table S1 %d" % (tot, TABLE_S1_TOTAL_ELEMENTS))
    return not why, why


def table_s1_compare(data):
    """Descriptive only: song_type counts next to Table S1's calendar-year counts."""
    out = {}
    for y, (nr, ne) in TABLE_S1.items():
        recs = data.get(y, [])
        out[str(y)] = {"recordings": len(recs), "table_s1_recordings": nr,
                       "elements": sum(len(r) for r in recs), "table_s1_elements": ne}
    return out


def code_s1_gate(zipf_r2, n_types):
    ok = (zipf_r2 == zipf_r2 and abs(zipf_r2 - CODE_S1["zipf_r2"]) <= CODE_S1["tol"]
          and n_types == CODE_S1["n_types"])
    return {"pass": bool(ok), "zipf_r2": zipf_r2, "n_types": n_types,
            "code_s1_zipf_r2": CODE_S1["zipf_r2"], "code_s1_n_types": CODE_S1["n_types"],
            "abs_diff": abs(zipf_r2 - CODE_S1["zipf_r2"]) if zipf_r2 == zipf_r2 else None}


def apply_gate_b(final, passed):
    """No headline for any statistic unless Gate B passed."""
    out = {}
    for stat, d in final.items():
        d = dict(d)
        d["notes"] = list(d.get("notes", []))
        if not passed:
            d["headline"] = False
            d["notes"].append("Code S1 not reproduced (Gate B): our implementation on "
                              "their data, no headline")
        out[stat] = d
    return out


REG_API = ("https://api.github.com/repos/munimtechnologies/song-zipf-test/commits"
           "?path=PREREG-AMENDMENT-5.md&per_page=1")


def registration(fetch=None, wait_minutes=45.0, sleep=time.sleep, poll_s=60):
    """Wait until PREREG-AMENDMENT-5.md is committed to GitHub; return its commit sha and
    UTC time, or {"found": False}. fetch(url) -> parsed JSON (injected in tests)."""
    if fetch is None:
        import urllib.request

        def fetch(url):
            req = urllib.request.Request(url, headers={"User-Agent": "mv2-song-zipf-test"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
    tries = max(1, int(wait_minutes * 60 // poll_s) + 1)
    for i in range(tries):
        try:
            js = fetch(REG_API)
            if isinstance(js, list) and js:
                return {"found": True, "sha": js[0]["sha"],
                        "utc": js[0]["commit"]["committer"]["date"], "polls": i + 1}
        except Exception:  # network hiccup: try again
            pass
        if i + 1 < tries:
            sleep(poll_s)
    return {"found": False, "polls": tries}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--max-minutes", type=float, default=150)
    ap.add_argument("--b-scale", type=float, default=1.0)
    ap.add_argument("--wait-minutes", type=float, default=45.0)
    a = ap.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import zipfseg as Z
    import whale_test as W
    os.makedirs(a.out_dir, exist_ok=True)
    reg = registration(wait_minutes=a.wait_minutes)
    reg["analysis_start_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(a.out_dir, "registration.json"), "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=1)
    print("REGISTRATION: %s" % json.dumps(reg))
    if not reg["found"]:
        print("PREREG-AMENDMENT-5.md not found on GitHub: nothing read, nothing computed.")
        return 4
    t0 = time.time()
    path = find_s2(a.data_dir)
    if path is None:
        print("DATA S2 NOT FOUND under %s" % a.data_dir)
        return 3
    with open(path, encoding="utf-8-sig") as f:
        data, rep = parse_s2(f.read())
    ok_a, why_a = gate_a(data, rep)
    rep.update({"gate_a": {"pass": ok_a, "reasons": why_a}, "data_sha256": sha256_file(path),
                "table_s1_compare": table_s1_compare(data),
                "code_sha256": {m: sha256_file(os.path.join(here, m)) for m in
                                ("whale_run.py", "whale_test.py", "whale_read.py",
                                 "zipfseg.py") if os.path.exists(os.path.join(here, m))}})
    with open(os.path.join(a.out_dir, "whale_read5_report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    if not ok_a:
        print("GATE A NOT PASSED: %s. No statistic computed." % "; ".join(why_a))
        return 0
    year_list = sorted(data)
    years = [data[y] for y in year_list]
    invs05 = W.inventories(W.segment_years(years, 0.5))
    zr = Z.nanmean([Z.zipf_r2(inv.values()) for inv in invs05])
    gb = code_s1_gate(zr, sum(len(inv) for inv in invs05))
    gb["sound_element_zipf_r2"] = Z.nanmean(
        [Z.zipf_r2(Counter(e for r in recs for e in r).values()) for recs in years])
    gb["sound_element_paper"] = 0.87
    print("GATE B (Code S1 reproduction): %s" % json.dumps(gb))
    deadline = t0 + 60 * a.max_minutes
    rows = {}
    s2 = None
    for th, rule, B in W.RUNS:
        row, invs = W.run_theta(years, th, max(1, int(round(B * a.b_scale))), deadline,
                                rule=rule)
        rows[W.run_key(th, rule)] = row
        if th == 0.5 and rule == "cur_over_prev":
            s2 = W.table_s2_check(year_list, invs)
            top = {str(y): [[list(k), v] for k, v in inv.most_common(15)]
                   for y, inv in zip(year_list, invs)}
            with open(os.path.join(a.out_dir, "whale_top15_theta0.5.json"), "w",
                      encoding="utf-8") as f:
                json.dump(top, f, indent=1)
    ho = W.heldout(years)
    g = W.grade(rows, s2, ho, PRIMARY_BREVITY_KEY)
    g_alt = W.grade(rows, s2, ho, "brev_pool")
    final = apply_gate_b(W.final_reading(g, CALIB2, CALIB4), gb["pass"])
    g1 = bool(gb["pass"])
    out = {"version": VERSION, "whale_test_version": W.VERSION,
           "python": sys.version.split()[0], "reader": "data_s2_song_type_literal_eval",
           "years": year_list, "n_recordings": [len(y) for y in years],
           "n_elements": [sum(len(r) for r in y) for y in years],
           "registration": reg, "gate_a": rep["gate_a"], "gate_b_code_s1": gb,
           "config": {"runs": [list(x) for x in W.RUNS], "b_scale": a.b_scale,
                      "seed": W.SEED, "nulls": list(W.NULL_ORDER),
                      "primary_brevity_key": PRIMARY_BREVITY_KEY,
                      "calib2": CALIB2, "calib4": CALIB4},
           "by_theta": rows, "table_s2": s2, "heldout_order2_minus_order1": ho,
           "grading": g, "grading_alternate_pool": g_alt,
           "g1": {"outcome": g1, "prior": G1_PRIOR},
           "brier_with_g1": (g["brier"] * len(g["predictions"])
                             + (G1_PRIOR - (1.0 if g1 else 0.0)) ** 2)
           / (len(g["predictions"]) + 1),
           "final_reading": final, "published": W.PUBLISHED,
           "elapsed_s": round(time.time() - t0, 1)}
    tmp = os.path.join(a.out_dir, "whale_results.json.%d.part" % os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    os.replace(tmp, os.path.join(a.out_dir, "whale_results.json"))
    print(json.dumps({"gate_b": gb["pass"], "labels": g["labels"],
                      "final": {k: (v["label"], v["headline"]) for k, v in final.items()},
                      "predictions": g["predictions"],
                      "table_s2_top1_years": s2["n_years_top1_match"],
                      "elapsed_s": out["elapsed_s"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
