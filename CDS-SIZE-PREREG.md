# CDS-SIZE-PREREG: how much data does this test need to find real human words?

Registered 2026-11-18 (about 13:45 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com), after
[RESULTS-CDS.md](RESULTS-CDS.md) and before anything below has been computed. Made with AI
agents. Text CC BY 4.0; code Apache-2.0. Code: `cds_size.py`, tests `test_cds_size.py`; job
`song-zipf-cdssize-v1`. The pipeline is used unchanged: `zipfseg.py` (commit 742fd83) and
`cds_job.py` (commit 83de8fd), fetched at those commits by the job.

## 1. Why

On child-directed English, the test did not find words beyond a second-order phoneme chain
at finch size (30 recordings of about 650 phonemes; p = 0.49) but did at whale size (8
recordings of about 6,150 phonemes; p = 0.005). At finch size the second-order chain was
overfit (held-out check D1: order 2 better in 1 of 30 recordings); at whale size it was not
(8 of 8). Two points do not make a curve. We ask:

* **Where between these sizes does the test start to find real words?**
* **Does the overfit check D1 tell in advance whether it can?** If it does, D1 is a cheap,
  data-internal power check that anyone can run on a new species before reading a Zipf
  result, which is the practical lesson for the whale, finch and future animal-song papers.

## 2. Design (fixed now)

Same corpus and reading gate as CDS-PREREG.md (Brent-Ratner `br-phono.txt`, read from the job's
cache or TalkBank). Bouts are utterances; symbols are phonemes. Every replicate has **8
recordings** (the whale design) of U consecutive utterances, in file order. Replicate r of size
U starts at utterance r x 8 x U; replicates of one size never overlap.

| U (utterances per recording) | replicates | about phonemes per recording |
|---|---|---|
| 70 | 5 | 650 (finch size) |
| 140 | 5 | 1,300 |
| 280 | 4 | 2,600 |
| 600 | 2 | 5,900 (whale size) |
| 1,200 | 1 | 11,800 |

Each replicate runs `zipfseg.analyze` (all six nulls, theta 0.3 / **0.5** / 0.7, B = 100, seed
20261118 + 10,000 r + U) and the held-out check D1. A replicate is **detected** if its theta-0.5
label is `BEYOND_SECOND_ORDER` (p(second-order) < 0.05). Its **D1 majority** holds if order 2
generalises better in more than 4 of its 8 recordings. We also record the boundary F1 of its
theta-0.5 cuts against the true word boundaries.

**Honest note on data reuse.** The corpus has 9,790 utterances, and these replicates reuse
utterances already analysed in CDS-F (1-2,100) and CDS-W (2,101-6,900), cut into different
recordings. No result at these sizes or splits has been computed. Both U = 600 replicates
(utterances 1-4,800 and 4,801-9,600) overlap CDS-W's span (2,101-6,900) with different
boundaries, so they are not independent replications of CDS-W; utterances 6,901-9,790 have
never been analysed.

## 3. Predictions and honest priors (graded by `cds_size.grade`)

| id | prediction | prior |
|---|---|---|
| Z1 | detection rate at U = 70 is <= 0.2 | 0.75 |
| Z2 | detection rate at U = 600 is >= 0.5 | 0.75 |
| Z3 | the U = 1,200 replicate is detected | 0.75 |
| Z4 | detection rate never falls as U grows | 0.50 |
| Z5 | no U = 70 replicate has a D1 majority | 0.85 |
| Z6 | every U = 600 and U = 1,200 replicate has a D1 majority | 0.85 |
| Z7 | the size threshold (T1) is U <= 280 | 0.40 |

## 4. Reading rules (fixed now)

* **T1 (size threshold):** the smallest U whose detection rate at theta 0.5 is at least 0.5,
  reported with its mean phonemes per recording; `NO_THRESHOLD_IN_RANGE` if none.
* **T2 (does D1 predict power?):** over all 17 replicates, `D1_TRACKS_DETECTION` if the
  detection rate is at least 0.5 among replicates with a D1 majority and at most 0.2 among
  those without; `D1_DOES_NOT_TRACK` otherwise; `UNDETERMINED` if either group is empty. If
  `D1_TRACKS_DETECTION`, we will recommend D1 as a power check to run before any Zipf result,
  and we will apply it to the whale result when that exists (reporting, never relabelling).
* **T3 (where the song data sit):** whether the T1 size in phonemes per recording is at most
  the whale's 5,720 elements per year, and at most the finch's 676 syllables per recording.
  This compares symbol counts only. Phonemes, syllables and whale sound elements are
  different units with different inventories, so T3 is context, not a test of either species.
* Thresholds 0.3 and 0.7 are reported as robustness. Whatever comes out is published as
  RESULTS-CDS-SIZE.md, with a test that re-derives every number.

## 5. Limits known now

* One language, one corpus, phonemes rather than syllables (50 symbol types).
* B = 100 per null: the smallest p is about 0.01, enough for the 0.05 rule.
* Few replicates at the large sizes (2 and 1), so the curve is coarse there.
* With 8 recordings per replicate, power at U = 70 is lower than in CDS-F (30 recordings).
