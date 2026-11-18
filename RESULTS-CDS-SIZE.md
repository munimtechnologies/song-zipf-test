# RESULTS-CDS-SIZE: how much data does this test need to find real human words?

Graded 2026-11-18 by MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents. Text CC BY
4.0; code Apache-2.0. Registration: [CDS-SIZE-PREREG.md](CDS-SIZE-PREREG.md) (commit 52b82ef,
13:27 UTC). Job `song-zipf-cdssize-v1` read the public registration at 18:08:20 UTC, then ran
(18:06-18:21 UTC, 753 s of analysis). Raw output: `results/cds-size/cds_size_results.json`.
Grader, published before the job ran: `test_cds_size_results.py` (commit e269a10).

## Headline

**On real child-directed English, the TP-chunk Zipf test starts finding words beyond a
second-order phoneme chain at about 2,700 phonemes per recording, and the held-out overfit
check D1 predicts in advance whether it will.** Below that size, English is "explained by
second order" just like finch song was; above it, English is detected every time at theta 0.5.

* T1 (size threshold): **`THRESHOLD_FOUND`** at U = 280 utterances per recording, which is
  2,745 phonemes per recording (mean of its 4 replicates).
* T2 (does D1 predict power?): **`D1_TRACKS_DETECTION`**. Replicates where order 2 generalises
  better than order 1 in most recordings were detected 7 of 7 times (rate 1.0); replicates
  without a D1 majority were detected 1 of 10 times (rate 0.1).
* T3 (context, symbol counts only): whale size within the detecting range: **yes** (5,720
  elements per year against 2,745); finch size within the detecting range: **no** (676
  syllables per recording).
* 7 of 7 true graded predictions; Brier score **0.120**.

## Size curve (theta 0.5 is the registered label; 0.3 and 0.7 are robustness)

| U | replicates | phonemes per recording | detected 0.3 | **detected 0.5** | detected 0.7 | D1 majority | mean second-order z (0.5) | mean boundary F1 (0.5) |
|---|---|---|---|---|---|---|---|---|
| 70 | 5 | 647 | 5 of 5 | **0 of 5** | 0 of 5 | 0 of 5 | 0.18 | 0.530 |
| 140 | 5 | 1,380 | 5 of 5 | **1 of 5** | 0 of 5 | 0 of 5 | 0.28 | 0.572 |
| 280 | 4 | 2,745 | 4 of 4 | **4 of 4** | 0 of 4 | 4 of 4 | 2.91 | 0.597 |
| 600 | 2 | 5,874 | 2 of 2 | **2 of 2** | 0 of 2 | 2 of 2 | 5.89 | 0.619 |
| 1,200 | 1 | 11,748 | 1 of 1 | **1 of 1** | 0 of 1 | 1 of 1 | 7.10 | 0.633 |

## Every replicate

| U | rep | phonemes | label at 0.5 | second-order z | second-order p | D1 | published controls pass at 0.5 | boundary F1 |
|---|---|---|---|---|---|---|---|---|
| 70 | 0 | 5,019 | `EXPLAINED_BY_SECOND_ORDER` | -0.39 | 0.564 | 0 of 8 | yes | 0.507 |
| 70 | 1 | 5,503 | `EXPLAINED_BY_SECOND_ORDER` | -1.03 | 0.851 | 0 of 8 | yes | 0.534 |
| 70 | 2 | 4,977 | `EXPLAINED_BY_SECOND_ORDER` | 0.45 | 0.347 | 0 of 8 | yes | 0.578 |
| 70 | 3 | 5,030 | `EXPLAINED_BY_SECOND_ORDER` | 0.94 | 0.208 | 1 of 8 | yes | 0.476 |
| 70 | 4 | 5,357 | `EXPLAINED_BY_SECOND_ORDER` | 0.97 | 0.168 | 0 of 8 | yes | 0.554 |
| 140 | 0 | 10,522 | `EXPLAINED_BY_SECOND_ORDER` | 0.77 | 0.228 | 0 of 8 | yes | 0.537 |
| 140 | 1 | 10,007 | `BEYOND_SECOND_ORDER` | 1.95 | 0.030 | 2 of 8 | yes | 0.564 |
| 140 | 2 | 12,012 | `EXPLAINED_BY_SECOND_ORDER` | -0.97 | 0.842 | 0 of 8 | yes | 0.600 |
| 140 | 3 | 11,770 | `EXPLAINED_BY_SECOND_ORDER` | -1.20 | 0.871 | 0 of 8 | yes | 0.573 |
| 140 | 4 | 10,896 | `EXPLAINED_BY_SECOND_ORDER` | 0.85 | 0.228 | 0 of 8 | yes | 0.585 |
| 280 | 0 | 20,529 | `BEYOND_SECOND_ORDER` | 3.68 | 0.010 | 6 of 8 | yes | 0.577 |
| 280 | 1 | 23,782 | `BEYOND_SECOND_ORDER` | 2.22 | 0.030 | 5 of 8 | yes | 0.614 |
| 280 | 2 | 22,958 | `BEYOND_SECOND_ORDER` | 2.17 | 0.010 | 8 of 8 | yes | 0.614 |
| 280 | 3 | 20,584 | `BEYOND_SECOND_ORDER` | 3.59 | 0.010 | 6 of 8 | yes | 0.585 |
| 600 | 0 | 47,485 | `BEYOND_SECOND_ORDER` | 7.15 | 0.010 | 8 of 8 | yes | 0.617 |
| 600 | 1 | 46,501 | `BEYOND_SECOND_ORDER` | 4.62 | 0.010 | 8 of 8 | yes | 0.620 |
| 1,200 | 0 | 93,986 | `BEYOND_SECOND_ORDER` | 7.10 | 0.010 | 8 of 8 | yes | 0.633 |

p = 0.010 is the floor for B = 100 null datasets. Every replicate at every size passed the two
controls the whale and finch papers used (shuffle and rotation).

## Graded predictions (registered priors)

| id | prediction | prior | outcome |
|---|---|---|---|
| Z1 | detection rate at U = 70 is <= 0.2 (got 0.0) | 0.75 | **true** |
| Z2 | detection rate at U = 600 is >= 0.5 (got 1.0) | 0.75 | **true** |
| Z3 | the U = 1,200 replicate is detected | 0.75 | **true** |
| Z4 | detection rate never falls as U grows (0, 0.2, 1, 1, 1) | 0.50 | **true** |
| Z5 | no U = 70 replicate has a D1 majority | 0.85 | **true** |
| Z6 | every U = 600 and U = 1,200 replicate has a D1 majority | 0.85 | **true** |
| Z7 | the size threshold (T1) is U <= 280 | 0.40 | **true** |

7 of 7 true. Brier score **0.120** = (3 x 0.25^2 + 0.5^2 + 2 x 0.15^2 + 0.6^2) / 7 = 0.8425 / 7.

## What it means

* **The finch result was below this test's power.** Kirby et al.'s recordings hold about 676
  syllables each. At that size real English words also come out "explained by a second-order
  chain" (0 of 5 replicates detected), so our finch label `EXPLAINED_BY_SECOND_ORDER` cannot be
  read as "finch song has no words", as RESULTS-FINCH.md and RESULTS-CDS.md already say.
* **D1 is a cheap power check anyone can run first.** Whether order 2 beats order 1 on held-out
  bouts in most recordings needs no null models and no word boundaries, and here it separated
  the replicates where words were detectable (7 of 7) from those where they were not (1 of 10).
  As registered, we apply it to the whale result (reporting, never relabelling): see
  [RESULTS-WHALE.md](RESULTS-WHALE.md).
* **The threshold theta matters as much as the size.** At theta 0.3 English was labelled
  `BEYOND_SECOND_ORDER` in all 17 replicates, even at finch size; at theta 0.7 in none, even at
  11,748 phonemes per recording. A label at one threshold is not a finding; only the registered
  threshold (0.5) is graded here.
* **The published controls see nothing of this.** Shuffle and rotation were passed in all 17
  replicates, whether or not words were detectable.

## Limits

One language, one corpus, phonemes (50 types) rather than syllables; few replicates at the two
largest sizes (2 and 1); the U = 600 replicates reuse utterances analysed in RESULTS-CDS.md with
different boundaries (stated in the registration). T3 compares symbol counts only: phonemes,
finch syllables (about 8 types per bird) and whale sound elements are different units, so T3 is
context, not a test of either species.

MV2, Munim, Inc., mv2@munimtech.com
