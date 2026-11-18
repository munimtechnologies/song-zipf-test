# SPDX-License-Identifier: Apache-2.0
# Tests for finch_xpop.py (stdlib only; needs zipfseg.py next to it). Expected values are
# worked out by hand in the comments. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import io
import json
import os
import random
import shutil
import tarfile
import tempfile
import time
import unittest
import zipfile

import finch_xpop as X
import zipfseg as z

XML = """<?xml version="1.0" encoding="utf-8"?>
<AnnotationSequences>
 <Sequence><WaveFileName>1.wav</WaveFileName><Position>1000</Position><Length>50000</Length>
  <NumNote>3</NumNote>
  <Note><Position>0</Position><Length>100</Length><Label>a</Label></Note>
  <Note><Position>2000</Position><Length>100</Length><Label>b</Label></Note>
  <Note><Position>4000</Position><Length>100</Length><Label>c</Label></Note>
 </Sequence>
 <Sequence><WaveFileName>1.wav</WaveFileName><Position>6000</Position><Length>2000</Length>
  <NumNote>2</NumNote>
  <Note><Position>0</Position><Length>100</Length><Label>d</Label></Note>
  <Note><Position>1000</Position><Length>100</Length><Label>e</Label></Note>
 </Sequence>
 <Sequence><WaveFileName>1.wav</WaveFileName><Position>30000</Position><Length>700</Length>
  <NumNote>2</NumNote>
  <Note><Position>0</Position><Length>100</Length><Label>f</Label></Note>
  <Note><Position>500</Position><Length>100</Length><Label>g</Label></Note>
 </Sequence>
 <Sequence><WaveFileName>0.wav</WaveFileName><Position>500</Position><Length>200</Length>
  <NumNote>2</NumNote>
  <Note><Position>0</Position><Length>10</Length><Label>h</Label></Note>
  <Note><Position>100</Position><Length>10</Length><Label>i</Label></Note>
 </Sequence>
 <Sequence><WaveFileName>10.wav</WaveFileName><Position>0</Position><Length>10</Length>
  <NumNote>1</NumNote>
  <Note><Position>0</Position><Length>10</Length><Label>j</Label></Note>
 </Sequence>
 <Sequence><WaveFileName>2.wav</WaveFileName><Position>0</Position><Length>10</Length>
  <NumNote>1</NumNote>
  <Note><Position>0</Position><Length>10</Length><Label>k</Label></Note>
 </Sequence>
</AnnotationSequences>
"""


def rand_recs(seed, n_rec=2, n_bouts=15, length=12, alphabet="abcde"):
    rng = random.Random(seed)
    return [[[rng.choice(alphabet) for _ in range(length)] for _ in range(n_bouts)]
            for _ in range(n_rec)]


def row(p1, p2, p3=None, r2=0.85, extra=None):
    nulls = {"markov1_pooled": {"p": p1}, "markov2_pooled": {"p": p2}}
    if p3 is not None:
        nulls["markov3_pooled"] = {"p": p3}
    for k, v in (extra or {}).items():
        nulls[k] = {"p": v}
    return {"real_mean_r2": r2, "nulls": nulls}


class TestKoumura(unittest.TestCase):
    def test_parse(self):
        seqs = X.parse_koumura_xml(XML.encode())
        self.assertEqual(len(seqs), 6)
        # sequence 1 at 1000: a (1000,1100), b (3000,3100), c (5000,5100)
        self.assertEqual(seqs[0]["notes"], [(1000, 1100, "a"), (3000, 3100, "b"),
                                            (5000, 5100, "c")])
        self.assertEqual(seqs[1]["notes"], [(6000, 6100, "d"), (7000, 7100, "e")])
        self.assertEqual(seqs[3]["wav"], "0.wav")
        self.assertEqual(seqs[3]["pos"], 500)

    def test_wav_key(self):
        names = ["10.wav", "2.wav", "x.wav", "0.wav", "1.wav"]
        self.assertEqual(sorted(names, key=X.wav_key),
                         ["0.wav", "1.wav", "2.wav", "10.wav", "x.wav"])

    def test_bouts_merged(self):
        # 1.wav: gap c->d = 6000-5100 = 900 < 9600 -> merged; gap e->f = 30000-7100 =
        # 22900 >= 9600 -> new bout. Files in order 0, 1, 2, 10; a new file is a new bout.
        seqs = X.parse_koumura_xml(XML.encode())
        self.assertEqual(X.koumura_bouts(seqs),
                         [["h", "i"], ["a", "b", "c", "d", "e"], ["f", "g"], ["k"], ["j"]])

    def test_bouts_raw(self):
        seqs = X.parse_koumura_xml(XML.encode())
        self.assertEqual(X.koumura_bouts(seqs, merge=False),
                         [["h", "i"], ["a", "b", "c"], ["d", "e"], ["f", "g"], ["k"], ["j"]])

    def test_merge_gap_threshold(self):
        # gap exactly 9600 is NOT < 9600 -> separate; 9599 -> merged
        s = [{"wav": "0.wav", "pos": 0, "notes": [(0, 100, "a")]},
             {"wav": "0.wav", "pos": 9700, "notes": [(9700, 9800, "b")]},
             {"wav": "0.wav", "pos": 19399, "notes": [(19399, 19400, "c")]}]
        self.assertEqual(X.koumura_bouts(s), [["a"], ["b", "c"]])

    def test_stats(self):
        st = X.koumura_stats(X.parse_koumura_xml(XML.encode()))
        # notes 3+2+2+2+1+1 = 11, all labels distinct
        self.assertEqual((st["sequences"], st["notes"], st["classes"],
                          st["max_notes_per_sequence"]), (6, 11, 11, 3))

    def test_gate(self):
        good = [{"notes": 18000, "classes": 8}] * 10 + [{"notes": 17209, "classes": 8}]
        # mean notes 197209 / 11 = 17928.09 (within 5% of 17930.9); classes 8 (|8-8.1| <= 0.5)
        g = X.gate_koumura(good)
        self.assertTrue(g["pass"])
        self.assertAlmostEqual(g["notes_mean"], 197209 / 11)
        self.assertFalse(X.gate_koumura(good[:10])["pass"])          # 10 birds
        self.assertFalse(X.gate_koumura([{"notes": 18000, "classes": 9}] * 11)["pass"])
        self.assertFalse(X.gate_koumura([{"notes": 20000, "classes": 8}] * 11)["pass"])
        self.assertFalse(X.gate_koumura([])["pass"])

    def test_load_bird_from_zip_and_cache(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("Bird0/Wave/0.wav", b"RIFF0000")
            zf.writestr("Bird0/Annotation.xml", XML)
        data = buf.getvalue()

        def fake(url, path):
            with open(path, "wb") as f:
                f.write(data)
            return len(data), "x"

        def boom(url, path):
            raise AssertionError("should use the cache")

        d = tempfile.mkdtemp()
        try:
            blob, info = X.load_koumura_bird("Bird0", "u", len(data), d, downloader=fake,
                                             pause=0)
            self.assertEqual(blob, XML.encode())
            self.assertEqual(info["attempts"][0]["member"], "Bird0/Annotation.xml")
            blob2, info2 = X.load_koumura_bird("Bird0", "u", len(data), d, downloader=boom)
            self.assertEqual(blob2, XML.encode())
            self.assertEqual(info2["source"], "cache")
            # wrong size: three attempts, nothing cached, None returned
            blob3, info3 = X.load_koumura_bird("Bird1", "u", len(data) + 1, d,
                                               downloader=fake, pause=0)
            self.assertIsNone(blob3)
            self.assertEqual(len(info3["attempts"]), 3)
            self.assertFalse(os.path.exists(os.path.join(d, "koumura", "Bird1_Annotation.xml")))
        finally:
            shutil.rmtree(d)


class TestNicholson(unittest.TestCase):
    CSV = "onset_s,offset_s,label\n0.10,0.15,i\n0.20,0.25,a\n0.90,0.95,b\n1.00,1.05,\n1.10,1.15,c\n"

    def test_parse(self):
        self.assertEqual(X.parse_simple_seq_csv(self.CSV),
                         [(0.1, 0.15, "i"), (0.2, 0.25, "a"), (0.9, 0.95, "b"),
                          (1.0, 1.05, ""), (1.1, 1.15, "c")])

    def test_parse_generic_and_headerless(self):
        t = "label,onset_s,offset_s,onset_sample\nb,0.5,0.6,16000\n"
        self.assertEqual(X.parse_simple_seq_csv(t), [(0.5, 0.6, "b")])
        self.assertEqual(X.parse_simple_seq_csv("0.1,0.2,a\n"), [(0.1, 0.2, "a")])
        self.assertEqual(X.parse_simple_seq_csv("\n"), [])

    def test_split_bouts(self):
        # i; a (gap .05) joins; b (gap .65) new; empty row dropped; c (gap 1.10-.95 = .15) joins
        self.assertEqual(X.split_bouts(X.parse_simple_seq_csv(self.CSV)),
                         [["i", "a"], ["b", "c"]])

    def test_file_ok(self):
        self.assertTrue(X.file_ok([(0.1, 0.2, "a"), (0.3, 0.4, "b")]))
        self.assertFalse(X.file_ok([(0.3, 0.2, "a")]))
        self.assertFalse(X.file_ok([(0.5, 0.6, "a"), (0.3, 0.4, "b")]))

    def test_bird_cap_and_order(self):
        calls = []
        days = {"d1": {"f2.csv": "0.0,0.1,x\n0.2,0.3,y\n0.4,0.5,z\n",   # 3 syllables, 1 bout
                       "f1.csv": "0.0,0.1,p\n1.0,1.1,q\n",               # 2 syllables, 2 bouts
                       "f0.csv": "0.0,0.1,\n"},                          # no labels: skipped
                "d2": {"g.csv": "0.0,0.1,r\n"}}

        def load(bird, day):
            calls.append(day)
            return days[day]
        bouts, info = X.nicholson_bird("b", ["d1", "d2"], load, cap=4)
        # f1 first (2 syll, n=2 < 4), then f2 (n=5 >= 4): stop; d2 never loaded
        self.assertEqual(bouts, [["p"], ["q"], ["x", "y", "z"]])
        self.assertEqual(calls, ["d1"])
        self.assertEqual((info["files"], info["syllables"], info["classes"]), (2, 5, 5))
        bouts, info = X.nicholson_bird("b", ["d1", "d2"], load, cap=100)
        self.assertEqual(bouts[-1], ["r"])
        self.assertEqual(info["syllables"], 6)

    def test_gate(self):
        good = [{"syllables": 20000, "files": 100, "bad_files": 0, "unreadable_files": 0}] * 4
        self.assertTrue(X.gate_nicholson(good)["pass"])
        self.assertFalse(X.gate_nicholson(good[:3])["pass"])
        low = good[:3] + [{"syllables": 4999, "files": 100, "bad_files": 0,
                           "unreadable_files": 0}]
        self.assertFalse(X.gate_nicholson(low)["pass"])
        bad = good[:3] + [{"syllables": 20000, "files": 100, "bad_files": 3,
                           "unreadable_files": 2}]
        # 5 bad of 400 files = 1.25% > 1%
        self.assertFalse(X.gate_nicholson(bad)["pass"])

    def test_stream_tar(self):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            for name, data in (("bird/a.wav", b"RIFF" * 100), ("bird/a.wav.csv", b"0,1,a\n"),
                               ("bird/b.wav.csv", b"onset_s,offset_s,label\n0,1,b\n")):
                ti = tarfile.TarInfo(name)
                ti.size = len(data)
                tf.addfile(ti, io.BytesIO(data))
        data = buf.getvalue()
        got = X.stream_tar_csvs("u", opener=lambda u: io.BytesIO(data))
        self.assertEqual(got, {"bird/a.wav.csv": "0,1,a\n",
                               "bird/b.wav.csv": "onset_s,offset_s,label\n0,1,b\n"})


class TestAnalysis(unittest.TestCase):
    def test_first_until(self):
        b = [["a"] * 3, ["b"], ["c"] * 4, ["d"] * 2]
        # transitions 2, 2, 5 -> stop after the third bout
        self.assertEqual(X.first_until(b, 4), b[:3])
        self.assertEqual(X.first_until(b, 100), b)

    def test_describe(self):
        d = X.describe([[["a", "b"], ["a"]], [["c", "c", "d"]]])
        self.assertEqual((d["recordings"], d["bouts"], d["symbols"], d["transitions"]),
                         (2, 3, 6, 3))
        self.assertEqual(d["alphabet_per_recording"], [2, 2])
        self.assertEqual(d["max_bout_length"], 3)

    def test_heldout_fast_matches_zipfseg(self):
        for seed in (1, 2, 3):
            rec = rand_recs(seed, n_rec=1, n_bouts=9, length=11, alphabet="abcd")[0]
            for k in (1, 2):
                self.assertAlmostEqual(X.heldout_fast(rec, k, skip=2), z.heldout_ll(rec, k),
                                       places=10)
            self.assertAlmostEqual(X.heldout_fast(rec, 3, skip=3),
                                   z.heldout_ll(rec, 3, skip=3), places=10)

    def test_markov3_null_registered(self):
        rec = rand_recs(5, n_rec=1)[0]
        fake = z.NULLS["markov3_pooled"](rec, random.Random(1))
        self.assertEqual([len(b) for b in fake], [len(b) for b in rec])

    def test_decision3(self):
        self.assertEqual(X.decision3(row(.001, .001, .01)), "BEYOND_THIRD_ORDER")
        self.assertEqual(X.decision3(row(.001, .01, .2)), "EXPLAINED_BY_THIRD_ORDER")
        self.assertEqual(X.decision3(row(.001, .01)), "BEYOND_SECOND_ORDER")
        self.assertEqual(X.decision3(row(.001, .3, .4)), "EXPLAINED_BY_SECOND_ORDER")
        self.assertEqual(X.decision3(row(.2, .3)), "EXPLAINED_BY_FIRST_ORDER")
        # same labels as zipfseg.decision when there is no third-order null
        for p1, p2 in ((.001, .01), (.001, .3), (.2, .3)):
            self.assertEqual(X.decision3(row(p1, p2)), z.decision(row(p1, p2)))

    def _res(self, k5, n2, s1, rob=True):
        ex = {"shuffle": .005, "rotate": .005, "bigram_within": .005}
        k = row(.005, .01 if k5 else .4, .3, r2=.9, extra=ex)
        res = {"K": {"by_theta": {"0.5": k}, "heldout": {"d1_n_favour_order2": 9,
                                                          "n_recordings": 11}},
               "N": {"by_theta": {"0.5": row(.005, .01 if n2 else .4, .3, extra=ex)}},
               "KS": {"by_theta": {"0.5": row(.005, .01 if s1 else .4, extra=ex)}}}
        if rob:
            res["K"]["by_theta"]["0.3"] = k
            res["K"]["by_theta"]["0.7"] = k
        return res

    def test_grade_all_true(self):
        res = self._res(True, True, True)
        res["K"]["by_theta"]["0.5"]["nulls"]["markov3_pooled"]["p"] = .01
        gr = X.grade(res, {"K": {"pass": True}, "N": {"pass": True}})
        self.assertTrue(all(gr["predictions"].values()))
        # sum of (1-p)^2 over the 11 priors = 1.94
        self.assertAlmostEqual(gr["brier"], 1.94 / 11)
        self.assertEqual(gr["rules"]["X1"], "ABOVE_BIGRAM_REPLICATES")
        self.assertEqual(gr["rules"]["X2"], "FINCH_ZIPF_BEYOND_SECOND_ORDER")
        self.assertEqual(gr["rules"]["X3"], "BEYOND_EVEN_AT_KIRBY_SIZE")
        self.assertFalse(gr["provisional"])
        # K's 0.3 / 0.5 / 0.7 rows are the same object, so K is robust once 0.5 is edited too
        self.assertTrue(gr["rules"]["robust_K"])

    def test_grade_rules(self):
        gr = X.grade(self._res(False, False, False), {"K": {"pass": True}, "N": {"pass": False}})
        self.assertEqual(gr["rules"]["X2"], "SECOND_ORDER_EXPLAINS_FINCH_ZIPF")
        self.assertEqual(gr["rules"]["X3"], "NOT_BEYOND_AT_EITHER_SIZE")
        self.assertTrue(gr["provisional"])
        self.assertEqual(gr["labels"]["K"]["0.5"], "EXPLAINED_BY_SECOND_ORDER")
        gr = X.grade(self._res(True, False, False), {})
        self.assertEqual(gr["rules"]["X2"], "SECOND_ORDER_MIXED")
        self.assertEqual(gr["rules"]["X3"], "SIZE_DEPENDENT")
        self.assertEqual(gr["labels"]["K"]["0.5"], "EXPLAINED_BY_THIRD_ORDER")

    def test_grade_missing_blocks(self):
        res = self._res(False, False, False, rob=False)
        del res["N"]
        gr = X.grade(res, {})
        self.assertIsNone(gr["predictions"]["N1"])
        self.assertEqual(gr["rules"]["X1"], "NOT_GRADED")
        self.assertEqual(len(gr["graded"]), 9)
        self.assertFalse(gr["rules"]["robust_K"])

    def test_run_task_and_assemble(self):
        recs = {"K": rand_recs(7), "N": rand_recs(8), "KS": [], "NS": rand_recs(9, n_rec=1)}
        blocks = [("K_0.5", "K", 0.5, 3, X.FULL_NULLS, False),
                  ("K_heldout", "K", None, 0, None, False),
                  ("KS_0.5", "KS", 0.5, 3, X.SMALL_NULLS, False),
                  ("N_0.3", "N", 0.3, 3, X.FULL_NULLS, True)]
        d = tempfile.mkdtemp()
        try:
            out = X.run_task((blocks, recs, d, time.time(), 3600))
            out2 = X.run_task(([("N_0.7", "N", 0.7, 3, X.FULL_NULLS, True)], recs, d,
                               time.time() - 3000, 3600))           # over 55% of budget
            res = X.assemble([out, out2])
            self.assertEqual(sorted(res["K"]["by_theta"]["0.5"]["nulls"]),
                             sorted(X.FULL_NULLS + ("rotate",)))
            self.assertEqual(res["K"]["heldout"]["n_recordings"], 2)
            self.assertIn("KS_0.5", res["KS"]["not_run"])
            self.assertIn("0.3", res["N"]["by_theta"])
            self.assertIn("N_0.7", res["N"]["not_run"])
            with open(os.path.join(d, "blocks", "K_0.5.json")) as f:
                self.assertIn("real_mean_r2", json.load(f))
        finally:
            shutil.rmtree(d)

    def test_plan(self):
        a, b = X.plan()
        ids = [x[0] for x in a + b]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual([x[0] for x in a if not x[5]], ["K_0.5", "K_heldout"])


if __name__ == "__main__":
    unittest.main()
