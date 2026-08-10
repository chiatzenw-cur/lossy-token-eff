# Manual read of the 7 longest-streak window-entropy ramp onsets

Source: `window_entropy_ramp_onsets.jsonl`, 5,737 onset events total across the
8 pilot cases' **plain, unguarded** `r_fuzzy` traces (streak-length distribution
is heavily front-loaded: mode 1, median low, max 19 -- see the parent
conversation). These are the 7 longest streaks in the whole set, i.e. the
purest, most sustained ramp episodes the criterion can produce -- the
hypothesis's best case, not a random sample.

| case | pos | streak | onset token | verdict |
|---|---:|---:|---|---|
| case_028 | 31322 | 19 | `Hence`→`Hence` | **clear hit** |
| case_011 | 3291 | 17 | ` half`→` half` | false positive |
| case_021 | 5466 | 17 | `=`→`?).` | false positive (messy but legitimate) |
| case_005 | 5920 | 16 | `=`→`=` | false positive (legitimate exhaustive case-check) |
| case_011 | 19837 | 16 | ` our`→` our` | false positive (reaches a real contradiction, self-corrects well) |
| case_028 | 8339 | 16 | ` be`→` be` | borderline (messy, same generally-degenerate case as the hit above) |
| case_028 | 13216 | 16 | ` `→` ` | borderline (messy phrasing, but legitimate case-by-case arithmetic) |

**1/7 clear hit, 2/7 borderline, 4/7 clear false positives.**

## The one clear hit (case_028, pos 31322)

Context before is already garbled -- a nonsensical aside ("Ok no we reason to
get same value for all n in a need that minus occurrence") and a mangled,
repeated congruence-system block. Right after the onset token (`Hence`), it
gets *more* incoherent: "Which equals? Wait for one fixed", "Ok actual.",
"We realize O solved but can produce final solution.", ending in a guessed,
non-answer ("5??"). Textbook coherence collapse.

## The false positives

Three of the four are genuinely good reasoning that happens to satisfy the
entropy-shape criterion: exhaustive case-by-case verification (case_005,
testing n=1..12 mod 13 -- legitimately repetitive because that's the correct
technique, not degeneration), and two instances of real algebra reaching a
contradiction and correctly pivoting off it (case_011's " our assumption
wrong" -- that's *good* self-correction, the opposite of a loop). case_021 is
messier ("Wait b'?)" ) but still systematically enumerating small cases
toward a real answer.

## Reading this

Even restricted to its most sustained occurrences, the joint
w64<w32<w16<w8 monotonic-ramp condition has **low precision** as a
standalone per-token loop-onset detector in this sample: confident,
coherent (and even well-self-correcting) reasoning triggers it about as
often as genuine degeneration does. The signal isn't nothing -- the one
clear hit is a strong example, and the two borderline cases both belong to
case_028, the same case that produced the clear hit and is independently
known to be one of `r_fuzzy`'s worst-performing cases in this pilot -- but
it looks more like "which *case* is generally struggling" than "which
*token* is where a loop specifically begins." Combined with the streak-
length distribution (thousands of mostly single-token, flickering matches
rather than sustained multi-token ramps), this is consistent with why the
guard's accuracy effect in the full pilot was a net cost rather than a
clean win: it's intervening on a noisy signal, not a precise one.
