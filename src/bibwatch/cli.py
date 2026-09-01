"""bibwatch CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bibwatch import __version__
from bibwatch.doctor import run_doctor
from bibwatch.init_data import init_data_root
from bibwatch.paths import resolve_data_root
from bibwatch.run import poll_new_papers, run_all
from bibwatch.watch import list_watch_files, load_watch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bibwatch", description="Research literature watch → RSS")
    parser.add_argument("--version", action="version", version=f"bibwatch {__version__}")
    parser.add_argument("--data", type=Path, default=None, help="bibwatch-data root (or BIBWATCH_DATA / cwd)")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create bibwatch-data directory layout")

    p_watch = sub.add_parser("watch", help="List watch definitions")
    p_watch.add_argument("action", choices=["list"], nargs="?", default="list")

    p_poll = sub.add_parser("poll", help="Fetch feeds and show new papers (no ingest)")
    p_poll.add_argument("--watch", default=None, help="Single watch id")
    p_poll.add_argument("--dry-run", action="store_true")

    p_run = sub.add_parser("run", help="poll + ingest + publish RSS")
    p_run.add_argument("--watch", default=None)
    p_run.add_argument("--dry-run", action="store_true")
    p_run.add_argument("--max-items", type=int, default=200)
    p_run.add_argument(
        "--site-base",
        default=None,
        help="GitHub Pages base URL, e.g. https://user.github.io/bibwatch-data",
    )

    sub.add_parser("doctor", help="Validate data dir and RSS output")

    args = parser.parse_args(argv)
    data = resolve_data_root(args.data)

    try:
        if args.command == "init":
            path = init_data_root(data)
            print(path)
            return 0

        if args.command == "watch":
            files = list_watch_files(data)
            if not files:
                print("No watches", file=sys.stderr)
                return 1
            for f in files:
                w = load_watch(f)
                status = "on" if w.enabled else "off"
                print(f"{w.id}\t{status}\t{w.title}")
            return 0

        if args.command == "poll":
            papers, errors = poll_new_papers(data, watch_id=args.watch, dry_run=True)
            for p in papers:
                print(f"{p.id}\t{p.title[:80]}")
            for err in errors:
                print(f"error: {err}", file=sys.stderr)
            print(f"{len(papers)} new", file=sys.stderr)
            return 0 if not errors else 1

        if args.command == "run":
            result = run_all(
                data,
                watch_id=args.watch,
                dry_run=args.dry_run,
                max_items=args.max_items,
                site_base=args.site_base,
            )
            for err in result.errors:
                print(f"error: {err}", file=sys.stderr)
            if result.feed_path:
                print(f"feed: {result.feed_path}")
            print(f"new: {result.new_count}, total: {result.total_in_feed}")
            return 0 if not result.errors else 1

        if args.command == "doctor":
            issues = run_doctor(data)
            if issues:
                for i in issues:
                    print(f"issue: {i}", file=sys.stderr)
                return 1
            print("ok")
            return 0

    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
