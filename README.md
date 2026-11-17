# song-zipf-test

A pre-registered test by MV2 of Munim, Inc. of a widely reported claim: that humpback whale
song (Arnon et al. 2025, *Science*) and Bengalese finch song (Kirby et al. 2026, *Science
Advances*) contain "language-like" units whose frequencies follow Zipf's law.

**Question.** Both papers cut songs into chunks at dips in transitional probability and
find that the chunk frequencies look Zipfian. The finch paper shows that the effect beats a
first-order (bigram) null. Is it more than **second-order syllable rules**? We test the
published statistic against pooled first- and second-order Markov chains fitted to each
recording, and add a held-out check against overfitting.

* Status: **pre-registered, no data seen** (2026-11-17). See [PREREG.md](PREREG.md).
* Stage 0: `inventory.py` fetches the published supplements and writes an inventory. It
  does no analysis.
* Core code: `zipfseg.py` (pure Python). Tests: `python -m unittest -v test_zipfseg`.

The "wow", whichever way it falls: either the Zipf structure in animal song reduces to
short-range transition rules, or it survives a much stronger control than any published one.

Raw data from the two papers are not redistributed here. The finch data are CC BY-NC, and
the whale data are released for reproducing or extending the Zipfian analysis.

Made with AI agents working in MV2's name. Code Apache-2.0; text CC BY 4.0.
Contact: MV2, Munim, Inc., mv2@munimtech.com
