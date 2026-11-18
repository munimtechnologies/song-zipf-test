# RESULTS-WHALE: does the "language-like" Zipf law of humpback whale song beat a Markov chain fitted to the song's own transitions?

Graded 2026-11-18 by MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents. Text CC BY
4.0; code Apache-2.0. Paper: Arnon et al. 2025, *Science* 387:649 (8 years of humpback song,
2010-2017; Zipf rank-frequency mean R^2 0.93, z 23.09 against shuffling and 14.43 against
rotation; law of brevity R^2 0.62). Registration: [PREREG.md](PREREG.md),
[PREREG-AMENDMENT-3.md](PREREG-AMENDMENT-3.md), [PREREG-AMENDMENT-5.md](PREREG-AMENDMENT-5.md)
(commit fdc85df, 10:41:36 UTC). Job `whale-test-v1` found that commit before reading any data,
started its analysis at 17:37:36 UTC and finished in 627 s. Code: `whale_run.py`,
`whale_test.py`, `whale_read.py`, `zipfseg.py` (sha256 recorded in the output). Raw output:
`results/whale/`.

## Headline

**Zipf: `NOT_DISTINGUISHABLE`.** On the authors' own data and code, reproduced to the last
digit, whale song beats the paper's two controls and a first-order chain. A second-order
Markov chain fitted to each year's song, with no words in it, gives song that is *more*
Zipfian than the real song (R^2 0.939 against 0.930; p = 0.970). By the registered rule this
is `EXPLAINED_BY_SECOND_ORDER`, reported as `NOT_DISTINGUISHABLE` because our calibration
showed the test cannot always tell word-like song from wordless song at whale size
(CALIB-2, K6 false).

**Brevity: `REPRODUCTION_FAILED`.** Our registered brevity statistic gave R^2 0.021, not the
paper's 0.62, and did not beat the shuffle control, so no brevity label is drawn. This says
nothing against the paper's brevity result: its own Code S1 fits a Poisson mixed model (length
coefficient -0.1197, z -29.53, 3,386 observations), and the 0.62 is not computed anywhere in
Code S1, so we did not have its exact recipe.

**The registered power check says this test is blind here.** The held-out check D1, which in
English predicted when this test can find real words (RESULTS-CDS-SIZE.md: 7 of 7 detected
with a D1 majority, 1 of 10 without), favours order 2 in only 1 of 8 whale years. So the whale
data sit in the regime where the test also misses real English words. The fair reading: **the
whale paper's Zipf evidence does not separate word-like units from second-order element
rules, and neither, at this size, can our test.** It is not evidence that whale song lacks
words.

## Gates

* Gate A (reading): **pass**. 55 rows, 0 bad; 8 years 2010-2017; recordings 4, 6, 6, 6, 7, 13,
  6, 7; 45,749 elements (Table S1 total 45,760; Data S2 groups by song type, so 2015/2016 split
  differently, as registered in Amendment 5). Data sha256 755e4357...a11cff.
* Gate B (exact reproduction of the authors' Code S1 output): **pass**. Zipf R^2
  **0.9303** (0.9302888665216728 against Code S1's printed 0.9302888665216734; difference
  6.7e-16) with 3,386 types, as Code S1 prints. Sound-element R^2 0.867 (paper 0.87).
* Table S2 (most frequent chunk per year): reproduced in 8 of 8 years, including counts.

## Zipf results (theta 0.5, cut rule current/previous, 1,000 null datasets per null)

| null | real R^2 | null mean | gap | z | p |
|---|---|---|---|---|---|
| shuffle (paper's control) | 0.930 | 0.739 | +0.192 | 23.83 | 0.001 |
| rotate (paper's control) | 0.930 | 0.876 | +0.054 | 13.90 | 0.001 |
| bigram_within | 0.930 | 0.905 | +0.025 | 5.02 | 0.001 |
| markov1_pooled | 0.930 | 0.900 | +0.030 | 5.81 | 0.001 |
| trigram_within | 0.930 | 0.943 | -0.013 | -2.73 | 0.991 |
| **markov2_pooled** | 0.930 | **0.939** | **-0.008** | **-2.00** | **0.970** |

Our shuffle and rotation z (23.8, 13.9) are close to the paper's (23.09, 14.43); null draws
differ.

**Robustness (200 null datasets each; labels from the registered rule):**

| run | real R^2 | markov2 null mean | markov2 p | trigram_within p | label |
|---|---|---|---|---|---|
| theta 0.25 | 0.832 | 0.795 | 0.010 | 0.393 | `BEYOND_SECOND_ORDER` |
| theta 0.3 | 0.858 | 0.839 | 0.030 | 0.667 | `BEYOND_SECOND_ORDER` |
| theta 0.5 (registered) | 0.930 | 0.939 | 0.970 | 0.991 | `EXPLAINED_BY_SECOND_ORDER` |
| theta 0.7 | 0.951 | 0.959 | 0.990 | 1.000 | `EXPLAINED_BY_SECOND_ORDER` |
| theta 0.75 | 0.953 | 0.963 | 1.000 | 1.000 | `EXPLAINED_BY_SECOND_ORDER` |
| theta 0.5, reversed cut rule | 0.925 | 0.926 | 0.612 | 0.910 | `EXPLAINED_BY_SECOND_ORDER` |

The Zipf label is **not robust**: at the loosest thresholds (0.25, 0.3) the real song beats the
pooled second-order chain, though never the within-year second-order resampling. English showed
the same threshold pattern at every size (RESULTS-CDS-SIZE.md: always detected at 0.3, never at
0.7), so only the registered threshold is graded.

**Held-out check D1** (order 2 minus order 1 log-likelihood per element, leave one bout out,
per year 2010-2017): -0.021, -0.085, -0.138, -0.036, -0.189, **+0.095**, -0.144, -0.115.
Order 2 generalises better only in 2015, the largest year (14,429 elements).

## Brevity results (theta 0.5; primary statistic: one point per year and chunk type)

Real R^2 0.021, slope -0.0081 (log10 count per element of chunk length). The shuffle null mean
is 0.090 (p = 1.0), the rotation null mean 0.032 (p = 1.0), and every Markov null is above the
real value too. In every null of every run, 100% of the surrogate data sets also have a negative
slope (pooled statistic): cutting at transitional-probability dips makes frequent chunks short whether or not there
are words, as CALIB-3 and CALIB-4 showed on synthetic song.

## Graded predictions (registered priors)

| id | prediction | prior | outcome |
|---|---|---|---|
| S-W | beats shuffle, and R^2 within 0.03 of 0.93 | 0.85 | **true** |
| W1 | beats bigram_within | 0.70 | **true** |
| W2 | beats markov1_pooled | 0.70 | **true** |
| W3 | beats trigram_within | 0.45 | **false** |
| W4 | beats markov2_pooled | 0.45 | **false** |
| W5 | markov2 null mean R^2 >= 0.80 | 0.50 | **true** |
| W6 | D1 favours order 2 in >= 6 of 8 years | 0.70 | **false** |
| N1 | Table S2 top chunk reproduced in >= 6 of 8 years | 0.60 | **true** |
| N2 | beats rotation | 0.90 | **true** |
| N3 | brevity R^2 within 0.10 of 0.62 | 0.45 | **false** |
| N4 | brevity slope negative and beats shuffle and rotation | 0.85 | **false** |
| N5 | brevity beats markov1_pooled | 0.40 | **false** |
| N6 | brevity beats markov2_pooled | 0.25 | **false** |
| G1 | Gate B passes (Amendment 5) | 0.70 | **true** |

7 of 13 original predictions true; Brier score 0.205 over those 13, and **0.197** with G1
(= (13 x 0.205 + 0.3^2) / 14). The alternate brevity statistic (one point per chunk type,
counts pooled over years) gives the same predictions and labels.

## What this adds

1. The whale paper's controls (shuffling and rotation) are passed by song with no words
   (CALIB-2, CALIB-4), by English and by finch song alike. A Markov chain fitted to the whale's
   own element transitions reproduces the Zipf law fully at the registered threshold.
2. On this dataset no test of this kind can yet decide whether whale song has word-like units:
   the second-order chain does not generalise (D1 1 of 8), the regime where real English words
   are missed too. Descriptively (not a registered test), the whale data behave like English at
   650-1,400 phonemes per recording, not like English at the whale's 5,720 symbols per year:
   detected at theta 0.3, not at 0.5 or 0.7, no D1 majority. A likely reason is that whale
   song is far more repetitive within a year than English, so its effective sample is smaller
   than its element count; we have not tested that.
3. What would decide it: more song per year, or a model-comparison test that does not refit
   the null on the same data (for example held-out chunk prediction). The independent-bird
   finch test ([XPOP-PREREG.md](XPOP-PREREG.md)) applies the same logic at 18,000-20,000 notes
   per bird.

## Limits

One dataset (8 years, 55 recordings); years are reconstructed from song types (Amendment 5);
elements are the authors' human-classified sound units; B = 200 in the robustness runs; the
calibration conditions (CALIB-2 K5 true / K6 false; CALIB-4 Q10/Q11 true) were applied as
registered. `test_whale_results.py` re-derives every number above from
`results/whale/whale_results.json`. It was written at 12:33-12:46 UTC, before the job finished,
but it was not included in that run's publish, so it is published only now, unchanged.

MV2, Munim, Inc., mv2@munimtech.com
