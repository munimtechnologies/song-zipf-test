# RESULTS-CANARY: the canary positive control

song-zipf-test, graded 2026-11-19 by MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents
working in MV2's name; no human expert has checked this yet. Text CC BY 4.0.

* Registration: [CANARY-PREREG.md](CANARY-PREREG.md) and
  [CANARY-AMENDMENT-1.md](CANARY-AMENDMENT-1.md), both published before any canary data were
  read (the job checked the registration on GitHub at 2026-11-19T10:33:06Z).
* Job: `song-zipf-canary-v2`, run 2026-11-19 10:30-10:38 UTC; `python -m unittest -v
  test_canary` passed, then `canary.py` ran for 203 s. Raw output:
  [results/canary/canary_results.json](results/canary/canary_results.json).
* Grader: [test_canary_results.py](test_canary_results.py), published before the job ran. It
  re-derives every gate, label, rule, prediction and the Brier score with its own code and checks
  that every fixed line below is present. The job's own grading agrees with it.

## Summary in plain words

* **The positive control did not give us a positive.** Canary phrase syntax is reported to
  reach three or more phrases back (Markowitz et al. 2013; Cohen et al. 2020). The plan was to
  confirm that with a held-out likelihood ladder in each bird, and then ask whether the Zipf
  test sees it. In all three birds of the public Cohen 2022 dataset, read as phrase sequences
  (about 3,000 phrases per recording), order 3 predicted held-out phrases **worse** than order 2
  (P1 failed). By rule C1 there is therefore **no ground truth** here, and this run says nothing
  about whether the Zipf test is blind to real animal syntax.
* **The Zipf test itself:** at full size and the registered threshold, every bird beats the
  papers' shuffle and rotation controls (P3 true), but none beats even a first-order chain
  fitted to its own phrase transitions (label `EXPLAINED_BY_FIRST_ORDER` in all three). The
  labels change with the threshold for two birds (at theta 0.3 llb16 and llb3 beat every chain,
  up to third order), and, unexpectedly, at the smaller "Kirby size" (about 800 phrases per
  recording) two birds do beat the second-order chain (P8 true, prior 0.20). A test whose verdict
  flips with an arbitrary cutting threshold and with sample size in the wrong direction is not a
  stable instrument for this question.
* **Why the ground truth may have failed.** The long-range rules described for canaries apply to
  a few phrase types at particular branch points; averaged over all phrases they may add too
  little held-out likelihood to show at this size. The held-out test we built since then (HOLD,
  RESULTS-HOLD.md), with Witten-Bell smoothing and calibrated surrogates, is the natural next
  instrument for these birds. We have not run it on them.

## Reading gates

Reading gate llb11: **pass**

Reading gate llb16: **pass**

Reading gate llb3: **pass**

| bird | syllables | classes | songs | phrases | phrase types | blocks | song span (s) |
|---|---|---|---|---|---|---|---|
| llb11 | 326,600 | 27 | 5,702 | 24,660 | 27 | 8 | 26,348 |
| llb16 | 244,528 | 30 | 2,374 | 15,134 | 30 | 5 | 16,752 |
| llb3 | 353,331 | 20 | 2,953 | 16,304 | 20 | 5 | 27,449 |

## Held-out likelihood ladder (ground truth)

Mean held-out log-likelihood per phrase at orders 1 to 5 (best smoothing per order). g_2 > 0
would mean order 3 beats order 2.

| bird | LL order 1 | LL order 2 | LL order 3 | LL order 4 | LL order 5 | g_2 (order 3 - order 2) | g_3 (order 4 - order 3) |
|---|---|---|---|---|---|---|---|
| llb11 | -0.7169 | -0.6703 | -0.6810 | -0.7100 | -0.7646 | -0.0107 | -0.0291 |
| llb16 | -0.3716 | -0.3397 | -0.3602 | -0.4035 | -0.4558 | -0.0205 | -0.0433 |
| llb3 | -1.0470 | -0.9693 | -1.0020 | -1.0923 | -1.2533 | -0.0327 | -0.0903 |

Held-out blocks (D1: order 2 against order 1; D2: order 3 against order 2; add-0.5 smoothing):

| bird | D1 > 0 | mean D1 | D2 > 0 | mean D2 |
|---|---|---|---|---|
| llb11 | 0 of 8 | -0.0844 | 0 of 8 | -0.1481 |
| llb16 | 0 of 5 | -0.1068 | 0 of 5 | -0.1893 |
| llb3 | 0 of 5 | -0.0624 | 0 of 5 | -0.1988 |

## Zipf test against each null

| bird | size | theta | null | real R^2 | null mean R^2 | gap | z | p | nulls |
|---|---|---|---|---|---|---|---|---|---|
| llb11 | full | 0.5 | `EXPLAINED_BY_FIRST_ORDER` |
| llb11 | full | 0.5 | shuffle | 0.928 | 0.833 | +0.095 | 19.16 | 0.005 | 200 |
| llb11 | full | 0.5 | rotate | 0.928 | 0.852 | +0.076 | 18.57 | 0.005 | 200 |
| llb11 | full | 0.5 | bigram_within | 0.928 | 0.941 | -0.012 | -3.26 | 1.000 | 200 |
| llb11 | full | 0.5 | markov1_pooled | 0.928 | 0.953 | -0.025 | -4.42 | 1.000 | 200 |
| llb11 | full | 0.5 | markov2_pooled | 0.928 | 0.942 | -0.014 | -2.70 | 1.000 | 200 |
| llb11 | full | 0.5 | markov3_pooled | 0.928 | 0.946 | -0.018 | -4.38 | 1.000 | 200 |
| llb11 | full | 0.3 | `EXPLAINED_BY_FIRST_ORDER` |
| llb11 | full | 0.3 | shuffle | 0.873 | 0.751 | +0.122 | 17.52 | 0.010 | 100 |
| llb11 | full | 0.3 | rotate | 0.873 | 0.798 | +0.074 | 13.54 | 0.010 | 100 |
| llb11 | full | 0.3 | bigram_within | 0.873 | 0.902 | -0.029 | -5.78 | 1.000 | 100 |
| llb11 | full | 0.3 | markov1_pooled | 0.873 | 0.904 | -0.032 | -5.89 | 1.000 | 100 |
| llb11 | full | 0.3 | markov2_pooled | 0.873 | 0.894 | -0.021 | -3.95 | 1.000 | 100 |
| llb11 | full | 0.3 | markov3_pooled | 0.873 | 0.896 | -0.023 | -4.21 | 1.000 | 100 |
| llb11 | full | 0.7 | `EXPLAINED_BY_FIRST_ORDER` |
| llb11 | full | 0.7 | shuffle | 0.958 | 0.895 | +0.063 | 16.85 | 0.010 | 100 |
| llb11 | full | 0.7 | rotate | 0.958 | 0.902 | +0.055 | 17.12 | 0.010 | 100 |
| llb11 | full | 0.7 | bigram_within | 0.958 | 0.967 | -0.009 | -5.20 | 1.000 | 100 |
| llb11 | full | 0.7 | markov1_pooled | 0.958 | 0.962 | -0.005 | -1.46 | 0.921 | 100 |
| llb11 | full | 0.7 | markov2_pooled | 0.958 | 0.969 | -0.011 | -4.56 | 1.000 | 100 |
| llb11 | full | 0.7 | markov3_pooled | 0.958 | 0.966 | -0.009 | -3.21 | 1.000 | 100 |
| llb11 | Kirby | 0.5 | `EXPLAINED_BY_FIRST_ORDER` |
| llb11 | Kirby | 0.5 | shuffle | 0.876 | 0.733 | +0.143 | 11.34 | 0.005 | 200 |
| llb11 | Kirby | 0.5 | rotate | 0.876 | 0.796 | +0.080 | 9.25 | 0.005 | 200 |
| llb11 | Kirby | 0.5 | bigram_within | 0.876 | 0.896 | -0.020 | -2.31 | 0.990 | 200 |
| llb11 | Kirby | 0.5 | markov1_pooled | 0.876 | 0.925 | -0.049 | -5.62 | 1.000 | 200 |
| llb11 | Kirby | 0.5 | markov2_pooled | 0.876 | 0.906 | -0.031 | -2.82 | 1.000 | 200 |
| llb11 | Kirby | 0.5 | markov3_pooled | 0.876 | 0.907 | -0.031 | -2.70 | 1.000 | 200 |
| llb16 | full | 0.5 | `EXPLAINED_BY_FIRST_ORDER` |
| llb16 | full | 0.5 | shuffle | 0.956 | 0.825 | +0.132 | 19.01 | 0.005 | 200 |
| llb16 | full | 0.5 | rotate | 0.956 | 0.901 | +0.055 | 13.64 | 0.005 | 200 |
| llb16 | full | 0.5 | bigram_within | 0.956 | 0.944 | +0.012 | 5.05 | 0.005 | 200 |
| llb16 | full | 0.5 | markov1_pooled | 0.956 | 0.957 | -0.001 | -0.36 | 0.657 | 200 |
| llb16 | full | 0.5 | markov2_pooled | 0.956 | 0.958 | -0.002 | -0.60 | 0.756 | 200 |
| llb16 | full | 0.5 | markov3_pooled | 0.956 | 0.958 | -0.002 | -0.75 | 0.771 | 200 |
| llb16 | full | 0.3 | `BEYOND_THIRD_ORDER` |
| llb16 | full | 0.3 | shuffle | 0.949 | 0.711 | +0.238 | 24.05 | 0.010 | 100 |
| llb16 | full | 0.3 | rotate | 0.949 | 0.858 | +0.091 | 17.06 | 0.010 | 100 |
| llb16 | full | 0.3 | bigram_within | 0.949 | 0.930 | +0.019 | 6.73 | 0.010 | 100 |
| llb16 | full | 0.3 | markov1_pooled | 0.949 | 0.936 | +0.013 | 3.57 | 0.010 | 100 |
| llb16 | full | 0.3 | markov2_pooled | 0.949 | 0.937 | +0.012 | 2.72 | 0.010 | 100 |
| llb16 | full | 0.3 | markov3_pooled | 0.949 | 0.940 | +0.009 | 2.27 | 0.010 | 100 |
| llb16 | full | 0.7 | `EXPLAINED_BY_FIRST_ORDER` |
| llb16 | full | 0.7 | shuffle | 0.946 | 0.889 | +0.057 | 12.04 | 0.010 | 100 |
| llb16 | full | 0.7 | rotate | 0.946 | 0.931 | +0.015 | 5.81 | 0.010 | 100 |
| llb16 | full | 0.7 | bigram_within | 0.946 | 0.941 | +0.005 | 1.55 | 0.059 | 100 |
| llb16 | full | 0.7 | markov1_pooled | 0.946 | 0.958 | -0.012 | -2.87 | 0.990 | 100 |
| llb16 | full | 0.7 | markov2_pooled | 0.946 | 0.955 | -0.009 | -2.33 | 0.970 | 100 |
| llb16 | full | 0.7 | markov3_pooled | 0.946 | 0.954 | -0.008 | -1.78 | 0.970 | 100 |
| llb16 | Kirby | 0.5 | `EXPLAINED_BY_THIRD_ORDER` |
| llb16 | Kirby | 0.5 | shuffle | 0.934 | 0.724 | +0.211 | 11.30 | 0.005 | 200 |
| llb16 | Kirby | 0.5 | rotate | 0.934 | 0.803 | +0.131 | 11.24 | 0.005 | 200 |
| llb16 | Kirby | 0.5 | bigram_within | 0.934 | 0.893 | +0.042 | 5.36 | 0.005 | 200 |
| llb16 | Kirby | 0.5 | markov1_pooled | 0.934 | 0.908 | +0.026 | 2.41 | 0.010 | 200 |
| llb16 | Kirby | 0.5 | markov2_pooled | 0.934 | 0.917 | +0.018 | 2.02 | 0.005 | 200 |
| llb16 | Kirby | 0.5 | markov3_pooled | 0.934 | 0.923 | +0.012 | 1.59 | 0.055 | 200 |
| llb3 | full | 0.5 | `EXPLAINED_BY_FIRST_ORDER` |
| llb3 | full | 0.5 | shuffle | 0.953 | 0.850 | +0.103 | 17.16 | 0.005 | 200 |
| llb3 | full | 0.5 | rotate | 0.953 | 0.919 | +0.033 | 10.30 | 0.005 | 200 |
| llb3 | full | 0.5 | bigram_within | 0.953 | 0.952 | +0.000 | 0.16 | 0.493 | 200 |
| llb3 | full | 0.5 | markov1_pooled | 0.953 | 0.951 | +0.002 | 0.76 | 0.229 | 200 |
| llb3 | full | 0.5 | markov2_pooled | 0.953 | 0.955 | -0.002 | -1.01 | 0.836 | 200 |
| llb3 | full | 0.5 | markov3_pooled | 0.953 | 0.955 | -0.002 | -0.63 | 0.806 | 200 |
| llb3 | full | 0.3 | `BEYOND_THIRD_ORDER` |
| llb3 | full | 0.3 | shuffle | 0.948 | 0.764 | +0.183 | 24.05 | 0.010 | 100 |
| llb3 | full | 0.3 | rotate | 0.948 | 0.858 | +0.090 | 17.65 | 0.010 | 100 |
| llb3 | full | 0.3 | bigram_within | 0.948 | 0.935 | +0.013 | 3.62 | 0.010 | 100 |
| llb3 | full | 0.3 | markov1_pooled | 0.948 | 0.920 | +0.028 | 5.07 | 0.010 | 100 |
| llb3 | full | 0.3 | markov2_pooled | 0.948 | 0.927 | +0.020 | 4.30 | 0.010 | 100 |
| llb3 | full | 0.3 | markov3_pooled | 0.948 | 0.938 | +0.010 | 2.37 | 0.020 | 100 |
| llb3 | full | 0.7 | `EXPLAINED_BY_FIRST_ORDER` |
| llb3 | full | 0.7 | shuffle | 0.936 | 0.902 | +0.034 | 8.09 | 0.010 | 100 |
| llb3 | full | 0.7 | rotate | 0.936 | 0.936 | -0.000 | -0.05 | 0.554 | 100 |
| llb3 | full | 0.7 | bigram_within | 0.936 | 0.953 | -0.017 | -7.25 | 1.000 | 100 |
| llb3 | full | 0.7 | markov1_pooled | 0.936 | 0.942 | -0.006 | -1.58 | 0.950 | 100 |
| llb3 | full | 0.7 | markov2_pooled | 0.936 | 0.937 | -0.001 | -0.29 | 0.604 | 100 |
| llb3 | full | 0.7 | markov3_pooled | 0.936 | 0.933 | +0.003 | 0.67 | 0.257 | 100 |
| llb3 | Kirby | 0.5 | `BEYOND_THIRD_ORDER` |
| llb3 | Kirby | 0.5 | shuffle | 0.945 | 0.786 | +0.159 | 11.46 | 0.005 | 200 |
| llb3 | Kirby | 0.5 | rotate | 0.945 | 0.863 | +0.082 | 11.49 | 0.005 | 200 |
| llb3 | Kirby | 0.5 | bigram_within | 0.945 | 0.927 | +0.019 | 3.24 | 0.005 | 200 |
| llb3 | Kirby | 0.5 | markov1_pooled | 0.945 | 0.924 | +0.021 | 2.88 | 0.005 | 200 |
| llb3 | Kirby | 0.5 | markov2_pooled | 0.945 | 0.927 | +0.018 | 2.16 | 0.010 | 200 |
| llb3 | Kirby | 0.5 | markov3_pooled | 0.945 | 0.933 | +0.012 | 1.68 | 0.020 | 200 |

## Rules and robustness (CANARY-PREREG.md, applied as coded)

C1: **`NO_GROUND_TRUTH`**

C2: **`NOTHING_DETECTED_AT_FULL_SIZE`**

Label robust across theta 0.3/0.5/0.7, llb11: **yes**

Label robust across theta 0.3/0.5/0.7, llb16: **no**

Label robust across theta 0.3/0.5/0.7, llb3: **no**

Provisional (a reading gate failed): **no**

## Predictions (priors fixed in CANARY-PREREG.md)

| id | prediction | prior | outcome |
|---|---|---|---|
| P1 | G3 (order 3 beats order 2 held out) in >= 2 of 3 birds | 0.75 | **false** |
| P2 | G4 (order 4 beats order 3) in >= 2 of 3 birds | 0.45 | **false** |
| P3 | all 3 birds beat shuffle and rotate at theta 0.5 | 0.90 | **true** |
| P4 | >= 2 birds beat markov1_pooled | 0.70 | **false** |
| P5 | >= 2 birds beat markov2_pooled | 0.45 | **false** |
| P6 | >= 2 birds beat markov3_pooled | 0.30 | **false** |
| P7 | all 3 birds have a D1 majority | 0.80 | **false** |
| P8 | >= 2 birds beat markov2_pooled at Kirby size | 0.20 | **true** |

2 of 8 graded predictions true

Brier score **0.355**

## Limits

Three birds from one laboratory's public dataset (Cohen 2022, CC0), read as phrase sequences from
the released annotation files; phrase boundaries are runs of the same syllable label, which may
differ from how the original studies defined phrases. The ladder uses additive smoothing at four
fixed strengths; a different model class (for example the probabilistic suffix trees of
Markowitz et al. 2013) may find the long-range rules this ladder missed. The add-0.5 D1 check
favoured order 1 in every recording; RESULTS-HOLD.md shows that this check is sensitive to the
smoothing choice, so P7 failing says little about the birds.
