# SPDX-License-Identifier: Apache-2.0
# finch_xpop.py: the independent-population finch test of song-zipf-test (XPOP-PREREG.md).
# Does the "language-like" Zipf structure of Bengalese finch song (Kirby et al. 2026, Sci. Adv.
# eaea3015) replicate in birds from other recordings, and does it go beyond second- or
# third-order syllable rules once each bird contributes ~20,000 notes instead of ~700?
# Data: Koumura & Okanoya 2016 BirdsongRecognition (figshare 3470165, 11 birds, CC BY 4.0) and
# Nicholson, Queen & Sober Bengalese Finch Song Repository (figshare 4805749, 4 birds, CC BY 4.0).
# Runs the unchanged registered pipeline zipfseg.py (fetched at commit 742fd83).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import csv
import hashlib
import io
import json
import math
import os
import sys
import tarfile
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict

import zipfseg as z

VERSION = "xpop-1"
ALPHA = 0.05
SEED = 20261118
UA = {"User-Agent": "song-zipf-test (MV2, Munim, Inc.)"}
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/main/"
              "XPOP-PREREG.md")

# Third-order pooled Markov null: same generator as markov2_pooled, k = 3.
z.NULLS["markov3_pooled"] = lambda rec, rng: z.markov_recording(rec, 3, rng)
FULL_NULLS = ("shuffle", "bigram_within", "markov1_pooled", "markov2_pooled", "markov3_pooled")
SMALL_NULLS = ("shuffle", "bigram_within", "markov1_pooled", "markov2_pooled")

# ---- Koumura & Okanoya 2016 (figshare 3470165, v1): name, file id, bytes ----
KOUMURA = [("Bird0", 5463221, 54675553), ("Bird1", 5463224, 214290775),
           ("Bird2", 5463227, 184940808), ("Bird3", 5463230, 234579033),
           ("Bird4", 5463233, 180002112), ("Bird5", 5463236, 148824616),
           ("Bird6", 5463239, 118492595), ("Bird7", 5463242, 145046810),
           ("Bird8", 5463245, 44275958), ("Bird9", 5463248, 117986514),
           ("Bird10", 5463251, 44160721)]
FS_URL = "https://ndownloader.figshare.com/files/%d"
SAMPLE_RATE = 32000                   # Koumura & Okanoya 2016, Methods
MERGE_GAP_SAMPLES = int(0.3 * SAMPLE_RATE)   # 9,600: the paper's "< 300 ms" song rule
GATE_K_BIRDS = 11
GATE_K_NOTES_MEAN = 17930.9           # paper: 17930.9 +- 8941.8 notes per bird
GATE_K_NOTES_TOL = 0.05               # relative
GATE_K_CLASSES_MEAN = 8.1             # paper: 8.1 +- 3.9 note classes per bird
GATE_K_CLASSES_TOL = 0.5              # absolute

# ---- Nicholson, Queen & Sober (figshare 4805749): wav+csv archives, chronological ----
NICHOLSON = {
    "bl26lb16": [("041912", 41669016), ("042012", 41669013), ("042112", 41669010)],
    "gr41rd51": [("061912", 41669001), ("062012", 41668998), ("062112", 41668995),
                 ("062212", 41669004), ("062312", 41669007)],
    "gy6or6": [("032212", 41668980), ("032312", 41668983), ("032412", 41668986),
               ("032512", 41668989), ("032612", 41668992)],
    "or60yw70": [("092712", 41668971), ("092812", 41668974), ("092912", 41668965),
                 ("093012", 41668977), ("100112", 41668968)],
}
CAP_N = 20000                         # syllables per bird (whole files, in time order)
BOUT_GAP_S = 0.3                      # same 300 ms rule as Koumura's song definition
GATE_N_BIRDS = 4
GATE_N_MIN_SYLL = 5000
GATE_N_MAX_BAD_FRAC = 0.01

KIRBY_TRANSITIONS = 666               # 19,990 transitions / 30 recordings (Kirby et al.)
PRIORS = {"K1": 0.80, "K2": 0.90, "K3": 0.85, "K4": 0.85, "K5": 0.50, "K6": 0.30,
          "K7": 0.90, "N1": 0.75, "N2": 0.45, "S1": 0.20, "S2": 0.70}


# --------------------------------------------------------------------------
# Koumura reading
# --------------------------------------------------------------------------
def parse_koumura_xml(blob):
    """Annotation.xml -> list of {"wav", "pos", "notes": [(abs_start, abs_end, label)]}.
    Sequence Position is in samples within the wav; Note Position is relative to it."""
    root = ET.fromstring(blob)
    seqs = []
    for s in root.iter("Sequence"):
        wav = (s.findtext("WaveFileName") or "").strip()
        pos = int((s.findtext("Position") or "0").strip())
        notes = []
        for n in s.iter("Note"):
            npos = int((n.findtext("Position") or "0").strip())
            nlen = int((n.findtext("Length") or "0").strip())
            lab = (n.findtext("Label") or "").strip()
            notes.append((pos + npos, pos + npos + nlen, lab))
        seqs.append({"wav": wav, "pos": pos, "notes": notes})
    return seqs


def wav_key(name):
    stem = name.rsplit(".", 1)[0]
    return (0, int(stem), name) if stem.isdigit() else (1, 0, name)


def koumura_bouts(seqs, gap_samples=MERGE_GAP_SAMPLES, merge=True):
    """Bouts in recording order (wav number, then position). With merge=True,
    a sequence joins the previous bout when it is in the same wav and starts
    less than gap_samples after the previous sequence's last note ends."""
    order = sorted(range(len(seqs)), key=lambda i: (wav_key(seqs[i]["wav"]), seqs[i]["pos"], i))
    bouts = []
    prev_wav = None
    prev_end = None
    for i in order:
        s = seqs[i]
        notes = sorted(n for n in s["notes"] if n[2])
        if not notes:
            continue
        labels = [n[2] for n in notes]
        if merge and bouts and s["wav"] == prev_wav and notes[0][0] - prev_end < gap_samples:
            bouts[-1].extend(labels)
        else:
            bouts.append(labels)
        prev_wav = s["wav"]
        prev_end = notes[-1][1]
    return bouts


def koumura_stats(seqs):
    labels = [n[2] for s in seqs for n in s["notes"] if n[2]]
    return {"sequences": len(seqs), "notes": len(labels), "classes": len(set(labels)),
            "max_notes_per_sequence": max((len(s["notes"]) for s in seqs), default=0),
            "label_counts": dict(sorted(Counter(labels).items()))}


def gate_koumura(stats):
    """stats: list of koumura_stats dicts, one per bird that was read."""
    n = len(stats)
    mn = sum(s["notes"] for s in stats) / n if n else float("nan")
    mc = sum(s["classes"] for s in stats) / n if n else float("nan")
    ok_b = n == GATE_K_BIRDS
    ok_n = n > 0 and abs(mn - GATE_K_NOTES_MEAN) <= GATE_K_NOTES_TOL * GATE_K_NOTES_MEAN
    ok_c = n > 0 and abs(mc - GATE_K_CLASSES_MEAN) <= GATE_K_CLASSES_TOL
    return {"birds": n, "notes_mean": mn, "classes_mean": mc, "birds_ok": ok_b,
            "notes_ok": ok_n, "classes_ok": ok_c, "pass": ok_b and ok_n and ok_c}


# --------------------------------------------------------------------------
# Nicholson reading
# --------------------------------------------------------------------------
def _col(head, exact, sub):
    if exact in head:
        return head.index(exact)
    for i, c in enumerate(head):
        if sub in c:
            return i
    raise ValueError("no %s column in %r" % (sub, head))


def parse_simple_seq_csv(text):
    """crowsetta simple-seq / generic-seq csv -> [(onset_s, offset_s, label)] in file order."""
    rows = [r for r in csv.reader(io.StringIO(text)) if r and any(c.strip() for c in r)]
    if not rows:
        return []
    head = [c.strip().lower() for c in rows[0]]
    if any("onset" in c or "label" in c for c in head):
        io_ = _col(head, "onset_s", "onset")
        oo = _col(head, "offset_s", "offset")
        lo = _col(head, "label", "label")
        body = rows[1:]
    else:
        io_, oo, lo = 0, 1, 2
        body = rows
    return [(float(r[io_]), float(r[oo]), r[lo].strip()) for r in body]


def file_ok(sylls):
    """onset <= offset for every row and onsets non-decreasing in file order."""
    for i, (on, off, _) in enumerate(sylls):
        if on > off:
            return False
        if i and on < sylls[i - 1][0]:
            return False
    return True


def split_bouts(sylls, gap_s=BOUT_GAP_S):
    """Rows with empty labels are dropped first; a new bout starts when the
    silent gap to the previous kept syllable is >= gap_s."""
    bouts = []
    prev_off = None
    for on, off, lab in sorted(s for s in sylls if s[2]):
        if bouts and on - prev_off < gap_s:
            bouts[-1].append(lab)
        else:
            bouts.append([lab])
        prev_off = off
    return bouts


def nicholson_bird(bird, days, load_day, cap=CAP_N):
    """Whole annotated files in time order (days chronological, files by name)
    until the bird has >= cap syllables. load_day(bird, day) -> {name: csv text}."""
    bouts = []
    n = files = bad = unreadable = 0
    used = []
    labels = Counter()
    for day in days:
        if n >= cap:
            break
        csvs = load_day(bird, day)
        used.append({"day": day, "csv_files": len(csvs)})
        for name in sorted(csvs):
            if n >= cap:
                break
            try:
                sy = parse_simple_seq_csv(csvs[name])
            except Exception:
                unreadable += 1
                continue
            if not any(s[2] for s in sy):
                continue
            files += 1
            if not file_ok(sy):
                bad += 1
            bs = split_bouts(sy)
            bouts.extend(bs)
            n += sum(len(b) for b in bs)
            labels.update(x for b in bs for x in b)
    return bouts, {"bird": bird, "days": used, "files": files, "bad_files": bad,
                   "unreadable_files": unreadable, "syllables": n, "classes": len(labels),
                   "label_counts": dict(sorted(labels.items()))}


def gate_nicholson(infos):
    ok_b = len(infos) == GATE_N_BIRDS
    ok_s = ok_b and all(i["syllables"] >= GATE_N_MIN_SYLL for i in infos)
    files = sum(i["files"] for i in infos)
    badf = (sum(i["bad_files"] + i["unreadable_files"] for i in infos) / files
            if files else float("nan"))
    ok_f = files > 0 and badf <= GATE_N_MAX_BAD_FRAC
    return {"birds": len(infos), "files": files, "bad_fraction": badf, "birds_ok": ok_b,
            "syllables_ok": ok_s, "files_ok": ok_f, "pass": ok_b and ok_s and ok_f}


# --------------------------------------------------------------------------
# data sets, held-out check, labels, grading
# --------------------------------------------------------------------------
def first_until(bouts, min_trans=KIRBY_TRANSITIONS):
    out = []
    t = 0
    for b in bouts:
        out.append(b)
        t += max(len(b) - 1, 0)
        if t >= min_trans:
            break
    return out


def describe(recs):
    return {"recordings": len(recs), "bouts": sum(len(r) for r in recs),
            "symbols": sum(len(b) for r in recs for b in r),
            "transitions": sum(max(len(b) - 1, 0) for r in recs for b in r),
            "symbols_per_recording": [sum(len(b) for b in r) for r in recs],
            "alphabet_per_recording": [len({s for b in r for s in b}) for r in recs],
            "max_bout_length": max((len(b) for r in recs for b in r), default=0)}


def heldout_fast(bouts, k, alpha=0.5, skip=2):
    """Same value as zipfseg.heldout_ll (leave-one-bout-out, additive smoothing),
    computed as (all-bout counts) - (held-out bout counts) for speed."""
    V = len({s for b in bouts for s in b})
    tot = defaultdict(Counter)
    for b in bouts:
        for i in range(len(b) - k):
            tot[tuple(b[i:i + k])][b[i + k]] += 1
    tot_n = {c: sum(v.values()) for c, v in tot.items()}
    total = 0.0
    count = 0
    for held in bouts:
        own = defaultdict(Counter)
        for i in range(len(held) - k):
            own[tuple(held[i:i + k])][held[i + k]] += 1
        for i in range(max(skip, k), len(held)):
            ctx = tuple(held[i - k:i])
            oc = own.get(ctx)
            tc = tot.get(ctx)
            n_xy = (tc[held[i]] if tc else 0) - (oc[held[i]] if oc else 0)
            n_ctx = tot_n.get(ctx, 0) - (sum(oc.values()) if oc else 0)
            total += math.log((n_xy + alpha) / (n_ctx + alpha * V))
            count += 1
    return total / count if count else float("nan")


def heldout_block(recs):
    d1 = [heldout_fast(r, 2, skip=2) - heldout_fast(r, 1, skip=2) for r in recs]
    d2 = [heldout_fast(r, 3, skip=3) - heldout_fast(r, 2, skip=3) for r in recs]
    return {"d1_per_recording": d1, "d1_n_favour_order2": sum(1 for a in d1 if a > 0),
            "d2_per_recording": d2, "d2_n_favour_order3": sum(1 for a in d2 if a > 0),
            "n_recordings": len(recs)}


def decision3(row, alpha=ALPHA):
    n = row["nulls"]
    has3 = "markov3_pooled" in n
    if has3 and n["markov3_pooled"]["p"] < alpha:
        return "BEYOND_THIRD_ORDER"
    if n["markov2_pooled"]["p"] < alpha:
        return "EXPLAINED_BY_THIRD_ORDER" if has3 else "BEYOND_SECOND_ORDER"
    if n["markov1_pooled"]["p"] < alpha:
        return "EXPLAINED_BY_SECOND_ORDER"
    return "EXPLAINED_BY_FIRST_ORDER"


def _row(res, d, th="0.5"):
    return res.get(d, {}).get("by_theta", {}).get(th)


def _beats(row, name):
    if row is None or name not in row.get("nulls", {}):
        return None
    return row["nulls"][name]["p"] < ALPHA


def _both(a, b):
    return None if a is None or b is None else (a and b)


def grade(res, gates):
    k, n, ks = _row(res, "K"), _row(res, "N"), _row(res, "KS")
    hk = res.get("K", {}).get("heldout")
    g = {"K1": None if k is None else k["real_mean_r2"] >= 0.80,
         "K2": _both(_beats(k, "shuffle"), _beats(k, "rotate")),
         "K3": _beats(k, "bigram_within"),
         "K4": _beats(k, "markov1_pooled"),
         "K5": _beats(k, "markov2_pooled"),
         "K6": _beats(k, "markov3_pooled"),
         "K7": (None if hk is None else
                hk["d1_n_favour_order2"] >= math.ceil(0.8 * hk["n_recordings"])),
         "N1": _beats(n, "bigram_within"),
         "N2": _beats(n, "markov2_pooled"),
         "S1": _beats(ks, "markov2_pooled"),
         "S2": _beats(ks, "bigram_within")}
    graded = [x for x in PRIORS if g[x] is not None]
    brier = (sum((PRIORS[x] - (1.0 if g[x] else 0.0)) ** 2 for x in graded) / len(graded)
             if graded else float("nan"))
    labels = {d: {th: decision3(row) for th, row in sorted(res[d]["by_theta"].items())}
              for d in res if res[d].get("by_theta")}
    if g["K3"] is None or g["N1"] is None:
        x1 = "NOT_GRADED"
    elif g["K3"] and g["N1"]:
        x1 = "ABOVE_BIGRAM_REPLICATES"
    elif not g["K3"] and not g["N1"]:
        x1 = "ABOVE_BIGRAM_FAILS"
    else:
        x1 = "ABOVE_BIGRAM_MIXED"
    if g["K5"] is None or g["N2"] is None:
        x2 = "NOT_GRADED"
    elif not g["K5"] and not g["N2"]:
        x2 = "SECOND_ORDER_EXPLAINS_FINCH_ZIPF"
    elif g["K5"] and g["N2"]:
        x2 = "FINCH_ZIPF_BEYOND_SECOND_ORDER"
    else:
        x2 = "SECOND_ORDER_MIXED"
    if g["K5"] is None or g["S1"] is None:
        x3 = "NOT_GRADED"
    elif g["S1"]:
        x3 = "BEYOND_EVEN_AT_KIRBY_SIZE"
    elif g["K5"]:
        x3 = "SIZE_DEPENDENT"
    else:
        x3 = "NOT_BEYOND_AT_EITHER_SIZE"
    lk = labels.get("K", {})
    robust_k = len(lk) == 3 and len(set(lk.values())) == 1
    provisional = not (gates.get("K", {}).get("pass") and gates.get("N", {}).get("pass"))
    return {"predictions": g, "graded": graded, "priors": PRIORS, "brier": brier,
            "labels": labels, "rules": {"X1": x1, "X2": x2, "X3": x3, "robust_K": robust_k},
            "provisional": provisional}


# --------------------------------------------------------------------------
# analysis blocks (two worker processes)
# --------------------------------------------------------------------------
def plan(b_full=200, b_rob=50, b_small=1000):
    """(id, data set, theta or None for the held-out check, B, nulls, optional)."""
    a = [("K_0.5", "K", 0.5, b_full, FULL_NULLS, False),
         ("K_heldout", "K", None, 0, None, False),
         ("K_0.3", "K", 0.3, b_rob, FULL_NULLS, True),
         ("K_0.7", "K", 0.7, b_rob, FULL_NULLS, True),
         ("Kraw_0.5", "Kraw", 0.5, b_rob, FULL_NULLS, True)]
    b = [("N_0.5", "N", 0.5, b_full, FULL_NULLS, False),
         ("N_heldout", "N", None, 0, None, False),
         ("KS_0.5", "KS", 0.5, b_small, SMALL_NULLS, False),
         ("KS_heldout", "KS", None, 0, None, False),
         ("NS_0.5", "NS", 0.5, b_small, SMALL_NULLS, False),
         ("N_0.3", "N", 0.3, b_rob, FULL_NULLS, True),
         ("N_0.7", "N", 0.7, b_rob, FULL_NULLS, True)]
    return [a, b]


def run_task(args):
    blocks, recs, out_dir, t0, budget_s = args
    done = []
    bdir = os.path.join(out_dir, "blocks")
    os.makedirs(bdir, exist_ok=True)
    for bid, data, theta, B, nulls, optional in blocks:
        t1 = time.time()
        if not recs.get(data):
            r = {"skipped": "no data"}
        elif optional and t1 - t0 > 0.55 * budget_s:
            r = {"skipped": "time budget (%.0f s used)" % (t1 - t0)}
        else:
            try:
                if theta is None:
                    r = heldout_block(recs[data])
                else:
                    r = z.analyze(recs[data], thetas=(theta,), B=B, seed=SEED, nulls=nulls,
                                  heldout=False)["by_theta"][str(theta)]
                r["seconds"] = time.time() - t1
            except Exception as e:                  # recorded, never hidden
                r = {"error": repr(e)[:500]}
        with open(os.path.join(bdir, bid + ".json"), "w", encoding="utf-8") as f:
            json.dump(r, f, indent=1)
        print("block", bid, "%.0f s" % (time.time() - t1), list(r)[:4], flush=True)
        done.append((bid, data, theta, r))
    return done


def assemble(task_outputs):
    res = {}
    for out in task_outputs:
        for bid, data, theta, r in out:
            d = res.setdefault(data, {})
            if "skipped" in r or "error" in r:
                d.setdefault("not_run", {})[bid] = r
            elif theta is None:
                d["heldout"] = r
            else:
                d.setdefault("by_theta", {})[str(theta)] = r
    return res


# --------------------------------------------------------------------------
# I/O
# --------------------------------------------------------------------------
def fetch(url, timeout=120):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def download(url, path, timeout=600):
    h = hashlib.sha256()
    n = 0
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r, \
            open(path, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            h.update(chunk)
            n += len(chunk)
    return n, h.hexdigest()


def load_koumura_bird(name, url, size, data_dir, downloader=download, pause=5):
    """Annotation.xml bytes for one bird (cached in data_dir); the zip goes to a
    temporary file that is deleted at once (audio is never kept)."""
    kdir = os.path.join(data_dir, "koumura")
    os.makedirs(kdir, exist_ok=True)
    cache = os.path.join(kdir, name + "_Annotation.xml")
    if os.path.exists(cache):
        with open(cache, "rb") as f:
            return f.read(), {"source": "cache"}
    info = {"attempts": []}
    for attempt in range(3):
        fd, tmp = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
        try:
            nbytes, sha = downloader(url, tmp)
            a = {"bytes": nbytes, "sha256": sha, "size_ok": nbytes == size}
            info["attempts"].append(a)
            if nbytes == size:
                with zipfile.ZipFile(tmp) as zf:
                    names = sorted((m for m in zf.namelist()
                                    if m.lower().endswith("annotation.xml")),
                                   key=lambda m: (m.count("/"), m))
                    if not names:
                        a["error"] = "no Annotation.xml in zip"
                        return None, info
                    blob = zf.read(names[0])
                    a["member"] = names[0]
                with open(cache, "wb") as f:
                    f.write(blob)
                info["source"] = "download"
                return blob, info
        except Exception as e:
            info["attempts"].append({"error": repr(e)[:300]})
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        time.sleep(pause * (attempt + 1))
    return None, info


def stream_tar_csvs(url, opener=None, timeout=900):
    """Stream a .tar.gz and keep only the .csv members (audio is read past, never stored)."""
    if opener is None:
        def opener(u):
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout)
    out = {}
    with opener(url) as resp:
        with tarfile.open(fileobj=resp, mode="r|gz") as tf:
            for m in tf:
                if m.isfile() and m.name.lower().endswith(".csv"):
                    out[m.name] = tf.extractfile(m).read().decode("utf-8", "replace")
    return out


def make_day_loader(data_dir, log, opener=None, pause=5):
    ndir = os.path.join(data_dir, "nicholson")
    os.makedirs(ndir, exist_ok=True)
    ids = {(b, d): fid for b, days in NICHOLSON.items() for d, fid in days}

    def load_day(bird, day):
        cache = os.path.join(ndir, "%s.%s.csvs.json" % (bird, day))
        if os.path.exists(cache):
            with open(cache, encoding="utf-8") as f:
                log.append({"bird": bird, "day": day, "source": "cache"})
                return json.load(f)
        url = FS_URL % ids[(bird, day)]
        for attempt in range(3):
            try:
                csvs = stream_tar_csvs(url, opener)
                with open(cache, "w", encoding="utf-8") as f:
                    json.dump(csvs, f)
                log.append({"bird": bird, "day": day, "source": url, "csv_files": len(csvs)})
                return csvs
            except Exception as e:
                log.append({"bird": bird, "day": day, "attempt": attempt, "error": repr(e)[:300]})
                time.sleep(pause * (attempt + 1))
        return {}
    return load_day


def wait_for_registration(max_minutes):
    t0 = time.time()
    tries = 0
    last = None
    while True:
        tries += 1
        try:
            blob = fetch(PREREG_URL, timeout=60)
            if b"XPOP-PREREG" in blob:
                return {"found": True, "tries": tries,
                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "sha256": hashlib.sha256(blob).hexdigest()}
        except Exception as e:
            last = repr(e)[:200]
        if time.time() - t0 > max_minutes * 60:
            return {"found": False, "tries": tries, "last_error": last}
        time.sleep(60)


def dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data/finch-xpop")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--max-minutes", type=float, default=230)
    ap.add_argument("--wait-minutes", type=float, default=60)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    out_path = os.path.join(a.out_dir, "xpop_results.json")
    out = {"version": VERSION, "python": sys.version.split()[0],
           "zipfseg_sha256": hashlib.sha256(open(z.__file__, "rb").read()).hexdigest()}
    t0 = time.time()

    reg = wait_for_registration(a.wait_minutes)
    out["registration"] = reg
    if not reg["found"]:
        out["status"] = "not_run_unregistered"
        dump(out, out_path)
        print("XPOP-PREREG.md not public; nothing analysed")
        return 4

    # Koumura
    kstats, kinfo, kmerged, kraw = [], {}, [], []
    for name, fid, size in KOUMURA:
        blob, info = load_koumura_bird(name, FS_URL % fid, size, a.data_dir)
        kinfo[name] = info
        if blob is None:
            continue
        try:
            seqs = parse_koumura_xml(blob)
        except Exception as e:
            info["parse_error"] = repr(e)[:300]
            continue
        st = koumura_stats(seqs)
        st["bird"] = name
        st["xml_sha256"] = hashlib.sha256(blob).hexdigest()
        kstats.append(st)
        kmerged.append(koumura_bouts(seqs, merge=True))
        kraw.append(koumura_bouts(seqs, merge=False))
        print(name, st["sequences"], "sequences", st["notes"], "notes", st["classes"],
              "classes", flush=True)
    gk = gate_koumura(kstats)

    # Nicholson
    nlog = []
    load_day = make_day_loader(a.data_dir, nlog)
    ninfo, nrecs = [], []
    for bird in sorted(NICHOLSON):
        bouts, info = nicholson_bird(bird, [d for d, _ in NICHOLSON[bird]], load_day)
        ninfo.append(info)
        if bouts:
            nrecs.append(bouts)
        print(bird, info["syllables"], "syllables", info["files"], "files", flush=True)
    gn = gate_nicholson(ninfo)

    recs = {"K": kmerged, "Kraw": kraw, "N": nrecs,
            "KS": [first_until(r) for r in kmerged], "NS": [first_until(r) for r in nrecs]}
    out.update({"koumura": {"stats": kstats, "downloads": kinfo},
                "nicholson": {"birds": ninfo, "downloads": nlog},
                "gates": {"K": gk, "N": gn},
                "describe": {k: describe(v) for k, v in recs.items()},
                "status": "analysing"})
    dump(out, out_path)
    print("gates", json.dumps({"K": gk, "N": gn}), flush=True)

    budget_s = a.max_minutes * 60
    tasks = [(blocks, recs, a.out_dir, t0, budget_s) for blocks in plan()]
    if a.workers > 1:
        import multiprocessing
        with multiprocessing.get_context("fork").Pool(len(tasks)) as pool:
            outs = pool.map(run_task, tasks)
    else:
        outs = [run_task(t) for t in tasks]
    res = assemble(outs)
    gr = grade(res, {"K": gk, "N": gn})
    out.update({"status": "ok", "results": res, "grading": gr, "seconds": time.time() - t0})
    dump(out, out_path)
    print(json.dumps({"rules": gr["rules"], "labels": gr["labels"],
                      "predictions": gr["predictions"], "brier": gr["brier"],
                      "provisional": gr["provisional"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
