# Finch gate note 1 (2026-11-17): the OCR stage failed its registered gate

Made with AI agents working in MV2's name. MV2, Munim, Inc., mv2@munimtech.com.

Job `song-zipf-finch-v1` ran on 2026-11-17 (20:57-21:02 UTC). It reads the Bengalese finch
song dataset printed in the supplement of Kirby et al. 2026 (Science Advances, eaea3015) and
checks the reading against the totals in the authors' own Code S1 output before any analysis
is allowed. **The gate failed, so no Zipf or null-model statistic was computed** (the analysis
step stopped by design: "GATE FAIL: analysis not run").

## What went wrong

The supplement's dataset pages (PDF pages 49-58) have no text layer: every glyph is a vector
path (800-3,400 drawing objects per page, zero text characters). We rendered them and read
them with Tesseract under four registered configurations (400/600 dpi, page-segmentation
modes 4/6). The best configuration (400 dpi, mode 6):

| Quantity | Target (authors' Code S1) | Read |
|---|---|---|
| Recordings | 30 | 16 found |
| Bouts | 299 | 50 |
| Syllables | 20,289 | 21,403 |
| Printed chunk boundaries (spaces) | 3,205 | 559 |

Letters were read roughly right in number, but Tesseract dropped almost every printed space
(the spaces are the chunk boundaries the test depends on). It also split bird names that sit
beside two-line rows ("At" / "ama"), which merged bouts, and misread some day numbers (89 as
39). Gate PASS_EXACT and PASS_APPROX both need far better than this. The OCR text, page
renders and validation are kept on the job's output volume; the raw finch data are CC BY-NC
and are not redistributed here.

## What happens next

This is a reading failure, not a result about birds. As registered, only the reading step
may change. Because the glyphs are vector paths, they can be read from geometry rather than
OCR. Each glyph's outline is identical wherever the same letter appears, and a space is a
measurable gap between outlines. A diagnostic job (`song-zipf-glyph-probe-v1`) is checking how
the paths are drawn. A new reading step will then be validated against the same targets by
the same gate, with no change to any registered prediction, statistic or threshold, before
the finch analysis runs (`song-zipf-finch-v2`).

Code Apache-2.0; text CC BY 4.0.
