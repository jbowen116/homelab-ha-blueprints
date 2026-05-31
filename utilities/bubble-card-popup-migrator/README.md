# Bubble Card pop-up migrator

A small Python script that converts [Bubble Card](https://github.com/Clooos/Bubble-Card) pop-ups from the pre-v3.2.0 `vertical-stack` wrapper format to the new standalone format introduced in v3.2.0.

## When you actually need this

The Bubble Card editor has a per-pop-up **"Migrate to standalone"** button. **Use that when you can** — it's purpose-built and lower-risk.

This script exists for the case where the editor button isn't practical:

- You inherited a dashboard (YouTube tutorial, friend's config, online template) with dozens of bubble-card pop-ups buried inside other cards, and the migration prompt nags every time you open the dashboard.
- The pop-ups are tucked inside cards you can't easily reach in the UI, so finding each one to click its migration button is a slog.
- You're editing in YAML mode and the editor migration button isn't available there.
- You want to script the migration as part of a config-management workflow.

If you only have a handful of pop-ups and they're easy to find in the editor, this script is overkill.

## What it does

For every pop-up wrapped in the old format::

```yaml
type: vertical-stack
cards:
  - type: custom:bubble-card
    card_type: pop-up
    hash: "#foo"
    sub_button: []
    # ... other pop-up fields ...
  - <content card 1>
  - <content card 2>
```

it rewrites to the new standalone shape::

```yaml
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
```

Specifically:

- The `vertical-stack` wrapper is removed; the bubble-card pop-up becomes the top-level card in its place.
- The pop-up's existing configuration (name, icon, `button_type`, `show_header`, `auto_close`, `margin`, `close_on_click`, `card_layout`, etc.) is preserved verbatim.
- `sub_button: []` (old list form) is converted to `sub_button: {main: [], bottom: []}` (new dict form). If `sub_button` already contains entries, they're moved into `main`; `bottom` defaults to empty.
- The content cards that were siblings of the pop-up header (i.e. `cards[1:]` of the old `vertical-stack`) become the new pop-up's own `cards:` array.
- Anything that doesn't match the old pop-up wrapper pattern is left untouched.

## Where the dashboard files live

Home Assistant stores Lovelace dashboards as JSON under `<config>/.storage/`:

- The default dashboard: `<config>/.storage/lovelace`
- Additional dashboards: `<config>/.storage/lovelace.<dashboard_id>`

Pass the file paths directly to the script.

## Usage

Three modes, mutually exclusive:

### `--list` — discover what would be migrated, change nothing

```sh
./migrate.py --list \
    /path/to/.storage/lovelace.dashboard_main \
    /path/to/.storage/lovelace.dashboard_extra
```

Prints each pop-up's hash, name, content-card count, and child types. Useful when you're not sure how many pop-ups need migration or where they live.

### `--dry-run` — write the transformed output to a sibling file

```sh
./migrate.py --dry-run /path/to/.storage/lovelace.dashboard_main
```

Writes `<input>.migrated` next to each input. Diff the two with your editor (or `diff -u`) to eyeball the transformation before committing to `--apply`.

### `--apply` — overwrite the input files in place

**Read the safety steps below first.**

```sh
./migrate.py --apply /path/to/.storage/lovelace.dashboard_main
```

## Safety procedure for `--apply`

`--apply` overwrites the dashboard storage files. The procedure that worked cleanly in testing:

1. **Take a Home Assistant backup**: Settings → System → Backups → "Create backup" (include the configuration). This gives you a one-click rollback if the migration leaves the dashboard in an unusable state.
2. **Optionally, also copy the dashboard files aside manually**: `cp .storage/lovelace.<id> /tmp/` for each file you're about to touch. Belt-and-suspenders backup separate from HA's own backup mechanism.
3. **Stop Home Assistant** so it doesn't overwrite the storage files while the script is rewriting them. Easiest way: call the `homeassistant.stop` service via the API or developer tools. With Docker `restart: unless-stopped`, the container will respawn HA automatically a moment later.

   ```sh
   curl -X POST -H "Authorization: Bearer $HA_TOKEN" \
        http://localhost:8123/api/services/homeassistant/stop \
        -H "Content-Type: application/json" -d '{}'
   ```

4. **Run the script** in `--apply` mode while HA is down. JSON parse failures abort with a non-zero exit code; only valid output is written.
5. **Verify** by waiting for HA to come back, then loading the affected dashboards. Buttons should open pop-ups normally; the v3.2.0 migration prompt should be gone.
6. **Rollback**, if something looks wrong: stop HA again, restore the backed-up files into `.storage/`, let HA restart.

## What this script does NOT do

- It does not understand pop-up patterns outside the `vertical-stack` wrapper idiom. If your dashboard puts a bubble-card pop-up inside some other layout (e.g. a `grid` for HA's section view), the script leaves it alone. That's intentional — those are typically already standalone or close enough that the editor's per-pop-up button is the right tool.
- It does not migrate other Bubble Card v3.2.0+ schema changes outside of pop-ups (e.g. button card revisions). Only the pop-up-in-vertical-stack pattern is in scope.
- It does not validate the transformed config against the current Bubble Card schema. Bubble Card's own parser will surface errors if anything's off; spot-check the migrated dashboard after running.

## Verified against

- Bubble Card v3.2.2
- Home Assistant Core 2026.5
- Storage-mode dashboards (the `.storage/lovelace.*` files)

YAML-mode dashboards (where the config lives in a `.yaml` file referenced from `configuration.yaml`) would need similar transformations applied with a YAML round-trip instead of JSON; not currently supported.

## Sample run

A real run on a 19-pop-up dashboard borrowed from a YouTube tutorial:

```
$ ./migrate.py --list /config/.storage/lovelace.dashboard_hadashboard
=== lovelace.dashboard_hadashboard: 13 pop-up(s) to migrate ===
  #shopping     Shopping Cart       children= 1  ['todo-list']
  #cameras      Road Conditions     children= 4  ['picture-entity', ...]
  #3dprinter    Creality K1C        children= 4  ['custom:button-card', ...]
  ...
Total: 13 pop-up(s) identified.
```

After `--apply` + HA restart, the v3.2.0 nag was gone and every pop-up's contents (todo list, camera tiles, calendar card, gauge, history graph, etc.) opened correctly from its launcher tile.
