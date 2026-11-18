# SPDX-License-Identifier: Apache-2.0
# test_whale_run.py: tests of the PREREG-AMENDMENT-5 reading and gates (stdlib only).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import csv
import io
import os
import shutil
import tempfile
import unittest

import whale_run as R

HDR = ["", "song_type", "cycle", "string", "sentence_number", "length", "repertoire_size"]


def make_csv(rows, length_override=None):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HDR)
    for i, (y, seq) in enumerate(rows):
        n = len(seq) if length_override is None else length_override
        w.writerow([i, y, 1, repr(seq), i, n, 3])
    return buf.getvalue()


def full_data(extra_elements=0):
    """Data with the expected recordings per song type and Table S1's total elements."""
    data = {}
    for y in R.SONG_TYPES:
        data[y] = [["a"] for _ in range(R.EXPECTED_RECS[y])]
    n = sum(len(r) for recs in data.values() for r in recs)
    data[2010][0] = ["a"] * (1 + R.TABLE_S1_TOTAL_ELEMENTS - n + extra_elements)
    return data


class TestParse(unittest.TestCase):
    def test_literal_parse_keeps_spaces_and_commas(self):
        text = make_csv([(2016, ["gr(s)-aws(s)", "b c", "d,e"]), (2010, ["x"])])
        data, rep = R.parse_s2(text)
        self.assertEqual(data, {2016: [["gr(s)-aws(s)", "b c", "d,e"]], 2010: [["x"]]})
        self.assertEqual(rep["n_rows"], 2)
        self.assertEqual(rep["bad_rows"], 0)
        self.assertEqual(rep["length_column_mismatch"], 0)
        self.assertEqual(rep["elements"], {"2010": 1, "2016": 3})
        self.assertEqual(rep["recordings"], {"2010": 1, "2016": 1})
        self.assertEqual(rep["total_elements"], 4)

    def test_bad_rows_and_length_mismatch(self):
        text = make_csv([(2011, ["a", "b"])], length_override=5)
        text += '9,2012,1,not a list,9,1,1\n9,2013,1,"[1, 2]",9,2,1\n9,20x,1,"[\'a\']",9,1,1\n'
        data, rep = R.parse_s2(text)
        self.assertEqual(data, {2011: [["a", "b"]]})
        self.assertEqual(rep["n_rows"], 4)
        self.assertEqual(rep["bad_rows"], 3)
        self.assertEqual(rep["length_column_mismatch"], 1)

    def test_order_within_type_is_file_order(self):
        text = make_csv([(2014, ["p"]), (2014, ["q", "r"]), (2012, ["s"])])
        data, _ = R.parse_s2(text)
        self.assertEqual(data[2014], [["p"], ["q", "r"]])


class TestGateA(unittest.TestCase):
    def rep(self, data, bad=0):
        return {"bad_rows": bad}

    def test_pass(self):
        d = full_data()
        ok, why = R.gate_a(d, self.rep(d))
        self.assertTrue(ok, why)
        self.assertEqual(sum(len(r) for recs in d.values() for r in recs), 45760)
        self.assertEqual(sum(len(v) for v in d.values()), 55)

    def test_total_tolerance(self):
        d = full_data(extra_elements=228)          # 228 <= 0.005 * 45760 = 228.8
        self.assertTrue(R.gate_a(d, self.rep(d))[0])
        d = full_data(extra_elements=229)
        self.assertFalse(R.gate_a(d, self.rep(d))[0])

    def test_fail_recordings_types_and_parse(self):
        d = full_data()
        d[2015].append(["a"])
        ok, why = R.gate_a(d, self.rep(d))
        self.assertFalse(ok)
        self.assertIn("2015: 14 recordings, expected 13", why)
        d = full_data()
        d[2018] = [["a"]]
        self.assertFalse(R.gate_a(d, self.rep(d))[0])
        d = full_data()
        self.assertFalse(R.gate_a(d, self.rep(d, bad=1))[0])


class TestGateB(unittest.TestCase):
    def test_exact_and_tolerance(self):
        self.assertTrue(R.code_s1_gate(0.9302888665216734, 3386)["pass"])
        self.assertTrue(R.code_s1_gate(0.9302888665216734 + 5e-7, 3386)["pass"])
        self.assertFalse(R.code_s1_gate(0.9302888665216734 + 2e-6, 3386)["pass"])
        self.assertFalse(R.code_s1_gate(0.9302888665216734, 3385)["pass"])
        self.assertFalse(R.code_s1_gate(float("nan"), 3386)["pass"])
        self.assertIsNone(R.code_s1_gate(float("nan"), 3386)["abs_diff"])

    def test_apply_gate_b(self):
        final = {"zipf": {"label": "BEYOND_SECOND_ORDER", "headline": True, "notes": []},
                 "brevity": {"label": "EXPLAINED_BY_FIRST_ORDER", "headline": True,
                             "notes": ["x"]}}
        kept = R.apply_gate_b(final, True)
        self.assertEqual(kept, final)
        off = R.apply_gate_b(final, False)
        self.assertFalse(off["zipf"]["headline"])
        self.assertFalse(off["brevity"]["headline"])
        self.assertEqual(len(off["brevity"]["notes"]), 2)
        self.assertEqual(off["zipf"]["label"], "BEYOND_SECOND_ORDER")
        self.assertTrue(final["zipf"]["headline"])        # input not modified
        self.assertEqual(final["brevity"]["notes"], ["x"])


class TestRegistration(unittest.TestCase):
    def test_found_after_two_polls(self):
        calls = []
        slept = []

        def fetch(url):
            calls.append(url)
            if len(calls) == 1:
                raise IOError("offline")
            if len(calls) == 2:
                return []
            return [{"sha": "abc", "commit": {"committer": {"date": "2026-11-18T12:00:00Z"}}}]
        reg = R.registration(fetch=fetch, wait_minutes=5, sleep=slept.append, poll_s=60)
        self.assertEqual(reg, {"found": True, "sha": "abc", "utc": "2026-11-18T12:00:00Z",
                               "polls": 3})
        self.assertEqual(slept, [60, 60])
        self.assertIn("PREREG-AMENDMENT-5.md", calls[0])

    def test_not_found(self):
        slept = []
        reg = R.registration(fetch=lambda url: [], wait_minutes=2, sleep=slept.append,
                             poll_s=60)
        self.assertEqual(reg, {"found": False, "polls": 3})
        self.assertEqual(slept, [60, 60])


class TestMisc(unittest.TestCase):
    def test_table_s1_compare(self):
        out = R.table_s1_compare({2015: [["a", "b"], ["c"]]})
        self.assertEqual(out["2015"], {"recordings": 2, "table_s1_recordings": 12,
                                       "elements": 3, "table_s1_elements": 13251})
        self.assertEqual(out["2010"]["recordings"], 0)
        self.assertEqual(len(out), 8)

    def test_find_s2(self):
        root = tempfile.mkdtemp()
        try:
            self.assertIsNone(R.find_s2(root))
            sub = os.path.join(root, "unzipped", "x.zip")
            os.makedirs(sub)
            p = os.path.join(sub, R.S2_NAME)
            with open(p, "w", encoding="utf-8") as f:
                f.write("x")
            self.assertEqual(R.find_s2(root), p)
            self.assertEqual(len(R.sha256_file(p)), 64)
        finally:
            shutil.rmtree(root)

    def test_constants(self):
        self.assertEqual(sum(R.EXPECTED_RECS.values()), 55)
        self.assertEqual(sum(v[0] for v in R.TABLE_S1.values()), 55)
        self.assertEqual(sum(v[1] for v in R.TABLE_S1.values()), R.TABLE_S1_TOTAL_ELEMENTS)
        self.assertEqual(R.PRIMARY_BREVITY_KEY, "brev_year")
        self.assertEqual(R.CALIB2, {"K5": True, "K6": False})
        self.assertEqual(R.CALIB4, {"Q10": True, "Q11": True})


if __name__ == "__main__":
    unittest.main()
