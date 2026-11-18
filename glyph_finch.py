# SPDX-License-Identifier: Apache-2.0
# song-zipf-test, finch reading step v2 (PREREG-AMENDMENT-4.md): read the Kirby et al. 2026
# (Sci. Adv. eaea3015) supplementary "Dataset" pages from their vector geometry instead of OCR.
#
# Every glyph on those pages is one filled vector path and the table rows are filled
# rectangles (bird, day and sequence cells). So:
#   * glyphs are grouped into classes by their exact outline (same letter = same outline);
#   * each glyph is placed in a row band and a column by its centre;
#   * a printed space is a horizontal gap between outlines wider than SPACE_GAP points;
#   * class -> character: bird-name classes are solved from the six known bird names,
#     digit classes from the 30 known (bird, age) pairs, and the remaining sequence classes
#     are labelled by single-character Tesseract (labels do not change any count or
#     statistic: the analysis only needs classes to be distinct and consistent).
# The result is validated by the UNCHANGED registered gate (finch_parse.validate / gate).
# No Zipf or null-model statistic is computed here (job_analyze.py does that, unchanged,
# only if the gate passes).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import hashlib
import io
import json
import os
import random
import subprocess
import urllib.request
import zipfile
from collections import Counter

import finch_parse as fp

URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13450306/supplementaryFiles"
UA = "MV2-research/1.0 (Munim, Inc.; mv2@munimtech.com)"
SM = "sciadv.aea3015_sm.pdf"
SM_SHA256 = "1c91799782c41a812287deca4779eaf666cf0f82b812f281f503559310895740"
CONFIG = "glyph_v1"

GLYPH_MAX = 12.0        # glyph outlines are < 12 pt in both directions
COORD_TOL = 0.08        # same class if every relative coordinate agrees within this (pt)
SEQ_MIN_WIDTH = 300.0   # sequence cells are ~440 pt wide
BAND_MIN_H = 8.0
BAND_MAX_H = 600.0
LINE_GAP = 4.0          # a new text line starts when glyph centres jump by more (pitch ~11 pt)
SPACE_GAP = 2.25        # printed space: gap > 2.25 pt (probe: letters <= 1.75, spaces >= 2.75)
SENS_SPACE_GAPS = (2.0, 2.5)
DEFAULT_X_DAY = 114.0   # day-cell left edge seen on pages 49-50 (fallback only)
N_CHECK_ROWS = 24
CHECK_SEED = 20261118
OCR_WHITELIST = "abcdefghijklmnopqrstuvwxyz"
FALLBACK_POOL = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                 + "".join(chr(c) for c in range(0x3B1, 0x3CA)))


# --------------------------------------------------------------------------
# pure functions (no third-party imports; tested in test_glyph_finch.py)
# --------------------------------------------------------------------------
def lum(fill):
    """Approximate lightness 0 (black) .. 1 (white) of a PDF fill colour."""
    if fill is None:
        return None
    f = [float(v) for v in fill]
    if len(f) == 1:
        return f[0]
    if len(f) == 3:
        return sum(f) / 3.0
    if len(f) == 4:                       # CMYK
        return (1.0 - f[3]) * (1.0 - sum(f[:3]) / 3.0)
    return None


def item_points(items):
    """(kinds string, list of (x, y)) from PyMuPDF drawing items."""
    kinds = []
    pts = []
    for it in items:
        if not it:
            continue
        kinds.append(str(it[0])[:1])
        for obj in it[1:]:
            if hasattr(obj, "x") and hasattr(obj, "y"):
                pts.append((float(obj.x), float(obj.y)))
            elif hasattr(obj, "x0") and hasattr(obj, "y1"):
                pts.append((float(obj.x0), float(obj.y0)))
                pts.append((float(obj.x1), float(obj.y1)))
            elif hasattr(obj, "ul") and hasattr(obj, "lr"):
                for q in (obj.ul, obj.ur, obj.ll, obj.lr):
                    pts.append((float(q.x), float(q.y)))
    return "".join(kinds), pts


def make_glyph(page, rect, kinds, pts):
    x0, y0, x1, y1 = (float(v) for v in rect)
    coords = tuple(v for p in pts for v in (p[0] - x0, p[1] - y0))
    return {"page": page, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "kinds": kinds, "coords": coords, "cls": None}


def classify(glyphs, tol=COORD_TOL):
    """Assign g['cls'] in place; return the class list (first-seen order)."""
    by_kinds = {}
    classes = []
    for g in glyphs:
        cands = by_kinds.setdefault((g["kinds"], len(g["coords"])), [])
        cid = None
        for c_id, coords in cands:
            if max((abs(a - b) for a, b in zip(coords, g["coords"])), default=0.0) <= tol:
                cid = c_id
                break
        if cid is None:
            cid = len(classes)
            classes.append({"kinds": g["kinds"], "n_points": len(g["coords"]) // 2, "n": 0,
                            "w": round(g["x1"] - g["x0"], 3), "h": round(g["y1"] - g["y0"], 3),
                            "ex": {k: g[k] for k in ("page", "x0", "y0", "x1", "y1")}})
            cands.append((cid, g["coords"]))
        g["cls"] = cid
        classes[cid]["n"] += 1
    return classes


def possible_splits(classes):
    """Groups of classes with the same kinds and the same size to 0.1 pt (diagnostic:
    one letter split into two classes would show up here)."""
    grp = {}
    for cid, c in enumerate(classes):
        grp.setdefault((c["kinds"], round(c["w"], 1), round(c["h"], 1)), []).append(cid)
    return [v for v in grp.values() if len(v) > 1]


def find_bands(rects):
    """Row bands from light filled rectangles (x0, y0, x1, y1): one per sequence cell,
    with the left edges of the bird and day cells in the same row when present."""
    seq = sorted((r for r in rects if r[2] - r[0] >= SEQ_MIN_WIDTH
                  and BAND_MIN_H <= r[3] - r[1] <= BAND_MAX_H), key=lambda r: (r[1], r[0]))
    bands = []
    for s in seq:
        if bands and abs(bands[-1]["y0"] - s[1]) < 0.3 and abs(bands[-1]["y1"] - s[3]) < 0.3:
            continue                                  # same cell drawn twice
        left = sorted((r for r in rects if r[2] - r[0] < SEQ_MIN_WIDTH
                       and abs(r[1] - s[1]) <= 0.6 and abs(r[3] - s[3]) <= 0.6
                       and r[2] <= s[0] + 0.6), key=lambda r: r[0])
        bands.append({"y0": s[1], "y1": s[3], "x_seq": s[0],
                      "x_day": left[-1][0] if len(left) >= 2 else None,
                      "x_bird": left[0][0] if left else None, "n_left": len(left)})
    return bands


def assign_columns(glyphs, bands, default_x_day=DEFAULT_X_DAY):
    cols = [{"bird": [], "day": [], "seq": []} for _ in bands]
    outside = []
    for g in glyphs:
        cx = (g["x0"] + g["x1"]) / 2.0
        cy = (g["y0"] + g["y1"]) / 2.0
        k = None
        for i, b in enumerate(bands):
            if b["y0"] <= cy < b["y1"]:
                k = i
                break
        if k is None:
            outside.append(g)
            continue
        b = bands[k]
        xd = b["x_day"] if b["x_day"] is not None else default_x_day
        if cx >= b["x_seq"]:
            cols[k]["seq"].append(g)
        elif cx >= xd:
            cols[k]["day"].append(g)
        else:
            cols[k]["bird"].append(g)
    return cols, outside


def text_lines(gl, line_gap=LINE_GAP):
    """Glyphs -> lines (top to bottom), each sorted left to right."""
    if not gl:
        return []
    order = sorted(gl, key=lambda g: ((g["y0"] + g["y1"]) / 2.0, g["x0"]))
    lines = [[order[0]]]
    prev = (order[0]["y0"] + order[0]["y1"]) / 2.0
    for g in order[1:]:
        c = (g["y0"] + g["y1"]) / 2.0
        if c - prev > line_gap:
            lines.append([g])
        else:
            lines[-1].append(g)
        prev = c
    return [sorted(L, key=lambda g: g["x0"]) for L in lines]


def cls_seq(gl):
    return tuple(g["cls"] for L in text_lines(gl) for g in L)


def words_and_gaps(line, labels, space_gap=SPACE_GAP):
    words = []
    gaps = []
    cur = ""
    prev = None
    for g in line:
        if prev is not None:
            gap = g["x0"] - prev["x1"]
            gaps.append(gap)
            if gap > space_gap and cur:
                words.append(cur)
                cur = ""
        cur += labels[g["cls"]]
        prev = g
    if cur:
        words.append(cur)
    return words, gaps


def _extend(c2ch, ch2c, seq, text):
    """Extend an injective class->char map with seq->text; None if inconsistent."""
    nc = dict(c2ch)
    nh = dict(ch2c)
    for c, ch in zip(seq, text):
        if nc.get(c, ch) != ch or nh.get(ch, c) != c:
            return None
        nc[c] = ch
        nh[ch] = c
    return nc, nh


def solve_names(seq_counts, names=None, limit=2):
    """Map the most frequent bird-cell class sequences to the known bird names so that
    the class->letter map is consistent and injective. Returns (solutions, seqs used);
    each solution is (seq -> name, class -> char)."""
    names = list(names or fp.DAYS)
    seqs = [s for s, _ in sorted(seq_counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    seqs = seqs[:len(names)]
    sols = []

    def rec(i, used, c2ch, ch2c, assign):
        if len(sols) >= limit:
            return
        if i == len(seqs):
            sols.append((dict(assign), dict(c2ch)))
            return
        s = seqs[i]
        for nm in names:
            if nm in used or len(nm) != len(s):
                continue
            ext = _extend(c2ch, ch2c, s, nm)
            if ext is None:
                continue
            assign[s] = nm
            rec(i + 1, used | {nm}, ext[0], ext[1], assign)
            del assign[s]

    rec(0, frozenset(), {}, {}, {})
    return sols, seqs


def solve_days(pair_counts, days=None, limit=2):
    """pair_counts: {(bird, digit-class tuple): n}. Find an injective class->digit map
    under which every pair is a distinct registered (bird, age). If no map fits all
    pairs, retry with the 30 most frequent pairs. Returns (solutions, pairs used)."""
    days = days or fp.DAYS
    n_rec = sum(len(v) for v in days.values())

    def run(pairs):
        pairs = sorted(pairs, key=lambda p: (p[0], -len(p[1]), p[1]))
        sols = []

        def rec(i, c2d, d2c, used):
            if len(sols) >= limit:
                return
            if i == len(pairs):
                sols.append(dict(c2d))
                return
            bird, seq = pairs[i]
            for day in days.get(bird, []):
                sd = str(day)
                if len(sd) != len(seq) or (bird, day) in used:
                    continue
                ext = _extend(c2d, d2c, seq, sd)
                if ext is not None:
                    rec(i + 1, ext[0], ext[1], used | {(bird, day)})

        rec(0, {}, {}, frozenset())
        return sols

    allp = list(pair_counts)
    sols = run(allp)
    if sols or len(allp) <= n_rec:
        return sols, allp
    top = [p for p, _ in sorted(pair_counts.items(), key=lambda kv: (-kv[1], kv[0]))][:n_rec]
    return run(top), top


def assign_labels(seq_counts, name_labels, ocr_labels):
    """Single-character, injective labels for every class used in sequences.
    Priority: bird-name letters, then OCR (most frequent class first), then a
    fallback pool. Returns (labels, sources)."""
    labels = {}
    sources = {}
    used = set()
    reserved = set(name_labels.values())
    order = sorted(seq_counts, key=lambda c: (-seq_counts[c], c))
    for c in order:
        if c in name_labels:
            labels[c] = name_labels[c]
            sources[c] = "name"
            used.add(labels[c])
    pending = []
    for c in order:
        if c in labels:
            continue
        ch = ocr_labels.get(c, "") or ""
        if len(ch) == 1 and ch.isalpha() and ch not in used and ch not in reserved:
            labels[c] = ch
            sources[c] = "ocr"
            used.add(ch)
        else:
            pending.append(c)
    pool = [ch for ch in FALLBACK_POOL if ch not in used and ch not in reserved]
    for c in pending:
        labels[c] = pool.pop(0)
        sources[c] = "fallback"
    return labels, sources


def build_rows(banded, bird_of, digit_of, labels, space_gap=SPACE_GAP):
    """banded: [(page, band, cols)] in reading order. Returns (rows, stats, seq gaps)."""
    rows = []
    st = Counter()
    gaps = []
    cur = None
    for page, b, cols in banded:
        bs = cls_seq(cols["bird"])
        ds = cls_seq(cols["day"])
        lines = text_lines(cols["seq"])
        if not bs and not ds:
            if cur is not None and lines:
                st["continuation_bands"] += 1
                cur["bands"].append([page, round(b["y0"], 3), round(b["y1"], 3)])
                for L in lines:
                    n = sum(len(w) for w in cur["words"])
                    if n:
                        cur["wraps"].append(n)
                    ws, gs = words_and_gaps(L, labels, space_gap)
                    cur["words"].extend(ws)
                    gaps.extend(gs)
            else:
                st["empty_bands"] += 1
            continue
        bird = bird_of.get(bs)
        day = "".join(digit_of.get(c, "?") for c in ds)
        if bird is None or not day.isdigit():
            st["unreadable_header"] += 1
            cur = None
            continue
        if int(day) not in fp.DAYS[bird]:
            st["day_not_registered"] += 1
            cur = None
            continue
        cur = {"bird": bird, "day": int(day), "cost": 0, "words": [], "wraps": [],
               "bad_chars": 0, "bands": [[page, round(b["y0"], 3), round(b["y1"], 3)]]}
        for i, L in enumerate(lines):
            if i > 0:
                n = sum(len(w) for w in cur["words"])
                if n:
                    cur["wraps"].append(n)
            ws, gs = words_and_gaps(L, labels, space_gap)
            cur["words"].extend(ws)
            gaps.extend(gs)
        rows.append(cur)
        st["rows"] += 1
    return rows, dict(st), gaps


def gap_hist(gaps, lo=-2.0, hi=12.0, step=0.25):
    h = Counter(round(round(g / step) * step, 2) for g in gaps if lo <= g <= hi)
    return {str(k): v for k, v in sorted(h.items())}


def read_dataset(pages_data, ocr=None, space_gap=SPACE_GAP, tol=COORD_TOL):
    """pages_data: [(page number, glyphs, light rects)]. ocr: optional callable
    (class id, class info) -> char. Returns everything the job writes."""
    all_glyphs = [g for _, gl, _ in pages_data for g in gl]
    classes = classify(all_glyphs, tol)
    banded = []
    n_outside = 0
    n_bands = 0
    bands_without_day_cell = 0
    for page, gl, rects in pages_data:
        bands = find_bands(rects)
        if not bands:
            n_outside += len(gl)
            continue
        n_bands += len(bands)
        xs = [round(b["x_day"], 1) for b in bands if b["x_day"] is not None]
        xd = Counter(xs).most_common(1)[0][0] if xs else DEFAULT_X_DAY
        bands_without_day_cell += sum(1 for b in bands if b["x_day"] is None)
        cols, out = assign_columns(gl, bands, xd)
        n_outside += len(out)
        banded.extend((page, b, c) for b, c in zip(bands, cols))

    name_counts = Counter(cls_seq(c["bird"]) for _, _, c in banded if c["bird"])
    nsols, nseqs = solve_names(name_counts)
    bird_of, name_lab = nsols[0] if nsols else ({}, {})

    pair_counts = Counter()
    for _, _, c in banded:
        bs = cls_seq(c["bird"])
        if bs in bird_of and c["day"]:
            pair_counts[(bird_of[bs], cls_seq(c["day"]))] += 1
    dsols, dpairs = solve_days(pair_counts)
    digit_of = dsols[0] if dsols else {}

    seq_counts = Counter(g["cls"] for _, _, c in banded for g in c["seq"])
    ocr_lab = {}
    if ocr is not None:
        for cid in sorted(seq_counts):
            if cid not in name_lab:
                try:
                    ocr_lab[cid] = ocr(cid, classes[cid]) or ""
                except Exception:          # OCR is only for labels; never fatal
                    ocr_lab[cid] = ""
    labels, sources = assign_labels(seq_counts, name_lab, ocr_lab)
    rows, st, gaps = build_rows(banded, bird_of, digit_of, labels, space_gap)

    all_labels = {}
    for c, ch in name_lab.items():
        all_labels[c] = ch
    for c, ch in digit_of.items():
        all_labels[c] = ch
    all_labels.update(labels)
    diag = {
        "n_glyphs": len(all_glyphs), "n_classes": len(classes), "n_bands": n_bands,
        "n_glyphs_outside_bands": n_outside,
        "bands_without_day_cell": bands_without_day_cell,
        "bird_cell_sequences": [{"classes": list(s), "count": n,
                                 "name": bird_of.get(s)}
                                for s, n in sorted(name_counts.items(), key=lambda kv: -kv[1])],
        "name_solutions": len(nsols), "day_solutions": len(dsols),
        "day_pairs_used": len(dpairs), "day_pairs_seen": len(pair_counts),
        "seq_classes": len(seq_counts),
        "label_sources": dict(Counter(sources.values())),
        "seq_gap_hist_0.25pt": gap_hist(gaps),
        "seq_gaps_ambiguous_1.9_2.6": sum(1 for g in gaps if 1.9 < g <= 2.6),
        "seq_gaps_negative": sum(1 for g in gaps if g < 0),
        "possible_class_splits": possible_splits(classes),
        "build_stats": st,
    }
    return {"rows": rows, "stats": st, "classes": classes, "labels": labels,
            "all_labels": all_labels, "sources": sources, "ocr_labels": ocr_lab,
            "bird_of": bird_of, "digit_of": digit_of, "banded": banded, "diag": diag}


# --------------------------------------------------------------------------
# PDF side (PyMuPDF + Tesseract; only in the job)
# --------------------------------------------------------------------------
def load_pdf(data_dir):
    """The supplement zip cached by earlier jobs (data_key song-zipf); downloaded from
    Europe PMC only if the cache is missing."""
    path = os.path.join(data_dir, "song", "finch_suppl.zip")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        blob = open(path, "rb").read()
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=300) as r:
            blob = r.read()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = "%s.%d.part" % (path, os.getpid())
        with open(tmp, "wb") as f:
            f.write(blob)
        os.replace(tmp, path)
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        pdf = zf.read(SM)
    return pdf, hashlib.sha256(pdf).hexdigest()


def dataset_pages(doc):
    cap = None
    for i in range(doc.page_count):
        if "Dataset: The complete set of songs" in " ".join(doc[i].get_text("text").split()):
            cap = i
    if cap is None:
        raise SystemExit("Dataset caption page not found")
    return cap, list(range(cap, doc.page_count))


def extract_page(page, pno):
    glyphs = []
    rects = []
    for d in page.get_drawings():
        r = d.get("rect")
        L = lum(d.get("fill"))
        if r is None or L is None:
            continue
        w, h = r.width, r.height
        if d.get("type") in ("f", "fs") and L < 0.5 and w < GLYPH_MAX and h < GLYPH_MAX:
            kinds, pts = item_points(d.get("items") or [])
            glyphs.append(make_glyph(pno, (r.x0, r.y0, r.x1, r.y1), kinds, pts))
        elif L >= 0.85:
            rects.append((float(r.x0), float(r.y0), float(r.x1), float(r.y1)))
    return glyphs, rects


def glyph_doc(doc, ex, pad=6.0):
    import fitz
    w = ex["x1"] - ex["x0"]
    h = ex["y1"] - ex["y0"]
    tmp = fitz.open()
    pg = tmp.new_page(width=w + 2 * pad + 0.3, height=h + 2 * pad + 0.3)
    clip = fitz.Rect(ex["x0"] - 0.15, ex["y0"] - 0.15, ex["x1"] + 0.15, ex["y1"] + 0.15)
    pg.show_pdf_page(fitz.Rect(pad, pad, pad + w + 0.3, pad + h + 0.3), doc, ex["page"] - 1,
                     clip=clip)
    return tmp, pg


def make_ocr(doc, tmpdir):
    import fitz

    def ocr(cid, info):
        tmp, pg = glyph_doc(doc, info["ex"])
        png = os.path.join(tmpdir, "cls_%d.png" % cid)
        pg.get_pixmap(dpi=800, colorspace=fitz.csGRAY).save(png)
        tmp.close()
        r = subprocess.run(["tesseract", png, "stdout", "--psm", "10",
                            "-c", "tessedit_char_whitelist=" + OCR_WHITELIST],
                           capture_output=True, text=True, timeout=120)
        t = "".join(r.stdout.split())
        return t[:1]
    return ocr


def class_sheet(doc, classes, labels, path, ncol=8, cw=80.0, chh=60.0):
    import fitz
    order = sorted(range(len(classes)), key=lambda c: (-classes[c]["n"], c))
    nrow = max(1, (len(order) + ncol - 1) // ncol)
    sheet = fitz.open()
    pg = sheet.new_page(width=ncol * cw, height=nrow * chh)
    for k, c in enumerate(order):
        ex = classes[c]["ex"]
        x = (k % ncol) * cw
        y = (k // ncol) * chh
        clip = fitz.Rect(ex["x0"] - 0.15, ex["y0"] - 0.15, ex["x1"] + 0.15, ex["y1"] + 0.15)
        pg.show_pdf_page(fitz.Rect(x + 6, y + 4, x + cw - 6, y + chh - 16), doc, ex["page"] - 1,
                         clip=clip)
        lab = labels.get(c, "-")
        if not (lab.isascii() and lab.isprintable()):
            lab = "u%04x" % ord(lab[0])
        pg.insert_text((x + 4, y + chh - 5), "%d:%s n=%d" % (c, lab, classes[c]["n"]),
                       fontsize=7)
    pg.get_pixmap(dpi=150).save(path)


def main():
    import fitz

    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    a = ap.parse_args()
    out = a.out_dir
    os.makedirs(os.path.join(out, "check"), exist_ok=True)
    tmpdir = "/tmp/glyph_finch_%d" % os.getpid()
    os.makedirs(tmpdir, exist_ok=True)

    pdf, sha = load_pdf(a.data_dir)
    doc = fitz.open(stream=pdf, filetype="pdf")
    cap, pages = dataset_pages(doc)
    pages_data = []
    page_info = []
    for p in pages:
        gl, rects = extract_page(doc[p], p + 1)
        pages_data.append((p + 1, gl, rects))
        page_info.append({"page": p + 1, "glyphs": len(gl), "light_rects": len(rects)})
    res = read_dataset(pages_data, ocr=make_ocr(doc, tmpdir))
    rows = res["rows"]
    v = fp.validate(rows)

    # spacing sensitivity (diagnostic only; the registered reading uses SPACE_GAP)
    sens = {}
    for sg in SENS_SPACE_GAPS:
        r2, _, _ = build_rows(res["banded"], res["bird_of"], res["digit_of"], res["labels"], sg)
        v2 = fp.validate(r2)
        sens[str(sg)] = {"printed_cuts": v2["printed_cuts"], "cut_agreement": v2["cut_agreement"],
                         "gate": v2["gate"]}

    info = {"sm_sha256": sha, "sha_matches_inventory": sha == SM_SHA256,
            "caption_page": cap + 1, "dataset_pages": [p + 1 for p in pages], "pages": page_info,
            "space_gap": SPACE_GAP, "coord_tol": COORD_TOL}
    st = dict(res["stats"])
    summary = {"info": info, "best_config": CONFIG,
               "configs": [{"config": CONFIG, "parse_stats": st, "validation": v,
                            "stderr_tail": []}],
               "gate": v["gate"], "glyph": res["diag"], "space_gap_sensitivity": sens}
    with open(os.path.join(out, "validation.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)

    # parsed rows stay on the job's /out (finch data are CC BY-NC; not redistributed)
    with open(os.path.join(out, "finch_parsed.json"), "w", encoding="utf-8") as f:
        json.dump({"config": CONFIG, "rows": rows}, f)
    with open(os.path.join(out, "finch_parsed.tsv"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write("%s\t%d\t%s\t%s\n" % (r["bird"], r["day"], " ".join(r["words"]),
                                          ",".join(map(str, r["wraps"]))))

    cls_out = []
    for cid, c in enumerate(res["classes"]):
        cls_out.append({"id": cid, "label": res["all_labels"].get(cid),
                        "source": res["sources"].get(cid) or (
                            "day" if cid in res["digit_of"] else
                            ("name" if cid in res["all_labels"] else None)),
                        "ocr": res["ocr_labels"].get(cid), "n": c["n"], "kinds": c["kinds"],
                        "n_points": c["n_points"], "w": c["w"], "h": c["h"], "ex": c["ex"]})
    with open(os.path.join(out, "glyph_classes.json"), "w", encoding="utf-8") as f:
        json.dump(cls_out, f, indent=1)
    try:
        class_sheet(doc, res["classes"], res["all_labels"], os.path.join(out, "class_sheet.png"))
    except Exception as e:                      # diagnostics must not stop the job
        print("class sheet failed:", repr(e)[:300])

    # hand-check material: N random rows, rendered, with the reading next to them
    rng = random.Random(CHECK_SEED)
    pick = sorted(rng.sample(range(len(rows)), min(N_CHECK_ROWS, len(rows))))
    with open(os.path.join(out, "check", "check_rows.tsv"), "w", encoding="utf-8") as f:
        f.write("k\trow\tpage\ty0\tbird\tday\treading (| = line wrap)\n")
        for k, i in enumerate(pick):
            r = rows[i]
            pno, y0, y1 = r["bands"][0]
            try:
                doc[pno - 1].get_pixmap(dpi=200, clip=fitz.Rect(72, y0, 586, y1)).save(
                    os.path.join(out, "check", "row_%02d.png" % k))
            except Exception as e:
                print("render failed", k, repr(e)[:200])
            text = []
            pos = 0
            wraps = set(r["wraps"])
            for w in r["words"]:
                text.append(("| " if pos in wraps and pos > 0 else "") + w)
                pos += len(w)
            f.write("%d\t%d\t%d\t%.2f\t%s\t%d\t%s\n" % (k, i, pno, y0, r["bird"], r["day"],
                                                        " ".join(text)))

    print(json.dumps({"gate": v["gate"], "n_exact": v["n_exact"], "exact": v["exact"],
                      "recordings_found": v["recordings_found"], "bouts": v["bouts"],
                      "syllables": v["syllables"], "transitions": v["transitions"],
                      "pipeline_cuts": v["pipeline_cuts"], "pipeline_types": v["pipeline_types"],
                      "printed_cuts": v["printed_cuts"], "f1": v["cut_agreement"]["f1"],
                      "glyph": {k: res["diag"][k] for k in
                                ("n_glyphs", "n_classes", "n_bands", "name_solutions",
                                 "day_solutions", "seq_classes", "label_sources",
                                 "build_stats")}}, indent=1, default=str))
    print("GATE", v["gate"])


if __name__ == "__main__":
    main()
