"""Helpers for tools/long_run.sh: read the Claude usage limits, and sum up a round for the log.
Taken from the owner's azkar project.

Usage: python tools/long_run.py wait PROBE START
       python tools/long_run.py checked
       python tools/long_run.py report ROUND PROBE CHECKED_BEFORE

PROBE and ROUND are the output of `claude -p ... --output-format stream-json --verbose`.
Its rate_limit_event lines give the account's use of the 5-hour and the weekly limit
(0 to 1) and when each resets.

wait prints "SECONDS REASON": how long to wait before the next round may start (0: start now).
A round doesn't start while the 5-hour window is at START percent or more, because a round
cut off by the limit loses the hadith it was working on. When a limit is reached (the 5-hour
or the weekly one), the next round waits until it resets.

checked prints how many hadith are left to check, and how many there are in all.

report prints the log lines for a finished round: its length and cost, how much of each
limit it used, how many hadith it checked, its fixes and zooms, and its closing message.
"""

import argparse
import datetime
import json
import pathlib
import time
from collections import Counter

from matn import CHECKED, checked as checked_ids, hadiths, todo

NAMES = {"five_hour": "5-hour", "seven_day": "weekly"}


def read_stream(path: str) -> list[dict]:
    events = []
    try:
        lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return events
    for line in lines:
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    return events


def limits(events: list[dict]) -> tuple[dict, tuple | None]:
    """{window: (use 0-1, reset time)} as last reported, and (window, reset time) if a request was refused."""
    windows, refused = {}, None
    for event in events:
        if event.get("type") != "rate_limit_event":
            continue
        info = event.get("rate_limit_info") or {}
        for name, window in (info.get("unifiedWindows") or {}).items():
            windows[name] = (window.get("utilization"), window.get("resetsAt"))
        if info.get("status") == "rejected" and info.get("resetsAt"):
            refused = (info.get("rateLimitType"), info["resetsAt"])
    return windows, refused


def when(timestamp: float) -> str:
    return datetime.datetime.fromtimestamp(timestamp).strftime("%a %F %H:%M")


def wait(args: argparse.Namespace) -> None:
    windows, refused = limits(read_stream(args.probe))
    now = time.time()
    waits = []
    if refused and refused[1] > now:
        waits.append((refused[1], f"the {NAMES.get(refused[0], refused[0])} limit is reached"))
    use, reset = windows.get("five_hour", (None, None))
    if use is not None and reset and reset > now and use * 100 >= args.start:
        waits.append((reset, f"the 5-hour limit is at {use:.0%} (a round starts below {args.start:g}%)"))
    if not waits:
        print("0 go")
        return
    reset, reason = max(waits)
    # A minute's margin, so the next check sees the window already reset.
    print(f"{int(reset - now) + 60} {reason}; waiting until it resets on {when(reset)}")


def checked(args: argparse.Namespace) -> None:
    print(len(todo()), len(hadiths()))


def work(events: list[dict]) -> str:
    """What a round did, to compare rounds at another effort: the fixes by reason and the misprints
    of the hadith it wrote to the inbox (as kept in content/matn/), and the zooms it read. Every word
    a round changes or gives marks to should be read on a zoom (docs/matn.md)."""
    ids, zooms = set(), set()
    for event in events:
        if event.get("type") != "assistant":
            continue
        for c in (event.get("message") or {}).get("content") or []:
            if c.get("type") != "tool_use":
                continue
            path = str((c.get("input") or {}).get("file_path", ""))
            if c.get("name") == "Read" and "pages/zoom-" in path:
                zooms.add(path)
            elif c.get("name") == "Write" and path.endswith("content/matn/inbox.json"):
                try:
                    ids |= set(json.loads(c["input"].get("content", "")))
                except (ValueError, TypeError):
                    pass
    kept = {i: d for f in CHECKED.glob("[0-9][0-9].json") for i, d in json.loads(f.read_text(encoding="utf-8")).items()}
    decided = [kept[i] for i in ids if i in kept]
    why = Counter(f[2] for d in decided for f in d.get("fix", []))
    misprints = sum(len(d.get("misprint", [])) for d in decided)
    return (f"fixes: {why['v1']} v1, {why['variant']} variant, {why['marks']} marks · misprints: {misprints}"
            f" · zooms read: {len(zooms)}")


def report(args: argparse.Namespace) -> None:
    events = read_stream(args.round)
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    if result is None:
        print(f"the round ended without a result; its output is in {args.round}")
    else:
        print(f"session {result.get('session_id')} · {result.get('num_turns')} turns"
              f" · {result.get('duration_ms', 0) / 60000:.0f} min"
              f" · ≈ ${result.get('total_cost_usd', 0):.2f} at API prices"
              + (" · ended with an error" if result.get("is_error") else ""))

    before, _ = limits(read_stream(args.probe))
    after, _ = limits(events)
    used = []
    for name, label in NAMES.items():
        if name not in after:
            continue
        use, reset = after[name]
        old, old_reset = before.get(name, (None, None))
        if old is not None and old_reset == reset:
            used.append(f"{label} {old:.0%} → {use:.0%} (+{(use - old) * 100:.0f})")
        else:
            used.append(f"{label} {use:.0%}")
    if used:
        print("limits: " + " · ".join(used))

    left = int(pathlib.Path(args.checked_before).read_text(encoding="utf-8").split()[0])
    print(f"left to check: {left} → {len(todo())}; checked in all: {len(checked_ids())} of {len(hadiths())}")
    print(work(events))

    if result is not None:
        print(result.get("result", ""))


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    w = commands.add_parser("wait")
    w.add_argument("probe")
    w.add_argument("start", type=float)
    commands.add_parser("checked")
    r = commands.add_parser("report")
    r.add_argument("round")
    r.add_argument("probe")
    r.add_argument("checked_before")
    args = parser.parse_args()
    {"wait": wait, "checked": checked, "report": report}[args.command](args)


if __name__ == "__main__":
    main()
