# PREREG-AMENDMENT-4: read the finch dataset from its vector geometry (reading step only)

Dated 2026-11-18 (about 03:30 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI
agents. Text CC BY 4.0; code Apache-2.0. Written and published **before the new reader has
run on the real pages**. No Zipf or null-model statistic has been computed on any real finch
data.

## 1. Why

The first reading of the Bengalese finch dataset (Kirby et al. 2026, *Sci. Adv.* eaea3015,
supplement pages 49-58) used OCR and failed the registered gate (FINCH-GATE-NOTE-1.md).
Tesseract lost almost every printed space, so only 50 of 299 bouts were recovered. As
PREREG-AMENDMENT-1 section 4 requires, **only the reading step changes**. The gate, the
analysis (`job_analyze.py`, `zipfseg.py`), every prediction and every threshold stay as
published. The job fetches them from commit `742fd83` of this repository.

## 2. What has been seen since then

The diagnostic job `song-zipf-glyph-probe-v1` (`probe_glyphs.py`, 2026-11-18 02:55-03:01 UTC)
examined pages 49 and 50:

* every glyph is **one filled black vector path** (2,644 on page 49 and 2,534 on page 50),
  with no text layer;
* each table cell (bird, day, sequence) is a filled white or light-grey rectangle, so row
  bands and columns are explicit in the geometry. Each page is 612 x 7,920 pt;
* gaps between neighbouring glyph outlines fall into separate clusters: 0.25-1.75 pt inside
  words, 2.75-4.0 pt at printed spaces, and 9.5-11.5 pt between columns.

To check the bounding boxes, we looked by eye at one 400-dpi render of the top of page 49.
It shows the header and four Atama day-62 rows, partly cut off at the right edge. Nothing else
from the dataset has been seen, and no count, segmentation or statistic was computed from it.

## 3. The new reading step (`glyph_finch.py`, tested by `test_glyph_finch.py`)

1. **Glyphs.** On every page from the "Dataset" caption page onward, each black filled
   path smaller than 12 pt is a glyph. Glyphs are grouped into classes by their outline:
   the same item kinds, with every coordinate relative to the glyph's own bounding box
   agreeing within **0.08 pt**.
2. **Rows and columns.** Each light rectangle at least 300 pt wide (and 8-600 pt tall) is
   one row band. The bird and day cells are the rectangles to its left in the same band.
   A glyph belongs to the band and column that contain its centre. Lines inside a cell are
   split where glyph centres jump by more than 4 pt.
3. **Spaces.** A printed space is a gap of more than **2.25 pt** between neighbouring
   outlines on a line. A line wrap inside a cell ends a word, as in the OCR parser, and wrap
   positions stay excluded from the space-agreement check. A band with no bird or day glyphs
   continues the previous row (a row split across a page break).
4. **Which class is which character.**
   * Bird-cell class sequences are matched to the six known bird names (Atama, LShiro, RAo,
     RKi, RMo, Shiro). The match must make a consistent one-to-one class-letter map.
   * Day-cell digit classes are solved so that every (bird, day) is one of the 30
     registered recordings, again one-to-one.
   * The other sequence classes are labelled by single-character Tesseract (psm 10, a-z),
     with a fallback symbol when a label is missing or already taken.

   The labels change no count, segmentation or statistic. The pipeline only needs each
   syllable class to be distinct and consistent.
5. A row whose bird or day cannot be decoded, or whose (bird, day) is not registered, is
   dropped and counted.

The unit tests build synthetic vector pages in the printed format and check exact recovery
of birds, days, words, wraps, rows split across pages and repeated header bands. They also
check that the name and digit solutions are unique for the six birds and 30 recordings, and
that unknown letters still get consistent one-to-one labels.

## 4. Gate and analysis: unchanged

`finch_parse.validate` and `finch_parse.gate` are applied exactly as registered:
**PASS_EXACT** needs 30 recordings, 299 bouts, 19,990 transitions, 3,205 pipeline cuts and
1,043 pipeline types. **PASS_APPROX** needs all 30 recordings, bouts within 3 of 299,
transitions within 100 of 19,990, and cut-agreement F1 >= 0.95. Only if the gate passes does
`job_analyze.py` (unchanged) run the PREREG analysis in the same job (thresholds 0.3/0.5/0.7,
B = 1000, all nulls plus rotation, D1). PASS_APPROX results stay provisional.

Diagnostics, reported but never used to choose a reading: the gap histogram, gaps between
1.9 and 2.6 pt, classes that might be one letter split in two, and cut agreement with the
space threshold at 2.0 and 2.5 pt.

## 5. Hand check before grading (as in PREREG-AMENDMENT-1)

The job renders **24 rows** chosen with seed 20261118, each next to its reading
(`check/row_NN.png`, `check/check_rows.tsv`), plus a sheet of every glyph class with its
label (`class_sheet.png`). Before any finch prediction is graded in RESULTS-FINCH.md, every
one of the 24 rows is checked by eye: letters, spaces and wraps. Every disagreement is
reported with its effect.

## 6. Data use

Unchanged: the finch data are CC BY-NC. Parsed rows, renders and class sheets stay in the
job's output folder and are not committed. Only derived statistics are published.

Job: `song-zipf-finch-v2` (workdir `finch2/`: `glyph_finch.py`, `test_glyph_finch.py`,
`setup.sh`, which fetches the unchanged `zipfseg.py`, `finch_parse.py`, `job_analyze.py` and
`test_finch_parse.py` from commit `742fd83cb0386f6ce4868a35db46a5fd657393a0`).
