# PREREG: Is the "language-like" Zipf structure in whale and finch song more than short-range syllable rules?

Registered 2026-11-17 by MV2 of Munim, Inc. (mv2@munimtech.com), before any song data was
downloaded or seen. Made with AI agents. Text CC BY 4.0; code Apache-2.0.

## 1. The claims under test

* **Arnon, Kirby, Allen, Garrigue, Carroll & Garland 2025, Science 387:649-653**
  (doi:10.1126/science.adq7055). Eight years of humpback whale song from New Caledonia. The
  song is segmented at dips in transitional probability (TP), the way infants are thought to
  segment speech. The recurring subsequences follow a Zipfian rank-frequency distribution
  that is "found in all human languages" and had not been reported in another species. The
  controls we could find described are shuffled and rotated baselines.
* **Kirby, Okanoya, Garland, Takahasi & Arnon 2026, Science Advances**
  (doi:10.1126/sciadv.aea3015, PMC13450306). Bengalese finch song: 6 birds x 5 recording
  days = 30 recordings of about 10 bouts each. Mean R^2 of log frequency on log rank is
  0.89 at cut threshold 0.5 (0.75 at 0.3, 0.90 at 0.7). The real song beats 1000 shuffled
  datasets (z = 17.05), 1000 rotated ones (z = 15.69) and 1000 "bigram" (first-order,
  within-bout) resampled ones (z = 6.77 at 0.5; z = 1.87, P = 0.03 at 0.7). The authors
  conclude that the Zipfian distribution "arises due to sequential structure above the bigram".

**Our question.** Structure "above the bigram" could be word-like chunks, or it could be
nothing more than second-order (trigram) syllable rules. Bengalese finch syntax is known
to be well described by second-order or hidden Markov models (Katahira et al. 2011). No
published test we could find, including both papers, their eLetters ("Zipf zapped",
"Solar flares show language-like statistical structures") and a Language Log thread,
compares the Zipf statistic against a **second-order** Markov null, or against **pooled**
(recording-level) Markov chains. We also found no test of the whale result against any
Markov null at all.

**What would be a "wow".** If the Zipf fit of whale or finch song is reproduced by a
second-order Markov chain, then "language-like statistical structure" in these songs
reduces to short-range syllable-transition rules, which would weaken a widely reported
Science result. If the real songs beat second-order nulls, that is much stronger evidence
than the published controls for word-like units in a non-human communication system.
Either outcome will be published.

## 2. What we have seen before registering

Only the abstracts, press coverage, and the finch paper's text (via the Europe PMC
full-text XML), including the numbers quoted above. We have **not** seen any song data,
Code S1 or Data S1-S3 of either paper, or the whale paper's supplementary text.

## 3. Pipeline (reproduction of the published method)

Code: `zipfseg.py` (tests: `test_zipfseg.py`).

* TP(a->b) = n(a,b)/n(a,.), estimated per recording from within-bout adjacent pairs.
* Cut rule: with t_i = TP(s_i -> s_{i+1}), place a boundary at transition i when
  t_i / t_{i-1} < theta (the current TP has dropped below theta times the previous one).
  Thresholds theta = 0.3, 0.5 (primary), 0.7.
* Inventory of subsequences per recording, rank-frequency, R^2 of log f on log r. The
  statistic is the mean R^2 over recordings.
* **If the authors' Code S1 differs** (cut position, ratio direction, TP estimation,
  segment counting), we follow Code S1 and record the change in a dated amendment before
  any analysis runs. The other rule direction (`prev_over_cur`) is reported as a sensitivity
  check either way.
* Units. Finch: a recording is one bird-day; bouts are the published bouts. Whale: a
  "recording" in our code is one **year** (TPs pooled within year, as in the paper), and a
  "bout" is one recording's concatenated element sequence, with theme and song-cycle
  boundaries removed as in the paper. Code S1 overrides this if it differs.

## 4. Null models (1000 datasets each, seed 20261117)

Every null keeps each bout's length and is re-segmented with TPs re-estimated on the null
data. Primary nulls are marked **P**.

| name | what it keeps |
|---|---|
| shuffle | symbol counts within each bout (published control) |
| bigram_within | first-order transitions within each bout (published finch control, reproduced) |
| **markov1_pooled** (P) | first-order Markov chain fitted to the whole recording |
| trigram_within | second-order transitions within each bout (secondary: short bouts make it near-copy) |
| **markov2_pooled** (P) | second-order Markov chain fitted to the whole recording |

For each null and threshold: z = (real - null mean)/null sd, and one-sided empirical
p = (1 + #null >= real)/(1 + 1000). We also report the share of null datasets whose mean
R^2 >= 0.80, i.e. how often a null alone looks "Zipfian" by the published metric.

**Overfitting diagnostic D1.** Leave-one-bout-out log-likelihood per symbol of order-2 vs
order-1 chains (additive smoothing 0.5, same predicted symbols). If order 2 does not
generalise better in most recordings, second-order nulls may just copy the data, and any
"explained by second order" result is labelled *overfit caveat*.

If the whale data make B = 1000 too slow, B is reduced to no less than 200 for the whale
only. This is fixed now, before any run.

## 5. Predictions, priors (our honest probabilities) and decision rule

Primary: theta = 0.5, published rule direction (or Code S1's).

**Finch** (conditional on the sanity check S-F passing)

| id | prediction | prior |
|---|---|---|
| S-F | sanity: our mean R^2 at theta 0.5 is within 0.03 of 0.89 | 60% |
| F1 | real > bigram_within, p < 0.05 (replicates published) | 85% |
| F2 | real > markov1_pooled, p < 0.05 | 80% |
| F3 | real > trigram_within, p < 0.05 | 35% |
| F4 | real > markov2_pooled, p < 0.05 | 35% |
| F5 | markov2_pooled null mean R^2 >= 0.80 | 60% |
| F6 | D1: order 2 generalises better in >= 20 of 30 recordings | 75% |

**Whale** (only if the published data can be obtained; our prior for that is 60%)

| id | prediction | prior |
|---|---|---|
| S-W | sanity: real > shuffle, p < 0.05; and within 0.03 of any published per-year mean R^2 we can find | 85% |
| W1 | real > bigram_within, p < 0.05 | 70% |
| W2 | real > markov1_pooled, p < 0.05 | 70% |
| W3 | real > trigram_within, p < 0.05 | 45% |
| W4 | real > markov2_pooled, p < 0.05 | 45% |
| W5 | markov2_pooled null mean R^2 >= 0.80 | 50% |
| W6 | D1: order 2 generalises better in >= 6 of 8 years | 70% |

**Decision, for each species separately, at theta = 0.5:**

* `REPRODUCTION_FAILED`: the sanity check fails. Results are reported descriptively, with no headline.
* `BEYOND_SECOND_ORDER`: p(markov2_pooled) < 0.05. The Zipf structure is not explained by short-range rules.
* `EXPLAINED_BY_SECOND_ORDER`: p(markov1_pooled) < 0.05 but p(markov2_pooled) >= 0.05. Add *overfit caveat* if D1 fails.
* `EXPLAINED_BY_FIRST_ORDER`: p(markov1_pooled) >= 0.05.

Thresholds 0.3 and 0.7 and the reversed rule are reported as robustness checks. They do
not change the headline. Any statement that the headline is "robust" needs the same label
at both 0.3 and 0.7. Our overall expectation for the finch is
`EXPLAINED_BY_SECOND_ORDER` (about 50%) over `BEYOND_SECOND_ORDER` (about 35%).

## 6. Stages

0. `inventory.py` downloads the finch supplement (Europe PMC) and the whale accepted
   manuscript (St Andrews, CC BY), records hashes and extracts text. It does no analysis.
1. A parser for the published data format is written after the inventory, with an amendment
   (`PREREG-AMENDMENT-1.md`) that lists exactly what was seen, before the analysis job is filed.
2. The analysis job runs `zipfseg.analyze` and writes `results.json`. Every prediction above
   is graded in `RESULTS.md`, whichever way it falls.

The whale data (Science Data S1-S3) sit behind a publisher bot wall. They will be fetched in
a browser. Their licence allows use "for the purposes of reproducing or extending the
Zipfian analysis". Raw data from either paper will not be redistributed in this repository
(the finch data are CC BY-NC); only derived statistics will be.

## 7. Limits we already know

* The R^2 of a log-log rank-frequency plot is a weak test of a power law (Clauset, Shalizi &
  Newman 2009). We keep it because it is the published statistic; we test the
  inference drawn from it, not whether the law is exactly a power law.
* A second-order chain fitted to about ten bouts can overfit; D1 is reported for that reason.
* "Explained by a Markov chain" does not mean the birds or whales produce song with a
  Markov chain. It means this statistic cannot tell word-like units apart from
  short-range transition rules.
