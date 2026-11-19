# SPDX-License-Identifier: Apache-2.0
# test_holdc_results.py: the grader for the held-out test on collapsed humpback song
# (HOLDC-PREREG.md, job song-zipf-holdc-v1), written and published BEFORE the job has
# produced any result. With its own code (it imports neither holdc.py nor hold.py) it
# re-derives the Control/R1/R2 labels, predictions Q1-Q7 and the Brier score from the raw
# job output; checks every p value, label, seed, B, held-out gain, best order, mean entropy,
# null mean, bout count and size for internal consistency; checks the whale sizes, bouts and
# data hash against RESULTS-RUNS.md (results/runs/runs_results.json); checks it all against
# the job's own grading; and fixes now the exact lines RESULTS-HOLDC.md must print
# (render_md_lines). Until results/holdc/holdc_results.json exists the result tests are
# skipped; the toy-data tests always run. Stdlib only; reads files only if they exist and
# writes nothing.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import copy
import hashlib
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "holdc", "holdc_results.json")
MD = os.path.join(HERE, "RESULTS-HOLDC.md")
PREREG = os.path.join(HERE, "HOLDC-PREREG.md")
HOLDC = os.path.join(HERE, "holdc.py")
HAVE = os.path.exists(RES)

VERSION = "holdc-1"
SEED = 20261121
LMAX = 8
ALPHA = 0.05
KMAX = 5
B_WHALE = 1000
B_NEG = 200
B_REP = 200
B_EN = 100
N_REP = 3
N_EN = 5
EN_STRIDE = 1850
N_REC = 8
YEARS = list(range(2010, 2018))
# From results/runs/runs_results.json (job song-zipf-runs-v1, the same Data S2 file)
WHALE_DATA_SHA256 = "755e4357ce50c672e961671598299c84d074514b4c66bd436ac0c71a3ea11cff"
WHALE_ELEMENTS = [1053, 2028, 3351, 2664, 5765, 14429, 7282, 9177]
WHALE_COLLAPSED = [248, 766, 1233, 908, 3141, 2926, 3046, 4403]
WHALE_BOUTS = [4, 6, 6, 6, 7, 13, 6, 7]          # recordings per year = bouts
# SHA-256 of every module setup_holdc.sh fetches (the values earlier jobs recorded)
PINNED = {"hold.py": "6ac8be4474968be23da2b42c76de2427dfe9d0177d32026b329ada0d63e02e4c",
          "runs.py": "82d4fbfce43dd24addfb9bd00eb827f650ca9af502785b6e3d119db73f618052",
          "zipfseg.py": "25002193229e6d6568939856de5a1760a41c3b462582ea06b6d75ba6d84bddf5",
          "cds_job.py": "a1564f8d48145642bd4dbf09488fd7e086f152e1a0fe4e15dc9775f0ba00c55d",
          "whale_run.py": "b1e128e0eb5f6a211335aa1f402124e94517f751450adf574dd4e742e46211a0"}
BSO = "BEYOND_SECOND_ORDER_HELDOUT"
ND = "NOT_DETECTED"
R1_BEYOND = "BEYOND_SECOND_ORDER_AFTER_COLLAPSE_HELDOUT"
R1_NOT = "NOT_DETECTED_WITH_POWER"
FOOLS = "REPETITION_FOOLS_HOLD"
NOT_FOOLS = "REPETITION_DOES_NOT_FOOL_HOLD"
MISSING = "WHALE_DATA_MISSING"
STATUSES = ("ok", "timeout_partial", "cds_gate_fail_or_no_data")
ORDER = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7")
PRIORS = {"Q1": 0.55, "Q2": 0.85, "Q3": 0.85, "Q4": 0.85, "Q5": 0.80, "Q6": 0.75,
          "Q7": 0.50}
PRED_TEXT = {"Q1": "the collapsed whale song is detected (p < 0.05)",
             "Q2": "English is detected in at least 4 of 5 replicates",
             "Q3": "at most 1 of 5 English negative controls is detected",
             "Q4": "the whale negative control is not detected",
             "Q5": "HOLD on the uncollapsed repetition-only song is detected in at least 2 "
                   "of 3",
             "Q6": "the collapsed repetition-only song is detected in none of 3",
             "Q7": "the collapsed whale's mean held-out gain is above zero"}
EXPECTED_CONFIG = {"seed": SEED, "lmax": LMAX, "alpha": ALPHA, "b_whale": B_WHALE,
                   "b_neg": B_NEG, "b_rep": B_REP, "b_en": B_EN, "n_rep": N_REP,
                   "n_en": N_EN, "en_stride": EN_STRIDE, "q": 0.35, "cell_max": 4,
                   "copies_max": 3, "kmax": KMAX}


# --------------------------------------------------------------------------
# independent re-implementation of HOLDC-PREREG.md sections 5 and 6
# --------------------------------------------------------------------------
def detected(t):
    return t["p"] < ALPHA


def lab(t):
    return BSO if detected(t) else ND


def regrade(r):
    w = r.get("whale") or {}
    ok = w.get("status") == "ok"
    eng = [x for x in (r.get("english") or []) if x.get("status") == "ok"]
    rp = r.get("repetition") or []
    en_complete = len(eng) == N_EN
    rep_complete = len(rp) == N_REP
    e_det = sum(1 for x in eng if detected(x["real"]))
    e_neg = sum(1 for x in eng if detected(x["neg"]))
    u_det = sum(1 for x in rp if detected(x["uncollapsed"]))
    c_det = sum(1 for x in rp if detected(x["collapsed"]))
    w_neg = detected(w["neg"]) if ok else None
    if not (ok and en_complete and rep_complete):
        control = "CALIBRATION_INCOMPLETE"
    elif e_det >= 4 and e_neg <= 1 and not w_neg and c_det <= 1:
        control = "CONTROL_OK"
    else:
        control = "CONTROL_FAILED"
    g = dict.fromkeys(ORDER)
    if en_complete:
        g["Q2"] = e_det >= 4
        g["Q3"] = e_neg <= 1
    if rep_complete:
        g["Q5"] = u_det >= 2
        g["Q6"] = c_det == 0
    if ok:
        g["Q1"] = detected(w["real"])
        g["Q4"] = not w_neg
        g["Q7"] = w["real"]["mean_gain"] > 0
        if control != "CONTROL_OK":
            r1 = control
        else:
            r1 = R1_BEYOND if detected(w["real"]) else R1_NOT
    else:
        r1 = MISSING
    if not rep_complete:
        r2 = "INCOMPLETE"
    else:
        r2 = FOOLS if u_det >= 2 else NOT_FOOLS
    scored = [k for k in ORDER if g[k] is not None]
    brier = (sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in scored) / len(scored)
             if scored else None)
    return {"rules": {"R1_whale_after_collapse": r1, "R2_repetition_alone": r2,
                      "control": control, "english_detected": e_det,
                      "english_negative_detected": e_neg,
                      "repetition_uncollapsed_detected": u_det,
                      "repetition_collapsed_detected": c_det,
                      "whale_negative_detected": w_neg},
            "predictions": g, "priors": dict(PRIORS), "brier": brier,
            "n_scored": len(scored), "en_complete": en_complete,
            "rep_complete": rep_complete, "n_en": len(eng), "n_rep": len(rp)}


# --------------------------------------------------------------------------
# internal consistency of the raw output
# --------------------------------------------------------------------------
def finite(x):
    return (isinstance(x, (int, float)) and not isinstance(x, bool) and x == x
            and abs(x) != float("inf"))


def close(a, b, tol=1e-9):
    if a is None or b is None:
        return a is None and b is None
    if a != a and b != b:
        return True
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def p_ok(p, n):
    """p = (1 + k) / (1 + n) for an integer 0 <= k <= n."""
    k = p * (n + 1) - 1
    return abs(k - round(k)) < 1e-6 and 0 <= round(k) <= n


def argmin(v):
    """Index of the smallest value; the lowest index on ties."""
    best = 0
    for i in range(1, len(v)):
        if v[i] < v[best]:
            best = i
    return best


def check_test(t, B, seed, tag, symbols=None, max_symbols=None, bouts=None):
    """One held-out test (the output of hold.test_set over the 8 recordings)."""
    if not isinstance(t, dict):
        return [tag + ": missing"]
    bad = []

    def need(cond, what):
        if not cond:
            bad.append("%s: %s" % (tag, what))

    need(t.get("B") == B, "B")
    need(t.get("seed") == seed, "seed")
    need(t.get("kmax") == KMAX, "kmax")
    p = t.get("p")
    need(finite(p) and p_ok(p, B), "p")
    need(finite(p) and t.get("label") == lab(t), "label")
    per = t.get("per_recording") or []
    need(len(per) == N_REC, "number of recordings")
    gains, hs, nms = [], [], []
    for i, x in enumerate(per):
        H = x.get("H") or []
        g = x.get("gain")
        if len(H) != KMAX + 1 or not all(finite(h) for h in H) or not finite(g):
            need(False, "non-finite or missing H or gain, recording %d" % i)
            continue
        gains.append(g)
        hs.append(H)
        nms.append(x.get("null_mean"))
        need(close(g, H[2] - min(H[3:])), "gain, recording %d" % i)
        need(x.get("best_order") == argmin(H), "best order, recording %d" % i)
        need(finite(x.get("p")) and p_ok(x["p"], B), "p, recording %d" % i)
        need(finite(x.get("null_sd")) and x["null_sd"] >= 0, "null sd, recording %d" % i)
        nb = x.get("bouts")
        need(isinstance(nb, int) and nb >= 2, "fewer than 2 bouts, recording %d" % i)
        if bouts is not None and i < len(bouts):
            need(nb == bouts[i], "bouts, recording %d" % i)
        if symbols is not None and i < len(symbols):
            need(x.get("symbols") == symbols[i], "symbols, recording %d" % i)
        if max_symbols is not None and i < len(max_symbols):
            s = x.get("symbols")
            need(isinstance(s, int) and 0 < s <= max_symbols[i],
                 "symbols above the real data, recording %d" % i)
    if per and len(gains) == len(per):
        need(close(t.get("mean_gain"), sum(gains) / len(gains)), "mean gain")
        mh = t.get("mean_H") or []
        need(len(mh) == KMAX + 1 and
             all(close(mh[k], sum(h[k] for h in hs) / len(hs)) for k in range(KMAX + 1)),
             "mean H")
        need(all(finite(v) for v in nms) and
             close(t.get("null_mean"), sum(nms) / len(nms)), "null mean")
    need(finite(t.get("null_sd")) and t["null_sd"] >= 0, "null sd")
    return bad


def bouts_of(t):
    return [y.get("bouts") for y in (t or {}).get("per_recording") or []]


def check_result(r):
    bad = []
    w = r.get("whale") or {}
    ok = w.get("status") == "ok"
    if ok:
        if w.get("years") != YEARS:
            bad.append("whale: years %r" % (w.get("years"),))
        if not (w.get("gate_a") or {}).get("pass"):
            bad.append("whale: gate A not passed but status ok")
        if w.get("data_sha256") != WHALE_DATA_SHA256:
            bad.append("whale: data sha256 differs from RUNS")
        if w.get("elements") != WHALE_ELEMENTS:
            bad.append("whale: sizes differ from RUNS")
        if w.get("elements_collapsed") != WHALE_COLLAPSED:
            bad.append("whale: collapsed sizes differ from RUNS")
        bad += check_test(w.get("real"), B_WHALE, SEED + 1, "whale real",
                          symbols=WHALE_COLLAPSED, bouts=WHALE_BOUTS)
        bad += check_test(w.get("neg"), B_NEG, SEED + 3, "whale negative",
                          max_symbols=WHALE_COLLAPSED, bouts=WHALE_BOUTS)
    eng = r.get("english") or []
    rp = r.get("repetition") or []
    if (eng or rp) and not ok:
        bad.append("controls without whale data")
    if [x.get("rep") for x in eng] != list(range(len(eng))):
        bad.append("English replicates out of order")
    for x in eng:
        rep = x.get("rep")
        tag = "english %s" % (rep,)
        if not (isinstance(rep, int) and 0 <= rep < N_EN):
            bad.append(tag + ": not in design")
            continue
        if x.get("start_utt") != rep * EN_STRIDE:
            bad.append(tag + ": start utterance")
        st = x.get("status")
        if st == "corpus_exhausted":
            continue
        if st != "ok":
            bad.append(tag + ": status %r" % (st,))
            continue
        ph = x.get("phonemes") or []
        pc = x.get("phonemes_collapsed") or []
        if len(ph) != N_REC or len(pc) != N_REC:
            bad.append(tag + ": number of recordings")
            continue
        if any(a < t for a, t in zip(ph, WHALE_COLLAPSED)):
            bad.append(tag + ": recording smaller than the collapsed whale year")
        if any(not 0 < c <= a for a, c in zip(ph, pc)):
            bad.append(tag + ": collapsed sizes")
        end = x.get("end_utt")
        if not (isinstance(end, int) and end > rep * EN_STRIDE):
            bad.append(tag + ": end utterance")
        s = SEED + 10000 * (rep + 1)
        bad += check_test(x.get("real"), B_EN, s, tag + " real", symbols=pc)
        bad += check_test(x.get("neg"), B_EN, s + 2, tag + " negative", max_symbols=pc)
        if bouts_of(x.get("real")) != bouts_of(x.get("neg")):
            bad.append(tag + ": negative control bouts differ from real")
    if [x.get("i") for x in rp] != list(range(len(rp))):
        bad.append("repetition data sets out of order")
    for x in rp:
        i = x.get("i")
        tag = "repetition %s" % (i,)
        if not (isinstance(i, int) and 0 <= i < N_REP):
            bad.append(tag + ": not in design")
            continue
        s = SEED + 100 * (i + 1)
        if x.get("seed") != s:
            bad.append(tag + ": seed")
        eb = x.get("elements_base") or []
        ei = x.get("elements_inflated") or []
        ec = x.get("elements_collapsed") or []
        if not (len(eb) == len(ei) == len(ec) == N_REC):
            bad.append(tag + ": number of recordings")
            continue
        if any(not 0 < b <= t for b, t in zip(eb, WHALE_COLLAPSED)):
            bad.append(tag + ": base sizes")
        if any(a < b for a, b in zip(ei, eb)):
            bad.append(tag + ": inflated smaller than base")
        if any(not 0 < c <= a for a, c in zip(ei, ec)):
            bad.append(tag + ": collapsed sizes")
        elif not close(x.get("share_removed"),
                       sum(1.0 - c / a for a, c in zip(ei, ec)) / N_REC):
            bad.append(tag + ": share removed")
        br = x.get("bouts_recovered")
        if not (finite(br) and 0 <= br <= 1):
            bad.append(tag + ": bouts recovered")
        bad += check_test(x.get("uncollapsed"), B_REP, s + 2, tag + " uncollapsed",
                          symbols=ei, bouts=WHALE_BOUTS)
        bad += check_test(x.get("collapsed"), B_REP, s + 3, tag + " collapsed",
                          symbols=ec, bouts=WHALE_BOUTS)
    return bad


def check_meta(r, prereg_sha=None, holdc_sha=None):
    bad = []
    if r.get("version") != VERSION:
        bad.append("version")
    if r.get("status") not in STATUSES:
        bad.append("status %r" % (r.get("status"),))
    reg = r.get("registration") or {}
    if not reg.get("found"):
        bad.append("registration not found")
    if prereg_sha and reg.get("sha256") != prereg_sha:
        bad.append("registration sha256 differs from HOLDC-PREREG.md")
    cs = r.get("code_sha256") or {}
    for m in sorted(PINNED):
        if cs.get(m) != PINNED[m]:
            bad.append("%s sha256" % m)
    if holdc_sha and cs.get("holdc.py") != holdc_sha:
        bad.append("holdc.py sha256 differs from the published holdc.py")
    if r.get("config") != EXPECTED_CONFIG:
        bad.append("config")
    if "grading" not in r:
        bad.append("no grading")
    if r.get("status") == "ok" and not (len(r.get("english") or []) == N_EN and
                                        len(r.get("repetition") or []) == N_REP):
        bad.append("status ok but a part did not run")
    return bad


def compare_grading(gr, rg):
    """Mismatches between the job's own grading and the regrade (empty list = agree)."""
    bad = []
    if gr.get("rules") != rg["rules"]:
        bad.append("rules")
    if gr.get("predictions") != rg["predictions"]:
        bad.append("predictions")
    if gr.get("priors") != PRIORS:
        bad.append("priors")
    if not close(gr.get("brier"), rg["brier"]):
        bad.append("brier")
    if gr.get("n_scored") != rg["n_scored"]:
        bad.append("n_scored")
    return bad


# --------------------------------------------------------------------------
# formats fixed before the result exists (RESULTS-HOLDC.md must contain these lines)
# --------------------------------------------------------------------------
def whale_line(w):
    t = w["real"]
    return ("Whale, repeats collapsed: mean held-out gain **{:+.4f}** bits per element against "
            "{:+.4f} (sd {:.4f}) for collapse-consistent second-order surrogates (B = {:,}), "
            "p = **{:.4f}**, label **`{}`**").format(
        t["mean_gain"], t["null_mean"], t["null_sd"], t["B"], t["p"], lab(t))


def neg_line(w):
    t = w["neg"]
    return ("Whale negative control (one collapse-consistent second-order surrogate): mean gain "
            "{:+.4f} against {:+.4f} (B = {:,}), p = {:.4f}, label `{}`").format(
        t["mean_gain"], t["null_mean"], t["B"], t["p"], lab(t))


def entropy_line(w):
    return ("Whale, repeats collapsed, mean held-out cross-entropy by context order 0 to 5 "
            "(bits per element): " + ", ".join("{:.4f}".format(h) for h in w["real"]["mean_H"]))


def year_row(w, i):
    """| year | elements | after collapsing | bouts | H order 2 | best of orders 3-5 | gain |
    p |"""
    x = w["real"]["per_recording"][i]
    return "| {} | {:,} | {:,} | {} | {:.4f} | {:.4f} | {:+.4f} | {:.4f} |".format(
        w["years"][i], w["elements"][i], w["elements_collapsed"][i], x["bouts"], x["H"][2],
        min(x["H"][3:]), x["gain"], x["p"])


def en_row(x):
    """| replicate | first utterance | next utterance | phonemes | after collapsing | gain | p |
    label | negative gain | negative p | negative label |"""
    if x.get("status") != "ok":
        return "| {} | {:,} | `{}` |".format(x["rep"], x["start_utt"], x.get("status"))
    a, b = x["real"], x["neg"]
    return ("| {} | {:,} | {:,} | {:,} | {:,} | {:+.4f} | {:.4f} | `{}` | {:+.4f} | {:.4f} | "
            "`{}` |").format(x["rep"], x["start_utt"], x["end_utt"], sum(x["phonemes"]),
                             sum(x["phonemes_collapsed"]), a["mean_gain"], a["p"], lab(a),
                             b["mean_gain"], b["p"], lab(b))


def rep_row(x):
    """| data set | base elements | after inflating | after collapsing | share removed | bouts
    recovered | uncollapsed gain | p | label | collapsed gain | p | label |"""
    a, b = x["uncollapsed"], x["collapsed"]
    return ("| {} | {:,} | {:,} | {:,} | {:.4f} | {:.4f} | {:+.4f} | {:.4f} | `{}` | {:+.4f} | "
            "{:.4f} | `{}` |").format(
        x["i"], sum(x["elements_base"]), sum(x["elements_inflated"]),
        sum(x["elements_collapsed"]), x["share_removed"], x["bouts_recovered"],
        a["mean_gain"], a["p"], lab(a), b["mean_gain"], b["p"], lab(b))


def pred_end(k, v):
    return "| {:.2f} | **{}** |".format(
        PRIORS[k], "not graded" if v is None else ("true" if v else "false"))


def yes_no(v):
    return "not run" if v is None else ("yes" if v else "no")


def required_strings(r, rg):
    w = r.get("whale") or {}
    need = ["Job status: `%s`; whale data status: `%s`" % (r.get("status"), w.get("status"))]
    if w.get("status") == "ok":
        need += [whale_line(w), neg_line(w), entropy_line(w)]
        need += [year_row(w, i) for i in range(len(w["years"]))]
    need += [en_row(x) for x in sorted(r.get("english") or [], key=lambda x: x["rep"])]
    need += [rep_row(x) for x in sorted(r.get("repetition") or [], key=lambda x: x["i"])]
    ru = rg["rules"]
    need.append(("Control: **`{}`** (English detected in {} of {} replicates, its negative "
                 "controls in {}; whale negative control detected: {}; collapsed "
                 "repetition-only song detected in {} of {})").format(
        ru["control"], ru["english_detected"], rg["n_en"], ru["english_negative_detected"],
        yes_no(ru["whale_negative_detected"]), ru["repetition_collapsed_detected"],
        rg["n_rep"]))
    need.append("R1 whale after collapsing repeats: **`%s`**" % ru["R1_whale_after_collapse"])
    need.append(("R2 repetition alone: **`{}`** (HOLD as registered detected the uncollapsed "
                 "repetition-only song in {} of {} data sets)").format(
        ru["R2_repetition_alone"], ru["repetition_uncollapsed_detected"], rg["n_rep"]))
    scored = [k for k in ORDER if rg["predictions"][k] is not None]
    ntrue = sum(1 for k in scored if rg["predictions"][k])
    need.append("%d of %d graded predictions true" % (ntrue, len(scored)))
    if scored:
        need.append("Brier score **%.3f**" % rg["brier"])
    return need


def render_md_lines(r, rg):
    """Every fixed line, in one list (prediction rows included), for writing RESULTS-HOLDC.md."""
    return required_strings(r, rg) + [
        "| %s | %s %s" % (k, PRED_TEXT[k], pred_end(k, rg["predictions"][k])) for k in ORDER]


def check_md(md, r, rg):
    """List of required lines missing from md (empty list = all present)."""
    missing = [s for s in required_strings(r, rg) if s not in md]
    lines = md.splitlines()
    for k in ORDER:
        hits = [ln for ln in lines if ln.startswith("| %s |" % k)]
        if len(hits) != 1 or not hits[0].rstrip().endswith(pred_end(k, rg["predictions"][k])):
            missing.append("prediction row " + k)
    return missing


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# --------------------------------------------------------------------------
# result tests (skipped until the job's output is published)
# --------------------------------------------------------------------------
@unittest.skipUnless(HAVE, "results/holdc/holdc_results.json not published yet")
class TestHoldcResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        cls.rg = regrade(cls.r)
        cls.md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""

    def test_meta(self):
        self.assertEqual(check_meta(
            self.r, sha256_file(PREREG) if os.path.exists(PREREG) else None,
            sha256_file(HOLDC) if os.path.exists(HOLDC) else None), [])

    def test_consistency(self):
        self.assertEqual(check_result(self.r), [])

    def test_grading_matches_regrade(self):
        self.assertEqual(compare_grading(self.r["grading"], self.rg), [])

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-HOLDC.md not written yet")
    def test_md_lines(self):
        self.assertEqual(check_md(self.md, self.r, self.rg), [])


# --------------------------------------------------------------------------
# toy tests (always run; every expected value worked out by hand)
# --------------------------------------------------------------------------
def mk_test(B, seed, g, k, symbols, bouts, null_mean=-0.05, null_sd=0.004):
    """A consistent held-out test: every recording has gain g (g > -0.1) and p (1+k)/(1+B)."""
    p = (1 + k) / (1 + B)
    per = []
    for i in range(N_REC):
        H = [3.0, 2.5, 2.0, 2.0 - g, 2.1, 2.2]
        per.append({"H": H, "gain": H[2] - min(H[3:]), "p": p, "null_mean": null_mean,
                    "null_sd": 0.01, "best_order": argmin(H), "symbols": symbols[i],
                    "bouts": bouts[i]})
    gains = [x["gain"] for x in per]
    return {"B": B, "seed": seed, "kmax": KMAX, "mean_gain": sum(gains) / len(gains), "p": p,
            "label": BSO if p < ALPHA else ND, "null_mean": null_mean, "null_sd": null_sd,
            "mean_H": [sum(x["H"][j] for x in per) / N_REC for j in range(KMAX + 1)],
            "per_recording": per}


def toy_result(over=None):
    """Default: every prediction true. over maps "whale", "wneg", ("en", r), ("enneg", r),
    ("unc", i) or ("col", i) to mk_test keyword overrides (g, k)."""
    over = over or {}

    def o(key, **kw):
        kw.update(over.get(key, {}))
        return kw

    whale = {"status": "ok", "years": list(YEARS), "gate_a": {"pass": True, "reasons": []},
             "data_sha256": WHALE_DATA_SHA256, "elements": list(WHALE_ELEMENTS),
             "elements_collapsed": list(WHALE_COLLAPSED),
             "real": mk_test(B_WHALE, SEED + 1, symbols=WHALE_COLLAPSED, bouts=WHALE_BOUTS,
                             **o("whale", g=0.01, k=0)),
             "neg": mk_test(B_NEG, SEED + 3, symbols=WHALE_COLLAPSED, bouts=WHALE_BOUTS,
                            **o("wneg", g=-0.05, k=100))}
    eng = []
    for r in range(N_EN):
        s = SEED + 10000 * (r + 1)
        ph = [c + 5 for c in WHALE_COLLAPSED]
        pc = [c + 2 for c in WHALE_COLLAPSED]
        eng.append({"rep": r, "start_utt": r * EN_STRIDE, "status": "ok",
                    "end_utt": r * EN_STRIDE + 1000, "phonemes": ph, "phonemes_collapsed": pc,
                    "real": mk_test(B_EN, s, symbols=pc, bouts=[20] * N_REC,
                                    **o(("en", r), g=0.02, k=0)),
                    "neg": mk_test(B_EN, s + 2, symbols=pc, bouts=[20] * N_REC,
                                   **o(("enneg", r), g=-0.05, k=50)),
                    "seconds_since_start": 1.0})
    rp = []
    for i in range(N_REP):
        s = SEED + 100 * (i + 1)
        eb = list(WHALE_COLLAPSED)
        ei = [4 * c for c in eb]
        ec = list(eb)
        rp.append({"i": i, "seed": s, "elements_base": eb, "elements_inflated": ei,
                   "elements_collapsed": ec,
                   "share_removed": sum(1.0 - c / a for a, c in zip(ei, ec)) / N_REC,
                   "bouts_recovered": 0.9,
                   "uncollapsed": mk_test(B_REP, s + 2, symbols=ei, bouts=WHALE_BOUTS,
                                          **o(("unc", i), g=0.03, k=0)),
                   "collapsed": mk_test(B_REP, s + 3, symbols=ec, bouts=WHALE_BOUTS,
                                        **o(("col", i), g=-0.05, k=100)),
                   "seconds_since_start": 2.0})
    cs = dict(PINNED)
    cs["holdc.py"] = "bb"
    return {"version": VERSION, "status": "ok", "registration": {"found": True, "sha256": "aa"},
            "code_sha256": cs, "config": dict(EXPECTED_CONFIG), "whale": whale,
            "english": eng, "repetition": rp}


def job_grading(rg):
    return {k: rg[k] for k in ("rules", "predictions", "priors", "brier", "n_scored")}


class TestToy(unittest.TestCase):
    def test_regrade_all_true(self):
        r = toy_result()
        rg = regrade(r)
        self.assertEqual(rg["rules"], {"R1_whale_after_collapse": R1_BEYOND,
                                       "R2_repetition_alone": FOOLS, "control": "CONTROL_OK",
                                       "english_detected": 5, "english_negative_detected": 0,
                                       "repetition_uncollapsed_detected": 3,
                                       "repetition_collapsed_detected": 0,
                                       "whale_negative_detected": False})
        self.assertEqual([rg["predictions"][k] for k in ORDER], [True] * 7)
        # .2025 + .0225 + .0225 + .0225 + .04 + .0625 + .25 = .6225
        self.assertAlmostEqual(rg["brier"], 0.6225 / 7, places=12)
        self.assertEqual(rg["n_scored"], 7)
        self.assertEqual(check_result(r), [])
        self.assertEqual(check_meta(r, "aa", "bb"), ["no grading"])
        r["grading"] = job_grading(rg)
        self.assertEqual(check_meta(r, "aa", "bb"), [])
        self.assertEqual(check_meta(r, "cc", "bb"),
                         ["registration sha256 differs from HOLDC-PREREG.md"])
        self.assertEqual(check_meta(r, "aa", "cc"),
                         ["holdc.py sha256 differs from the published holdc.py"])
        r2 = copy.deepcopy(r)
        r2["code_sha256"]["hold.py"] = "x"
        r2["config"]["q"] = 0.3
        self.assertEqual(check_meta(r2, "aa", "bb"), ["hold.py sha256", "config"])
        self.assertEqual(compare_grading(json.loads(json.dumps(r["grading"])), rg), [])
        g = json.loads(json.dumps(r["grading"]))
        g["rules"]["R1_whale_after_collapse"] = R1_NOT
        g["brier"] = 0.2
        self.assertEqual(compare_grading(g, rg), ["rules", "brier"])

    def test_not_detected_with_power(self):
        # whale p = 301/1001 = 0.3007, mean gain -0.02
        r = toy_result({"whale": {"g": -0.02, "k": 300}})
        rg = regrade(r)
        self.assertEqual(rg["rules"]["R1_whale_after_collapse"], R1_NOT)
        self.assertEqual(rg["rules"]["control"], "CONTROL_OK")
        self.assertFalse(rg["predictions"]["Q1"])
        self.assertFalse(rg["predictions"]["Q7"])
        # Q1 false costs .55^2 = .3025 instead of .2025; Q7 costs .25 either way
        self.assertAlmostEqual(rg["brier"], 0.7225 / 7, places=12)
        self.assertEqual(check_result(r), [])

    def test_controls(self):
        # English detected in 3 of 5 (replicates 3 and 4 at p = 51/101)
        rg = regrade(toy_result({("en", 3): {"k": 50}, ("en", 4): {"k": 50}}))
        self.assertEqual(rg["rules"]["english_detected"], 3)
        self.assertEqual(rg["rules"]["control"], "CONTROL_FAILED")
        self.assertEqual(rg["rules"]["R1_whale_after_collapse"], "CONTROL_FAILED")
        self.assertFalse(rg["predictions"]["Q2"])
        # two English negative controls detected -> failed; one is allowed
        rg = regrade(toy_result({("enneg", 0): {"k": 0}, ("enneg", 1): {"k": 0}}))
        self.assertEqual(rg["rules"]["english_negative_detected"], 2)
        self.assertEqual(rg["rules"]["control"], "CONTROL_FAILED")
        self.assertFalse(rg["predictions"]["Q3"])
        rg = regrade(toy_result({("enneg", 0): {"k": 0}}))
        self.assertEqual(rg["rules"]["control"], "CONTROL_OK")
        self.assertTrue(rg["predictions"]["Q3"])
        # collapsed repetition-only song detected in 1 of 3 -> still OK, but Q6 false
        rg = regrade(toy_result({("col", 0): {"k": 0}}))
        self.assertEqual(rg["rules"]["control"], "CONTROL_OK")
        self.assertEqual(rg["rules"]["R1_whale_after_collapse"], R1_BEYOND)
        self.assertFalse(rg["predictions"]["Q6"])
        rg = regrade(toy_result({("col", 0): {"k": 0}, ("col", 2): {"k": 0}}))
        self.assertEqual(rg["rules"]["repetition_collapsed_detected"], 2)
        self.assertEqual(rg["rules"]["control"], "CONTROL_FAILED")
        # whale negative control detected
        rg = regrade(toy_result({"wneg": {"k": 0}}))
        self.assertIs(rg["rules"]["whale_negative_detected"], True)
        self.assertEqual(rg["rules"]["control"], "CONTROL_FAILED")
        self.assertFalse(rg["predictions"]["Q4"])
        # uncollapsed repetition-only song detected in only 1 of 3
        rg = regrade(toy_result({("unc", 1): {"k": 100}, ("unc", 2): {"k": 100}}))
        self.assertEqual(rg["rules"]["R2_repetition_alone"], NOT_FOOLS)
        self.assertEqual(rg["rules"]["control"], "CONTROL_OK")
        self.assertFalse(rg["predictions"]["Q5"])

    def test_incomplete_and_missing(self):
        r = toy_result()
        r["english"][4] = {"rep": 4, "start_utt": 4 * EN_STRIDE, "status": "corpus_exhausted"}
        rg = regrade(r)
        self.assertEqual(rg["rules"]["control"], "CALIBRATION_INCOMPLETE")
        self.assertEqual(rg["rules"]["R1_whale_after_collapse"], "CALIBRATION_INCOMPLETE")
        self.assertIsNone(rg["predictions"]["Q2"])
        self.assertIsNone(rg["predictions"]["Q3"])
        self.assertEqual(rg["n_scored"], 5)
        # .2025 + .0225 + .04 + .0625 + .25 = .5775
        self.assertAlmostEqual(rg["brier"], 0.5775 / 5, places=12)
        self.assertEqual(check_result(r), [])
        r["grading"] = job_grading(rg)
        self.assertEqual(check_meta(r, "aa", "bb"), [])        # the job counts rows
        self.assertIn("| 4 | 7,400 | `corpus_exhausted` |", render_md_lines(r, rg))
        r["repetition"].pop()
        self.assertEqual(check_meta(r, "aa", "bb"), ["status ok but a part did not run"])
        self.assertEqual(regrade(r)["rules"]["R2_repetition_alone"], "INCOMPLETE")
        r["status"] = "timeout_partial"
        self.assertEqual(check_meta(r, "aa", "bb"), [])
        # whale missing: the job runs neither English nor the repetition-only song
        r = toy_result()
        r["whale"] = {"status": "missing"}
        r["english"] = []
        r["repetition"] = []
        rg = regrade(r)
        self.assertEqual(rg["rules"], {"R1_whale_after_collapse": MISSING,
                                       "R2_repetition_alone": "INCOMPLETE",
                                       "control": "CALIBRATION_INCOMPLETE",
                                       "english_detected": 0, "english_negative_detected": 0,
                                       "repetition_uncollapsed_detected": 0,
                                       "repetition_collapsed_detected": 0,
                                       "whale_negative_detected": None})
        self.assertEqual(rg["n_scored"], 0)
        self.assertIsNone(rg["brier"])
        self.assertEqual(check_result(r), [])
        r["english"] = toy_result()["english"]
        self.assertIn("controls without whale data", check_result(r))

    def test_consistency_catches_errors(self):
        r = toy_result()
        w = r["whale"]
        w["real"]["per_recording"][0]["p"] = 0.03              # 0.03 * 1001 - 1 = 29.03
        w["real"]["label"] = ND
        r["english"][1]["start_utt"] = 5
        r["repetition"][2]["share_removed"] = 0.7
        w["elements_collapsed"][3] = 909
        w["real"]["per_recording"][2]["bouts"] = 1
        r["repetition"][0]["uncollapsed"]["seed"] = 1
        bad = check_result(r)
        want = ["whale real: p, recording 0", "whale real: label",
                "english 1: start utterance", "repetition 2: share removed",
                "whale: collapsed sizes differ from RUNS",
                "whale real: fewer than 2 bouts, recording 2", "whale real: bouts, recording 2",
                "repetition 0 uncollapsed: seed"]
        self.assertEqual(sorted(bad), sorted(want))
        # a nan gain (a single-bout recording in hold.py) is caught on its own
        r = toy_result()
        r["whale"]["real"]["per_recording"][0]["gain"] = float("nan")
        self.assertEqual(check_result(r),
                         ["whale real: non-finite or missing H or gain, recording 0"])
        # sizes and symbols
        r = toy_result()
        r["english"][0]["phonemes"][0] = 240      # below 248, and below its collapse (250)
        r["repetition"][1]["collapsed"]["per_recording"][5]["symbols"] = 1
        r["whale"]["neg"]["per_recording"][7]["symbols"] = 4404
        self.assertEqual(sorted(check_result(r)), sorted([
            "english 0: recording smaller than the collapsed whale year",
            "english 0: collapsed sizes",
            "repetition 1 collapsed: symbols, recording 5",
            "whale negative: symbols above the real data, recording 7"]))

    def test_helpers(self):
        self.assertTrue(p_ok(1 / 1001, 1000))
        self.assertTrue(p_ok(51 / 101, 100))
        self.assertFalse(p_ok(0.03, 1000))
        self.assertFalse(p_ok(1.5, 100))
        self.assertTrue(close(None, None))
        self.assertFalse(close(None, 1.0))
        self.assertTrue(close(float("nan"), float("nan")))
        self.assertEqual(argmin([3.0, 2.5, 2.0, 1.99, 2.1, 2.2]), 3)
        self.assertEqual(argmin([3.0, 2.5, 2.0, 2.0, 2.1, 2.2]), 2)
        self.assertFalse(finite(float("nan")))
        self.assertFalse(finite(True))
        self.assertTrue(finite(0))

    def test_formats(self):
        r = toy_result()
        w = r["whale"]
        self.assertEqual(whale_line(w),
                         "Whale, repeats collapsed: mean held-out gain **+0.0100** bits per "
                         "element against -0.0500 (sd 0.0040) for collapse-consistent "
                         "second-order surrogates (B = 1,000), p = **0.0010**, label **`"
                         + BSO + "`**")
        self.assertEqual(neg_line(w),
                         "Whale negative control (one collapse-consistent second-order "
                         "surrogate): mean gain -0.0500 against -0.0500 (B = 200), p = 0.5025, "
                         "label `NOT_DETECTED`")
        self.assertEqual(entropy_line(w),
                         "Whale, repeats collapsed, mean held-out cross-entropy by context order "
                         "0 to 5 (bits per element): 3.0000, 2.5000, 2.0000, 1.9900, 2.1000, "
                         "2.2000")
        self.assertEqual(year_row(w, 0),
                         "| 2010 | 1,053 | 248 | 4 | 2.0000 | 1.9900 | +0.0100 | 0.0010 |")
        self.assertEqual(year_row(w, 5),
                         "| 2015 | 14,429 | 2,926 | 13 | 2.0000 | 1.9900 | +0.0100 | 0.0010 |")
        self.assertEqual(en_row(r["english"][0]),
                         "| 0 | 0 | 1,000 | 16,711 | 16,687 | +0.0200 | 0.0099 | `" + BSO +
                         "` | -0.0500 | 0.5050 | `NOT_DETECTED` |")
        self.assertEqual(en_row(r["english"][1])[:22], "| 1 | 1,850 | 2,850 | ")
        self.assertEqual(rep_row(r["repetition"][0]),
                         "| 0 | 16,671 | 66,684 | 16,671 | 0.7500 | 0.9000 | +0.0300 | 0.0050 | `"
                         + BSO + "` | -0.0500 | 0.5025 | `NOT_DETECTED` |")
        self.assertEqual(pred_end("Q1", True), "| 0.55 | **true** |")
        self.assertEqual(pred_end("Q7", None), "| 0.50 | **not graded** |")

    def test_md_check(self):
        r = toy_result()
        rg = regrade(r)
        lines = render_md_lines(r, rg)
        self.assertIn("Job status: `ok`; whale data status: `ok`", lines)
        self.assertIn("Control: **`CONTROL_OK`** (English detected in 5 of 5 replicates, its "
                      "negative controls in 0; whale negative control detected: no; collapsed "
                      "repetition-only song detected in 0 of 3)", lines)
        self.assertIn("R1 whale after collapsing repeats: **`" + R1_BEYOND + "`**", lines)
        self.assertIn("R2 repetition alone: **`" + FOOLS + "`** (HOLD as registered detected "
                      "the uncollapsed repetition-only song in 3 of 3 data sets)", lines)
        self.assertIn("7 of 7 graded predictions true", lines)
        self.assertIn("Brier score **0.089**", lines)
        self.assertIn("| Q6 | the collapsed repetition-only song is detected in none of 3 | "
                      "0.75 | **true** |", lines)
        # 1 status + 3 whale lines + 8 years + 5 English + 3 repetition + 3 rules
        # + 2 score lines + 7 predictions
        self.assertEqual(len(lines), 32)
        md = "\n".join(lines)
        self.assertEqual(check_md(md, r, rg), [])
        r1 = "R1 whale after collapsing repeats: **`" + R1_BEYOND + "`**"
        no_r1 = "\n".join(ln for ln in lines if ln != r1)
        self.assertEqual(check_md(no_r1, r, rg), [r1])
        no_q6 = "\n".join(ln for ln in lines if not ln.startswith("| Q6 |"))
        self.assertEqual(check_md(no_q6, r, rg), ["prediction row Q6"])
        # whale missing (so no English and no repetition-only song): 12 lines
        r["whale"] = {"status": "missing"}
        r["english"] = []
        r["repetition"] = []
        rg = regrade(r)
        lines = render_md_lines(r, rg)
        self.assertEqual(len(lines), 12)
        self.assertIn("Job status: `ok`; whale data status: `missing`", lines)
        self.assertIn("Control: **`CALIBRATION_INCOMPLETE`** (English detected in 0 of 0 "
                      "replicates, its negative controls in 0; whale negative control detected: "
                      "not run; collapsed repetition-only song detected in 0 of 0)", lines)
        self.assertIn("0 of 0 graded predictions true", lines)
        self.assertIn("| Q1 | the collapsed whale song is detected (p < 0.05) | 0.55 | "
                      "**not graded** |", lines)


if __name__ == "__main__":
    unittest.main()
