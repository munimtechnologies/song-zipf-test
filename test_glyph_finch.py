# SPDX-License-Identifier: Apache-2.0
# Offline tests for glyph_finch (finch reading step v2) on synthetic "vector pages":
# every letter is a fake outline with its own shape, laid out in the printed Dataset
# format (bird cell, day cell, sequence cell with spaces and line wraps).
# Standard library only. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import unittest
from collections import Counter

import finch_parse as fp
import glyph_finch as gf

W = 4.0
H = 5.0


def G(ch, x, y, page=49, bold=False, noise=0.0):
    """Fake glyph: the outline's third point encodes the character (and weight)."""
    k = ord(ch) + (300 if bold else 0)
    pts = [(x, y), (x + W, y + H),
           (x + (k // 10 % 20) * 0.2 + noise, y + (k % 10) * 0.2 + noise)]
    return gf.make_glyph(page, (x, y, x + W, y + H), "ll", pts)


def put_text(text, x, y, page, bold=False):
    out = []
    gap = None
    for ch in text:
        if ch == " ":
            gap = 3.5
            continue
        if out:
            x = out[-1]["x1"] + (gap if gap is not None else 1.0)
        out.append(G(ch, x, y, page, bold=bold))
        gap = None
    return out


def add_row(glyphs, rects, page, y0, bird, day, lines, bold=False):
    nl = max(1, len(lines))
    y1 = y0 + 9.0 + 11.0 * nl
    rects += [(78.0, y0, 114.0, y1), (114.0, y0, 139.5, y1), (139.5, y0, 579.75, y1)]
    mid = (y0 + y1) / 2.0 - H / 2.0
    if bird:
        glyphs += put_text(bird, 80.0, mid, page, bold)
    if day:
        glyphs += put_text(day, 116.0, mid, page, bold)
    for i, L in enumerate(lines):
        glyphs += put_text(L, 141.0, y0 + 4.5 + 11.0 * i, page, bold)
    return y1


PATTERNS = [["ta ham"], ["oi rat", "mo"], ["hit"], ["a ma", "ta", "rim"]]
PATTERNS_X = [["ta bam"], ["oc rat", "mo"], ["hit"], ["a mb", "cc", "rim"]]


def expected(lines):
    words = [w for L in lines for w in L.split()]
    wraps = []
    n = 0
    for i, L in enumerate(lines):
        if i > 0 and n:
            wraps.append(n)
        n += sum(len(w) for w in L.split())
    return words, wraps


def synth(patterns=PATTERNS):
    recs = [(b, d) for b in fp.DAYS for d in fp.DAYS[b]]
    g49, r49, g50, r50 = [], [], [], []
    for r, p in ((r49, 49), (r50, 50)):
        r.append((0.0, 0.0, 612.0, 7920.0))            # page background
    r49.append((78.0, 30.0, 579.75, 31.0))              # header rule
    g49 += put_text("bird", 80.0, 20.0, 49, bold=True)  # header outside any band
    g49 += put_text("day", 116.0, 20.0, 49, bold=True)
    exp = []
    y = 38.25
    for i, (b, d) in enumerate(recs[:20]):
        lines = patterns[i % len(patterns)]
        y = add_row(g49, r49, 49, y, b, str(d), lines)
        exp.append([b, d] + list(expected(lines)))
    # the last row of page 49 continues at the top of page 50
    y = add_row(g50, r50, 50, 5.0, None, None, ["hot"])
    n = sum(len(w) for w in exp[-1][2])
    exp[-1][2] = exp[-1][2] + ["hot"]
    exp[-1][3] = exp[-1][3] + [n]
    # a repeated header band (bold, inside cells): unreadable, skipped
    y = add_row(g50, r50, 50, y, "bird", "day", ["sequence"], bold=True)
    for i, (b, d) in enumerate(recs[20:], start=20):
        lines = patterns[i % len(patterns)]
        y = add_row(g50, r50, 50, y, b, str(d), lines)
        exp.append([b, d] + list(expected(lines)))
    return [(49, g49, r49), (50, g50, r50)], exp


class TestPieces(unittest.TestCase):
    def test_lum(self):
        self.assertEqual(gf.lum([0, 0, 0]), 0.0)
        self.assertEqual(gf.lum([1, 1, 1]), 1.0)
        self.assertEqual(gf.lum([0, 0, 0, 1]), 0.0)
        self.assertAlmostEqual(gf.lum([0.961, 0.961, 0.961]), 0.961)
        self.assertIsNone(gf.lum(None))

    def test_item_points(self):
        class P:
            def __init__(s, x, y):
                s.x, s.y = x, y

        class R:
            def __init__(s, a, b, c, d):
                s.x0, s.y0, s.x1, s.y1 = a, b, c, d

        kinds, pts = gf.item_points([("l", P(0, 0), P(1, 1)), ("re", R(0, 0, 2, 3), 1), ()])
        self.assertEqual(kinds, "lr")
        self.assertEqual(pts, [(0.0, 0.0), (1.0, 1.0), (0.0, 0.0), (2.0, 3.0)])

    def test_classify(self):
        gl = [G("a", 10, 10), G("a", 50.123, 70.456, noise=0.01), G("b", 10, 30),
              G("a", 10, 10, bold=True)]
        classes = gf.classify(gl)
        self.assertEqual([g["cls"] for g in gl], [0, 0, 1, 2])
        self.assertEqual([c["n"] for c in classes], [2, 1, 1])
        # far beyond the tolerance -> new class
        g = G("a", 0, 0, noise=0.5)
        gf.classify([g] + gl[:1])
        self.assertNotEqual(g["cls"], gl[0]["cls"])

    def test_find_bands(self):
        rects = [(0.0, 0.0, 612.0, 7920.0), (78.0, 30.0, 579.75, 31.0),
                 (78.0, 40.0, 114.0, 60.0), (114.0, 40.0, 139.5, 60.0),
                 (139.5, 40.0, 579.75, 60.0), (139.5, 40.0, 579.75, 60.0),
                 (139.5, 60.0, 579.75, 80.0)]
        b = gf.find_bands(rects)
        self.assertEqual(len(b), 2)
        self.assertEqual((b[0]["x_bird"], b[0]["x_day"], b[0]["x_seq"]), (78.0, 114.0, 139.5))
        self.assertIsNone(b[1]["x_day"])
        self.assertEqual(b[1]["n_left"], 0)

    def test_words_and_gaps(self):
        gl = [G("a", 0, 0), G("b", 6.0, 0), G("c", 12.5, 0)]    # gaps 2.0 and 2.5
        gf.classify(gl)
        labels = {g["cls"]: ch for g, ch in zip(gl, "abc")}
        words, gaps = gf.words_and_gaps(gl, labels, 2.25)
        self.assertEqual(words, ["ab", "c"])
        self.assertEqual([round(x, 6) for x in gaps], [2.0, 2.5])
        self.assertEqual(gf.words_and_gaps(gl, labels, 2.6)[0], ["abc"])

    def test_text_lines(self):
        gl = [G("b", 20, 10.5), G("a", 10, 10), G("c", 10, 21)]
        gf.classify(gl)
        L = gf.text_lines(gl)
        self.assertEqual([[g["x0"] for g in line] for line in L], [[10, 20], [10]])

    def test_solve_names_unique(self):
        counts = Counter({tuple(map(ord, nm)): 5 for nm in fp.DAYS})
        sols, seqs = gf.solve_names(counts)
        self.assertEqual(len(sols), 1)
        bird_of, c2ch = sols[0]
        self.assertEqual({s: n for s, n in bird_of.items()},
                         {tuple(map(ord, nm)): nm for nm in fp.DAYS})
        self.assertEqual(c2ch[ord("a")], "a")

    def test_solve_names_rejects_inconsistent(self):
        # 'Atama' needs positions 2 and 4 to be the same class
        counts = Counter({(1, 2, 3, 4, 5): 3})
        sols, _ = gf.solve_names(counts, names=["Atama"])
        self.assertEqual(sols, [])

    def test_solve_days_unique(self):
        pairs = Counter({(b, tuple(100 + int(c) for c in str(d))): 1
                         for b in fp.DAYS for d in fp.DAYS[b]})
        sols, used = gf.solve_days(pairs)
        self.assertEqual(len(sols), 1)
        self.assertEqual(sols[0], {100 + d: str(d) for d in range(10)})
        self.assertEqual(len(used), 30)

    def test_solve_days_bad_pair_falls_back(self):
        pairs = Counter({(b, tuple(100 + int(c) for c in str(d))): 3
                         for b in fp.DAYS for d in fp.DAYS[b]})
        pairs[("Atama", (100, 100, 100, 100))] = 1           # unreadable extra
        sols, used = gf.solve_days(pairs)
        self.assertEqual(len(sols), 1)
        self.assertEqual(len(used), 30)

    def test_assign_labels(self):
        seq_counts = Counter({1: 10, 2: 7, 3: 5, 4: 1})
        labels, src = gf.assign_labels(seq_counts, {1: "a"}, {2: "a", 3: "q", 4: "q"})
        self.assertEqual(labels[1], "a")
        self.assertEqual(labels[3], "q")
        self.assertEqual(src, {1: "name", 2: "fallback", 3: "ocr", 4: "fallback"})
        self.assertEqual(len(set(labels.values())), 4)


class TestEndToEnd(unittest.TestCase):
    def test_full_synthetic(self):
        pages, exp = synth()
        res = gf.read_dataset(pages)
        got = [[r["bird"], r["day"], r["words"], r["wraps"]] for r in res["rows"]]
        self.assertEqual(got, exp)
        d = res["diag"]
        self.assertEqual(d["name_solutions"], 1)
        self.assertEqual(d["day_solutions"], 1)
        self.assertEqual(res["stats"], {"rows": 30, "continuation_bands": 1,
                                        "unreadable_header": 1})
        self.assertEqual(d["seq_gaps_ambiguous_1.9_2.6"], 0)
        self.assertEqual(d["n_glyphs_outside_bands"], 7)     # the bold header line
        v = fp.validate(res["rows"])
        self.assertEqual(v["recordings_found"], 30)
        self.assertEqual(v["bouts"], 30)
        self.assertEqual(v["gate"], "FAIL")                   # 30 bouts, not 299
        self.assertEqual(v["printed_cuts"], sum(len(e[2]) - 1 for e in exp))

    def test_unknown_letters_get_consistent_labels(self):
        pages, exp = synth(PATTERNS_X)
        res = gf.read_dataset(pages, ocr=lambda cid, info: "b")
        m = {}
        for r, e in zip(res["rows"], exp):
            self.assertEqual([len(w) for w in r["words"]], [len(w) for w in e[2]])
            for wr, we in zip(r["words"], e[2]):
                for cr, ce in zip(wr, we):
                    self.assertEqual(m.setdefault(ce, cr), cr)
        self.assertEqual(len(set(m.values())), len(m))         # injective
        for ch in "tahmiro":
            self.assertEqual(m[ch], ch)                         # bird-name letters
        self.assertEqual(Counter(res["sources"].values())["ocr"], 1)


if __name__ == "__main__":
    unittest.main()
