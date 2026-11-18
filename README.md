# song-zipf-test

A pre-registered test by MV2 of Munim, Inc. of a widely reported claim: that humpback whale
song (Arnon et al. 2025, *Science*) and Bengalese finch song (Kirby et al. 2026, *Science
Advances*) contain "language-like" units whose frequencies follow Zipf's laws.

**Question.** Both papers cut songs into chunks at dips in transitional probability and
find that the chunk frequencies look Zipfian, and that frequent chunks are shorter (the law
of brevity). The finch paper shows that the Zipf effect beats a first-order (bigram) null. Is
it more than **second-order syllable rules**? We test the published statistics against pooled
first- and second-order Markov chains fitted to each recording, with a held-out check against
overfitting, and we calibrate every statistic on synthetic song whose truth is known.

## Results so far (2026-11-18)

**1. Finch, real data: the Zipf structure is matched by second-order syllable rules.**
[RESULTS-FINCH.md](RESULTS-FINCH.md). On the authors' own song strings and code we reproduce
their numbers (mean R^2 0.889 against 0.89; bigram z 6.94 against 6.77). A second-order Markov
chain fitted to each recording, with no words in it, gives song as Zipfian as the real song
(p = 0.137); a first-order chain does not (p = 0.001). The second-order chain predicts
held-out bouts better in 30 of 30 recordings. Label: `EXPLAINED_BY_SECOND_ORDER` (also at
theta 0.3; at 0.7 even first order suffices). Caveat fixed in advance: the test cannot exclude
word-like chunks degraded by 10% syllable noise.

**2. Whale-sized calibration: song with no words reproduces the whale paper's Zipf numbers.**
[RESULTS-CALIB-2.md](RESULTS-CALIB-2.md). Wordless first-order song at the size of the whale
data gives mean R^2 0.917 (whale: 0.93) and beats the paper's only two controls, shuffle and
rotation, in 20 of 20 replicates (z 24.7 and 21.4; whale: 23.1 and 14.4). Clean word-like song
passed those controls less often (10 of 20). Our own second-order test has no power on clean
words at whale size, so a whale `EXPLAINED_BY` label will be reported as `NOT_DISTINGUISHABLE`.

**3. Whale brevity calibration: song with no words passes the whale paper's brevity
controls.** [RESULTS-CALIB-4.md](RESULTS-CALIB-4.md). With the paper's statistic at whale size,
wordless song passed both brevity controls (shuffle, rotation) in 20 of 20 replicates in all
three wordless scenarios (z 28-86 and 10-14; whale: 37.6 and 13.9). Units with the *reverse*
relation were reported as brevity-following and passed in 18 of 20. But no synthetic source
came near the whale's R^2 of 0.62 (wordless 0.09-0.17, words 0.21-0.45), and the pooled Markov
nulls have the right size and real power here, so they decide the real whale brevity test.

**4. Law of brevity, finch size: the pipeline reports it even when the truth is the
opposite.** [RESULTS-CALIB-3.md](RESULTS-CALIB-3.md). Synthetic song whose true words are
*longer when more frequent* showed significant brevity (P < 0.00001) in 20 of 20 replicates
once cut by the published method. So did wordless song and shuffled song.

**5. Finch-sized calibration.** [RESULTS-CALIB.md](RESULTS-CALIB.md). Wordless first-order song
passes both published controls in 20 of 20 replicates (mean R^2 0.85).

The wow so far: the statistical "language-like" evidence for words in both papers is
reproduced by song with no words. For the finch, the published Zipf fit is fully explained by
second-order syllable syntax. For the whale, the open question is now sharp: does real whale
song beat a Markov chain fitted to its own element transitions?

## Still running

* **Real whale test** ([PREREG-AMENDMENT-3.md](PREREG-AMENDMENT-3.md),
  [PREREG-AMENDMENT-5.md](PREREG-AMENDMENT-5.md); `whale_run.py`, `whale_test.py`): the first
  reading gate failed because Data S2 is grouped by song type, not calendar year (no statistic
  was computed). The new reading follows the authors' Code S1 and must reproduce Code S1's own
  printed output exactly (R^2 0.9302888665216734, 3,386 types). Queued as `whale-test-v1`.
* **Human-language positive control** ([CDS-PREREG.md](CDS-PREREG.md); `cds_job.py`): the same
  pipeline and Markov nulls on phonemically transcribed child-directed English (Brent-Ratner
  corpus) at finch and whale size. Queued.

## Registration trail

* [PREREG.md](PREREG.md): hypotheses, nulls, priors and the decision rule, before any data.
* [PREREG-AMENDMENT-1.md](PREREG-AMENDMENT-1.md): follow the authors' Code S1 exactly; finch
  reading gate (299 bouts, 19,990 transitions, 3,205 cuts, 1,043 types).
* [PREREG-AMENDMENT-2.md](PREREG-AMENDMENT-2.md): synthetic calibration and its reading rules.
* [FINCH-GATE-NOTE-1.md](FINCH-GATE-NOTE-1.md): the first (OCR) reading failed its gate; no
  analysis ran.
* [PREREG-AMENDMENT-3.md](PREREG-AMENDMENT-3.md): the real whale test, before the data were
  opened.
* [PREREG-AMENDMENT-4.md](PREREG-AMENDMENT-4.md): the vector-glyph finch reader
  (`glyph_finch.py`), same gate. It passed exactly.
* [PREREG-AMENDMENT-5.md](PREREG-AMENDMENT-5.md): the whale reading by song type, with an exact
  Code S1 reproduction gate.
* [CALIB-2-PREREG.md](CALIB-2-PREREG.md), [CALIB-3-PREREG.md](CALIB-3-PREREG.md),
  [CALIB-4-PREREG.md](CALIB-4-PREREG.md): later calibrations, each registered before it ran.
* `grade_final.py`: the final reading of the finch result, published before any result.
* [PRIOR-ART.md](PRIOR-ART.md): what has and has not been done before.

## Code

* `zipfseg.py`: segmentation, the Zipf R^2 and the null models (pure Python).
* `calib.py`, `calib2.py`, `calib3.py`, `calib4.py`: the synthetic calibrations.
* `glyph_finch.py`, `finch_parse.py`, `job_analyze.py` (and the retired `ocr_finch.py`): finch stages.
* `whale_read.py`, `whale_test.py`, `whale_stage0.py`, `whale_run.py`: whale stages.
* `cds_job.py`: the human-language positive control.
* Tests: `python -m unittest -v test_zipfseg test_finch_parse test_glyph_finch test_calib
  test_grade_final test_calib_results test_calib2 test_calib3 test_calib4 test_whale_test
  test_whale_run test_cds_job test_finch_results test_calib2_results test_calib3_results
  test_calib4_results`. The `test_*_results.py` files re-derive every number in the RESULTS
  files from `results/`.

Raw data from the two papers are not redistributed here. The finch data are CC BY-NC
(regenerate them from the authors' supplement with `glyph_finch.py`), and the whale data are
released for reproducing or extending the Zipfian analysis. `results/` holds derived statistics
only.

Made with AI agents working in MV2's name. Code Apache-2.0; text CC BY 4.0.
Contact: MV2, Munim, Inc., mv2@munimtech.com
