# SPDX-License-Identifier: Apache-2.0
# hold.py: a held-out prediction test for structure beyond second order in song
# (HOLD-PREREG.md, song-zipf-test). Does knowing more than the last two symbols help
# predict UNSEEN song? Leave-one-bout-out cross-entropy (bits per symbol) of
# interpolated Witten-Bell n-gram models of order 0..5, compared with the same
# quantity on pooled second-order Markov surrogates (zipfseg.markov_recording, the
# null the Zipf test used). Calibrated on child-directed English (the 17 replicates
# of CDS-SIZE, where words are known to exist), with Markov-2 negative controls, then
# applied to the 8 years of humpback song of Arnon et al. 2025 (Science 387:649).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
"""Core functions are pure standard-library Python; the pipeline modules
(zipfseg.py, cds_job.py, whale_run.py, fetched at pinned commits by setup_hold.sh)
are imported only inside main(), so the tests run anywhere."""
import argparse
import hashlib
import json
import math
import os
import random
import sys
import time
from collections import Counter

VERSION = "hold-1"
K_MAX = 5
ALPHA = 0.05
SEED = 20261119
B_CDS = 100
B_WHALE = 200
N_REC = 8
DESIGN = ((70, 5), (140, 5), (280, 4), (600, 2), (1200, 1))   # identical to CDS-SIZE
SIZES = tuple(u for u, _ in DESIGN)
# Zipf-vs-Markov-2 labels (theta 0.5) of the SAME 17 English replicates, as graded in
# RESULTS-CDS-SIZE.md (commit a54379f): True = BEYOND_SECOND_ORDER.
ZIPF_BSO = {(70, 0): False, (70, 1): False, (70, 2): False, (70, 3): False,
            (70, 4): False, (140, 0): False, (140, 1): True, (140, 2): False,
            (140, 3): False, (140, 4): False, (280, 0): True, (280, 1): True,
            (280, 2): True, (280, 3): True, (600, 0): True, (600, 1): True,
            (1200, 0): True}
WHALE_ELEMENTS_PER_YEAR = 5720
BSO = "BEYOND_SECOND_ORDER_HELDOUT"
ND = "NOT_DETECTED"
PRIORS = {"H1": 0.45, "H2": 0.80, "H3": 0.55, "H4": 0.85, "H5": 0.85, "H6": 0.60,
          "H7": 0.60, "H8": 0.90, "H9": 0.60}
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/main/"
              "HOLD-PREREG.md")


# --------------------------------------------------------------------------
# n-gram counts and interpolated Witten-Bell probabilities
# --------------------------------------------------------------------------
def ngram_counts(bouts, kmax):
    """{context tuple: Counter(next symbol)} for context lengths 0..kmax.
    Contexts never cross a bout boundary: at position i only the last
    min(i, kmax) symbols of the same bout are used."""
    F = {}
    for b in bouts:
        for i, w in enumerate(b):
            for j in range(min(i, kmax) + 1):
                h = tuple(b[i - j:i])
                c = F.get(h)
                if c is None:
                    c = F[h] = Counter()
                c[w] += 1
    return F


class Stats:
    """Leave-one-bout-out view: training counts = F (all bouts) minus D (held-out bout)."""

    def __init__(self, F, D, tot=None, types=None):
        self.F = F
        self.D = D
        self.tot = tot if tot is not None else {h: sum(c.values()) for h, c in F.items()}
        self.types = types if types is not None else {h: len(c) for h, c in F.items()}
        self.cache = {}
        self.V = self.ctx(())[1]

    def ctx(self, h):
        """(training count of context h, number of distinct training successors)."""
        r = self.cache.get(h)
        if r is None:
            f = self.F.get(h)
            if f is None:
                r = (0, 0)
            else:
                d = self.D.get(h)
                if d is None:
                    r = (self.tot[h], self.types[h])
                else:
                    r = (self.tot[h] - sum(d.values()),
                         self.types[h] - sum(1 for s, v in d.items() if f[s] == v))
            self.cache[h] = r
        return r

    def count(self, h, w):
        f = self.F.get(h)
        if f is None:
            return 0
        d = self.D.get(h)
        return f.get(w, 0) - (d.get(w, 0) if d is not None else 0)


def probs_all_orders(w, hist, kmax, st):
    """[P_0(w), ..., P_kmax(w)]; order k uses the last min(k, len(hist)) symbols.
    P_{-1} is uniform over the training alphabet plus one slot for unseen symbols;
    P_j(w|h) = (c(h,w) + T(h) P_{j-1}(w)) / (c(h) + T(h)), or P_{j-1} if c(h) = 0."""
    p = 1.0 / (st.V + 1)
    out = []
    alive = True
    n = len(hist)
    for j in range(kmax + 1):
        if alive and j <= n:
            h = hist[n - j:]
            c, t = st.ctx(h)
            if c > 0:
                p = (st.count(h, w) + t * p) / (c + t)
            else:
                alive = False
        out.append(p)
    return out


def heldout_entropy(bouts, kmax=K_MAX):
    """Leave-one-bout-out cross-entropy in bits per symbol for orders 0..kmax.
    Every symbol of every bout is scored by every order."""
    F = ngram_counts(bouts, kmax)
    tot = {h: sum(c.values()) for h, c in F.items()}
    types = {h: len(c) for h, c in F.items()}
    acc = [0.0] * (kmax + 1)
    n = 0
    for b in bouts:
        st = Stats(F, ngram_counts([b], kmax), tot, types)
        if st.V == 0:
            continue                      # nothing to train on (single-bout recording)
        for i, w in enumerate(b):
            ps = probs_all_orders(w, tuple(b[max(0, i - kmax):i]), kmax, st)
            for k in range(kmax + 1):
                acc[k] -= math.log2(ps[k])
            n += 1
    if n == 0:
        return [float("nan")] * (kmax + 1)
    return [a / n for a in acc]


def gain(H):
    """Bits per symbol saved on unseen song by the best order 3..kmax over order 2."""
    return H[2] - min(H[3:])


def argmin(v):
    return min(range(len(v)), key=lambda i: (v[i], i))


def mean(v):
    return sum(v) / len(v) if v else float("nan")


def sd(v):
    if not v:
        return float("nan")
    m = mean(v)
    return math.sqrt(sum((a - m) ** 2 for a in v) / len(v))


def pval(real, nulls):
    """One-sided empirical p (null >= real) with +1 correction."""
    return (1 + sum(1 for a in nulls if a >= real)) / (1 + len(nulls))


# --------------------------------------------------------------------------
# the test
# --------------------------------------------------------------------------
def test_set(recordings, B, seed, surrogate, kmax=K_MAX):
    """Mean held-out gain over recordings vs the same mean over B surrogate sets.
    surrogate(recording, rng) -> recording; recording i uses Random(seed*100 + i)."""
    per = []
    nulls_by_rec = []
    for i, rec in enumerate(recordings):
        H = heldout_entropy(rec, kmax)
        g = gain(H)
        rng = random.Random(seed * 100 + i)
        nulls = [gain(heldout_entropy(surrogate(rec, rng), kmax)) for _ in range(B)]
        nulls_by_rec.append(nulls)
        per.append({"H": H, "gain": g, "p": pval(g, nulls), "null_mean": mean(nulls),
                    "null_sd": sd(nulls), "best_order": argmin(H),
                    "symbols": sum(len(x) for x in rec), "bouts": len(rec)})
    gm = mean([r["gain"] for r in per])
    null_means = [mean([nl[b] for nl in nulls_by_rec]) for b in range(B)]
    p = pval(gm, null_means)
    return {"B": B, "seed": seed, "kmax": kmax, "mean_gain": gm, "p": p,
            "label": BSO if p < ALPHA else ND, "null_mean": mean(null_means),
            "null_sd": sd(null_means),
            "mean_H": [mean([r["H"][k] for r in per]) for k in range(kmax + 1)],
            "per_recording": per}


def markov2(z):
    return lambda rec, rng: z.markov_recording(rec, 2, rng)


def seed_for(u, r):
    return SEED + 10000 * r + u


def neg_dataset(recordings, seed, surrogate):
    """Negative control: each recording replaced by one Markov-2 surrogate of itself."""
    return [surrogate(rec, random.Random(seed * 100 + i)) for i, rec in enumerate(recordings)]


# --------------------------------------------------------------------------
# grading (HOLD-PREREG.md sections 6 and 7)
# --------------------------------------------------------------------------
def detect_rates(rows, key):
    out = {}
    for u in SIZES:
        rs = [x for x in rows if x["u"] == u]
        if rs:
            out[u] = sum(1 for x in rs if x[key]["label"] == BSO) / len(rs)
    return out


def zipf_detect():
    out = {}
    for u in SIZES:
        v = [ZIPF_BSO[k] for k in sorted(ZIPF_BSO) if k[0] == u]
        out[u] = sum(1 for a in v if a) / len(v)
    return out


def power_label(det_h, det_z):
    if any(u not in det_h for u in SIZES):
        return "INCOMPLETE"
    ge = all(det_h[u] >= det_z[u] for u in SIZES)
    le = all(det_h[u] <= det_z[u] for u in SIZES)
    if ge and le:
        return "HOLD_EQUAL"
    if ge:
        return "HOLD_MORE_POWERFUL"
    if le:
        return "HOLD_LESS_POWERFUL"
    return "MIXED"


def grade(rows, whale):
    """rows: CDS replicates {"u","rep","phonemes_per_recording","real","neg"};
    whale: {"status": "ok"|..., "real": test_set out, "neg": test_set out}."""
    complete = sorted((x["u"], x["rep"]) for x in rows) == sorted(ZIPF_BSO)
    det_h = detect_rates(rows, "real")
    det_z = zipf_detect()
    n_neg = sum(1 for x in rows if x["neg"]["label"] == BSO)
    ustar = None
    ppr = None
    if complete:
        for u in SIZES:
            if det_h[u] >= 0.5:
                ustar = u
                break
        if ustar is not None:
            ppr = mean([x["phonemes_per_recording"] for x in rows if x["u"] == ustar])
    r3 = ("INCOMPLETE" if not complete else
          ("CONTROL_OK" if n_neg <= 2 else "CONTROL_FAILED"))
    g = {"H1": det_h[70] >= 0.6 if complete else None,
         "H2": (det_h[280] == 1.0 and det_h[600] == 1.0 and det_h[1200] == 1.0)
         if complete else None,
         "H3": power_label(det_h, det_z) == "HOLD_MORE_POWERFUL" if complete else None,
         "H4": n_neg <= 2 if complete else None}
    w_ok = bool(whale) and whale.get("status") == "ok"
    if w_ok:
        wr = whale["real"]
        mh = wr["mean_H"]
        g["H5"] = wr["p"] < ALPHA
        g["H6"] = sum(1 for r in wr["per_recording"] if r["p"] < ALPHA) >= 6
        g["H7"] = argmin(mh) >= 3
        g["H8"] = whale["neg"]["label"] != BSO
        g["H9"] = mh[2] < mh[1]
        if r3 == "INCOMPLETE":
            r4 = "CALIBRATION_INCOMPLETE"
        elif r3 == "CONTROL_FAILED":
            r4 = "CONTROL_FAILED"
        elif wr["p"] < ALPHA:
            r4 = BSO
        elif ppr is not None and ppr <= WHALE_ELEMENTS_PER_YEAR:
            r4 = "NOT_DETECTED_WITH_POWER"
        else:
            r4 = "NOT_DETECTED_UNDERPOWERED"
    else:
        for k in ("H5", "H6", "H7", "H8", "H9"):
            g[k] = None
        r4 = "WHALE_DATA_MISSING"
    rules = {"R1_power_vs_zipf": power_label(det_h, det_z) if complete else "INCOMPLETE",
             "R2_threshold_utterances": ustar,
             "R2_threshold_phonemes_per_recording": ppr,
             "R3_negative_control": r3, "R3_negative_positives": n_neg,
             "R4_whale": r4}
    scored = [k for k in PRIORS if g.get(k) is not None]
    brier = (sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in scored) / len(scored)
             if scored else None)
    return {"complete": complete, "detect_hold": {str(u): v for u, v in det_h.items()},
            "detect_zipf": {str(u): v for u, v in det_z.items()},
            "predictions": g, "rules": rules, "priors": PRIORS, "brier": brier,
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
            if b"HOLD-PREREG" in blob:
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


def run_whale(whale_dir, WR, sur, b):
    path = WR.find_s2(whale_dir)
    if path is None:
        return {"status": "missing", "dir": whale_dir}
    with open(path, encoding="utf-8-sig") as f:
        data, rep = WR.parse_s2(f.read())
    ok, why = WR.gate_a(data, rep)
    out = {"data_sha256": sha_file(path), "gate_a": {"pass": ok, "reasons": why},
           "recordings": rep.get("recordings"), "elements": rep.get("elements")}
    if not ok:
        out["status"] = "gate_fail"
        return out
    years = [data[y] for y in sorted(data)]
    out["years"] = sorted(data)
    out["real"] = test_set(years, b, SEED + 1, sur)
    out["neg"] = test_set(neg_dataset(years, SEED + 2, sur), b, SEED + 3, sur)
    out["status"] = "ok"
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cds-dir", default="/data/cds")
    ap.add_argument("--whale-dir", default="/data/song/whale")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--b-cds", type=int, default=B_CDS)
    ap.add_argument("--b-whale", type=int, default=B_WHALE)
    ap.add_argument("--wait-minutes", type=float, default=60)
    ap.add_argument("--max-minutes", type=float, default=270)
    a = ap.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import zipfseg as z
    import cds_job as C
    import whale_run as WR
    os.makedirs(a.out_dir, exist_ok=True)
    out_path = os.path.join(a.out_dir, "hold_results.json")
    out = {"version": VERSION, "python": sys.version.split()[0],
           "code_sha256": {m: sha_file(os.path.join(here, m)) for m in
                           ("hold.py", "zipfseg.py", "cds_job.py", "whale_run.py")
                           if os.path.exists(os.path.join(here, m))},
           "config": {"kmax": K_MAX, "alpha": ALPHA, "seed": SEED, "b_cds": a.b_cds,
                      "b_whale": a.b_whale, "design": [list(d) for d in DESIGN],
                      "n_rec": N_REC}}

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
        print("HOLD-PREREG.md not public; nothing analysed")
        return 4
    t0 = time.time()
    sur = markov2(z)
    out["whale"] = run_whale(a.whale_dir, WR, sur, a.b_whale)
    save()
    w = out["whale"]
    if w["status"] == "ok":
        print("WHALE real p=%.4f gain=%.4f meanH=%s | neg p=%.4f (%.0f s)" % (
            w["real"]["p"], w["real"]["mean_gain"],
            [round(x, 3) for x in w["real"]["mean_H"]], w["neg"]["p"], time.time() - t0),
            flush=True)
    else:
        print("WHALE status:", w["status"], flush=True)
    utts, info = C.load_corpus(a.cds_dir)
    out["corpus"] = info
    rows = out["replicates"] = []
    if utts is None:
        out["status"] = "cds_gate_fail_or_no_data"
    else:
        out["status"] = "running"
        for u, n_rep in DESIGN:
            for r in range(n_rep):
                if time.time() - t0 > a.max_minutes * 60:
                    out["status"] = "timeout_partial"
                    break
                blocks = C.blocks(utts, r * N_REC * u, N_REC, u)
                recs = [C.to_recording(bl) for bl in blocks]
                s = seed_for(u, r)
                row = {"u": u, "rep": r, "start_utt": r * N_REC * u,
                       "phonemes_per_recording": mean([sum(len(x) for x in rec)
                                                       for rec in recs]),
                       "zipf_bso": ZIPF_BSO[(u, r)],
                       "real": test_set(recs, a.b_cds, s, sur),
                       "neg": test_set(neg_dataset(recs, s + 5000000, sur), a.b_cds,
                                       s + 7000000, sur),
                       "seconds_since_start": round(time.time() - t0, 1)}
                rows.append(row)
                save()
                print("u=%d rep=%d real p=%.3f gain=%.4f | neg p=%.3f | zipf %s (%.0f s)" % (
                    u, r, row["real"]["p"], row["real"]["mean_gain"], row["neg"]["p"],
                    row["zipf_bso"], row["seconds_since_start"]), flush=True)
        if out["status"] == "running":
            out["status"] = "ok"
    out["grading"] = grade(rows, w)
    out["seconds"] = round(time.time() - t0, 1)
    save()
    gr = out["grading"]
    print(json.dumps({"status": out["status"], "rules": gr["rules"],
                      "predictions": gr["predictions"], "brier": gr["brier"],
                      "detect_hold": gr["detect_hold"], "detect_zipf": gr["detect_zipf"]},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
