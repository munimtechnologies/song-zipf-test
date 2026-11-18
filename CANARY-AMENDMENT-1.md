# CANARY-AMENDMENT-1: a test fix, nothing else (2026-11-18, before any canary data were read)

Registered 2026-11-18 (about 22:00 UTC) by MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI
agents. Text CC BY 4.0. This amends only how the job is run; CANARY-PREREG.md is unchanged.

**What was wrong.** In `test_canary.py` as first published (commit 86bf93b), `test_range_reader`
built its fake range reader with the URL `"u"`. Python's `urllib.request.Request` rejects a URL
without a scheme ("unknown url type") before the injected opener is called, so that one test
failed. This is why the repository's pre-commit test step refused the tested commit of
`canary.py`, and the job `song-zipf-canary-v1` runs that test file as its first step, so it would
have stopped before reading anything.

**What changed.** `test_range_reader` now uses `http://example.invalid/llb3_data.zip` (never
opened: every test injects its own opener). No other test, expected value or line of `canary.py`
changed.

**How the job runs now.** `song-zipf-canary-v2` replaces v1, which never ran. Its `setup.sh`
fetches `canary.py` from this repository at commit 86bf93b and `zipfseg.py` at 742fd83, so the
analysis code is byte-identical to what was public before the job could read data. The fixed
`test_canary.py` runs first, then `canary.py` exactly as registered (same data, units, gates,
nulls, B values, rules C1-C2, predictions P1-P8 and priors).

**Grader.** `test_canary_results.py`, published with this amendment and before any result exists,
re-derives every gate, label, prediction, rule and the Brier score from
`results/canary/canary_results.json` and fixes the lines RESULTS-CANARY.md must print.

MV2, Munim, Inc., mv2@munimtech.com
