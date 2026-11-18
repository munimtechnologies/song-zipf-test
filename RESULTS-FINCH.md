# RESULTS-FINCH: the Zipf structure of Bengalese finch song is matched by second-order syllable rules

Graded 2026-11-18 by MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in
his name. Text CC BY 4.0; code Apache-2.0. Re-derived by `test_finch_results.py`.

## Headline

Kirby, Okanoya, Garland, Takahasi & Arnon (2026, *Science Advances*, eaea3015) found that
chunks of Bengalese finch song, cut at dips in transitional probability, follow Zipf's
rank-frequency law (mean R^2 0.89), and that this beats a first-order ("bigram") control
(z = 6.77). They concluded that it "arises due to sequential structure above the bigram".

Using the authors' own published song strings and their own segmentation code (Code S1),
we reproduced their numbers almost exactly, and then asked the question registered in
[PREREG.md](PREREG.md) before any data were seen: **is the structure above the bigram more
than second-order (trigram) syllable rules?**

**It is not.** A second-order Markov chain fitted to each recording, with no words in it,
gives song whose chunks are as Zipfian as the real song (null mean R^2 0.879 against the real
0.889; z = 1.07, p = 0.137, 1,000 null datasets). A first-order chain does not (p = 0.001).
The registered label is **`EXPLAINED_BY_SECOND_ORDER`**. The second-order chain is not just
copying the data: on held-out bouts it predicts better than the first-order chain in **30 of
30** recordings (registered overfitting check D1).

What this means: the rank-frequency evidence for "language-like" units in finch song is
fully accounted for by short-range syllable-transition rules that have been known in this
species since Katahira et al. (2011). It does not show that finches have no word-like
units. It shows that this statistic cannot see past second-order syntax in these data.

## Reproduction of the published numbers (theta = cutting ratio)

| quantity | published | ours |
|---|---|---|
| recordings / bouts / transitions | 30 / 299 / 19,990 | 30 / 299 / 19,990 |
| cuts / chunk types (theta 0.5) | 3,205 / 1,043 | 3,205 / 1,043 |
| mean R^2, theta 0.3 / 0.5 / 0.7 | 0.75 / 0.89 / 0.90 | 0.751 / 0.889 / 0.899 |
| z vs shuffle (theta 0.5) | 17.05 | 16.69 |
| z vs within-bout bigram (theta 0.5) | 6.77 | 6.94 |
| z vs rotation (theta 0.5) | 15.69 | 15.07 |
| z vs within-bout bigram (theta 0.7) | 1.87 (P = 0.03) | 1.89 (p = 0.027) |

Our cut positions agree with the boundaries printed in the authors' supplement at every one
of the 3,098 within-line positions (precision 1.000, recall 1.000; all 299 bouts identical).

## Main result (theta 0.5, B = 1,000 per null, seed 20261117)

| null (what it keeps) | null mean R^2 | z | p |
|---|---|---|---|
| shuffle (symbol counts per bout; published) | 0.583 | 16.69 | 0.001 |
| rotation (published) | 0.710 | 15.07 | 0.001 |
| within-bout bigram (published finch control) | 0.791 | 6.94 | 0.001 |
| **pooled first-order chain** (registered primary) | 0.804 | 6.52 | **0.001** |
| within-bout trigram (secondary) | 0.878 | 1.27 | 0.096 |
| **pooled second-order chain** (registered primary) | 0.879 | 1.07 | **0.137** |

Real mean R^2 = 0.8888. Every one of the 1,000 second-order null datasets had a mean R^2 of
at least 0.80, the level usually read as "Zipfian".

## Registered predictions (PREREG.md section 5; Amendment 1)

| id | prediction | prior | outcome |
|---|---|---|---|
| S-F | our mean R^2 at theta 0.5 within 0.03 of 0.89 | 0.60 | TRUE (0.889) |
| F1 | real > within-bout bigram, p < 0.05 | 0.85 | TRUE (p 0.001) |
| F2 | real > pooled first-order chain, p < 0.05 | 0.80 | TRUE (p 0.001) |
| F3 | real > within-bout trigram, p < 0.05 | 0.35 | **FALSE** (p 0.096) |
| F4 | real > pooled second-order chain, p < 0.05 | 0.35 | **FALSE** (p 0.137) |
| F5 | second-order null mean R^2 >= 0.80 | 0.60 | TRUE (0.879) |
| F6 | D1: order 2 generalises better in >= 20 of 30 recordings | 0.75 | TRUE (30 of 30) |
| A1-R1 | our z vs shuffle, bigram and rotation each within 25% of published | (no prior) | TRUE |

6 of 7 scored predictions came true; Brier score **0.099** (S-F to F6).

## The final reading, applied mechanically (`grade_final.py`, published before any result)

* Reading gate: **PASS_EXACT** (all five registered totals exact). Not provisional.
* Base label at theta 0.5: `EXPLAINED_BY_SECOND_ORDER`. Headline allowed.
* Overfit caveat: not applied (D1 holds, 30 of 30).
* Calibration rule A2-R2 (low power): does not apply. Calibration 1 found that the test
  detects clean word-like song in 40 of 40 finch-sized replicates
  ([RESULTS-CALIB.md](RESULTS-CALIB.md)).
* **Robustness (registered rule: same label at theta 0.3 and 0.7): NOT robust.** At 0.3 the
  label is the same (`EXPLAINED_BY_SECOND_ORDER`, second-order p = 0.106). At 0.7, even the
  first-order chain is not beaten (p = 0.060), so the label there is
  `EXPLAINED_BY_FIRST_ORDER`. No threshold gives `BEYOND_SECOND_ORDER`.
* Reversed cut rule and the alternative TP denominator (sensitivity, B = 200): both
  `EXPLAINED_BY_SECOND_ORDER`.
* **Power caveat (CALIB-2 rule WR4):** at finch size, our second-order test detects
  word-like chunks in 100% of replicates with 0% or 2% syllable noise, 85% with 5% noise, and
  10% with 10% noise. **This label cannot exclude word-like chunks degraded by 10% noise.**
  ([RESULTS-CALIB-2.md](RESULTS-CALIB-2.md))

## Hand checks (Amendment 1 requires at least 20 rows before grading)

* 24 rows chosen at random (seed 20261118) were rendered straight from the supplement PDF
  (PyMuPDF crop of the page, independent of our reading) and compared by eye with our reading,
  letter by letter, including every space and line wrap. **24 of 24 matched.** Long runs of
  one letter (e.g. `ddddddd`) were checked as patterns. Their exact lengths are pinned by the
  exact transition total.
* The 42 glyph classes were checked on a contact sheet. Every song letter (a-j), digit and
  name letter carries the right label. The one flagged "possible split" is the digits 6
  and 9, which really are different glyphs.
* z vs shuffle by hand: (0.88877 - 0.58303) / 0.018316 = 16.69. The second-order p,
  0.137 = 137/1001, means 136 of 1,000 null datasets were at least as Zipfian as the real
  song.
* Sums: per-recording syllables add up to 20,289, so 20,289 - 299 bouts = 19,990
  transitions. Per-recording chunk types add up to 1,043. Bout counts add up to 299.

## Prior art (searched again 2026-11-18)

We found no test of either song paper against a second-order or pooled Markov null. The
published discussion includes the eLetters "Zipf zapped" and Lameira & Hills ("Solar
flares..."), press comments (e.g. R. Futrell: "a million different things can give rise to
Zipf's law"), and work showing that finch syntax needs second-order or hidden-state models
(Katahira et al. 2011, PLoS ONE; partially observable Markov models, bioRxiv
10.1101/2022.11.15.516592). See [PRIOR-ART.md](PRIOR-ART.md).

## What this does NOT show

* It does not show that Bengalese finches lack chunk-like units. Their song is famous for
  stereotyped "chunks", and second-order rules are one way to produce them. The point is
  narrower: the Zipf fit carries no information about units **beyond** second-order
  transition statistics.
* We do not yet know whether the test can find **real human words** at this data size. That
  is the next registered test ([CDS-PREREG.md](CDS-PREREG.md): child-directed English at
  finch and whale size). If English also fails to beat a second-order chain, this label will
  be reported as "not distinguishable from real language" (rule L1).
* It is one species, 6 birds and 30 recordings. The whale test is registered separately
  ([PREREG-AMENDMENT-3.md](PREREG-AMENDMENT-3.md)).
* Low power against noisy words (above). The robustness criterion we set ourselves fails
  because at theta 0.7 the result is even weaker (first order suffices).
* The law of brevity in finch song is not tested here. [RESULTS-CALIB-3.md](RESULTS-CALIB-3.md)
  shows the published brevity regression is uninformative on its own.

## Files

* `results/finch/results_finch.json`: every statistic above, per threshold, per null and per
  recording (R^2, slope, chunk types, syllable count). Derived statistics only.
* `results/finch/validation.json`: the reading gate, glyph diagnostics and spacing
  sensitivity.
* The parsed song strings are **not** redistributed (the finch data are CC BY-NC). Anyone
  can regenerate them from the authors' supplement with `glyph_finch.py`.
* Job `song-zipf-finch-v2`, 2026-11-18 03:43-03:56 UTC. Registration commits b583ecc and
  5234e13 (03:25 UTC) came before the job started.
