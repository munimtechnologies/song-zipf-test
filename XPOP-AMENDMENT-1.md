# XPOP-AMENDMENT-1 (2026-11-19): independent-bird finch test, job song-zipf-xpop-v2

Amends XPOP-PREREG.md. Written on 2026-11-19, **before any of the finch data were downloaded or
read**: job `song-zipf-xpop-v1` stopped at its first step (the unit tests) and never reached
the download. MV2, Munim, Inc. Made with AI agents. Text CC BY 4.0, code Apache-2.0.

## What happened

`song-zipf-xpop-v1` ran on 2026-11-19 at 07:45 UTC and failed in `test_finch_xpop.py`, test
`test_run_task_and_assemble` (25 tests, 1 error). That test fed the N block uniform random
toy song (5 letters, seed 8) at theta 0.3. Toy song with no syllable rules has almost no
transitional-probability dips, so every chunk is a whole, unique bout; every inventory is all
singletons; every Zipf R^2, real and null, is undefined (nan); and the pinned `zipfseg.compare`
divides by zero on the empty list. `run_task` caught and recorded the error exactly as
designed ("recorded, never hidden"); the test wrongly expected a result. It was a fault in the
test's toy data, not in the analysis.

## Changes (only these)

1. **Test fix.** `test_xpop_v2.py` reruns every registered test unchanged except that one,
   which now gives N the same toy data as K (where theta 0.5 runs) and checks that a
   degenerate data set is recorded as an error and never raised or hidden.
2. **Reading guard (Gate N).** Tar archives made on a Mac carry a hidden metadata file named
   `._<name>` next to every real file. Members whose file name starts with `._` are not
   annotation files; they are now skipped before Gate N and their number is reported per bird
   (`appledouble_skipped`). Without this, each such member would count as an unreadable file
   and Gate N (at most 1% unreadable) could fail for a reason unrelated to the annotations. We
   do not know yet whether the Nicholson archives contain such files; if they do not, this
   change does nothing.
3. **How it runs.** The registered `finch_xpop.py` and `test_finch_xpop.py` are fetched
   unchanged at commit 06460e4 and `zipfseg.py` at 742fd83. `xpop_v2.py` only wraps them
   (the guard above, a wait for this file to be public, and provenance fields `job` and
   `amendment` with SHA-256 of the code that ran). The output keeps `version` "xpop-1" because
   the analysis is the registered one.

Unchanged: data, reading rules, gates, nulls, B, seeds, thresholds, time budget, the 11
predictions and their priors, the decision rules X1-X3, and the published grader
`test_xpop_results.py` (d89b7ad), which still re-derives every gate, label and score.
