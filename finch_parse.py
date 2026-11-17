# SPDX-License-Identifier: Apache-2.0
# Parse OCR text of the Kirby et al. 2026 (Sci. Adv. eaea3015) supplementary
# "Dataset" pages (one song bout per row: bird, age in days, syllable letters
# with spaces at the authors' segmentation boundaries) and validate it against
# totals printed in the authors' own Code S1 output. Pure Python.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import re
from collections import Counter

import zipfseg as z

# The 30 recordings (bird -> ages in days) printed by Code S1 cell [95].
DAYS = {
    "Atama": [62, 69, 89, 103, 124],
    "LShiro": [73, 85, 93, 100, 121],
    "RAo": [61, 76, 87, 102, 127],
    "RKi": [71, 79, 93, 106, 121],
    "RMo": [70, 77, 91, 99, 125],
    "Shiro": [64, 78, 92, 105, 120],
}
# Totals implied by Code S1 printed output (see PREREG-AMENDMENT-1.md):
#  cuts per bout 10.719063545150501 -> 299 bouts, 3205 cuts, 3504 subsequences;
#  all_TPs: 19990 transitions -> 20289 syllables; new_ranked_freq: 1043 rows.
TARGETS = {"recordings": 30, "bouts": 299, "transitions": 19990,
           "syllables": 20289, "pipeline_cuts": 3205, "pipeline_types": 1043}
CUTS_PER_BOUT = 10.719063545150501

DIGIT_FIX = {"O": "0", "o": "0", "D": "0", "Q": "0", "l": "1", "I": "1", "i": "1",
             "|": "1", "!": "1", "S": "5", "s": "5", "B": "8", "Z": "2", "z": "2",
             "g": "9", "q": "9", "G": "6", "b": "6", "A": "4", "T": "7"}


def edit(a, b):
    """Levenshtein distance."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def fix_digits(tok):
    return "".join(DIGIT_FIX.get(c, c) for c in tok)


def match_header(name_tok, day_tok):
    """Return (bird, day, cost) for the best (bird, day) pair, or None.

    cost = edit distance of the name (case-insensitive) + number of differing
    day digits (3 if the lengths differ). Accepted if name distance <= 2 and
    cost <= 3; ties are broken by name distance, then alphabetically."""
    if not any(c.isdigit() for c in day_tok):
        return None
    d = fix_digits(day_tok)
    if not d.isdigit() or not 1 <= len(d) <= 3:
        return None
    best = None
    for bird, days in DAYS.items():
        ne = edit(name_tok.lower(), bird.lower())
        if ne > 2:
            continue
        for day in days:
            sd = str(day)
            dd = sum(x != y for x, y in zip(sd, d)) if len(sd) == len(d) else 3
            cand = (ne + dd, ne, bird, day)
            if best is None or cand < best:
                best = cand
    if best is None or best[0] > 3:
        return None
    return best[2], best[3], best[0]


HEADER = re.compile(r"^\s*(\S+)\s+(\S+)(?:\s+(.*))?$")


def parse_lines(lines):
    """Rows from OCR lines.

    A header line is 'name day letters...'; any other non-empty line after a
    header is a continuation of that row (a wrapped long bout). Returns
    (rows, stats). Each row: bird, day, cost, words (letters only), wraps
    (symbol indices where a continuation line began), bad_chars (count of
    non-letter characters dropped from the sequence part)."""
    rows = []
    stats = {"lines": 0, "header_lines": 0, "continuation_lines": 0,
             "ignored_lines": 0, "bad_chars": 0}
    cur = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        stats["lines"] += 1
        m = HEADER.match(line)
        h = match_header(m.group(1), m.group(2)) if m else None
        if h is not None:
            cur = {"bird": h[0], "day": h[1], "cost": h[2], "words": [],
                   "wraps": [], "bad_chars": 0}
            rows.append(cur)
            stats["header_lines"] += 1
            rest = m.group(3) or ""
        elif cur is not None:
            stats["continuation_lines"] += 1
            n = sum(len(w) for w in cur["words"])
            if n:
                cur["wraps"].append(n)
            rest = line
        else:
            stats["ignored_lines"] += 1
            continue
        for tok in rest.split():
            letters = "".join(c for c in tok if c.isalpha())
            bad = len(tok) - len(letters)
            cur["bad_chars"] += bad
            stats["bad_chars"] += bad
            if letters:
                cur["words"].append(letters)
    return rows, stats


def recordings_from_rows(rows):
    """{(bird, day): [bout symbol lists]} in printed order."""
    recs = {}
    for r in rows:
        recs.setdefault((r["bird"], r["day"]), []).append(list("".join(r["words"])))
    return recs


def printed_cuts(row):
    """Symbol indices where the authors printed a boundary (word starts > 0)."""
    out = []
    pos = 0
    for w in row["words"][:-1]:
        pos += len(w)
        out.append(pos)
    return out


def validate(rows, theta=0.5):
    """Compare the parsed data with the Code S1 totals and with the printed
    segmentation. Boundaries at line-wrap positions are excluded from the
    agreement counts (a wrap can hide or invent a space)."""
    recs = recordings_from_rows(rows)
    expected = {(b, d) for b, ds in DAYS.items() for d in ds}
    found = set(recs)
    n_bouts = sum(len(v) for v in recs.values())
    n_syll = sum(len(b) for v in recs.values() for b in v)
    n_trans = sum(max(len(b) - 1, 0) for v in recs.values() for b in v)
    # our Code S1 pipeline on the unspaced sequences
    tp_agree = fp = fn = 0
    bouts_identical = 0
    pipe_words = 0
    pipe_types = 0
    by_key_rows = {}
    for r in rows:
        by_key_rows.setdefault((r["bird"], r["day"]), []).append(r)
    for key, bouts in recs.items():
        segs_all = z.segment_recording_bouts(bouts, theta)
        pipe_words += sum(len(s) for s in segs_all)
        pipe_types += len({w for s in segs_all for w in s})
        for r, segs in zip(by_key_rows[key], segs_all):
            wraps = set(r["wraps"])
            pred = set(z.cut_positions(segs)) - wraps
            prin = set(printed_cuts(r)) - wraps
            tp_agree += len(pred & prin)
            fp += len(pred - prin)
            fn += len(prin - pred)
            if pred == prin:
                bouts_identical += 1
    prec = tp_agree / (tp_agree + fp) if tp_agree + fp else float("nan")
    rec = tp_agree / (tp_agree + fn) if tp_agree + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if prec == prec and rec == rec and prec + rec else float("nan")
    letters = {}
    for (b, _), v in recs.items():
        letters.setdefault(b, Counter()).update(s for bout in v for s in bout)
    rare = {b: sorted(k for k, c in cnt.items() if c < 5) for b, cnt in letters.items()}
    out = {
        "recordings_found": len(found & expected),
        "recordings_missing": sorted("%s %d" % k for k in expected - found),
        "bouts": n_bouts,
        "bouts_per_recording": {"%s %d" % k: len(v) for k, v in sorted(recs.items())},
        "syllables": n_syll,
        "transitions": n_trans,
        "printed_cuts": sum(len(r["words"]) - 1 for r in rows if r["words"]),
        "wraps": sum(len(r["wraps"]) for r in rows),
        "pipeline_cuts": pipe_words - n_bouts,
        "pipeline_cuts_per_bout": (pipe_words / n_bouts - 1) if n_bouts else float("nan"),
        "pipeline_types": pipe_types,
        "cut_agreement": {"both": tp_agree, "pipeline_only": fp, "printed_only": fn,
                          "precision": prec, "recall": rec, "f1": f1,
                          "bouts_identical": bouts_identical},
        "letters_per_bird": {b: dict(sorted(c.items())) for b, c in sorted(letters.items())},
        "rare_letters_per_bird": rare,
        "bad_chars": sum(r["bad_chars"] for r in rows),
        "header_cost_nonzero": sum(1 for r in rows if r["cost"] > 0),
    }
    exact = {
        "recordings": out["recordings_found"] == TARGETS["recordings"],
        "bouts": n_bouts == TARGETS["bouts"],
        "transitions": n_trans == TARGETS["transitions"],
        "pipeline_cuts": out["pipeline_cuts"] == TARGETS["pipeline_cuts"],
        "pipeline_types": pipe_types == TARGETS["pipeline_types"],
    }
    out["exact"] = exact
    out["n_exact"] = sum(exact.values())
    out["gate"] = gate(out)
    return out


def gate(v):
    """Pre-registered gate (PREREG-AMENDMENT-1.md section 4)."""
    if v["n_exact"] == 5:
        return "PASS_EXACT"
    f1 = v["cut_agreement"]["f1"]
    if (v["recordings_found"] == 30 and abs(v["bouts"] - 299) <= 3
            and abs(v["transitions"] - 19990) <= 100 and f1 == f1 and f1 >= 0.95):
        return "PASS_APPROX"
    return "FAIL"


def score(v):
    """Ranking of OCR configurations: exact matches first, then cut F1, then
    closeness of the syllable count."""
    f1 = v["cut_agreement"]["f1"]
    return (v["n_exact"], f1 if f1 == f1 else -1.0, -abs(v["syllables"] - TARGETS["syllables"]))
