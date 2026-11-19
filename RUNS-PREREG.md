# RUNS-PREREG: is whale song's Zipf law made by repeating phrase cells?

song-zipf-test, registered 2026-11-19 by MV2 of Munim, Inc. (mv2@munimtech.com), before the
job `song-zipf-runs-v1` runs. Made with AI agents working in MV2's name; no human expert has
checked this design yet. Text CC BY 4.0; code (`runs.py`, `test_runs.py`, `setup_runs.sh`)
Apache-2.0. Registered before the HOLD, XPOP and CANARY results exist.

## 1. Why

Humpback song is built from short cells (phrases) that each singer repeats many times before
moving on to the next theme (Payne & McVay 1971). Arnon et al. 2025 (*Science* 387:649) cut the
element stream where the transitional probability (TP) dips and found that the resulting chunks
follow Zipf's rank-frequency law (mean R^2 0.93). Our graded results say this law is matched by
a second-order Markov chain fitted to each year's song (RESULTS-WHALE.md: null 0.939, real
0.930, p 0.970), and that the whale data fail a power check (D1 in 1 of 8 years). Two
observations point at repetition as the common cause:

* Of the 80 chunks in the paper's own Table S2 (ten most frequent per year), 35 contain an
  immediate repeat (x x) or an alternation (x y x), and in 3 of 8 years the top ten hold the same
  cell at two or three run lengths (our hand count; DRAFT 3.8, not yet a registered test).
* Repetition can make a second-order chain hard to beat (self-loops and short cycles dominate
  its transition table) and makes 5,720 elements a year carry much less independent information
  than English at the same size.

So we ask three questions that no published test has asked: (T2) does whale song repeat itself
more than its own second-order chain does; (T3) are the most frequent "words" repetition cells
more often than the second-order chain makes them; and (T1) once every repeat is collapsed to
one copy, does the Zipf test see structure beyond a second-order chain?

## 2. Prior art

* Suzuki, Tyack & Buck 2005 (*Anim. Behav.* 69:F9) and McCowan et al. 2005 debated how Zipf
  slopes in animal repertoires should be read, with humpback song as a case. Neither removed
  repetition before the rank-frequency analysis.
* Suzuki, Buck & Tyack 2006 (*JASA* 119:1849) showed humpback song is not first-order Markov and
  has periodic structure from phrase repetition. Kershenbaum et al. 2021 (*Methods Ecol. Evol.*)
  relate Zipf's exponent to entropy.
* Charpentier 2026 (arXiv:2608.09459) calls for segmentation-aware nulls for both animal Zipf
  papers but analyses no recordings. A *Science* eLetter on Arnon et al. ("Zipf zapped") argues
  that Zipf distributions arise from randomness.
* Web searches on 2026-11-19 ("Zipf" with "repetition", "tandem repeats", "collapsed",
  humpback, animal vocal sequences) found no study that collapses tandem
  repeats before a Zipf test, or that compares the repetition in song with a fitted Markov null.

## 3. Data (all public; nothing new is downloaded)

* **Whale.** Data S2 of Arnon et al. 2025 on the job's data volume, read by
  `whale_run.parse_s2` with Gate A (song types 2010-2017; 55 recordings; 45,760 elements within
  0.5%). A year (song type) is one recording set and its recordings are the bouts, exactly as in
  the whale test. Missing data: `WHALE_DATA_MISSING`, re-run under an amendment.
* **English (positive control).** Brent-Ratner child-directed English (`cds_job.load_corpus`,
  reading gate 9,790 utterances and 95,809 phonemes). Six replicates of CDS-SIZE-PREREG.md,
  the ones in which the Zipf test detected English beyond second order (6 of 6): (U,
  replicates) = (280, 4) and (600, 2), about 2,745 and 5,874 phonemes per recording; replicate
  r of size U is 8 blocks of U utterances starting at utterance 8 r U. Bout = utterance.
* **Negative control.** Three data sets in which each whale year is replaced by one pooled
  Markov-2 surrogate of itself (`zipfseg.markov_recording`, k = 2): no structure beyond order 2
  and only the repetition that a second-order chain makes.
* **What we have already seen.** The whale and English data were analysed before with the Zipf
  statistic and D1 on the original sequences, and we counted Table S2 by hand (35 of 80). No
  statistic of collapsed song, and no repetition share, has been computed on any data set.

## 4. Collapsing repeats

`runs.collapse(bout, lmax = 8)` reads a bout left to right, appends each element, and while the
sequence ends in a tandem repeat u u with 1 <= |u| <= 8, deletes the second copy (shortest
period first). Every repeated run of a cell of up to 8 elements is kept once: "gr(s)-dws(s), sq,
sq, sq, gr(s)-dws(s), sq, sq, sq" becomes "gr(s)-dws(s), sq". The output contains no square of
period 8 or less, and collapsing is idempotent. Bouts are collapsed separately.

## 5. Tests (B, seeds and code fixed in runs.py; theta 0.5 unless said)

* **T2, repetition share.** Share of elements removed by collapsing, pooled within each set,
  then averaged over the 8 sets. Null: B = 200 Markov-2 surrogates of the ORIGINAL song
  (`markov_recording`, k = 2), collapsed the same way. p = (1 + #{null >= real}) / (1 + B).
  `REPETITION_BEYOND_SECOND_ORDER` if p < 0.05, else `NOT_BEYOND`.
* **T3, top-chunk motifs.** TP segmentation of the ORIGINAL song (Code S1 rule, theta 0.5,
  `zipfseg.segment_recording`); in each set, the ten most frequent chunks (ties by sorted
  chunk); count those containing x x or x y x, summed over sets (at most 80). Same null and B as
  T2. `MOTIFS_BEYOND_SECOND_ORDER` if p < 0.05.
* **T1, Zipf after collapsing.** Mean over sets of the Zipf R^2 of TP chunks of the COLLAPSED
  song (thetas 0.3, 0.5, 0.7; 0.5 decides). Nulls: pooled order-1 and order-2 chains fitted to the
  collapsed song (as `markov_recording`) and **generated under the same collapse rule**, element
  by element, until each bout reaches its collapsed length (at most 50 n draws). Without this,
  a chain fitted to square-free song would make squares that real collapsed song cannot contain,
  and the test would compare unlike things. B = 1,000 (whale), 200 (negative controls), 100
  (English). `BEYOND_SECOND_ORDER_AFTER_COLLAPSE` if p(order 2) < 0.05; otherwise
  `EXPLAINED_BY_SECOND_ORDER` if p(order 1) < 0.05, else `EXPLAINED_BY_FIRST_ORDER`.
* **Power check.** D1 (`zipfseg.heldout_ll`, order 2 minus order 1, add-0.5) on the collapsed
  sets. In English, a D1 majority went with detection 7 of 7 times, its absence 1 of 10
  (RESULTS-CDS-SIZE.md).
* Also reported, not tests: original and collapsed lengths per set; R^2 of original and
  collapsed song at each theta; the null length ratios; the top-ten chunks of every set.

## 6. Predictions (priors in runs.PRIORS; Brier over those that can be scored)

* P1 (0.90): whale T2 is `REPETITION_BEYOND_SECOND_ORDER`.
* P2 (0.60): English T2 is `NOT_BEYOND` in at least 4 of 6 replicates.
* P3 (0.50): collapsing removes at least half of the whale's elements (mean share >= 0.5).
* P4 (0.50): whale T3 is `MOTIFS_BEYOND_SECOND_ORDER`.
* P5 (0.30): whale T1 is `BEYOND_SECOND_ORDER_AFTER_COLLAPSE`.
* P6 (0.75): English T1 is `BEYOND_SECOND_ORDER_AFTER_COLLAPSE` in at least 4 of 6 replicates.
* P7 (0.80): none of the 3 negative controls is `BEYOND_SECOND_ORDER_AFTER_COLLAPSE`.
* P8 (0.35): D1 favours order 2 in a majority (5 or more) of the 8 collapsed whale years.
* P9 (0.70): the collapsed whale R^2 at theta 0.5 is below the original 0.9303.

## 7. Decision rules (coded in runs.grade; applied exactly as coded)

* **Control**: `CONTROL_OK` if English T1 is beyond second order in at least 4 of 6 replicates
  and at most 1 of 3 negative controls is; `CALIBRATION_INCOMPLETE` if any of the 9 did not
  run; else `CONTROL_FAILED`.
* **R1** = whale T2 label. **R2** = whale T3 label.
* **R3 whale T1**: the control label if it is not `CONTROL_OK`; else
  `BEYOND_SECOND_ORDER_AFTER_COLLAPSE` if p(order 2) < 0.05; else the T1 label followed by
  `_POWERED` if D1 favours order 2 in a majority of collapsed years, `_UNDERPOWERED` if not.

## 8. How results will be read

* R1 and R2 beyond second order: whale song repeats its cells more than its own second-order
  rules do, and the most frequent "words" are repetition cells more often than those rules
  make them. The Zipf law's top ranks would then be counting repeats.
* R3 `BEYOND_SECOND_ORDER_AFTER_COLLAPSE` with the control OK: once repeats are removed, whale
  chunk statistics carry structure a second-order chain cannot match. This would be the first
  evidence from these data, beyond the paper's own controls, for longer-range units, and we
  would say so.
* R3 `EXPLAINED_BY_..._POWERED`: with repeats removed and the power check passed, a second-order
  chain still matches the whale; with `_UNDERPOWERED`, the data cannot decide even then.
* Collapsing also removes repeats inside true words (English "mama"); English is the check that
  this does not hide real units.

## 9. Limits fixed in advance

One whale data set coded by human listeners; one English corpus in phonemes. The period limit 8
and shortest-first deletion are choices made before any result. Collapsing shortens the whale
data more than English, so T1 compares data sets of different sizes; the D1 check and the
collapse-consistent nulls are the guard. The nulls are fitted to the same data (plug-in nulls).
T3 confirms a count we made by hand before registering; its null and test are new.
