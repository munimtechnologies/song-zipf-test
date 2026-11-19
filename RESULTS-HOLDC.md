# RESULTS-HOLDC: with its repeats removed, humpback song shows no structure beyond a second-order chain

song-zipf-test, graded 2026-11-19 by MV2 of Munim, Inc. (mv2@munimtech.com). Registration:
[HOLDC-PREREG.md](HOLDC-PREREG.md) (registered before the job ran; the job found it public at
2026-11-19T19:53:17Z before reading any data). Job `song-zipf-holdc-v1` (python 3.12.16, 1,031 s).
Raw output: [results/holdc/holdc_results.json](results/holdc/holdc_results.json). Every fixed line
below is re-derived from the raw output by [test_holdc_results.py](test_holdc_results.py), which
was published before the job ran. Made with AI agents working in MV2's name; no human expert has
checked this yet. Text CC BY 4.0.

## What we found

1. **Once its tandem repeats are collapsed, humpback song has no structure on unseen song that
   a second-order chain lacks.** HOLD, the held-out test of [RESULTS-HOLD.md](RESULTS-HOLD.md),
   run unchanged on the collapsed song against 1,000 second-order chains generated under the
   same collapse rule, gives a mean held-out gain of -0.1454 bits per element against -0.0955
   for the surrogates (p = 1.0000). No year shows a positive gain: in all 8 collapsed years,
   looking 3 to 5 elements back predicts unseen song worse than looking 2 back. The uncollapsed
   song had been detected (gain -0.0490 against -0.0783, p = 0.005). Label
   `NOT_DETECTED_WITH_POWER`.
2. **The test had the power to see real units at this size.** Real English, cut into recordings
   with at least as many phonemes as each collapsed whale year (16,503 to 16,620 phonemes per
   replicate after collapsing, against the whale's 16,671 elements), was detected in 5 of 5
   replicates (gains +0.0709 to +0.1215, each p = 0.0099, the smallest 100 surrogates allow).
   None of the 5 English negative controls and not the whale negative control was detected, and
   collapsed repetition-only song was detected in 0 of 3: `CONTROL_OK`.
3. **Random repetition alone does not fool the held-out test.** Song made of second-order
   surrogates re-inflated with random repeats, to about the whale's collapse share (0.6229 to
   0.6266 of elements removed by collapsing, against the whale's 0.6290), was detected in 0 of 3
   data sets uncollapsed and 0 of 3 collapsed (`REPETITION_DOES_NOT_FOOL_HOLD`). We had expected
   the opposite (prediction Q5, prior 0.80).

**Reading, by the rules fixed in HOLDC-PREREG.md section 7.** With `DOES_NOT_FOOL`, random
repetition alone does not explain HOLD's whale result, whatever R1 says. With R1
`NOT_DETECTED_WITH_POWER`, nothing beyond second order is left once the repeats are removed,
although English units of the same size are still found. Taken together: the structure beyond
second order that HOLD found in humpback song is carried by the song's repeats, but not by
repetition as such, since memoryless random repeats do not produce it. It lies in how the whale
repeats (for example, how many times a cell is sung, or which cells are repeated where), not in
the order of distinct cells. That last sentence is our reading of two registered results, not a
registered test; it is the hypothesis to test next.

**What this means for the whale Zipf claim.** The Zipf law of humpback song (Arnon et al. 2025,
*Science* 387:649) is reproduced by a second-order chain ([RESULTS-WHALE.md](RESULTS-WHALE.md));
its most frequent "words" are largely repetition cells ([RESULTS-RUNS.md](RESULTS-RUNS.md)); and
with the repeats removed, a calibrated held-out test that finds English words at the same size
finds nothing in the song beyond a second-order chain. On these data, the sequential structure
behind the "language-like" chunks is phrase repetition plus short-range element rules. This does
not show that humpback song lacks units or meaning; it shows that the published statistics, and
our stronger one, find no word-like ordering beyond repetition.

**Predictions.** 4 of 7 came true (Brier 0.189). The failures: the collapsed whale was not
detected (Q1, prior 0.55), random repetition did not fool HOLD (Q5, prior 0.80), and the collapsed
whale's mean gain was not above zero (Q7, prior 0.50).

**Unpredicted, and not registered (exploratory).** (a) The collapsed whale sits as far below its
null as data drawn from second-order chains do. In units of each test's null sd (from the
`mean_gain`, `null_mean` and `null_sd` fields; computed by hand, not by the grader): collapsed
whale -5.6; whale negative control -5.7; the 5 English negative controls -5.1 to -6.3; the 3
collapsed repetition-only data sets -3.2 to -6.7; the 5 English replicates +14.5 to +24.3. The
registered caveat that this plug-in null leans against detection (HOLD-PREREG.md, section 8)
holds again: every negative control gave p = 1.0000. (b) On collapsed song, order 1 is the best
held-out order in 4 of 8 years (2010, 2011, 2013, 2016), and on average order 2 beats order 1 by
only 0.0437 bits per element (3.8126 against 3.8563), in line with the first-order Zipf match of
RESULTS-RUNS.md. (c) One year, 2014, has a per-year p of 0.0420 (gain -0.0975 against -0.1204);
with 8 years tested and no correction, we do not read it as a detection.

## Fixed lines (test_holdc_results.render_md_lines)

Job status: `ok`; whale data status: `ok`

Whale, repeats collapsed: mean held-out gain **-0.1454** bits per element against -0.0955 (sd 0.0089) for collapse-consistent second-order surrogates (B = 1,000), p = **1.0000**, label **`NOT_DETECTED`**

Whale negative control (one collapse-consistent second-order surrogate): mean gain -0.0974 against -0.0525 (B = 200), p = 1.0000, label `NOT_DETECTED`

Whale, repeats collapsed, mean held-out cross-entropy by context order 0 to 5 (bits per element): 4.9755, 3.8563, 3.8126, 3.9579, 4.0761, 4.1645

### Whale, year by year (repeats collapsed)

| year | elements | after collapsing | bouts | H order 2 | best of orders 3-5 | gain | p |
|---|---|---|---|---|---|---|---|
| 2010 | 1,053 | 248 | 4 | 4.1808 | 4.2939 | -0.1131 | 0.9361 |
| 2011 | 2,028 | 766 | 6 | 4.0987 | 4.2112 | -0.1125 | 0.9081 |
| 2012 | 3,351 | 1,233 | 6 | 3.2242 | 3.3814 | -0.1572 | 1.0000 |
| 2013 | 2,664 | 908 | 6 | 3.8196 | 3.9762 | -0.1566 | 1.0000 |
| 2014 | 5,765 | 3,141 | 7 | 3.5072 | 3.6047 | -0.0975 | 0.0420 |
| 2015 | 14,429 | 2,926 | 13 | 3.3610 | 3.5209 | -0.1599 | 0.9750 |
| 2016 | 7,282 | 3,046 | 6 | 4.6601 | 4.8266 | -0.1665 | 1.0000 |
| 2017 | 9,177 | 4,403 | 7 | 3.6489 | 3.8485 | -0.1996 | 1.0000 |

(Held-out cross-entropy in bits per element; gain = H order 2 minus the best of orders 3-5; p
per year against the same 1,000 surrogates, not used by any rule.)

### English positive control, size-matched to the collapsed whale years (Brent-Ratner child-directed English, 8 recordings per replicate)

| replicate | first utterance | next utterance | phonemes | after collapsing | gain | p | label | negative gain | negative p | negative label |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,814 | 16,758 | 16,568 | +0.0882 | 0.0099 | `BEYOND_SECOND_ORDER_HELDOUT` | -0.0364 | 1.0000 | `NOT_DETECTED` |
| 1 | 1,850 | 3,476 | 16,735 | 16,620 | +0.0859 | 0.0099 | `BEYOND_SECOND_ORDER_HELDOUT` | -0.0226 | 1.0000 | `NOT_DETECTED` |
| 2 | 3,700 | 5,354 | 16,708 | 16,581 | +0.0709 | 0.0099 | `BEYOND_SECOND_ORDER_HELDOUT` | -0.0245 | 1.0000 | `NOT_DETECTED` |
| 3 | 5,550 | 7,239 | 16,750 | 16,541 | +0.1215 | 0.0099 | `BEYOND_SECOND_ORDER_HELDOUT` | -0.0229 | 1.0000 | `NOT_DETECTED` |
| 4 | 7,400 | 9,143 | 16,732 | 16,503 | +0.0921 | 0.0099 | `BEYOND_SECOND_ORDER_HELDOUT` | -0.0234 | 1.0000 | `NOT_DETECTED` |

### Repetition-only song (square-free second-order surrogates of the collapsed whale, re-inflated with random repeats)

| data set | base elements | after inflating | after collapsing | share removed | bouts recovered | uncollapsed gain | p | label | collapsed gain | p | label |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 16,671 | 45,454 | 17,046 | 0.6229 | 0.3273 | -0.1811 | 1.0000 | `NOT_DETECTED` | -0.1193 | 1.0000 | `NOT_DETECTED` |
| 1 | 16,671 | 45,821 | 16,947 | 0.6266 | 0.3818 | -0.1650 | 1.0000 | `NOT_DETECTED` | -0.1008 | 1.0000 | `NOT_DETECTED` |
| 2 | 16,671 | 45,507 | 16,975 | 0.6240 | 0.3273 | -0.1780 | 1.0000 | `NOT_DETECTED` | -0.0778 | 1.0000 | `NOT_DETECTED` |

(Bouts recovered as defined in HOLDC-PREREG.md.)

### Rules

Control: **`CONTROL_OK`** (English detected in 5 of 5 replicates, its negative controls in 0; whale negative control detected: no; collapsed repetition-only song detected in 0 of 3)

R1 whale after collapsing repeats: **`NOT_DETECTED_WITH_POWER`**

R2 repetition alone: **`REPETITION_DOES_NOT_FOOL_HOLD`** (HOLD as registered detected the uncollapsed repetition-only song in 0 of 3 data sets)

### Predictions

4 of 7 graded predictions true

Brier score **0.189**

| prediction | text | prior | outcome |
|---|---|---|---|
| Q1 | the collapsed whale song is detected (p < 0.05) | 0.55 | **false** |
| Q2 | English is detected in at least 4 of 5 replicates | 0.85 | **true** |
| Q3 | at most 1 of 5 English negative controls is detected | 0.85 | **true** |
| Q4 | the whale negative control is not detected | 0.85 | **true** |
| Q5 | HOLD on the uncollapsed repetition-only song is detected in at least 2 of 3 | 0.80 | **false** |
| Q6 | the collapsed repetition-only song is detected in none of 3 | 0.75 | **true** |
| Q7 | the collapsed whale's mean held-out gain is above zero | 0.50 | **false** |

## Limits

One whale data set (New Caledonia, 2010-2017), coded by human listeners, each year treated as
one recording and its recordings as bouts; one English corpus, in phonemes. "With power" means
power against structure as strong as English words at matched size: weaker structure beyond
second order could still be present and missed, and English phonemes (50 types) are not whale
elements. The null is fitted to the same data (plug-in) and leans against detection, so p values
are conservative, not exact. The collapse rule (cells of 1-8 elements, shortest period first) was
fixed before any result; a different rule could keep some structure this one removes. The
repetition-only control uses memoryless random repeats; real repetition with regular counts is
exactly what it does not model, which is why the reading above is a hypothesis.
