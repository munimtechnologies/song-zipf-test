# HOLD-PREREG: a held-out prediction test for structure beyond second order

song-zipf-test, registered 2026-11-19 by MV2 of Munim, Inc. (mv2@munimtech.com), before the
job `song-zipf-hold-v1` runs. Made with AI agents working in MV2's name; no human expert has
checked this design yet. Text CC BY 4.0; code (`hold.py`, `test_hold.py`, `setup_hold.sh`)
Apache-2.0.

## 1. Why

Our graded results so far say that the Zipf-of-chunks statistic used by Arnon et al. 2025
(*Science* 387:649, humpback whale) and Kirby et al. 2026 (*Science Advances*, Bengalese finch)
does not separate song from a second-order Markov chain fitted to it: whale song is
`NOT_DISTINGUISHABLE` (RESULTS-WHALE.md), finch song `EXPLAINED_BY_SECOND_ORDER`
(RESULTS-FINCH.md), and real English is missed below about 2,745 phonemes per recording
(RESULTS-CDS-SIZE.md). Both the whale and the English results point to the same fix: ask
directly whether knowing more than the last two symbols helps predict **unseen** song. If song
contains units longer than three symbols (words, or phrases that repeat), a model that looks
further back must predict held-out song better than an order-2 model. If song is a second-order
chain, it cannot, beyond what finite data allow, and that allowance is measured with the same
Markov-2 surrogates the Zipf test used.

The aim is a method that (a) is calibrated on human language, where words are known to exist,
(b) has a measured false-positive rate, and (c) can be compared head to head with the Zipf test
on identical data. Then it is applied to the whale data.

## 2. Prior art (what is and is not new)

* Suzuki, Buck & Tyack 2006 (*JASA* 119:1849) found that humpback song is not captured by a
  first-order Markov model and has structure at periods of 6-8 and 180-400 units. They did not
  test orders above one with held-out data.
* Kershenbaum et al. 2014 (arXiv:1308.3616) reported conditional entropies by order across
  species; the humpback series stops at order 2 for lack of data.
* Sainburg, Theilman & Gentner 2019 (*Nat. Commun.*) found mutual-information decay with an
  exponential (Markov) and a power-law part in birdsong and speech, but not for humpback song.
  Morita et al. 2021 (*PLoS Comput. Biol.*) asked how much past context predicts Bengalese finch
  syllables, using neural networks.
* Our own D1 check (zipfseg.heldout_ll) compares orders 1 and 2 only, with add-0.5 smoothing.
  The canary job (CANARY-PREREG.md) has a held-out order ladder, but no surrogate calibration.
* We found no study that (i) measures held-out gain beyond order 2 against fitted Markov-2
  surrogates, (ii) calibrates its power on human language at matched sizes against the Zipf
  test on the same data, or (iii) applies it to the Arnon et al. whale data.

## 3. Data (all public; nothing new is downloaded except what the earlier jobs used)

* **English (calibration).** Brent-Ratner child-directed English (br-phono.txt), read by
  `cds_job.load_corpus` with its reading gate (9,790 utterances, 95,809 phonemes). The 17
  replicates are exactly those of CDS-SIZE-PREREG.md: replicate r of size U is 8 consecutive
  blocks of U utterances starting at utterance r x 8 x U (`cds_job.blocks`), for (U, replicates)
  = (70, 5), (140, 5), (280, 4), (600, 2), (1200, 1). An utterance is a bout; phonemes are the
  symbols; word spaces are removed.
* **Whale.** Data S2 of Arnon et al. 2025, read by `whale_run.parse_s2` with Gate A (song types
  2010-2017; 55 recordings; 45,760 elements within 0.5%). A year (song type) is one recording
  and the recordings in it are its bouts, as in the whale test. If the data are not present on
  the machine that runs the job, the whale part is recorded as `WHALE_DATA_MISSING` and run
  later under an amendment; the English part is still graded.
* **What we have already seen.** Both data sets were analysed before, but only with the Zipf
  statistic and D1 (orders 1 and 2). No held-out entropy of order 3 or more has been computed
  on either. While preparing this registration we read one raw whale row (2016, 1,043 elements).
  It shows phrases repeated a fixed number of times, which raised our prior for H5.

## 4. Statistic

For one recording (a list of bouts) and each order k = 0..5: **leave-one-bout-out
cross-entropy** H_k in bits per symbol. Every symbol of every bout is predicted by an
interpolated Witten-Bell model trained on all other bouts of the same recording:
P_j(w|h) = (c(h,w) + T(h) P_{j-1}(w)) / (c(h) + T(h)), with T(h) the number of distinct
successors of h. P_{-1} is uniform over the training alphabet plus one slot for unseen symbols.
If c(h) = 0, P_{j-1} is kept. Contexts never cross a bout boundary; order k uses the last
min(k, i) symbols of the bout. Gain **G = H_2 - min(H_3, H_4, H_5)** (bits per symbol saved on
unseen song by looking further back).

## 5. Null and test

**Null:** `zipfseg.markov_recording(recording, 2, rng)` at commit 742fd83, the pooled
second-order chain that the Zipf test used (same bout lengths). For a set of recordings (one
English replicate of 8 recordings, or the 8 whale years), the statistic is the **mean G over
recordings**. Its null distribution is the mean over recordings of G on surrogate b, for
b = 1..B. p = (1 + #{null >= real}) / (1 + B), one-sided. Label `BEYOND_SECOND_ORDER_HELDOUT`
if p < 0.05, else `NOT_DETECTED`. B = 100 for each English replicate and B = 200 for the whale.
Seeds are fixed in hold.py: recording i of a set with seed s uses Random(100 s + i);
English replicate (U, r) has s = 20261119 + 10000 r + U, and the whale has s = 20261120.
Per-recording p-values are also reported.

**Negative controls (false-positive rate).** For each English replicate, and for the whale,
every recording is replaced by one Markov-2 surrogate of itself (Random(100 s' + i), with
s' = s + 5,000,000 for English and 20261121 for the whale). The full test is then rerun on
that set (English s + 7,000,000; whale 20261122). Such data have no structure beyond order 2,
so they should be labelled `NOT_DETECTED` in about 95% of cases.

## 6. Predictions (priors in hold.PRIORS; Brier over those that can be scored)

* H1 (0.45): HOLD detects English in at least 3 of 5 replicates at U = 70 (about 650 phonemes
  per recording, finch size), where the Zipf test detected 0 of 5.
* H2 (0.80): HOLD detects every replicate at U = 280, 600 and 1200.
* H3 (0.55): R1 is `HOLD_MORE_POWERFUL`.
* H4 (0.85): at most 2 of the 17 English negative controls are labelled
  `BEYOND_SECOND_ORDER_HELDOUT` (P(X <= 2) = 0.95 for Binomial(17, 0.05)).
* H5 (0.85): whale song is `BEYOND_SECOND_ORDER_HELDOUT` (pooled p < 0.05).
* H6 (0.60): at least 6 of the 8 whale years have per-year p < 0.05.
* H7 (0.60): the best order of the year-averaged held-out entropy is 3 or more.
* H8 (0.90): the whale negative control is `NOT_DETECTED`.
* H9 (0.60): with Witten-Bell smoothing, order 2 beats order 1 on held-out whale song
  (year-averaged H_2 < H_1). D1 (add-0.5 smoothing) favoured order 2 in only 1 of 8 years.

## 7. Decision rules (coded in hold.grade; applied exactly as coded)

* **R1 power vs Zipf** (same 17 replicates; Zipf detection rates at theta 0.5 from
  RESULTS-CDS-SIZE.md: 0/5, 1/5, 4/4, 2/2, 1/1). `HOLD_MORE_POWERFUL` if the HOLD detection
  rate is at least the Zipf rate at every size and higher at one or more; `HOLD_EQUAL` if equal
  at every size; `HOLD_LESS_POWERFUL` if at most at every size and lower at one or more;
  otherwise `MIXED`.
* **R2 threshold**: the smallest U with HOLD detection rate >= 0.5, and its mean phonemes per
  recording.
* **R3 negative control**: `CONTROL_OK` if at most 2 of the 17 English negative controls are
  detected, else `CONTROL_FAILED`. If R3 fails, no claim is made from HOLD on any data.
* **R4 whale**: `CONTROL_FAILED` if R3 failed; `BEYOND_SECOND_ORDER_HELDOUT` if pooled
  p < 0.05; `NOT_DETECTED_WITH_POWER` if not, and the R2 threshold is at most 5,720 symbols
  per recording (whale size); else `NOT_DETECTED_UNDERPOWERED`. If the calibration did not
  finish: `CALIBRATION_INCOMPLETE`.

## 8. How results will be read and published

Whichever way it falls, the raw output (`results/hold/hold_results.json`) and
RESULTS-HOLD.md go to this repository, with a grader that re-derives every label, prediction
and the Brier score from the raw output. What each outcome means:
* Whale `BEYOND_SECOND_ORDER_HELDOUT` together with R3 `CONTROL_OK`: whale song carries
  structure that an order-2 chain cannot predict on unseen recordings, but the Zipf statistic
  did not see it. The Zipf law would then be the wrong instrument, not the song simple. This does
  **not** show that the structure is word-like: phrase repetition (Payne & McVay 1971) predicts
  it too.
* Whale `NOT_DETECTED_WITH_POWER`: at a size where English words are detected, unseen whale
  song is predicted no better beyond two symbols than a second-order chain allows.
* `HOLD_MORE_POWERFUL`: a cheap held-out test finds known words at sizes where the Zipf test
  cannot. We would propose it as the default check for animal-song "linguistic law" claims.

## 9. Limits fixed in advance

One English corpus, written as phonemes, and one whale data set coded by human listeners.
Witten-Bell is one smoothing choice (made before any result). min over orders 3-5 is a
selection, but it is applied to the surrogates in the same way. Orders above 5 are not tested.
The Markov-2 surrogate is fitted to the same data, so it is a plug-in null. The English and
whale alphabets differ in size (about 50 phonemes against the whale's element types), so
"whale size" in R4 compares symbol counts, not information.
