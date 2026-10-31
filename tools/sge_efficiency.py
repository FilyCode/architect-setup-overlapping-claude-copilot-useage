#!/usr/bin/env python3
"""Measured CPU use of this user's SGE jobs, read incrementally from the SGE accounting file.

`qacct` needs ~2 min for 14 days; this reads only the bytes appended since the last run and
keeps the last DAYS days of the user's records in a JSON cache under software/ (home is
quota-capped). The qsub guard hook reads the per-job-name summary; people read `report`.

  sge_efficiency.py refresh            # incremental read (seeds ~SEED_BYTES on first run)
  sge_efficiency.py report [--days N]  # job names ranked by reserved-but-unused core-hours
  sge_efficiency.py job <jobid>        # cores used vs slots for one finished job (or array)
  sge_efficiency.py lookup <name>      # summary row the guard uses for a job name

Cores used = cpu / ru_wallclock (accounting fields 37 and 14); efficiency = cores used / slots.
"""
import argparse
import fcntl
import getpass
import json
import os
import statistics
import sys
import time
from pathlib import Path

ACCOUNTING = Path(os.environ.get("SGE_ACCOUNTING",
                                 "/usr/local/ogs-ge2011.11.p1/sge_root/default/common/accounting"))
CACHE_DIR = Path(os.environ.get("SGE_EFF_CACHE", "/projectnb/liu-scc/philipp/software/claude-sge"))
CACHE = CACHE_DIR / "efficiency.json"
DAYS = 60
SEED_BYTES = 1_800_000_000  # ~60 days of the shared accounting file (300 MB ~ 11 days, 2026-10-31)
MIN_WALL = 60  # seconds; shorter runs say little about steady-state core use

# accounting(5) field positions, 0-based
F_NAME, F_JOB, F_END, F_WALL, F_PROJ, F_SLOTS, F_TASK, F_CPU, F_CAT, F_MAXVMEM = 4, 5, 10, 13, 31, 34, 35, 36, 39, 42


def parse_line(line: str, owner: str):
    f = line.rstrip("\n").split(":")
    if len(f) < 43 or f[3] != owner:
        return None
    try:
        wall, slots, cpu = float(f[F_WALL]), int(f[F_SLOTS]), float(f[F_CPU])
        end = int(f[F_END])
    except ValueError:
        return None
    if end == 0:
        return None
    return {"name": f[F_NAME], "job": f[F_JOB], "task": f[F_TASK], "proj": f[F_PROJ], "slots": slots,
            "wall": wall, "cpu": cpu, "end": end, "gb": round(float(f[F_MAXVMEM] or 0) / 2**30, 2),
            "gpu": "gpus=" in f[F_CAT]}


def load():
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return {"inode": None, "offset": 0, "records": [], "updated": 0}


def summarize(records):
    """Per job name: runs, median slots, median cores used, median efficiency (runs >= MIN_WALL)."""
    by = {}
    for r in records:
        if r["wall"] >= MIN_WALL and r["name"] != "QRLOGIN":
            by.setdefault(r["name"], []).append(r)
    out = {}
    for name, rs in by.items():
        used = [r["cpu"] / r["wall"] for r in rs]
        out[name] = {"n": len(rs), "slots": statistics.median(r["slots"] for r in rs),
                     "cores_used": round(statistics.median(used), 2),
                     "eff": round(statistics.median(u / r["slots"] for u, r in zip(used, rs)), 2),
                     "last_end": max(r["end"] for r in rs), "gpu": any(r["gpu"] for r in rs)}
    return out


def refresh(owner=None):
    owner = owner or getpass.getuser()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / "refresh.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return load()  # another refresh is running
        st = ACCOUNTING.stat()
        state = load()
        offset = state["offset"] if state["inode"] == st.st_ino and state["offset"] <= st.st_size else None
        records = state["records"] if offset is not None else []
        if offset is None:  # first run or file rotated: seed from the tail
            offset = max(0, st.st_size - SEED_BYTES) if state["inode"] is None else 0
        with open(ACCOUNTING, "rb") as fh:
            fh.seek(offset)
            if offset:
                fh.readline()  # drop a partial line (harmless if it was whole and already counted)
            for raw in fh:
                if not raw.endswith(b"\n"):
                    break  # writer mid-line; re-read next time
                offset = fh.tell()
                if b":" + owner.encode() + b":" not in raw:
                    continue
                r = parse_line(raw.decode("utf-8", "replace"), owner)
                if r:
                    records.append(r)
            else:
                offset = fh.tell()
        cutoff = time.time() - DAYS * 86400
        records = [r for r in records if r["end"] >= cutoff]
        new = {"inode": st.st_ino, "offset": offset, "records": records,
               "summary": summarize(records), "updated": int(time.time())}
        tmp = CACHE.with_suffix(".tmp")
        tmp.write_text(json.dumps(new))
        tmp.replace(CACHE)
        return new


def report(days, project=None, top=30):
    data = load()
    cutoff = time.time() - days * 86400
    rs = [r for r in data["records"] if r["end"] >= cutoff and (not project or r["proj"] == project)]
    res = sum(r["slots"] * r["wall"] for r in rs) / 3600
    used = sum(r["cpu"] for r in rs) / 3600
    print(f"{len(rs)} job records, last {days} d{' project ' + project if project else ''}: "
          f"reserved {res:.0f} core-h, used {used:.0f} cpu-h ({used / res if res else 0:.0%}). "
          f"Cache updated {time.strftime('%F %H:%M', time.localtime(data['updated']))}.")
    by = {}
    for r in rs:
        b = by.setdefault((r["proj"], r["name"], r["slots"]), [0, 0.0, 0.0])
        b[0] += 1
        b[1] += r["slots"] * r["wall"] / 3600
        b[2] += r["cpu"] / 3600
    print(f"{'project':12} {'job name':24} {'slots':>5} {'runs':>5} {'res core-h':>10} {'cpu-h':>7} "
          f"{'cores used':>10} {'unused core-h':>13}")
    for (proj, name, slots), (n, rh, ch) in sorted(by.items(), key=lambda x: x[1][2] - x[1][1])[:top]:
        print(f"{proj[:12]:12} {name[:24]:24} {slots:>5} {n:>5} {rh:>10.1f} {ch:>7.1f} "
              f"{slots * ch / rh if rh else 0:>10.2f} {rh - ch:>13.1f}")


def job(jobid):
    rs = [r for r in refresh()["records"] if r["job"] == str(jobid)]
    if not rs:
        print(f"job {jobid}: not in the accounting file yet (it may still be running, or accounting lags "
              "a few seconds; retry once)")
        return 1
    res = sum(r["slots"] * r["wall"] for r in rs)
    cpu = sum(r["cpu"] for r in rs)
    slots = rs[0]["slots"]
    used = slots * cpu / res if res else 0
    verdict = "OK" if slots == 1 or used >= 0.5 * slots else \
        f"OVER-RESERVED: next time request -pe omp {suggest(used)}"
    print(f"job {jobid} ({rs[0]['name']}, {len(rs)} task(s)): slots {slots}, cores used {used:.2f} "
          f"({used / slots:.0%}), max mem {max(r['gb'] for r in rs):.1f} GB -> {verdict}")
    return 0


def suggest(cores_used: float) -> int:
    """Smallest of SCC's efficient sizes (1/2/4/8/16/28) covering cores used with ~25% headroom.

    Up to 1.3 cores used is a single-threaded job with some I/O or interpreter overhead: 1 slot.
    """
    if cores_used <= 1.3:
        return 1
    need = cores_used * 1.25
    return next((k for k in (1, 2, 4, 8, 16, 28) if k >= need), 28)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("refresh")
    p = sub.add_parser("report")
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--project")
    p.add_argument("--top", type=int, default=30)
    p = sub.add_parser("job")
    p.add_argument("jobid")
    p = sub.add_parser("lookup")
    p.add_argument("name")
    a = ap.parse_args(argv)
    if a.cmd == "refresh":
        d = refresh()
        print(f"{len(d['records'])} records cached in {CACHE}")
    elif a.cmd == "report":
        refresh()
        report(a.days, a.project, a.top)
    elif a.cmd == "job":
        return job(a.jobid)
    elif a.cmd == "lookup":
        print(json.dumps(load().get("summary", {}).get(a.name)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
