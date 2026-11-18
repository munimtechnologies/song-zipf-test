# SPDX-License-Identifier: Apache-2.0
# cds_size.py: how much data does the song-zipf test need to find real human words?
# A size curve on child-directed English (Brent-Ratner), registered in CDS-SIZE-PREREG.md.
# Uses the registered pipeline unchanged: zipfseg.py (commit 742fd83) and cds_job.py
# (commit 83de8fd). MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import hashlib
import json
import os
import sys
import time

import cds_job as C
import zipfseg as z

VERSION = "cds-size-1"
ALPHA = 0.05
N_REC = 8                       # recordings per replicate (the whale design: 8 "years")
DESIGN = ((70, 5), (140, 5), (280, 4), (600, 2), (1200, 1))   # (utterances each, replicates)
SIZES = tuple(u for u, _ in DESIGN)
THETAS = (0.3, 0.5, 0.7)
B = 100
SEED = 20261118
WHALE_ELEMENTS_PER_YEAR = 5720
FINCH_SYLLABLES_PER_RECORDING = 676
BSO = "BEYOND_SECOND_ORDER"
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/main/"
              "CDS-SIZE-PREREG.md")
PRIORS = {"Z1": 0.75, "Z2": 0.75, "Z3": 0.75, "Z4": 0.50, "Z5": 0.85, "Z6": 0.85, "Z7": 0.40}


def check_design(n_utt):
    """Every replicate of every size must fit in the corpus without overlap."""
    return all(r * N_REC * u <= n_utt for u, r in DESIGN)


def seed_for(u, r):
    return SEED + 10000 * r + u


def replicate_blocks(utts, u, r):
    """Replicate r of size u: N_REC consecutive blocks of u utterances, starting at
    utterance r * N_REC * u. Replicates of one size never overlap."""
    return C.blocks(utts, r * N_REC * u, N_REC, u)


def run_one(utts, u, r, b=B, thetas=THETAS):
    blocks = replicate_blocks(utts, u, r)
    recs = [C.to_recording(bl) for bl in blocks]
    res = z.analyze(recs, thetas=thetas, B=b, seed=seed_for(u, r))
    rows = res["by_theta"]
    d1 = res["heldout_ll_order2_minus_order1"]
    out = {"u": u, "rep": r, "seed": seed_for(u, r), "B": b,
           "start_utt": r * N_REC * u,
           "phonemes": sum(len(x) for rec in recs for x in rec),
           "labels": {th: z.decision(row) for th, row in rows.items()},
           "real": {th: row["real_mean_r2"] for th, row in rows.items()},
           "m2": {th: {k: row["nulls"]["markov2_pooled"][k]
                       for k in ("null_mean", "z", "p")} for th, row in rows.items()},
           "m1_p": {th: row["nulls"]["markov1_pooled"]["p"] for th, row in rows.items()},
           "published_controls_p": {th: [row["nulls"]["shuffle"]["p"],
                                         row["nulls"]["rotate"]["p"]]
                                    for th, row in rows.items()},
           "d1_n_favour": d1["n_favour_order2"], "d1_mean": d1["mean"],
           "d1_majority": 2 * d1["n_favour_order2"] > len(recs),
           "boundary_f1_0.5": C.boundary_scores(blocks, 0.5)["f1"]}
    out["phonemes_per_recording"] = out["phonemes"] / len(recs)
    return out


def aggregate(rows):
    agg = {}
    for u in SIZES:
        rs = [x for x in rows if x["u"] == u]
        if not rs:
            continue
        n = len(rs)
        agg[str(u)] = {
            "n_rep": n,
            "phonemes_per_recording_mean": sum(x["phonemes_per_recording"] for x in rs) / n,
            "detect": {th: sum(1 for x in rs if x["labels"][th] == BSO) / n
                       for th in rs[0]["labels"]},
            "d1_majority_rate": sum(1 for x in rs if x["d1_majority"]) / n,
            "m2_z_mean_0.5": sum(x["m2"]["0.5"]["z"] for x in rs) / n,
        }
    return agg


def size_threshold(agg):
    """Smallest size whose detection rate at theta 0.5 is >= 0.5 (None if none)."""
    for u in SIZES:
        a = agg.get(str(u))
        if a and a["detect"]["0.5"] >= 0.5:
            return u
    return None


def d1_tracks(rows):
    yes = [x for x in rows if x["d1_majority"]]
    no = [x for x in rows if not x["d1_majority"]]
    if not yes or not no:
        return "UNDETERMINED", None, None
    ry = sum(1 for x in yes if x["labels"]["0.5"] == BSO) / len(yes)
    rn = sum(1 for x in no if x["labels"]["0.5"] == BSO) / len(no)
    lab = "D1_TRACKS_DETECTION" if (ry >= 0.5 and rn <= 0.2) else "D1_DOES_NOT_TRACK"
    return lab, ry, rn


def grade(rows):
    agg = aggregate(rows)
    det = {u: agg[str(u)]["detect"]["0.5"] for u in SIZES}
    d1 = {u: agg[str(u)]["d1_majority_rate"] for u in SIZES}
    ustar = size_threshold(agg)
    g = {
        "Z1": det[70] <= 0.2,
        "Z2": det[600] >= 0.5,
        "Z3": det[1200] == 1.0,
        "Z4": all(det[a] <= det[b] for a, b in zip(SIZES, SIZES[1:])),
        "Z5": d1[70] == 0.0,
        "Z6": d1[600] == 1.0 and d1[1200] == 1.0,
        "Z7": ustar is not None and ustar <= 280,
    }
    lab, ry, rn = d1_tracks(rows)
    ppr = agg[str(ustar)]["phonemes_per_recording_mean"] if ustar is not None else None
    rules = {
        "T1_threshold_utterances": ustar,
        "T1_threshold_phonemes_per_recording": ppr,
        "T1_label": "NO_THRESHOLD_IN_RANGE" if ustar is None else "THRESHOLD_FOUND",
        "T2": lab, "T2_detect_rate_d1_majority": ry, "T2_detect_rate_d1_minority": rn,
        "T3_whale_size_within_detecting_range": (ppr is not None
                                                 and ppr <= WHALE_ELEMENTS_PER_YEAR),
        "T3_finch_size_within_detecting_range": (ppr is not None
                                                 and ppr <= FINCH_SYLLABLES_PER_RECORDING),
    }
    brier = sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in PRIORS) / len(PRIORS)
    return {"aggregate": agg, "predictions": g, "rules": rules, "priors": PRIORS,
            "brier": brier}


def wait_for_registration(max_minutes, fetcher=None):
    fetcher = fetcher or C.fetch
    t0 = time.time()
    tries = 0
    last = None
    while True:
        tries += 1
        try:
            blob = fetcher(PREREG_URL)
            if b"CDS-SIZE-PREREG" in blob:
                return {"found": True, "tries": tries,
                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "sha256": hashlib.sha256(blob).hexdigest()}
        except Exception as e:                      # 404 until published
            last = repr(e)[:200]
        if time.time() - t0 > max_minutes * 60:
            return {"found": False, "tries": tries, "last_error": last}
        time.sleep(60)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data/cds")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--B", type=int, default=B)
    ap.add_argument("--wait-minutes", type=float, default=60)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    out_path = os.path.join(a.out_dir, "cds_size_results.json")
    out = {"version": VERSION, "python": sys.version.split()[0],
           "zipfseg_sha256": hashlib.sha256(open(z.__file__, "rb").read()).hexdigest(),
           "cds_job_sha256": hashlib.sha256(open(C.__file__, "rb").read()).hexdigest(),
           "design": {"n_rec": N_REC, "design": [list(d) for d in DESIGN], "B": a.B,
                      "thetas": list(THETAS), "seed": SEED}}

    def save():
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)

    reg = wait_for_registration(a.wait_minutes)
    out["registration"] = reg
    if not reg["found"]:
        out["status"] = "not_run_unregistered"
        save()
        print("CDS-SIZE-PREREG.md not public; nothing analysed")
        return 4
    utts, info = C.load_corpus(a.data_dir)
    out["corpus"] = info
    if utts is None or not check_design(len(utts)):
        out["status"] = "gate_fail_or_no_data"
        save()
        print("corpus not usable:", json.dumps(info.get("attempts", []))[:2000])
        return 0
    out["status"] = "running"
    out["replicates"] = []
    t0 = time.time()
    for u, n_rep in DESIGN:
        for r in range(n_rep):
            row = run_one(utts, u, r, b=a.B)
            row["seconds_since_start"] = time.time() - t0
            out["replicates"].append(row)
            save()
            print("u=%d rep=%d label0.5=%s p2=%.4f d1=%d/8 (%.0f s)" % (
                u, r, row["labels"]["0.5"], row["m2"]["0.5"]["p"], row["d1_n_favour"],
                row["seconds_since_start"]), flush=True)
    out["grading"] = grade(out["replicates"])
    out["status"] = "ok"
    out["seconds"] = time.time() - t0
    save()
    gr = out["grading"]
    print(json.dumps({"predictions": gr["predictions"], "rules": gr["rules"],
                      "brier": gr["brier"],
                      "detect_0.5": {u: v["detect"]["0.5"] for u, v in gr["aggregate"].items()},
                      "d1_majority": {u: v["d1_majority_rate"]
                                      for u, v in gr["aggregate"].items()}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
