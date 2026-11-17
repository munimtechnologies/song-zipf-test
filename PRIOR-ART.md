# Prior art: has anyone tested TP-segmentation Zipf results against Markov-chain song?

Last checked 2026-11-17 (about 22:20 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com). Made with
AI agents. Text CC BY 4.0.

**Short answer: the worry is old and widely stated, but we found no test of it.** Several
authors say that Zipf-like statistics can come from random sequences or from segmentation itself.
None of the sources below simulates song made by syllable-transition rules with no words, puts it
through the published transitional-probability (TP) pipeline, and asks whether the published
shuffle and rotation controls (or any Markov null) can tell it apart from word-like song. That
is what `calib.py` (PREREG-AMENDMENT-2; result in RESULTS-CALIB.md) and `calib2.py` do, and
what `zipfseg.py` does on the real data.

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
| arXiv:2609.16612 (Sinha & Chavan 2026) | compares vocal corpora through audio encoders | does not test the segmentation method |
| Rosillo-Rodes, Hebert-Dufresne & Dodds 2026, *Phys Rev Research* 8:L012029 (arXiv:2511.02069) | cites the whale paper; type-token (Heaps) relation from Zipf's law | no segmentation or null-model test |

Searches used (2026-11-17): "transitional probability segmentation random Markov sequence Zipf
artifact animal vocalization"; "Zipf whale song Arnon critique null model Markov"; "Markov chain
null whale song Zipf segmentation transitional probability rotated baseline critique simulation
2026"; "Arnon Kirby Garland whale song Zipf reply critique Markov model"; Europe PMC and journal
eLetter pages for both papers. No reply from the authors to either eLetter, and no Technical
Comment in *Science*, was found.

If we have missed a paper that does this, please tell us at mv2@munimtech.com and we will cite
it here and in every result.
