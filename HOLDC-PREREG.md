# HOLDC-PREREG: does humpback song keep structure beyond second order once its repeats are removed?

song-zipf-test, registered 2026-11-19 by MV2 of Munim, Inc. (mv2@munimtech.com), before the
job `song-zipf-holdc-v1` runs. Made with AI agents working in MV2's name; no human expert has
checked this design yet. Text CC BY 4.0; code (`holdc.py`, `test_holdc.py`,
`setup_holdc.sh`) Apache-2.0.

## 1. Why

Two graded results point in different directions:

* **HOLD** ([RESULTS-HOLD.md](RESULTS-HOLD.md)): on held-out song, whale song carries
  structure beyond a second-order Markov chain (held-out gain -0.0490 bits per element
  against -0.0783 for second-order surrogates, p = 0.005).
* **RUNS** ([RESULTS-RUNS.md](RESULTS-RUNS.md)): whale song repeats its cells far more than
  its own second-order chain does (0.6290 of elements removable by collapsing tandem repeats,
  against 0.4982 in the surrogates, p = 0.005), and 35 of the 80 top "words" are repetition
  cells (null 26.89). Once the repeats are collapsed, the Zipf test sees nothing beyond a
  first-order chain, but its power check failed (D1 in 0 of 8 years).

So the question HOLD left open is still open: is the whale's extra held-out structure just
phrase repetition (known since Payne & McVay 1971), or is there sequential structure beyond
second order in the order of the cells themselves? This job asks it with the more powerful
instrument (HOLD), on the collapsed song, with a control that HOLD can still see real units at
exactly the collapsed whale's size, and a control made of repetition alone.

## 2. Prior art

As in HOLD-PREREG.md and RUNS-PREREG.md (Suzuki, Buck & Tyack 2006 on non-Markov and periodic
structure in humpback song; Kershenbaum et al.; Charpentier 2026 arXiv:2608.09459). Searches on
2026-11-19 found no study that tests humpback song for beyond-second-order structure after
removing tandem repeats, or that calibrates a held-out n-gram test against a repetition-only
control.

## 3. Data (all public; nothing new is downloaded)

* **Whale.** Data S2 of Arnon et al. 2025 (*Science* 387:649) on the job's data volume, read by
  `whale_run.parse_s2` with Gate A; one recording per year (song type, 2010-2017), its
  recordings as bouts, exactly as in HOLD and RUNS. Each bout is collapsed with
  `runs.collapse` (lmax 8). RUNS already reports the collapsed sizes: 248, 766, 1,233, 908,
  3,141, 2,926, 3,046 and 4,403 elements (16,671 in all).
* **English (positive control).** Brent-Ratner child-directed English (`cds_job.load_corpus`,
  same reading gate). Five replicates; replicate r starts at utterance 1,850 r and fills 8
  recordings of consecutive utterances (bouts), recording i until it holds at least as many
  phonemes as collapsed whale year i. Each utterance is then collapsed the same way.
* **Repetition-only song (control).** Three data sets. Each starts from one
  collapse-consistent second-order surrogate of the collapsed whale (square-free, no
  structure beyond order 2), then after every element, with probability 0.35, the last L
  elements (L uniform on 1-4) are sung again r more times (r uniform on 1-3)
  (`holdc.inflate`). By design this adds about 1.75 elements per element, so collapsing
  should remove about 0.64 of them (the whale: 0.6290).
* **What we have already seen.** HOLD on the original whale and English; RUNS (sizes, repeat
  shares, the Zipf test on collapsed song). No held-out statistic of collapsed song, and no
  statistic of the repetition-only song, has been computed.

## 4. Test

The statistic and its null are HOLD's, unchanged (`hold.test_set`): leave-one-bout-out
cross-entropy of interpolated Witten-Bell models of order 0-5; held-out gain = entropy at
order 2 minus the best of orders 3-5, averaged over the 8 recordings; one-sided p against the
same mean over B surrogate data sets. Only the surrogate changes: on collapsed song it is
`runs.collapsed_markov(rec, 2)`, a pooled second-order chain fitted to the collapsed bouts and
generated under the same collapse rule, so the null is square-free like the data.

* Whale: B = 1,000. Whale negative control: one collapse-consistent surrogate data set,
  B = 200.
* English: B = 100 for each replicate and for its negative control.
* Repetition-only song: (a) HOLD exactly as registered (Markov-2 surrogates from
  `zipfseg.markov_recording`, uncollapsed song), B = 200; (b) the collapsed version with
  collapse-consistent surrogates, B = 200. Also reported: share removed, and the share of bouts
  that collapsing returns exactly to the square-free base.
* Seeds: SEED = 20261121; whale SEED+1, its negative SEED+2/+3; repetition data set i uses
  SEED+100(i+1) (+1 inflation, +2 test a, +3 test b); English replicate r uses
  SEED+10000(r+1) (+1, +2 for its negative control).

Detected means p < 0.05.

## 5. Decision rules (coded in `holdc.grade`; applied exactly as coded)

* **Control**: `CONTROL_OK` if English is detected in at least 4 of 5 replicates, at most 1 of
  5 English negative controls is detected, the whale negative control is not detected, and the
  collapsed repetition-only song is detected in at most 1 of 3 data sets;
  `CALIBRATION_INCOMPLETE` if any part did not run; else `CONTROL_FAILED`.
* **R1, whale after collapsing**: the control label if it is not `CONTROL_OK`; else
  `BEYOND_SECOND_ORDER_AFTER_COLLAPSE_HELDOUT` if p < 0.05; else `NOT_DETECTED_WITH_POWER`
  (the English control already shows detection at this size).
* **R2, repetition alone**: `REPETITION_FOOLS_HOLD` if HOLD on the uncollapsed
  repetition-only song is detected in at least 2 of 3 data sets; else
  `REPETITION_DOES_NOT_FOOL_HOLD`.

## 6. Predictions (priors in `holdc.PRIORS`; Brier over those that can be scored)

* Q1 (0.55): the collapsed whale song is detected (p < 0.05).
* Q2 (0.85): English is detected in at least 4 of 5 replicates.
* Q3 (0.85): at most 1 of 5 English negative controls is detected.
* Q4 (0.85): the whale negative control is not detected.
* Q5 (0.80): HOLD on the uncollapsed repetition-only song is detected in at least 2 of 3.
* Q6 (0.75): the collapsed repetition-only song is detected in none of 3.
* Q7 (0.50): the collapsed whale's mean held-out gain is above zero (orders 3-5 beat order 2
  outright).

## 7. How results will be read

* R1 `BEYOND_..._HELDOUT` with R2 `REPETITION_FOOLS_HOLD`: repetition alone can produce HOLD's
  signal, but the whale keeps structure beyond second order after its repeats are gone. That
  is evidence for longer-range order among the song's cells (for example the fixed order of
  themes humpbacks are known for), measured with a calibrated test. It is not by itself
  evidence for word-like units.
* R1 `NOT_DETECTED_WITH_POWER` with R2 `REPETITION_FOOLS_HOLD`: at the element level, the
  structure HOLD saw is accounted for by repetition: with repeats removed, a second-order chain
  predicts unseen whale song as well as longer contexts do, while real English units at the
  same size are still found.
* R2 `REPETITION_DOES_NOT_FOOL_HOLD`: repetition alone does not explain HOLD's whale result,
  whatever R1 says.

## 8. Limits fixed in advance

One whale data set coded by human listeners, one year per recording; the nulls are fitted to
the same data (plug-in), and HOLD's negative controls showed this null leans against detection
(every one gave p = 1.000). The repetition-only song is a simple model of repetition (random
cells of 1-4 elements, 1-3 extra copies), not a model of humpback song. English is phonemes
with utterances as bouts, while whale bouts are whole recordings, so the two differ in bout
length. Collapsing removes about 1% of English (RUNS), so the English control is close to
uncollapsed English. If a single-bout recording occurred, its held-out entropy would be
undefined; no whale year or English recording here has fewer than 4 bouts.
