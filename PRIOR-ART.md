# Prior art: has anyone tested TP-segmentation Zipf results against Markov-chain song?

Last checked 2026-11-18 (about 12:50 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com). Made with
AI agents. Text CC BY 4.0.

**Short answer: the worry is old and widely stated, but we found no test of it.** Several
authors say that Zipf-like statistics can come from random sequences or from segmentation itself.
None of the sources below simulates song made by syllable-transition rules with no words, puts it
through the published transitional-probability (TP) pipeline, and asks whether the published
shuffle and rotation controls (or any Markov null) can tell it apart from word-like song. That
is what `calib.py` (PREREG-AMENDMENT-2; result in RESULTS-CALIB.md) and `calib2.py` do, and
what `zipfseg.py` does on the real data. The closest work (Charpentier 2026, below) recommends
this kind of null for whale song but states that it does not reanalyse any recordings.

| source | what it says | does it test the TP pipeline against Markov song? |
|---|---|---|
| Miller 1957, *Am J Psychol* 70:311 ("Some effects of intermittent silence") | random typing with a space key gives Zipf-like word frequencies | no (no TP segmentation) |
| Li 1992, *IEEE Trans Inf Theory* 38:1842 ("Random texts exhibit Zipf's-law-like word frequency distribution") | same, analytically | no |
| Ferrer-i-Cancho & Elvevag 2010, *PLoS ONE* | random texts do not fit Zipf's law as well as real ones | no |
| Bochkarev & Lerner 2012, arXiv:1207.1872 ("Zipf and non-Zipf laws for homogeneous Markov chain") | "words" read off a Markov chain between visits to a "space" state typically have power-law rank-probability; sparse chains can fall off faster | theory with an explicit space state; no TP-dip segmentation, no controls |
| Arnon et al. 2025, *Science* 387:649 (whale) | controls: shuffled elements and rotated (shifted) cut points | no Markov null |
| eLetter "Zipf zapped: The randomness of Zipf" (Science, on Arnon et al.) | Zipf's law appears in random texts, so it is weak evidence | conceptual, no simulation of the pipeline |
| eLetter, Lameira & Hills, "Solar flares show language-like statistical structures" | the method finds "language-like" structure in solar-flare data | a non-biological example, no Markov calibration |
| Kirby et al. 2026, *Science Advances* (Bengalese finch; doi 10.1126/sciadv.aea3015) | adds a within-bout bigram (first-order) control and concludes the structure is "above the bigram" | first order only; no second-order null, no calibration of the controls |
| Ferrer-i-Cancho 2025, *EPL* 151:62001 (arXiv:2505.20015) | Zipf's law as a sign of a class of coding optimality; humpback whales "might" belong to it | theory, no segmentation test |
| Bahle & Long 2026, *Curr Opin Neurobiol* 99:103208 ("Language-like properties in the vocal behavior of animals") | Zipfian distributions "may also result from an artifact of segmentation" (citing Miller 1957 and Li 1992), so they are weak evidence on their own | review, no test |
| Charpentier 2026, arXiv:2608.09459 v2 ("Beyond Zipf's Law: Equifinality and Mechanistic Inference from Scaling Laws") | the same Zipf marginal can come from i.i.d., persistent-Markov and sample-space-reducing processes; surrogates "should therefore repeat the segmentation step"; uses the whale and finch papers as examples | no: "We do not reanalyze either dataset"; its Markov chains are synthetic, "not models calibrated to whale or birdsong production" |
| arXiv:2609.16612 (Sinha & Chavan 2026) | compares vocal corpora through audio encoders | does not test the segmentation method |
| Rosillo-Rodes, Hebert-Dufresne & Dodds 2026, *Phys Rev Research* 8:L012029 (arXiv:2511.02069) | cites the whale paper; type-token (Heaps) relation from Zipf's law | no segmentation or null-model test |

Searches used (2026-11-17): "transitional probability segmentation random Markov sequence Zipf
artifact animal vocalization"; "Zipf whale song Arnon critique null model Markov"; "Markov chain
null whale song Zipf segmentation transitional probability rotated baseline critique simulation
2026"; "Arnon Kirby Garland whale song Zipf reply critique Markov model"; Europe PMC and journal
eLetter pages for both papers. No reply from the authors to either eLetter, and no Technical
Comment in *Science*, was found. Re-checked 2026-11-18 ("comment on 'Whale song shows
language-like statistical structure' Markov null transitional probability critique"): nothing
new. Re-checked 2026-11-18 about 12:45 UTC ("comment on 'Whale song shows language-like
statistical structure' Arnon Zipf critique Markov null 2026"; "transitional probability
segmentation animal song Zipf artifact null model 2026 preprint"): found Charpentier 2026
(added above; full text read, no reanalysis of real song) and no Technical Comment.

## Law of brevity (added 2026-11-17, about 23:50 UTC, for CALIB-3; CALIB-4 added 2026-11-18)

**Short answer: it is old theory that randomly generated "words" show brevity, but we found
no test of what the TP pipeline reports for sources whose true units have no brevity, or the
reverse.** That is what `calib3.py` ([CALIB-3-PREREG.md](CALIB-3-PREREG.md)) does, and
`calib4.py` ([CALIB-4-PREREG.md](CALIB-4-PREREG.md)) does it for the whale paper's statistic
exactly as its text defines it (one point per chunk type, pooled over the whole data set).

| source | what it says | does it test TP chunks for brevity against sources of known brevity? |
|---|---|---|
| Miller 1957; Li 1992 | random typing gives frequent short "words" (brevity) as well as Zipf | no TP segmentation |
| Ferrer-i-Cancho et al. 2015, arXiv:1504.04884 ("Compression and the origins of Zipf's law of abbreviation") | random typing differs from real languages; it can be read as a form of compression | theory, no segmentation test |
| Arnon et al. 2025 (whale) | chunk length vs log frequency R^2 0.62, above shuffled and rotated baselines (z 37.57 and 13.92) | no source of known brevity, no Markov null |
| Kirby et al. 2026 (finch; open text PMC13450306) | Poisson mixed model, beta = -0.04, SE 0.0045, P < 0.00001, random intercepts for bird | no baseline for brevity at all |
| Youngblood 2025, *Sci Adv* ads6014 ("Language-like efficiency in whale communication") | Menzerath's law in 11 whale species; law of abbreviation in humpback (phrase types, estimate -0.086 [-0.124, -0.049]) and blue whales, on annotated element types with measured durations | not TP chunks. Note: its supplement also ran the James et al. 2021 production-constraint null for Menzerath's law: 12 of 16 whale species beat it, 0 of 51 human languages did, and the author set it aside as "far too conservative" |
| Lewis et al. 2025 (ZLAvian, PMC12349147, "Does Zipf's law of abbreviation shape birdsong?") | null distribution of concordance by permuting durations; weak evidence within single bird populations | annotated notes and phrases, not TP chunks |
| Clink et al. 2020, *R Soc Open Sci* 7:200151 ("Brevity is not a universal in animal communication") | in gibbons, evidence for compression depends on the unit of analysis | not TP chunks |
| Bahle & Long 2026 (review) | segmentation-artefact warning, applied to frequency distributions only | no test |

What our tests can and cannot say about Youngblood 2025: his humpback law of abbreviation is
measured on phrase types annotated by people, with real durations, not on TP chunks counted in
sound elements. A result of ours on the TP-chunk statistic does not test his result.

Searches used: "law of abbreviation artifact segmentation null model random typing animal
vocal sequences"; "'law of abbreviation' segmented units transitional probability chunks null
model simulation birdsong whale 2025 2026"; Youngblood 2025 (Europe PMC full text, code
github.com/masonyoungblood/whale_efficiency, supplement source); Europe PMC full text of the
finch paper.

If we have missed a paper that does this, please tell us at mv2@munimtech.com and we will cite
it here and in every result.
