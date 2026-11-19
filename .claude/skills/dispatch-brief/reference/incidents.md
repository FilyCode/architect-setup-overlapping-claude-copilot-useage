# dispatch-brief: worked incidents

The rules are in [../SKILL.md](../SKILL.md); this file keeps the incidents behind them.

Contents:
- Wait-and-report stalls (2026-08-29, 2026-09-05)
- Relayed figures and wrong citations (2026-08-24 to 2026-09-21)
- Reviewers that hit the turn limit (2026-08-29 to 2026-09-23)
- Shared worktrees and a frozen-tree claim (W2b-1 2026-09-23)
- A defect documented instead of fixed
- Model and effort tiering

## Wait-and-report stalls (2026-08-29, 2026-09-05)

An implementer told to wait for an SGE job and report polled `qstat`/`qacct` across ~4
round-trips at ~230k tokens each (1M+ tokens). On 2026-08-29 four subagents in one session ended
their turn mid-wait anyway, one after 350k tokens and 171 tool calls, another after 555k, and the
caller had to check the job regardless. On 2026-09-05 two agents stalled at 176k and 285k tokens,
each told verbatim *"submit, report the job id, and STOP"*, with the rule written in two other
places: three statements, two violations. Hence the caller owns every `qsub`: waiting is then not
expressible rather than merely forbidden.

## Relayed figures and wrong citations (2026-08-24 to 2026-09-21)

- 2026-08-24: three unchecked caller claims reached commits; "stage 7c depends only on stage 1
  and stage 7a" became the final review's only Critical. The same day a subagent correctly
  disputed a stale-exemption claim.
- 2026-08-29: the contradiction slot caught five false claims in one session: a benchmark's CLI
  flags (the real mechanism was no-op degradation), an over-broad "cannot reach the service"
  claim true of one of two code paths, an EMBL/GenBank accession called RefSeq, a "permanently
  dormant" contradiction that dissolved against manifest dates, a corpus size understated by half.
- 2026-09-01: `0.0717` travelled through a plan, a brief and a backlog entry before it was found
  to be 16/223 with a 48-row comparator; the missing n failed three times in the wave. Eleven of
  twelve implementers found an error in the controller's brief; the classes were figures without
  n, drifting line numbers, and mechanism descriptions.
- Two agents reported 1,577 (10.79%) and 1,459 (9.98%) on the same wire and corpus, on
  `top_hit_identity` and `identity_to_donor` respectively; two artifacts quoted as "the b10
  corpus" differed on 87 rows because one `fuse()` call omitted a signal.
- W2 2026-09-21: six wrong citations, all the controller's: three relayed from a subagent report,
  two from grep where a parser was needed, one SHA attributed to the wrong action and pre-labelled
  as a copy-paste defect. The stop rule made one implementer resolve 71 shell scripts, find the
  number inverted, and write nothing. `check_citations.py` catches a reconstruction of all six
  except the two counts.
- W2b-1: an implementer refused two rows correctly because it read the full per-row record, not
  the controller's table (one fix site was another file; one row was blocked on an open finding).

## Reviewers that hit the turn limit (2026-08-29 to 2026-09-23)

A wave-end `critic-reviewer` (2026-08-29) burned 162,646 tokens over 49 tool calls exploring
five equal areas and returned one sentence; resumed with a findings file, ranked areas and a drop
order, it produced one Blocking and three lesser findings. W14's reviewer repeated it (162,630
tokens, 44 calls): the controller had included the objection slot in every review dispatch and
missed the findings-file line mid-paragraph, so the failure was retrieval, and the review
checklist is now one lookup. On 2026-09-07 a reviewer given the file path and the append
instruction returned nothing after 144,164 tokens and 45 calls, never having created the file. In
W2b-1 seat 1 hit its 40-turn limit with no report, but its file held 125 lines and three
findings, one Blocking (CI red at HEAD). W2b-1's domain seat added the no-negative-control
objection: three of its six findings were in dark modules wrong for months because nothing ran
them on data. W2: removing a guard proved it load-bearing; regenerating into scratch gave
`rewrote 0 line(s)`. W14: the objection slot produced three of the best findings.

## Shared worktrees and a frozen-tree claim (W2b-1 2026-09-23)

A review brief said *"the working tree is clean and HEAD is frozen at `56993903`"*; the controller
kept committing fixes while six seats ran, and a seat files drift findings against corrected text
when told not to look. A reviewer ran a generator in `--write` mode, then restored the file with
`cp`, silently reverting a newer controller version; a gate went red for no visible reason. On
2026-09-01 one agent's bare commit swept another's staged file, and the reverse happened to a
third; `git show --stat` caught both.

## A defect documented instead of fixed

`pipeline/stages.py` gained 94 lines: 81 comment, 1 blank, 12 code; two of the twelve were
`_confidence_config_snapshot = None` in branches differing only by their comment. A 55-line
comment named the defect, the fix and the rule, and survived four agents and a review.
One-file-per-agent ownership manufactures unowned seams. A four-task chain built a manifest field,
wired two call sites and a typed enum, and nobody passed the value; its own test passed it directly.

## Model and effort tiering

| Task shape | Model | Effort |
|---|---|---|
| Small check, lint-shaped question, single-file mechanical fix | haiku | low |
| Ordinary coding task, single-module change | sonnet | low-medium |
| Coding task with real design tradeoffs | sonnet | high |
| Large rewrite, cross-cutting architecture, highest-stakes review | opus | medium-high |

A judgment per task, not a lookup; no hook enforces it.
