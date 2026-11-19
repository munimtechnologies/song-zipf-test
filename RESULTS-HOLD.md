# RESULTS-HOLD: held-out prediction beyond second order (English calibration and whale song)

song-zipf-test, graded 2026-11-19 by MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents
working in MV2's name; no human expert has checked this yet. Text CC BY 4.0.

* Registration: [HOLD-PREREG.md](HOLD-PREREG.md) (published before the job ran; the job checked
  its sha256 `132ec99f...` on GitHub at 2026-11-19T10:49:14Z before reading any data).
* Job: `song-zipf-hold-v1`, run 2026-11-19 10:47-11:08 UTC, `python -m unittest -v test_hold`
  passed, then `hold.py` ran for 989 s. Raw output:
  [results/hold/hold_results.json](results/hold/hold_results.json).
* Grader: [test_hold_results.py](test_hold_results.py), published before the result. It
  re-derives every label, rule, prediction and the Brier score with its own code and checks
  that every fixed line below is present. The job's own grading agrees with it.

## Summary in plain words

* **The calibration worked.** On real child-directed English (phonemes, word spaces removed),
  asking whether looking back more than two sounds helps predict *unseen* utterances finds the
  words in **17 of 17** replicates, including **5 of 5** at about 650 phonemes per recording,
  where the Zipf-of-chunks test used by the whale and finch papers found **0 of 5**. Data that
  really are a second-order chain were flagged in **0 of 17** English replicates and in the
  whale negative control. By rule R1 the held-out test is more powerful than the Zipf test at
  every size.
* **Whale song is beyond second order on held-out song.** On the eight years of humpback song
  released with Arnon et al. 2025 (*Science* 387:649), the held-out gain from looking 3-5
  elements back is **-0.0490** bits per element, against **-0.0783** (sd 0.0048) for
  second-order chains fitted to the same song, **p = 0.005** (the smallest value 200 surrogates
  allow). Our earlier Zipf test on the same data could not tell the song from those chains
  (RESULTS-WHALE.md, p = 0.970). So that Zipf result was a power problem, not evidence that the
  song is simple.
* **What it is not.** On average, looking further back still does not *beat* order 2 on unseen
  whale song (the gain is negative; prediction H7 failed). It only costs much less than it
  would if the song were a second-order chain. The effect is clear in 4 of the 8 years
  (2013-2016; H6 failed), and only in 2013 does order 3 actually predict better than order 2.
  Long-range structure in humpback song (repeated phrases and themes) has been known since
  Payne & McVay 1971 and Suzuki et al. 2006; this test does **not** show that it is word-like.
  The repeat-collapse test (RUNS-PREREG.md, queued) asks whether repetition alone explains it.
* **A calibration surprise we did not predict.** Every negative control (17 English, 1 whale)
  came out at p = 1.000, not spread between 0 and 1. A chain refitted to the output of a chain
  scores a higher gain than the chain it came from, so on true second-order data this null
  leans against detection. That makes the whale result conservative, but it also means the
  p values here are not exact under the null. We report it as observed; its cause is not yet
  tested (a likely candidate is that refitting drops rare transitions).

## Status

Job status: `ok`; whale data status: `ok`

## English calibration: detection rate by size

| U (utterances per recording) | HOLD detected | Zipf detected |
|---|---|---|
| 70 | 5 of 5 | 0 of 5 |
| 140 | 5 of 5 | 1 of 5 |
| 280 | 4 of 4 | 4 of 4 |
| 600 | 2 of 2 | 2 of 2 |
| 1200 | 1 of 1 | 1 of 1 |

## English replicates

Gain = H_2 - min(H_3, H_4, H_5), bits per phoneme, mean over the 8 recordings of a replicate.
B = 100 Markov-2 surrogates per replicate.

| U | rep | phonemes per recording | mean gain | null mean gain | p | HOLD label | Zipf detected | negative control mean gain | negative control p | negative control label |
|---|---|---|---|---|---|---|---|---|---|---|
| 70 | 0 | 627 | +0.0469 | +0.0013 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | no | +0.0033 | 1.000 | `NOT_DETECTED` |
| 70 | 1 | 688 | +0.0279 | -0.0036 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | no | +0.0056 | 1.000 | `NOT_DETECTED` |
| 70 | 2 | 622 | +0.0731 | -0.0114 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | no | -0.0188 | 1.000 | `NOT_DETECTED` |
| 70 | 3 | 629 | +0.0597 | +0.0045 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | no | +0.0013 | 1.000 | `NOT_DETECTED` |
| 70 | 4 | 670 | +0.0575 | -0.0006 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | no | -0.0160 | 1.000 | `NOT_DETECTED` |
| 140 | 0 | 1,315 | +0.0591 | -0.0263 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | no | -0.0350 | 1.000 | `NOT_DETECTED` |
| 140 | 1 | 1,251 | +0.1007 | -0.0190 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | yes | -0.0215 | 1.000 | `NOT_DETECTED` |
| 140 | 2 | 1,502 | +0.0663 | -0.0354 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | no | -0.0324 | 1.000 | `NOT_DETECTED` |
| 140 | 3 | 1,471 | +0.0607 | -0.0288 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | no | -0.0280 | 1.000 | `NOT_DETECTED` |
| 140 | 4 | 1,362 | +0.0703 | -0.0196 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | no | -0.0175 | 1.000 | `NOT_DETECTED` |
| 280 | 0 | 2,566 | +0.1184 | -0.0421 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | yes | -0.0429 | 1.000 | `NOT_DETECTED` |
| 280 | 1 | 2,973 | +0.1011 | -0.0603 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | yes | -0.0578 | 1.000 | `NOT_DETECTED` |
| 280 | 2 | 2,870 | +0.1473 | -0.0447 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | yes | -0.0441 | 1.000 | `NOT_DETECTED` |
| 280 | 3 | 2,573 | +0.1160 | -0.0394 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | yes | -0.0494 | 1.000 | `NOT_DETECTED` |
| 600 | 0 | 5,936 | +0.1604 | -0.0766 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | yes | -0.0755 | 1.000 | `NOT_DETECTED` |
| 600 | 1 | 5,813 | +0.1939 | -0.0699 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | yes | -0.0655 | 1.000 | `NOT_DETECTED` |
| 1200 | 0 | 11,748 | +0.2408 | -0.0904 | 0.010 | `BEYOND_SECOND_ORDER_HELDOUT` | yes | -0.0887 | 1.000 | `NOT_DETECTED` |

## English held-out entropy by order (bits per phoneme, mean over recordings)

| U | rep | H0 | H1 | H2 | H3 | H4 | H5 | best order |
|---|---|---|---|---|---|---|---|---|
| 70 | 0 | 5.0016 | 3.7494 | 3.2855 | 3.2415 | 3.2519 | 3.2641 | 3 |
| 70 | 1 | 5.0620 | 4.0277 | 3.6347 | 3.6077 | 3.6230 | 3.6381 | 3 |
| 70 | 2 | 4.9874 | 3.5018 | 3.0137 | 2.9470 | 2.9500 | 2.9676 | 3 |
| 70 | 3 | 4.9731 | 3.6258 | 3.0315 | 2.9735 | 2.9839 | 3.0010 | 3 |
| 70 | 4 | 5.0138 | 3.7893 | 3.2958 | 3.2388 | 3.2442 | 3.2559 | 3 |
| 140 | 0 | 5.0429 | 3.8148 | 3.2818 | 3.2228 | 3.2432 | 3.2623 | 3 |
| 140 | 1 | 4.9860 | 3.5031 | 2.8541 | 2.7578 | 2.7634 | 2.7820 | 3 |
| 140 | 2 | 5.0594 | 3.8694 | 3.3344 | 3.2687 | 3.2834 | 3.3012 | 3 |
| 140 | 3 | 5.0731 | 3.8455 | 3.3092 | 3.2486 | 3.2660 | 3.2878 | 3 |
| 140 | 4 | 5.1047 | 3.8654 | 3.2462 | 3.1767 | 3.1858 | 3.2004 | 3 |
| 280 | 0 | 5.0219 | 3.6122 | 2.9090 | 2.7955 | 2.8007 | 2.8205 | 3 |
| 280 | 1 | 5.0785 | 3.8252 | 3.1857 | 3.0846 | 3.0978 | 3.1215 | 3 |
| 280 | 2 | 5.1104 | 3.8025 | 3.0260 | 2.8860 | 2.8833 | 2.9019 | 4 |
| 280 | 3 | 5.1319 | 3.7137 | 3.0080 | 2.8933 | 2.8978 | 2.9169 | 3 |
| 600 | 0 | 5.0579 | 3.7009 | 2.9479 | 2.7933 | 2.7946 | 2.8190 | 3 |
| 600 | 1 | 5.1290 | 3.7369 | 2.9066 | 2.7216 | 2.7139 | 2.7343 | 4 |
| 1200 | 0 | 5.0998 | 3.7233 | 2.8633 | 2.6415 | 2.6225 | 2.6447 | 4 |

## Whale song (Arnon et al. 2025 Data S2, song types 2010-2017)

B = 200 Markov-2 surrogates. Each year is one "recording"; its recordings are the bouts.

Whale song: mean gain **-0.0490** bits per symbol, null mean -0.0783 (sd 0.0048), p = **0.0050**, label **`BEYOND_SECOND_ORDER_HELDOUT`**

Whale negative control: mean gain **-0.0841** bits per symbol, null mean -0.0589 (sd 0.0045), p = **1.0000**, label **`NOT_DETECTED`**

| year | recordings | elements | H0 | H1 | H2 | H3 | H4 | H5 | best order | gain | null mean gain | p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2010 | 4 | 1,053 | 4.7601 | 4.0365 | 3.9147 | 3.9634 | 4.0890 | 4.1766 | 2 | -0.0487 | -0.0570 | 0.363 |
| 2011 | 6 | 2,028 | 4.6627 | 3.7237 | 3.4464 | 3.5309 | 3.6508 | 3.7735 | 2 | -0.0844 | -0.0811 | 0.582 |
| 2012 | 6 | 3,351 | 4.6430 | 2.8192 | 2.6902 | 2.7957 | 2.8579 | 2.9737 | 2 | -0.1055 | -0.0718 | 1.000 |
| 2013 | 6 | 2,664 | 4.5790 | 3.1326 | 2.8422 | 2.8240 | 2.9408 | 3.0572 | 3 | +0.0181 | -0.0790 | 0.005 |
| 2014 | 7 | 5,765 | 5.0658 | 3.2334 | 2.9324 | 2.9671 | 3.0977 | 3.2288 | 2 | -0.0346 | -0.0977 | 0.005 |
| 2015 | 13 | 14,429 | 3.8654 | 2.1933 | 1.8909 | 1.8946 | 1.9472 | 1.9874 | 2 | -0.0037 | -0.0553 | 0.005 |
| 2016 | 6 | 7,282 | 5.2658 | 3.8292 | 3.5589 | 3.5953 | 3.6880 | 3.7748 | 2 | -0.0364 | -0.0866 | 0.005 |
| 2017 | 7 | 9,177 | 4.8978 | 3.2526 | 2.9821 | 3.0793 | 3.2561 | 3.4665 | 2 | -0.0971 | -0.0978 | 0.498 |

Year-averaged held-out entropy:

| | | | H0 | H1 | H2 | H3 | H4 | H5 | best order |
|---|---|---|---|---|---|---|---|---|---|
| all years (mean) | | | 4.7175 | 3.2775 | 3.0322 | 3.0813 | 3.1909 | 3.3048 | 2 |

## Decision rules (HOLD-PREREG.md section 7, applied as coded)

R1 power vs Zipf: **`HOLD_MORE_POWERFUL`**

R2 threshold: **U = 70** (647 phonemes per recording)

R3 negative control: **`CONTROL_OK`** (0 of 17 English negative controls detected)

R4 whale: **`BEYOND_SECOND_ORDER_HELDOUT`**

## Predictions (priors fixed in HOLD-PREREG.md section 6)

| id | prediction | prior | outcome |
|---|---|---|---|
| H1 | HOLD detects English in >= 3 of 5 replicates at U = 70 | 0.45 | **true** |
| H2 | HOLD detects every replicate at U = 280, 600 and 1200 | 0.80 | **true** |
| H3 | R1 is HOLD_MORE_POWERFUL | 0.55 | **true** |
| H4 | at most 2 of the 17 English negative controls detected | 0.85 | **true** |
| H5 | whale song BEYOND_SECOND_ORDER_HELDOUT (pooled p < 0.05) | 0.85 | **true** |
| H6 | at least 6 of the 8 whale years have p < 0.05 | 0.60 | **false** |
| H7 | best order of the year-averaged whale entropy is 3 or more | 0.60 | **false** |
| H8 | the whale negative control is NOT_DETECTED | 0.90 | **true** |
| H9 | year-averaged whale H_2 < H_1 (Witten-Bell) | 0.60 | **true** |

7 of 9 graded predictions true

Brier score **0.164**

## How to read this together with the earlier results

* RESULTS-WHALE.md: the Zipf-of-chunks statistic could not separate whale song from a
  second-order chain fitted to it (p = 0.970). RESULTS-CDS-SIZE.md: the same statistic also
  misses real English words below about 2,700 phonemes per recording. Here, a held-out test
  finds English words at about 650 phonemes per recording and finds structure beyond second
  order in the whale song. The Zipf statistic was the weak instrument.
* H9 is true: with Witten-Bell smoothing, order 2 predicts unseen whale song better than order 1
  (3.0322 against 3.2775 bits). Our earlier D1 check (add-0.5 smoothing) favoured order 2 in
  only 1 of 8 years, so that D1 result reflected the smoothing, not the song.
* The year-level picture is uneven: the four years with p = 0.005 (2013-2016) are not simply the
  largest (2017, with 9,177 elements, has p = 0.498).

## Limits

One English corpus written as phonemes, and one whale data set coded by human listeners into
element types. Witten-Bell smoothing and orders up to 5 were fixed in advance. The surrogates are
fitted to the same data (a plug-in null), and the negative controls show that this null is
conservative rather than exact. A year of whale song is treated as one recording, so years
differ in size (1,053 to 14,429 elements) and in the number of bouts (4 to 13). The result says
that whale song has sequential structure that a second-order chain does not reproduce on unseen
song; it does not say what that structure is.
