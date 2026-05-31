#!/usr/bin/env python3
"""Migrate Bubble Card pop-ups from the pre-v3.2.0 vertical-stack format to standalone.

Bubble Card v3.2.0 introduced a new "standalone" pop-up format. Pop-ups
defined in the older idiom — a ``vertical-stack`` wrapper where ``cards[0]``
is the bubble-card pop-up header and ``cards[1..]`` are its contents — must
be converted to the new shape, where the pop-up is itself the top-level
card and its content cards live in the pop-up's own ``cards:`` field.

The Bubble Card editor has a per-pop-up "Migrate to standalone" button.
Use that when you can. This script exists for the case where you can't
easily find or edit the pop-ups individually — e.g. a borrowed dashboard
with dozens of pop-ups nested inside other cards, or YAML-only editing
without UI access to the bubble-card editor.

Transformation per pop-up::

    # BEFORE
    type: vertical-stack
    cards:
      - type: custom:bubble-card
        card_type: pop-up
        hash: "#foo"
        sub_button: []
        # ... other pop-up fields ...
      - <content card 1>
      - <content card 2>

    # AFTER
    type: custom:bubble-card
    card_type: pop-up
    hash: "#foo"
    sub_button:
      main: []
      bottom: []
    # ... other pop-up fields preserved ...
    cards:
      - <content card 1>
      - <content card 2>

Usage::

    # Discover pop-ups that need migration (no changes made)
    ./migrate.py --list   path/to/lovelace.dashboard_main [more...]

    # Generate a transformed copy alongside the input (no in-place changes)
    ./migrate.py --dry-run  path/to/lovelace.dashboard_main [more...]

    # Overwrite the input files in place (BACK UP FIRST, STOP HA FIRST)
    ./migrate.py --apply  path/to/lovelace.dashboard_main [more...]

Safety: ``--apply`` overwrites the input files. Before using it:

1. Take a Home Assistant backup via Settings → System → Backups.
2. Stop Home Assistant so it does not overwrite the storage during the
   rewrite (e.g. call the ``homeassistant.stop`` service via the API,
   or stop the ``homeassistant`` container).
3. Run ``--dry-run`` first and eyeball the transformed file at
   ``<input>.migrated`` next to each input.

Tested against Bubble Card v3.2.2 storage-mode dashboards
(``.storage/lovelace.<id>``). Storage files are JSON; the script reads
and writes pretty-printed JSON with four-space indent.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def is_old_popup_wrapper(item: object) -> bool:
    """Return True if `item` is a vertical-stack whose first child is a bubble-card pop-up."""
    if not isinstance(item, dict):
        return False
    if item.get("type") != "vertical-stack":
        return False
    cards = item.get("cards") or []
    if not cards:
        return False
    first = cards[0]
    if not isinstance(first, dict):
        return False
    return first.get("type") == "custom:bubble-card" and first.get("card_type") == "pop-up"


def migrate_sub_button(value: object) -> object:
    """Convert ``sub_button`` from the old list shape to the new ``{main, bottom}`` shape."""
    if isinstance(value, list):
        return {"main": value, "bottom": []}
    return value


def unwrap_popup(vstack: dict) -> dict:
    """Build the standalone bubble-card pop-up from an old vertical-stack wrapper."""
    cards = vstack["cards"]
    popup_header = cards[0]
    contents = cards[1:]

    new_popup = dict(popup_header)
    if "sub_button" in new_popup:
        new_popup["sub_button"] = migrate_sub_button(new_popup["sub_button"])
    new_popup["cards"] = contents
    return new_popup


def transform(node: object, found: list[dict]) -> object:
    """Recursive in-place transform of card lists inside the dashboard tree."""
    if isinstance(node, dict):
        for key, val in list(node.items()):
            if isinstance(val, list):
                node[key] = _transform_list(val, found)
            elif isinstance(val, dict):
                transform(val, found)
    return node


def _transform_list(items: list, found: list[dict]) -> list:
    """Walk a list, replacing old pop-up wrappers with the new standalone form."""
    new_items: list = []
    for item in items:
        if is_old_popup_wrapper(item):
            popup_card = item["cards"][0]
            found.append(
                {
                    "hash": popup_card.get("hash", "(no hash)"),
                    "name": popup_card.get("name", "(no name)"),
                    "n_children": len(item["cards"]) - 1,
                    "child_types": [
                        c.get("type", "-") for c in item["cards"][1:] if isinstance(c, dict)
                    ],
                }
            )
            new_items.append(unwrap_popup(item))
        elif isinstance(item, dict):
            transform(item, found)
            new_items.append(item)
        else:
            new_items.append(item)
    return new_items


def process(path: pathlib.Path, mode: str) -> int:
    """Process one dashboard file. Returns the number of pop-ups found/migrated."""
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR reading {path}: {exc}", file=sys.stderr)
        return -1

    config = data["data"].get("config", data["data"]) if isinstance(data.get("data"), dict) else data

    found: list[dict] = []
    transform(config, found)

    print(f"=== {path.name}: {len(found)} pop-up(s) to migrate ===")
    for f in found:
        print(
            f"  {f['hash']:30s} {f['name']!s:25s} children={f['n_children']:>2}  {f['child_types']}"
        )

    if not found:
        return 0

    if mode == "apply":
        path.write_text(json.dumps(data, indent=4))
        print(f"  wrote {path}")
    elif mode == "dry-run":
        out_path = path.with_suffix(path.suffix + ".migrated")
        out_path.write_text(json.dumps(data, indent=4))
        print(f"  dry-run output: {out_path}")
    # list mode: print only, no output file

    return len(found)


def main(argv: list[str] | None = None) -> int:
    """Parse args and process each dashboard file under the requested mode."""
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n", maxsplit=1)[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_const", const="list", dest="mode",
                      help="show which pop-ups need migration; make no changes")
    mode.add_argument("--dry-run", action="store_const", const="dry-run", dest="mode",
                      help="write transformed output to <input>.migrated alongside each input")
    mode.add_argument("--apply", action="store_const", const="apply", dest="mode",
                      help="overwrite input files in place (BACK UP and STOP HA FIRST)")
    parser.add_argument("paths", nargs="+", type=pathlib.Path,
                        help="dashboard storage files (e.g. /config/.storage/lovelace.<id>)")
    args = parser.parse_args(argv)

    total = 0
    for path in args.paths:
        n = process(path, args.mode)
        if n < 0:
            return 2
        total += n
        print()
    print(f"Total: {total} pop-up(s) {'migrated' if args.mode == 'apply' else 'identified'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
