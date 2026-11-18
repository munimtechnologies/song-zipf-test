# RESULTS-CDS: can the test find real human words? Not at finch size, yes at whale size

Graded 2026-11-18 by MV2 of Munim, Inc. (mv2@munimtech.com) from job `song-zipf-cds-v1`
(2026-11-18 12:46-12:59 UTC). Registered in [CDS-PREREG.md](CDS-PREREG.md) (commit 0a01e07,
08:31:59 UTC) and `cds_job.py` (commit 83de8fd, 08:32:04 UTC) before the job started. The job
itself waited until it could read CDS-PREREG.md from the public repository before analysing
anything (found at 12:48:22 UTC). Made with AI agents working in his name. Text CC BY 4.0; code
Apache-2.0. Every number below is re-derived by `test_cds_results.py` from
`results/cds/results_cds.json`.

## Headline

We ran the whole pipeline (the same transitional-probability cutting, the same Zipf
statistic and the same Markov nulls used on finch and whale song) on **real child-directed
English**, transcribed one symbol per phoneme with the word spaces removed. This is the
positive control. If the test cannot find English words, its verdicts on animal song say
little about words either way.

* **At finch size (30 recordings of about 650 phonemes) English does not beat the
  second-order chain.** The real chunks have a mean Zipf R^2 of 0.8955. A second-order
  phoneme chain with no words in it gives 0.8954 (z = 0.01, p = 0.49, 1,000 null datasets).
  Registered rule L1: **`LANGUAGE_FAILS_AT_FINCH_SIZE`**. So the finch label
  `EXPLAINED_BY_SECOND_ORDER` is reported from now on as **not distinguishable from what real
  English gives at the same size**, never as evidence that finch song lacks words.
* **But the registered overfit caveat applies to English and not to the finch.** On held-out
  utterances the second-order English chain predicts worse than a first-order chain in 29 of
  30 recordings (order 2 better in **1 of 30**; registered check D1). With 50 phoneme types
  and about 650 phonemes per recording, a second-order chain has 2,500 contexts to fill and
  partly copies the data. For the finch (syllable letters a-j) order 2 was better in 30 of 30.
  The English failure is therefore partly a failure of the null to generalise, and the
  finch-English comparison is weaker than either label alone suggests.
* **At whale size (8 recordings of about 6,150 phonemes) English beats every null,
  including the second-order chain** (z = 5.6, p = 0.005, the smallest possible with 200
  null datasets; 0 of 200 reached the real value). Registered rule L2:
  **`LANGUAGE_PASSES_AT_WHALE_SIZE`**. Here the second-order chain is not overfit (D1:
  **8 of 8**). The test can see real human words at the size of the whale data.

The wow for the whale test still in the queue: at whale size the Markov test missed a tiny
synthetic lexicon of 12 words ([RESULTS-CALIB-2.md](RESULTS-CALIB-2.md)), but it finds the
1,321-word vocabulary of real speech to infants. A whale result of `BEYOND_SECOND_ORDER` would
put whale song alongside English on this test. A whale result of `EXPLAINED_BY_...` is still
reported as `NOT_DISTINGUISHABLE` (rule WR2, fixed before any whale result), now with the
added fact that real English, at that size, was distinguishable.

## Reading gate (passed exactly)

| quantity | registered | read |
|---|---|---|
| utterances | 9,790 | 9,790 |
| phonemes | 95,809 | 95,809 |
| word tokens | 33,387 or 33,399 (+-20) | 33,399 |
| phoneme / word types | (not gated) | 50 / 1,321 |

Source: TalkBank `BR.zip`, file `br-phono.txt` (129,208 bytes, SHA-256 `b76e44c4...7c99`). The
byte count is a check by itself: 95,809 phonemes + 23,609 word spaces (33,399 - 9,790) + 9,790
line ends = 129,208. The corpus is not redistributed here.

## Main results (theta 0.5; B = 1,000 for CDS-F, 200 for CDS-W; seed 20261117)

| null (what it keeps) | CDS-F null mean R^2 | z | p | CDS-W null mean R^2 | z | p |
|---|---|---|---|---|---|---|
| shuffle (published) | 0.577 | 28.88 | 0.001 | 0.741 | 44.77 | 0.005 |
| rotation (published) | 0.681 | 30.69 | 0.001 | 0.880 | 35.30 | 0.005 |
| within-bout bigram (finch paper) | 0.834 | 13.28 | 0.001 | 0.917 | 16.51 | 0.005 |
| within-bout trigram | 0.855 | 10.57 | 0.001 | 0.930 | 14.09 | 0.005 |
| pooled first-order chain | 0.827 | 12.03 | 0.001 | 0.881 | 23.83 | 0.005 |
| **pooled second-order chain** | **0.895** | **0.01** | **0.49** | **0.941** | **5.61** | **0.005** |
| *real English chunks* | *0.895* | | | *0.952* | | |

Every one of the 1,000 finch-size second-order null datasets had a mean R^2 of at least 0.80.
At whale size English chunks (0.952) are more Zipfian than whale song (0.93) and our wordless
synthetic song (0.917).

## All thresholds (registered robustness: same label at 0.3 and 0.7)

| theta | CDS-F label | p(2nd order) | CDS-W label | p(2nd order) |
|---|---|---|---|---|
| 0.3 | `BEYOND_SECOND_ORDER` | 0.001 | `BEYOND_SECOND_ORDER` | 0.005 |
| **0.5** | **`EXPLAINED_BY_SECOND_ORDER`** | **0.49** | **`BEYOND_SECOND_ORDER`** | **0.005** |
| 0.7 | `EXPLAINED_BY_SECOND_ORDER` | 0.998 | `EXPLAINED_BY_SECOND_ORDER` | 0.76 |

Neither label is robust. English beats the second-order chain at the conservative cut
(theta 0.3) at both sizes, and at no size at the liberal cut (0.7), where the second-order
null is even more Zipfian than English (finch size z = -2.89). For the finch, no threshold gave
`BEYOND_SECOND_ORDER` ([RESULTS-FINCH.md](RESULTS-FINCH.md); second-order p = 0.106 at 0.3), so
at theta 0.3 English beats the second-order chain and finch song does not. We report this
because it is there, but the registered reading is at 0.5.

## How well the cuts find the real word boundaries (descriptive)

| theta | CDS-F precision | recall | F1 | CDS-W F1 |
|---|---|---|---|---|
| 0.3 | 0.627 | 0.362 | 0.459 | 0.590 |
| 0.5 | 0.547 | 0.513 | **0.529** | 0.630 |
| 0.7 | 0.481 | 0.613 | 0.539 | 0.634 |

At theta 0.5 about half of all cuts fall on real word boundaries and about half of the real
boundaries are found. The true English words themselves have a mean Zipf R^2 of 0.917 (finch
size) and 0.943 (whale size), close to what the chunks give.

## Registered predictions (CDS-PREREG.md section 4)

| id | prediction | prior | outcome |
|---|---|---|---|
| H0 | CDS-F mean chunk R^2 at 0.5 >= 0.80 | 0.65 | TRUE (0.895) |
| H1 | CDS-F beats shuffle and rotation | 0.90 | TRUE (p 0.001, 0.001) |
| H2 | CDS-F beats within-bout bigram | 0.50 | TRUE (p 0.001) |
| H3 | CDS-F beats pooled first-order chain | 0.80 | TRUE (p 0.001) |
| H4 | CDS-F `BEYOND_SECOND_ORDER` | 0.40 | **FALSE** (p 0.49) |
| H5 | CDS-W `BEYOND_SECOND_ORDER` | 0.35 | TRUE (p 0.005) |
| H6 | CDS-F D1: order 2 better in >= 20 of 30 | 0.85 | **FALSE** (1 of 30) |
| H7 | CDS-F boundary F1 at 0.5 >= 0.50 | 0.45 | TRUE (0.529) |

6 of 8 true; Brier score **0.254** (0.25375). Our worst misses were H6 (prior 0.85: we did not
foresee that 50 phoneme types would make the second-order chain overfit at finch size) and H5
(prior 0.35: we expected English to fail at whale size too).

## Rules fixed in advance, applied

* **L1:** CDS-F at 0.5 is not `BEYOND_SECOND_ORDER` -> **`LANGUAGE_FAILS_AT_FINCH_SIZE`**.
  RESULTS-FINCH.md now carries a dated note saying its label is not distinguishable from what
  real English gives at that size.
* **Overfit caveat (PREREG.md, decision rule):** an `EXPLAINED_BY_SECOND_ORDER` label gets an
  *overfit caveat* when D1 fails. D1 fails for CDS-F (1 of 30), so the CDS-F label carries it.
  It did not apply to the finch (30 of 30).
* **L2:** CDS-W at 0.5 is `BEYOND_SECOND_ORDER` -> **`LANGUAGE_PASSES_AT_WHALE_SIZE`**. It will be
  printed beside the whale result, together with CALIB-2 rule WR2, which stays as registered.
* **L3:** English beats shuffle and rotation (H1), and so did finch song and wordless synthetic
  song -> **the published controls are passed alike by English, finch song and song with no
  words.**
* **Robustness:** neither CDS label is robust (see the threshold table).

## Hand checks

* z, CDS-F shuffle at 0.5: (0.89547 - 0.57750) / 0.011010 = 28.88.
* z, CDS-W second-order at 0.5: (0.95186 - 0.94139) / 0.0018668 = 5.61.
* p, CDS-F second-order at 0.5: 0.4905 = 491 / 1,001, so 490 of 1,000 null datasets were at
  least as Zipfian as English. CDS-W: 0.004975 = 1 / 201, so none of 200 were.
* Boundary scores, CDS-F at 0.5: 2,420 hits / 4,424 cuts = 0.547; 2,420 / 4,721 true boundaries
  = 0.513; F1 = 0.529.
* Brier: (0.35^2 + 0.10^2 + 0.50^2 + 0.20^2 + 0.40^2 + 0.65^2 + 0.85^2 + 0.55^2) / 8 = 2.03 / 8
  = 0.25375.
* Sizes: CDS-F 19,402 phonemes / 30 = 646.7 per recording (finch: 676 syllables); CDS-W 49,162
  / 8 = 6,145 (whale: about 5,720 elements per year).

## What this does NOT show

* **Phonemes are not syllables or song elements.** English has 50 phoneme types; the finch
  songs are written with 10 syllable letters (a-j). The number of symbol types decides how fast a second-order
  chain overfits, which is exactly where English and finch differ (D1). A matched comparison
  would need units with a similar inventory.
* One language, one corpus, one register (speech to infants), with dictionary pronunciations
  that are cleaner than real speech.
* It does not show that the finch has words, nor that it does not. It shows that at finch
  size this test does not separate finch song from English at the registered threshold.
* B = 200 at whale size: p = 0.005 is the floor, so "beats the second-order chain" is as
  strong as this design can say, no stronger.

## Prior art

We found no study that runs the transitional-probability Zipf pipeline of the whale and
finch papers, or its controls, on human speech as a positive control. Charpentier (2026,
arXiv:2608.09459) recommends stronger surrogates for these papers without reanalysing data.
See [PRIOR-ART.md](PRIOR-ART.md).

## Files

* `results/cds/results_cds.json`: the job's full output (gate, per-threshold statistics for
  every null, held-out check per recording, boundary scores, grading). Derived statistics only.
* Code: `cds_job.py` (with `zipfseg.py` at commit 742fd83, SHA-256 recorded in the results file).
