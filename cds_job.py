# SPDX-License-Identifier: Apache-2.0
# cds_job.py: the human-language positive control of song-zipf-test (CDS-PREREG.md).
# Runs the unchanged zipfseg pipeline and Markov nulls on phonemically transcribed
# child-directed English (Brent-Ratner corpus, br-phono.txt) at finch and whale size.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import hashlib
import io
import json
import os
import sys
import time
import urllib.request
import zipfile
from collections import Counter

import zipfseg as z

VERSION = "cds-1"
ALPHA = 0.05
SOURCES = (
    ("talkbank_zip", "https://talkbank.org/childes/access/Derived/0docs/BR.zip"),
    ("github_mirror", "https://raw.githubusercontent.com/melsner/neural-segmentation/"
                      "master/br-phono/br-phono.txt"),
)
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/main/"
              "CDS-PREREG.md")
GATE_UTT = 9790
GATE_PHON = 95809
GATE_WORDS = (33387, 33399)
WORD_TOL = 20
F_REC, F_UTT = 30, 70          # CDS-F: utterances 0 .. 2099
W_REC, W_UTT = 8, 600          # CDS-W: utterances 2100 .. 6899
W_START = F_REC * F_UTT
THETAS = (0.3, 0.5, 0.7)
PRIORS = {"H0": 0.65, "H1": 0.90, "H2": 0.50, "H3": 0.80, "H4": 0.40, "H5": 0.35,
          "H6": 0.85, "H7": 0.45}


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------
def parse_text(text):
    """One utterance per non-empty line; words separated by whitespace; one
    character per phoneme. Returns a list of utterances (lists of word strings)."""
    utts = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        words = line.split()
        if words:
            utts.append(words)
    return utts


def counts(utts):
    return {"utterances": len(utts),
            "words": sum(len(u) for u in utts),
            "phonemes": sum(len(w) for u in utts for w in u),
            "phoneme_types": len({c for u in utts for w in u for c in w}),
            "word_types": len({w for u in utts for w in u})}


def gate(c):
    ok_u = c["utterances"] == GATE_UTT
    ok_p = c["phonemes"] == GATE_PHON
    ok_w = any(abs(c["words"] - w) <= WORD_TOL for w in GATE_WORDS)
    return {"utterances": ok_u, "phonemes": ok_p, "words": ok_w,
            "pass": ok_u and ok_p and ok_w}


def extract_phono(blob):
    """br-phono.txt from the TalkBank zip, or the blob itself if it is not a zip."""
    if blob[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith("br-phono.txt")]
            if not names:
                raise ValueError("br-phono.txt not in zip: %r" % zf.namelist()[:20])
            return zf.read(names[0])
    return blob


# --------------------------------------------------------------------------
# data sets
# --------------------------------------------------------------------------
def blocks(utts, start, n_rec, per):
    return [utts[start + k * per: start + (k + 1) * per] for k in range(n_rec)]


def to_recording(block):
    """bouts = utterances, symbols = phonemes (word spaces removed)."""
    return [list("".join(u)) for u in block]


def word_boundaries(u):
    """Within-utterance positions (0 < pos < length) where a new word starts."""
    pos = 0
    out = []
    for w in u[:-1]:
        pos += len(w)
        out.append(pos)
    return out


def boundary_scores(block_list, theta):
    hit = n_pred = n_true = 0
    for block in block_list:
        segs = z.segment_recording_bouts(to_recording(block), theta)
        for u, s in zip(block, segs):
            t = set(word_boundaries(u))
            p = set(z.cut_positions(s))
            hit += len(t & p)
            n_pred += len(p)
            n_true += len(t)
    prec = hit / n_pred if n_pred else float("nan")
    rec = hit / n_true if n_true else float("nan")
    if prec == prec and rec == rec and prec + rec > 0:
        f1 = 2 * prec * rec / (prec + rec)
    else:
        f1 = float("nan")
    return {"hits": hit, "n_cuts": n_pred, "n_word_boundaries": n_true,
            "precision": prec, "recall": rec, "f1": f1}


def true_word_r2(block_list):
    return z.nanmean([z.zipf_r2(Counter(w for u in b for w in u).values())
                      for b in block_list])


def describe(block_list):
    recs = [to_recording(b) for b in block_list]
    return {"recordings": len(recs),
            "utterances": sum(len(r) for r in recs),
            "phonemes": sum(len(x) for r in recs for x in r),
            "phonemes_per_recording_mean": sum(len(x) for r in recs for x in r) / len(recs),
            "true_word_tokens": sum(len(u) for b in block_list for u in b),
            "true_word_zipf_r2_mean": true_word_r2(block_list)}


# --------------------------------------------------------------------------
# grading (CDS-PREREG.md sections 4 and 5)
# --------------------------------------------------------------------------
def grade(F, W, bscores):
    f5 = F["by_theta"]["0.5"]
    n = f5["nulls"]
    w5 = W["by_theta"]["0.5"]
    g = {
        "H0": f5["real_mean_r2"] >= 0.80,
        "H1": n["shuffle"]["p"] < ALPHA and n["rotate"]["p"] < ALPHA,
        "H2": n["bigram_within"]["p"] < ALPHA,
        "H3": n["markov1_pooled"]["p"] < ALPHA,
        "H4": n["markov2_pooled"]["p"] < ALPHA,
        "H5": w5["nulls"]["markov2_pooled"]["p"] < ALPHA,
        "H6": F["heldout_ll_order2_minus_order1"]["n_favour_order2"] >= 20,
        "H7": bscores["0.5"]["f1"] >= 0.50,
    }
    labels = {"F": {th: z.decision(F["by_theta"][th]) for th in F["by_theta"]},
              "W": {th: z.decision(W["by_theta"][th]) for th in W["by_theta"]}}
    bso = "BEYOND_SECOND_ORDER"
    rules = {
        "L1": ("LANGUAGE_PASSES_AT_FINCH_SIZE" if labels["F"]["0.5"] == bso
               else "LANGUAGE_FAILS_AT_FINCH_SIZE"),
        "L2": ("LANGUAGE_PASSES_AT_WHALE_SIZE" if labels["W"]["0.5"] == bso
               else "LANGUAGE_FAILS_AT_WHALE_SIZE"),
        "L3_published_controls_passed_by_english": g["H1"],
        "robust_F": len(set(labels["F"].values())) == 1 and len(labels["F"]) == 3,
        "robust_W": len(set(labels["W"].values())) == 1 and len(labels["W"]) == 3,
    }
    brier = sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in PRIORS) / len(PRIORS)
    return {"predictions": g, "labels": labels, "rules": rules, "priors": PRIORS,
            "brier": brier}


# --------------------------------------------------------------------------
# job
# --------------------------------------------------------------------------
def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "song-zipf-test (MV2, Munim, Inc.)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def wait_for_registration(max_minutes):
    """The analysis runs only once CDS-PREREG.md is public (it is committed right
    after the filing run). Polls the public repository."""
    t0 = time.time()
    tries = 0
    last = None
    while True:
        tries += 1
        try:
            blob = fetch(PREREG_URL, timeout=60)
            if b"CDS-PREREG" in blob:
                return {"found": True, "tries": tries,
                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "sha256": hashlib.sha256(blob).hexdigest()}
        except Exception as e:                       # 404 until published
            last = repr(e)[:200]
        if time.time() - t0 > max_minutes * 60:
            return {"found": False, "tries": tries, "last_error": last}
        time.sleep(60)


def read_blob(blob):
    """bytes -> (utterances, counts, gate)."""
    utts = parse_text(blob.decode("utf-8", errors="replace"))
    c = counts(utts)
    return utts, c, gate(c)


def load_corpus(data_dir, sources=SOURCES, fetcher=None):
    """First source whose file passes the reading gate wins; every attempt is
    recorded. A passing file is cached in data_dir. Returns (utts, info) with
    utts None if no source passed."""
    fetcher = fetcher or fetch
    os.makedirs(data_dir, exist_ok=True)
    cache = os.path.join(data_dir, "br-phono.txt")
    info = {"attempts": []}
    cands = []
    if os.path.exists(cache):
        cands.append(("cache", None))
    cands.extend(sources)
    for name, url in cands:
        try:
            blob = open(cache, "rb").read() if url is None else extract_phono(fetcher(url))
        except Exception as e:
            info["attempts"].append({"source": name, "ok": False, "error": repr(e)[:300]})
            continue
        utts, c, gt = read_blob(blob)
        info["attempts"].append({"source": name, "ok": gt["pass"], "counts": c, "gate": gt,
                                 "sha256": hashlib.sha256(blob).hexdigest(),
                                 "bytes": len(blob)})
        if gt["pass"]:
            info.update({"source": name, "url": url, "sha256": hashlib.sha256(blob).hexdigest(),
                         "bytes": len(blob), "counts": c, "gate": gt})
            if url is not None:
                open(cache, "wb").write(blob)
            return utts, info
    return None, info


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data/cds")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--B-f", type=int, default=1000)
    ap.add_argument("--B-w", type=int, default=200)
    ap.add_argument("--wait-minutes", type=float, default=45)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    out = {"version": VERSION, "python": sys.version.split()[0],
           "zipfseg_sha256": hashlib.sha256(open(z.__file__, "rb").read()).hexdigest()}
    out_path = os.path.join(a.out_dir, "results_cds.json")

    reg = wait_for_registration(a.wait_minutes)
    out["registration"] = reg
    if not reg["found"]:
        out["status"] = "not_run_unregistered"
        json.dump(out, open(out_path, "w", encoding="utf-8"), indent=1)
        print("CDS-PREREG.md not public; nothing analysed")
        return 4

    utts, info = load_corpus(a.data_dir)
    out["corpus"] = info
    if utts is None:
        out["status"] = "gate_fail_or_no_data"
        json.dump(out, open(out_path, "w", encoding="utf-8"), indent=1)
        print("no source passed the reading gate:", json.dumps(info["attempts"])[:2000])
        return 0

    fb = blocks(utts, 0, F_REC, F_UTT)
    wb = blocks(utts, W_START, W_REC, W_UTT)
    out["describe"] = {"F": describe(fb), "W": describe(wb)}
    t0 = time.time()
    F = z.analyze([to_recording(b) for b in fb], thetas=THETAS, B=a.B_f)
    print("CDS-F done in %.0f s" % (time.time() - t0), flush=True)
    W = z.analyze([to_recording(b) for b in wb], thetas=THETAS, B=a.B_w)
    print("CDS-W done in %.0f s" % (time.time() - t0), flush=True)
    bs = {str(th): boundary_scores(fb, th) for th in THETAS}
    bs_w = {str(th): boundary_scores(wb, th) for th in THETAS}
    out.update({"status": "ok", "F": F, "W": W, "boundary_scores_F": bs,
                "boundary_scores_W": bs_w, "grading": grade(F, W, bs),
                "seconds": time.time() - t0})
    json.dump(out, open(out_path, "w", encoding="utf-8"), indent=1)
    gr = out["grading"]
    print(json.dumps({"labels": gr["labels"], "rules": gr["rules"],
                      "predictions": gr["predictions"], "brier": gr["brier"],
                      "F_0.5": {k: [v["z"], v["p"]] for k, v in
                                F["by_theta"]["0.5"]["nulls"].items()},
                      "W_0.5": {k: [v["z"], v["p"]] for k, v in
                                W["by_theta"]["0.5"]["nulls"].items()},
                      "real_F": F["by_theta"]["0.5"]["real_mean_r2"],
                      "real_W": W["by_theta"]["0.5"]["real_mean_r2"],
                      "boundary_F_0.5": bs["0.5"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
