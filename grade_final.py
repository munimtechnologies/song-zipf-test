# SPDX-License-Identifier: Apache-2.0
# grade_final.py: the final, mechanical reading of the finch result of song-zipf-test.
#
# Written and published 2026-11-17 (about 16:30 UTC), BEFORE any finch result or any
# calibration result existed. It combines, exactly as registered:
#   * PREREG.md section 5: S-F, F1-F6 and the decision label at theta 0.5;
#   * PREREG.md section 5: a label is "robust" only if the same label holds at 0.3 and 0.7;
#   * PREREG-AMENDMENT-1.md: prediction R1 (our z against shuffle, bigram_within and
#     rotate each within 25% of the published 17.05, 6.77, 15.69), PASS_APPROX = provisional,
#     and the hand check of >= 20 rows before anything is graded in RESULTS-FINCH.md;
#   * PREREG-AMENDMENT-2.md: rules R1 (size caveat), R2 (low power -> NOT_DISTINGUISHABLE)
#     and R3 (published controls), read from calib.py's calib_results.json.
# Inputs: results_finch.json (job_analyze.py) and, if it exists, calib_results.json.
# Output: final_grades.json and FINAL-LABEL.md. No new statistic is computed here.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import json
import math
import os

ALPHA = 0.05
PUBLISHED_R2_05 = 0.89
PUBLISHED_Z = {"shuffle": 17.05, "bigram_within": 6.77, "rotate": 15.69}


def decision(row, alpha=ALPHA):
    """PREREG section 5 label (identical to zipfseg.decision)."""
    p1 = row["nulls"]["markov1_pooled"]["p"]
    p2 = row["nulls"]["markov2_pooled"]["p"]
    if p2 < alpha:
        return "BEYOND_SECOND_ORDER"
    if p1 < alpha:
        return "EXPLAINED_BY_SECOND_ORDER"
    return "EXPLAINED_BY_FIRST_ORDER"


def _finite(x):
    return isinstance(x, (int, float)) and x == x and not math.isinf(x)


def prereg_grades(main):
    """S-F, F1-F6 (PREREG) and A1-R1 (AMENDMENT-1), recomputed from the raw output."""
    r5 = main["by_theta"]["0.5"]
    n = r5["nulls"]
    d1 = main["heldout_ll_order2_minus_order1"]["n_favour_order2"]
    real = r5["real_mean_r2"]
    g = {
        "S-F": _finite(real) and abs(real - PUBLISHED_R2_05) <= 0.03,
        "F1": n["bigram_within"]["p"] < ALPHA,
        "F2": n["markov1_pooled"]["p"] < ALPHA,
        "F3": n["trigram_within"]["p"] < ALPHA,
        "F4": n["markov2_pooled"]["p"] < ALPHA,
        "F5": _finite(n["markov2_pooled"]["null_mean"]) and n["markov2_pooled"]["null_mean"] >= 0.80,
        "F6": d1 >= 20,
    }
    zs = {k: n[k]["z"] for k in PUBLISHED_Z}
    g["A1-R1"] = all(_finite(zs[k]) and abs(zs[k] - v) <= 0.25 * v
                     for k, v in PUBLISHED_Z.items())
    return g, zs


def calibration_rules(calib):
    """AMENDMENT-2 rules from calib_results.json; None = not measured."""
    if calib is None:
        return {"status": "missing", "A2-R1": None, "A2-R2": None, "A2-R3": None,
                "n_skipped": None}
    r = calib["grading"]["rules"]
    skipped = calib.get("n_skipped", 0) or 0
    return {"status": "complete" if skipped == 0 else "partial",
            "A2-R1": r.get("R1_size_caveat_on_beyond_second_order"),
            "A2-R2": r.get("R2_low_power_relabel_explained_as_not_distinguishable"),
            "A2-R3": r.get("R3_published_controls_do_not_separate_words_from_first_order_rules"),
            "n_skipped": skipped}


def final_label(finch, calib=None):
    cal = calibration_rules(calib)
    out = {"calibration": cal, "hand_check_required": True}
    if finch is None or finch.get("status") != "ok":
        out.update({"label": "NOT_RUN", "headline": False,
                    "gate": None if finch is None else finch.get("gate"),
                    "caveats": ["analysis not run (OCR gate failed or no result)"]})
        return out
    main = finch["main"]
    g, zs = prereg_grades(main)
    by = main["by_theta"]
    base = decision(by["0.5"]) if g["S-F"] else "REPRODUCTION_FAILED"
    label = base
    headline = base != "REPRODUCTION_FAILED"
    caveats = []
    if base == "EXPLAINED_BY_SECOND_ORDER" and not g["F6"]:
        caveats.append("overfit caveat: order 2 does not generalise better in >= 20 of 30 "
                       "recordings (D1)")
    if base == "BEYOND_SECOND_ORDER":
        if cal["A2-R1"] is None:
            headline = False
            caveats.append("pending calibration: the size of the second-order null is not "
                           "yet measured (AMENDMENT-2 C4)")
        elif cal["A2-R1"]:
            headline = False
            caveats.append("size caveat (AMENDMENT-2 R1): the second-order null rejects true "
                           "second-order song too often; not a headline")
    if base.startswith("EXPLAINED_BY"):
        if cal["A2-R2"] is None:
            headline = False
            caveats.append("pending calibration: the power against word-like song is not yet "
                           "measured (AMENDMENT-2 C5)")
        elif cal["A2-R2"]:
            label = "NOT_DISTINGUISHABLE"
            caveats.append("low power (AMENDMENT-2 R2): the test cannot tell word-like song "
                           "from syllable rules at this data size; reported as "
                           "NOT_DISTINGUISHABLE, never as 'reduces to syllable rules'")
    if cal["status"] == "partial":
        caveats.append("calibration partial: %d replicate(s) skipped by the time limit"
                       % cal["n_skipped"])
    thetas = {th: decision(by[th]) for th in ("0.3", "0.5", "0.7") if th in by}
    robust = (base != "REPRODUCTION_FAILED" and len(thetas) == 3
              and len(set(thetas.values())) == 1)
    provisional = finch.get("gate") != "PASS_EXACT"
    if provisional:
        caveats.append("provisional: OCR gate was %s, not PASS_EXACT" % finch.get("gate"))
    mismatch = []
    mg = finch.get("machine_grades") or {}
    for k in ("S-F", "F1", "F2", "F3", "F4", "F5", "F6"):
        if k in mg and bool(mg[k]) != bool(g[k]):
            mismatch.append(k)
    if mismatch:
        caveats.append("job's own machine grades differ on %s: check by hand" % ", ".join(mismatch))
    out.update({"label": label, "base_label": base, "headline": headline,
                "robust": robust, "labels_by_theta": thetas, "provisional": provisional,
                "gate": finch.get("gate"), "grades": g, "z_0.5": zs,
                "published_z": PUBLISHED_Z, "real_mean_r2_0.5": by["0.5"]["real_mean_r2"],
                "grade_mismatch_with_job": mismatch, "caveats": caveats})
    return out


def _fmt(v):
    if v is None:
        return "not measured"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return "%.3f" % v if v == v else "nan"
    return str(v)


def render_md(res):
    lines = ["# FINAL-LABEL (machine reading; see RESULTS-FINCH.md for the hand-checked grading)",
             "",
             "Produced by grade_final.py, which was published before any result existed.",
             "",
             "| item | value |", "|---|---|",
             "| label (theta 0.5) | **%s** |" % res["label"],
             "| headline allowed | %s |" % _fmt(res["headline"])]
    if res["label"] != "NOT_RUN":
        lines += ["| base label before calibration rules | %s |" % res["base_label"],
                  "| robust (same label at 0.3 and 0.7) | %s |" % _fmt(res["robust"]),
                  "| OCR gate | %s |" % res["gate"],
                  "| real mean R^2 at 0.5 (published 0.89) | %s |" % _fmt(res["real_mean_r2_0.5"])]
        for k in ("S-F", "F1", "F2", "F3", "F4", "F5", "F6", "A1-R1"):
            lines.append("| %s | %s |" % (k, _fmt(res["grades"][k])))
        for k, v in res["z_0.5"].items():
            lines.append("| z vs %s (published %.2f) | %s |" % (k, PUBLISHED_Z[k], _fmt(v)))
    cal = res["calibration"]
    lines += ["| calibration | %s |" % cal["status"],
              "| AMENDMENT-2 R1 (size caveat applies) | %s |" % _fmt(cal["A2-R1"]),
              "| AMENDMENT-2 R2 (low power applies) | %s |" % _fmt(cal["A2-R2"]),
              "| AMENDMENT-2 R3 (published controls cannot separate words from first-order "
              "rules) | %s |" % _fmt(cal["A2-R3"]),
              ""]
    if res.get("caveats"):
        lines.append("Caveats:")
        lines += ["* " + c for c in res["caveats"]]
        lines.append("")
    lines.append("At least 20 random rows must be checked by eye against the page images "
                 "before any prediction is graded in RESULTS-FINCH.md (AMENDMENT-1).")
    return "\n".join(lines) + "\n"


def _load(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--finch", required=True, help="results_finch.json")
    ap.add_argument("--calib", default=None, help="calib_results.json (optional)")
    ap.add_argument("--out-dir", default=".")
    a = ap.parse_args(argv)
    res = final_label(_load(a.finch), _load(a.calib))
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "final_grades.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(a.out_dir, "FINAL-LABEL.md"), "w", encoding="utf-8") as f:
        f.write(render_md(res))
    print(json.dumps({"label": res["label"], "headline": res["headline"],
                      "caveats": res.get("caveats", [])}, indent=1))
    return res


if __name__ == "__main__":
    main()
