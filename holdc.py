# SPDX-License-Identifier: Apache-2.0
# holdc.py: does humpback song keep structure beyond second order once its repeats are
# removed? (HOLDC-PREREG.md, song-zipf-test). HOLD found whale song beyond a second-order
# chain on held-out song (p = 0.005); RUNS found that the song repeats its cells far more
# than its own second-order chain does (63% of elements removable against 50%). This job
# runs HOLD's held-out test (hold.test_set, unchanged) on the song with every tandem repeat
# collapsed (runs.collapse, unchanged), against second-order chains generated under the
# same collapse rule (runs.collapsed_markov), with three controls fixed in advance:
#   * English (Brent-Ratner), collapsed the same way, in recordings size-matched to the
#     collapsed whale years (positive control: real units, same size);
#   * repetition-only song: square-free second-order surrogates of the collapsed whale,
#     re-inflated with random tandem repeats (does repetition alone fool HOLD, and does
#     collapsing undo that?);
#   * negative controls: collapse-consistent second-order surrogates.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
"""hold.py (4e73d8a) and runs.py (bdd0203) are imported unchanged; zipfseg.py, cds_job.py
and whale_run.py (fetched at pinned commits by setup_holdc.sh) are imported only inside
main(), so the tests need only hold.py and runs.py."""
import argparse
import hashlib
import json
import os
import random
import sys
import time

import hold as H
import runs as R

VERSION = "holdc-1"
SEED = 20261121
LMAX = 8
ALPHA = 0.05
B_WHALE = 1000
B_NEG = 200
B_REP = 200
B_EN = 100
N_REP = 3
N_EN = 5
EN_STRIDE = 1850
Q = 0.35          # repetition-only song: chance of a repeat after each symbol
CELL_MAX = 4      # cell length L uniform on 1..CELL_MAX
COPIES_MAX = 3    # extra copies r uniform on 1..COPIES_MAX
BSO = H.BSO       # "BEYOND_SECOND_ORDER_HELDOUT"
R1_BEYOND = "BEYOND_SECOND_ORDER_AFTER_COLLAPSE_HELDOUT"
R1_NOT = "NOT_DETECTED_WITH_POWER"
FOOLS = "REPETITION_FOOLS_HOLD"
NOT_FOOLS = "REPETITION_DOES_NOT_FOOL_HOLD"
PRIORS = {"Q1": 0.55, "Q2": 0.85, "Q3": 0.85, "Q4": 0.85, "Q5": 0.80, "Q6": 0.75,
          "Q7": 0.50}
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/main/"
              "HOLDC-PREREG.md")


# --------------------------------------------------------------------------
# building blocks
# --------------------------------------------------------------------------
def surc(rec, rng):
    """Collapse-consistent pooled second-order surrogate of one recording."""
    return R.collapsed_markov(rec, 2, rng, LMAX)


def n_sym(recs):
    return [sum(len(b) for b in rec) for rec in recs]


def collapse_all(recs):
    return [R.collapse_rec(rec, LMAX) for rec in recs]


def inflate(seq, rng, q=Q, cell_max=CELL_MAX, copies_max=COPIES_MAX):
    """Repetition-only song: after each symbol, with probability q, the last L symbols
    (L uniform on 1..min(cell_max, length so far)) are sung r more times (r uniform on
    1..copies_max)."""
    out = []
    for s in seq:
        out.append(s)
        if rng.random() < q:
            L = rng.randint(1, min(cell_max, len(out)))
            r = rng.randint(1, copies_max)
            cell = out[-L:]
            for _ in range(r):
                out.extend(cell)
    return out


def size_matched(utts, start, targets):
    """Recordings of consecutive utterances (bouts; phonemes as symbols, word spaces
    removed as in cds_job.to_recording) from utterance `start`; recording i takes
    utterances until it holds at least targets[i] phonemes. Empty utterances are skipped.
    Returns (recordings, next utterance), or (None, position) if the corpus runs out."""
    pos = start
    recs = []
    for t in targets:
        rec, n = [], 0
        while n < t:
            if pos >= len(utts):
                return None, pos
            b = list("".join(utts[pos]))
            pos += 1
            if b:
                rec.append(b)
                n += len(b)
        recs.append(rec)
    return recs, pos


# --------------------------------------------------------------------------
# the registered analyses
# --------------------------------------------------------------------------
def run_whale_sets(years, b_real=B_WHALE, b_neg=B_NEG):
    """years: list (8) of recordings (lists of bouts) of the ORIGINAL song."""
    W = collapse_all(years)
    out = {"elements": n_sym(years), "elements_collapsed": n_sym(W),
           "real": H.test_set(W, b_real, SEED + 1, surc),
           "neg": H.test_set(H.neg_dataset(W, SEED + 2, surc), b_neg, SEED + 3, surc)}
    return out, W


def rep_control(W, i, sur2, b=B_REP):
    """Repetition-only song built from the collapsed whale W; HOLD on it as registered
    (Markov-2 surrogates, sur2) and HOLD-C on its collapse (collapse-consistent
    surrogates)."""
    s = SEED + 100 * (i + 1)
    base = H.neg_dataset(W, s, surc)
    rng = random.Random(s + 1)
    inf = [[inflate(bt, rng) for bt in rec] for rec in base]
    col = collapse_all(inf)
    nb = sum(len(rec) for rec in base)
    same = sum(1 for rb, rc in zip(base, col) for x, y in zip(rb, rc) if list(x) == list(y))
    return {"i": i, "seed": s, "elements_base": n_sym(base),
            "elements_inflated": n_sym(inf), "elements_collapsed": n_sym(col),
            "share_removed": H.mean([R.share_removed(rec, LMAX) for rec in inf]),
            "bouts_recovered": same / nb if nb else float("nan"),
            "uncollapsed": H.test_set(inf, b, s + 2, sur2),
            "collapsed": H.test_set(col, b, s + 3, surc)}


def en_replicate(utts, r, targets, b=B_EN):
    recs, end = size_matched(utts, r * EN_STRIDE, targets)
    row = {"rep": r, "start_utt": r * EN_STRIDE}
    if recs is None:
        row["status"] = "corpus_exhausted"
        return row
    col = collapse_all(recs)
    s = SEED + 10000 * (r + 1)
    row.update({"status": "ok", "end_utt": end, "phonemes": n_sym(recs),
                "phonemes_collapsed": n_sym(col),
                "real": H.test_set(col, b, s, surc),
                "neg": H.test_set(H.neg_dataset(col, s + 1, surc), b, s + 2, surc)})
    return row


# --------------------------------------------------------------------------
# grading (HOLDC-PREREG.md sections 6 and 7)
# --------------------------------------------------------------------------
def det(t):
    return t["p"] < ALPHA


def grade(res):
    w = res.get("whale") or {}
    ok = w.get("status") == "ok"
    en = [x for x in (res.get("english") or []) if x.get("status") == "ok"]
    rp = res.get("repetition") or []
    en_full = len(en) == N_EN
    rp_full = len(rp) == N_REP
    en_real = sum(1 for x in en if det(x["real"]))
    en_neg = sum(1 for x in en if det(x["neg"]))
    rp_unc = sum(1 for x in rp if det(x["uncollapsed"]))
    rp_col = sum(1 for x in rp if det(x["collapsed"]))
    w_neg = det(w["neg"]) if ok else None
    if not (ok and en_full and rp_full):
        control = "CALIBRATION_INCOMPLETE"
    elif en_real >= 4 and en_neg <= 1 and not w_neg and rp_col <= 1:
        control = "CONTROL_OK"
    else:
        control = "CONTROL_FAILED"
    g = dict.fromkeys(sorted(PRIORS))
    if en_full:
        g["Q2"] = en_real >= 4
        g["Q3"] = en_neg <= 1
    if rp_full:
        g["Q5"] = rp_unc >= 2
        g["Q6"] = rp_col == 0
    if ok:
        g["Q1"] = det(w["real"])
        g["Q4"] = not w_neg
        g["Q7"] = w["real"]["mean_gain"] > 0
        if control != "CONTROL_OK":
            r1 = control
        elif det(w["real"]):
            r1 = R1_BEYOND
        else:
            r1 = R1_NOT
    else:
        r1 = "WHALE_DATA_MISSING"
    r2 = "INCOMPLETE" if not rp_full else (FOOLS if rp_unc >= 2 else NOT_FOOLS)
    scored = [k for k in sorted(PRIORS) if g[k] is not None]
    brier = (sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in scored) / len(scored)
             if scored else None)
    return {"rules": {"R1_whale_after_collapse": r1, "R2_repetition_alone": r2,
                      "control": control, "english_detected": en_real,
                      "english_negative_detected": en_neg,
                      "repetition_uncollapsed_detected": rp_unc,
                      "repetition_collapsed_detected": rp_col,
                      "whale_negative_detected": w_neg},
            "predictions": g, "priors": dict(PRIORS), "brier": brier,
            "n_scored": len(scored)}


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
            if b"HOLDC-PREREG" in blob:
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
    out_path = os.path.join(a.out_dir, "holdc_results.json")
    out = {"version": VERSION, "python": sys.version.split()[0],
           "code_sha256": {m: sha_file(os.path.join(here, m)) for m in
                           ("holdc.py", "hold.py", "runs.py", "zipfseg.py", "cds_job.py",
                            "whale_run.py") if os.path.exists(os.path.join(here, m))},
           "config": {"seed": SEED, "lmax": LMAX, "alpha": ALPHA, "b_whale": B_WHALE,
                      "b_neg": B_NEG, "b_rep": B_REP, "b_en": B_EN, "n_rep": N_REP,
                      "n_en": N_EN, "en_stride": EN_STRIDE, "q": Q, "cell_max": CELL_MAX,
                      "copies_max": COPIES_MAX, "kmax": H.K_MAX},
           "english": [], "repetition": []}

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
        print("HOLDC-PREREG.md not public; nothing analysed")
        return 4
    t0 = time.time()

    def late():
        return time.time() - t0 > a.max_minutes * 60

    def sur2(rec, rng):
        return Z.markov_recording(rec, 2, rng)

    # ---- whale (main test) ----
    w = out["whale"] = {}
    W = None
    path = WR.find_s2(a.whale_dir)
    if path is None:
        w["status"] = "missing"
    else:
        with open(path, encoding="utf-8-sig") as f:
            data, rep = WR.parse_s2(f.read())
        okg, why = WR.gate_a(data, rep)
        w.update({"data_sha256": sha_file(path), "gate_a": {"pass": okg, "reasons": why}})
        if not okg:
            w["status"] = "gate_fail"
        else:
            w["years"] = sorted(data)
            res, W = run_whale_sets([data[y] for y in sorted(data)])
            w.update(res)
            w["status"] = "ok"
    save()
    if W is not None:
        print("WHALE collapsed: gain %.4f null %.4f p %.4f %s | meanH %s | neg p %.4f (%.0f s)"
              % (w["real"]["mean_gain"], w["real"]["null_mean"], w["real"]["p"],
                 w["real"]["label"], [round(x, 3) for x in w["real"]["mean_H"]],
                 w["neg"]["p"], time.time() - t0), flush=True)
    else:
        print("WHALE status:", w.get("status"), flush=True)

    # ---- English, size-matched to the collapsed whale years ----
    utts, info = C.load_corpus(a.cds_dir)
    out["corpus"] = info
    if utts is None:
        out["status"] = "cds_gate_fail_or_no_data"
    elif W is not None:
        targets = n_sym(W)
        for r in range(N_EN):
            if late():
                break
            row = en_replicate(utts, r, targets)
            row["seconds_since_start"] = round(time.time() - t0, 1)
            out["english"].append(row)
            save()
            if row["status"] == "ok":
                print("EN %d real gain %.4f p %.4f | neg p %.4f (%.0f s)" % (
                    r, row["real"]["mean_gain"], row["real"]["p"], row["neg"]["p"],
                    row["seconds_since_start"]), flush=True)
            else:
                print("EN %d %s" % (r, row["status"]), flush=True)

    # ---- repetition-only song ----
    if W is not None:
        for i in range(N_REP):
            if late():
                break
            row = rep_control(W, i, sur2)
            row["seconds_since_start"] = round(time.time() - t0, 1)
            out["repetition"].append(row)
            save()
            print("REP %d removed %.3f recovered %.3f | uncollapsed p %.4f | collapsed p %.4f"
                  " (%.0f s)" % (i, row["share_removed"], row["bouts_recovered"],
                                 row["uncollapsed"]["p"], row["collapsed"]["p"],
                                 row["seconds_since_start"]), flush=True)

    if W is None:
        out["status"] = "whale_" + str(w.get("status"))
    elif "status" not in out:
        complete = (len(out["english"]) == N_EN and len(out["repetition"]) == N_REP)
        out["status"] = "ok" if complete else "timeout_partial"
    out["grading"] = grade(out)
    out["seconds"] = round(time.time() - t0, 1)
    save()
    print(json.dumps({"status": out["status"], "grading": out["grading"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
