# SPDX-License-Identifier: Apache-2.0
# Stage 2 of song-zipf-test (finch): run only if the pre-registered OCR gate
# passed (PREREG-AMENDMENT-1.md section 4). Computes the published statistic
# and every null of PREREG.md, the decision label, and a machine grading of
# the finch predictions (hand-checked afterwards in RESULTS-FINCH.md).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import json
import os
import time

import zipfseg as z

PUBLISHED = {"mean_r2": {"0.3": 0.75, "0.5": 0.89, "0.7": 0.90},
             "z_0.5": {"shuffle": 17.05, "bigram_within": 6.77, "rotate": 15.69},
             "z_0.7_bigram": 1.87}


def load_recordings(parsed):
    recs = {}
    for r in parsed["rows"]:
        recs.setdefault((r["bird"], r["day"]), []).append(list("".join(r["words"])))
    keys = sorted(recs)
    return keys, [recs[k] for k in keys]


def grade(main, sens):
    r5 = main["by_theta"]["0.5"]
    n = r5["nulls"]
    d1 = main["heldout_ll_order2_minus_order1"]["n_favour_order2"]
    g = {
        "S-F": abs(r5["real_mean_r2"] - 0.89) <= 0.03,
        "F1": n["bigram_within"]["p"] < 0.05,
        "F2": n["markov1_pooled"]["p"] < 0.05,
        "F3": n["trigram_within"]["p"] < 0.05,
        "F4": n["markov2_pooled"]["p"] < 0.05,
        "F5": n["markov2_pooled"]["null_mean"] >= 0.80,
        "F6": d1 >= 20,
    }
    label = z.decision(r5) if g["S-F"] else "REPRODUCTION_FAILED"
    if label == "EXPLAINED_BY_SECOND_ORDER" and not g["F6"]:
        label += " (overfit caveat)"
    robust = {th: z.decision(main["by_theta"][th]) for th in main["by_theta"]}
    robust.update({k: z.decision(v["by_theta"]["0.5"]) for k, v in sens.items()})
    return g, label, robust


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default="/out")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--B", type=int, default=1000)
    ap.add_argument("--B-sens", type=int, default=200)
    a = ap.parse_args()
    val = json.load(open(os.path.join(a.in_dir, "validation.json"), encoding="utf-8"))
    gate = val["gate"]
    out_path = os.path.join(a.out_dir, "results_finch.json")
    if gate == "FAIL":
        json.dump({"status": "not_run", "gate": gate, "best_config": val["best_config"]},
                  open(out_path, "w", encoding="utf-8"), indent=1)
        print("GATE FAIL: analysis not run (see validation.json)")
        return
    parsed = json.load(open(os.path.join(a.in_dir, "finch_parsed.json"), encoding="utf-8"))
    keys, recs = load_recordings(parsed)
    t0 = time.time()
    main_res = z.analyze(recs, thetas=(0.3, 0.5, 0.7), B=a.B)
    print("main done in %.0f s" % (time.time() - t0), flush=True)
    sub = ("bigram_within", "markov1_pooled", "markov2_pooled")
    sens = {
        "rule_prev_over_cur": z.analyze(recs, thetas=(0.5,), B=a.B_sens, nulls=sub,
                                        rule="prev_over_cur", rotation=False, heldout=False),
        "tp_denominator_followed": z.analyze(recs, thetas=(0.5,), B=a.B_sens, nulls=sub,
                                             denominator="followed", rotation=False,
                                             heldout=False),
    }
    print("sensitivity done in %.0f s" % (time.time() - t0), flush=True)
    per_rec = []
    for k, r in zip(keys, recs):
        inv = z.segment_recording(r, 0.5)
        per_rec.append({"bird": k[0], "day": k[1], "bouts": len(r),
                        "syllables": sum(len(b) for b in r), "types_0.5": len(inv),
                        "r2_0.5": z.zipf_r2(inv.values()),
                        "slope_0.5": z.zipf_slope(inv.values())})
    g, label, robust = grade(main_res, sens)
    res = {"status": "ok", "gate": gate, "best_config": val["best_config"],
           "recordings": ["%s %d" % k for k in keys], "main": main_res,
           "sensitivity": sens, "per_recording": per_rec, "published": PUBLISHED,
           "machine_grades": g, "decision_0.5": label, "labels_robustness": robust,
           "provisional": gate != "PASS_EXACT", "seconds": time.time() - t0}
    json.dump(res, open(out_path, "w", encoding="utf-8"), indent=1)
    print(json.dumps({"decision_0.5": label, "grades": g, "robustness": robust,
                      "real_0.5": main_res["by_theta"]["0.5"]["real_mean_r2"],
                      "p": {k: v["p"] for k, v in main_res["by_theta"]["0.5"]["nulls"].items()},
                      "z": {k: v["z"] for k, v in main_res["by_theta"]["0.5"]["nulls"].items()}},
                     indent=1))


if __name__ == "__main__":
    main()
