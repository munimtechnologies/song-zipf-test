# RESULTS-RUNS: whale song's "words" are largely repeats

song-zipf-test, graded 2026-11-19 by MV2 of Munim, Inc. (mv2@munimtech.com). Registration:
[RUNS-PREREG.md](RUNS-PREREG.md) (registered before the job ran, and before the HOLD result
existed). Job `song-zipf-runs-v1` (python 3.12, 834 s). Raw output:
[results/runs/runs_results.json](results/runs/runs_results.json). Every fixed line below is
re-derived from the raw output by [test_runs_results.py](test_runs_results.py), which was
published before the job ran. Made with AI agents working in MV2's name; no human expert has
checked this yet. Text CC BY 4.0.

## What we found

1. **Humpback song repeats itself far more than its own second-order rules do.** Collapsing
   every within-recording tandem repeat (a cell of 1-8 elements sung twice or more in a row)
   to one copy removes 0.6290 of the whale's elements on average over the 8 years. Second-order
   Markov surrogates of the same years lose 0.4982 (sd 0.0072); none of 200 reached the real
   value (p = 0.005). Real English goes the other way: collapsing removes about 1% of its
   phonemes, less than its own second-order surrogates (NOT_BEYOND in 6 of 6 replicates).
2. **The most frequent whale "words" are repetition cells more often than chance.** Of the ten
   most frequent chunks in each year (80 in all; the paper's Table S2 rule), 35 contain an
   immediate repeat (x x) or an alternation (x y x), against 26.89 in surrogates (p = 0.005).
   Our recount matches the hand count of 35 that we made from the paper's Table S2 before
   registering.
3. **With repeats removed, the Zipf test sees nothing beyond a first-order chain, but it
   cannot see much at this size.** The collapsed song's Zipf R^2 falls from 0.9303 to 0.8962.
   A first-order chain generated under the same collapse rule matches it (p = 0.0659), and a
   second-order chain makes song more Zipfian than the real song (null 0.9216, p = 1.0000).
   But collapsing leaves only 248 to 4,403 elements per year, and the registered power check
   failed: held out, order 2 never beat order 1 in any collapsed year (0 of 8). So the label is
   `EXPLAINED_BY_FIRST_ORDER_UNDERPOWERED`: the Zipf test cannot decide whether anything
   beyond repetition is left. Real English, collapsed the same way, still beats the second-order
   chain in 6 of 6 replicates, and 0 of 3 whale negative controls did.

**What this means for the whale Zipf claim.** The "language-like" Zipf law of humpback song
(Arnon et al. 2025, *Science* 387:649) is computed on chunks that are, to a large and
measurable degree, repeated cells, and the song's repetition is far beyond what the
second-order chain that matches its Zipf law produces. Removing the repeats weakens the Zipf
fit and leaves nothing the Zipf statistic can tell from a first-order chain. Together with
[RESULTS-HOLD.md](RESULTS-HOLD.md), which found structure beyond second order on held-out
song, the simplest reading is that the extra structure is phrase repetition, which whale
biologists have described since Payne & McVay (1971). That reading is not yet tested with the
stronger held-out instrument: [HOLDC-PREREG.md](HOLDC-PREREG.md) registers HOLD on the
collapsed song, with an English control at the same size and a repetition-only control.

**Predictions.** 7 of 9 came true (Brier 0.119). The two failures: the collapsed whale was not
beyond second order (P5, prior 0.30) and the power check did not pass (P8, prior 0.35).

**Unpredicted.** English repeats itself less than its own second-order chain (T2 p = 1.0000
in 4 of 6 replicates): a phoneme-level second-order chain makes more immediate repeats than
real speech. In the whale negative controls, collapsing makes D1 favour order 1 in 7 of 8
years, as in the real collapsed whale; at these sizes D1 has little power for any song.

## Fixed lines (test_runs_results.render_md_lines)

Job status: `ok`; whale data status: `ok`

Whale T2: **0.6290** of elements removed by collapsing (null mean 0.4982, sd 0.0072), p = **0.0050**, label **`REPETITION_BEYOND_SECOND_ORDER`**

Whale T3: **35 of 80** top-ten chunks contain x x or x y x (null mean 26.89, sd 2.32), p = **0.0050**, label **`MOTIFS_BEYOND_SECOND_ORDER`**

Whale T1 (theta 0.5): collapsed R^2 **0.8962**; order-1 null mean 0.8860, p = 0.0659; order-2 null mean 0.9216, p = **1.0000**; label **`EXPLAINED_BY_FIRST_ORDER`**

Whale D1 (order 2 minus order 1, held out) favours order 2 in **0 of 8** collapsed years and 1 of 8 original years

Null lengths as a share of the real collapsed length: order 1 mean 1.0000 (min 1.0000), order 2 mean 1.0000 (min 1.0000)

### Whale, year by year

| year | elements | after collapsing | share removed | D1 original | D1 collapsed | motif chunks in top ten |
|---|---|---|---|---|---|---|
| 2010 | 1,053 | 248 | 0.7645 | -0.0214 | -0.2034 | 7 of 10 |
| 2011 | 2,028 | 766 | 0.6223 | -0.0849 | -0.3951 | 3 of 10 |
| 2012 | 3,351 | 1,233 | 0.6321 | -0.1385 | -0.3857 | 5 of 10 |
| 2013 | 2,664 | 908 | 0.6592 | -0.0357 | -0.4153 | 1 of 10 |
| 2014 | 5,765 | 3,141 | 0.4552 | -0.1889 | -0.4326 | 1 of 10 |
| 2015 | 14,429 | 2,926 | 0.7972 | +0.0945 | -0.1513 | 8 of 10 |
| 2016 | 7,282 | 3,046 | 0.5817 | -0.1438 | -0.4688 | 6 of 10 |
| 2017 | 9,177 | 4,403 | 0.5202 | -0.1148 | -0.3833 | 4 of 10 |

### Whale, Zipf R^2 by threshold (collapse-consistent nulls)

| theta | original R^2 | collapsed R^2 | order-1 null mean | p | order-2 null mean | p |
|---|---|---|---|---|---|---|
| 0.3 | 0.8584 | 0.7528 | 0.7320 | 0.1399 | 0.8214 | 1.0000 |
| 0.5 | 0.9303 | 0.8962 | 0.8860 | 0.0659 | 0.9216 | 1.0000 |
| 0.7 | 0.9513 | 0.9279 | 0.9259 | 0.3087 | 0.9394 | 0.9930 |

### Whale, the ten most frequent chunks of the original song (theta 0.5)

| year | ten most frequent chunks of the original song (theta 0.5) |
|---|---|
| 2010 | `gr gr m`; `m ac ac ac`; `m`; `v ba`; `ac(l) m`; `dm ngr ngr`; `m(pul) ngr(s) ngr(s)`; `agr agr m`; `m ac ac ac ac`; `ngr(s) ngr(s) m` |
| 2011 | `ba p(l) ba`; `dws m`; `m(s) dws`; `gr(s) ba`; `c m`; `m`; `m(s) dws m`; `m(s)`; `ngr ngr m`; `m ba ba` |
| 2012 | `w gr w`; `gr ba`; `gr(pul) m(pul) gr`; `m gr`; `w gr w gr`; `ba gr ba`; `ba`; `ahq ba`; `gw hs(pul) hs(pul)`; `ba lb gw hs(pul) hs(pul)` |
| 2013 | `lb sn lb sn hs(pul) ba lb`; `aws(s) sq`; `lb`; `hs(pul) ba lb`; `ba lb`; `dsq aws(s)`; `agr(l) sq`; `agr(s) aws(s) sq`; `ba`; `gr(s) hs(pul) ba lb` |
| 2014 | `agr(pul-s) w`; `agr(pul) w`; `ac be ac`; `aws(s) agr(pul-s) w`; `gr(l) ac`; `ac`; `dgr`; `gr(s)-modhc gr(s)-nc(s)`; `gr(s)-nc(s) gr(s)-dc`; `ti(a) w` |
| 2015 | `gr(s)-dws(s) sq sq sq`; `gr(s)-dws(s) gr gr(s)-dws(s) sq sq sq`; `gr(s)-dws(s)`; `gr(s)-dws(s) ba ba`; `gr`; `gw(l) gw(l) gr`; `gr(s)-dws gr gr(s)-dws`; `gr(s)-dws(s) gr gr(s)-dws(s) ba ba`; `gr(s)-dws(s) sq sq sq sq`; `gr(s)-dws(s) sq sq` |
| 2016 | `dm(l) dm`; `gr(s)`; `hsq w`; `ngr(s) ngr(s) ngr(s) ngr(s)`; `dm`; `dm ngr(s) ngr(s) ngr(s) ngr(s)`; `gr(s)-aws nm nm`; `gr(s)-aws nm nm sn gr(s)-aws am(l)`; `gr(s)-uws(s) ngr(s) ngr(s)`; `ngr(s) ngr(s) ngr(s)` |
| 2017 | `gw(low) gr`; `ns ns`; `dhq w`; `ds(s) gr`; `hq w`; `gw gr`; `hq sq`; `gr gw(low) gr`; `sn gr(s) gr(s)`; `ns ns gr gw(low) gr` |

### Negative controls (each whale year replaced by a second-order surrogate of itself)

| negative control | share removed | T2 p | T2 label | collapsed R^2 | p order 1 | p order 2 | T1 label | D1 collapsed favours order 2 |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.4999 | 0.7525 | `NOT_BEYOND` | 0.9230 | 0.0050 | 0.9801 | `EXPLAINED_BY_SECOND_ORDER` | 1 of 8 |
| 1 | 0.5038 | 0.8119 | `NOT_BEYOND` | 0.9248 | 0.0050 | 0.9453 | `EXPLAINED_BY_SECOND_ORDER` | 1 of 8 |
| 2 | 0.4905 | 0.8911 | `NOT_BEYOND` | 0.9288 | 0.0050 | 0.7015 | `EXPLAINED_BY_SECOND_ORDER` | 1 of 8 |

### English positive control (Brent-Ratner child-directed English, 8 recordings per replicate)

| U | rep | phonemes per recording | share removed | null share | T2 p | T2 label | collapsed R^2 | p order 1 | p order 2 | T1 label | D1 collapsed favours order 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 280 | 0 | 2,566 | 0.0097 | 0.0130 | 1.0000 | `NOT_BEYOND` | 0.9439 | 0.0099 | 0.0099 | `BEYOND_SECOND_ORDER_AFTER_COLLAPSE` | 6 of 8 |
| 280 | 1 | 2,973 | 0.0065 | 0.0103 | 1.0000 | `NOT_BEYOND` | 0.9398 | 0.0099 | 0.0099 | `BEYOND_SECOND_ORDER_AFTER_COLLAPSE` | 5 of 8 |
| 280 | 2 | 2,870 | 0.0118 | 0.0159 | 1.0000 | `NOT_BEYOND` | 0.9404 | 0.0099 | 0.0198 | `BEYOND_SECOND_ORDER_AFTER_COLLAPSE` | 8 of 8 |
| 280 | 3 | 2,573 | 0.0140 | 0.0161 | 0.8614 | `NOT_BEYOND` | 0.9423 | 0.0099 | 0.0099 | `BEYOND_SECOND_ORDER_AFTER_COLLAPSE` | 5 of 8 |
| 600 | 0 | 5,936 | 0.0082 | 0.0108 | 1.0000 | `NOT_BEYOND` | 0.9526 | 0.0099 | 0.0099 | `BEYOND_SECOND_ORDER_AFTER_COLLAPSE` | 8 of 8 |
| 600 | 1 | 5,813 | 0.0136 | 0.0148 | 0.8713 | `NOT_BEYOND` | 0.9496 | 0.0099 | 0.0099 | `BEYOND_SECOND_ORDER_AFTER_COLLAPSE` | 8 of 8 |

### Rules

Control: **`CONTROL_OK`** (English beyond second order after collapsing in 6 of 6 replicates; negative controls 0 of 3)

R1 whale repetition (T2): **`REPETITION_BEYOND_SECOND_ORDER`**

R2 whale top-chunk motifs (T3): **`MOTIFS_BEYOND_SECOND_ORDER`**

R3 whale Zipf after collapsing (T1): **`EXPLAINED_BY_FIRST_ORDER_UNDERPOWERED`**

### Predictions

7 of 9 graded predictions true

Brier score **0.119**

| prediction | text | prior | outcome |
|---|---|---|---|
| P1 | whale T2 is REPETITION_BEYOND_SECOND_ORDER | 0.90 | **true** |
| P2 | English T2 is NOT_BEYOND in at least 4 of 6 replicates | 0.60 | **true** |
| P3 | collapsing removes at least half of the whale's elements (mean share >= 0.5) | 0.50 | **true** |
| P4 | whale T3 is MOTIFS_BEYOND_SECOND_ORDER | 0.50 | **true** |
| P5 | whale T1 is BEYOND_SECOND_ORDER_AFTER_COLLAPSE | 0.30 | **false** |
| P6 | English T1 is BEYOND_SECOND_ORDER_AFTER_COLLAPSE in at least 4 of 6 replicates | 0.75 | **true** |
| P7 | none of the 3 negative controls is BEYOND_SECOND_ORDER_AFTER_COLLAPSE | 0.80 | **true** |
| P8 | D1 favours order 2 in 5 or more of the 8 collapsed whale years | 0.35 | **false** |
| P9 | the collapsed whale R^2 at theta 0.5 is below the original 0.9303 | 0.70 | **true** |

## Limits

One whale data set coded by human listeners, each year treated as one recording; one English
corpus in phonemes. The nulls are fitted to the same data (plug-in). Collapsing shortens the
whale far more than English, so the collapsed whale is tested at a size where the power check
fails; T1 cannot decide. The period limit (8) and shortest-first deletion were fixed before any
result. T3 confirms a count we had made by hand from Table S2 before registering; its null is
new.
