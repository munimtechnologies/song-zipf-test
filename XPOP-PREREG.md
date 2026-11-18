# XPOP-PREREG: does the finch Zipf result replicate in other birds, and does it go beyond second-order syllable rules when each bird gives ~20,000 notes?

Registered 2026-11-18, before any of the data below were downloaded or opened by this
project. The code that will run is `finch_xpop.py` (tests: `test_finch_xpop.py`), published
in the same commit. Job: `song-zipf-xpop-v1`. It polls this repository and analyses nothing
until this file is public.

**Publication note (2026-11-18, about 19:00 UTC).** This text was written at about 16:30 UTC.
Two attempts to publish it together with its code (16:30 and 17:50 UTC) did not land, for a
reason we could not see. It is therefore published on its own, unchanged apart from this
note, and the code (`finch_xpop.py`, `test_finch_xpop.py`, byte-identical to the copy the job
runs) follows in a separate commit. The job downloads nothing until this file is public, so
the registration still precedes all data. The English size curve graded since then
(RESULTS-CDS-SIZE.md) puts the test's threshold for finding English words at about 2,745
phonemes per recording, not the 6,150 quoted in section 1; nothing below is changed by that.

MV2, Munim, Inc. Made with AI agents. Text CC BY 4.0, code Apache-2.0.

## 1. Why

Kirby et al. (2026, *Sci. Adv.* eaea3015) found that Bengalese finch song cut at
transitional-probability dips gives Zipf-distributed chunks, beyond a bigram baseline. Their
data are 30 recordings from 6 birds in one laboratory, each with about 666 syllable
transitions. On those data we found (RESULTS-FINCH.md) that a pooled **second-order** Markov
chain with no words in it is just as Zipfian (p = 0.137). The English control (RESULTS-CDS.md)
showed the test cannot find real English words at that size (p = 0.49) but can at about
6,150 phonemes per recording (p = 0.005). So the finch result left an open question: was the
second-order chain's match a real property of finch song, or a lack of power at ~700
transitions per recording?

This study answers it with two independent, public, hand-annotated Bengalese finch datasets
recorded by other groups, at about 18,000 to 20,000 notes per bird (about three times the
size at which the test found English words), and adds a **third-order** chain.

## 2. Data (both CC BY 4.0)

* **K: Koumura & Okanoya 2016** (*PLoS ONE* 11:e0159188), figshare 10.6084/m9.figshare.3470165
  v1, files Bird0.zip to Bird10.zip (11 adult males, > 120 days post-hatch). Like Kirby et
  al.'s birds they come from K. Okanoya's group, so K gives different birds and different
  recordings, not a different laboratory; N does. Only `Annotation.xml` is kept from each zip;
  the audio is deleted unopened. Each byte count must equal the figshare listing.
* **N: Nicholson, Queen & Sober**, Bengalese Finch Song Repository, figshare
  10.6084/m9.figshare.4805749 (the `.wav.csv.tar.gz` archives; 4 adult birds bl26lb16,
  gr41rd51, gy6or6, or60yw70, Sober laboratory, Emory University). Archives are streamed; only
  the `.csv` annotation members are kept.

## 3. Reading rules (fixed now)

**K.** Each `<Sequence>` gives a wav file, a start sample and its notes (start relative to the
sequence, length, label). The paper defines song as notes with less than 300 ms of silence
between them and split long songs into pieces of at most 15 notes. We rebuild songs: sequences
are put in recording order (wav number, then start sample) and a sequence joins the previous
bout when it is in the same wav and starts less than 9,600 samples (300 ms at 32 kHz) after
the previous sequence's last note ends. One recording = one bird (all its bouts).
Sensitivity data set **Kraw**: each `<Sequence>` as its own bout.

**Reading gate K** (from the paper's own text): 11 birds read; mean notes per bird within 5%
of 17,930.9; mean number of note classes per bird within 0.5 of 8.1.

**N.** Each annotated audio file's csv (columns onset_s, offset_s, label) is read in file
order; rows with an empty label are dropped; a new bout starts at a silent gap of 300 ms or
more (the same rule as K). Days are taken chronologically and files by name within a day,
whole files only, until the bird has at least 20,000 syllables. All labels are kept (including
introductory notes). One recording = one bird.

**Reading gate N** (internal; the dataset publishes no totals): 4 birds; each at least 5,000
syllables; at most 1% of files unreadable or with onsets out of order or onset > offset.

If a gate fails the analysis still runs, all output is published, and every result is marked
**provisional**; no headline is drawn from a failed gate.

**Kirby-size data sets KS and NS:** each bird's first bouts in recording order until they hold
at least 666 transitions (Kirby et al.: 19,990 transitions / 30 recordings).

## 4. Analysis (unchanged `zipfseg.py`, commit 742fd83)

Statistic: mean over recordings of the Zipf R^2 of the TP-chunk inventory (Kirby et al. Code
S1 rules, as reproduced exactly in RESULTS-FINCH.md). One-sided empirical p (null >= real, +1
correction), alpha = 0.05. Seed 20261118.

| block | data | theta | nulls | B |
|---|---|---|---|---|
| main | K, N | 0.5 | shuffle, rotate, bigram_within, markov1, markov2, **markov3** (pooled) | 200 |
| Kirby size | KS, NS | 0.5 | shuffle, rotate, bigram_within, markov1, markov2 | 1,000 |
| robustness | K, N | 0.3, 0.7 | as main | 50 |
| sensitivity | Kraw | 0.5 | as main | 50 |

markov3 is the same generator as markov2 with k = 3. Held-out check (leave one bout out,
additive smoothing 0.5): D1 = order 2 minus order 1 log-likelihood per symbol (positions >= 2),
D2 = order 3 minus order 2 (positions >= 3), per recording, for K, N and KS.

Label per data set and theta: `BEYOND_THIRD_ORDER` if p(markov3) < 0.05; else
`EXPLAINED_BY_THIRD_ORDER` if p(markov2) < 0.05; else `EXPLAINED_BY_SECOND_ORDER` if
p(markov1) < 0.05; else `EXPLAINED_BY_FIRST_ORDER` (without a markov3 null, the first case is
`BEYOND_SECOND_ORDER`, as in PREREG.md).

Robustness and sensitivity blocks start only if less than 55% of the 230-minute budget is
used; anything skipped is reported as skipped.

## 5. Predictions (graded at theta 0.5; prior probability that each is true)

| id | prediction | prior |
|---|---|---|
| K1 | K mean R^2 >= 0.80 | 0.80 |
| K2 | K beats shuffle and rotation | 0.90 |
| K3 | K beats bigram_within (Kirby's "above the bigram" replicates) | 0.85 |
| K4 | K beats markov1 | 0.85 |
| K5 | K beats markov2 | 0.50 |
| K6 | K beats markov3 | 0.30 |
| K7 | D1 > 0 in at least 80% of K birds (9 of 11) | 0.90 |
| N1 | N beats bigram_within | 0.75 |
| N2 | N beats markov2 | 0.45 |
| S1 | KS beats markov2 | 0.20 |
| S2 | KS beats bigram_within | 0.70 |

Brier score over the graded predictions.

## 6. Decision rules

* **X1** (does "above the bigram" replicate in other birds?): `ABOVE_BIGRAM_REPLICATES` if K3
  and N1; `ABOVE_BIGRAM_FAILS` if neither; else `ABOVE_BIGRAM_MIXED`.
* **X2** (main): `SECOND_ORDER_EXPLAINS_FINCH_ZIPF` if neither K nor N beats markov2;
  `FINCH_ZIPF_BEYOND_SECOND_ORDER` if both do; else `SECOND_ORDER_MIXED`.
* **X3** (size): `BEYOND_EVEN_AT_KIRBY_SIZE` if S1; else `SIZE_DEPENDENT` if K5; else
  `NOT_BEYOND_AT_EITHER_SIZE`.
* K's label is called robust only if theta 0.3, 0.5 and 0.7 all give the same label.

How we will read it, fixed now: `FINCH_ZIPF_BEYOND_SECOND_ORDER` with `SIZE_DEPENDENT` would
mean our earlier finch label reflected low power at Kirby et al.'s recording size, and we will
say so in RESULTS-FINCH.md the same day. `SECOND_ORDER_EXPLAINS_FINCH_ZIPF` at ~18,000 to
20,000 notes per bird, a size at which the same test found English words, would be strong evidence that the
finch Zipf pattern carries no information beyond second-order syllable rules. Either way the
finch alphabet (~8 classes) is much smaller than English's (~50 phonemes), so the English
comparison is a power reference, not a like-for-like control; we will say that too. A
`BEYOND_THIRD_ORDER` label would mean chunk structure that no chain up to order 3 reproduces,
which is the "word-like units" reading Kirby et al. propose.

## 7. Known limits, stated before the data

* K's merge rule can join two pieces of song across a note the authors marked unclassifiable
  (< 1% of notes), creating a few false transitions; Kraw is the check.
* Both datasets are adult song; Kirby et al.'s are developmental. K3 tests replication of the
  pattern in adult birds, not of their developmental claim.
* With 4 birds, N has little power on the held-out checks; it is not graded on them.
* Large recordings give tight null distributions, so small real departures become
  significant. The R^2 gap (real minus null mean) is reported next to every p.

## 8. Prior art (checked 2026-11-18)

No published test of the TP-chunk Zipf result on either dataset, and no test of Kirby et al.
or Arnon et al. against Markov nulls other than this repository (see PRIOR-ART.md). Both
datasets are widely used for automatic annotation (TweetyNet, vak, DAS) and sequence models
(e.g. partially observable Markov models, bioRxiv 2022.11.15.516592), not for Zipf analyses.
