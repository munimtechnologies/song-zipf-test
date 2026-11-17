# PREREG-AMENDMENT-1: follow the authors' Code S1, and read the finch data by OCR behind a pre-registered gate

Dated 2026-11-17 (about 14:30 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
Text CC BY 4.0; code Apache-2.0. Written **before any song sequence was seen**. No Zipf or
null-model statistic has been computed on any real data.

## 1. What has been seen since PREREG.md

Stage 0 (`inventory.py`, job `song-zipf-inventory-v1`, finished 2026-11-17 14:00 UTC) fetched:

* the finch paper's Europe PMC supplementary bundle (14,648,242 bytes). It contains
  `sciadv.aea3015_sm.pdf` (sha256 `1c917997...0895740`, 58 pages) and the figure images;
* the finch full-text XML. Its data statement says that all data are "present in the paper
  and/or the Supplementary Materials". No external repository is named;
* the whale paper's accepted manuscript (St Andrews, CC BY), whose text we read for methods.
  The Science supplement page returned HTTP 403 (a bot wall).

We read the **text layer** of the finch supplement. Pages 5-47 are a printout of Code S1 (a
Python notebook) with its outputs. Pages 49-58 hold the "Dataset" (one song bout per row:
bird, age in days, syllable letters, with spaces marking the authors' segmentation). **These
pages have no text layer.** Text extraction returned nothing for them, and we have not
viewed them as images. So no sequence data has been seen.

From the Code S1 printout we learned the following, all of which is published output:

* the six birds (Atama, LShiro, RAo, RKi, RMo, Shiro) and the age in days of each of their
  30 recordings (cell [95]);
* "cuts: 10.719063545150501" per bout at ratio 0.5 (cell [92]). That figure implies 299 bouts,
  3,205 cuts and 3,504 subsequences, since 0.719063545150501 x 299 = 215 exactly;
* 19,990 transitional probabilities in `all_TPs` (cell [111]). That implies 19,990 + 299 =
  20,289 syllables;
* 1,043 rows in `new_ranked_freq` (cell [110]), i.e. the number of distinct subsequences
  summed over the 30 recordings;
* mixed-model outputs on R^2, alpha and similarity by age. These are published results; we do not use them.

## 2. Pipeline changes to match Code S1 (PREREG section 3 said Code S1 wins)

| item | PREREG.md | Code S1 (now used) |
|---|---|---|
| TP denominator | n(a, any successor) | **n(a) over all occurrences, including bout-final ones** (`ngram_table(n-1)`) |
| cut rule | t_i / t_{i-1} < theta | **t_i < t_{i-1} x theta**, first transition never cuts. This is the same rule; the product form gives exactly the same floating-point results |
| R^2 per recording | nan if fewer than 3 types | **nan if fewer than 2 types or all frequencies equal** (scipy `pearsonr` under `warnings("error")`); 2 unequal types give 1 |
| statistic | mean of per-recording R^2 | same (confirmed: `mean_r2` over the 30 bird-day recordings) |
| z-score | sample SD | **population SD** (`np.std`) |
| published "bigram" null | our `bigram_within` | confirmed equivalent in distribution: per bout, a random start symbol, successors drawn from that bout's own observed successors with their multiplicity, and a random symbol of the bout at a dead end |
| rotation null | not implemented | **added** (`rotate_bout_segments`): each bout's segmented symbols are rotated by `randint(0, 100000) mod length` and cut again at the original subsequence lengths, with no re-segmentation |

The test `test_matches_code_s1_exactly` checks our segmentation against a literal
transcription of Code S1 on 30 random recordings at all three thresholds. The PDF text loses
Python indentation, and we read Code S1 so that the symbol after a cut starts the next
subsequence and `last_tp` is updated after every transition. Those are the only readings
under which the printed subsequences add up to the bout. The OCR validation below checks
this reading against the authors' printed spaces.

New pre-specified sensitivity checks at theta 0.5, with B = 200, against the bigram_within,
markov1_pooled and markov2_pooled nulls: (a) the reversed rule `prev_over_cur`; (b) the old TP
denominator (`followed`). They are reported and do not change the headline.

## 3. Getting the finch data: OCR with fixed settings

`ocr_finch.py` renders the caption page (48) and pages 49-58 in greyscale
and runs Tesseract under exactly four configurations: 400 or 600 dpi, crossed with page
segmentation mode 6 or 4. Every run turns the dictionaries off and allows only the
characters A-Z, a-z, 0-9 and space. `finch_parse.py` parses each OCR output as follows:

* A header is "name age letters...". The name is matched to one of the six birds (edit
  distance <= 2), and the pair must be one of the 30 recordings (name distance + differing age
  digits <= 3). The age token must contain at least one digit.
* Other lines are continuations of a wrapped row.
* Non-letters in a sequence are dropped and counted.

Each configuration is validated against the Code S1 totals in section 1, and against the
authors' printed spaces. For the second check, our Code S1 pipeline is run on the **unspaced**
letters at theta 0.5, and the cut positions it finds are compared with the printed ones.
Positions where a printed line wraps are excluded, since a wrap can hide or invent a space.
The configuration with the most exact matches is kept (ties broken by cut-agreement F1, then
by closeness to 20,289 syllables). The exact matches checked are: 30 recordings, 299 bouts,
19,990 transitions, 3,205 pipeline cuts, and 1,043 pipeline types.

## 4. The gate (decided now, applied by code)

* **PASS_EXACT**: all five exact matches.
* **PASS_APPROX**: all 30 recordings, bouts within 3 of 299, transitions within 100 of
  19,990, and cut-agreement F1 >= 0.95.
* **FAIL**: anything else. The analysis is not run. We then improve the OCR in a new job
  version, changing only OCR settings and the parser, never the analysis.

If the gate passes, `job_analyze.py` runs the PREREG analysis in the same job. That is
thresholds 0.3/0.5/0.7, B = 1000, all five nulls plus rotation, and D1. Results from
PASS_APPROX are **provisional**. In every case, before any prediction is graded in
`RESULTS-FINCH.md`, at least 20 randomly chosen rows are checked by eye against the page
images that the job saves. Any OCR error found is reported, together with its effect.

## 5. Predictions

All predictions and priors in PREREG.md section 5 are unchanged (S-F, F1-F6, S-W, W1-W6,
and the decision rule). One new prediction is added:

| id | prediction | prior |
|---|---|---|
| R1 | our z-scores at theta 0.5 against shuffle, bigram_within and rotate are each within 25% of the published 17.05, 6.77 and 15.69 | 55% |

## 6. Data use

The finch data are CC BY-NC. The OCR text and the parsed rows stay in the job's output folder
and are **not** committed to this repository. Only derived statistics are published. The whale
supplement will be fetched in a browser, as PREREG.md says. Until then the whale half of the
test is waiting on data.
