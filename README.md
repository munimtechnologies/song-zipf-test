# song-zipf-test

A pre-registered test by MV2 of Munim, Inc. of a widely reported claim: that humpback whale
song (Arnon et al. 2025, *Science*) and Bengalese finch song (Kirby et al. 2026, *Science
Advances*) contain "language-like" units whose frequencies follow Zipf's laws.

**Question.** Both papers cut songs into chunks at dips in transitional probability and
find that the chunk frequencies look Zipfian, and that frequent chunks are shorter (the law
of brevity). The finch paper shows that the Zipf effect beats a first-order (bigram) null. Is
it more than **second-order syllable rules**? We test the published statistics against pooled
first- and second-order Markov chains fitted to each recording, with a held-out check against
overfitting. We calibrate every statistic on synthetic song whose truth is known, and on real
human language (child-directed English) as a positive control.

## Results so far (2026-11-18)

**1. Whale, real data: the Zipf law is fully reproduced by a second-order chain fitted to the
song's own transitions, and the test's power check says it cannot see words here.**
[RESULTS-WHALE.md](RESULTS-WHALE.md). On the authors' own data and code we reproduce their Zipf
R^2 to the last digit (0.9302888665216728 against Code S1's 0.9302888665216734) and their top
chunk in 8 of 8 years. The song beats the paper's controls and a first-order chain, but a
second-order chain with no words in it gives song that is more Zipfian than the real song (R^2
0.939 against 0.930, p = 0.970). Label `NOT_DISTINGUISHABLE` (not robust: at the loosest
thresholds, 0.25 and 0.3, the song does beat that chain). The held-out power check D1 favours
order 2 in only 1 of 8 years, the regime in which real English words are missed too (result 2).
Our brevity statistic did not reproduce the paper's R^2 of 0.62 (we got 0.021), so no brevity
label is drawn; that is a gap in our reproduction, not evidence against the paper.

**2. English size curve: the test finds real words from about 2,700 phonemes per recording,
and D1 predicts when it can.** [RESULTS-CDS-SIZE.md](RESULTS-CDS-SIZE.md). 17 replicates of 8
recordings of child-directed English, from 647 to 11,748 phonemes per recording: detected 0 of
5 at finch size, 1 of 5 at 1,380, and every time from 2,745 up. Replicates in which order 2
generalises better than order 1 in most recordings (D1 majority) were detected 7 of 7 times;
the others 1 of 10. All 7 registered predictions came true (Brier 0.120). Every replicate
passed the published shuffle and rotation controls.

**3. Finch, real data: the Zipf structure is matched by second-order syllable rules, and so
is English at the same size.** [RESULTS-FINCH.md](RESULTS-FINCH.md). On the authors' own song
strings and code we reproduce their numbers (mean R^2 0.889 against 0.89; bigram z 6.94 against
6.77). A second-order Markov chain fitted to each recording, with no words in it, gives song as
Zipfian as the real song (p = 0.137); a first-order chain does not (p = 0.001). Label:
`EXPLAINED_BY_SECOND_ORDER`. Because real English at the same size also fails to beat the
second-order chain (results 2 and 4), this is reported as not distinguishable from what real
English gives, not as evidence that finch song lacks words.

**4. Human-language positive control.** [RESULTS-CDS.md](RESULTS-CDS.md). At finch size (30 x
about 650 phonemes) English does not beat the second-order chain (p = 0.49); at whale size (8 x
about 6,150 phonemes) it beats every null (z = 5.6, p = 0.005).

**5. Calibrations on song whose truth is known.** Wordless song at whale size reproduces the
whale paper's Zipf numbers and passes both of its controls 20 of 20 times
([RESULTS-CALIB-2.md](RESULTS-CALIB-2.md)) and passes its brevity controls 20 of 20 times
([RESULTS-CALIB-4.md](RESULTS-CALIB-4.md)); units whose true relation is the reverse of
brevity are still reported as brevity-following ([RESULTS-CALIB-3.md](RESULTS-CALIB-3.md));
wordless song passes the finch paper's controls 20 of 20 times
([RESULTS-CALIB.md](RESULTS-CALIB.md)).

**Where this leaves the two papers.** The controls both papers rely on (shuffling and
rotation) are passed alike by English, finch song, whale song and song with no words. A Markov
chain fitted to each species' own transitions reproduces its Zipf law at the registered
threshold. Whether either species has word-like units is still open: at the data sizes
published, the held-out check says this kind of test cannot tell. D1 costs nothing to run, and
we suggest reporting it next to any animal-song Zipf result.

## Still running

* **An animal positive control: canary song** ([CANARY-PREREG.md](CANARY-PREREG.md);
  `canary.py`). Canary phrase sequences are known to follow rules that reach three or more
  phrases back (Markowitz et al. 2013; Cohen et al. 2020, *Nature*). Three canaries from a
  public CC0 dataset (Cohen 2022), about 30,000 s of song each, read as phrase sequences. A
  held-out likelihood ladder measures whether order 3 beats order 2 in each bird; then the same
  Zipf test asks whether the song beats second- and third-order chains. If the ladder sees
  syntax the Zipf test cannot, the test is blind to real animal syntax. Queued as
  `song-zipf-canary-v1`, registered before any canary data were read.
* **Finch song in other birds, at full size** ([XPOP-PREREG.md](XPOP-PREREG.md);
  `finch_xpop.py`): two public, hand-annotated Bengalese finch datasets from other recordings
  (Koumura & Okanoya 2016, 11 birds; Nicholson, Queen & Sober, 4 birds from a different
  laboratory), at about 18,000 to 20,000 notes per bird instead of about 700, with a
  third-order chain added. Queued as `song-zipf-xpop-v1`; its grader (`test_xpop_results.py`)
  was published before it ran. Its code was published without passing the repository's
  pre-commit test step (see the commit message); the job runs the same unit tests as its first
  step and its log will be published with the result.

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
  [CALIB-4-PREREG.md](CALIB-4-PREREG.md), [CDS-PREREG.md](CDS-PREREG.md),
  [CDS-SIZE-PREREG.md](CDS-SIZE-PREREG.md), [XPOP-PREREG.md](XPOP-PREREG.md),
  [CANARY-PREREG.md](CANARY-PREREG.md): later calibrations, the human-language control, the
  independent-bird test and the canary positive control, each registered before it ran.
* `grade_final.py`: the final reading of the finch result, published before any result.
* `test_cds_size_results.py`, `test_xpop_results.py`: graders published before their jobs ran.
  `test_whale_results.py` was written before the whale job finished but published with its
  result (see RESULTS-WHALE.md). Each re-derives every label, prediction, rule and Brier score
  from the raw output with its own code.
* [PRIOR-ART.md](PRIOR-ART.md): what has and has not been done before.

## Code

* `zipfseg.py`: segmentation, the Zipf R^2 and the null models (pure Python).
* `calib.py`, `calib2.py`, `calib3.py`, `calib4.py`: the synthetic calibrations.
* `cds_job.py`, `cds_size.py`: the human-language positive control and its size curve.
* `finch_xpop.py`: the independent-bird finch test (Koumura and Nicholson datasets).
* `canary.py`: the canary positive control (reads only the annotation csv inside each zip, by
  HTTP Range requests; audio is never downloaded).
* `glyph_finch.py`, `finch_parse.py`, `job_analyze.py` (and the retired `ocr_finch.py`): finch stages.
* `whale_read.py`, `whale_test.py`, `whale_stage0.py`, `whale_run.py`: whale stages.
* Tests: `python -m unittest -v test_zipfseg test_finch_parse test_glyph_finch test_calib
  test_grade_final test_calib_results test_calib2 test_calib3 test_calib4 test_whale_test
  test_whale_run test_cds_job test_cds_size test_finch_xpop test_canary test_finch_results
  test_calib2_results test_calib3_results test_calib4_results test_cds_results
  test_cds_size_results test_whale_results test_xpop_results`. The `test_*_results.py` files
  re-derive every number in the RESULTS files from `results/`.

Raw data are not redistributed here. The finch data of Kirby et al. are CC BY-NC (regenerate
them from the authors' supplement with `glyph_finch.py`); the whale data are released for
reproducing or extending the Zipfian analysis (`results/whale/` holds derived statistics only);
the Brent-Ratner corpus is fetched from TalkBank/CHILDES at run time; the Koumura & Okanoya and
Nicholson, Queen & Sober finch datasets (CC BY 4.0) and the Cohen 2022 canary annotations (CC0)
are fetched at run time.

Made with AI agents working in MV2's name. Code Apache-2.0; text CC BY 4.0.
Contact: MV2, Munim, Inc., mv2@munimtech.com
