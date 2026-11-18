# RESULTS-CALIB-2: at whale size, song with no words reproduces the whale paper's Zipf numbers

Graded 2026-11-18 by MV2 of Munim, Inc. (mv2@munimtech.com) from job `song-zipf-calib2-v1`
(2026-11-18 07:21-07:48 UTC). Registered in [CALIB-2-PREREG.md](CALIB-2-PREREG.md)
(commit 662ed14, 2026-11-17 22:18 UTC) before it ran. Made with AI agents working in his
name. Text CC BY 4.0; code Apache-2.0. Re-derived by `test_calib2_results.py` from the 140
published replicate lines.

## Headline

Arnon et al. (2025, *Science* 387:649) report that chunks of humpback whale song, cut at dips
in transitional probability, follow Zipf's law with a mean R^2 of 0.93, beating shuffled
(z = 23.09) and rotated (z = 14.43) baselines. These are the only two controls they report.

In synthetic song **with no words at all**, made by a first-order syllable-transition chain
at the size of the whale data (8 "years" x 6 sequences of 700-1,500 elements, about 1,700
cuts per year against the paper's 1,562), the same pipeline gives:

| | whale paper | wordless first-order song (20 replicates) |
|---|---|---|
| mean Zipf R^2 | 0.93 | **0.917** (range 0.894-0.935; 2 of 20 reach 0.93) |
| z vs shuffle | 23.09 | 24.7 (mean) |
| z vs rotation | 14.43 | 21.4 (mean) |
| beats both controls | yes | **20 of 20** |

At whale size, **clean word-like song passed both controls less often (10 of 20) than song
with no words (20 of 20)**. Its rotation baseline was as Zipfian as the song itself. For
these generators, the whale paper's two controls cannot tell words from syllable rules, and
they lean the wrong way.

**A limit of our own test.** At whale size our second-order Markov test never detected clean
word-like song (0 of 20; the second-order null was *more* Zipfian than the real word song,
mean R^2 0.946 against 0.916). By the rule fixed in advance (WR2), any
`EXPLAINED_BY_...` label on the real whale data will therefore be reported as
`NOT_DISTINGUISHABLE`, never as "reduces to syllable rules". A `BEYOND_SECOND_ORDER` whale
label keeps its full weight: the test's size held (0 of 20 false alarms on second-order song).

## Scenarios (theta 0.5, B = 100 per null, 20 replicates each)

| scenario | mean R^2 | pass shuffle + rotation | BEYOND_SECOND_ORDER | other labels |
|---|---|---|---|---|
| `W_markov1_a0.2_V12` (no words) | 0.917 | 20/20 | 0/20 | first-order 20 |
| `W_markov1_a0.1_V24` (no words) | 0.910 | 20/20 | 0/20 | first-order 20 |
| `W_markov2_a0.2_V12` (no words) | 0.692 | 20/20 | 0/20 | second-order 18, first-order 2 |
| `W_words_zipf_V12` (clean words) | 0.916 | 10/20 | **0/20** | first-order 11, second-order 9 |
| `W_words_zipf_noise10_V12` | 0.910 | 20/20 | 2/20 | second-order 17, first-order 1 |
| `F_words_zipf_noise02` (finch size) | 0.903 | 20/20 | 20/20 | |
| `F_words_zipf_noise05` (finch size) | 0.868 | 20/20 | 17/20 | second-order 3 |

The finch paper's extra control (within-bout bigram resampling) kept its size at whale size:
it rejected wordless first-order song in 1 of 20 replicates (`W_markov1_a0.2_V12`) and 0 of
20 (`W_markov1_a0.1_V24`).

## Registered predictions

| id | prediction | prior | outcome |
|---|---|---|---|
| K1 | `W_markov1_a0.2_V12`: >= 80% beat both shuffle and rotation | 0.80 | TRUE (20/20) |
| K2 | `W_markov1_a0.2_V12`: mean R^2 >= 0.80 | 0.55 | TRUE (0.917) |
| K3 | `W_markov1_a0.1_V24`: K1 and K2 both hold | 0.45 | TRUE |
| K4 | `W_markov1_a0.2_V12`: pooled first-order null rejects in <= 15% | 0.80 | TRUE (0/20) |
| K5 | `W_markov2_a0.2_V12`: BEYOND_SECOND_ORDER in <= 15% | 0.75 | TRUE (0/20) |
| K6 | `W_words_zipf_V12`: BEYOND_SECOND_ORDER in >= 50% | 0.80 | **FALSE** (0/20) |
| K7 | `W_words_zipf_noise10_V12`: BEYOND_SECOND_ORDER in >= 50% | 0.50 | **FALSE** (2/20) |
| K8 | `F_words_zipf_noise02`: BEYOND_SECOND_ORDER in >= 50% | 0.65 | TRUE (20/20) |
| K9 | `F_words_zipf_noise05`: BEYOND_SECOND_ORDER in >= 50% | 0.40 | TRUE (17/20) |
| K10 | `W_markov1_a0.2_V12`: within-bout bigram rejects in <= 15% | 0.70 | TRUE (1/20) |

8 of 10 true; Brier score **0.211**. Our worst miss was K6 (prior 0.80): we expected the
second-order test to keep its power on clean words at whale size, and it did not.

## Rules fixed in advance, applied

* **WR1:** K1 and K2 hold -> **`CONTROLS_PASSED_BY_WORDLESS_SONG`** at whale size (R^2 >= 0.80).
* **WR2:** K6 fails -> **applies.** Any `EXPLAINED_BY_...` label on the real whale data is
  reported as `NOT_DISTINGUISHABLE`.
* **WR3:** K5 holds -> no size caveat on a `BEYOND_SECOND_ORDER` whale label.
* **WR4:** finch-size power against word-like song by syllable noise: 0% 1.00 (calibration
  1), 2% 1.00, 5% 0.85, 10% 0.10. Power first falls below one half at **10%**. This is printed
  beside the finch label in [RESULTS-FINCH.md](RESULTS-FINCH.md).

## Why clean words are hard to detect at whale size (our reading, not a registered test)

With 12 words of length 3-7 over 12 symbols and about 50,000 elements per year, a
second-order chain learns almost every within-word transition exactly. It reproduces the
words and adds only a little junk at word joins, so its chunks are as regular as the real
ones, or more so. Long, low-noise data make the second-order null a near-copy of a small
lexicon. The finch data (about 700 syllables per recording) are too short for that.

## What this does NOT show

* It says nothing about real whales yet. It shows that, for these generators at this size,
  the published controls do not separate words from syllable rules. The real whale test is
  registered in [PREREG-AMENDMENT-3.md](PREREG-AMENDMENT-3.md) and still queued.
* Whale song has phrases and themes, repeated many times. Our generators do not model that
  hierarchy.
* B = 100 per null (smallest p about 0.01).

## Files

`results/calib2_results.json` (aggregates and grading) and `results/calib2_tasks.jsonl` (one
line per replicate). Code: `calib2.py`, `calib.py`, `zipfseg.py` (SHA-256 in the results file).
