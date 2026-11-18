# PREREG-AMENDMENT-5: reading the whale data the way the authors' code does

Registered 2026-11-18 (about 11:30 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com), before any
statistic of any kind has been computed on the whale song data. Made with AI agents. Text
CC BY 4.0; code Apache-2.0.

Code: [whale_run.py](whale_run.py), tests [test_whale_run.py](test_whale_run.py). Job
`whale-test-v1`. It imports `whale_test.py` and `whale_read.py` (commit 742fd83) and
`zipfseg.py` (commit e976e63) **unchanged**. Before reading any data, the job waits until this
file is on GitHub and records its commit time.

## 1. What happened

Job `whale-stage0-v3` (2026-11-18 08:43-08:46 UTC) unpacked the supplement of Arnon et al.
2025 (*Science* 387:649) and ran the reader registered in
[PREREG-AMENDMENT-3.md](PREREG-AMENDMENT-3.md). **The reading gate was not passed, so no
statistic was computed**, as registered. The one-row-per-recording layout of Data S2 matched
Table S1 of the paper exactly in 6 of 8 years:

| | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | total |
|---|---|---|---|---|---|---|---|---|---|
| Data S2 `song_type`: recordings | 4 | 6 | 6 | 6 | 7 | **13** | **6** | 7 | 55 |
| Table S1 year: recordings | 4 | 6 | 6 | 6 | 7 | **12** | **7** | 7 | 55 |
| Data S2 `song_type`: elements | 1,053 | 2,028 | 3,351 | 2,664 | 5,765 | **14,429** | **7,282** | 9,177 | 45,749 |
| Table S1 year: elements | 1,053 | 2,028 | 3,351 | 2,664 | 5,765 | **13,251** | **8,469** | 9,179 | 45,760 |

Seen so far: these counts, the column names, and the first characters of the first seven
rows (in the job's inventory). No sub-sequence, transition probability, rank-frequency
or brevity value has been computed on whale data.

## 2. Why the gate failed, from the authors' own code

We then read Code S1 (the authors' analysis notebook, published with the paper). It reads
the same table (`whale_data.csv`; columns `song_type`, `string`, ...) and **groups everything
by `song_type`**: "We refer to 'song types' here for historical reasons. For our purposes
they are synonymous with 'years'." Table S1 counts recordings by calendar year. The two
differ mainly by one recording of about 1,180 elements, grouped with the 2015 song type but
counted under 2016 in Table S1 (that is our inference, not something the paper states),
plus 11 elements overall (45,749 against 45,760). Our reader
was right to stop. Its gate checked the wrong grouping.

## 3. The new reading and two gates

* **Reading.** Data S2, one row per recording, grouped by `song_type`. The `string` cell is
  parsed with `ast.literal_eval` (Code S1 uses `eval` on the same column), so element codes
  are kept exactly as written. Recordings stay separate; no transition crosses a recording
  boundary, as in Code S1.
* **Gate A (data).** Every row parses to a list of strings; the song types are exactly
  2010-2017; recordings per song type are 4, 6, 6, 6, 7, 13, 6, 7; total elements are within
  0.5% of Table S1's 45,760. If Gate A fails, nothing is computed.
* **Gate B (exact reproduction of Code S1), stricter than the old gate.** Code S1's output is
  deterministic for the real data. At theta 0.5 it prints a mean sub-sequence Zipf R^2 of
  **0.9302888665216734**, and its brevity model has **3,386** observations (one per song type
  and sub-sequence). Gate B passes if our mean R^2 is within 1e-6 of that value **and** our
  number of (song type, sub-sequence) types is exactly 3,386. If Gate B fails, everything is
  still computed and published as "our implementation on their data", **with no headline**
  (the same rule as PREREG-AMENDMENT-3 section 5.2), and we look for the difference.
  The sound-element Zipf R^2 (paper: 0.87) is reported but is not part of the gate.

## 4. One switch that Amendment 3 fixed in advance

PREREG-AMENDMENT-3 graded brevity on two statistics: `pool` (one point per sub-sequence,
counts summed over years) and `year` (one point per year and sub-sequence). It said: "when
Code S1 is read, the one it uses is the one compared with 0.62." Code S1 builds its brevity
data with one row per (song type, sub-sequence) (`lengths()`, 3,386 rows over 8 song types),
and its Figure 3 plots those rows. **So `year` is now the primary brevity statistic**, and
`pool` is reported as the alternate. The predictions do not change.

Code S1 does not compute the R^2 = 0.62 or its z scores (37.57, 13.92). It fits a Poisson
mixed model (length coefficient -0.120, z = -29.5). We keep the registered R^2 statistic.
CALIB-3 showed that a significant Poisson slope on these chunks is expected even from
wordless and shuffled song.

## 5. Everything else is unchanged

Runs, nulls, B, seed, time limit, predictions S-W, W1-W6, N1-N6 with their priors, labels,
the Table S2 check, D1, and the calibration conditions are those of PREREG-AMENDMENT-3. The
calibrations have now been graded, so their conditions are applied mechanically:

* **Zipf** (CALIB-2: K5 true, K6 false). A `BEYOND_SECOND_ORDER` label can be a headline. An
  `EXPLAINED_BY_...` label is reported as `NOT_DISTINGUISHABLE` (the second-order test has no
  power against clean words at whale size).
* **Brevity** (CALIB-4: Q10 true, Q11 true). Both kinds of label stand as registered.
* No headline unless N1 (Table S2 reproduced in at least 6 of 8 years) **and** Gate B hold.

One new prediction, for the Brier score: **G1**: Gate B passes (prior 0.70).

## 6. The wow, either way

* If whale song's Zipf and brevity fits **beat a second-order Markov chain fitted to each
  year's own element transitions**, the evidence for word-like units in whale song becomes
  far stronger than the paper itself could show. Its only controls (shuffle, rotation) are
  passed by wordless song (CALIB-1, -2, -4).
* If a first- or second-order chain matches them, the "language-like" statistics of
  humpback song are a property of element-to-element transitions, as we found for the finch
  (RESULTS-FINCH.md).
* CALIB-4 found that no synthetic source, with or without words, came near the whale's
  brevity R^2 of 0.62 (wordless 0.09-0.17, words 0.21-0.45). Whether a Markov chain fitted to
  the real song reaches it is a direct test of whether that number needs units at all.
