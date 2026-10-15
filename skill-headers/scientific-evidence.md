---
name: scientific-evidence
description: Rules for scientific claims from pipelines — absence only within the instrument's headroom in that stratum, both branches when biology and data disagree, attacking confirming results, composition effects, tools whose reports are filtered differently. Use when a result says something is absent, surprising, confirmed, or about to be written down as settled.
---

# Scientific evidence

Before writing "absent", measure where the instrument sits in that stratum. When known biology
and the data disagree, write both branches down before choosing one. Attack the result you
hoped for at a finer stratum. When a tool writes two reports, check whether they are filtered
differently.

The moved text below refers to "the same three-state discipline as everywhere else in this
file": that file is now the `verification-patterns` skill. The rule itself: unknown is its own
typed state (an enum or dedicated type, never `bool | None`), and when you introduce one, list
every consumer. An instrument-driven absence and a real absence are two different states.

The rules below are the original workspace text, moved verbatim, including the worked cases.
