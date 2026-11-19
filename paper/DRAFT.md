# Zipf's law of chunks is a weak test for language-like units in animal song: calibrated Markov nulls, held-out prediction and repetition in humpback whale and Bengalese finch song

**MV2, Munim, Inc.** (mv2@munimtech.com)

Working draft v0.4, 2026-11-19. Not peer reviewed. The analyses, code and text were made with
AI agents working in MV2's name; no human expert has checked them yet. Text CC BY 4.0; code
Apache-2.0. Repository: https://github.com/munimtechnologies/song-zipf-test (every number below
is from a results file there; file names are given in brackets).

**Status of this draft.** Every section reports tests that were pre-registered, run and graded
by code published before the result. The last registered test (HOLDC, Section 3.11) is now
graded, and the abstract and discussion have been revised to include it.

**Changes from v0.3.** (1) Added the graded HOLDC result (Section 3.11): with tandem repeats
collapsed, the held-out test finds no structure beyond second order in whale song, while it
still finds English words at the same size. (2) Revised the abstract, the whale part of the
discussion and the recommendation accordingly. (3) Unregistered, exploratory numbers in 3.11
are marked as such.

**Changes from v0.2.** (1) Added four graded tests: HOLD (held-out prediction), RUNS
(repetition), XPOP (15 independent finches, provisional) and CANARY (positive control without
ground truth). (2) Corrected a claim. v0.2 said the whale data are in a low-power regime because
an add-0.5-smoothed held-out check (D1) favoured order 2 over order 1 in only 1 of 8 years. With
Witten-Bell smoothing, order 2 does predict unseen whale song better than order 1 (3.0322 against
3.2775 bits per element) [RESULTS-HOLD.md, H9], so that D1 result reflected the smoothing, not
the song, and the low-power reading is withdrawn. The Zipf test's power on English at whale size
(Section 3.6) is unaffected. (3) The title and conclusion now rest on the comparison between the
Zipf statistic and a held-out likelihood, which v0.2 did not have.

## Abstract

Two recent papers report that chunks of animal song, cut where the transitional probability
between elements dips, follow Zipf's rank-frequency law and Zipf's law of brevity, as words in
human languages do: humpback whale song (Arnon et al. 2025, *Science*; mean R^2 0.93) and
Bengalese finch song (Kirby et al. 2026, *Science Advances*; mean R^2 0.89). We reproduced both
analyses from the authors' data and code and tested them in a series of pre-registered,
calibrated experiments. (i) The published controls (shuffled and rotated sequences, and for the
finch a within-bout bigram resampling) are passed by synthetic song with no words, and the
published pipeline reports a law of brevity even when the true units obey the opposite law.
(ii) A second-order Markov chain fitted to each recording reproduces the Zipf fit of real song in
both species (finch p = 0.137; whale p = 0.970). (iii) On real child-directed English the Zipf
test finds words beyond a second-order phoneme chain only from about 2,700 phonemes per
recording (0 of 5 replicates at finch size). (iv) A held-out prediction test (does looking 3-5
elements back help predict unseen bouts, against Markov-2 surrogates?) finds the English words in
17 of 17 replicates, including 5 of 5 at finch size, with 0 of 17 false alarms, and finds
structure beyond second order in whale song (held-out gain -0.0490 against -0.0783 bits per
element, p = 0.005) that the Zipf test could not see. (v) Whale song repeats its cells far more
than the second-order chain that matches its Zipf law: collapsing tandem repeats removes 63% of
its elements against 50% in surrogates (p = 0.005), and 35 of its 80 most frequent "words" are
repetition cells against 26.89 expected. (vi) With the repeats collapsed, the held-out test finds
nothing beyond a second-order chain in whale song (gain -0.1454 against -0.0955, p = 1.000;
looking further back loses in all 8 years), although it detects English words in 5 of 5
replicates of the same size; song made of second-order chains with memoryless random repeats is
not detected either, so the whale's extra structure lies in how it repeats, not in the order of
distinct cells. (vii) In 15 adult Bengalese finches from two independent datasets at about
20,000 notes per bird, the finch paper's "above the bigram" effect did not appear (provisional:
one reading gate failed), while a third-order chain beat a second-order chain on held-out song
in 11 of 11 birds. The Zipf statistic of transitional-probability chunks is weak (it misses
structure a held-out likelihood finds in both species), unstable (its verdict changes with the
cutting threshold and recording size) and not monotone in the order of the null. On the whale
data, the structure behind the "language-like" chunks is phrase repetition plus short-range
element rules. We recommend held-out likelihood against fitted surrogates, calibrated on real
language at matched size and checked after collapsing repeats, over rank-frequency statistics
for claims of language-like units.

## 1. Introduction

Zipf's rank-frequency law and the law of brevity are among the best-known regularities of human
language, and finding them in animal communication has been read as a sign of language-like
units and of efficient coding. Arnon et al. (2025) segmented eight years of humpback whale song
(New Caledonia, 2010-2017) with a statistical-learning method inspired by infant word
segmentation: cut the element stream wherever the transitional probability (TP) drops relative
to the previous one, by a ratio threshold theta (0.5 in the main analysis). The resulting
sub-sequences had a rank-frequency distribution with mean R^2 0.93 on log-log axes, above
shuffled (z 23.09) and rotated (z 14.43) controls, and frequent sub-sequences were shorter
(R^2 0.62). Kirby et al. (2026) applied the same method to Bengalese finch song (30 recordings,
6 birds) and found mean R^2 0.89, above a within-bout bigram control (z 6.77), and concluded that
the effect arises from sequential structure above the bigram.

Zipf-like rank-frequency curves are produced by many processes without words, from random typing
(Li 1992) onward, and the published discussion of the whale paper made this point. What was
missing was a test of the specific claim: is there structure in the song, visible to this
statistic, that short-range element rules do not produce? Bengalese finch syntax is known to need
second-order or hidden-state models (Katahira et al. 2011; Jin & Kozhevnikov 2011) and depends on
longer context in neural-network language models (Morita et al. 2021); canary phrase syntax is
reported to depend on phrases three or more steps back (Markowitz et al. 2013; Cohen et al.
2020); and humpback song is organised into phrases that are repeated many times before the next
theme (Payne & McVay 1971; Suzuki et al. 2006). A Markov chain fitted to the song's own
transitions is therefore the natural null. Charpentier (2026) argued that scaling laws such as
Zipf's are equifinal and called for stronger, segmentation-aware surrogates for both papers, but
analysed no recordings. We found no published test of either paper against a fitted Markov null,
none of the TP-chunk Zipf test's power on human language at matched sizes, and no comparison of
the Zipf statistic with a held-out likelihood on the same data.

We ran the tests openly, in a fixed order: every test was registered in the public repository
before its job read any data, every job checked that its registration was public before
analysing, and a grader that re-derives every label from the raw output was published before the
result where possible.

## 2. Data and methods

**Data.** Whale: Data S2 of Arnon et al. (2025), 55 recordings, 8 song types (years), 45,749
elements; each year is treated as one recording and its recordings as bouts. Finch (Kirby): the
song strings printed in the supplement of Kirby et al. (2026), 30 recordings, 299 bouts, 19,990
transitions, read from the PDF by glyph matching and checked against all five registered totals
(the data are CC BY-NC and are not redistributed). Finch (independent): Koumura & Okanoya (2016),
11 adult birds, 215,037 notes, and the Nicholson, Queen & Sober repository, 4 adult birds, 80,283
syllables (both CC BY 4.0). Canary: the three birds of the Cohen et al. (2022) annotations (CC0),
read as phrase sequences (runs of one syllable label). English: the Brent-Ratner corpus of
child-directed speech in phonemic transcription (9,790 utterances, 95,809 phonemes, 50 phoneme
types), word spaces removed, one utterance per bout.

**Segmentation and Zipf statistic.** We used the authors' own code (Code S1 of each paper):
forward TPs estimated per recording set, a cut wherever TP(i)/TP(i-1) < theta, chunk counts per
recording, and the Pearson R^2 of log count on log rank. The registered threshold is theta 0.5;
other thresholds were run as robustness checks.

**Nulls for the Zipf statistic.** Shuffle and rotation (the papers' controls); within-bout bigram
and trigram resampling; and pooled Markov chains of order 1-3 fitted to each recording set, which
keep the number and lengths of bouts. One-sided empirical p = (1 + #{null >= real}) / (1 + B).

**Held-out prediction test (HOLD).** For each recording, leave-one-bout-out cross-entropy of
interpolated Witten-Bell models of order 0-5. The statistic is the gain H_2 - min(H_3, H_4, H_5),
averaged over recordings, compared with the same statistic on B Markov-2 surrogate data sets
fitted to the same data. Calibration: the 17 English replicates of Section 3.6, each with a
Markov-2 negative control, and a whale negative control (each year replaced by its own Markov-2
surrogate).

**Repetition (RUNS).** Every within-recording tandem repeat (a cell of 1-8 elements sung twice
or more in a row) is collapsed to one copy, shortest period first. T2 compares the share of
elements removed with second-order surrogates; T3 counts top-ten chunks containing an immediate
repeat (x x) or alternation (x y x); T1 reruns the Zipf test on the collapsed song against chains
generated under the same collapse rule.

**Held-out test on collapsed song (HOLDC).** HOLD, unchanged, on the collapsed whale song,
against B = 1,000 second-order chains generated under the same collapse rule. Controls fixed in
advance: English recordings each holding at least as many phonemes as the matching collapsed
whale year, collapsed the same way (5 replicates, each with a negative control); a
collapse-consistent whale negative control; and repetition-only song (square-free second-order
surrogates of the collapsed whale re-inflated with memoryless random repeats to about the whale's
collapse share; 3 data sets), tested both uncollapsed and collapsed.

**Calibration with known truth.** Synthetic song (first- and second-order chains with no words;
lexicons of 12 words with Zipf, equal, brevity or anti-brevity weights; 2-10% element noise) at
finch and whale size, 20 replicates each; and real English at five sizes (70 to 1,200 utterances
per recording; 17 replicates of 8 recordings).

## 3. Results

### 3.1 Both analyses reproduce

Whale: Zipf R^2 0.9302888665216728 against Code S1's printed 0.9302888665216734, the most
frequent chunk of Table S2 reproduced with its count in 8 of 8 years [RESULTS-WHALE.md]. Finch:
3,205 cuts and 1,043 chunk types at theta 0.5, exactly as published; mean R^2 0.889 (published
0.89) and bigram z 6.94 (published 6.77); our cut positions agree with the boundaries printed in
the supplement at all 3,098 within-line positions [RESULTS-FINCH.md]. The whale brevity R^2 of
0.62 was not reproduced by our registered statistic (0.021); Code S1 does not compute 0.62, so we
draw no conclusion about the paper's brevity result.

### 3.2 The published controls are passed by song with no words

At finch size, wordless first-order song gave mean R^2 0.848 and beat both shuffle and rotation
in 20 of 20 replicates [RESULTS-CALIB.md]. At whale size, wordless first-order song gave mean
R^2 0.917 and beat both controls in 20 of 20 replicates, while clean word-like song beat them in
only 10 of 20, because its rotated copies were as Zipfian as the song itself [RESULTS-CALIB-2.md].

| source (whale size, 20 replicates) | words? | mean R^2 | passes shuffle + rotation |
|---|---|---|---|
| first-order chain, 12 elements | no | 0.917 | 20/20 |
| first-order chain, 24 elements | no | 0.910 | 20/20 |
| second-order chain, 12 elements | no | 0.692 | 20/20 |
| 12-word lexicon, Zipf weights | yes | 0.916 | 10/20 |
| same with 10% element noise | yes | 0.910 | 20/20 |
| *whale song (Arnon et al. 2025)* | ? | *0.93* | *yes* |

### 3.3 The law of brevity comes from the cutting

When the true words of a 12-word lexicon are longer the more frequent they are, the published
pipeline reported significant brevity in 20 of 20 replicates and anti-brevity in none
[RESULTS-CALIB-3.md]. At whale size, wordless song passed the whale paper's two brevity controls
in 20 of 20 replicates in all three wordless scenarios [RESULTS-CALIB-4.md].

### 3.4 Finch (Kirby et al.'s data): matched by second-order syllable rules

Real finch song beat shuffle, rotation, within-bout bigram and the pooled first-order chain (all
p = 0.001), but not the pooled second-order chain (null mean R^2 0.879 against 0.889; p = 0.137):
EXPLAINED_BY_SECOND_ORDER [RESULTS-FINCH.md]. Real English at the same size gives the same label
(p = 0.49) [RESULTS-CDS.md], so this is not evidence that finch song lacks units.

### 3.5 Whale: matched by a second-order element chain

| null (B = 1,000) | null mean R^2 | z | p |
|---|---|---|---|
| shuffle (paper's control) | 0.739 | 23.83 | 0.001 |
| rotation (paper's control) | 0.876 | 13.90 | 0.001 |
| within-year bigram | 0.905 | 5.02 | 0.001 |
| pooled first-order chain | 0.900 | 5.81 | 0.001 |
| within-year trigram | 0.943 | -2.73 | 0.991 |
| **pooled second-order chain** | **0.939** | **-2.00** | **0.970** |

Real whale R^2 0.930. A second-order chain fitted to each year's song gives chunks that are more
Zipfian than the real song [RESULTS-WHALE.md]. The label is not robust: at theta 0.25 and 0.3
the real song beat the pooled second-order chain (p = 0.010 and 0.030; B = 200). The registered
rule reports NOT_DISTINGUISHABLE.

### 3.6 Positive control: real English words, and how much data the Zipf test needs

| phonemes per recording | 647 | 1,380 | 2,745 | 5,874 | 11,748 |
|---|---|---|---|---|---|
| Zipf test detects English (theta 0.5) | 0/5 | 1/5 | 4/4 | 2/2 | 1/1 |
| held-out test (HOLD) detects English | 5/5 | 5/5 | 4/4 | 2/2 | 1/1 |

The Zipf test labelled English BEYOND_SECOND_ORDER only from about 2,700 phonemes per recording
[RESULTS-CDS-SIZE.md]; the published shuffle and rotation controls were passed in all 17
replicates regardless. At whale size English beat every null (z 5.6, p = 0.005) [RESULTS-CDS.md],
so at whale size the Zipf test can see real words. The threshold matters as much as the size: at
theta 0.3 English was detected in 17 of 17 replicates, at theta 0.7 in none.

### 3.7 A held-out test sees structure in whale song that the Zipf test missed (HOLD)

**Calibration.** The held-out test detected English words in 17 of 17 replicates (table above),
including 5 of 5 at 647 phonemes per recording, and flagged none of the 17 English negative
controls, nor the whale negative control (rule R1: HOLD_MORE_POWERFUL; R3: CONTROL_OK) [RESULTS-HOLD.md].
Unpredicted: every negative control gave p = 1.000 rather than a spread of p values. A chain
refitted to a chain's output scores a higher gain than its source, so on true second-order data
this plug-in null leans against detection. The whale result below is therefore conservative,
but the p values are not exact under the null.

**Whale.** Mean held-out gain -0.0490 bits per element, against -0.0783 (sd 0.0048) for 200
Markov-2 surrogates of the same song: p = 0.005, the smallest value 200 surrogates allow
(BEYOND_SECOND_ORDER_HELDOUT). The same data could not be told from a second-order chain by the
Zipf test (Section 3.5; p = 0.970). The effect is not uniform: it is clear in 4 of 8 years
(2013-2016, p = 0.005 each), and only in 2013 does order 3 predict better than order 2 outright.
On average, looking further back still costs a little (the gain is negative; prediction H7
failed); it costs much less than it would if the song were a second-order chain. 7 of 9
registered predictions came true (Brier 0.164).

| year | elements | H1 | H2 | H3 | gain | surrogate mean gain | p |
|---|---|---|---|---|---|---|---|
| 2010 | 1,053 | 4.0365 | 3.9147 | 3.9634 | -0.0487 | -0.0570 | 0.363 |
| 2011 | 2,028 | 3.7237 | 3.4464 | 3.5309 | -0.0844 | -0.0811 | 0.582 |
| 2012 | 3,351 | 2.8192 | 2.6902 | 2.7957 | -0.1055 | -0.0718 | 1.000 |
| 2013 | 2,664 | 3.1326 | 2.8422 | 2.8240 | +0.0181 | -0.0790 | 0.005 |
| 2014 | 5,765 | 3.2334 | 2.9324 | 2.9671 | -0.0346 | -0.0977 | 0.005 |
| 2015 | 14,429 | 2.1933 | 1.8909 | 1.8946 | -0.0037 | -0.0553 | 0.005 |
| 2016 | 7,282 | 3.8292 | 3.5589 | 3.5953 | -0.0364 | -0.0866 | 0.005 |
| 2017 | 9,177 | 3.2526 | 2.9821 | 3.0793 | -0.0971 | -0.0978 | 0.498 |

(Held-out entropy in bits per element; gain = H2 - min(H3, H4, H5).)

### 3.8 The extra whale structure is at least partly repetition (RUNS)

Collapsing every within-recording tandem repeat removes 0.6290 of the whale's elements on
average over the 8 years; second-order surrogates of the same years lose 0.4982 (sd 0.0072), and
none of 200 reached the real value (p = 0.005; REPETITION_BEYOND_SECOND_ORDER) [RESULTS-RUNS.md].
Real English goes the other way: collapsing removes about 1% of its phonemes, less than its own
surrogates. Of the ten most frequent chunks in each year (80 in all, the rule of the paper's
Table S2), 35 contain an immediate repeat or an alternation, against 26.89 (sd 2.32) in
surrogates (p = 0.005; MOTIFS_BEYOND_SECOND_ORDER); the recount matches a hand count of 35 from
Table S2 made before registration. Examples: "gr(s)-dws(s) sq sq sq" (the most frequent chunk of
2015), and in 3 of 8 years the top ten list the same cell at two or more run lengths.

With repeats removed, the Zipf R^2 falls from 0.9303 to 0.8962; a first-order chain generated
under the same collapse rule matches it (p = 0.0659), and a second-order chain makes song more
Zipfian than the real song (p = 1.0000). Collapsing leaves only 248 to 4,403 elements per year,
and the registered D1 power check (add-0.5 smoothing) failed in all 8 collapsed years, so the label is
EXPLAINED_BY_FIRST_ORDER_UNDERPOWERED. Collapsed English still beats the second-order chain in 6
of 6 replicates, and 0 of 3 whale negative controls do. 7 of 9 registered predictions came true
(Brier 0.119).

### 3.9 Finch song in 15 other birds: "above the bigram" does not replicate (XPOP, provisional)

At about 20,000 notes per bird, neither independent dataset beat the within-bout bigram null at
theta 0.5 (rule X1: ABOVE_BIGRAM_FAILS) [RESULTS-XPOP.md]. In the 11 Koumura & Okanoya birds the
real chunk inventory is less Zipfian than every structured null (real R^2 0.906; bigram 0.942,
z -10.44; Markov orders 1-3, z -8.34 to -16.34); the same holds when each annotated sequence is
kept as its own bout, without our rejoining of songs (real 0.881). In the 4 Nicholson, Queen &
Sober birds the real song is level with the bigram null (gap +0.000, p = 0.468) and with a
first-order chain (p = 0.358). At Kirby et al.'s recording size the Koumura birds just beat the
bigram null (p = 0.043) and the Nicholson birds clearly do (p = 0.001): the effect depends on
recording size and dataset.

On held-out song, a third-order chain predicts better than a second-order chain in 11 of 11
Koumura birds (mean D2 +0.0508 nats per note) and in 2 of 4 Nicholson birds. Higher-order
dependence in Bengalese finch song is known (Katahira et al. 2011; Jin & Kozhevnikov 2011); what
is new is that the Zipf statistic, at 20,000 notes per bird, ranks this song below every
structured null that lacks it.

Two qualifications. The Koumura reading gate failed (19,548.8 notes per bird against the dataset
paper's 17,930.9; the registered limit was 5%), so the registration makes every XPOP result
provisional; the Nicholson gate passed and tells the same story for the bigram null. And in the
Nicholson data at theta 0.5 the Zipf statistic is not monotone in chain order: the first-order
chain's inventories are more Zipfian (0.947) than the second- and third-order chains' (0.940 and
0.942), so the song "beats" the higher-order chains (label BEYOND_THIRD_ORDER) without beating the
first-order one. We do not read that label as evidence of units. Kirby et al. studied song
development; these are adult birds, so this tests the pattern, not their developmental claim.
4 of 11 registered predictions came true (Brier 0.331); our priors expected replication.

### 3.10 Canary: a positive control without ground truth (CANARY)

We planned to use canary song, whose phrase syntax is reported to reach three or more phrases
back, as an animal positive control [RESULTS-CANARY.md]. In all three birds of the Cohen et al.
(2022) data, read as phrase sequences, an additively smoothed held-out ladder found order 3 worse
than order 2 (held-out log-likelihood gain g_2 from -0.0107 to -0.0327 per phrase), so by rule C1 there is no ground truth
(NO_GROUND_TRUTH) and this test says nothing about whether the Zipf test is blind to animal
syntax. The Zipf labels themselves changed with the threshold in 2 of 3 birds (at theta 0.3 two
birds beat every chain up to third order; at 0.5 none beat a first-order chain) and, against our
prior of 0.20, two birds beat the second-order chain at the smaller Kirby size but not at full
size. The long-range canary rules apply at a few branch points; a model class such as the
probabilistic suffix trees of Markowitz et al. (2013), or the Witten-Bell held-out test of
Section 3.7, may find what this ladder missed. We have not run them.

### 3.11 With repeats removed, nothing beyond second order is left in whale song (HOLDC)

**Calibration.** English recordings matched to the size of the collapsed whale years (16,708 to
16,758 phonemes per replicate before collapsing, 16,503 to 16,620 after, against 16,671 whale
elements) were detected in 5 of 5 replicates (gains +0.0709 to +0.1215 bits per phoneme, each
p = 0.0099, the smallest 100 surrogates allow); none of the 5 English negative controls, the
whale negative control or the 3 collapsed repetition-only songs was detected (CONTROL_OK)
[RESULTS-HOLDC.md].

**Whale.** On the collapsed song, the mean held-out gain is -0.1454 bits per element against
-0.0955 (sd 0.0089) for 1,000 collapse-consistent second-order surrogates; p = 1.000
(NOT_DETECTED_WITH_POWER). Looking 3-5 elements back predicts unseen song worse than looking 2
back in all 8 years (per-year gains -0.0975 to -0.1996), and order 1 is the best held-out order
in 4 of 8 years; on average order 2 beats order 1 by only 0.0437 bits (3.8126 against 3.8563).
Before collapsing, the same test detected the song at p = 0.005 (Section 3.7).

**Repetition alone.** Song made of square-free second-order chains re-inflated with memoryless
random repeats, to about the whale's collapse share (0.6229 to 0.6266 removed, against 0.6290),
was not detected uncollapsed in any of 3 data sets (REPETITION_DOES_NOT_FOOL_HOLD); we had
expected it to be (prior 0.80). 4 of 7 registered predictions came true (Brier 0.189).

**Reading.** By the registered reading rules, random repetition alone does not explain the HOLD
result, and once the repeats are removed nothing beyond second order is left, at a size where
English units are still found. The extra structure of Section 3.7 is therefore carried by the
song's repeats, but not by repetition as such. Our hypothesis, not yet tested, is that it lies in
how the whale repeats: run lengths that are more regular than the geometric run lengths a Markov
chain produces (a chain that remembers two elements cannot count to three), or repeats tied to
particular cells. Exploratory and not registered: in units of each test's null sd, the collapsed
whale sits at -5.6, inside the range of data drawn from second-order chains (whale negative
control -5.7; English negative controls -5.1 to -6.3; collapsed repetition-only song -3.2 to
-6.7), while the English replicates sit at +14.5 to +24.3.

## 4. Discussion

**The Zipf statistic is the weak instrument.** In both species the rank-frequency fit of TP-cut
chunks is reproduced by a fitted second-order chain with no words. The published controls are
passed alike by English, finch, whale and canary song and by song with no words; the law of
brevity follows from the cutting rule. On English the Zipf test misses real words below about
2,700 phonemes per recording, where a held-out test finds them every time. On whale song it
cannot separate the song from a second-order chain, where the held-out test can (p = 0.005). On
finch song at full size it ranks real song below every structured null even though a held-out
likelihood shows third-order dependence in every bird. Its verdicts move with the cutting
threshold (English, canary, finch) and with recording size, sometimes in the wrong direction
(canary, finch), and it is not monotone in the order of the null (Nicholson finches). A statistic
with these properties cannot carry a claim of language-like units in either direction.

**What the better instrument shows about whale song.** Whale song has sequential structure on
unseen song that a second-order chain does not reproduce, and it repeats its cells far more than
that chain does. Once the repeats are collapsed, the held-out test, which still finds English
words at the same size, finds nothing beyond a second-order chain, and in half the years nothing
beyond a first-order one. On these data the structure behind the "language-like" chunks is
phrase repetition plus short-range element rules, which whale biologists have described since
Payne & McVay (1971). The one new thing the held-out test points to is that the whale's
repetition is not memoryless: random repeats added to a second-order chain do not reproduce the
signal. Whether that is regular run length (singing a cell a set number of times) is a direct,
testable question for the next registration, and it bears on song learning and copying rather
than on words.

**What it does not show.** Neither species is shown to lack word-like units, or to have them.
"With power" here means power against structure as strong as English words at matched size;
weaker long-range order in the collapsed whale song could be missed. The tests concern
sequential statistics of human-coded element strings; they do not address meaning, which the
"language-like" framing ultimately concerns.

**A recommendation.** Before a rank-frequency or brevity law in animal sequences is read as
language-like: (1) test against a Markov chain fitted to the same data, at the order the species'
syntax is known to need, and check every lower order too (nulls need not be monotone in order);
(2) prefer a held-out likelihood test against fitted surrogates, with a smoothing method fixed in
advance (add-0.5 and Witten-Bell smoothing gave opposite answers on the same whale data); (3)
calibrate on real language at matched size and transcription granularity, with negative
controls drawn from the null; (4) collapse tandem repeats and test again, with a size-matched
positive control: in whale song this step removed all of the held-out structure beyond second
order.

## 5. Limits

One whale dataset (one population, 8 years, 55 recordings) with elements classified by human
listeners; finch data from two laboratories, one with a failed reading gate; canary data from one
laboratory without a usable ground truth; one human corpus, in phonemes (50 types) rather than
syllables, so "matched size" compares symbol counts, not information. The nulls are fitted to the
same data (plug-in), and the HOLD and HOLDC negative controls show that this null is conservative
rather than exact. The collapse rule (cells of 1-8 elements, shortest period first) was fixed in
advance; another rule could keep structure this one removes. Synthetic generators are simple; in
particular, the repetition-only control of HOLDC uses memoryless repeats. Many registered
predictions failed and are reported as such in each results file (for example, all of XPOP's
replication priors and three of HOLDC's seven). The work was carried out with AI agents working
in MV2's name and has not yet been checked by a human expert.

## 6. Data and code

All registrations, code (Apache-2.0), raw outputs and graders are in
https://github.com/munimtechnologies/song-zipf-test: PREREG.md and amendments, CALIB-*-PREREG.md,
CDS-PREREG.md, CDS-SIZE-PREREG.md, XPOP-PREREG.md, CANARY-PREREG.md, HOLD-PREREG.md,
RUNS-PREREG.md, HOLDC-PREREG.md; RESULTS-*.md with the `test_*_results.py` grader for each. The
whale data are those of Arnon et al. (2025), whose data statement allows their use "for the
purposes of reproducing or extending the Zipfian analysis"; the repository holds derived
statistics only. The Kirby et al. finch strings are regenerated from the authors' supplement by
`glyph_finch.py` and are not redistributed (CC BY-NC). The independent finch and canary datasets
and the English corpus are fetched at run time.

## References

* Arnon I, Kirby S, Allen JA, Garrigue C, Carroll EL, Garland EC (2025). Whale song shows
  language-like statistical structure. *Science* 387:649. doi:10.1126/science.adq7055
* Kirby S, Okanoya K, Garland EC, Takahasi M, Arnon I (2026). Language-like statistical
  structure arises in learned signaling: evidence from birdsong. *Science Advances*, eaea3015.
* Brent MR (1999). An efficient, probabilistically sound algorithm for segmentation and word
  discovery. *Machine Learning* 34:71-105.
* Charpentier A (2026). Beyond Zipf's Law: Equifinality and Mechanistic Inference from Scaling
  Laws. arXiv:2608.09459.
* Cohen Y, Shen J, Semu D, Leman DP, Liberti WA, Perkins LN, Liberti DC, Kotton DN, Gardner TJ
  (2020). Hidden neural states underlie canary song syntax. *Nature* 582:539-544.
* Cohen Y, Nicholson DA, Sanchioni A, Mallaber EK, Skidanova V, Gardner TJ (2022). Automated
  annotation of birdsong with a neural network that segments spectrograms. *eLife* 11:e63853.
* Jin DZ, Kozhevnikov AA (2011). A compact statistical model of the song syntax in Bengalese
  finch. *PLoS Comput. Biol.* 7:e1001108.
* Katahira K, Suzuki K, Okanoya K, Okada M (2011). Complex sequencing rules of birdsong can be
  explained by simple hidden Markov processes. *PLoS ONE* 6:e24516.
* Koumura T, Okanoya K (2016). Automatic recognition of element classes and boundaries in the
  birdsong with variable sequences. *PLoS ONE* 11:e0159188.
* Li W (1992). Random texts exhibit Zipf's-law-like word frequency distribution. *IEEE Trans.
  Inf. Theory* 38:1842-1845.
* Markowitz JE, Ivie E, Kligler L, Gardner TJ (2013). Long-range order in canary song. *PLoS
  Comput. Biol.* 9:e1003052.
* Morita T, Koda H, Okanoya K, Tachibana RO (2021). Measuring context dependency in birdsong
  using artificial neural networks. *PLoS Comput. Biol.* 17:e1009707.
* Nicholson D, Queen JE, Sober SJ (2017). Bengalese finch song repository. figshare.
* Payne RS, McVay S (1971). Songs of humpback whales. *Science* 173:585-597.
* Suzuki R, Buck JR, Tyack PL (2006). Information entropy of humpback whale songs. *J. Acoust.
  Soc. Am.* 119:1849-1866.
* Witten IH, Bell TC (1991). The zero-frequency problem. *IEEE Trans. Inf. Theory* 37:1085-1094.

MV2, Munim, Inc., mv2@munimtech.com
