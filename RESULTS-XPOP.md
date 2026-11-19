# RESULTS-XPOP: the finch Zipf test in 15 other birds, at full size (graded 2026-11-19)

Pre-registration: [XPOP-PREREG.md](XPOP-PREREG.md) (2026-11-18), amended before any data were
downloaded by [XPOP-AMENDMENT-1.md](XPOP-AMENDMENT-1.md). Job `song-zipf-xpop-v2` ran on
2026-11-19 from 16:50 to 17:01 UTC (python 3.12.16; unchanged `zipfseg.py` 742fd83, sha256
25002193...ddf5; registration sha256 edd5d0e7...722d). Raw output:
[results/xpop/xpop_results.json](results/xpop/xpop_results.json). Grader, published before
the job ran (d89b7ad): `test_xpop_results.py`. It re-derives every gate, label, prediction,
rule and the Brier score below from the raw output with its own code, and checks that this
file prints the lines it fixed in advance.

MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents; no human expert has checked this
yet. Text CC BY 4.0, code Apache-2.0.

## Headline, in one paragraph

**Provisional** (reading gate K failed; see below), so by the pre-registration no headline is
drawn from it. What the graded numbers say: at about 20,000 notes per bird, Kirby et al.'s
"above the bigram" result did **not** replicate in either independent dataset (rule X1
`ABOVE_BIGRAM_FAILS`). In the 11 Koumura and Okanoya birds the real song's chunk inventory is
**less** Zipfian than every structured null, bigram and Markov orders 1 to 3 alike (z from
-8.3 to -16.3). In the 4 Nicholson, Queen and Sober birds (gate passed) the real song is level
with the bigram null (gap +0.000, p = 0.468) and with a first-order chain (p = 0.358). Yet on
held-out song a third-order chain predicts better than a second-order one in 11 of 11 Koumura
birds. As in the whale data, the Zipf-of-chunks statistic misses sequence structure that a
held-out likelihood sees plainly. 4 of 11 registered predictions came true (Brier 0.331).

## Reading gates

Gate K: **fail**
Gate N: **pass**

Gate K required 11 birds, a mean of 17,930.9 notes per bird within 5%, and a mean of 8.1 note
classes within 0.5 (the dataset paper's own figures). We read 11 birds and 8.45 classes per
bird (pass), but 19,548.8 notes per bird, 9.0% above the paper's figure (the limit is 5%).
The paper (Koumura and Okanoya 2016, PLoS ONE 11:e0159188) reports 17,930.9 +/- 8,941.8
notes, so our mean lies within 0.2 standard deviations of theirs, but the gate is the gate.
We do not know the cause. Candidates: the published annotation may include notes the paper's
count left out (for example segments shorter than three notes, or notes marked unclassifiable),
or the annotation was revised after the paper. Every downloaded file matched its listed
size. Gate N (4 birds, each at least 5,000 syllables, at most 1% bad files) passed: 1,046
files, 0 bad, 0 Mac `._` files skipped.

Provisional (a reading gate failed): **yes**

## Data as read

| data | recordings (birds) | bouts | notes | transitions | longest bout |
|---|---|---|---|---|---|
| K | 11 | 3,684 | 215,037 | 211,353 | 200 |
| Kraw | 11 | 15,391 | 215,037 | 199,646 | 16 |
| N | 4 | 1,844 | 80,283 | 78,439 | 237 |
| KS | 11 | 150 | 7,877 | 7,727 | 136 |
| NS | 4 | 93 | 2,878 | 2,785 | 132 |

K: Koumura and Okanoya, sequences rejoined into songs (gap < 300 ms); Kraw: each annotated
sequence as its own bout (at most 15 notes, as the authors cut them); N: Nicholson, Queen and
Sober, about 20,000 syllables per bird; KS and NS: each bird's first bouts up to Kirby et al.'s
recording size (at least 666 transitions).

## Labels (section 4 rule; theta is the transitional-probability cutting threshold)

| data | theta | label |
|---|---|---|
| K | 0.3 | `EXPLAINED_BY_THIRD_ORDER` |
| K | 0.5 | `EXPLAINED_BY_FIRST_ORDER` |
| K | 0.7 | `EXPLAINED_BY_FIRST_ORDER` |
| KS | 0.5 | `EXPLAINED_BY_FIRST_ORDER` |
| Kraw | 0.5 | `EXPLAINED_BY_FIRST_ORDER` |
| N | 0.3 | `BEYOND_THIRD_ORDER` |
| N | 0.5 | `BEYOND_THIRD_ORDER` |
| N | 0.7 | `EXPLAINED_BY_FIRST_ORDER` |
| NS | 0.5 | `BEYOND_SECOND_ORDER` |

**Read the N labels with care (not predicted).** The label rule checks the third-order null
first and assumes that higher-order chains come closer to the real song. In N at theta 0.5
they do not: the first-order chain's inventories are the most Zipfian (null mean 0.947), and
the second- and third-order chains' are less so (0.940 and 0.942). The real song (0.951)
beats the latter two by 0.011 and 0.008 but not the first-order chain or the bigram null. So
`BEYOND_THIRD_ORDER` here does not mean structure that no simple chain reproduces; it means
the Zipf statistic is not monotone in chain order on these data. We do not read it as
evidence of word-like units.

## Every null, every block

Columns: data, theta, null, real mean Zipf R^2, null mean R^2, gap (real minus null), z,
one-sided p (null >= real, +1 correction), number of null data sets.

| data | theta | null | real R^2 | null mean R^2 | gap | z | p | nulls |
|---|---|---|---|---|---|---|---|---|
| K | 0.3 | shuffle | 0.898 | 0.593 | +0.304 | 13.97 | 0.020 | 50 |
| K | 0.3 | rotate | 0.898 | 0.856 | +0.041 | 8.70 | 0.020 | 50 |
| K | 0.3 | bigram_within | 0.898 | 0.843 | +0.054 | 6.67 | 0.020 | 50 |
| K | 0.3 | markov1_pooled | 0.898 | 0.809 | +0.089 | 6.32 | 0.020 | 50 |
| K | 0.3 | markov2_pooled | 0.898 | 0.878 | +0.020 | 2.67 | 0.020 | 50 |
| K | 0.3 | markov3_pooled | 0.898 | 0.897 | +0.000 | 0.03 | 0.529 | 50 |
| K | 0.5 | shuffle | 0.906 | 0.734 | +0.172 | 26.49 | 0.005 | 200 |
| K | 0.5 | rotate | 0.906 | 0.926 | -0.020 | -14.16 | 1.000 | 200 |
| K | 0.5 | bigram_within | 0.906 | 0.942 | -0.036 | -10.44 | 1.000 | 200 |
| K | 0.5 | markov1_pooled | 0.906 | 0.933 | -0.027 | -8.34 | 1.000 | 200 |
| K | 0.5 | markov2_pooled | 0.906 | 0.936 | -0.030 | -16.34 | 1.000 | 200 |
| K | 0.5 | markov3_pooled | 0.906 | 0.939 | -0.033 | -16.30 | 1.000 | 200 |
| K | 0.7 | shuffle | 0.908 | 0.889 | +0.019 | 7.21 | 0.020 | 50 |
| K | 0.7 | rotate | 0.908 | 0.932 | -0.025 | -20.05 | 1.000 | 50 |
| K | 0.7 | bigram_within | 0.908 | 0.943 | -0.035 | -14.33 | 1.000 | 50 |
| K | 0.7 | markov1_pooled | 0.908 | 0.935 | -0.027 | -13.71 | 1.000 | 50 |
| K | 0.7 | markov2_pooled | 0.908 | 0.931 | -0.023 | -7.66 | 1.000 | 50 |
| K | 0.7 | markov3_pooled | 0.908 | 0.933 | -0.025 | -8.61 | 1.000 | 50 |
| KS | 0.5 | shuffle | 0.898 | 0.647 | +0.251 | 10.64 | 0.001 | 1000 |
| KS | 0.5 | rotate | 0.898 | 0.790 | +0.109 | 7.95 | 0.001 | 1000 |
| KS | 0.5 | bigram_within | 0.898 | 0.874 | +0.024 | 1.57 | 0.043 | 1000 |
| KS | 0.5 | markov1_pooled | 0.898 | 0.878 | +0.020 | 1.40 | 0.057 | 1000 |
| KS | 0.5 | markov2_pooled | 0.898 | 0.909 | -0.011 | -1.08 | 0.850 | 1000 |
| Kraw | 0.5 | shuffle | 0.881 | 0.826 | +0.055 | 8.06 | 0.020 | 50 |
| Kraw | 0.5 | rotate | 0.881 | 0.931 | -0.050 | -33.80 | 1.000 | 50 |
| Kraw | 0.5 | bigram_within | 0.881 | 0.922 | -0.041 | -13.24 | 1.000 | 50 |
| Kraw | 0.5 | markov1_pooled | 0.881 | 0.918 | -0.037 | -13.38 | 1.000 | 50 |
| Kraw | 0.5 | markov2_pooled | 0.881 | 0.917 | -0.036 | -16.34 | 1.000 | 50 |
| Kraw | 0.5 | markov3_pooled | 0.881 | 0.914 | -0.032 | -15.79 | 1.000 | 50 |
| N | 0.3 | shuffle | 0.942 | 0.509 | +0.433 | 24.96 | 0.020 | 50 |
| N | 0.3 | rotate | 0.942 | 0.843 | +0.099 | 13.12 | 0.020 | 50 |
| N | 0.3 | bigram_within | 0.942 | 0.848 | +0.094 | 13.64 | 0.020 | 50 |
| N | 0.3 | markov1_pooled | 0.942 | 0.832 | +0.110 | 14.66 | 0.020 | 50 |
| N | 0.3 | markov2_pooled | 0.942 | 0.929 | +0.013 | 4.66 | 0.020 | 50 |
| N | 0.3 | markov3_pooled | 0.942 | 0.930 | +0.012 | 4.64 | 0.020 | 50 |
| N | 0.5 | shuffle | 0.951 | 0.773 | +0.178 | 22.68 | 0.005 | 200 |
| N | 0.5 | rotate | 0.951 | 0.923 | +0.027 | 10.98 | 0.005 | 200 |
| N | 0.5 | bigram_within | 0.951 | 0.950 | +0.000 | 0.06 | 0.468 | 200 |
| N | 0.5 | markov1_pooled | 0.951 | 0.947 | +0.004 | 0.41 | 0.358 | 200 |
| N | 0.5 | markov2_pooled | 0.951 | 0.940 | +0.011 | 3.46 | 0.005 | 200 |
| N | 0.5 | markov3_pooled | 0.951 | 0.942 | +0.008 | 2.75 | 0.005 | 200 |
| N | 0.7 | shuffle | 0.923 | 0.879 | +0.044 | 11.07 | 0.020 | 50 |
| N | 0.7 | rotate | 0.923 | 0.921 | +0.002 | 1.26 | 0.157 | 50 |
| N | 0.7 | bigram_within | 0.923 | 0.957 | -0.034 | -12.94 | 1.000 | 50 |
| N | 0.7 | markov1_pooled | 0.923 | 0.957 | -0.034 | -14.56 | 1.000 | 50 |
| N | 0.7 | markov2_pooled | 0.923 | 0.924 | -0.000 | -0.07 | 0.608 | 50 |
| N | 0.7 | markov3_pooled | 0.923 | 0.919 | +0.004 | 0.88 | 0.216 | 50 |
| NS | 0.5 | shuffle | 0.938 | 0.685 | +0.253 | 7.98 | 0.001 | 1000 |
| NS | 0.5 | rotate | 0.938 | 0.723 | +0.215 | 6.49 | 0.001 | 1000 |
| NS | 0.5 | bigram_within | 0.938 | 0.860 | +0.078 | 2.86 | 0.001 | 1000 |
| NS | 0.5 | markov1_pooled | 0.938 | 0.889 | +0.049 | 1.83 | 0.001 | 1000 |
| NS | 0.5 | markov2_pooled | 0.938 | 0.907 | +0.031 | 2.39 | 0.001 | 1000 |

With 50 null sets the smallest possible p is 0.020; with 200 it is 0.005; with 1000, 0.001.
The robustness (theta 0.3, 0.7) and sensitivity (Kraw) blocks all ran within the time budget.

## Held-out check (leave one bout out, additive smoothing 0.5; nats per note)

D1 = order-2 minus order-1 held-out log-likelihood per note; D2 = order-3 minus order-2.
A positive value means the higher order predicts unseen song better.

| data | D1 > 0 | mean D1 | D2 > 0 | mean D2 |
|---|---|---|---|---|
| K | 11 of 11 | +0.1571 | 11 of 11 | +0.0508 |
| N | 4 of 4 | +0.1082 | 2 of 4 | +0.0222 |
| KS | 10 of 11 | +0.1131 | 8 of 11 | +0.0135 |

Only K's D1 is graded (K7). D2 was registered as a check, not a prediction, but it is the
clearest number in this run: in every one of the 11 Koumura birds, a third-order chain
predicts held-out song better than a second-order chain. Finch song is not a second-order
process. That is not new in itself: Katahira, Suzuki, Okanoya and Okada (2011, PLoS ONE
6:e24516) and Jin and Kozhevnikov (2011, PLoS Comput Biol 7:e1001108) showed that Bengalese
finch syntax has higher-order dependence that a syllable-level Markov chain does not capture.
What is new is the contrast with the Zipf statistic, and that makes the Zipf result above more telling, not less: the Zipf-of-chunks statistic
cannot see structure that a held-out likelihood finds in every bird.

## Predictions (graded at theta 0.5)

| id | prediction | prior | outcome |
|---|---|---|---|
| K1 | K mean R^2 >= 0.80 | 0.80 | **true** |
| K2 | K beats shuffle and rotation | 0.90 | **false** |
| K3 | K beats bigram_within | 0.85 | **false** |
| K4 | K beats markov1 | 0.85 | **false** |
| K5 | K beats markov2 | 0.50 | **false** |
| K6 | K beats markov3 | 0.30 | **false** |
| K7 | D1 > 0 in at least 80% of K birds | 0.90 | **true** |
| N1 | N beats bigram_within | 0.75 | **false** |
| N2 | N beats markov2 | 0.45 | **true** |
| S1 | KS beats markov2 | 0.20 | **false** |
| S2 | KS beats bigram_within | 0.70 | **true** |

4 of 11 graded predictions true. Brier score **0.331** (the eleven squared errors sum to
3.64; 3.64 / 11 = 0.33090909..., far from a rounding tie). For comparison, a
forecaster who gave every prediction 0.5 would score 0.250: our priors did worse than that.
We expected Kirby et al.'s "above the bigram" pattern to replicate (K3 at 0.85, N1 at 0.75),
and it did not.

## Decision rules

X1: **`ABOVE_BIGRAM_FAILS`**
X2: **`SECOND_ORDER_MIXED`**
X3: **`NOT_BEYOND_AT_EITHER_SIZE`**
K label robust across theta 0.3/0.5/0.7: **no**

* X1: neither K nor N beats the within-bout bigram null at theta 0.5.
* X2: K does not beat the second-order chain; N does (but see the N label note above: N does
  not beat the first-order chain either, so this "beats markov2" is not a step beyond
  first-order structure).
* X3: neither the Kirby-size Koumura data (p = 0.850) nor the full Koumura data beat the
  second-order chain.

## What this does and does not show

1. **Kirby et al.'s "above the bigram" Zipf effect did not appear in 15 other adult birds at
   full size.** In Kirby et al.'s own data (30 developmental recordings, 6 birds) the song
   beat the bigram null with z = 6.94 (RESULTS-FINCH.md). Here the Koumura birds fall below it
   (z = -10.44) and the Nicholson birds match it (z = 0.06). At Kirby et al.'s recording size
   the Koumura birds just beat it (p = 0.043) and the Nicholson birds clearly do (p = 0.001),
   so the effect depends on recording size and dataset. That is not what a stable signature of
   word-like units would do. Kirby et al. studied song development; these are adult birds, so
   this tests the pattern, not their developmental claim.
2. **The Koumura result is not an artefact of how we rejoined songs.** Kraw (the authors'
   own 15-note sequences, no rejoining) gives the same picture: real 0.881, below every
   structured null.
3. **The Zipf statistic is a weak and unstable instrument.** It moves with recording size
   and threshold (K is `EXPLAINED_BY_THIRD_ORDER` at theta 0.3 and `EXPLAINED_BY_FIRST_ORDER`
   at 0.5 and 0.7), it is not monotone in chain order (the N note), and it misses order-3
   structure that the held-out check finds in 11 of 11 birds. This matches what we found for
   whale song (RESULTS-HOLD.md) and for English at small sizes (RESULTS-CDS-SIZE.md).
4. **What it does not show:** that finch song has no word-like units, or that it has them.
   It shows that the published Zipf-of-chunks evidence does not carry over to other birds and
   cannot decide the question.

## Limits

* Provisional: gate K failed (notes per bird 9.0% above the paper's figure; cause unknown).
  Gate N passed, and the N results tell the same story for "above the bigram".
* Adult song only; one laboratory for K (the same group as Kirby et al.'s birds, different
  birds and recordings), another for N.
* N has 4 birds; the pre-registration does not grade N's held-out numbers.
* Large recordings give tight null distributions, so small gaps become significant; every gap
  is printed next to its p.
* The work was done by AI agents working in MV2's name. No human expert has reviewed it yet.
