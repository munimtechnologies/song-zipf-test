# PREREG-AMENDMENT-2: a synthetic calibration, and how it changes what a label may claim

Registered 2026-11-17 (about 15:30 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com). Made with
AI agents. Text CC BY 4.0; code Apache-2.0.

## 1. Status when this was written

* The finch OCR and analysis job (`song-zipf-finch-v1`, PREREG-AMENDMENT-1) was queued at
  about 14:40 UTC. When this amendment was written it had produced no output, and no finch
  sequence, OCR text, R^2 or z-score had been seen by anyone working on this project.
* The whale supplement (Science Code S1 and Data S1-S3) was downloaded at 14:22 UTC and has
  **not** been opened or unzipped. Only file names, sizes and SHA-256 hashes are known.
* The calibration below uses no real song data at all.

Nothing in PREREG.md or AMENDMENT-1 is changed: the statistic, the nulls, B, the seeds and the
decision labels stay as registered. This amendment adds a **calibration study** and fixes, in
advance, how its outcome qualifies the labels.

## 2. Why a calibration

Our decision rule asks whether real song beats a pooled second-order Markov null
(`BEYOND_SECOND_ORDER`) or not (`EXPLAINED_BY_...`). The rule is only meaningful if:

1. **Size.** Song that really *is* a second-order chain is rarely labelled
   `BEYOND_SECOND_ORDER` (a false positive).
2. **Power.** Song that really *is* made of word-like chunks is usually labelled
   `BEYOND_SECOND_ORDER`. Otherwise "explained by second order" just means "this test cannot
   tell".

A third question bears directly on the published claims. Random texts are known to give
Zipf-like word statistics (Miller 1957; Li 1992). The published controls are a shuffle
(both papers) and a rotation of the cut points (both papers). Can these controls, on data the
size of the finch set, tell word-like song apart from plain syllable-transition rules with
**no words at all**? We could not find any published simulation that checks this, including
the two papers, their eLetters ("Zipf zapped"; Lameira & Hills, "Solar flares show
language-like statistical structures") and a 2026 arXiv comparison of vocal corpora
(arXiv:2609.16612), which does not test the segmentation method.

## 3. Design (`calib.py`, tests `test_calib.py`)

Each synthetic dataset matches the finch data: 30 "recordings" x 10 bouts, bout length uniform
in 40-96 syllables (mean 68; the real data have 20,289 syllables in 299 bouts), alphabet of 8
syllable types. Every recording gets fresh source parameters, like a new bird-day.

| scenario | how song is generated | words? |
|---|---|---|
| `markov1_a0.2` | first-order chain, each row ~ Dirichlet(0.2) (sparse, birdsong-like) | no |
| `markov1_a1.0` | first-order chain, rows ~ Dirichlet(1.0) (dense) | no |
| `markov2_a0.2` | second-order chain, rows ~ Dirichlet(0.2) | no |
| `words_uniform` | 12 distinct random words of length 3-7, drawn i.i.d. with equal probability and concatenated | yes |
| `words_zipf` | same, word probability proportional to 1/rank | yes |
| `words_zipf_noise10` | `words_zipf`, then each syllable replaced by a random one with probability 0.1 | yes, noisy |

For each scenario: 20 replicate datasets (seed 20261117 + 1000 x scenario index + replicate),
theta = 0.5, the Code S1 pipeline in `zipfseg.py`, and B = 100 null datasets each for shuffle,
rotation, `markov1_pooled` and `markov2_pooled` (fewer than the 1000 used on real data, which
is enough to estimate rejection rates at alpha = 0.05). Each replicate gets the same label
function as the real data (`zipfseg.decision`), and D1 is recorded. If the job's time limit
cuts replicates, the ones finished are reported, with the count.

## 4. Predictions and honest priors

| id | prediction | prior |
|---|---|---|
| C1 | `markov1_a0.2`: mean R^2 >= 0.80 (as "Zipfian" as the published finch value, 0.89, roughly) | 55% |
| C2 | `markov1_a0.2`: >= 80% of replicates beat **both** published controls (shuffle and rotation, p < 0.05) | 65% |
| C3 | `markov1_a0.2`: `markov1_pooled` rejects in <= 15% of replicates (size of the first-order null) | 75% |
| C4 | `markov2_a0.2`: labelled `BEYOND_SECOND_ORDER` in <= 15% of replicates (size) | 70% |
| C5 | `words_zipf`: labelled `BEYOND_SECOND_ORDER` in >= 50% of replicates (power) | 50% |
| C6 | `words_uniform`: mean R^2 >= 0.80 even though word frequencies are not Zipfian | 40% |
| C7 | `words_zipf_noise10`: labelled `BEYOND_SECOND_ORDER` in >= 50% of replicates | 35% |

## 5. Rules fixed now for reading the real-data labels

* **R1 (size caveat).** If C4 fails, a `BEYOND_SECOND_ORDER` label on real finch or whale data
  carries the caveat "the second-order null rejects true second-order song too often" and is
  not reported as a headline.
* **R2 (power).** If C5 fails, an `EXPLAINED_BY_SECOND_ORDER` or `EXPLAINED_BY_FIRST_ORDER`
  label on real data is reported as `NOT_DISTINGUISHABLE` (the test has low power against
  word-like song of this size), never as "the Zipf structure reduces to syllable rules".
* **R3 (published controls).** If at least 80% of `markov1_a0.2` replicates beat both published
  controls **and** their mean R^2 is at least 0.80, we will report, independently of the real
  data, that the published shuffle and rotation controls cannot by themselves tell word-like
  units from first-order syllable rules on data of this size. If R3 does not hold, we will say
  that too.
* The z-scores of the synthetic sources against shuffle and rotation are reported next to
  the published finch values (17.05 and 15.69) for comparison only. They do not grade anything.

## 6. Limits

* An 8-syllable alphabet, 12-word lexicons and Dirichlet rows are one choice among many. Real
  Bengalese finch song has bird-specific repertoires and repeated syllables, and the
  calibration says nothing about other choices. The whale data (eight years, one long
  concatenated sequence per recording) are not matched here. A whale-sized calibration will
  be registered with the whale amendment if this one is informative.
* B = 100 limits the smallest p to about 0.01, which is enough for alpha = 0.05.
