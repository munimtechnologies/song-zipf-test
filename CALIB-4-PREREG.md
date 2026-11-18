# CALIB-4: is the whale paper's law-of-brevity result passed by song with no words?

Registered 2026-11-18 (about 01:40 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com), before
any of the code below was run and before any brevity statistic was computed on any data,
real or synthetic. Made with AI agents. Text CC BY 4.0; code Apache-2.0.

Code: [calib4.py](calib4.py), tests [test_calib4.py](test_calib4.py). Job:
`song-zipf-calib4-v1` (uses `zipfseg.py` and `calib.py` unchanged from commit 0a5fabe).

## 1. Why this, and why now

Arnon et al. 2025 (*Science* 387:649) report that the chunks found in eight years of
humpback whale song obey **Zipf's law of brevity**: R^2 = 0.62 between chunk length and log
frequency, far above 1000 shuffled datasets (z = 37.57) and 1000 rotated datasets
(z = 13.92). Those two baselines are the only controls reported for it. The paper reads
this as a sign "we are detecting units relevant to the whales".

Reading the paper's own text (the open accepted manuscript, St Andrews repository) fixed
two details that CALIB-3 (registered 2026-11-17, still queued) does not reproduce:

* **The statistic is pooled.** Fig. 3A: "Each point in 3A is one sub-sequence ... the
  frequency distribution of all sub-sequences discovered by our segmentation method across
  the entire data set plotted by length". CALIB-3's whale-style statistic averages a
  per-recording R^2 instead.
* **Each year is one long sequence.** "We ran this segmentation pipeline for each year
  separately ... We created one file containing all the recordings from a given 'year'",
  with "an average of 1562 cuts" per year and a cutting ratio of 0.5.

CALIB-4 runs the statistic as the text defines it, at that size, on sources whose truth we
know. It is registered **before any CALIB-3 or CALIB-2 result exists**, so nothing it
contains was chosen after seeing a brevity result.

## 2. Sources (synthetic only; no real song data)

Six scenarios, 20 replicates each. Each replicate has 8 "years". Each year is ONE sequence
of 5,000-8,000 elements (uniform) from a **fresh** source, because the real song changes
every year. Transitional probabilities are estimated per year, as in the paper.

| scenario | alphabet | what generates each year | true length-frequency relation |
|---|---|---|---|
| `W_markov1_a0.2_V12` | 12 | first-order chain, Dirichlet(0.2) rows | no units at all |
| `W_markov1_a0.1_V24` | 24 | first-order chain, Dirichlet(0.1) rows | no units at all |
| `W_markov2_a0.2_V12` | 12 | second-order chain, Dirichlet(0.2) rows | no units at all |
| `W_words_uniform_V12` | 12 | 12 words of length 3-7, equal weights | none |
| `W_words_brevity_V12` | 12 | 12 words, weight 2^-(L-3) | **brevity** (positive control) |
| `W_words_antibrevity_V12` | 12 | 12 words, weight 2^(L-3) | **reversed** |

Words are concatenated i.i.d. with no noise. For the word sources, the same pooled
statistic is also computed on the **true** words (complete words only) as a sanity check
of the built-in sign.

## 3. Statistic and baselines (theta = 0.5; TPs and cut rule exactly as zipfseg.py / Code S1)

* **Primary, `pool`:** chunk counts summed over the 8 years; one point per chunk type;
  OLS of log10(count) on length (elements). We record R^2 and the slope.
* **Alternate, `year`:** one point per (year, chunk type), with that year's count. If the
  authors' Code S1 (still to be read; job whale-stage0) shows that Fig. 3A uses per-year
  points, `year` becomes the one compared to the published number. Both are graded now
  under the same predictions, so the switch cannot be chosen after seeing results.
* **Baselines**, B = 100 each: shuffle (each year's sequence shuffled, TPs re-estimated,
  re-segmented: "our full segmentation method on ... shuffled datasets"); rotation (Code S1
  `rotate_strings`: rotate the sequence and re-cut at the original chunk lengths); pooled
  first- and second-order Markov chains fitted to each year (our registered nulls).
  One-sided p = share of null R^2 >= real (+1 correction; smallest possible 1/101);
  z uses the population SD, as Code S1 does.
* **Whale controls passed** in a replicate: slope < 0 AND R^2 p < 0.05 against shuffle AND
  against rotation.

## 4. Predictions (graded by `calib4.grade`; priors are ours, for a Brier score)

On the primary `pool` statistic (the same predictions are graded on `year` as the alternate):

| id | prediction | prior |
|---|---|---|
| Q1 | `W_markov1_a0.2_V12`: whale controls passed in >= 80% of replicates | 0.50 |
| Q2 | `W_markov1_a0.1_V24`: whale controls passed in >= 80% | 0.50 |
| Q3 | `W_markov2_a0.2_V12`: whale controls passed in >= 80% | 0.50 |
| Q4 | `W_markov1_a0.2_V12`: mean R^2 >= 0.62 (the whale value) | 0.35 |
| Q5 | `W_markov1_a0.2_V12`: mean z against shuffle >= 10 | 0.30 |
| Q6 | `W_words_brevity_V12`: whale controls passed in >= 90% (positive control works) | 0.85 |
| Q7 | `W_words_uniform_V12`: whale controls passed in >= 50% | 0.50 |
| Q8 | `W_words_antibrevity_V12`: slope < 0 (brevity reported) in >= 50% | 0.30 |
| Q9 | `W_words_antibrevity_V12`: whale controls passed in >= 50% | 0.25 |
| Q10 | `W_markov1_a0.2_V12`: R^2 beats the pooled first-order null (p < 0.05) in <= 15% (size) | 0.80 |
| Q11 | `W_words_brevity_V12`: R^2 beats the pooled second-order null in >= 50% (power) | 0.45 |

## 5. What we will say (rules fixed now)

* **BW1.** If any of Q1-Q3 is true: `WORDLESS_SONG_PASSES_WHALE_BREVITY_CONTROLS`, naming
  the sources. We will then say that the whale paper's two brevity controls, as its text
  defines them, are passed by song generated from syllable-transition rules with no words,
  so on their own they are not evidence of whale-relevant units. If Q1-Q3 are all false:
  `WHALE_BREVITY_CONTROLS_REJECT_WORDLESS_SONG`, and we will say that those controls carry
  real information for these sources. **This is the headline either way.**
* **BW2.** Q8 and Q9 true, and the anti-brevity sources are positive in their true words in
  20 of 20 replicates: the pipeline reports brevity, with both controls passed, **when the
  true units show the opposite relation**.
* **BW3.** Q10 true: the pooled first-order null has the right size for this statistic, and
  the real whale brevity test (registered separately, after Code S1 is read) will use the
  pooled first- and second-order nulls as its deciding baselines.
* **BW4.** Q1, Q2, Q3 and Q9 all false, Q6 true, and the brevity sources are negative in
  their true words in 20 of 20: the published controls separate and track the truth here.
* Sanity: a word scenario whose true words do not have the built-in sign in 20 of 20
  replicates is reported as invalid and its predictions are not interpreted.
* If fewer than 10 replicates of any scenario finish before the time limit, that scenario
  is reported as underpowered and re-run as `-v2` with the same code and a longer limit;
  nothing else changes.
* Whatever happens, this is a statement about the statistic on these synthetic sources, not
  about whales. The real whale test comes after Code S1 and the data are unpacked.

## 6. Disclosures

* Already seen: calib-1 results (rank-frequency R^2 at finch size, different sources and
  seeds). No brevity statistic of any kind has been computed by us on any data.
* Not yet seen: CALIB-2 and CALIB-3 (both queued). The whale data (Data S1-S3) and Code S1
  have been downloaded but not opened.
* Known limits, fixed in advance: one generator family (alphabet 12 or 24, Dirichlet rows,
  12-word lexicons of length 3-7, no noise); real whale years differ in size and share song
  material from year to year, which fresh sources per year do not model; B = 100 instead of
  the paper's 1000 (p resolution 0.0099; z is comparable).
