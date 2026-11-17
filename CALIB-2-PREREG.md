# CALIB-2-PREREG: a whale-sized calibration, and a power-versus-noise curve

Registered 2026-11-17 (about 22:30 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com), before
`calib2.py` was run. Made with AI agents. Text CC BY 4.0; code Apache-2.0.

## 1. What we knew when we wrote this

* The first calibration (`calib.py`, PREREG-AMENDMENT-2) has finished and is graded in
  [RESULTS-CALIB.md](RESULTS-CALIB.md). At finch size, song made by first-order syllable
  rules **with no words** reached a mean Zipf R^2 of 0.85 and beat both of the published
  controls (shuffle and rotation) in 20 of 20 replicates. Our second-order test detected
  noise-free word-like song in 20 of 20 replicates, but only 2 of 20 when 10% of syllables
  were replaced at random.
* No real finch or whale result exists. The finch OCR failed its gate (FINCH-GATE-NOTE-1)
  and the whale supplement has not been unzipped. Only the whale paper's text has been read:
  8 years of song, TPs estimated per year, recordings concatenated within a year, "an average
  of 1562 cuts" per year, mean R^2 0.93, z = 23.09 against shuffle and z = 14.43 against
  rotation (accepted manuscript, St Andrews repository, CC BY). The whale paper's only
  controls are shuffle and rotation.

## 2. Questions

1. **Whale size.** Does wordless first-order song still pass the whale paper's two controls
   when the data look like the whale data (8 pooled years, about 1,500 cuts per year)? How
   Zipfian does it look next to the whale's 0.93?
2. **The finch paper's extra control.** Does the within-bout bigram resampling control of
   Kirby et al. 2026 keep its size (rarely rejecting truly first-order song) at whale size?
3. **Power against noisy words.** Between 0% noise (power 1.00) and 10% noise (power 0.10)
   at finch size, where does our second-order test lose its power?

## 3. Design (`calib2.py`, tests `test_calib2.py`)

`zipfseg.py` and `calib.py` are used unchanged (fetched from commit 0a5fabe of this
repository; their SHA-256 are written into the output). theta = 0.5, B = 100 per null,
20 replicates per scenario, seed 20261118 + 1000 x scenario index + replicate. Nulls:
shuffle, rotation, `bigram_within` (the finch paper's control), `markov1_pooled`,
`markov2_pooled`. Labels use the registered decision rule (`zipfseg.decision`).

Whale size: 8 recordings (= years), each 6 sequences of 700-1500 elements (about 6,600 per
year; at the ~4.4 elements per chunk seen in calib-1, about 1,500 cuts per year). Every year
gets a fresh source. Finch size: as calib-1.

| scenario | size | alphabet | source | words? |
|---|---|---|---|---|
| `W_markov1_a0.2_V12` | whale | 12 | first-order chain, rows ~ Dirichlet(0.2) | no |
| `W_markov1_a0.1_V24` | whale | 24 | first-order chain, rows ~ Dirichlet(0.1) | no |
| `W_markov2_a0.2_V12` | whale | 12 | second-order chain, rows ~ Dirichlet(0.2) | no |
| `W_words_zipf_V12` | whale | 12 | 12 words of length 3-7, Zipf weights | yes |
| `W_words_zipf_noise10_V12` | whale | 12 | same, 10% of symbols replaced at random | yes, noisy |
| `F_words_zipf_noise02` | finch | 8 | calib-1 `words_zipf`, 2% noise | yes, noisy |
| `F_words_zipf_noise05` | finch | 8 | calib-1 `words_zipf`, 5% noise | yes, noisy |

## 4. Predictions and honest priors (graded mechanically by `calib2.grade`)

| id | prediction | prior |
|---|---|---|
| K1 | `W_markov1_a0.2_V12`: >= 80% of replicates beat both shuffle and rotation (p < 0.05) | 80% |
| K2 | `W_markov1_a0.2_V12`: mean R^2 >= 0.80 | 55% |
| K3 | `W_markov1_a0.1_V24`: K1 and K2 both hold for this source too | 45% |
| K4 | `W_markov1_a0.2_V12`: `markov1_pooled` rejects in <= 15% of replicates | 80% |
| K5 | `W_markov2_a0.2_V12`: labelled `BEYOND_SECOND_ORDER` in <= 15% | 75% |
| K6 | `W_words_zipf_V12`: labelled `BEYOND_SECOND_ORDER` in >= 50% | 80% |
| K7 | `W_words_zipf_noise10_V12`: labelled `BEYOND_SECOND_ORDER` in >= 50% | 50% |
| K8 | `F_words_zipf_noise02`: labelled `BEYOND_SECOND_ORDER` in >= 50% | 65% |
| K9 | `F_words_zipf_noise05`: labelled `BEYOND_SECOND_ORDER` in >= 50% | 40% |
| K10 | `W_markov1_a0.2_V12`: `bigram_within` rejects in <= 15% | 70% |

The Brier score of these priors is reported.

## 5. Rules fixed now

* **WR1 (the whale paper's controls at whale size).** If K1 and K2 hold, we report that at
  whale-like size the shuffle and rotation controls are passed by wordless first-order song
  with R^2 >= 0.80 (`CONTROLS_PASSED_BY_WORDLESS_SONG`). If K1 holds and K2 fails:
  `CONTROLS_PASSED_BUT_LESS_ZIPFIAN`. If K1 fails: `CONTROLS_SEPARATE_AT_WHALE_SIZE`, and we
  say plainly that the finch-size finding does not carry over to the whale data. The share of
  replicates reaching R^2 >= 0.93 (the whale value) is reported next to it, as is the
  shuffle and rotation z, for comparison only.
* **WR2 (whale power).** If K6 fails, any `EXPLAINED_BY_...` label on the real whale data is
  reported as `NOT_DISTINGUISHABLE`.
* **WR3 (whale size).** If K5 fails, a `BEYOND_SECOND_ORDER` label on the real whale data
  carries the size caveat and is not a headline.
* **WR4 (noise).** The smallest noise level (of 0, 2, 5 and 10%) at which finch-size power
  falls below 0.50 is printed beside any `EXPLAINED_BY_SECOND_ORDER` finch label, as "this
  label cannot exclude word-like chunks degraded by this much noise".
* Whatever comes out is published, with the prediction table, as RESULTS-CALIB-2.md.

## 6. Limits

* The whale data are not matched in alphabet size or in their hierarchical
  phrase-and-theme structure. Two alphabets (12 and 24) are tried, and the result is a
  statement about these generators, not about whales.
* Real whale song repeats phrases many times within a theme. A first-order chain with
  strong self-transitions is one crude version of that; we do not model themes.
* B = 100 limits the smallest p to about 0.01, which is enough at alpha = 0.05.
