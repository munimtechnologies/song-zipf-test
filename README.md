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

**Manuscript:** [paper/DRAFT.md](paper/DRAFT.md) (working draft v0.4, not peer reviewed).

## Results so far (2026-11-19)

**1. With its repeats removed, humpback song shows no structure beyond a second-order chain on
unseen song, although the same test finds English words at the same size.**
[RESULTS-HOLDC.md](RESULTS-HOLDC.md). The held-out test of result 4, unchanged, on the whale
song with every tandem repeat collapsed, against 1,000 second-order chains generated under the
same collapse rule: mean gain -0.1454 bits per element against -0.0955 for the surrogates,
p = 1.0000 (`NOT_DETECTED_WITH_POWER`); looking 3-5 elements back loses to looking 2 back in all
8 years. English recordings matched to the collapsed whale's size were detected in 5 of 5
replicates; none of the 5 English negative controls, the whale negative control or the 3
collapsed repetition-only songs was detected (`CONTROL_OK`). Song made of second-order chains with random
repeats was not detected either (0 of 3; `REPETITION_DOES_NOT_FOOL_HOLD`). So the structure
beyond second order that result 4 found lives in the song's repeats, though not in memoryless
random repetition; our reading (not yet tested) is that it lies in how the whale repeats, such as
how many times a cell is sung. 4 of 7 registered predictions came true (Brier 0.189).

**2. Finch song in 15 other birds, at full size: "above the bigram" does not replicate
(provisional).** [RESULTS-XPOP.md](RESULTS-XPOP.md). Two public, hand-annotated Bengalese finch
datasets (Koumura & Okanoya 2016, 11 birds; Nicholson, Queen & Sober, 4 birds from another
laboratory), about 20,000 notes per bird. Neither beats the within-bout bigram null that
Kirby et al.'s finch song beat (rule X1 `ABOVE_BIGRAM_FAILS`): the Koumura birds' chunk
inventories are less Zipfian than every structured null (bigram z = -10.44; Markov orders 1-3
z = -8.3 to -16.3), and the Nicholson birds are level with the bigram null (p = 0.468). Yet on
held-out song a third-order chain beats a second-order one in 11 of 11 Koumura birds: the
Zipf statistic misses sequence structure a held-out likelihood finds in every bird. The
Koumura reading gate failed (19,548.8 notes per bird against the paper's 17,930.9; limit 5%),
so every XPOP result is provisional; the Nicholson gate passed. 4 of 11 registered
predictions came true (Brier 0.331).

**3. Whale song's "words" are largely repeats.** [RESULTS-RUNS.md](RESULTS-RUNS.md).
Collapsing every within-recording tandem repeat (a cell of 1-8 elements sung twice or more in a
row) removes 0.6290 of the whale's elements, against 0.4982 (sd 0.0072) in second-order
surrogates of the same song (p = 0.005); real English loses about 1%, less than its own
surrogates. 35 of the 80 most frequent whale "words" (ten per year) contain an immediate repeat
or an x-y-x alternation, against 26.89 in surrogates (p = 0.005). With repeats removed, the
Zipf fit falls from 0.9303 to 0.8962 and a first-order chain matches it (p = 0.0659), but the
registered power check failed (0 of 8 collapsed years), so the Zipf test cannot say whether
anything beyond repetition is left (`EXPLAINED_BY_FIRST_ORDER_UNDERPOWERED`); result 1 answers
that with the held-out test. Collapsed English still beats the second-order chain in 6 of 6
replicates; 0 of 3 negative controls do. 7 of 9 registered predictions came true (Brier 0.119).

**4. A held-out test sees what the Zipf test missed: whale song has structure beyond a
second-order chain on unseen song.** [RESULTS-HOLD.md](RESULTS-HOLD.md). We asked directly
whether looking 3-5 elements back helps predict held-out song (leave-one-bout-out, Witten-Bell
smoothing), against Markov-2 surrogates of the same data. Calibrated on real English, this test
found the words in 17 of 17 replicates, including 5 of 5 at about 650 phonemes per recording,
where the Zipf test found 0 of 5; it flagged 0 of 17 English negative controls. On the whale
data, the held-out gain is -0.0490 bits per element against -0.0783 (sd 0.0048) for the
surrogates, p = 0.005; the whale negative control is not detected. Limits: on average, looking
further back still does not beat order 2 outright (prediction H7 failed); the effect is clear in
4 of 8 years; the null proved conservative (every negative control gave p = 1.000). Result 1
shows that this structure is gone once the song's repeats are collapsed. 7 of 9 registered
predictions came true (Brier 0.164).

**5. Whale, Zipf test on real data: the Zipf law is fully reproduced by a second-order chain
fitted to the song's own transitions.** [RESULTS-WHALE.md](RESULTS-WHALE.md). On the authors'
own data and code we reproduce their Zipf R^2 to the last digit (0.9302888665216728 against
Code S1's 0.9302888665216734) and their top chunk in 8 of 8 years. The song beats the paper's
controls and a first-order chain, but a second-order chain with no words in it gives song that
is more Zipfian than the real song (R^2 0.939 against 0.930, p = 0.970). Label
`NOT_DISTINGUISHABLE` (not robust: at the loosest thresholds, 0.25 and 0.3, the song does beat
that chain). Our brevity statistic did not reproduce the paper's R^2 of 0.62 (we got 0.021), so
no brevity label is drawn; that is a gap in our reproduction, not evidence against the paper.

**6. English size curve: the Zipf test finds real words only from about 2,700 phonemes per
recording.** [RESULTS-CDS-SIZE.md](RESULTS-CDS-SIZE.md). 17 replicates of 8 recordings of
child-directed English, from 647 to 11,748 phonemes per recording: detected 0 of 5 at finch
size, 1 of 5 at 1,380, and every time from 2,745 up. All 7 registered predictions came true
(Brier 0.120). The held-out test of result 4 detects all 17.

**7. Finch, Kirby et al.'s data: the Zipf structure is matched by second-order syllable rules,
and so is English at the same size.** [RESULTS-FINCH.md](RESULTS-FINCH.md). On the authors'
own song strings and code we reproduce their numbers (mean R^2 0.889 against 0.89; bigram z 6.94
against 6.77). A second-order Markov chain fitted to each recording gives song as Zipfian as
the real song (p = 0.137); a first-order chain does not (p = 0.001). Label:
`EXPLAINED_BY_SECOND_ORDER`. Because real English at the same size also fails this test
(results 6 and 9), this is not evidence that finch song lacks words. Result 2 shows the
"above the bigram" effect itself does not carry over to other birds at full size.

**8. Canary positive control: no ground truth at this size.**
[RESULTS-CANARY.md](RESULTS-CANARY.md). Canary phrase syntax is reported to reach three or more
phrases back, but in all three birds of the public Cohen 2022 dataset (about 3,000 phrases per
recording) a held-out likelihood ladder found order 3 worse than order 2, so rule C1 is
`NO_GROUND_TRUTH` and the run cannot say whether the Zipf test is blind to animal syntax. The
Zipf labels themselves flip with the cutting threshold in two of three birds. 2 of 8 registered
predictions came true (Brier 0.355).

**9. Human-language positive control.** [RESULTS-CDS.md](RESULTS-CDS.md). At finch size (30 x
about 650 phonemes) English does not beat the second-order chain with the Zipf test (p = 0.49);
at whale size (8 x about 6,150 phonemes) it beats every null (z = 5.6, p = 0.005).

**10. Calibrations on song whose truth is known.** Wordless song at whale size reproduces the
whale paper's Zipf numbers and passes both of its controls 20 of 20 times
([RESULTS-CALIB-2.md](RESULTS-CALIB-2.md)) and passes its brevity controls 20 of 20 times
([RESULTS-CALIB-4.md](RESULTS-CALIB-4.md)); units whose true relation is the reverse of
brevity are still reported as brevity-following ([RESULTS-CALIB-3.md](RESULTS-CALIB-3.md));
wordless song passes the finch paper's controls 20 of 20 times
([RESULTS-CALIB.md](RESULTS-CALIB.md)).

**Where this leaves the two papers.** The controls both papers rely on (shuffling and
rotation) are passed alike by English, finch song, whale song, canary song and song with no
words. The Zipf-of-chunks statistic is a weak and unstable instrument: it misses real English
words below about 2,700 phonemes per recording, cannot separate whale song from a second-order
chain, flips with recording size and threshold in finch song, and misses the third-order
structure that a held-out likelihood finds in 11 of 11 finch birds. The finch paper's "above
the bigram" effect did not appear in 15 other birds at full size (provisional). A calibrated
held-out prediction test does better. In whale song it finds structure beyond second order, but
that structure is carried by the song's repeats: the top "words" are largely repeated cells, the
song repeats far more than the chain that matches its Zipf law, and once the repeats are
collapsed the held-out test finds nothing beyond a second-order chain, while it still finds
English words at the same size. On these data, the structure behind the whale's "language-like"
chunks is phrase repetition plus short-range element rules.

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
  [CANARY-PREREG.md](CANARY-PREREG.md), [HOLD-PREREG.md](HOLD-PREREG.md),
  [RUNS-PREREG.md](RUNS-PREREG.md), [HOLDC-PREREG.md](HOLDC-PREREG.md): later calibrations,
  the human-language control, the independent-bird test, the canary positive control, the
  held-out prediction test, the repeat-collapse test and the held-out test on collapsed song,
  each registered before it ran.
* [CANARY-AMENDMENT-1.md](CANARY-AMENDMENT-1.md): a test-only fix for the canary job, before
  any canary data were read.
* [XPOP-AMENDMENT-1.md](XPOP-AMENDMENT-1.md): a test fix and a `._*` reading guard for the
  independent-bird job, before any finch data were downloaded.
* `grade_final.py`: the final reading of the finch result, published before any result.
* `test_cds_size_results.py`, `test_xpop_results.py`, `test_canary_results.py`,
  `test_hold_results.py`, `test_runs_results.py`, `test_holdc_results.py`: graders published
  before their jobs ran. `test_whale_results.py` was written before the whale job finished but
  published with its result (see RESULTS-WHALE.md). Each re-derives every label, prediction,
  rule and Brier score from the raw output with its own code.
* [PRIOR-ART.md](PRIOR-ART.md): what has and has not been done before.

## Code

* `zipfseg.py`: segmentation, the Zipf R^2 and the null models (pure Python).
* `calib.py`, `calib2.py`, `calib3.py`, `calib4.py`: the synthetic calibrations.
* `cds_job.py`, `cds_size.py`: the human-language positive control and its size curve.
* `hold.py`: the held-out prediction test (Witten-Bell orders 0-5 against Markov-2 surrogates).
* `runs.py`: the repeat-collapse test (tandem-repeat collapse, collapse-consistent Markov nulls).
* `holdc.py`: the held-out test on collapsed song (imports `hold.py` and `runs.py` unchanged).
* `finch_xpop.py`: the independent-bird finch test (Koumura and Nicholson datasets);
  `xpop_v2.py` runs it unchanged with the XPOP-AMENDMENT-1 reading guard.
* `canary.py`: the canary positive control (reads only the annotation csv inside each zip, by
  HTTP Range requests; audio is never downloaded).
* `glyph_finch.py`, `finch_parse.py`, `job_analyze.py` (and the retired `ocr_finch.py`): finch stages.
* `whale_read.py`, `whale_test.py`, `whale_stage0.py`, `whale_run.py`: whale stages.
* Tests: `python -m unittest -v test_zipfseg test_finch_parse test_glyph_finch test_calib
  test_grade_final test_calib_results test_calib2 test_calib3 test_calib4 test_whale_test
  test_whale_run test_cds_job test_cds_size test_xpop_v2 test_canary test_hold test_runs
  test_holdc test_finch_results test_calib2_results test_calib3_results test_calib4_results
  test_cds_results test_cds_size_results test_whale_results test_xpop_results
  test_canary_results test_hold_results test_runs_results test_holdc_results`. The
  `test_*_results.py` files re-derive every number in the RESULTS files from `results/`.
  (`test_xpop_v2` runs every test of `test_finch_xpop` with the one correction in
  XPOP-AMENDMENT-1.md.)

Raw data are not redistributed here. The finch data of Kirby et al. are CC BY-NC (regenerate
them from the authors' supplement with `glyph_finch.py`); the whale data are released for
reproducing or extending the Zipfian analysis (`results/whale/`, `results/hold/`,
`results/runs/` and `results/holdc/` hold derived statistics and the most frequent chunks only);
the Brent-Ratner corpus is fetched from TalkBank/CHILDES at run time; the Koumura & Okanoya and
Nicholson, Queen & Sober finch datasets (CC BY 4.0) and the Cohen 2022 canary annotations (CC0)
are fetched at run time (`results/xpop/` holds per-bird label counts and statistics only).

Made with AI agents working in MV2's name. Code Apache-2.0; text CC BY 4.0.
