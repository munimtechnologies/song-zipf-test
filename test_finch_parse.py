# SPDX-License-Identifier: Apache-2.0
# Offline tests for finch_parse on small hand-made samples in the printed
# Dataset format ("bird age letters-with-spaces"). MV2, Munim, Inc.; made with AI agents.
import random
import unittest

import finch_parse as fp
import zipfseg as z


class TestHeader(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(fp.match_header("RKi", "71"), ("RKi", 71, 0))
        self.assertEqual(fp.match_header("LShiro", "93"), ("LShiro", 93, 0))

    def test_ocr_noise(self):
        self.assertEqual(fp.match_header("RK1", "71"), ("RKi", 71, 1))
        self.assertEqual(fp.match_header("Shir0", "105"), ("Shiro", 105, 1))
        self.assertEqual(fp.match_header("RAo", "6l"), ("RAo", 61, 0))
        # RMo 91 (name 0 + 1 digit) beats RAo 61 (name 1 + 0 digits) on name distance
        self.assertEqual(fp.match_header("RMo", "61"), ("RMo", 91, 1))

    def test_rejects(self):
        self.assertIsNone(fp.match_header("Dataset:", "The"))
        self.assertIsNone(fp.match_header("abc", "ab"))      # no digit in day token
        self.assertIsNone(fp.match_header("RKi", "1234"))
        self.assertIsNone(fp.match_header("Pigeon", "71"))   # name too far


class TestParse(unittest.TestCase):
    LINES = [
        "Dataset: The complete set of songs analysed in the paper.",
        "",
        "RKi 71 ab cab",
        "cd",
        "RAo 6l abab",
        "Shiro 64 x1y",
    ]

    def test_rows(self):
        rows, st = fp.parse_lines(self.LINES)
        self.assertEqual([(r["bird"], r["day"]) for r in rows],
                         [("RKi", 71), ("RAo", 61), ("Shiro", 64)])
        self.assertEqual(rows[0]["words"], ["ab", "cab", "cd"])
        self.assertEqual(rows[0]["wraps"], [5])
        self.assertEqual(fp.printed_cuts(rows[0]), [2, 5])
        self.assertEqual(rows[2]["words"], ["xy"])
        self.assertEqual(rows[2]["bad_chars"], 1)
        self.assertEqual(st["ignored_lines"], 1)
        self.assertEqual(st["continuation_lines"], 1)
        self.assertEqual(st["header_lines"], 3)

    def test_recordings(self):
        rows, _ = fp.parse_lines(self.LINES)
        recs = fp.recordings_from_rows(rows)
        self.assertEqual(recs[("RKi", 71)], [list("abcabcd")])

    def test_validate_roundtrip(self):
        # print our own segmentation, parse it back: agreement must be perfect
        rng = random.Random(4)
        lines = []
        for bird, day in (("RKi", 71), ("Atama", 62)):
            bouts = [[rng.choice("abcde") for _ in range(rng.randint(5, 40))] for _ in range(6)]
            for segs in z.segment_recording_bouts(bouts, 0.5):
                lines.append("%s %d %s" % (bird, day, " ".join("".join(s) for s in segs)))
        rows, _ = fp.parse_lines(lines)
        v = fp.validate(rows)
        self.assertEqual(v["bouts"], 12)
        self.assertEqual(v["recordings_found"], 2)
        self.assertEqual(v["printed_cuts"], v["pipeline_cuts"])
        self.assertEqual(v["cut_agreement"]["bouts_identical"], 12)
        self.assertEqual(v["cut_agreement"]["printed_only"], 0)
        self.assertEqual(v["cut_agreement"]["pipeline_only"], 0)
        self.assertEqual(v["gate"], "FAIL")          # only 2 of 30 recordings
        self.assertFalse(v["exact"]["recordings"])


class TestGate(unittest.TestCase):
    def base(self):
        return {"n_exact": 3, "recordings_found": 30, "bouts": 298,
                "transitions": 19950, "cut_agreement": {"f1": 0.97}}

    def test_approx(self):
        self.assertEqual(fp.gate(self.base()), "PASS_APPROX")

    def test_exact(self):
        v = self.base()
        v["n_exact"] = 5
        self.assertEqual(fp.gate(v), "PASS_EXACT")

    def test_fail(self):
        for key, val in (("recordings_found", 29), ("bouts", 295), ("transitions", 19800)):
            v = self.base()
            v[key] = val
            self.assertEqual(fp.gate(v), "FAIL")
        v = self.base()
        v["cut_agreement"] = {"f1": 0.94}
        self.assertEqual(fp.gate(v), "FAIL")
        v["cut_agreement"] = {"f1": float("nan")}
        self.assertEqual(fp.gate(v), "FAIL")


if __name__ == "__main__":
    unittest.main()
