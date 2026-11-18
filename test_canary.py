# SPDX-License-Identifier: Apache-2.0
# Tests for canary.py (stdlib only, in memory: no files are written). Needs zipfseg.py next
# to it. Expected values are worked out by hand in the comments.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import io
import random
import struct
import unittest
import zipfile
import zlib

import canary as C
import zipfseg as z

CSV = ("label,onset_s,offset_s,onset_Hz,offset_Hz,audio_file,annot_file,sequence,annotation\n"
       "a,0.10,0.20,4410,8820,f1.wav,x.mat,0,0\n"
       "b,0.30,0.40,,,f1.wav,x.mat,0,0\n"
       ",0.50,0.60,,,f1.wav,x.mat,0,0\n"
       "c,0.70,0.65,,,f1.wav,x.mat,0,0\n"
       "d,abc,0.9,,,f1.wav,x.mat,0,0\n"
       "e,1.0,1.1,,,,x.mat,0,0\n")


def make_zip(members, seekable=True):
    """members: [(name, bytes)], deflated. seekable=False makes zipfile write data
    descriptors (flag bit 3), as a streaming zip tool would."""
    if seekable:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for n, d in members:
                zf.writestr(n, d)
        return buf.getvalue()

    class NoSeek:
        def __init__(self):
            self.b = io.BytesIO()

        def write(self, d):
            return self.b.write(d)

        def flush(self):
            pass

    ns = NoSeek()
    with zipfile.ZipFile(ns, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for n, d in members:
            zf.writestr(n, d)
    return ns.b.getvalue()


MEMBERS = [("llb3/audio/0001.wav", b"RIFF" + bytes(range(256)) * 40),
           ("__MACOSX/llb3/._llb3_annot.csv", b"junk"),
           ("llb3/._hidden.csv", b"junk2"),
           ("llb3/llb3_annot.csv", CSV.encode()),
           ("llb3/llb3_annot.mat", b"MATLAB" * 50)]


def rand_songs(seed, n=30, length=12, alphabet="abcdef"):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        s = []
        while len(s) < length:
            x = rng.choice(alphabet)
            if not s or s[-1] != x:
                s.append(x)
        out.append(s)
    return out


class TestZip(unittest.TestCase):
    def test_list_and_read_by_range(self):
        blob = make_zip(MEMBERS)
        calls = []

        def rr(a, b):
            calls.append((a, b))
            return blob[a:b + 1]
        members, info = C.list_zip(rr, len(blob))
        self.assertFalse(info["zip64"])
        self.assertEqual([m["name"] for m in members], [n for n, _ in MEMBERS])
        want = [m for m in members if C.is_annotation_csv(m["name"])]
        self.assertEqual([m["name"] for m in want], ["llb3/llb3_annot.csv"])
        self.assertEqual(C.member_bytes(rr, want[0]), CSV.encode())
        # the tail read starts at 0 for an archive shorter than 65,558 bytes
        self.assertEqual(calls[0], (0, len(blob) - 1))
        wav = [m for m in members if m["name"].endswith(".wav")][0]
        self.assertEqual(C.member_bytes(rr, wav), MEMBERS[0][1])

    def test_stream_with_and_without_descriptors(self):
        for seekable in (True, False):
            blob = make_zip(MEMBERS, seekable=seekable)
            got = C.stream_zip_members(io.BytesIO(blob), C.is_annotation_csv)
            self.assertEqual(got, {"llb3/llb3_annot.csv": CSV.encode()})
            allm = C.stream_zip_members(io.BytesIO(blob), lambda n: True)
            self.assertEqual(allm, dict(MEMBERS))

    def test_descriptor_flag_really_set(self):
        blob = make_zip(MEMBERS[:1], seekable=False)
        flags = struct.unpack("<H", blob[6:8])[0]
        self.assertTrue(flags & 8)

    def test_inflate_checks_crc(self):
        raw = zlib.compressobj(6, zlib.DEFLATED, -15)
        data = b"hello hello hello"
        comp = raw.compress(data) + raw.flush()
        crc = zlib.crc32(data) & 0xFFFFFFFF
        self.assertEqual(C.inflate(comp, 8, len(data), crc), data)
        with self.assertRaises(ValueError):
            C.inflate(comp, 8, len(data), crc ^ 1)
        with self.assertRaises(ValueError):
            C.inflate(comp, 12, len(data), crc)

    def test_zip64_extra(self):
        other = struct.pack("<HH", 0x5455, 5) + b"\x01abcd"
        z64 = struct.pack("<HH3Q", 1, 24, 10, 20, 30)
        F = 0xFFFFFFFF
        self.assertEqual(C.zip64_extra(other + z64, F, F, F), (10, 20, 30))
        only_off = struct.pack("<HHQ", 1, 8, 5000000000)
        self.assertEqual(C.zip64_extra(only_off, 7, 6, F), (7, 6, 5000000000))
        with self.assertRaises(ValueError):
            C.zip64_extra(other, F, 1, 2)
        self.assertTrue(C.has_zip64_extra(other + z64))
        self.assertFalse(C.has_zip64_extra(other))

    def test_zip64_end_records(self):
        loc = struct.pack("<4sLQL", b"PK\x06\x07", 0, 123456789012, 1)
        eocd = struct.pack("<4s4H2LH", b"PK\x05\x06", 0, 0, 0xFFFF, 0xFFFF,
                           0xFFFFFFFF, 0xFFFFFFFF, 0)
        info = C.find_eocd(b"xyz" + loc + eocd)
        self.assertTrue(info["zip64"])
        self.assertEqual(info["z64_eocd_offset"], 123456789012)
        rec = struct.pack("<4sQ2H2L4Q", b"PK\x06\x06", 44, 45, 45, 0, 0, 70000, 70000,
                          9000000, 6000000000)
        self.assertEqual(C.parse_z64_eocd(rec),
                         {"entries": 70000, "cd_size": 9000000, "cd_offset": 6000000000})
        with self.assertRaises(ValueError):
            C.find_eocd(b"xyz" + eocd)          # zip64 markers without a locator
        with self.assertRaises(ValueError):
            C.find_eocd(b"no record here")

    def test_range_reader(self):
        class Resp:
            def __init__(self, status, data, cr):
                self.status = status
                self.data = data
                self.headers = {"Content-Range": cr}

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return self.data

        seen = []

        def ok(req):
            seen.append(req.get_header("Range"))
            return Resp(206, b"abc", "bytes 10-12/999")
        log = []
        rr = C.http_range_reader("u", log, opener=ok, pause=0)
        self.assertEqual(rr(10, 12), b"abc")
        self.assertEqual(seen, ["bytes=10-12"])
        self.assertEqual(rr.state["total"], 999)
        rr2 = C.http_range_reader("u", log, opener=lambda req: Resp(200, b"x" * 9, ""), pause=0)
        with self.assertRaises(C.RangeUnsupported):
            rr2(0, 2)
        rr3 = C.http_range_reader("u", log, opener=lambda req: Resp(206, b"ab", ""), pause=0)
        with self.assertRaises(IOError):          # short reads, 4 attempts
            rr3(0, 2)
        self.assertEqual(sum(1 for x in log if x.get("range") == [0, 2]), 4)


class TestReading(unittest.TestCase):
    def test_parse_csv(self):
        rows, n, bad = C.parse_annotation_csv(CSV)
        # rows 3-6 bad: empty label, offset < onset, onset 'abc', empty audio_file
        self.assertEqual((n, bad), (6, 4))
        self.assertEqual(rows, [("f1.wav", 0.1, 0.2, "a"), ("f1.wav", 0.3, 0.4, "b")])
        self.assertEqual(C.parse_annotation_csv("label,offset_s\na,1\n")[1:], (1, 1))

    def test_songs_and_phrases(self):
        rows = [("A/f2.wav", 3.25, 3.5, "c"), ("A/f2.wav", 0.0, 0.25, "a"),
                ("A/f2.wav", 0.5, 0.75, "a"), ("A/f2.wav", 1.75, 2.0, "b"),
                ("B/f1.wav", 0.75, 1.0, "y"), ("B/f1.wav", 0.0, 0.5, "x")]
        songs = C.songs_from_rows(rows)
        # f1 sorts before f2 by file name; in f2 the gap b - a is exactly 1.0 (same song)
        # and c - b is 1.25 (new song)
        self.assertEqual([[s[2] for s in song] for song in songs],
                         [["x", "y"], ["a", "a", "b"], ["c"]])
        self.assertEqual(C.phrases(["a", "a", "b", "b", "b", "a", "c", "c"]),
                         ["a", "b", "a", "c"])

    def test_bird_inputs_and_gate(self):
        rows = ("label,onset_s,offset_s,audio_file\n"
                "x,0.0,0.5,B/f1.wav\ny,0.75,1.0,B/f1.wav\n"
                "a,0.0,0.25,A/f2.wav\na,0.5,0.75,A/f2.wav\nb,1.75,2.0,A/f2.wav\n"
                "c,3.25,3.5,A/f2.wav\n")
        dup = "label,onset_s,offset_s,audio_file\nc,3.25,3.5,A/f2.wav\n"
        phr, st = C.bird_inputs({"one.csv": rows, "two.csv": dup})
        self.assertEqual(phr, [["x", "y"], ["a", "b"], ["c"]])
        # spans 1.0 + 2.0 + 0.25
        self.assertAlmostEqual(st["song_span_s"], 3.25)
        self.assertEqual((st["rows"], st["bad_rows"], st["duplicate_rows_dropped"],
                          st["syllables"], st["classes"], st["songs"], st["phrases"],
                          st["phrase_types"], st["audio_files"]), (7, 0, 1, 6, 5, 3, 5, 5, 2))
        self.assertFalse(C.gate_bird(st)["pass"])
        good = {"rows": 1000, "bad_rows": 10, "classes": 10, "song_span_s": 15000.0}
        self.assertTrue(C.gate_bird(good)["pass"])
        self.assertFalse(C.gate_bird(dict(good, bad_rows=11))["pass"])
        self.assertFalse(C.gate_bird(dict(good, classes=9))["pass"])
        self.assertFalse(C.gate_bird(dict(good, song_span_s=14999.0))["pass"])
        self.assertFalse(C.gate_bird(dict(good, rows=0, bad_rows=0))["pass"])

    def test_blocks(self):
        songs = [["a"] * 2, ["b"] * 2, ["c"], ["d"] * 3, ["e"] * 2]
        # 2+2 = 4 -> block; 1+3 = 4 -> block; trailing 2 dropped
        self.assertEqual(C.make_blocks(songs, size=4), [songs[:2], songs[2:4]])
        self.assertEqual(C.make_blocks(songs, size=4, max_blocks=1), [songs[:2]])
        b = [["a"] * 3, ["b"], ["c"] * 4, ["d"] * 2]
        # transitions 2, 0, 3 -> cumulative 2, 2, 5 >= 4 after the third bout
        self.assertEqual(C.first_until(b, 4), b[:3])


class TestAnalysis(unittest.TestCase):
    def test_heldout_matches_zipfseg(self):
        for seed in (1, 2):
            rec = rand_songs(seed, n=9, length=11, alphabet="abcd")
            for k in (1, 2, 3):
                for alpha, skip in ((0.5, 2), (0.1, 5), (0.005, 3)):
                    self.assertAlmostEqual(C.heldout_fast(rec, k, alpha=alpha, skip=skip),
                                           z.heldout_ll(rec, k, alpha=alpha, skip=skip),
                                           places=10)

    def test_ladder(self):
        rec = rand_songs(3, n=12, length=10)
        lad = C.ladder(rec, max_k=3, alphas=(0.5, 0.1))
        for k in (1, 2, 3):
            self.assertAlmostEqual(lad["best"][k - 1],
                                   max(C.heldout_fast(rec, k, alpha=0.5, skip=3),
                                       C.heldout_fast(rec, k, alpha=0.1, skip=3)))
        self.assertAlmostEqual(lad["gains"][1], lad["best"][2] - lad["best"][1])
        self.assertEqual(len(lad["gains"]), 2)
        self.assertEqual(lad["scored"], 12 * 7)

    def test_markov3_registered(self):
        rec = rand_songs(5)
        fake = z.NULLS["markov3_pooled"](rec, random.Random(1))
        self.assertEqual([len(b) for b in fake], [len(b) for b in rec])

    def test_analyse_smoke(self):
        data = {"llb3": (rand_songs(7, n=40), C.make_blocks(rand_songs(7, n=40), size=100)),
                "llb16": (rand_songs(8, n=40), C.make_blocks(rand_songs(8, n=40), size=100))}
        res = C.analyse(data, 0.0, 1.0, b_main=2, b_rob=2, b_kirby=2, log=lambda *a: None)
        for b in data:
            self.assertIn("gains", res[b]["ladder"])
            self.assertIn("d1_n_favour_order2", res[b]["heldout_blocks"])
            self.assertEqual(res[b]["heldout_blocks"]["n_recordings"], 4)
            # t0 = 0 is long past 60% of a 1 s budget, so robustness is skipped
            self.assertEqual(len(res[b]["not_run"]), 2)
            self.assertTrue("0.5" in res[b]["by_theta"] or "0.5" in res[b].get("errors", {}))
        gr = C.grade(res, {})
        self.assertTrue(gr["provisional"])
        self.assertIsNone(gr["predictions"]["P1"])        # llb11 missing

    def test_decision3(self):
        def row(p1, p2, p3=None):
            n = {"markov1_pooled": {"p": p1}, "markov2_pooled": {"p": p2}}
            if p3 is not None:
                n["markov3_pooled"] = {"p": p3}
            return {"nulls": n}
        self.assertEqual(C.decision3(row(.001, .001, .01)), "BEYOND_THIRD_ORDER")
        self.assertEqual(C.decision3(row(.001, .01, .2)), "EXPLAINED_BY_THIRD_ORDER")
        self.assertEqual(C.decision3(row(.001, .01)), "BEYOND_SECOND_ORDER")
        self.assertEqual(C.decision3(row(.001, .3, .4)), "EXPLAINED_BY_SECOND_ORDER")
        self.assertEqual(C.decision3(row(.2, .3)), "EXPLAINED_BY_FIRST_ORDER")
        for p1, p2 in ((.001, .01), (.001, .3), (.2, .3)):
            self.assertEqual(C.decision3(row(p1, p2)), z.decision(row(p1, p2)))


def bird_res(g3, g4, m2, k2, m3=False, d1=5, rob=True):
    def row(p2, p3):
        return {"real_mean_r2": .9, "nulls": {
            "shuffle": {"p": .001}, "rotate": {"p": .001}, "bigram_within": {"p": .001},
            "markov1_pooled": {"p": .001}, "markov2_pooled": {"p": p2},
            "markov3_pooled": {"p": p3}}}
    main = row(.01 if m2 else .5, .01 if m3 else .5)
    r = {"ladder": {"gains": [.1, .02 if g3 else -.02, .01 if g4 else -.01, -.1]},
         "heldout_blocks": {"d1_n_favour_order2": d1, "n_recordings": 8},
         "by_theta": {"0.5": main},
         "kirby": row(.01 if k2 else .5, .5)}
    if rob:
        r["by_theta"]["0.3"] = main
        r["by_theta"]["0.7"] = main
    return r


class TestGrade(unittest.TestCase):
    def test_all_true(self):
        res = {b: bird_res(True, True, True, True, m3=True) for b in C.BIRD_NAMES}
        gates = {b: {"pass": True} for b in C.BIRD_NAMES}
        gr = C.grade(res, gates)
        self.assertTrue(all(gr["predictions"].values()))
        # sum of (1-p)^2 over the 8 priors = 1.9375
        self.assertAlmostEqual(gr["brier"], 1.9375 / 8)
        self.assertEqual(gr["rules"], {"C1": "TEST_SEES_REAL_SYNTAX", "C2": "KEPT_AT_KIRBY_SIZE"})
        self.assertFalse(gr["provisional"])
        self.assertEqual(gr["labels"]["llb3"]["0.5"], "BEYOND_THIRD_ORDER")
        self.assertTrue(all(gr["robust"].values()))
        self.assertEqual(gr["kirby_labels"]["llb3"], "EXPLAINED_BY_THIRD_ORDER")

    def test_blind_and_lost(self):
        res = {"llb11": bird_res(True, False, False, False),
               "llb16": bird_res(True, False, False, False),
               "llb3": bird_res(False, False, True, False, d1=4)}
        gr = C.grade(res, {"llb11": {"pass": True}})
        self.assertEqual(gr["rules"]["C1"], "TEST_BLIND_TO_REAL_SYNTAX")
        self.assertEqual(gr["rules"]["C2"], "LOST_AT_KIRBY_SIZE")
        p = gr["predictions"]
        self.assertEqual((p["P1"], p["P2"], p["P3"], p["P5"], p["P7"], p["P8"]),
                         (True, False, True, False, False, False))
        self.assertTrue(gr["provisional"])
        self.assertEqual(gr["labels"]["llb11"]["0.5"], "EXPLAINED_BY_SECOND_ORDER")

    def test_mixed_and_no_ground_truth(self):
        res = {"llb11": bird_res(True, False, True, True),
               "llb16": bird_res(True, False, False, False),
               "llb3": bird_res(False, False, False, False)}
        gr = C.grade(res, {})
        self.assertEqual(gr["rules"], {"C1": "TEST_MIXED", "C2": "KEPT_AT_KIRBY_SIZE"})
        res = {b: bird_res(False, False, False, False) for b in C.BIRD_NAMES}
        res["llb3"] = bird_res(True, False, False, False)
        gr = C.grade(res, {})
        self.assertEqual(gr["rules"], {"C1": "NO_GROUND_TRUTH",
                                       "C2": "NOTHING_DETECTED_AT_FULL_SIZE"})

    def test_missing_and_errors(self):
        res = {b: bird_res(True, True, True, True) for b in C.BIRD_NAMES}
        res["llb3"]["ladder"] = {"error": "x"}
        del res["llb16"]["kirby"]
        res["llb11"]["heldout_blocks"] = {"error": "y"}
        gr = C.grade(res, {})
        p = gr["predictions"]
        self.assertIsNone(p["P1"])
        self.assertIsNone(p["P7"])
        self.assertIsNone(p["P8"])
        self.assertTrue(p["P5"])
        self.assertFalse(p["P6"])                 # m3 not beaten in bird_res by default
        # graded: P3, P4, P5, P6 (P1, P2, P7, P8 have a missing bird)
        self.assertEqual(len(gr["graded"]), 4)
        self.assertEqual(gr["rules"]["C1"], "NOT_GRADED")
        self.assertEqual(gr["rules"]["C2"], "NOT_GRADED")


if __name__ == "__main__":
    unittest.main()
