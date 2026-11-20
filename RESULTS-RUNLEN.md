# RESULTS-RUNLEN: humpback song's extra structure survives scrambling how often and where phrases are repeated

song-zipf-test, graded 2026-11-20 by MV2 of Munim, Inc. (mv2@munimtech.com). Registration:
[RUNLEN-PREREG.md](RUNLEN-PREREG.md) (registered before the job ran; the job found it public at
2026-11-20T04:07:35Z before reading any data). Job `song-zipf-runlen-v1` (python 3.12.16, 1,876 s
of analysis). Raw output: [results/runlen/runlen_results.json](results/runlen/runlen_results.json).
Every fixed line below is re-derived from the raw output by
[test_runlen_results.py](test_runlen_results.py), which was published before the job ran. Made
with AI agents working in MV2's name; no human expert has checked this yet. Text CC BY 4.0.

## What we found

1. **How many times the whale sings a phrase does not carry the structure beyond second order.**
   We parsed each year's song into runs (a phrase cell of 1-8 elements and the number of times it
   is sung in a row; 4,919 repeated runs in all) and permuted the copy counts, first among runs
   of the same cell (M1) and then among runs of any cell of the same length (M2). The held-out
   test of [RESULTS-HOLD.md](RESULTS-HOLD.md), unchanged, still found structure beyond a
   second-order chain in 5 of 5 data sets of each kind (every p at most 0.0100). R1:
   `COUNTS_NOT_NEEDED`. This refutes the hypothesis we wrote down after HOLDC, that regular run
   lengths carry the signal.
2. **Which phrase is repeated where does not carry it either.** Swapping the repeated phrases of
   2-8 elements among runs of the same cell length (M3; 0.8554 of the runs it acts on changed)
   left the signal in place in 5 of 5 data sets. R2: `PLACEMENT_NOT_NEEDED`.
3. **Copy counts are phrase-specific.** Read on its own (R3): how many times a run is sung depends
   on which phrase it is, beyond what the phrase's length explains (2647.544 against 1837.574,
   sd 34.812, in 2,000 permutations; p = 0.0005). Whale biologists have long noted that some
   themes are repeated more than others; this puts a permutation test on that at the level of the
   repeated cell.
4. **The pipeline and the control held.** The run parse expands back to the song exactly, and the
   unpermuted song reproduces RESULTS-HOLD.md's gain and p to the last digit. A second-order
   surrogate of the whale, permuted by M3, was not detected (p = 1.0000): the permutations do not
   create structure by themselves.

**Reading, by the rules fixed in RUNLEN-PREREG.md section 7.** With `COUNTS_NOT_NEEDED` and
`PLACEMENT_NOT_NEEDED`, the beyond-second-order signal survives scrambling both how many times and
where phrases are repeated. By elimination it lies in the repertoire of repeated multi-element
phrases themselves: recurring cells of three or more elements, sung as runs, whose internal order
a chain that remembers two elements cannot hold but a longer context can. Together with
[RESULTS-HOLDC.md](RESULTS-HOLDC.md) (with repeats collapsed, nothing beyond second order is left):
the extra structure HOLD found is phrase structure, the textbook unit of humpback song (Payne &
McVay 1971), made visible to a held-out test because each phrase is sung many times. It is not
evidence of word-like ordering. None of the three permutations scrambles the element order
inside a phrase, so "it lies in the phrases" is a reading by elimination, not a direct test.

**Predictions.** All 7 came true (Brier 0.107). The least confident, Q5 (M3 survives, prior 0.45),
came true.

**Unpredicted, and not registered (exploratory).** In units of each test's null sd (the z column
below; M0's own z, computed by hand from its fields, is +6.10): scrambling which phrase is
repeated where made the signal stronger, not weaker (M3: +6.62 to +11.71), while scrambling copy
counts within cell length weakened it (M2: +2.22 to +4.21) and scrambling them within cell barely
did (M1: +3.94 to +4.98). Each permuted data set gets its own fitted null, so these z values mix
changes in the song with changes in how well a second-order chain fits it; we draw no conclusion
from them.

## Fixed lines (test_runlen_results.render_md_lines)

Job status: `ok`; whale data status: `ok`

M0, the unpermuted song with HOLD's seed: runs expand back to the song exactly: yes; mean held-out gain **-0.0490** bits per element against -0.0783 (sd 0.0048) for second-order surrogates (B = 200), p = **0.0050**; identical to RESULTS-HOLD.md's gain and p: yes; **`PIPELINE_OK`**

Negative control (M3 on one second-order surrogate of the whale): 1,778 of 2,118 repeated runs changed; mean gain -0.1326 against -0.1107 (B = 200), p = 1.0000, label `NOT_DETECTED`

Count specificity (cell and copy count given cell length, over repeated runs, summed over years): 2647.544 against 1837.574 (sd 34.812) after M2 permutations (B = 2,000), p = **0.0005**, **`COUNTS_CELL_SPECIFIC`**

### The whale's runs, year by year

| year | elements | runs | repeated runs | share of elements in repeated runs | distinct repeated cells | repeated runs of recurring cells | mean copies | max copies | share at a cell's modal count |
|---|---|---|---|---|---|---|---|---|---|
| 2010 | 1,053 | 306 | 135 | 0.8376 | 48 | 108 | 3.56 | 17 | 0.7037 |
| 2011 | 2,028 | 722 | 277 | 0.7806 | 92 | 224 | 2.82 | 12 | 0.7942 |
| 2012 | 3,351 | 1,219 | 364 | 0.7449 | 106 | 298 | 2.46 | 8 | 0.8214 |
| 2013 | 2,664 | 932 | 297 | 0.7616 | 89 | 237 | 2.62 | 28 | 0.8653 |
| 2014 | 5,765 | 3,116 | 606 | 0.5646 | 126 | 536 | 2.57 | 14 | 0.7475 |
| 2015 | 14,429 | 3,610 | 1,355 | 0.8437 | 222 | 1,237 | 4.39 | 42 | 0.6435 |
| 2016 | 7,282 | 3,349 | 766 | 0.6453 | 170 | 674 | 2.87 | 12 | 0.7010 |
| 2017 | 9,177 | 5,082 | 1,119 | 0.5682 | 172 | 1,028 | 2.39 | 9 | 0.7909 |

(A run is a cell of 1-8 elements with its number of consecutive copies, parsed greedily as in
RUNLEN-PREREG.md section 3; a repeated run has 2 or more copies.)

### Permuted data sets (held-out test against 200 second-order surrogates each)

| kind | replicate | seed | repeated runs changed | gain | null mean | z | p | label |
|---|---|---|---|---|---|---|---|---|
| M1 | 0 | 20262132 | 1,620 of 4,919 | -0.0564 | -0.0780 | +4.60 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M2 | 0 | 20263132 | 2,255 of 4,919 | -0.0662 | -0.0839 | +3.58 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M3 | 0 | 20264132 | 2,184 of 2,544 | -0.0807 | -0.1190 | +7.12 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M1 | 1 | 20262142 | 1,648 of 4,919 | -0.0552 | -0.0778 | +4.98 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M2 | 1 | 20263142 | 2,283 of 4,919 | -0.0640 | -0.0833 | +4.21 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M3 | 1 | 20264142 | 2,159 of 2,544 | -0.0837 | -0.1180 | +6.62 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M1 | 2 | 20262152 | 1,617 of 4,919 | -0.0581 | -0.0784 | +3.94 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M2 | 2 | 20263152 | 2,251 of 4,919 | -0.0723 | -0.0829 | +2.22 | 0.0100 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M3 | 2 | 20264152 | 2,161 of 2,544 | -0.0749 | -0.1200 | +9.93 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M1 | 3 | 20262162 | 1,661 of 4,919 | -0.0563 | -0.0786 | +4.72 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M2 | 3 | 20263162 | 2,322 of 4,919 | -0.0630 | -0.0836 | +4.04 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M3 | 3 | 20264162 | 2,190 of 2,544 | -0.0775 | -0.1182 | +8.33 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M1 | 4 | 20262172 | 1,651 of 4,919 | -0.0551 | -0.0779 | +4.94 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M2 | 4 | 20263172 | 2,251 of 4,919 | -0.0668 | -0.0835 | +3.47 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |
| M3 | 4 | 20264172 | 2,187 of 2,544 | -0.0661 | -0.1188 | +11.71 | 0.0050 | `BEYOND_SECOND_ORDER_HELDOUT` |

(Gain in bits per element: held-out cross-entropy at order 2 minus the best of orders 3-5,
averaged over the 8 years; z = (gain - null mean) / null sd. M3 acts only on repeated runs of
cells with 2 or more elements.)

### Verdicts

M1 (copy counts within cell): detected in 5 of 5 permuted data sets; share of repeated runs changed 0.3333; verdict **`SURVIVES`**

M2 (copy counts within cell length): detected in 5 of 5 permuted data sets; share of repeated runs changed 0.4620; verdict **`SURVIVES`**

M3 (repeated phrases within cell length): detected in 5 of 5 permuted data sets; share of repeated runs changed 0.8554; verdict **`SURVIVES`**

Mean held-out gain of the 5 M2 data sets -0.0665 against M0's -0.0490

### Rules

Pipeline: **`PIPELINE_OK`**; control: **`CONTROL_OK`** (negative control detected: no)

R1 copy counts: **`COUNTS_NOT_NEEDED`**

R2 placement of repeated phrases: **`PLACEMENT_NOT_NEEDED`**

R3 count specificity: **`COUNTS_CELL_SPECIFIC`**

### Predictions

7 of 7 graded predictions true

Brier score **0.107**

| prediction | text | prior | outcome |
|---|---|---|---|
| Q1 | the pipeline check passes (`PIPELINE_OK`) | 0.95 | **true** |
| Q2 | copy counts are cell-specific beyond cell length (count specificity p < 0.05) | 0.75 | **true** |
| Q3 | M1 (copy counts within cell) SURVIVES | 0.70 | **true** |
| Q4 | M2 (copy counts within cell length) SURVIVES | 0.60 | **true** |
| Q5 | M3 (repeated phrases within cell length) SURVIVES | 0.45 | **true** |
| Q6 | the negative control is not detected | 0.90 | **true** |
| Q7 | the mean held-out gain of the five M2 data sets is below M0's | 0.65 | **true** |

## Limits

One whale data set (New Caledonia, 2010-2017), coded by human listeners, each year treated as one
recording and its recordings as bouts. The run parse is one greedy rule (longest coverage, cells
of up to 8 elements, ties to the shorter cell); another parse could split runs differently. The
permutations keep run boundaries fixed, so they can create new adjacent repeats where a permuted
count or phrase meets its neighbours; the negative control shows this does not by itself create
detection. With B = 200 the smallest p is 0.005, and the plug-in null leans against detection, so
"survives" is the conservative direction. No permutation here scrambles the order of elements
inside a phrase; the reading that the signal lies in the phrases' internal order is by
elimination.
