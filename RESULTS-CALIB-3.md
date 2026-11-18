# RESULTS-CALIB-3: TP chunking reports Zipf's law of brevity even when the true units have the opposite relation

Graded 2026-11-18 by MV2 of Munim, Inc. (mv2@munimtech.com) from job `song-zipf-calib3-v1`
(2026-11-18 07:53-08:12 UTC). Registered in [CALIB-3-PREREG.md](CALIB-3-PREREG.md)
(commit 55b215d, 2026-11-17 23:38 UTC; code 05c628c, 2026-11-18 01:21 UTC) before it ran.
Made with AI agents working in his name. Text CC BY 4.0; code Apache-2.0. Re-derived by
`test_calib3_results.py` from the 140 published replicate lines.

## Headline

Both song papers say that their transitional-probability (TP) chunks obey **Zipf's law of
brevity**: frequent chunks are shorter. They present this as a sign of efficient,
language-like units. The finch paper (Kirby et al. 2026) reports a Poisson regression slope
of -0.04 (P < 0.00001) with no baseline. The whale paper (Arnon et al. 2025) reports
R^2 = 0.62 against shuffled and rotated baselines.

We built synthetic song whose **true words have the reverse relation**: a 12-word lexicon
in which longer words are more frequent (weight 2^(L-3); fitted on the true words, the slope
was positive in 20 of 20 replicates, mean +0.66). Cut into chunks by the published method,
this song showed **significant brevity in 20 of 20 replicates** (mean Wald z = -18.3, past
the finch paper's P < 0.00001 bar) and significant anti-brevity in none.

**The published pipeline reports the law of brevity when the true units obey its opposite.**
The same happened for song with no words at all (first- and second-order chains, 20 of 20
each), for words with no built-in relation (20 of 20), and for **shuffled** song: on average
100% of shuffled copies of wordless song showed significant brevity themselves. Brevity in
this pipeline comes from how it cuts, not from the units it is supposed to find.

## Results (finch size unless marked; theta 0.5; B = 100 per null; 20 replicates)

| source | true relation | mean beta (finch-style) | significant brevity | significant anti-brevity | whale controls passed |
|---|---|---|---|---|---|
| first-order chain | no units | -0.111 | 20/20 | 0/20 | 9/20 |
| second-order chain | no units | -0.037 | 20/20 | 0/20 | 20/20 |
| words, 1/rank weights | none built in | -0.100 | 20/20 | 0/20 | 12/20 |
| words, equal weights | none | -0.128 | 20/20 | 0/20 | 20/20 |
| words, brevity (positive control) | brevity | -0.160 | 20/20 | 0/20 | 20/20 |
| **words, anti-brevity** | **reverse** | **-0.085** | **20/20** | **0/20** | 5/20 |
| first-order chain, whale size | no units | -0.327 | 20/20 | 0/20 | 18/20 |

"Significant" = Wald z beyond 4.42 (two-sided P < 0.00001, the finch paper's bar). "Whale
controls passed" = negative mean slope of log count on length, with R^2 above both the
shuffle and rotation baselines (p < 0.05).

Against Markov nulls, the finch-style slope beat the pooled first-order null in 0 of 20
wordless first-order replicates (correct size). It never beat the pooled second-order null,
even for the positive control (0 of 20): **the Markov nulls have no power for brevity at
finch size.** The within-bout bigram null did better (16 of 20 on the positive control,
0 of 20 on the anti-brevity source).

## Registered predictions

| id | prediction | prior | outcome |
|---|---|---|---|
| P1 | first-order chain: significant brevity in >= 90% | 0.85 | TRUE (20/20) |
| P2 | first-order chain: whale controls passed in >= 80% | 0.45 | **FALSE** (9/20) |
| P3 | first-order chain, whale size: whale controls passed in >= 80% | 0.50 | TRUE (18/20) |
| P4 | brevity words: significant brevity in >= 90% | 0.90 | TRUE (20/20) |
| P5 | equal-weight words: significant brevity in >= 50% | 0.60 | TRUE (20/20) |
| P6 | **anti-brevity words: significant brevity in >= 50%** | 0.35 | **TRUE (20/20)** |
| P7 | anti-brevity words: significant anti-brevity in >= 50% | 0.40 | **FALSE** (0/20) |
| P8 | first-order chain: mean share of shuffled copies with significant brevity >= 90% | 0.85 | TRUE (1.00) |
| P9 | first-order chain: beta beats the pooled first-order null in <= 15% | 0.80 | TRUE (0/20) |
| P10 | brevity words: beta beats the pooled second-order null in >= 50% | 0.45 | **FALSE** (0/20) |

7 of 10 true; Brier score **0.149**.

## Rules fixed in advance, applied

* Sanity: the brevity lexicon's true words have a negative slope and the anti-brevity
  lexicon's a positive slope in 20 of 20 replicates each. Both scenarios are valid.
* **BR1 holds** (P1 and P8): a significant Poisson brevity slope on TP chunks is expected
  from song with no words, and even from shuffled song. On its own it is not evidence of
  efficient units. This applies to the finch paper's brevity test as reported.
* **BR2:** `BREVITY_CONTROLS_PASSED_BY_WORDLESS_SONG_AT_ONE_SIZE`. Wordless first-order song
  passed the whale paper's two brevity controls in 18 of 20 replicates at whale size, but
  only 9 of 20 at finch size.
* **BR3 holds** (P6 true, sanity true): **TP chunking can report brevity when the true units
  show the opposite relation.** This was registered as the headline if it happened.
* **BR4 does not hold** (P7 false): the pipeline does not track the sign of the true
  relation, even for clean, noise-free word sources.

## What this does NOT show

* It does not show that finches or whales lack brevity in their real units. It shows that
  this pipeline's brevity statistic cannot reveal it, because it reports brevity whatever
  the truth is.
* The whale-style R^2 here is computed per recording, over chunk types. The whale paper's
  exact definition (one point per chunk type, pooled over the data set) is calibrated
  separately in [CALIB-4-PREREG.md](CALIB-4-PREREG.md) (queued). Rule BR2 concerns this
  version.
* One generator family (alphabets 8 and 12, 12-word lexicons of length 3-7, no noise).
  Fixed intercepts per recording instead of random intercepts per bird.

## Prior art

Random typing gives brevity in theory (Miller 1957; Li 1992). Brevity in small-ape calls
depends on the unit of analysis (Huang et al. 2020, "Brevity is not a universal in animal
communication"). A
2026 study of crow vocal "counting" built a shuffle null for Menzerath's law. We found no test
of TP segmentation on sources with a known reverse length-frequency relation.

## Files

`results/calib3_results.json` (aggregates and grading) and `results/calib3_tasks.jsonl` (one
line per replicate). Code: `calib3.py`, `calib.py`, `zipfseg.py` (SHA-256 in the results file).
