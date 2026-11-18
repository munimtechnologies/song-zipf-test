# SPDX-License-Identifier: Apache-2.0
# Tests for cds_job.py (stdlib only; needs zipfseg.py next to it). Every expected value is
# worked out by hand in the comments. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import io
import math
import os
import shutil
import tempfile
import unittest
import zipfile

import cds_job as C


def good_text():
    # 9,789 lines "a a a" (3 words, 3 phonemes each) = 29,367 words and phonemes;
    # last line: 4,019 words "a" + one word of 62,423 "b" = 4,020 words, 66,442 phonemes.
    # Totals: 9,790 utterances, 33,387 words, 95,809 phonemes (the registered gate).
    lines = ["a a a"] * 9789 + [" ".join(["a"] * 4019 + ["b" * 62423])]
    return "\n".join(lines) + "\n"


def zip_of(name, data):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(name, data)
    return buf.getvalue()


def row(ps, r2=0.85):
    keys = ("shuffle", "rotate", "bigram_within", "markov1_pooled", "markov2_pooled")
    return {"real_mean_r2": r2, "nulls": {k: {"p": p} for k, p in zip(keys, ps)}}


class TestReading(unittest.TestCase):
    def test_parse_text(self):
        self.assertEqual(C.parse_text("ab c\r\n\n d ef \n"), [["ab", "c"], ["d", "ef"]])

    def test_counts(self):
        c = C.counts([["ab", "c"], ["d", "ef"]])
        self.assertEqual(c, {"utterances": 2, "words": 4, "phonemes": 6,
                             "phoneme_types": 6, "word_types": 4})

    def test_gate(self):
        self.assertTrue(C.gate({"utterances": 9790, "phonemes": 95809, "words": 33390})["pass"])
        self.assertTrue(C.gate({"utterances": 9790, "phonemes": 95809, "words": 33419})["pass"])
        g = C.gate({"utterances": 9790, "phonemes": 95809, "words": 33500})
        self.assertFalse(g["words"])
        self.assertFalse(g["pass"])
        self.assertFalse(C.gate({"utterances": 9789, "phonemes": 95809, "words": 33387})["pass"])
        self.assertFalse(C.gate({"utterances": 9790, "phonemes": 95808, "words": 33387})["pass"])

    def test_good_text_passes(self):
        c = C.counts(C.parse_text(good_text()))
        self.assertEqual((c["utterances"], c["words"], c["phonemes"]), (9790, 33387, 95809))
        self.assertTrue(C.gate(c)["pass"])

    def test_extract_phono(self):
        self.assertEqual(C.extract_phono(zip_of("BR/br-phono.txt", b"x y\n")), b"x y\n")
        self.assertEqual(C.extract_phono(b"x y\n"), b"x y\n")
        with self.assertRaises(ValueError):
            C.extract_phono(zip_of("BR/br-text.txt", b"x"))

    def test_load_corpus_falls_back_and_caches(self):
        d = tempfile.mkdtemp()
        try:
            good = zip_of("BR/br-phono.txt", good_text().encode())

            def fetcher(url):
                if url == "u1":
                    return b"<html>not found</html>"
                if url == "u2":
                    return good
                raise IOError("offline")

            utts, info = C.load_corpus(d, sources=(("bad", "u1"), ("good", "u2")),
                                       fetcher=fetcher)
            self.assertEqual(len(utts), 9790)
            self.assertEqual(info["source"], "good")
            self.assertEqual([a["ok"] for a in info["attempts"]], [False, True])
            self.assertTrue(os.path.exists(os.path.join(d, "br-phono.txt")))
            # second call: cache is used first, the network is never needed
            utts2, info2 = C.load_corpus(d, sources=(("x", "u3"),), fetcher=fetcher)
            self.assertEqual(info2["source"], "cache")
            self.assertEqual(len(utts2), 9790)
            # no passing source at all
            e = tempfile.mkdtemp()
            try:
                u3, i3 = C.load_corpus(e, sources=(("bad", "u1"), ("x", "u3")), fetcher=fetcher)
                self.assertIsNone(u3)
                self.assertEqual([a["ok"] for a in i3["attempts"]], [False, False])
                self.assertIn("error", i3["attempts"][1])
            finally:
                shutil.rmtree(e)
        finally:
            shutil.rmtree(d)


class TestDataSets(unittest.TestCase):
    def test_blocks(self):
        self.assertEqual(C.blocks(list(range(10)), 2, 3, 2), [[2, 3], [4, 5], [6, 7]])
        self.assertEqual(C.W_START, 2100)
        self.assertLessEqual(C.W_START + C.W_REC * C.W_UTT, 9790)

    def test_to_recording(self):
        self.assertEqual(C.to_recording([["ab", "c"], ["d"]]), [["a", "b", "c"], ["d"]])

    def test_word_boundaries(self):
        self.assertEqual(C.word_boundaries(["ab", "c", "def"]), [2, 3])
        self.assertEqual(C.word_boundaries(["abc"]), [])

    def test_boundary_scores(self):
        # One bout "abab" (words ab|ab). n(a)=2, n(b)=2, pairs ab x2, ba x1:
        # TP(a->b)=1, TP(b->a)=0.5, so t = [1, 0.5, 1].
        # theta 0.7: i=1: 0.5 < 1*0.7 -> cut after position 1 (boundary at 2);
        #            i=2: 1 < 0.5*0.7 no. Cuts {2} = true boundaries {2}.
        s = C.boundary_scores([[["ab", "ab"]]], 0.7)
        self.assertEqual((s["hits"], s["n_cuts"], s["n_word_boundaries"]), (1, 1, 1))
        self.assertEqual((s["precision"], s["recall"], s["f1"]), (1.0, 1.0, 1.0))
        # theta 0.5: 0.5 < 0.5 is false -> no cut; precision undefined, recall 0.
        s = C.boundary_scores([[["ab", "ab"]]], 0.5)
        self.assertEqual((s["hits"], s["n_cuts"], s["n_word_boundaries"]), (0, 0, 1))
        self.assertTrue(math.isnan(s["precision"]))
        self.assertEqual(s["recall"], 0.0)
        self.assertTrue(math.isnan(s["f1"]))

    def test_true_word_r2(self):
        # block 1: ab x2, c x1 -> two unequal types -> R^2 = 1; block 2: a, b equal -> nan.
        self.assertAlmostEqual(C.true_word_r2([[["ab", "ab", "c"]], [["a", "b"]]]), 1.0,
                               places=12)

    def test_describe(self):
        d = C.describe([[["ab", "c"], ["d"]], [["ab", "ab", "c"]]])
        self.assertEqual(d["recordings"], 2)
        self.assertEqual(d["utterances"], 3)
        self.assertEqual(d["phonemes"], 4 + 5)
        self.assertEqual(d["phonemes_per_recording_mean"], 4.5)
        self.assertEqual(d["true_word_tokens"], 6)


class TestGrade(unittest.TestCase):
    def test_grade(self):
        a = 0.001
        F = {"by_theta": {"0.3": row((a, a, a, a, 0.2)), "0.5": row((a, a, a, a, 0.2)),
                          "0.7": row((a, a, a, 0.3, 0.4))},
             "heldout_ll_order2_minus_order1": {"n_favour_order2": 25}}
        W = {"by_theta": {th: row((a, a, a, a, 0.01)) for th in ("0.3", "0.5", "0.7")}}
        bs = {"0.5": {"f1": 0.4}}
        g = C.grade(F, W, bs)
        self.assertEqual(g["predictions"], {"H0": True, "H1": True, "H2": True, "H3": True,
                                            "H4": False, "H5": True, "H6": True, "H7": False})
        self.assertEqual(g["labels"]["F"], {"0.3": "EXPLAINED_BY_SECOND_ORDER",
                                            "0.5": "EXPLAINED_BY_SECOND_ORDER",
                                            "0.7": "EXPLAINED_BY_FIRST_ORDER"})
        self.assertEqual(set(g["labels"]["W"].values()), {"BEYOND_SECOND_ORDER"})
        r = g["rules"]
        self.assertEqual(r["L1"], "LANGUAGE_FAILS_AT_FINCH_SIZE")
        self.assertEqual(r["L2"], "LANGUAGE_PASSES_AT_WHALE_SIZE")
        self.assertTrue(r["L3_published_controls_passed_by_english"])
        self.assertFalse(r["robust_F"])
        self.assertTrue(r["robust_W"])
        # Brier: .1225 + .01 + .25 + .04 + .16 + .4225 + .0225 + .2025 = 1.23; / 8
        self.assertAlmostEqual(g["brier"], 1.23 / 8, places=9)

    def test_grade_nan_f1_and_finch_pass(self):
        a = 0.001
        F = {"by_theta": {th: row((a, 0.2, 0.2, a, a), r2=0.7) for th in ("0.3", "0.5", "0.7")},
             "heldout_ll_order2_minus_order1": {"n_favour_order2": 3}}
        g = C.grade(F, F, {"0.5": {"f1": float("nan")}})
        p = g["predictions"]
        self.assertEqual((p["H0"], p["H1"], p["H2"], p["H4"], p["H6"], p["H7"]),
                         (False, False, False, True, False, False))
        self.assertEqual(g["rules"]["L1"], "LANGUAGE_PASSES_AT_FINCH_SIZE")
        self.assertTrue(g["rules"]["robust_F"])


if __name__ == "__main__":
    unittest.main()
