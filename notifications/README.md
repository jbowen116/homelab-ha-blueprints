# Notification blueprints

Integration-agnostic blueprints for actionable notifications via the Home Assistant Companion App.

## Blueprints

### `appliance_finished.yaml` — Appliance finished, with focus + actions

Notifies you when an appliance finishes (a binary sensor transitions `on` → `off`) with smart home / away / focus-mode branching and actionable buttons.

**Behavior:**

- **Home, focus mode on**: waits until focus clears, then notifies.
- **Home, focus off or no focus sensor**: notifies immediately.
- **Away**: notifies immediately with an "away" copy + a "remind when home" button.

**Notification actions:** Acknowledge / Remind in 30 min / Remind in 1 h / Remind when home. The "remind when home" reminder only fires once the person is actually home **and** focus is off (or not configured).

**Inputs:** running binary_sensor, person entity, notify service, optional focus binary_sensor, customizable home/away titles + messages, customizable action IDs (override these if you stamp the blueprint out for multiple appliances so each has unique action IDs).

[![Open in HA](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fjbowen116%2Fhomelab-ha-blueprints%2Fblob%2Fmain%2Fnotifications%2Fappliance_finished.yaml)

## Notes

- **iOS Focus integration**: the Home Assistant Companion App can expose iOS Focus modes as binary sensors. On Android, you can use an `input_boolean` you toggle manually as the focus sensor.
- **Unique action IDs**: HA's notification actions are global. If you instance this blueprint for both your washer and dryer, override the action IDs per instance (e.g. `ACK_WASHER` and `ACK_DRYER`) — otherwise tapping "Acknowledge" on one notification triggers handlers for the other appliance too.
- **`mode: parallel, max: 10`**: lets multiple appliances finish simultaneously (e.g. washer + dryer both done) without blocking each other.
