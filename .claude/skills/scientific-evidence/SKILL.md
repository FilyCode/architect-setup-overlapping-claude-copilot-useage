---
name: scientific-evidence
description: Rules for scientific claims from pipelines — absence only within the instrument's headroom in that stratum, both branches when biology and data disagree, attacking confirming results, composition effects, tools whose reports are filtered differently. Use when a result says something is absent, surprising, confirmed, or about to be written down as settled.
---

# Scientific evidence

Before writing "absent", measure where the instrument sits in that stratum. When known biology
and the data disagree, write both branches down before choosing one. Attack the result you
hoped for at a finer stratum. When a tool writes two reports, check whether they are filtered
differently.

The rules below are the original workspace text, moved verbatim, including the worked cases.

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
<!-- from verification.md:372 -->
- `selD` is itself a selenoprotein, so its in-frame UGA defeats gene calling — 66 of 73
  genomes called SelD-negative carried a near-full-length unannotated *selD* in their DNA;
<!-- from verification.md:374 -->
- `TIGR00475` (SelB) sits a median **32.6 bits** over its trusted cutoff in Actinomycetota
  against **209** in Pseudomonadota, and Actinomycetota SelA+/SelB− is **46.7%** of the
  published orphan count;
<!-- from verification.md:377 -->
- `RF01852` (tRNA-Sec) declares **TC 47.00 against NC 46.90** — a **0.1-bit** discrimination
  band — and Campylobacterota's surviving calls cluster **3.2 bits** over the gate against
  31.0 for Pseudomonadota.

Each was read as biology before it was read as instrumentation. So:

<!-- from verification.md:383 -->
- **Before writing "X is absent in C", measure where the instrument sits in C.** Report the
  margin between C's surviving calls and the cutoff beside the same margin elsewhere. A clade
  whose calls pile onto the gate cannot support an absence claim, and the pile-up is itself
  reportable. **The measured margin IS the instrument check. Do not reach for the
  model's declared cutoffs to corroborate it** — neither `GA` vs `TC` nor `TC - NC`
  carries the meaning this rule twice claimed for them.

  The history is worth keeping because the same error was made twice in a row, in
  opposite directions, by an author each time convinced the previous version was the
  careless one. Version 1 said to compare `GA` vs `TC`; those are equal by NCBIfam
  convention (23 of 23 models in the originating project), so it could never fire.
  Version 2 replaced it with `TC - NC` and cited `RF01852` (tRNA-Sec) declaring a
  0.1-bit band as evidence of a model that "cannot absorb any phylogenetic distance".
  **That is also wrong, and it is wrong for a reason that generalises: `TC - NC` is a
  database curation convention, not a property of the model.** Pfam and Rfam set `TC`
  at the lowest-scoring included member and `NC` at the highest-scoring excluded one,
  both adjacent in a ranked hit list, so the band measures **how densely that list is
  populated near the cutoff** — a function of family size and sampling. A large,
  well-sampled family has a tiny band by construction.

  Measured 2026-09-28, and the segregation is total. Across the full Pfam-A library,
  **30,134 models: `TC - NC` is exactly 0.1 for 10,867 of them (36.1%), median 0.3,
  68.3% at or under 1.0 bit.** A 0.1-bit band is the *mode* of Pfam, not an outlier.
  In one project's own model set the split is perfect with no overlap: all 3 Pfam
  models at 0.10, both Rfam CMs at 0.10, and all 22 TIGRFAM/NCBIfam models between
  2.0 and 177.85. The decisive case sat unread in that project's own `data/cm/`:
  **`RF00005`, generic tRNA — one of Rfam's largest and best-curated families —
  declares GA 29.00 / TC 29.00 / NC 28.90, the identical 0.1-bit band as `RF01852`.**
  A counterexample from the same corpus: `PF00266` declares the narrowest possible
  band and its hits sit 230-260 bits above `GA` (252.4-282.2 vs 21.5, n=8).

  So: a declared band may be compared only **within one source database**, and even
  then it is weak. The instrument check that survives is the empirical one this rule
  opens with — the margin between a stratum's surviving calls and the gate, beside
  the same margin elsewhere. In the originating project that was Campylobacterota's
  tRNA-Sec calls clustering **3.2 bits** over the gate against **31.0** for
  Pseudomonadota, and that leg stands on its own.
<!-- from verification.md:420 -->
- **A general score depression is a mechanism, not a verdict.** Campylobacterota scores lower
  on *every* selenium model (SelA 0.88, SelD 0.81, SelB 0.65 of Pseudomonadota's median). That
  makes "the cutoff is failing this clade" plausible; it does not make it true. Test it against
  a **within-clade true-negative control** — same composition, pathway genuinely absent — and
  be ready for the control to be noisy: in that probe the negative arm produced a hit in
  **40/40** genomes and 4 of them cleared GA, so "a sub-threshold hit exists" proved nothing.
  What discriminated was a *relational* measure the negatives could not fake (the Sec model
  outscoring the generic tRNA model at the same locus: 16/16 in the test arm, **0/80** in
  controls).
<!-- from verification.md:429 -->
- **When known biology says a thing must be present and the data says absent, write BOTH
  branches down before choosing.** Branch A, the instrument is failing — then name how, measure
  it, and the failure mode is a finding in its own right. Branch B, the premise does not hold
  here — then you have found something. A write-up naming only branch A has not done the work.
  The phrasing that marks the error is *"X must be true, therefore the measurement is wrong"*;
  it is usually right, which is exactly why it is invisible when it is not.
<!-- from verification.md:435 -->
- **An instrument-driven absence and a real absence are different states and must be typed as
  such** — the same three-state discipline as everywhere else in this file, applied to the
  detector rather than to the value.

<!-- from verification.md:439 -->
**Attack the results that CONFIRMED what you expected, not only the surprising ones.** Effort
is allocated by surprise, so confirming results are the least audited and the most likely to be
quietly wrong. Measured on 2026-09-25: a wave's own headline negative — "not one of 3,866 fusion
proteins carries Sec, and phylum does not explain it, P(0) = 1.3e-10" — **dissolved under finer
matching**, going 22.80 expected at phylum → 14.21 at class → 3.09 at order (p = 0.045) → **0.25
at family (p = 0.78)** → 0.00 at genus. The effect was where fusions *live*, not what fusions
*are*. Nobody asked, because the result was the one being hoped for. Take the wave's best result
and try to dissolve it: match at a finer stratum, swap the denominator, restrict instead of
stratify. State the power loss honestly when you do — comparator coverage fell 887 → 284 across
those ranks, so the fine strata lose power as well as confound, and "expected 0.00" is partly an
absence of comparator rather than a demonstrated absence of effect.

The seat that owns all of this is **`anomaly-hunter`** (`.claude/agents/anomaly-hunter.md`,
opus/45 turns), added 2026-09-25. Every other review seat is structurally biased toward closure
— `critic-reviewer` closes on "the code does what it says", `domain-reviewer` closes on "this is
plausible given what we know", and *plausible given what we know* is precisely the instrument
that buries a real result. Dispatch it at wave end alongside `domain-reviewer`, and before any
result is written down as settled.

**When a tool writes two reports, check whether they are FILTERED differently — the
difference is usually invisible and always silent.** `hmmsearch --cut_tc` applies the
model's SEQUENCE trusted cutoff to `--tblout` and its DOMAIN trusted cutoff to
`--domtblout`. A pipeline that collected only `--domtblout` therefore dropped every protein
whose full-sequence score cleared TC while no single domain did — and a multi-domain model on
a divergent sequence fragments its alignment, so that is the *normal* case, not an edge one.
The dropped file is written, exits `# [ok]`, and is empty. Nothing anywhere reports a
discrepancy.

Measured across 23,414 proteomes on 2026-09-25, and the shape of the damage is the tell:

    TIGR00475 (SelB, 581 cols, ~4 domains)   4,611 -> 4,940   +329  (+7.1%)
    TIGR00474 (SelA, 455 cols)               5,341 -> 5,348     +7
    NF041186  (SenA, 382 cols)                 405 ->   408     +3
    TIGR00476 (SelD, 311 cols, ~1 domain)    8,807 -> 8,807     +0

Zero lost in the other direction, so the sequence-level set is a strict superset. One
worked case: full sequence 268.3 against TC 242.25 passes, best single domain 216.1 fails,
signal split 216.1 + 34.9 + 14.1. It cost a published headline 27% (an orphan count of 1,121
that is really 816) and moved a project's core population by 3.

Generalising, because the specific flag is not the point:

<!-- from verification.md:481 -->
- **Any tool with more than one output format may gate them differently.** Read the manual
  for the format you are parsing, not for the tool. The same applies to summary-vs-detail
  reports, `--long`/`--short` modes, and API "list" versus "get" endpoints that apply
  different default filters.
<!-- from verification.md:485 -->
- **Prefer the report whose UNIT matches your question.** A membership question ("does this
  genome have the gene?") is a sequence-level question; a coordinate question ("where does
  the domain align?") is a domain-level one. The pipeline above needed both and collected one.
<!-- from verification.md:488 -->
- **When two reports should agree, compute the difference and store it**, with a third state
  for "this run produced only one of them, so the gap is NOT MEASURABLE". A clean zero and an
  unmeasurable gap are different, and collapsing them is the error this file names most often.
<!-- from verification.md:491 -->
- **The symptom to watch for is a phylum, class or subgroup that looks "marginal" on one
  instrument.** That was read here as a biological signal (a model failing a clade) for a
  whole investigation before anyone re-ran the search a different way. A subgroup pressed
  against a threshold is *sometimes* real divergence and *sometimes* a collection artifact,
  and the two are distinguished by re-running, not by reasoning.

