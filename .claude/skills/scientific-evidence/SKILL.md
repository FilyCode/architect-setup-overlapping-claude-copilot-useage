---
name: scientific-evidence
description: Rules for scientific claims from pipelines — absence only within the instrument's headroom in that stratum, both branches when biology and data disagree, attacking confirming results, composition effects, tools whose reports are filtered differently, between-model contrasts with a seed-swap control. Use when a result says something is absent, surprising, confirmed, or about to be written down as settled.
---

# Scientific evidence

## When to use

A result says something is absent, surprising or confirmed, or is about to be written down as
settled. Preloaded by `anomaly-hunter`, `domain-reviewer` and `figure-auditor`.

## Checklist

1. Before writing "absent", measure where the instrument sits in that stratum.
2. When known biology and the data disagree, write both branches down before choosing one.
3. Attack the result you hoped for at a finer stratum.
4. When a tool writes two reports, check whether they are filtered differently.
5. Type the absence: instrument-driven and real are two states, and unknown is a third.
6. A between-model contrast is quoted only with its comparison K inside every arm's trained
   regime and with its seed-swap result.

## Rules, by consequence

### Absence only within the instrument's headroom in that stratum

**Before writing "X is absent in C", measure where the instrument sits in C.** Report the
margin between C's surviving calls and the cutoff beside the same margin elsewhere. A clade
whose calls pile onto the gate cannot support an absence claim, and the pile-up is itself
reportable. Each of these was read as biology before it was read as instrumentation:

- `selD` is itself a selenoprotein, so its in-frame UGA defeats gene calling: 66 of 73
  genomes called SelD-negative carried a near-full-length unannotated *selD* in their DNA.
- `TIGR00475` (SelB) sits a median **32.6 bits** over its trusted cutoff in Actinomycetota
  against **209** in Pseudomonadota, and Actinomycetota SelA+/SelB− is **46.7%** of the
  published orphan count.
- `RF01852` (tRNA-Sec): Campylobacterota's surviving calls cluster **3.2 bits** over the gate
  against **31.0** for Pseudomonadota. That leg stands on its own.

**The measured margin IS the instrument check; do not use the model's declared cutoffs to
corroborate it.** Neither `GA` vs `TC` nor `TC - NC` carries that meaning (this rule claimed
each in turn and was wrong twice). `GA` equals `TC` by NCBIfam convention (23 of 23 models in
the originating project), so that check could never fire. `TC - NC` is a database curation
convention, not a model property: Pfam and Rfam set `TC` at the lowest-scoring included member
and `NC` at the highest-scoring excluded one, so the band measures how densely the ranked hit
list is populated near the cutoff, and a large, well-sampled family has a tiny band by
construction. `RF01852` declaring **TC 47.00 against NC 46.90**, a **0.1-bit** discrimination
band, is therefore no evidence that the model "cannot absorb any phylogenetic distance".

Measured 2026-09-28: across the full Pfam-A library, **30,134 models, `TC - NC` is exactly 0.1
for 10,867 (36.1%), median 0.3, 68.3% at or under 1.0 bit**; a 0.1-bit band is the mode of
Pfam. In one project's model set the split was total: 3 Pfam models and both Rfam CMs at 0.10,
all 22 TIGRFAM/NCBIfam models between 2.0 and 177.85. **`RF00005`, generic tRNA, one of Rfam's
largest and best-curated families, declares GA 29.00 / TC 29.00 / NC 28.90**, the same band as
`RF01852`; `PF00266` declares the narrowest band and its hits sit 230-260 bits above `GA`
(252.4-282.2 vs 21.5, n=8). A declared band may be compared only within one source database,
and even then it is weak.

### Instrument-driven and real absence are different typed states

**An instrument-driven absence and a real absence are different states and must be typed as
such**, the same three-state discipline as in `verification-patterns`, applied to the detector
rather than to the value. Unknown is its own typed state (an enum or dedicated type, never
`bool | None`), and when you introduce one, list every consumer.

### Tools whose reports are filtered differently

When a tool writes two reports, check whether they are filtered differently; the difference is
usually invisible and always silent. `hmmsearch --cut_tc` applies the model's sequence trusted
cutoff to `--tblout` and its domain trusted cutoff to `--domtblout`. A pipeline that collected
only `--domtblout` dropped every protein whose full-sequence score cleared TC while no single
domain did, which is the normal case for a multi-domain model on a divergent sequence. The
file is written, exits `# [ok]`, and nothing reports a discrepancy. Measured across 23,414
proteomes (2026-09-25):

    TIGR00475 (SelB, 581 cols, ~4 domains)   4,611 -> 4,940   +329  (+7.1%)
    TIGR00474 (SelA, 455 cols)               5,341 -> 5,348     +7
    NF041186  (SenA, 382 cols)                 405 ->   408     +3
    TIGR00476 (SelD, 311 cols, ~1 domain)    8,807 -> 8,807     +0

None lost in the other direction, so the sequence-level set is a strict superset. Worked case:
full sequence 268.3 against TC 242.25 passes, best single domain 216.1 fails (signal split
216.1 + 34.9 + 14.1). It cost a published headline 27% (an orphan count of 1,121 that is really
816) and moved a project's core population by 3. In general:

- **Any tool with more than one output format may gate them differently.** Read the manual for
  the format you parse, not for the tool; the same holds for summary vs detail reports,
  `--long`/`--short` modes, and API "list" vs "get" endpoints with different default filters.
- **Prefer the report whose UNIT matches your question.** A membership question ("does this
  genome have the gene?") is sequence-level; a coordinate question ("where does the domain
  align?") is domain-level. The pipeline above needed both and collected one.
- **When two reports should agree, compute the difference and store it**, with a third state
  for "this run produced only one of them, so the gap is NOT MEASURABLE". A clean zero and an
  unmeasurable gap are different states.
- **The symptom to watch for is a phylum, class or subgroup that looks "marginal" on one
  instrument.** It was read here as a model failing a clade for a whole investigation. A
  subgroup pressed against a threshold is sometimes real divergence and sometimes a collection
  artifact; re-running distinguishes them, reasoning does not.

### Attack confirming results, not only surprising ones

Attack the results that confirmed what you expected, not only the surprising ones. Effort is allocated by surprise, so confirming results are the least audited and the most
likely to be quietly wrong. Take the wave's best result and try to dissolve it: match at a
finer stratum, swap the denominator, restrict instead of stratify. Measured 2026-09-25: "not
one of 3,866 fusion proteins carries Sec, and phylum does not explain it, P(0) = 1.3e-10"
dissolved under finer matching, 22.80 expected at phylum → 14.21 at class → 3.09 at order
(p = 0.045) → **0.25 at family (p = 0.78)** → 0.00 at genus: the effect was where fusions live,
not what they are. State the power loss honestly: comparator coverage fell 887 → 284 across
those ranks, so "expected 0.00" is partly an absence of comparator, not of effect.

`anomaly-hunter` owns this (added 2026-09-25). Every other review seat is biased toward closure
(`critic-reviewer` on "the code does what it says", `domain-reviewer` on "plausible given what
we know", which is the instrument that buries a real result). Dispatch it at wave end beside
`domain-reviewer`, and before any result is written down as settled.

### Both branches when known biology and the data disagree

**When known biology says a thing must be present and the data says absent, write BOTH branches
down before choosing.** Branch A, the instrument is failing: name how and measure it; the
failure mode is a finding in its own right. Branch B, the premise does not hold here: you have
found something. A write-up naming only branch A has not done the work. The marker is *"X must
be true, therefore the measurement is wrong"*: usually right, which is why it is invisible when
it is not.

### A general score depression is a mechanism, not a verdict

Campylobacterota scores lower on every selenium model (SelA 0.88, SelD 0.81, SelB 0.65 of
Pseudomonadota's median). That makes "the cutoff is failing this clade" plausible, not true.
Test it against a **within-clade true-negative control** (same composition, pathway genuinely
absent) and expect the control to be noisy: there the negative arm produced a hit in **40/40**
genomes and 4 cleared GA, so "a sub-threshold hit exists" proved nothing. What discriminated
was a relational measure the negatives could not fake: the Sec model outscoring the generic
tRNA model at the same locus, 16/16 in the test arm, **0/80** in controls.

### Between-model contrasts: K in regime, seed-swap first

A between-model contrast is quoted only with its comparison K inside every arm's trained regime
and with its seed-swap result. Run the seed-swap negative control before the first results
table, not at wave end (R-20261025-8).
