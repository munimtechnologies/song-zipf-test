# SPDX-License-Identifier: Apache-2.0
# canary.py: the canary positive control of song-zipf-test (CANARY-PREREG.md).
# Canary phrase sequences are known to carry rules that reach back three or more phrases
# (Markowitz et al. 2013, PLoS Comput. Biol. 9:e1003052; Cohen et al. 2020, Nature 582:539).
# Question: can the transitional-probability chunk Zipf test used for whale and finch song
# (zipfseg.py, unchanged) see that higher-order syntax in real animal song, i.e. does canary
# song beat Markov chains of order 2 (and 3) fitted to the same phrase sequences, in the
# birds where a held-out likelihood ladder shows that order 3 predicts better than order 2?
# Data: Cohen 2022, "Song recordings and annotation files of 3 canaries used to evaluate
# training of TweetyNet models" (Dryad 10.5061/dryad.xgxd254f4 = Zenodo 5956980, CC0).
# Only the annotation csv inside each bird's zip is read (HTTP Range requests); audio is
# never downloaded or stored.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
import struct
import sys
import time
import urllib.request
import zlib
from collections import Counter, defaultdict

import zipfseg as z

VERSION = "canary-1"
ALPHA = 0.05
SEED = 20261119
UA = {"User-Agent": "song-zipf-test (MV2, Munim, Inc.)"}
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/song-zipf-test/main/"
              "CANARY-PREREG.md")
ZENODO = "https://zenodo.org/api/records/5956980/files/%s/content"
# (bird, zip key, bytes, md5 from the Zenodo record)
BIRDS = [("llb11", "llb11_data.zip", 6477283885, "09a799c711b3ac06d5d6d10ab8ed4694"),
         ("llb16", "llb16_data.zip", 2392131064, "a846fd7c68077cf033f84d6194f725f7"),
         ("llb3", "llb3_data.zip", 2541578049, "de57dd94fb18212f64a315b86f9e57e5")]
BIRD_NAMES = tuple(b[0] for b in BIRDS)

SONG_GAP_S = 1.0          # Cohen et al. 2022: songs are separated by silences > 1 s
BLOCK_PHRASES = 3000      # a "recording" = consecutive whole songs with >= 3,000 phrases
MAX_BLOCKS = 8            # per bird
KIRBY_TRANSITIONS = 666   # 19,990 transitions / 30 recordings (Kirby et al. 2026)
LADDER_MAX_K = 5
LADDER_ALPHAS = (0.5, 0.1, 0.02, 0.005)
GATE_MIN_SPAN_S = 15000.0
GATE_MIN_CLASSES = 10
GATE_MAX_BAD = 0.01

z.NULLS["markov3_pooled"] = lambda rec, rng: z.markov_recording(rec, 3, rng)
FULL_NULLS = ("shuffle", "bigram_within", "markov1_pooled", "markov2_pooled", "markov3_pooled")
PRIORS = {"P1": 0.75, "P2": 0.45, "P3": 0.90, "P4": 0.70, "P5": 0.45, "P6": 0.30,
          "P7": 0.80, "P8": 0.20}


# --------------------------------------------------------------------------
# zip reading (central directory via HTTP Range; streaming fallback)
# --------------------------------------------------------------------------
EOCD_SIG = b"PK\x05\x06"
Z64_LOC_SIG = b"PK\x06\x07"
Z64_EOCD_SIG = b"PK\x06\x06"
CD_SIG = b"PK\x01\x02"
LFH_SIG = b"PK\x03\x04"
DD_SIG = b"PK\x07\x08"
FFFF = 0xFFFFFFFF


class RangeUnsupported(Exception):
    pass


def find_eocd(tail):
    """Parse the end-of-central-directory record found in `tail` (the last bytes of
    the archive). Offsets returned are absolute archive offsets."""
    i = tail.rfind(EOCD_SIG)
    if i < 0 or i + 22 > len(tail):
        raise ValueError("no end of central directory record")
    f = struct.unpack("<4s4H2LH", tail[i:i + 22])
    info = {"entries": f[4], "cd_size": f[5], "cd_offset": f[6], "zip64": False}
    if f[4] == 0xFFFF or f[5] == FFFF or f[6] == FFFF:
        j = i - 20
        if j < 0 or tail[j:j + 4] != Z64_LOC_SIG:
            raise ValueError("zip64 locator missing")
        loc = struct.unpack("<4sLQL", tail[j:j + 20])
        info["zip64"] = True
        info["z64_eocd_offset"] = loc[2]
    return info


def parse_z64_eocd(b):
    if b[:4] != Z64_EOCD_SIG or len(b) < 56:
        raise ValueError("bad zip64 end record")
    f = struct.unpack("<4sQ2H2L4Q", b[:56])
    return {"entries": f[7], "cd_size": f[8], "cd_offset": f[9]}


def zip64_extra(extra, usize, csize, offset):
    """Fill the fields stored as 0xFFFFFFFF from the zip64 extra field (id 1), in the
    order uncompressed size, compressed size, local header offset."""
    q = 0
    while q + 4 <= len(extra):
        hid, hlen = struct.unpack("<HH", extra[q:q + 4])
        body = extra[q + 4:q + 4 + hlen]
        if hid == 1:
            vals = [struct.unpack("<Q", body[r:r + 8])[0] for r in range(0, len(body) - 7, 8)]
            it = iter(vals)
            if usize == FFFF:
                usize = next(it)
            if csize == FFFF:
                csize = next(it)
            if offset == FFFF:
                offset = next(it)
            return usize, csize, offset
        q += 4 + hlen
    raise ValueError("zip64 extra field missing")


def has_zip64_extra(extra):
    q = 0
    while q + 4 <= len(extra):
        hid, hlen = struct.unpack("<HH", extra[q:q + 4])
        if hid == 1:
            return True
        q += 4 + hlen
    return False


def parse_central_directory(cd):
    out = []
    p = 0
    while p + 46 <= len(cd) and cd[p:p + 4] == CD_SIG:
        f = struct.unpack("<4s6H3L5H2L", cd[p:p + 46])
        flags, method, crc, csize, usize = f[3], f[4], f[7], f[8], f[9]
        nlen, elen, clen, offset = f[10], f[11], f[12], f[16]
        name = cd[p + 46:p + 46 + nlen].decode("utf-8" if flags & 0x800 else "cp437")
        extra = cd[p + 46 + nlen:p + 46 + nlen + elen]
        if FFFF in (usize, csize, offset):
            usize, csize, offset = zip64_extra(extra, usize, csize, offset)
        out.append({"name": name, "flags": flags, "method": method, "crc": crc,
                    "csize": csize, "usize": usize, "offset": offset})
        p += 46 + nlen + elen + clen
    return out


def list_zip(read_range, total):
    """read_range(a, b) -> bytes a..b inclusive. Returns (members, info)."""
    tail_start = max(0, total - 65536 - 22)
    info = find_eocd(read_range(tail_start, total - 1))
    if info["zip64"]:
        o = info["z64_eocd_offset"]
        info.update(parse_z64_eocd(read_range(o, o + 55)))
    o = info["cd_offset"]
    members = parse_central_directory(read_range(o, o + info["cd_size"] - 1))
    if len(members) != info["entries"]:
        raise ValueError("central directory lists %d members, end record says %d"
                         % (len(members), info["entries"]))
    return members, info


def inflate(raw, method, usize, crc):
    if method == 0:
        data = raw
    elif method == 8:
        d = zlib.decompressobj(-15)
        data = d.decompress(raw) + d.flush()
    else:
        raise ValueError("compression method %d not supported" % method)
    if len(data) != usize or (zlib.crc32(data) & FFFF) != crc:
        raise ValueError("size or CRC mismatch")
    return data


def member_bytes(read_range, m):
    h = read_range(m["offset"], m["offset"] + 29)
    if h[:4] != LFH_SIG:
        raise ValueError("bad local header for %s" % m["name"])
    f = struct.unpack("<4s5H3L2H", h[:30])
    start = m["offset"] + 30 + f[9] + f[10]
    raw = read_range(start, start + m["csize"] - 1) if m["csize"] else b""
    if len(raw) != m["csize"]:
        raise ValueError("short read for %s" % m["name"])
    return inflate(raw, m["method"], m["usize"], m["crc"])


def is_annotation_csv(name):
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    return (name.lower().endswith(".csv") and not base.startswith("._")
            and not name.startswith("__MACOSX/"))


class Reader:
    """Sequential reader with push-back over a non-seekable stream."""

    def __init__(self, f):
        self.f = f
        self.buf = b""

    def read(self, n):
        out = self.buf[:n]
        self.buf = self.buf[n:]
        parts = [out]
        got = len(out)
        while got < n:
            c = self.f.read(min(1 << 20, n - got))
            if not c:
                break
            parts.append(c)
            got += len(c)
        return b"".join(parts)

    def chunk(self):
        if self.buf:
            c, self.buf = self.buf, b""
            return c
        return self.f.read(1 << 20)

    def unread(self, b):
        self.buf = b + self.buf

    def skip(self, n):
        while n > 0:
            c = self.read(min(n, 1 << 20))
            if not c:
                raise EOFError("archive ended early")
            n -= len(c)


def stream_zip_members(f, want):
    """Walk the local headers of a zip read front to back; return {name: bytes} for the
    members where want(name) is true. Other members are read past, never kept."""
    r = Reader(f)
    out = {}
    while True:
        sig = r.read(4)
        if sig != LFH_SIG:
            break
        h = sig + r.read(26)
        if len(h) != 30:
            raise EOFError("archive ended in a local header")
        fl = struct.unpack("<4s5H3L2H", h)
        flags, method, crc, csize, usize, nlen, elen = (fl[2], fl[3], fl[6], fl[7], fl[8],
                                                       fl[9], fl[10])
        name = r.read(nlen).decode("utf-8" if flags & 0x800 else "cp437")
        extra = r.read(elen)
        keep = want(name)
        if flags & 8:
            if method != 8:
                raise ValueError("stored member with a data descriptor: %s" % name)
            d = zlib.decompressobj(-15)
            parts = []
            while not d.eof:
                c = r.chunk()
                if not c:
                    raise EOFError("archive ended inside %s" % name)
                o = d.decompress(c)
                if keep:
                    parts.append(o)
            r.unread(d.unused_data)
            s = r.read(4)
            if s != DD_SIG:
                r.unread(s)
            dd = r.read(20 if has_zip64_extra(extra) else 12)
            crc = struct.unpack("<L", dd[:4])[0]
            if keep:
                data = b"".join(parts)
                if (zlib.crc32(data) & FFFF) != crc:
                    raise ValueError("CRC mismatch for %s" % name)
                out[name] = data
        else:
            if FFFF in (csize, usize):
                usize, csize, _ = zip64_extra(extra, usize, csize, 0)
            if keep:
                out[name] = inflate(r.read(csize), method, usize, crc)
            else:
                r.skip(csize)
    return out


def http_range_reader(url, log, opener=None, pause=5):
    if opener is None:
        def opener(req):
            return urllib.request.urlopen(req, timeout=300)
    state = {"total": None, "requests": 0, "bytes": 0}

    def rr(a, b):
        last = None
        for attempt in range(4):
            req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"],
                                                       "Range": "bytes=%d-%d" % (a, b)})
            try:
                with opener(req) as resp:
                    st = getattr(resp, "status", None)
                    if st != 206:
                        raise RangeUnsupported("HTTP status %s for a Range request" % st)
                    cr = resp.headers.get("Content-Range", "") or ""
                    data = resp.read()
            except RangeUnsupported:
                raise
            except Exception as e:
                last = repr(e)[:200]
                log.append({"range": [a, b], "attempt": attempt, "error": last})
                time.sleep(pause * (attempt + 1))
                continue
            tot = cr.rsplit("/", 1)[-1].strip() if "/" in cr else ""
            if tot.isdigit():
                state["total"] = int(tot)
            if len(data) != b - a + 1:
                last = "got %d bytes for %d-%d" % (len(data), a, b)
                log.append({"range": [a, b], "attempt": attempt, "error": last})
                time.sleep(pause * (attempt + 1))
                continue
            state["requests"] += 1
            state["bytes"] += len(data)
            return data
        raise IOError("range %d-%d failed: %s" % (a, b, last))

    rr.state = state
    return rr


# --------------------------------------------------------------------------
# annotation -> songs -> phrases
# --------------------------------------------------------------------------
def parse_annotation_csv(text):
    """Cohen 2022 csv (label, onset_s, offset_s, ..., audio_file, ...) ->
    ([(audio_file, onset_s, offset_s, label)], rows read, bad rows)."""
    rows = list(csv.DictReader(io.StringIO(text)))
    out = []
    bad = 0
    for r in rows:
        try:
            on = float(r["onset_s"])
            off = float(r["offset_s"])
            lab = (r.get("label") or "").strip()
            af = (r.get("audio_file") or "").strip()
        except (KeyError, TypeError, ValueError):
            bad += 1
            continue
        if not lab or not af or off < on or on != on or off != off:
            bad += 1
            continue
        out.append((af, on, off, lab))
    return out, len(rows), bad


def file_key(af):
    return (af.replace("\\", "/").rsplit("/", 1)[-1], af)


def songs_from_rows(rows, gap=SONG_GAP_S):
    """Audio files in name order; syllables in onset order; a new song starts after a
    silence longer than `gap` seconds (and at every new file)."""
    by_file = defaultdict(list)
    for af, on, off, lab in rows:
        by_file[af].append((on, off, lab))
    songs = []
    for af in sorted(by_file, key=file_key):
        sy = sorted(by_file[af])
        cur = [sy[0]]
        for s in sy[1:]:
            if s[0] - cur[-1][1] > gap:
                songs.append(cur)
                cur = [s]
            else:
                cur.append(s)
        songs.append(cur)
    return songs


def phrases(labels):
    """A phrase is a run of one repeated syllable type; the phrase sequence keeps one
    symbol per run."""
    out = []
    for lab in labels:
        if not out or out[-1] != lab:
            out.append(lab)
    return out


def bird_inputs(texts):
    """{csv member name: text} -> (phrase sequences, one per song; stats)."""
    rows = []
    n_rows = bad = 0
    for name in sorted(texts):
        r, n, b = parse_annotation_csv(texts[name])
        rows.extend(r)
        n_rows += n
        bad += b
    before = len(rows)
    rows = list(dict.fromkeys(rows))
    songs = songs_from_rows(rows) if rows else []
    phr = [phrases([s[2] for s in song]) for song in songs]
    labels = Counter(r[3] for r in rows)
    span = sum(max(s[1] for s in song) - min(s[0] for s in song) for song in songs)
    ptypes = Counter(p for seq in phr for p in seq)
    st = {"csv_members": sorted(texts), "rows": n_rows, "bad_rows": bad,
          "duplicate_rows_dropped": before - len(rows), "syllables": len(rows),
          "classes": len(labels), "audio_files": len({r[0] for r in rows}),
          "songs": len(songs), "song_span_s": span,
          "phrases": sum(len(p) for p in phr), "phrase_types": len(ptypes),
          "songs_with_6_or_more_phrases": sum(1 for p in phr if len(p) >= 6),
          "label_counts": dict(sorted(labels.items())),
          "phrase_counts": dict(sorted(ptypes.items()))}
    return phr, st


def gate_bird(st):
    badf = st["bad_rows"] / st["rows"] if st["rows"] else float("nan")
    ok = (st["rows"] > 0 and badf <= GATE_MAX_BAD and st["classes"] >= GATE_MIN_CLASSES
          and st["song_span_s"] >= GATE_MIN_SPAN_S)
    return {"bad_fraction": badf, "classes": st["classes"], "song_span_s": st["song_span_s"],
            "pass": bool(ok)}


def make_blocks(songs, size=BLOCK_PHRASES, max_blocks=MAX_BLOCKS):
    """Consecutive whole songs until a block holds >= size phrases; a trailing
    incomplete block is dropped."""
    blocks = []
    cur = []
    n = 0
    for s in songs:
        cur.append(s)
        n += len(s)
        if n >= size:
            blocks.append(cur)
            cur = []
            n = 0
            if len(blocks) == max_blocks:
                break
    return blocks


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
            "alphabet_per_recording": [len({s for b in r for s in b}) for r in recs]}


# --------------------------------------------------------------------------
# held-out likelihood (ground truth for "beyond second order")
# --------------------------------------------------------------------------
def heldout_fast(bouts, k, alpha=0.5, skip=2):
    """Same value as zipfseg.heldout_ll (leave-one-bout-out, additive smoothing),
    computed as (all-bout counts) - (held-out bout counts)."""
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


def ladder(bouts, max_k=LADDER_MAX_K, alphas=LADDER_ALPHAS):
    """Held-out log-likelihood per phrase for orders 1..max_k, all scored on the same
    positions (>= max_k in every song); each order takes its best smoothing alpha."""
    by_alpha = {repr(a): [heldout_fast(bouts, k, alpha=a, skip=max_k)
                          for k in range(1, max_k + 1)] for a in alphas}
    best = [max(by_alpha[repr(a)][k] for a in alphas) for k in range(max_k)]
    gains = [best[i + 1] - best[i] for i in range(max_k - 1)]
    return {"skip": max_k, "alphas": list(alphas), "by_alpha": by_alpha, "best": best,
            "gains": gains, "scored": sum(max(0, len(b) - max_k) for b in bouts)}


def heldout_block(recs):
    d1 = [heldout_fast(r, 2, skip=2) - heldout_fast(r, 1, skip=2) for r in recs]
    d2 = [heldout_fast(r, 3, skip=3) - heldout_fast(r, 2, skip=3) for r in recs]
    return {"d1_per_recording": d1, "d1_n_favour_order2": sum(1 for a in d1 if a > 0),
            "d2_per_recording": d2, "d2_n_favour_order3": sum(1 for a in d2 if a > 0),
            "n_recordings": len(recs)}


# --------------------------------------------------------------------------
# labels and grading (CANARY-PREREG.md sections 5 and 6)
# --------------------------------------------------------------------------
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


def _beats(row, name):
    if not row or name not in row.get("nulls", {}):
        return None
    return row["nulls"][name]["p"] < ALPHA


def _pos(x):
    return None if x is None or x != x else x > 0


def _both(a, b):
    return None if a is None or b is None else (a and b)


def _per_bird(res, f):
    return {b: (f(res[b]) if b in res else None) for b in BIRD_NAMES}


def _atleast(d, n):
    v = list(d.values())
    return None if any(x is None for x in v) else sum(1 for x in v if x) >= n


def _all(d):
    v = list(d.values())
    return None if any(x is None for x in v) else all(v)


def grade(res, gates):
    """res[bird] = {"ladder", "heldout_blocks", "by_theta": {"0.5": row, ...}, "kirby": row}."""
    def lad(i):
        def f(r):
            g = (r.get("ladder") or {}).get("gains")
            return _pos(g[i]) if g else None
        return f

    def main(r):
        return r.get("by_theta", {}).get("0.5")

    def d1maj(r):
        h = r.get("heldout_blocks") or {}
        if not h.get("n_recordings"):
            return None
        return 2 * h["d1_n_favour_order2"] > h["n_recordings"]

    gt3 = _per_bird(res, lad(1))
    gt4 = _per_bird(res, lad(2))
    ctrl = _per_bird(res, lambda r: _both(_beats(main(r), "shuffle"), _beats(main(r), "rotate")))
    m1 = _per_bird(res, lambda r: _beats(main(r), "markov1_pooled"))
    m2 = _per_bird(res, lambda r: _beats(main(r), "markov2_pooled"))
    m3 = _per_bird(res, lambda r: _beats(main(r), "markov3_pooled"))
    d1 = _per_bird(res, d1maj)
    k2 = _per_bird(res, lambda r: _beats(r.get("kirby"), "markov2_pooled"))
    g = {"P1": _atleast(gt3, 2), "P2": _atleast(gt4, 2), "P3": _all(ctrl),
         "P4": _atleast(m1, 2), "P5": _atleast(m2, 2), "P6": _atleast(m3, 2),
         "P7": _all(d1), "P8": _atleast(k2, 2)}
    graded = [x for x in PRIORS if g[x] is not None]
    brier = (sum((PRIORS[x] - (1.0 if g[x] else 0.0)) ** 2 for x in graded) / len(graded)
             if graded else float("nan"))
    # C1: the positive control
    if any(v is None for v in list(gt3.values()) + list(m2.values())):
        c1 = "NOT_GRADED"
    else:
        gt_birds = [b for b in BIRD_NAMES if gt3[b]]
        hits = sum(1 for b in gt_birds if m2[b])
        if len(gt_birds) < 2:
            c1 = "NO_GROUND_TRUTH"
        elif hits == len(gt_birds):
            c1 = "TEST_SEES_REAL_SYNTAX"
        elif hits == 0:
            c1 = "TEST_BLIND_TO_REAL_SYNTAX"
        else:
            c1 = "TEST_MIXED"
    # C2: does a detection survive at Kirby et al.'s data size?
    det = [b for b in BIRD_NAMES if m2[b]]
    if any(m2[b] is None for b in BIRD_NAMES) or any(k2[b] is None for b in det):
        c2 = "NOT_GRADED"
    elif not det:
        c2 = "NOTHING_DETECTED_AT_FULL_SIZE"
    else:
        kept = sum(1 for b in det if k2[b])
        c2 = ("KEPT_AT_KIRBY_SIZE" if kept == len(det) else
              "LOST_AT_KIRBY_SIZE" if kept == 0 else "PARTLY_KEPT_AT_KIRBY_SIZE")
    labels = {b: {th: decision3(row) for th, row in sorted(res[b].get("by_theta", {}).items())}
              for b in BIRD_NAMES if b in res}
    robust = {b: (len(v) == 3 and len(set(v.values())) == 1) for b, v in labels.items()}
    kirby_labels = {b: decision3(res[b]["kirby"]) for b in BIRD_NAMES
                    if b in res and res[b].get("kirby")}
    provisional = not all(gates.get(b, {}).get("pass") for b in BIRD_NAMES)
    return {"predictions": g, "graded": graded, "priors": PRIORS, "brier": brier,
            "per_bird": {"gt3": gt3, "gt4": gt4, "controls": ctrl, "m1": m1, "m2": m2,
                         "m3": m3, "d1_majority": d1, "kirby_m2": k2},
            "labels": labels, "kirby_labels": kirby_labels, "robust": robust,
            "rules": {"C1": c1, "C2": c2}, "provisional": provisional}


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------
def zipf_row(recs, theta, B):
    return z.analyze(recs, thetas=(theta,), B=B, seed=SEED, nulls=FULL_NULLS,
                     heldout=False)["by_theta"][str(theta)]


def run_step(fn, *a):
    t1 = time.time()
    try:
        r = fn(*a)
        if isinstance(r, dict):
            r["seconds"] = time.time() - t1
        return r
    except Exception as e:                       # recorded, never hidden
        return {"error": repr(e)[:500]}


def analyse(data, t0, budget_s, b_main=200, b_rob=100, b_kirby=200, log=print):
    """data[bird] = (phrase sequences, blocks). Order: ladders, held-out D1, main
    Zipf (theta 0.5), Kirby size, then robustness (skipped past 60% of the budget)."""
    res = {b: {} for b in data}
    for b, (phr, blocks) in data.items():
        res[b]["ladder"] = run_step(ladder, phr)
        res[b]["heldout_blocks"] = run_step(heldout_block, blocks)
        log("ladder", b, res[b]["ladder"].get("best"), res[b]["ladder"].get("gains"))
    for b, (phr, blocks) in data.items():
        res[b]["by_theta"] = {}
        r = run_step(zipf_row, blocks, 0.5, b_main)
        if "error" in r:
            res[b].setdefault("errors", {})["0.5"] = r
        else:
            res[b]["by_theta"]["0.5"] = r
        log("zipf 0.5", b, r.get("real_mean_r2"), {k: v["p"] for k, v in r.get("nulls", {}).items()})
    for b, (phr, blocks) in data.items():
        ks = [first_until(x) for x in blocks]
        res[b]["kirby_describe"] = describe(ks)
        r = run_step(zipf_row, ks, 0.5, b_kirby)
        if "error" in r:
            res[b].setdefault("errors", {})["kirby"] = r
        else:
            res[b]["kirby"] = r
    for th in (0.3, 0.7):
        for b, (phr, blocks) in data.items():
            if time.time() - t0 > 0.6 * budget_s:
                res[b].setdefault("not_run", []).append("theta %s (time budget)" % th)
                continue
            r = run_step(zipf_row, blocks, th, b_rob)
            if "error" in r:
                res[b].setdefault("errors", {})[str(th)] = r
            else:
                res[b]["by_theta"][str(th)] = r
    return res


# --------------------------------------------------------------------------
# I/O
# --------------------------------------------------------------------------
def fetch(url, timeout=120):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def load_bird_csvs(key, size, cache, log):
    """{csv member name: text} for one bird's zip, cached (gzip json) in the data volume."""
    if os.path.exists(cache):
        with gzip.open(cache, "rt", encoding="utf-8") as f:
            return json.load(f), {"source": "cache"}
    url = ZENODO % key
    info = {"url": url}
    try:
        rr = http_range_reader(url, log)
        members, zi = list_zip(rr, size)
        if rr.state["total"] is not None and rr.state["total"] != size:
            raise ValueError("archive is %d bytes, registered %d" % (rr.state["total"], size))
        want = [m for m in members if is_annotation_csv(m["name"])]
        info.update({"mode": "range", "members": len(members), "zip64": zi["zip64"],
                     "csv_members": [m["name"] for m in want],
                     "wav_members": sum(1 for m in members
                                        if m["name"].lower().endswith(".wav"))})
        texts = {m["name"]: member_bytes(rr, m).decode("utf-8-sig", "replace") for m in want}
        info["requests"] = rr.state["requests"]
        info["bytes_read"] = rr.state["bytes"]
    except RangeUnsupported as e:
        info.update({"mode": "stream", "range_error": str(e)})
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=900) as resp:
            blobs = stream_zip_members(resp, is_annotation_csv)
        texts = {k: v.decode("utf-8-sig", "replace") for k, v in blobs.items()}
        info["csv_members"] = sorted(texts)
    with gzip.open(cache, "wt", encoding="utf-8") as f:
        json.dump(texts, f)
    return texts, info


def wait_for_registration(max_minutes):
    t0 = time.time()
    tries = 0
    last = None
    while True:
        tries += 1
        try:
            blob = fetch(PREREG_URL, timeout=60)
            if b"CANARY-PREREG" in blob:
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
    ap.add_argument("--data-dir", default="/data/canary")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--max-minutes", type=float, default=200)
    ap.add_argument("--wait-minutes", type=float, default=90)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    os.makedirs(a.data_dir, exist_ok=True)
    out_path = os.path.join(a.out_dir, "canary_results.json")
    out = {"version": VERSION, "python": sys.version.split()[0],
           "zipfseg_sha256": hashlib.sha256(open(z.__file__, "rb").read()).hexdigest(),
           "canary_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest()}
    t0 = time.time()
    reg = wait_for_registration(a.wait_minutes)
    out["registration"] = reg
    if not reg["found"]:
        out["status"] = "not_run_unregistered"
        dump(out, out_path)
        print("CANARY-PREREG.md not public; nothing read")
        return 4
    t0 = time.time()
    data, stats, gates, reads = {}, {}, {}, {}
    for bird, key, size, _md5 in BIRDS:
        log = []
        try:
            texts, info = load_bird_csvs(key, size, os.path.join(a.data_dir, bird + ".csvs.json.gz"),
                                         log)
        except Exception as e:
            reads[bird] = {"error": repr(e)[:500], "log": log[-20:]}
            gates[bird] = {"pass": False, "error": "not read"}
            print(bird, "read failed", repr(e)[:200], flush=True)
            continue
        info["log"] = log[-20:]
        reads[bird] = info
        phr, st = bird_inputs(texts)
        del texts
        gates[bird] = gate_bird(st)
        blocks = make_blocks(phr)
        st["blocks"] = describe(blocks)
        stats[bird] = st
        if blocks:
            data[bird] = (phr, blocks)
        print(bird, st["syllables"], "syllables", st["songs"], "songs", st["phrases"],
              "phrases", st["phrase_types"], "phrase types", len(blocks), "blocks",
              "gate", gates[bird]["pass"], flush=True)
    out.update({"reads": reads, "stats": stats, "gates": gates, "status": "analysing"})
    dump(out, out_path)
    res = analyse(data, t0, a.max_minutes * 60)
    gr = grade(res, gates)
    out.update({"status": "ok", "results": res, "grading": gr, "seconds": time.time() - t0})
    dump(out, out_path)
    print(json.dumps({"rules": gr["rules"], "labels": gr["labels"],
                      "predictions": gr["predictions"], "brier": gr["brier"],
                      "per_bird": gr["per_bird"], "provisional": gr["provisional"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
