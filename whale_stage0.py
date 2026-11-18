# SPDX-License-Identifier: Apache-2.0
# song-zipf-test, whale stage 0 (v3): unpack the Science supplementary files of
# Arnon et al. 2025 (downloaded by hand into ../whale-download/), copy them into
# the job's persistent data volume (/data/song/whale/) so later analysis jobs
# can read them, and write an inventory (names, sizes, sha256, first lines, PDF
# text, spreadsheet previews). NO analysis is done here. Run as:
#   python -I code/whale_stage0.py --src whale-download
# v2: checks the three expected files and their SHA-256 (recorded at download time,
# 2026-11-17) and stops before writing anything if one is missing or different.
# v3: also previews .xlsx sheets (names, size, first rows) and keeps small text files whole.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import hashlib
import io
import json
import os
import sys
import zipfile

TEXT_EXT = (".txt", ".csv", ".tsv", ".py", ".r", ".json", ".md", ".ipynb", ".m")
EXPECTED = {
    "science.adq7055_sm.v2.pdf":
        "c79312a9882abd5d2beaa158883a2a96324ad5333216f93877bae28630a9ba7a",
    "science.adq7055_code_s1.v2.zip":
        "826c0da48de0b2419675f7c955e5fd5507e706df66271b18d5fc12db0b52a9f1",
    "science.adq7055_data_s1_to_s3.zip":
        "d4e5c50336e4dcd0b6f0d48c90a1c2a8b7507f3a4a48a1ad698417951fb4e1bd",
}


def pdf_text(data):
    try:
        from pypdf import PdfReader
        rd = PdfReader(io.BytesIO(data))
        return "\n\n".join("=== page %d ===\n%s" % (i + 1, p.extract_text() or "")
                           for i, p in enumerate(rd.pages))
    except Exception as e:
        return "pdf text extraction failed: %r" % (e,)


def xlsx_preview(data, n_rows=15):
    try:
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        out = []
        for ws in wb.worksheets:
            rows = []
            n = 0
            for r in ws.iter_rows(values_only=True):
                n += 1
                if len(rows) < n_rows:
                    rows.append(["" if v is None else str(v)[:200] for v in r][:30])
            out.append({"sheet": ws.title, "n_rows": n, "first_rows": rows})
        return out
    except Exception as e:
        return "xlsx preview failed: %r" % (e,)


def record(name, data, textdir):
    rec = {"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    low = name.lower()
    safe = name.replace("/", "__").replace("\\", "__")
    if low.endswith(".pdf"):
        t = pdf_text(data)
        with open(os.path.join(textdir, safe + ".txt"), "w", encoding="utf-8") as f:
            f.write(t)
        rec["text_chars"] = len(t)
    elif low.endswith((".xlsx", ".xlsm")):
        prev = xlsx_preview(data)
        rec["xlsx"] = prev
        with open(os.path.join(textdir, safe + ".preview.json"), "w", encoding="utf-8") as f:
            json.dump(prev, f, indent=1)
    elif low.endswith(TEXT_EXT):
        txt = data.decode("utf-8", "replace")
        rec["lines"] = txt.count("\n") + 1
        rec["head"] = [ln[:300] for ln in txt.splitlines()[:8]]
        if len(data) < 2_000_000:
            with open(os.path.join(textdir, safe), "wb") as f:
                f.write(data)
    return rec


def check_inputs(src):
    bad = []
    for fn, sha in EXPECTED.items():
        path = os.path.join(src, fn)
        if not os.path.isfile(path):
            bad.append("%s: missing" % fn)
            continue
        got = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if got != sha:
            bad.append("%s: sha256 %s, expected %s" % (fn, got, sha))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="whale-download")
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    a = ap.parse_args()
    bad = check_inputs(a.src)
    if bad:
        print("INPUTS NOT READY, nothing written:\n" + "\n".join(bad))
        sys.exit(3)
    dest = os.path.join(a.data_dir, "song", "whale")
    textdir = os.path.join(a.out_dir, "text")
    os.makedirs(dest, exist_ok=True)
    os.makedirs(textdir, exist_ok=True)
    inv = []
    for fn in sorted(os.listdir(a.src)):
        path = os.path.join(a.src, fn)
        if not os.path.isfile(path) or fn not in EXPECTED:
            continue
        data = open(path, "rb").read()
        tmp = os.path.join(dest, "%s.%d.part" % (fn, os.getpid()))
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, os.path.join(dest, fn))
        inv.append(record(fn, data, textdir))
        if zipfile.is_zipfile(io.BytesIO(data)):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for m in zf.namelist():
                    if m.endswith("/") or ".." in m or m.startswith("/"):
                        continue
                    if m.startswith("__MACOSX/") or os.path.basename(m).startswith("._"):
                        continue
                    md = zf.read(m)
                    target = os.path.join(dest, "unzipped", fn, m)
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    with open(target, "wb") as f:
                        f.write(md)
                    inv.append(record(fn + "/" + m, md, textdir))
    with open(os.path.join(a.out_dir, "whale_inventory.json"), "w", encoding="utf-8") as f:
        json.dump({"dest": dest, "files": inv}, f, indent=1)
    print(json.dumps(inv, indent=1)[:6000])


if __name__ == "__main__":
    main()
