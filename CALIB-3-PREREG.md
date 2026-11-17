# CALIB-3: does TP chunking report Zipf's law of brevity for song that has none?

Registered 2026-11-17 (about 23:50 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com), before
any of the code below was run and before any brevity statistic was computed on any data,
real or synthetic. Made with AI agents. Text CC BY 4.0; code Apache-2.0.

Code: [calib3.py](calib3.py), tests [test_calib3.py](test_calib3.py). Job:
`song-zipf-calib3-v1` (uses `zipfseg.py` and `calib.py` unchanged from commit 0a5fabe).

## 1. Why

Both song papers we are re-testing say that the chunks found by transitional-probability
(TP) segmentation obey **Zipf's law of brevity** (more frequent units are shorter), and both
present this as a sign of language-like, efficient units:

* Arnon et al. 2025 (*Science* 387:649, humpback whale) report an R^2 of 0.62 between chunk
  length and log frequency, above shuffled and rotated baselines (z = 37.57 and 13.92).
* Kirby et al. 2026 (*Sci. Adv.* eaea3015, Bengalese finch) report a Poisson mixed-effects
  regression of a chunk's frequency in a recording on its length in syllables, with random
  intercepts for bird: beta = -0.04, SE 0.0045, P < 0.00001. No baseline is reported for
  brevity (checked in the open full text, Europe PMC PMC13450306, 2026-11-17).

Random typing (Miller 1957; Li 1992) is known to produce brevity in theory, and a 2026
review (Bahle & Long, *Curr. Opin. Neurobiol.* 99:103208) warns that segmentation can
create Zipfian frequency curves, but nobody we found has run this pipeline on sources whose
true units have **no** brevity, or the **reverse** relation, to see what it reports. That
is the test here. Our calibration 1 ([RESULTS-CALIB.md](RESULTS-CALIB.md)) did the same
for the rank-frequency law and found that song with no words passes both of the whale
paper's controls.

## 2. Sources (synthetic only; no real song data)

Seven scenarios, 20 replicates each, every recording with a fresh source (as in calib-1):

| scenario | size | alphabet | what generates the song | true length-frequency relation |
|---|---|---|---|---|
| `markov1_a0.2` | finch | 8 | first-order chain, Dirichlet(0.2) rows | no units at all |
| `markov2_a0.2` | finch | 8 | second-order chain, Dirichlet(0.2) rows | no units at all |
| `words_zipf` | finch | 8 | 12 words, length 3-7, weights 1/rank (rank independent of length) | none built in |
| `words_uniform` | finch | 8 | 12 words, equal weights | none |
| `words_brevity` | finch | 8 | 12 words, weight 2^-(L-3) | **brevity** (positive control) |
| `words_antibrevity` | finch | 8 | 12 words, weight 2^(L-3) | **reverse**: longer words more frequent |
| `W_markov1_a0.2_V12` | whale | 12 | first-order chain | no units at all |

Finch size: 30 recordings x 10 bouts of 40-96 syllables. Whale size: 8 "years" x 6 bouts of
700-1,500 elements, TPs pooled within a year (as CALIB-2). Words are concatenated
i.i.d. with no noise. For word sources we also fit the same regression to the **true** words
(complete words only) to confirm the built-in sign (sanity check, section 5).

## 3. Statistics (theta = 0.5, cut rule and TPs exactly as in zipfseg.py / Code S1)

On each recording's inventory of chunk types (observed types only, as in both papers):

* **Finch-style:** Poisson regression of a type's count in its recording on its length,
  with one free intercept per recording (the paper used random intercepts per bird; with
  this many recordings the slope is nearly the same). We report beta, its Wald SE and
  z = beta/SE. "Significant brevity" = z <= -4.42 (two-sided P < 0.00001, the paper's
  bar); "significant anti-brevity" = z >= +4.42.
* **Whale-style:** per recording, R^2 and OLS slope of log(count) on length over chunk
  types, averaged over recordings. The whale paper's exact R^2 (per type or per length
  bin) will be read from its Code S1 (job whale-stage0-v1) before any real whale analysis;
  this calibration does not depend on it.
* **Baselines**, B = 100 each: shuffle (within bout, re-segmented), rotation (Code S1
  `rotate_strings`: rotate the bout and re-cut at the original chunk lengths),
  within-bout bigram resampling (the finch paper's extra control), pooled first- and
  second-order Markov chains (our registered nulls). For R^2: one-sided p = share of null
  values >= real (+1 correction). For beta: one-sided p = share of null betas <= real
  (real more negative = more brevity than the null).
* **Whale controls passed** in a replicate = mean OLS slope < 0 AND R^2 p < 0.05 against
  both shuffle and rotation.

## 4. Predictions (graded by `calib3.grade`; priors are ours, for a Brier score)

| id | prediction | prior |
|---|---|---|
| P1 | `markov1_a0.2`: significant brevity (finch-style) in >= 90% of replicates | 0.85 |
| P2 | `markov1_a0.2`: whale controls passed in >= 80% | 0.45 |
| P3 | `W_markov1_a0.2_V12`: whale controls passed in >= 80% | 0.50 |
| P4 | `words_brevity`: significant brevity in >= 90% (positive control works) | 0.90 |
| P5 | `words_uniform`: significant brevity in >= 50% | 0.60 |
| P6 | `words_antibrevity`: significant **brevity** in >= 50% | 0.35 |
| P7 | `words_antibrevity`: significant **anti-brevity** in >= 50% | 0.40 |
| P8 | `markov1_a0.2`: mean share of **shuffled** datasets that themselves show significant brevity >= 90% | 0.85 |
| P9 | `markov1_a0.2`: beta beats the pooled first-order null (p < 0.05) in <= 15% (size) | 0.80 |
| P10 | `words_brevity`: beta beats the pooled second-order null in >= 50% (power) | 0.45 |

## 5. What we will say (rules fixed now)

* **BR1** (P1 and P8 true): a significant Poisson brevity slope on TP chunks is expected
  from song with no words and even from shuffled song, so on its own it is not evidence of
  efficient units. This would apply to the finch paper's brevity test as reported.
* **BR2**: P2 and P3 true -> `BREVITY_CONTROLS_PASSED_BY_WORDLESS_SONG` (the whale paper's
  two brevity controls are passed by wordless song at both sizes); one of them ->
  `..._AT_ONE_SIZE`; neither -> `BREVITY_CONTROLS_SEPARATE` (those controls do carry
  information about units, for these sources).
* **BR3** (P6 true and the anti-brevity sources really are anti-brevity in their true words
  in 20 of 20 replicates): **TP chunking can report brevity when the true units show the
  opposite relation.** This is the headline result if it happens.
* **BR4** (P4 and P7 true): the pipeline tracks the sign of the true relation for clean word
  sources.
* Sanity: if `words_brevity` true words are not negative (or `words_antibrevity` not
  positive) in 20 of 20 replicates, that scenario is reported as invalid and its
  predictions are not interpreted.
* Whatever happens, the result is a statement about the statistic on these synthetic
  sources, not about whales or finches. Real-data brevity tests, with the same baselines
  plus the bigram and Markov nulls, will be registered separately after CALIB-3 and the
  whale Code S1 reading.

## 6. Disclosures

* Already seen: calib-1 outputs (rank-frequency R^2 and labels for the same generator
  family at finch size, different seeds). No brevity statistic was computed there.
* Not yet seen: everything in this file. CALIB-2 (whale size, rank-frequency) is queued and
  has not returned.
* Limits fixed in advance: one generator family (alphabet 8 or 12, Dirichlet rows, 12-word
  lexicons of length 3-7, no noise); B = 100 (smallest p 0.0099); fixed intercepts instead
  of random intercepts; whale R^2 definition to be confirmed from Code S1.
