# RUNLEN-PREREG: what in humpback song's repetition carries its structure beyond second order?

song-zipf-test, registered 2026-11-19 by MV2 of Munim, Inc. (mv2@munimtech.com), before the
job `song-zipf-runlen-v1` runs. Made with AI agents working in MV2's name; no human expert has
checked this design yet. Text CC BY 4.0; code (`runlen.py`, `test_runlen.py`,
`setup_runlen.sh`) Apache-2.0.

## 1. Why

Three graded results frame the question:

* **HOLD** ([RESULTS-HOLD.md](RESULTS-HOLD.md)): on held-out song, humpback song carries
  structure beyond a second-order Markov chain (mean held-out gain -0.0490 bits per element
  against -0.0783 for second-order surrogates, p = 0.005).
* **HOLDC** ([RESULTS-HOLDC.md](RESULTS-HOLDC.md)): once every tandem repeat is collapsed, the
  same test finds nothing beyond second order (-0.1454 against -0.0955, p = 1.0000), although
  it finds English units at the same size in 5 of 5 replicates.
* Also HOLDC: song made of random repeats of random cells, at the whale's repeat share, does
  not fool the test (0 of 3).

So the extra structure lives in how the whale repeats, and memoryless repetition does not
produce it. RESULTS-HOLDC.md ended with a hypothesis, not a test: the signal may lie in how
many times a cell is sung, or in which cells are repeated where. This job tests those
alternatives directly by permuting the whale's own repetition while keeping everything else.

## 2. Prior art

Humpback song is hierarchical: units form phrases, a phrase is repeated to form a theme,
themes follow a fixed order (Payne & McVay 1971). The number of phrase repetitions per theme
is known to vary widely, within and between singers (for example 1 to 17 phrases per theme in
one recording; a 2021 review of song morphing, PMC7844363, notes that what prompts a singer to
vary it is not known), and some themes are typically repeated more than others. Suzuki, Buck &
Tyack (2006) showed non-Markov structure in humpback song with information-theoretic measures.
Arnon et al. (2025, *Science* 387:649) found Zipf-distributed chunks; our RESULTS-RUNS.md
showed those chunks are largely repetition cells. Web searches on 2026-11-19 (and the eLetters
listed on the Arnon et al. article page) found no study that asks whether repetition counts or
the placement of repeated phrases carry sequential structure that a held-out n-gram test can
detect, or that tests copy counts for cell specificity against a within-length permutation.

## 3. Data (all public; nothing new is downloaded)

Data S2 of Arnon et al. 2025 on the job's data volume, read by `whale_run.parse_s2` with Gate
A; one recording per year (2010-2017), its recordings as bouts, exactly as in HOLD (45,749
elements in all). Nothing about runs of this data has been computed before this job, except
RUNS's share of elements removed by collapsing (0.6290).

**Runs.** Each bout is parsed left to right (`runlen.tokenize`, lmax 8): at each position the
cell of 1-8 elements whose consecutive copies (at least 2) cover the most elements is taken,
with its number of copies (ties go to the shorter cell); a position with no adjacent copy is a
one-element cell sung once. Expanding the runs gives back the bout exactly (checked by the
job). A "repeated run" is a run with 2 or more copies.

## 4. Tests

The held-out statistic and its null are HOLD's, unchanged (`hold.test_set`, Markov-2
surrogates from `zipfseg.markov_recording`, B = 200, the same as HOLD on the whale): mean over
the 8 years of held-out gain (cross-entropy at order 2 minus the best of orders 3-5); detected
means p < 0.05. Every permutation acts within one year, across its bouts.

* **M0 (pipeline check).** HOLD on the unpermuted song with HOLD's own seed (20261120). It must
  reproduce RESULTS-HOLD.md (mean gain -0.0490 to 4 decimals, p < 0.05).
* **M1, counts within cell.** The copy counts of repeated runs are permuted among runs of the
  same cell. Kept: which cells are repeated, where, and each cell's count distribution. Broken:
  any link between a count and its place in the song.
* **M2, counts within cell length.** The copy counts of repeated runs are permuted among runs
  whose cells have the same length. Also broken: any cell-specific count. Total length is kept.
* **M3, cells within cell length.** The cells of repeated runs with 2-8 elements are permuted
  among runs of the same cell length; every count stays where it was. Kept: the repertoire of
  repeated phrases and how often each is repeated as a run. Broken: which phrase is repeated
  where (the order of the repeated phrases).
* Five permuted data sets of each kind, interleaved (M1, M2, M3 for replicate 0, then 1, ...).
  Seeds: permutation SEED + 1000 k + 10 (i + 1) for kind k = 1, 2, 3 and replicate i = 0-4,
  HOLD on it with that seed + 1; SEED = 20261122.
* **Negative control.** One Markov-2 surrogate of the whale (`hold.neg_dataset`, seed SEED+7),
  parsed into runs and permuted by M3 (seed SEED+8), HOLD with seed SEED+9. It should not be
  detected: the permutation itself must not create structure HOLD can see.
* **Count specificity (CS).** Among repeated runs, the conditional mutual information between
  cell and copy count given cell length, I = H(count | length) - H(count | cell), times the
  number of repeated runs, summed over years; against the same statistic after M2, B = 2,000
  (seed SEED+5); one-sided p with +1 correction. Are counts cell-specific beyond what cell
  length explains?
* A permutation is INERT if it changes fewer than 20% of the repeated runs it acts on (summed
  over its 5 data sets), for example if most repeated cells occur only once a year.

## 5. Decision rules (coded in `runlen.grade`; applied exactly as coded)

* Verdict of a kind: `SURVIVES` if detected in at least 3 of 5 data sets, `DESTROYED` if in at
  most 1, else `MIXED`; `INCOMPLETE` if fewer than 5 ran.
* **Pipeline**: `PIPELINE_OK` if expanding the runs is lossless and M0 is detected with mean
  gain within 0.00005 of HOLD's -0.04904; else `PIPELINE_FAILED`. **Control**: the pipeline
  label if not OK; `CONTROL_FAILED` if the negative control is detected; else `CONTROL_OK`.
* **R1, copy counts** (if CONTROL_OK): if M1 is INERT, `COUNTS_NOT_NEEDED` /
  `COUNTS_CARRY_IT_M1_INERT` / `MIXED` by M2's verdict; else `CONTEXT_SPECIFIC_COUNTS_CARRY_IT`
  if M1 is DESTROYED; `CELL_SPECIFIC_COUNTS_CARRY_IT` if M1 SURVIVES and M2 is DESTROYED;
  `COUNTS_NOT_NEEDED` if both SURVIVE; else `MIXED`.
* **R2, placement of repeated phrases** (if CONTROL_OK): `M3_INERT` if M3 is INERT; else
  `PLACEMENT_NOT_NEEDED` (SURVIVES), `PLACEMENT_CARRIES_IT` (DESTROYED) or `MIXED`.
* **R3, count specificity**: `COUNTS_CELL_SPECIFIC` if CS p < 0.05, else
  `NO_CELL_SPECIFIC_COUNTS`.

## 6. Predictions (priors in `runlen.PRIORS`; Brier over those that can be scored)

* Q1 (0.95): PIPELINE_OK.
* Q2 (0.75): copy counts are cell-specific beyond cell length (CS p < 0.05).
* Q3 (0.70): M1 SURVIVES.
* Q4 (0.60): M2 SURVIVES.
* Q5 (0.45): M3 SURVIVES.
* Q6 (0.90): the negative control is not detected.
* Q7 (0.65): the mean held-out gain of the five M2 data sets is below M0's.

## 7. How results will be read

* `COUNTS_NOT_NEEDED` with `PLACEMENT_NOT_NEEDED`: the beyond-second-order signal survives
  scrambling both how many times and where phrases are repeated. It then lies in the
  repertoire of repeated multi-element phrases themselves (recurring cells longer than two
  elements, sung as runs), which a second-order chain cannot hold but a longer context can.
  That is phrase structure, the textbook unit of humpback song, not evidence of word-like
  ordering.
* `COUNTS_NOT_NEEDED` with `PLACEMENT_CARRIES_IT`: the order in which repeated phrases follow
  one another (theme order) carries the signal.
* `CELL_SPECIFIC_COUNTS_CARRY_IT` or `CONTEXT_SPECIFIC_COUNTS_CARRY_IT`: how many times a
  phrase is sung is itself predictable, by phrase or by position, and that regularity is
  what a held-out test sees beyond second order. That would be a new, measurable regularity of
  humpback song, given how variable repetition counts are reported to be.
* R3 is read on its own: whether count variation is phrase-specific, independent of whether
  HOLD can see it.
* `MIXED` outcomes are reported as such, with the number detected of 5; we do not re-run with
  more replicates to break a tie.

## 8. Limits fixed in advance

One whale data set coded by human listeners, one year per recording. The run parse is one
greedy rule (longest coverage, cells up to 8 elements); nested repetition inside a cell is
kept as the cell's content, and a different parse could split runs differently. The
permutations keep run boundaries fixed, so they can create new adjacent repeats where a
permuted count or cell meets its neighbours; the negative control checks that this does not
by itself create detection. HOLD's plug-in null leans against detection (every earlier
negative control gave p = 1.000), so DESTROYED is the conservative direction. With B = 200 the
smallest p is 0.005.
