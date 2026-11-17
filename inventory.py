# SPDX-License-Identifier: Apache-2.0
# Stage 0 of song-zipf-test: fetch the published supplements and write an
# inventory (file names, sizes, sha256, extracted text). NO analysis is done
# here; the segmentation/Zipf analysis runs only in a later, separately filed
# job whose parser is written after this inventory (see PREREG.md section 6).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import hashlib
import io
import json
import os
import urllib.request
import zipfile

UA = "MV2-research/1.0 (Munim, Inc.; mv2@munimtech.com)"
SOURCES = {
    # Kirby et al. 2026 Sci. Adv. (CC BY-NC): Europe PMC supplementary bundle
    "finch_suppl.zip": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13450306/supplementaryFiles",
    "finch_fulltext.xml": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13450306/fullTextXML",
    # Arnon et al. 2025 Science, author accepted manuscript (CC BY), St Andrews
    "whale_aam.pdf": "https://research-repository.st-andrews.ac.uk/bitstream/10023/31372/1/Arnon_2024_Science_Whale-song-language_CCBY_AAM.pdf",
    # Science supplement landing page (expected to be bot-walled; status logged only)
    "whale_suppl_page.html": "https://www.science.org/doi/suppl/10.1126/science.adq7055",
}
TEXT_EXT = (".txt", ".csv", ".tsv", ".py", ".r", ".R", ".json", ".md", ".xml", ".ipynb")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, r.read()
    except Exception as e:  # record, never crash
        return getattr(e, "code", None) or repr(e), b""


def pdf_text(data):
    try:
        from pypdf import PdfReader
    except Exception as e:
        return "pypdf unavailable: %r" % (e,)
    try:
        rd = PdfReader(io.BytesIO(data))
        return "\n\n".join("=== page %d ===\n%s" % (i + 1, (p.extract_text() or ""))
                           for i, p in enumerate(rd.pages))
    except Exception as e:
        return "pdf text extraction failed: %r" % (e,)


def xlsx_to_csv(data, outdir, stem):
    try:
        import openpyxl
    except Exception:
        return []
    made = []
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    for ws in wb.worksheets:
        path = os.path.join(outdir, "%s__%s.csv" % (stem, "".join(c if c.isalnum() else "_" for c in ws.title)))
        with open(path, "w", encoding="utf-8") as f:
            for row in ws.iter_rows(values_only=True):
                f.write(",".join("" if v is None else str(v).replace(",", ";") for v in row) + "\n")
        made.append(os.path.basename(path))
    return made


def handle_file(name, data, textdir, inv):
    rec = {"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    low = name.lower()
    safe = name.replace("/", "__").replace("\\", "__")
    if low.endswith(".pdf"):
        t = pdf_text(data)
        with open(os.path.join(textdir, safe + ".txt"), "w", encoding="utf-8") as f:
            f.write(t)
        rec["text_chars"] = len(t)
    elif low.endswith(TEXT_EXT) and len(data) < 20_000_000:
        with open(os.path.join(textdir, safe), "wb") as f:
            f.write(data)
        rec["copied"] = True
    elif low.endswith((".xlsx", ".xlsm")):
        rec["csv"] = xlsx_to_csv(data, textdir, safe)
    inv.append(rec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    a = ap.parse_args()
    cache = os.path.join(a.data_dir, "song")
    textdir = os.path.join(a.out_dir, "text")
    os.makedirs(cache, exist_ok=True)
    os.makedirs(textdir, exist_ok=True)
    status, inv = {}, []
    for name, url in SOURCES.items():
        path = os.path.join(cache, name)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            data, st = open(path, "rb").read(), "cached"
        else:
            st, data = fetch(url)
            if data and st == 200:
                tmp = "%s.%d.part" % (path, os.getpid())
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, path)
        status[name] = {"url": url, "status": str(st), "bytes": len(data),
                        "head": data[:200].decode("latin-1", "replace") if data else ""}
        if not data or name.endswith(".html"):
            continue
        if zipfile.is_zipfile(io.BytesIO(data)):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                status[name]["members"] = zf.namelist()
                for m in zf.namelist():
                    if m.endswith("/"):
                        continue
                    handle_file(name + "/" + m, zf.read(m), textdir, inv)
        else:
            handle_file(name, data, textdir, inv)
    with open(os.path.join(a.out_dir, "inventory.json"), "w", encoding="utf-8") as f:
        json.dump({"sources": status, "files": inv}, f, indent=1)
    print(json.dumps(status, indent=1)[:4000])
    print("files:", len(inv))


if __name__ == "__main__":
    main()
