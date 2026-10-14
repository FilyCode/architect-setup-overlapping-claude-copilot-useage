---
name: verification-patterns
description: Catalogue of verification failures seen in this workspace — stale artifacts, gates that cannot fail, vacuous tests, counts taken with grep, fixes that are effective but unsafe, claims and docs that decay. Use when writing or reviewing a test, gate or check, or before claiming a fix works. Scientific absences and anomalies are in scientific-evidence.
---

# Verification patterns

Each entry is a failure that actually happened here, with the check that catches it. Before
claiming a fix works, find the entries that match what you changed and apply their checks. A
gate or guard is verified by removing it and watching its test fail.

The rules below are the original workspace text, moved verbatim.

## Reference files (read the one you need)

- See [reference/part-2.md](reference/part-2.md) — A test made vacuous by a change that never edited it. `test_; **A capability claimed as "implemented" with no call path.**; **Match the command as invoked, not as idealised.** `^git lo; **A positive control built from a convenient fixture proves ; **Check the aggregate's distribution before optimising for i; The earlier line in this file that "every other command runs; Before blaming the wrapper, 
- See [reference/part-3.md](reference/part-3.md) — **Making a no-op live is a behaviour change, and must not al; **A boundary test that does not probe the disputed interval ; Reporting.** State what was run and what it returned. If tes; A plan's own tests and fixtures are suspects, not specificat; one never exercised the state it existed to protect — the `U; one asserted a branch that never executes (`if "ef_ec_confid; one used a fixture that coul

Old file names in the moved text are retired: `subagent-dispatch.md` is now the skills
`dispatch-brief`, `wave-review` and `plan-critique`; `verification.md` is `verification-patterns`
and `scientific-evidence`; `scc.md` is `running-sge-jobs`.

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
<!-- from verification.md:7 -->
**The shapes this takes**

<!-- from verification.md:9 -->
- An output file predates the fix, or was never regenerated. Check mtimes against the fix,
  or rerun and diff — do not reason about which outputs "should be unaffected".
<!-- from verification.md:11 -->
- A clean exit code with no artifact. A tool that catches its own errors exits 0 having
  produced nothing. Check the expected file exists.
<!-- from verification.md:13 -->
- A comment or docstring describes a change the code below it never received. After
  changing behaviour, grep the actual invocation line, not the prose around it.
<!-- from verification.md:15 -->
- A plan's own example code carries the bug. Re-derive maths, library behaviour and
  adapter signatures from real current source — especially against any claim of the form
  "this is exact", "this mirrors the existing pattern", or "this always holds".
<!-- from verification.md:18 -->
- A field survives the forward path but is dropped by checkpoint serialization, so only
  resumed runs are wrong, silently. Test the round-trip's downstream consequence.
<!-- from verification.md:20 -->
- A cached column or stored flag is trusted as current. Re-check against the live source
  before reporting something as missing or needing manual work.
<!-- from verification.md:22 -->
- A gate that passes because it never exercises the path in use. A regression check ran the
  statistic on the *production* artifacts and passed, while the new code path it was meant to
  protect produced a null result for every input. When you add a code path, assume the existing
  gate does not cover it, and add a positive control on the new path specifically.
<!-- from verification.md:26 -->
- A parser validated against a fixture its own author wrote. The fixture encodes the same
  misunderstanding as the parser, so it passes a dry run and fails on first real input.
  Validate against a real artifact, or state plainly that it is unvalidated.
<!-- from verification.md:29 -->
- Two artifacts compared positionally when their row order is not guaranteed. Align on a
  unique key first. An unstable sort on a tied key is itself a reproducibility bug even when
  every value is correct — row order that changes between runs is not reproducible output.
<!-- from verification.md:32 -->
- A check that cannot fail, because it matches the wrong field. A docstring stating what a
  check does is not evidence the check works. Test it against a real case that should trip it.
<!-- from verification.md:34 -->
- A test that fails *on the fix* — the inverse of the bullet above, and it does fail, on the
  correct repair, because it asserts the defect as the expected behaviour.
  `test_plm_backend_revision_override` asserted that a 15-character non-SHA revision is
  *accepted*, pinning the defeat of a version pin. When a fix turns an existing test red, ask
  whether the test was asserting the bug before assuming the fix is wrong. Three instances
  surfaced on 2026-08-27, one in a file no task owned — per-task review cannot find those, only
  a full-suite run after the fix.
<!-- from verification.md:41 -->
- A named metric appears in a governance doc as evidence without three basic checks having been
  done: quote its defining formula from the code and state in one sentence what it physically
  measures; compute it on the control/negative arm too (if both arms saturate, the metric cannot
  support the comparison at that setting — that, not "the window/threshold was too wide," is the
  real lesson); and state the physical state of the modelled system (e.g. holo/apo, ligands present,
  which cofactors) and whether it matches the claim being made. All three are needed — each
  catches a different failure, and none substitutes for another.
<!-- from verification.md:48 -->
- **Positive-control corollary:** if a positive control scores below a candidate on the same
  metric, the metric is suspect, not the control. A yardstick that fails on a case it should have
  passed easily is broken before it says anything about the harder case.
<!-- from verification.md:51 -->
- A number that supports or closes a claim in a governance doc (decisions/findings/summary/status
  files) traces only to chat-report or ledger prose, never to a committed script + output
  artifact. Plausibility is not provenance — a wrong number survives review precisely because it
  looks right; require it to resolve to something on disk before it is cited as evidence.
<!-- from verification.md:55 -->
- Report-generating code contains a hardcoded numeric literal in its prose output, rather than
  formatting a value computed from data. This is the mechanism, not just a symptom — a literal
  sitting in a template is exactly how a fabricated statistic gets produced and then gets cited as
  if it were computed.
<!-- from verification.md:59 -->
- Two populations/rates/groups get compared without first listing every axis they could differ on
  (taxonomy, detection method, window or distance scale, copy number, annotation quality,
  sampling) and stating which were matched and which were not. Fixing only the one axis you were
  told about just relocates the confound to the next one.
<!-- from verification.md:63 -->
- An isolation run credited with more than it executed. Isolating a diff to find *whose* failures
  these are is valid **attribution** and invalid **clearance** — the two need different runs, and
  the second always costs a full suite. On 2026-08-29 an isolation over the five *failing* files
  correctly attributed 9 failures to one agent, and was then quoted as "the other agent's work is
  clean"; that run never executed the other agent's own new test file, which held 2 of its 3 real
  failures. Second half of the same rule: **a `git worktree` is not the main checkout.** Tests
  keying on CWD, an env lock, or on-disk state fail there for reasons unrelated to the diff — the
  same day, a worktree isolation reported 5 failures of which 2 reproduced on a clean worktree
  with *no diff applied*. Run a clean-worktree baseline before believing any worktree failure, and
  read the **skip count**, not only the FAILED lines: 23-vs-12 skipped was the only visible tell
  that the environment differed.
<!-- from verification.md:74 -->
- A green mocked test over a code path that cannot reach its service at all. Mocked transport
  asserts what the code does with a response it was handed; it cannot observe that no socket
  ever opens. On 2026-08-29 an ID-mapping path had a full mocked suite passing while every real
  call died in the TLS handshake — and behind that, once the handshake was fixed, every call
  returned HTTP 400 for a second, independent reason. Two stacked defects, neither reachable by
  any mock, in a path whose paging bug had been "fixed" with mocked tests 43 minutes earlier. For
  an adapter that talks to an external service, evidence is **one live call showing the real
  response**; the regression test then asserts the *construction* (that the session is built
  with the right policy), because that is the part that silently regressed and the part a test
  can actually hold.
<!-- from verification.md:84 -->
- A claim written into multiple locations gets its scope qualifier updated in only one of them.
  This is asymmetric in practice: a strengthening edit naturally recruits the author to hunt down
  every place the old, weaker claim lived, but an edit that *undercuts* an existing claim gets
  written once and the other locations are never revisited because nothing there looks wrong, only
  unsupported. When a finding undercuts an existing claim, grep for that claim's other homes
  before considering the fix committed.

<!-- from verification.md:91 -->
- A three-state value collapsed back to two at a boundary its author did not own. This is
  the single most repeated defect in this workspace: **five instances in one wave**
  (2026-09-01), two of them in code written during that wave *to fix* the class, by agents
  whose briefs quoted the convention. Unknown became `False` and manufactured a novelty flag;
  became "index unavailable" with no flag; became **`unanimous`, the strongest state**; became
  a prediction failure; became `[]`, identical to a genuine empty result. **A three-state
  value must be typed, not conventional** — introduce it as a distinct type or explicit enum,
  never a `bool | None` guarded by a comment, because `bool()`, `or False`, `.get(k, False)`
  and any truthiness test erases the third state silently. **At introduction, enumerate every
  consumer** with `command grep` across `src/`, tests, renderers and exporters, and list them
  in the commit message: four of those five collapses were in a consumer the introducing
  change never looked at.
<!-- from verification.md:103 -->
- **A check that compares a derived quantity between two populations read through the SAME code
  path, with no liveness assertion.** Rename the field and BOTH sides go to zero; the comparison
  then passes vacuously, forever, and nothing reddens. Three instances in one wave (2026-09-21),
  including an implementer discovering its **own** synthetic tests were vacuous because a fixture
  package name never resolved — caught only because one of them *passed on the unfixed code*. The
  repair is one line: assert the quantity is non-zero on at least one side before comparing. Prove
  it by removing the guard and watching the check pass anyway.
<!-- from verification.md:110 -->
- **Where a record carries both a generated field and a hand-written one, the hand-written one holds
  ALL the decay risk and needs MORE verification, not less.** Stated best by the agent who missed it:
  *"a `reach:` value is regenerated on every `--write` and cannot drift; a `no-impl` reason is prose
  nothing re-checks."* It had been sizing verification effort by how **visible** a claim was rather
  than how **load-bearing**. The same error produced its earlier miss — it verified a baseline's
  *counts* were untouched (they were) and never read its *prose*, which the preceding commit had
  just falsified.
<!-- from verification.md:117 -->
- **When you correct a false statement, check what was DECIDED on it.** A false premise that
  supported a decision means the decision is now unjustified-as-written, and that belongs in the
  record rather than buried under the correction. A CI comment asserted the job ran Python 3.13 and
  used that to justify making a type-check ratchet report-only instead of gating; the job runs
  3.11.13, the same version CI pins. Correcting the sentence exposed that the gating decision rests
  on nothing — which is now a visible open question instead of a settled one.
<!-- from verification.md:123 -->
- **Four shape gates cannot detect decay.** A gate that validates a record's *shape* — row count,
  enum membership, non-empty reason — can never go red when its *content* stops being true: a
  parked item whose blocker was resolved, a superseded item whose named replacement was itself
  deleted. At least one gate must **dereference a claim**. This objection reshaped a wave's largest
  deliverable from four shape checks into five of which three dereference, and all three were then
  watched failing against a mutated copy of the real artifact.
<!-- from verification.md:129 -->
- A claim that a signal is live, or dark, argued from wiring rather than measured. **Firing is
  not moving.** On 2026-09-01 a controller reported "no shipped score moves" from a code
  comment, a reviewer corrected it to "the signal is live, so scores move", and the
  measurement showed it was live *and algebraically incapable of changing any score* — it sat
  in a `max`-folded group where its own upper bound could never beat a co-member. Three
  parties reasoned about connectivity; none probed behaviour. The cheap probe is the value's
  **own upper bound**: if the output does not move there, the signal cannot move it anywhere.
<!-- from verification.md:136 -->
- A boundary held constant while the thing producing it changed meaning, with no version stamp
  on the output. **Stability of the scale is not stability of the meaning** — it is what makes
  old and new artifacts incomparable *while looking comparable*. If a score's inputs, grouping
  or semantics change, bump a version that travels with every artifact carrying it and refuse
  to resume across a mismatch. "No boundary was touched" was offered as this workspace's
  safety property on 2026-09-01 and was precisely the hazard.
