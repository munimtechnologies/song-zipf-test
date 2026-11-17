# SPDX-License-Identifier: Apache-2.0
# Stage 1 of song-zipf-test (PREREG-AMENDMENT-1.md): read the Kirby et al. 2026
# supplementary "Dataset" pages, which are printed without a text layer, by
# OCR (Tesseract) under several fixed configurations; parse every
# configuration, validate it against the totals in the authors' Code S1 output,
# keep the best-scoring one, and write the pre-registered gate. No Zipf or
# null-model statistic is computed here.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import hashlib
import io
import json
import os
import subprocess
import urllib.request
import zipfile

import finch_parse as fp

URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13450306/supplementaryFiles"
UA = "MV2-research/1.0 (Munim, Inc.; mv2@munimtech.com)"
SM = "sciadv.aea3015_sm.pdf"
SM_SHA256 = "1c91799782c41a812287deca4779eaf666cf0f82b812f281f503559310895740"
WHITELIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
CONFIGS = [(400, 6), (400, 4), (600, 6), (600, 4)]   # (dpi, tesseract page-segmentation mode)


def load_pdf(data_dir):
    path = os.path.join(data_dir, "song", "finch_suppl.zip")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        blob = open(path, "rb").read()
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=300) as r:
            blob = r.read()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = "%s.%d.part" % (path, os.getpid())
        with open(tmp, "wb") as f:
            f.write(blob)
        os.replace(tmp, path)
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        pdf = zf.read(SM)
    sha = hashlib.sha256(pdf).hexdigest()
    return pdf, sha


def dataset_pages(doc):
    """0-based index of the 'Dataset:' caption page, and the pages to OCR
    (the caption page itself, in case rows start below the caption, and
    every page after it)."""
    cap = None
    for i in range(doc.page_count):
        if "Dataset: The complete set of songs" in " ".join(doc[i].get_text("text").split()):
            cap = i
    if cap is None:
        raise SystemExit("Dataset caption page not found")
    return cap, list(range(cap, doc.page_count))


def ocr_png(png_path, psm):
    cmd = ["tesseract", png_path, "stdout", "--psm", str(psm),
           "-c", "load_system_dawg=0", "-c", "load_freq_dawg=0",
           "-c", "preserve_interword_spaces=1",
           "-c", "tessedit_char_whitelist=" + WHITELIST]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    return r.stdout, r.stderr[-500:]


def main():
    import fitz  # PyMuPDF, only needed here

    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    a = ap.parse_args()
    out = a.out_dir
    os.makedirs(os.path.join(out, "ocr"), exist_ok=True)
    os.makedirs(os.path.join(out, "pages"), exist_ok=True)
    tmpdir = "/tmp/song_render_%d" % os.getpid()
    os.makedirs(tmpdir, exist_ok=True)

    pdf, sha = load_pdf(a.data_dir)
    doc = fitz.open(stream=pdf, filetype="pdf")
    cap, pages = dataset_pages(doc)
    info = {"sm_sha256": sha, "sha_matches_inventory": sha == SM_SHA256,
            "caption_page": cap + 1, "dataset_pages": [p + 1 for p in pages], "pages": []}
    for p in pages:
        pg = doc[p]
        info["pages"].append({
            "page": p + 1, "width_pt": pg.rect.width, "height_pt": pg.rect.height,
            "images": [list(x[:5]) for x in pg.get_images(full=True)],
            "n_drawings": len(pg.get_drawings()),
            "text_chars": len(pg.get_text("text")),
        })
        # preview strips for visual hand-checking (grey, 250 dpi, 4 per page)
        h = pg.rect.height
        for k in range(4):
            clip = fitz.Rect(0, h * k / 4, pg.rect.width, h * (k + 1) / 4)
            pix = pg.get_pixmap(dpi=250, clip=clip, colorspace=fitz.csGRAY)
            pix.save(os.path.join(out, "pages", "p%02d_%d.png" % (p + 1, k + 1)))

    results = []
    for dpi, psm in CONFIGS:
        name = "dpi%d_psm%d" % (dpi, psm)
        lines = []
        errs = []
        for p in pages:
            png = os.path.join(tmpdir, "p%02d_%d.png" % (p + 1, dpi))
            if not os.path.exists(png):
                doc[p].get_pixmap(dpi=dpi, colorspace=fitz.csGRAY).save(png)
            txt, err = ocr_png(png, psm)
            with open(os.path.join(out, "ocr", "%s_p%02d.txt" % (name, p + 1)), "w",
                      encoding="utf-8") as f:
                f.write(txt)
            if err.strip():
                errs.append(err.strip())
            lines.extend(txt.splitlines())
        rows, st = fp.parse_lines(lines)
        v = fp.validate(rows)
        results.append({"config": name, "parse_stats": st, "validation": v,
                        "stderr_tail": errs[-3:], "rows": rows})
        print(name, "bouts", v["bouts"], "syll", v["syllables"], "cuts(printed)",
              v["printed_cuts"], "cuts(pipeline)", v["pipeline_cuts"], "types",
              v["pipeline_types"], "f1", round(v["cut_agreement"]["f1"], 4)
              if v["cut_agreement"]["f1"] == v["cut_agreement"]["f1"] else None,
              "exact", v["n_exact"], "gate", v["gate"], flush=True)

    best = max(results, key=lambda r: fp.score(r["validation"]))
    summary = {"info": info, "best_config": best["config"],
               "configs": [{k: r[k] for k in ("config", "parse_stats", "validation", "stderr_tail")}
                           for r in results],
               "gate": best["validation"]["gate"]}
    with open(os.path.join(out, "validation.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    # parsed rows of the best configuration (raw data stay on the job's /out,
    # they are CC BY-NC and are not redistributed in the repository)
    with open(os.path.join(out, "finch_parsed.json"), "w", encoding="utf-8") as f:
        json.dump({"config": best["config"], "rows": best["rows"]}, f)
    with open(os.path.join(out, "finch_parsed.tsv"), "w", encoding="utf-8") as f:
        for r in best["rows"]:
            f.write("%s\t%d\t%s\t%s\n" % (r["bird"], r["day"], " ".join(r["words"]),
                                          ",".join(map(str, r["wraps"]))))
    print("BEST", best["config"], "GATE", summary["gate"])


if __name__ == "__main__":
    main()
