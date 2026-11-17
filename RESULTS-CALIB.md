# RESULTS-CALIB: the published Zipf controls are passed by song with no words

Graded 2026-11-17 (about 22:30 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI
agents. Text CC BY 4.0; code Apache-2.0.

Job `song-zipf-calib-v1` ran `calib.py` (registered in
[PREREG-AMENDMENT-2.md](PREREG-AMENDMENT-2.md), committed 2026-11-17 15:15 UTC in 9a281b8)
from 21:30 to 21:39 UTC on 2026-11-17: 120 of 120 replicates, none skipped, unit tests
passed. Raw output: [results/calib_results.json](results/calib_results.json) and one line per
replicate in [results/calib_tasks.jsonl](results/calib_tasks.jsonl). No real song data were
used.

## Headline

On synthetic data the size of the Bengalese finch dataset (30 recordings x 10 bouts):

1. **Song made by first-order syllable rules with no words at all** (`markov1_a0.2`) gave a
   mean Zipf R^2 of **0.85** (the published finch value is 0.89). It beat **both** published
   controls, shuffle and rotation, in **20 of 20** replicates, with mean z = 14.4 and 11.9
   (published finch: 17.05 and 15.69).
2. **Every one of the six sources passed both controls in 20 of 20 replicates**, including
   dense first-order chains, second-order chains and word lexicons. On data of this size the
   shuffle and rotation controls detect *some* sequential structure, not word-like units.
3. Song built from a lexicon whose words are drawn with **equal** probability (not Zipfian)
   still gave a mean R^2 of **0.89**. A Zipf-like curve of TP-cut chunks does not by itself
   say that the underlying units have Zipfian frequencies.
4. Our pre-registered pooled-Markov test behaved as hoped on clean data: it never called
   first-order song "beyond second order" (0 of 40), and it called noise-free word song
   "beyond second order" in 40 of 40. But with **10% of syllables replaced at random**, the
   word song was called `BEYOND_SECOND_ORDER` in only **2 of 20**. A future
   `EXPLAINED_BY_SECOND_ORDER` label on real song therefore cannot exclude word-like chunks
   blurred by modest noise or transcription error.

Registered rule **R3 holds**: we report, independently of any real data, that **the shuffle
and rotation controls cannot by themselves tell word-like units from first-order syllable
rules on data of this size**. These are the only two controls reported for the humpback whale
result (Arnon et al. 2025, *Science* 387:649). The finch paper (Kirby et al. 2026) adds a
within-bout bigram control, which is the informative one: its pooled analogue in our
calibration rejected 0 of 20 first-order sources and 20 of 20 word sources.

What this does **not** show: that whale or finch song has no word-like units. The whale data
are larger and differ in structure, so a whale-sized calibration is registered next
([CALIB-2-PREREG.md](CALIB-2-PREREG.md)), and the real-data tests are still to come.

## Graded predictions (PREREG-AMENDMENT-2, section 4)

| id | prediction | prior | outcome | value |
|---|---|---|---|---|
| C1 | `markov1_a0.2`: mean R^2 >= 0.80 | 55% | **TRUE** | 0.848 (sd 0.021; min 0.808) |
| C2 | `markov1_a0.2`: >= 80% beat both shuffle and rotation | 65% | **TRUE** | 20/20 |
| C3 | `markov1_a0.2`: `markov1_pooled` rejects in <= 15% | 75% | **TRUE** | 0/20 |
| C4 | `markov2_a0.2`: `BEYOND_SECOND_ORDER` in <= 15% (size) | 70% | **TRUE** | 0/20 |
| C5 | `words_zipf`: `BEYOND_SECOND_ORDER` in >= 50% (power) | 50% | **TRUE** | 20/20 |
| C6 | `words_uniform`: mean R^2 >= 0.80 | 40% | **TRUE** | 0.892 |
| C7 | `words_zipf_noise10`: `BEYOND_SECOND_ORDER` in >= 50% | 35% | **FALSE** | 2/20 |

Brier score of our priors: (0.45^2 + 0.35^2 + 0.25^2 + 0.30^2 + 0.50^2 + 0.60^2 + 0.35^2) / 7
= 1.21 / 7 = **0.173**.

Rules (section 5): **R1** (size caveat) does not apply, since C4 holds. **R2** (low-power
relabel) does not apply, since C5 holds. **R3** (published controls) **holds**: 20/20 >= 80%
and mean R^2 0.848 >= 0.80.

## Key numbers (theta = 0.5, B = 100, 20 replicates each)

| source | words? | mean R^2 | z shuffle | z rotate | beat both published controls | `markov1_pooled` rejects | `markov2_pooled` rejects | labels |
|---|---|---|---|---|---|---|---|---|
| `markov1_a0.2` | no | 0.848 | 14.4 | 11.9 | 20/20 | 0/20 | 0/20 | 20 first-order |
| `markov1_a1.0` | no | 0.736 | 16.1 | 11.4 | 20/20 | 0/20 | 0/20 | 20 first-order |
| `markov2_a0.2` | no | 0.640 | 12.4 | 11.4 | 20/20 | 2/20 | 0/20 | 18 first-order, 2 second-order |
| `words_uniform` | yes | 0.892 | 24.4 | 23.1 | 20/20 | 20/20 | 20/20 | 20 beyond second order |
| `words_zipf` | yes | 0.920 | 22.6 | 22.9 | 20/20 | 20/20 | 20/20 | 20 beyond second order |
| `words_zipf_noise10` | yes, 10% noise | 0.825 | 18.7 | 16.7 | 20/20 | 20/20 | 2/20 | 18 second-order, 2 beyond |
| *published finch (Kirby et al. 2026)* | ? | *0.89* | *17.05* | *15.69* | | | | |
| *published whale (Arnon et al. 2025)* | ? | *0.93* | *23.09* | *14.43* | | | | |

The whale row is a different data size and is shown for orientation only. The z-scores do
not grade anything (PREREG-AMENDMENT-2, section 5).

## What else the calibration tells us

* **The Zipf statistic is blind to second-order structure in these chains.** For the
  second-order source, the held-out likelihood check D1 favoured order 2 in all 30 of 30
  recordings of every replicate, yet the Zipf statistic did not beat the first-order null in
  18 of 20. So `EXPLAINED_BY_FIRST_ORDER` means "the Zipf statistic carries nothing beyond
  first order", not "the song is first-order". PREREG.md section 7 already says that a
  Markov label is a statement about the statistic, not about the animal.
* **Noise.** Word structure blurred by 10% random substitutions is mostly absorbed by a
  second-order chain fitted to the same data. Reporting note N1 (added now, after this
  calibration and before any real-song result): any `EXPLAINED_BY_SECOND_ORDER` label on
  real data will be printed with the noise level at which our test loses power. CALIB-2
  measures 2% and 5% to locate it. This note changes no registered label.
* **Size.** Our second-order null did not over-reject (0 of 20 on second-order song), so a
  `BEYOND_SECOND_ORDER` label on real data would not be a size artefact of the test, at least
  for sources like these.

## Hand checks

* Replicate 0 of `markov1_a0.2` (seed 20261117): real R^2 0.80771, shuffle null mean 0.61780,
  sd 0.015885 -> z = 0.18991 / 0.015885 = 11.96 (file: 11.955); rotation null mean 0.71923,
  sd 0.0094322 -> z = 9.381 (file: 9.381). p = 1/101 = 0.0099 for both, the smallest
  possible with B = 100. `markov1_pooled` p = 0.713, `markov2_pooled` p = 0.891 -> label
  `EXPLAINED_BY_FIRST_ORDER` (file agrees).
* Replicate 0 of `words_zipf_noise10`: `markov1_pooled` p = 0.0198 < 0.05,
  `markov2_pooled` p = 0.782 -> `EXPLAINED_BY_SECOND_ORDER` (file agrees).
* `test_calib_results.py` re-derives every aggregate, every label and every graded
  prediction above from the 120 per-replicate lines, and recomputes the Brier score.

## Prior art

We know of no published simulation that runs the TP-segmentation pipeline of these papers
on Markov-chain song and checks the shuffle and rotation controls against it (see
[PRIOR-ART.md](PRIOR-ART.md), rechecked 2026-11-17 ~22:20 UTC). The closest theory is old:
random typing (Miller 1957; Li 1992) and words read off homogeneous Markov chains with a
"space" state (Bochkarev & Lerner 2012, arXiv:1207.1872) give power-law word frequencies.
Our result is the empirical, pipeline-specific version: the same thing happens when the
"spaces" are put in by the published TP-dip rule, and the published controls do not catch
it.

## Limits

* One family of generators: an 8-symbol alphabet, Dirichlet transition rows, 12-word
  lexicons with words of length 3-7. Real song has bird- and year-specific repertoires,
  repeated syllables and (in whales) phrases nested in themes.
* Finch size only. Whale size is CALIB-2.
* B = 100 nulls per test (enough at alpha = 0.05; the smallest possible p is 0.0099).
* This calibrates the statistic. It says nothing about meaning, learning or culture in
  either species, which neither paper's Zipf result was needed for.

## Files

* [results/calib_results.json](results/calib_results.json): config, aggregates, grading.
* [results/calib_tasks.jsonl](results/calib_tasks.jsonl): 120 replicate lines.
* `calib.py`, `zipfseg.py`: the code that ran (unchanged since 9a281b8).
* `test_calib_results.py`: re-derives this file's numbers from the output.
