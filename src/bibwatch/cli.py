"""bibwatch CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bibwatch import __version__
from bibwatch.doctor import run_doctor
from bibwatch.init_data import init_data_root
from bibwatch.paths import resolve_data_root
from bibwatch.run import poll_new_papers, publish_all_feeds, run_all
from bibwatch.translate import (
    apply_abstract_translation,
    apply_translations_file,
    papers_needing_translation,
    pending_payload,
)
from bibwatch.watch import list_watch_files, load_watch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bibwatch", description="Research literature watch → RSS")
    parser.add_argument("--version", action="version", version=f"bibwatch {__version__}")
    parser.add_argument("--data", type=Path, default=None, help="bibwatch-data root (or BIBWATCH_DATA / cwd)")
    parser.add_argument(
        "--feed-root",
        type=Path,
        default=None,
        help="Public bibwatch-feed checkout (or BIBWATCH_FEED). Writes docs/feeds/<token>/*.xml there.",
    )

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
    p_run.add_argument("--max-items", type=int, default=None, help="Override max items for every named feed")
    p_run.add_argument(
        "--site-base",
        default=None,
        help="GitHub Pages base URL, e.g. https://user.github.io/bibwatch-feed",
    )

    p_tr = sub.add_parser("translate", help="List or apply Japanese abstract translations (agent, not DeepL)")
    tr_sub = p_tr.add_subparsers(dest="translate_cmd", required=True)
    p_tr_list = tr_sub.add_parser("list", help="Papers whose abstracts still need a Japanese translation")
    p_tr_list.add_argument("--all", action="store_true", help="Include papers not currently in a named feed")
    p_tr_list.add_argument("--json", action="store_true", help="JSON objects (id, title, journal, abstract)")
    p_tr_set = tr_sub.add_parser("set", help="Set one paper's Japanese abstract (read from --ja-file or stdin)")
    p_tr_set.add_argument("paper_id")
    p_tr_set.add_argument("--ja-file", type=Path, default=None)
    p_tr_apply = tr_sub.add_parser("apply", help="Apply a YAML file of translations")
    p_tr_apply.add_argument("file", type=Path)

    p_pub = sub.add_parser("publish", help="Rebuild RSS from stored papers (no poll)")
    p_pub.add_argument("--max-items", type=int, default=None)
    p_pub.add_argument("--site-base", default=None)

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
                feed_root=args.feed_root,
            )
            for err in result.errors:
                print(f"error: {err}", file=sys.stderr)
            for path in result.feed_paths or ([result.feed_path] if result.feed_path else []):
                print(f"feed: {path}")
            print(f"new: {result.new_count}, total: {result.total_in_feed}")
            return 0 if not result.errors else 1

        if args.command == "translate":
            if args.translate_cmd == "list":
                pending = papers_needing_translation(data, in_feeds=not args.all)
                if args.json:
                    import json

                    json.dump([pending_payload(p) for p in pending], sys.stdout, ensure_ascii=False, indent=2)
                    sys.stdout.write("\n")
                else:
                    for p in pending:
                        print(f"{p.id}\t{(p.title or '')[:80]}")
                    print(f"{len(pending)} pending", file=sys.stderr)
                return 0
            if args.translate_cmd == "set":
                ja = args.ja_file.read_text(encoding="utf-8") if args.ja_file else sys.stdin.read()
                paper = apply_abstract_translation(data, args.paper_id, ja)
                print(paper.id)
                return 0
            if args.translate_cmd == "apply":
                applied = apply_translations_file(data, args.file)
                for paper_id in applied:
                    print(paper_id)
                print(f"{len(applied)} applied", file=sys.stderr)
                return 0

        if args.command == "publish":
            feed_path, feed_paths = publish_all_feeds(
                data,
                max_items=args.max_items,
                site_base=args.site_base,
                feed_root=args.feed_root,
            )
            for path in feed_paths or ([feed_path] if feed_path else []):
                print(f"feed: {path}")
            return 0

        if args.command == "doctor":
            issues = run_doctor(data, feed_root=args.feed_root)
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
