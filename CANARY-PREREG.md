# CANARY-PREREG: can the Zipf chunk test see real higher-order syntax in animal song?

Registered 2026-11-18 by MV2 of Munim, Inc. (mv2@munimtech.com), before any canary annotation
was read. Made with AI agents. Text CC BY 4.0; code Apache-2.0. Job: `song-zipf-canary-v1`
(code `canary.py`, tests `test_canary.py`; `zipfseg.py` unchanged, fetched at commit 742fd83).
The job polls this file on GitHub and reads no data until it is public (marker: CANARY-PREREG).

## 1. Why

Every result in this repository so far is "explained by a second-order chain" or "not
distinguishable" from one: finch song (RESULTS-FINCH.md), whale song (RESULTS-WHALE.md), and
real English below about 2,745 phonemes per recording (RESULTS-CDS-SIZE.md). English is a
human positive control. We have no **animal** positive control: a species in which song is
known to carry rules beyond second order, run through the same test.

Canaries are that species. Their songs are sequences of *phrases* (trills of one repeated
syllable), and which phrase comes next can depend on three or more phrases back (Markowitz et
al. 2013, PLoS Comput. Biol. 9:e1003052; Cohen et al. 2020, Nature 582:539: transitions after
about 10% of phrase types change by up to an order of magnitude depending on the preceding
three phrases). Prior-art search (2026-11-18): no study has run the transitional-probability
chunk Zipf test of Arnon et al. 2025 (Science) or Kirby et al. 2026 (Sci. Adv.) on canary
song, with or without Markov nulls.

Possible outcomes, and what each would mean:
* **Ground truth beyond order 2, and the Zipf test beats the order-2 chain**: the test can see
  real animal syntax at this data size, so its silence on whale and finch song is informative.
* **Ground truth beyond order 2, but the Zipf test does not beat the order-2 chain**: the test
  is blind to known higher-order syntax in real animal song, and "language-like Zipf" results
  (positive or negative) say little about animal syntax.
* **No ground truth** (our held-out ladder does not show order 3 beating order 2): the control
  is not informative at this size; reported as such.

## 2. Data

Cohen 2022, "Song recordings and annotation files of 3 canaries used to evaluate training of
TweetyNet models for birdsong segmentation and annotation", Dryad 10.5061/dryad.xgxd254f4 =
Zenodo record 5956980, CC0. Birds llb3, llb11, llb16 (files `llb3_data.zip` 2,541,578,049 B,
`llb11_data.zip` 6,477,283,885 B, `llb16_data.zip` 2,392,131,064 B; `*_data_matrices.zip`
not used). Recorded late April to early May 2018; about 30,000 s of song per bird; labels
hand-made for 100 songs, the rest by TweetyNet and then checked and corrected by people
(Cohen et al. 2022, eLife 11:e63853).

Reading: only the annotation csv members inside each zip are read, with HTTP Range requests
(end record, central directory, then the csv member alone; zip64 handled). If the server
does not honour Range, the zip is streamed front to back and only csv members are kept.
Audio is never stored. Members whose file name starts with `._` or that sit under
`__MACOSX/` are ignored. If a zip holds several csv files, all rows are pooled and exact
duplicate rows (same audio file, onset, offset, label) are dropped.

Columns used: `label`, `onset_s`, `offset_s`, `audio_file`. A row is bad if a number does not
parse, the label or audio file is empty, or offset < onset.

## 3. Units

* **Songs**: audio files in file-name order (the names are expected to carry the recording
  time; if not, the order is still fixed and is reported); within a file, syllables in onset
  order; a new song starts after a silence > 1.0 s (the eLife paper's definition) and at every
  new file.
* **Phrases**: each run of one repeated syllable label inside a song becomes one symbol. A
  song's phrase sequence therefore never repeats a symbol twice in a row.
* **Recordings** (the unit over which the papers average Zipf R^2): consecutive whole songs
  until the block holds >= 3,000 phrases (above the 2,745-symbol size where English words were
  found); at most 8 blocks per bird; a trailing incomplete block is dropped.
* **Kirby size**: each block cut to its first songs with >= 666 transitions (Kirby et al.'s
  19,990 transitions / 30 recordings).
* All labels are used as given (no class is removed).

## 4. Gates (per bird; reported, and a failing bird makes the run provisional)

Reading gate: rows > 0, bad rows <= 1%, >= 10 syllable classes (the paper's inclusion rule),
and summed song span (last offset minus first onset, over songs) >= 15,000 s. (The paper's
30,000 s counts whole audio, including silences; we register half of it as a floor, not an
exact reproduction.) Gate failure for a bird does not stop the analysis of the others.

## 5. Analyses (one bird at a time; nothing pooled across birds)

**Ground truth (G): held-out likelihood ladder** on all of a bird's phrase sequences (not
blocks). For Markov orders k = 1..5: leave-one-song-out mean log-likelihood per phrase with
additive smoothing, all orders scored on the same positions (>= 5 in each song). Each order
takes its best alpha from {0.5, 0.1, 0.02, 0.005}. Gains g_k = LL(k+1) - LL(k).
* G3 (bird has syntax beyond order 2) = g_2 > 0, i.e. order 3 predicts held-out phrases better
  than order 2.
* G4 = g_3 > 0 (order 4 beats order 3).

**Power check (D1)**, as in RESULTS-CDS-SIZE.md: per block, order 2 minus order 1 held-out
log-likelihood (alpha 0.5, positions >= 2); D1 majority = more than half of the bird's blocks
favour order 2. Also reported: D2 (order 3 minus order 2, positions >= 3).

**Zipf test** (zipfseg.analyze, unchanged: TP = n(a,b)/n(a), cut where t_i < theta * t_(i-1),
mean per-recording Zipf R^2): theta 0.5 registered, B = 200 null datasets per null; nulls
shuffle, rotate, bigram_within, markov1_pooled, markov2_pooled, markov3_pooled (pooled
third-order chain, same generator with k = 3); one-sided empirical p with +1 correction;
alpha 0.05. Kirby size: theta 0.5, B = 200, same nulls. Robustness: theta 0.3 and 0.7,
B = 100, run only if less than 60% of the 200-minute budget is used.

Label per bird and theta: BEYOND_THIRD_ORDER (beats markov3) > EXPLAINED_BY_THIRD_ORDER
(beats markov2, not markov3) > EXPLAINED_BY_SECOND_ORDER (beats markov1 only) >
EXPLAINED_BY_FIRST_ORDER.

## 6. Reading rules (fixed now)

* **C1 (the positive control)**: if G3 holds in fewer than 2 birds: `NO_GROUND_TRUTH`.
  Otherwise, among the birds with G3: all beat markov2_pooled at theta 0.5:
  `TEST_SEES_REAL_SYNTAX`; none: `TEST_BLIND_TO_REAL_SYNTAX`; some: `TEST_MIXED`.
* **C2 (data size)**: among birds that beat markov2_pooled at full size: all still do at Kirby
  size: `KEPT_AT_KIRBY_SIZE`; none: `LOST_AT_KIRBY_SIZE`; some: `PARTLY_KEPT_AT_KIRBY_SIZE`;
  no bird at full size: `NOTHING_DETECTED_AT_FULL_SIZE`.
* Labels at theta 0.3/0.7 are robustness only and never change C1 or C2.
* `NOT_GRADED` if a needed value is missing for any bird.

## 7. Predictions (priors fixed now; Brier score over graded ones)

| id | prediction | prior |
|---|---|---|
| P1 | G3 (order 3 beats order 2 held out) in >= 2 of 3 birds | 0.75 |
| P2 | G4 (order 4 beats order 3) in >= 2 of 3 birds | 0.45 |
| P3 | all 3 birds beat shuffle and rotate at theta 0.5 | 0.90 |
| P4 | >= 2 birds beat markov1_pooled | 0.70 |
| P5 | >= 2 birds beat markov2_pooled | 0.45 |
| P6 | >= 2 birds beat markov3_pooled | 0.30 |
| P7 | all 3 birds have a D1 majority | 0.80 |
| P8 | >= 2 birds beat markov2_pooled at Kirby size | 0.20 |

## 8. What we will publish

`results/canary/canary_results.json` (every number), RESULTS-CANARY.md with every label,
rule, prediction and the Brier score, and a grader `test_canary_results.py` that re-derives
them from the json. Negative and uninformative outcomes are published the same way.

## 9. Limits known now

Three birds from one lab and season; labels are TweetyNet output checked by people, not all
hand labels; phrases are defined from labels only (no timing rule inside a song); blocks are
consecutive songs, so they are not independent recordings in the papers' sense; the
ground-truth ladder uses simple additive smoothing, which favours low orders when data are
sparse (so G3 is conservative).

MV2, Munim, Inc., mv2@munimtech.com
