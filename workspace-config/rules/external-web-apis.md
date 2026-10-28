---
paths:
  - "projects/**"
---

# External web APIs (NCBI, UniProt, ENA, BLAST)

Why: F1 NCBI enrichment took ~2 days from ~6.8 single-id requests per protein, 475 whole-record
downloads (1,126 MB) and serial web BLAST (1 of 11 queries in ~10 h). Evidence:
config `.superpowers/findings/2026-10-27/ncbi-efficiency/audit.md`.

1. Local first: a pinned local index or table before any web call; web BLAST is never the default.
2. Batch by id: one call per chunk of ids (E-utilities ≤ 200, epost/WebEnv above; UniProt OR-batches),
   never a per-id loop; a per-id fallback only for ids the batch missed, typed and counted.
3. Fetch windows, not records: `seq_start`/`seq_stop` once coordinates are known; a whole-record
   fetch needs a logged reason.
4. One session per service, the API key from the site file (never printed), `tool` and `email`
   on every call, one process-wide rate limiter (NCBI: 10 req/s with key, 3 without), a total deadline.
5. Web BLAST: ≥ 10 s between contacts, poll a RID at most once per 60 s, reuse the RID after a
   transient error, > 50 searches only off-peak (NCBI developerinfo), multi-query Puts.
6. EBI/ENA: TLS 1.2 sessions; reuse them.
7. A "batched" or "efficient" claim needs a call-site grep and a request count from a real run
   (manifest `http_breakers[...].sent`), not a reading of the code.
