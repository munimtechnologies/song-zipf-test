# SPDX-License-Identifier: Apache-2.0
# zipfseg: transitional-probability (TP) segmentation of animal song, the Zipf
# rank-frequency R^2 used by Arnon et al. 2025 (Science 387:649) and Kirby et al.
# 2026 (Sci. Adv., doi 10.1126/sciadv.aea3015), and sequence null models of
# increasing order (shuffle, within-bout bigram/trigram resampling, pooled
# first/second-order Markov chains).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
"""Pure-Python core (no third-party imports) so the tests run anywhere.

Conventions
-----------
A *recording* is a list of *bouts*; a bout is a list of hashable symbols
(syllable or sound-element labels). Transitional probabilities are estimated
per recording from within-bout adjacent pairs only (no pair crosses a bout
boundary), as in Kirby et al. 2026.

Cut rule (PREREG.md section 3): with t_i = TP(s_i -> s_{i+1}), a boundary is
placed at transition i (between s_i and s_{i+1}) when t_i / t_{i-1} < theta,
i.e. when the current TP has dropped below theta times the previous one. The
rule direction can be switched with ``rule="prev_over_cur"`` for the
sensitivity check required by the pre-registration.
"""
import math
import random
from collections import Counter, defaultdict

RULES = ("cur_over_prev", "prev_over_cur")


# --------------------------------------------------------------------------
# transitional probabilities and segmentation
# --------------------------------------------------------------------------
def bigram_tp(bouts):
    """TP(a->b) = n(a,b) / n(a, any) over within-bout adjacent pairs."""
    pair = Counter()
    first = Counter()
    for b in bouts:
        for x, y in zip(b, b[1:]):
            pair[(x, y)] += 1
            first[x] += 1
    return {k: v / first[k[0]] for k, v in pair.items()}


def segment_bout(bout, tp, theta, rule="cur_over_prev"):
    """Split one bout into subsequences (tuples). Concatenation == bout."""
    if rule not in RULES:
        raise ValueError(rule)
    n = len(bout)
    if n == 0:
        return []
    t = [tp[(bout[i], bout[i + 1])] for i in range(n - 1)]
    segs = []
    start = 0
    for i in range(1, n - 1):
        if rule == "cur_over_prev":
            ratio = t[i] / t[i - 1]
        else:
            ratio = t[i - 1] / t[i]
        if ratio < theta:
            segs.append(tuple(bout[start:i + 1]))
            start = i + 1
    segs.append(tuple(bout[start:]))
    return segs


def segment_recording(bouts, theta, rule="cur_over_prev"):
    """Inventory (Counter) of detected subsequences for one recording."""
    tp = bigram_tp(bouts)
    inv = Counter()
    for b in bouts:
        for s in segment_bout(b, tp, theta, rule):
            inv[s] += 1
    return inv


# --------------------------------------------------------------------------
# Zipf statistic
# --------------------------------------------------------------------------
def _pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return float("nan")
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / math.sqrt(sxx * syy)


def zipf_r2(freqs):
    """R^2 of log(frequency) on log(rank), ranks 1..K by descending frequency.

    Returns nan for fewer than 3 types or no variation in frequency."""
    f = sorted((v for v in freqs if v > 0), reverse=True)
    if len(f) < 3:
        return float("nan")
    x = [math.log(r) for r in range(1, len(f) + 1)]
    y = [math.log(v) for v in f]
    r = _pearson(x, y)
    return r * r if r == r else float("nan")


def zipf_slope(freqs):
    """OLS slope of log f on log r (descriptive only; negative for Zipf)."""
    f = sorted((v for v in freqs if v > 0), reverse=True)
    if len(f) < 3:
        return float("nan")
    x = [math.log(r) for r in range(1, len(f) + 1)]
    y = [math.log(v) for v in f]
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    sxx = sum((a - mx) ** 2 for a in x)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx


def nanmean(v):
    v = [a for a in v if a == a]
    return sum(v) / len(v) if v else float("nan")


def dataset_r2(recordings, theta, rule="cur_over_prev"):
    """Mean over recordings of the per-recording Zipf R^2 (the papers' statistic)."""
    return nanmean([zipf_r2(segment_recording(b, theta, rule).values())
                    for b in recordings])


# --------------------------------------------------------------------------
# null models (each returns a new recording with the same bout lengths)
# --------------------------------------------------------------------------
def shuffle_recording(bouts, rng):
    out = []
    for b in bouts:
        c = list(b)
        rng.shuffle(c)
        out.append(c)
    return out


def resample_bout(target, k, rng):
    """Within-bout order-k resampling (k=1 reproduces the 'bigram' baseline
    of Kirby et al. 2026). Seed with k consecutive symbols at a random point;
    then repeatedly pick a random occurrence of the last k symbols that has a
    successor inside the target bout and append that successor; if the
    context occurs only at the end of the bout, reseed. Truncate to len."""
    n = len(target)
    target = list(target)
    if n <= k:
        return list(target)
    index = defaultdict(list)          # context -> successor positions, ascending
    for i in range(n - k):
        index[tuple(target[i:i + k])].append(i + k)
    p = rng.randrange(n - k + 1)
    out = target[p:p + k]
    while len(out) < n:
        cands = index.get(tuple(out[-k:]))
        if cands:
            out.append(target[rng.choice(cands)])
        else:
            p = rng.randrange(n - k + 1)
            out.extend(target[p:p + k])
    return out[:n]


def resample_recording(bouts, k, rng):
    return [resample_bout(b, k, rng) for b in bouts]


def markov_recording(bouts, k, rng):
    """Pooled order-k Markov chain fitted to the whole recording.

    Start k-grams are drawn from the bouts' own opening k-grams; successors
    are drawn with their observed multiplicity; a context never followed by a
    symbol (seen only at bout ends) triggers a reseed from a random k-gram
    that has a successor. Bouts shorter than k+1 are copied unchanged."""
    succ = defaultdict(list)
    starts = []
    with_succ = []
    for b in bouts:
        b = list(b)
        if len(b) >= k:
            starts.append(tuple(b[:k]))
        for i in range(len(b) - k):
            ctx = tuple(b[i:i + k])
            succ[ctx].append(b[i + k])
            with_succ.append(ctx)
    out = []
    for b in bouts:
        n = len(b)
        if n <= k or not with_succ:
            out.append(list(b))
            continue
        seq = list(rng.choice(starts))
        while len(seq) < n:
            ctx = tuple(seq[-k:])
            nxt = succ.get(ctx)
            if nxt:
                seq.append(rng.choice(nxt))
            else:
                seq.extend(rng.choice(with_succ))
        out.append(seq[:n])
    return out


NULLS = {
    "shuffle": lambda rec, rng: shuffle_recording(rec, rng),
    "bigram_within": lambda rec, rng: resample_recording(rec, 1, rng),
    "trigram_within": lambda rec, rng: resample_recording(rec, 2, rng),
    "markov1_pooled": lambda rec, rng: markov_recording(rec, 1, rng),
    "markov2_pooled": lambda rec, rng: markov_recording(rec, 2, rng),
}


# --------------------------------------------------------------------------
# comparison and diagnostics
# --------------------------------------------------------------------------
def compare(real, nulls):
    """z-score and one-sided empirical p (null >= real) with +1 correction."""
    v = [a for a in nulls if a == a]
    m = sum(v) / len(v)
    sd = math.sqrt(sum((a - m) ** 2 for a in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    z = (real - m) / sd if sd > 0 else float("nan")
    p = (1 + sum(1 for a in v if a >= real)) / (1 + len(v))
    frac80 = sum(1 for a in v if a >= 0.80) / len(v)
    return {"real": real, "null_mean": m, "null_sd": sd, "z": z, "p": p,
            "n_null": len(v), "null_frac_r2_ge_0.80": frac80}


def heldout_ll(bouts, k, alpha=0.5, skip=2):
    """Leave-one-bout-out mean log-likelihood per symbol of an order-k Markov
    chain with additive smoothing; predicts positions >= skip in every bout
    so that orders 1 and 2 are scored on the same symbols."""
    alphabet = sorted({s for b in bouts for s in b}, key=repr)
    V = len(alphabet)
    total = 0.0
    count = 0
    for j, held in enumerate(bouts):
        c = defaultdict(Counter)
        for i2, b in enumerate(bouts):
            if i2 == j:
                continue
            for i in range(len(b) - k):
                c[tuple(b[i:i + k])][b[i + k]] += 1
        for i in range(max(skip, k), len(held)):
            ctx = tuple(held[i - k:i])
            cc = c.get(ctx, Counter())
            tot = sum(cc.values())
            total += math.log((cc.get(held[i], 0) + alpha) / (tot + alpha * V))
            count += 1
    return total / count if count else float("nan")


def analyze(recordings, thetas=(0.3, 0.5, 0.7), B=1000, seed=20261117,
            nulls=tuple(NULLS), rule="cur_over_prev"):
    """Real vs null mean-R^2 for every threshold and null model.

    One RNG per (null, theta), seeded from the master seed, so results do not
    depend on the order in which nulls are run."""
    res = {"thetas": list(thetas), "B": B, "seed": seed, "rule": rule,
           "n_recordings": len(recordings), "by_theta": {}}
    for th in thetas:
        real = dataset_r2(recordings, th, rule)
        row = {"real_mean_r2": real, "nulls": {}}
        for ni, name in enumerate(nulls):
            rng = random.Random(seed * 1000 + ni * 10 + int(round(th * 10)))
            vals = []
            for _ in range(B):
                fake = [NULLS[name](rec, rng) for rec in recordings]
                vals.append(dataset_r2(fake, th, rule))
            row["nulls"][name] = compare(real, vals)
        res["by_theta"][str(th)] = row
    d = []
    for rec in recordings:
        l1 = heldout_ll(rec, 1)
        l2 = heldout_ll(rec, 2)
        d.append(l2 - l1)
    res["heldout_ll_order2_minus_order1"] = {
        "per_recording": d, "mean": nanmean(d),
        "n_favour_order2": sum(1 for a in d if a > 0)}
    return res
