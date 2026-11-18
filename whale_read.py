# SPDX-License-Identifier: Apache-2.0
# whale_read.py: read the song strings of Arnon et al. 2025 (Science 387:649, Data S2)
# into {year: [recording, ...]} where a recording is a list of sound-element codes.
#
# Registered in PREREG-AMENDMENT-3.md BEFORE the data files were opened by anyone working
# for MV2. The file format is not known yet, so this reader tries a fixed, short list of
# layouts and accepts a layout ONLY if it passes a gate built from the paper's own
# Table S1 (recordings and sound elements per year). If no layout passes, or two layouts
# pass with different contents, nothing is analysed and the reading step is fixed in a
# later, separately published amendment (format only).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import csv
import io
import os
import re

# Table S1 of the paper: year -> (recordings, sound elements)
TABLE_S1 = {2010: (4, 1053), 2011: (6, 2028), 2012: (6, 3351), 2013: (6, 2664),
            2014: (7, 5765), 2015: (12, 13251), 2016: (7, 8469), 2017: (7, 9179)}
ELEMENT_TOL = 0.02          # per-year element count must be within 2% of Table S1
MIN_TOKENS = 10             # a recording has at least this many elements
_YEAR = re.compile(r"(?<!\d)(201[0-7])(?!\d)")
_SPLIT = re.compile(r"[\s,;]+")
_STRIP = "[]'\"`"
_TEXT_EXT = (".csv", ".tsv", ".txt")
_HDR_YEAR = re.compile(r"year", re.I)
_HDR_REC = re.compile(r"record|file|song|singer|session|\bid\b", re.I)
_HDR_EL = re.compile(r"element|unit|sound|code|label|type|string", re.I)


def year_of(text):
    m = _YEAR.search(str(text))
    return int(m.group(1)) if m else None


def tokens(cell):
    out = []
    for t in _SPLIT.split(str(cell).strip()):
        t = t.strip(_STRIP)
        if t:
            out.append(t)
    return out


# --------------------------------------------------------------------------
# tables
# --------------------------------------------------------------------------
def text_table(name, data):
    """bytes -> list of rows (lists of str). .tsv or tab-separated -> tab; .csv -> csv;
    other text -> one cell per line."""
    try:
        txt = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        txt = data.decode("latin-1")
    lines = txt.splitlines()
    low = name.lower()
    first = lines[0] if lines else ""
    if low.endswith(".tsv") or "\t" in first:
        return [ln.split("\t") for ln in lines]
    if low.endswith(".csv"):
        return [row for row in csv.reader(io.StringIO(txt))]
    return [[ln] for ln in lines]


def xlsx_tables(name, data):
    """[(sheet name, rows)] from an .xlsx file (needs openpyxl)."""
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out = []
    for ws in wb.worksheets:
        rows = []
        for r in ws.iter_rows(values_only=True):
            rows.append(["" if v is None else str(v) for v in r])
        out.append((ws.title, rows))
    return out


def load_files(root):
    """{file path relative to root: [(table name, rows)]} for every text/xlsx file."""
    files = {}
    for dp, dns, fns in os.walk(root):
        dns.sort()
        for fn in sorted(fns):
            path = os.path.join(dp, fn)
            rel = os.path.relpath(path, root).replace("\\", "/")
            low = fn.lower()
            data = open(path, "rb").read()
            if low.endswith(".xlsx"):
                try:
                    files[rel] = [(rel + "::" + s, rows) for s, rows in xlsx_tables(rel, data)]
                except Exception:
                    continue
            elif low.endswith(_TEXT_EXT):
                files[rel] = [(rel, text_table(rel, data))]
    return files


# --------------------------------------------------------------------------
# layouts (each returns {year: [recording tokens, ...]} or {})
# --------------------------------------------------------------------------
def layout_row(name, rows):
    """One row per recording: the row's cell with the most tokens is the song string;
    the year is the first year found in the row's other cells, else in the table name."""
    out = {}
    for row in rows:
        if not row:
            continue
        toks = [tokens(c) for c in row]
        j = max(range(len(row)), key=lambda i: len(toks[i]))
        if len(toks[j]) < MIN_TOKENS:
            continue
        y = None
        for i, c in enumerate(row):
            if i != j:
                y = year_of(c)
                if y:
                    break
        y = y or year_of(name)
        if y:
            out.setdefault(y, []).append(toks[j])
    return out


def layout_long(name, rows):
    """Header row, then one row per sound element; columns found by header name.
    Consecutive rows with the same (year, recording) form one recording, in file order."""
    if len(rows) < 2:
        return {}
    hdr = rows[0]
    yc = [i for i, h in enumerate(hdr) if _HDR_YEAR.search(h)]
    rc = [i for i, h in enumerate(hdr) if _HDR_REC.search(h) and i not in yc]
    ec = [i for i, h in enumerate(hdr) if _HDR_EL.search(h) and i not in yc and i not in rc]
    if not rc or not ec:
        return {}
    yc, rc, ec = (yc[0] if yc else None), rc[0], ec[0]
    out = {}
    key, cur = None, None
    for row in rows[1:]:
        if len(row) <= max(rc, ec, -1 if yc is None else yc):
            continue
        el = str(row[ec]).strip().strip(_STRIP)
        if not el:
            continue
        y = year_of(row[yc]) if yc is not None else year_of(row[rc])
        y = y or year_of(name)
        k = (y, row[rc])
        if k != key:
            key = k
            cur = []
            if y:
                out.setdefault(y, []).append(cur)
        if y:
            cur.append(el)
    return {y: [r for r in recs if r] for y, recs in out.items()}


def layout_col(name, rows):
    """One column per recording: the header names the recording (it must contain a year
    or a word like 'recording'/'song'/'file'); the year is the header's, else the table
    name's; the column's non-empty cells, in order, are the elements."""
    if len(rows) < MIN_TOKENS + 1:
        return {}
    width = max(len(r) for r in rows)
    out = {}
    for j in range(width):
        h = rows[0][j] if j < len(rows[0]) else ""
        if not (year_of(h) or _HDR_REC.search(h)):
            continue
        y = year_of(h) or year_of(name)
        seq = []
        for r in rows[1:]:
            if j < len(r):
                seq.extend(tokens(r[j]))
        if y and len(seq) >= MIN_TOKENS:
            out.setdefault(y, []).append(seq)
    return out


def layout_file(name, rows):
    """The whole table is one recording (all tokens of all cells, in order); the year
    comes from the table name (for example a folder per year, a file per recording)."""
    y = year_of(name)
    seq = [t for row in rows for c in row for t in tokens(c)]
    if y and len(seq) >= MIN_TOKENS:
        return {y: [seq]}
    return {}


LAYOUTS = {"row": layout_row, "long": layout_long, "col": layout_col, "file": layout_file}
_S2 = re.compile(r"s2|string", re.I)


def merge(parts):
    out = {}
    for p in parts:
        for y, recs in p.items():
            out.setdefault(y, []).extend(recs)
    return out


def candidates(files):
    """(label, data) for every layout applied to every table, to every whole file (all
    sheets), and to all tables together (all files; files whose path names S2/strings)."""
    out = []
    every = [(rel, tn, rows) for rel, tables in files.items() for tn, rows in tables]
    for lname, f in LAYOUTS.items():
        per = {tn: f(tn, rows) for _, tn, rows in every}
        for rel, tables in files.items():
            for tn, _ in tables:
                if per[tn]:
                    out.append(("%s|%s" % (lname, tn), per[tn]))
            if len(tables) > 1:
                m = merge([per[tn] for tn, _ in tables])
                if m:
                    out.append(("%s|%s::ALL" % (lname, rel), m))
        for tag, keep in (("all", lambda rel: True), ("s2", lambda rel: bool(_S2.search(rel)))):
            m = merge([per[tn] for rel, tn, _ in every if keep(rel)])
            if m:
                out.append(("%s|GLOBAL:%s" % (lname, tag), m))
    return out


def gate(data):
    """Table S1 gate: exactly the 8 years, the recording count of each year exact, and
    each year's element count within ELEMENT_TOL. Returns (ok, per-year report)."""
    rep = {}
    ok = sorted(data) == sorted(TABLE_S1)
    for y, (nr, ne) in TABLE_S1.items():
        recs = data.get(y, [])
        n_el = sum(len(r) for r in recs)
        good = len(recs) == nr and abs(n_el - ne) <= ELEMENT_TOL * ne
        rep[y] = {"recordings": len(recs), "expected_recordings": nr,
                  "elements": n_el, "expected_elements": ne, "ok": good}
        ok = ok and good
    return ok, rep


def read_songs(root):
    """Returns (data or None, report). data only if exactly one distinct passing reading."""
    files = load_files(root)
    cands = candidates(files)
    report = {"files": {k: [(t, len(r)) for t, r in v] for k, v in files.items()},
              "candidates": []}
    passing = []
    for label, d in cands:
        ok, rep = gate(d)
        report["candidates"].append({"label": label, "pass": ok, "per_year": rep})
        if ok:
            passing.append((label, d))
    distinct = []
    for label, d in passing:
        canon = {y: [list(r) for r in d[y]] for y in sorted(d)}
        if canon not in [c for _, c in distinct]:
            distinct.append((label, canon))
    report["n_passing"] = len(passing)
    report["n_distinct_passing"] = len(distinct)
    if len(distinct) == 1:
        report["chosen"] = distinct[0][0]
        return distinct[0][1], report
    report["chosen"] = None
    return None, report
