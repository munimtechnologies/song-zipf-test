# song-zipf-test

A pre-registered test by MV2 of Munim, Inc. of a widely reported claim: that humpback whale
song (Arnon et al. 2025, *Science*) and Bengalese finch song (Kirby et al. 2026, *Science
Advances*) contain "language-like" units whose frequencies follow Zipf's law.

**Question.** Both papers cut songs into chunks at dips in transitional probability and
find that the chunk frequencies look Zipfian. The finch paper shows that the effect beats a
first-order (bigram) null. Is it more than **second-order syllable rules**? We test the
published statistic against pooled first- and second-order Markov chains fitted to each
recording, and add a held-out check against overfitting.

## Status (2026-11-17)

* [PREREG.md](PREREG.md): hypotheses, nulls, priors and the decision rule, registered before any data.
* [PREREG-AMENDMENT-1.md](PREREG-AMENDMENT-1.md): the pipeline now follows the authors' own
  Code S1 exactly (TP denominator, R^2 edge cases, population-SD z, rotation null). The
  finch data are printed in the supplement only as page images, so they are read by OCR. A
  pre-registered gate checks the OCR against totals in the authors' printed output (299 bouts,
  19,990 transitions, 3,205 cuts, 1,043 subsequence types) and against their printed
  segmentation. If the gate fails, the analysis does not run.
* [PREREG-AMENDMENT-2.md](PREREG-AMENDMENT-2.md): a synthetic calibration, registered before
  any finch result was seen. Song is generated from Markov chains with no words, and from
  lexicons of word-like chunks, at the size of the finch data. It measures three things: how
  often our second-order null wrongly rejects real second-order song, how often it detects
  real words, and whether the published shuffle and rotation controls can tell words from
  plain syllable rules at all. The rules for reading the real-data labels in light of the
  calibration are fixed in advance.
* Jobs: finch OCR and analysis, queued; calibration (`calib.py`), queued; whale stage 0
  (unpacking the Science supplement, downloaded 2026-11-17), queued.

## Code

* `zipfseg.py`: segmentation, the Zipf R^2, and the null models (pure Python).
* `calib.py`: the synthetic calibration (Amendment 2).
* `finch_parse.py`: parses and validates the OCR'd finch dataset.
* `ocr_finch.py`: Stage 1, the OCR (Tesseract).
* `job_analyze.py`: Stage 2, the analysis, which runs only if the gate passed.
* `inventory.py`: Stage 0, which fetched the supplements.
* Tests: `python -m unittest -v test_zipfseg test_finch_parse test_calib`. One test checks
  our segmentation against a literal transcription of the authors' Code S1.

The "wow", whichever way it falls: either the Zipf structure in animal song reduces to
short-range transition rules, or it survives a much stronger control than any published one.

Raw data from the two papers are not redistributed here. The finch data are CC BY-NC, and
the whale data are released for reproducing or extending the Zipfian analysis.

Made with AI agents working in MV2's name. Code Apache-2.0; text CC BY 4.0.
Contact: MV2, Munim, Inc., mv2@munimtech.com
