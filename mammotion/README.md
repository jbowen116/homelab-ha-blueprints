# Mammotion blueprints

Home Assistant blueprints for the [Mammotion-HA integration](https://github.com/mikey0000/Mammotion-HA).

Built and tested against a **Mammotion Yuka Mini 2**. Should work for other models that expose the same set of entities through Mammotion-HA, but treat that as untested.

## Blueprints

### `mow_complete.yaml` — Notify when the mower finishes

Sends a notification when the mower returns to the dock **for real** — i.e. not a brief mid-mow recharge stop. Uses a debounce (default 2 min) because mid-mow low-battery returns transition through `paused`, not `docked`, so this only fires for true completion.

**Inputs**: mower entity, notify service, debounce duration.

[![Open in HA](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fjbowen116%2Fhomelab-ha-blueprints%2Fblob%2Fmain%2Fmammotion%2Fmow_complete.yaml)

### `stranded_alert.yaml` — Alert when the mower is stranded

Critical alert (iOS-aware) when the mower is stuck. Fires in either of two cases:

1. **Hard error codes** — defaults cover the known Yuka Mini 2 "stuck" cases (`1010`, `1017`, `1100`, `1203`, `1008`). Fires immediately.
2. **Off-dock idle** — mower has been off-dock and idle for a sustained duration (default 15 min), battery is below threshold (default 95 %), and the user is not actively driving from the app.

The off-dock-idle path requires the **`binary_sensor.{mower}_app_interactive`** entity from Mammotion-HA — added in [Mammotion-HA#767](https://github.com/mikey0000/Mammotion-HA/pull/767). Without that sensor the blueprint will not fire the off-dock-idle path (the condition will always be false), but the error-code path still works.

**Inputs**: mower entity, notify service, battery threshold, off-dock-idle duration, error code list, iOS critical-alert toggle.

[![Open in HA](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fjbowen116%2Fhomelab-ha-blueprints%2Fblob%2Fmain%2Fmammotion%2Fstranded_alert.yaml)

### `lift_during_mow.yaml` — Alert when the mower is lifted mid-mow

Fires when the lift sensor (error `2801` on Yuka Mini 2) trips while the mower is in the `mowing` state. Does **not** fire when you lift the mower on its dock for maintenance.

**Inputs**: mower entity, notify service, lift error code.

[![Open in HA](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fjbowen116%2Fhomelab-ha-blueprints%2Fblob%2Fmain%2Fmammotion%2Flift_during_mow.yaml)

## How the blueprints derive entity names

All three blueprints take a single `lawn_mower` entity as the primary input and derive the related entity IDs from its slug. For example, if you pick `lawn_mower.robie`, the blueprint will look up `sensor.robie_battery`, `binary_sensor.robie_charging`, etc.

This works because Mammotion-HA names entities with a consistent `{device_name}_{key}` pattern. If you rename any of the auto-generated entity IDs in HA, the templates won't find them.

## Notes

- Tested on Home Assistant 2026.5.4 with Mammotion-HA 0.5.48-beta12 and PyMammotion 0.7.126.
- The error code defaults in `stranded_alert.yaml` were derived from on-device traces and the integration's error dictionary; the `1010`/`1017`/`1100`/`1203`/`1008` set is what's been useful in practice on a Yuka Mini 2. Other models may have different error semantics — adjust the input.
- The iOS critical-alert payload (`push.sound.critical: 1`) is iOS-specific. Turn it off in the blueprint inputs for non-iOS notify services.
