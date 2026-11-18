# CDS-PREREG: can the test find real words? A human-language positive control

Registered 2026-11-18 (about 09:30 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com), before
any of the data below were downloaded or analysed by anyone working for MV2. Made with AI
agents. Text CC BY 4.0; code Apache-2.0. Code: `cds_job.py`, tests `test_cds_job.py`; job
`song-zipf-cds-v1`. `zipfseg.py` is used unchanged (commit 742fd83).

## 1. Why

[RESULTS-FINCH.md](RESULTS-FINCH.md) found that the Zipf structure of Bengalese finch song is
matched by a second-order syllable chain (`EXPLAINED_BY_SECOND_ORDER`). Our synthetic
calibrations ([RESULTS-CALIB.md](RESULTS-CALIB.md), [RESULTS-CALIB-2.md](RESULTS-CALIB-2.md))
show when the test can and cannot detect artificial word lexicons. Neither the song papers
nor we have run the pipeline on **real human language**, the system the "language-like" claim
is measured against. (The whale paper cites the use of transitional probabilities on
child-directed speech, but does not run its pipeline or controls on speech. We found no study
that does.)

So we ask: **at the size of the finch and whale data, does real child-directed English, cut by
the same infant-inspired method, beat a second-order Markov chain over its own phonemes?**

* If it does, the finch result is a real contrast: English passes the test that finch song
  fails, at the same size.
* If it does not, the test cannot find even real English words at that size. The finch label
  then says nothing about words either way, and the published Zipf evidence (which uses
  weaker controls) is weaker still.

## 2. Data

The Brent-Ratner derived corpus (Bernstein-Ratner 1987; Brent & Cartwright 1996; CHILDES,
MacWhinney & Snow 1985): 9,790 child-directed utterances to children aged 13-23 months,
transcribed one character per phoneme, with spaces between words. It is fetched at run time
from TalkBank (`https://talkbank.org/childes/access/Derived/0docs/BR.zip`, file
`br-phono.txt`), with the GitHub copy in `melsner/neural-segmentation` as fallback. Its SHA-256
is recorded. The corpus is not redistributed; only derived statistics are published.

**Reading gate** (no analysis unless it passes): exactly 9,790 non-empty utterances and
95,809 phonemes (the published counts), and 33,387 or 33,399 word tokens (+-20; both counts
appear in the literature).

## 3. Design

Symbols are phonemes; the word spaces are removed. A **bout** is one utterance (a natural
pause, like a finch bout), and TPs never cross it. A **recording** is a block of consecutive
utterances, in file order:

| data set | recordings | utterances each | utterances used | about |
|---|---|---|---|---|
| **CDS-F** (finch size, primary) | 30 | 70 | 1-2,100 | 685 phonemes per recording (finch: 676 syllables) |
| **CDS-W** (whale size) | 8 | 600 | 2,101-6,900 | 5,870 phonemes per recording (whale: 5,720 elements per year) |

Pipeline and nulls exactly as in [PREREG.md](PREREG.md) and Amendment 1 (`zipfseg.analyze`,
Code S1 cut rule, theta 0.3 / **0.5** / 0.7): shuffle, rotation, within-bout bigram and trigram,
pooled first- and second-order chains, held-out check D1. B = 1,000 (CDS-F) and 200 (CDS-W,
as PREREG.md allows for whale-sized data). Seed 20261117. The label rule is unchanged:
`BEYOND_SECOND_ORDER` if p(second-order) < 0.05; `EXPLAINED_BY_SECOND_ORDER` if only
p(first-order) < 0.05; otherwise `EXPLAINED_BY_FIRST_ORDER`.

Descriptive extras, not used by any rule except H7: how well the theta-0.5 cuts find the true
word boundaries (precision, recall and F1 over within-utterance positions), and the Zipf R^2
of the **true words** in each recording.

## 4. Predictions and honest priors (graded by `cds_job.grade`)

| id | prediction | prior |
|---|---|---|
| H0 | CDS-F: mean chunk Zipf R^2 at theta 0.5 >= 0.80 | 0.65 |
| H1 | CDS-F: beats both shuffle and rotation (p < 0.05) | 0.90 |
| H2 | CDS-F: beats within-bout bigram resampling (p < 0.05) | 0.50 |
| H3 | CDS-F: beats the pooled first-order chain (p < 0.05) | 0.80 |
| H4 | CDS-F: beats the pooled second-order chain, i.e. `BEYOND_SECOND_ORDER` | 0.40 |
| H5 | CDS-W: `BEYOND_SECOND_ORDER` | 0.35 |
| H6 | CDS-F: D1, order 2 generalises better in >= 20 of 30 recordings | 0.85 |
| H7 | CDS-F: word-boundary F1 of the theta-0.5 cuts >= 0.50 | 0.45 |

Our overall expectation: English child-directed words are short (about 2.9 phonemes), so a
second-order phoneme chain may reproduce much of them. We lean, weakly, towards English
**not** beating the second-order chain at finch size.

## 5. Reading rules (fixed now)

* **L1 (finch size).** CDS-F `BEYOND_SECOND_ORDER` at theta 0.5 ->
  `LANGUAGE_PASSES_AT_FINCH_SIZE`: the finch label is a contrast with real language at matched
  size. Otherwise -> `LANGUAGE_FAILS_AT_FINCH_SIZE`: the finch label is reported, in
  RESULTS-FINCH.md and anywhere it is quoted, as *not distinguishable from what real English
  gives*, never as evidence that finch song lacks words.
* **L2 (whale size).** The same for CDS-W -> `LANGUAGE_PASSES_AT_WHALE_SIZE` /
  `LANGUAGE_FAILS_AT_WHALE_SIZE`, applied to the whale result when it exists, together with
  CALIB-2 rule WR2.
* **L3 (published controls).** If CDS-F beats shuffle and rotation (H1) and the finch and
  CALIB results also pass them, we report that the published controls are passed alike by
  English, finch song, and song with no words.
* **Robustness.** A label is called robust only if it is the same at theta 0.3 and 0.7.
* Whatever comes out is published as RESULTS-CDS.md.

## 6. Limits known now

* Phonemes are not syllables. Finch syllables and whale sound elements are the units those
  papers cut, and they are not the same thing as phonemes. Human syllables would be the
  closer match, but this corpus has no syllabification. This is a test of the pipeline on
  one real language, not a matched comparison of species.
* The transcription uses dictionary pronunciations, so it is cleaner than real speech, which
  favours detecting words.
* One language, one corpus, one register (speech to infants).
