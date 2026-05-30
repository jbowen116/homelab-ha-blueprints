# Zooz blueprints

Home Assistant blueprints for [Zooz](https://www.getzooz.com/) Z-Wave devices. Requires the `zwave_js` integration.

## Blueprints

### `zen32_button_group.yaml` — ZEN32 button + LED group logic

Universal button binding for the **Zooz ZEN32** scene controller. Pick a button (1–5) and a group of light/switch entities; this blueprint handles:

- **Short press** → toggle the group (any-on → all off; else all on).
- **Long press** → force all entities on.
- **Button LED** reflects collective state:
  - White = all on
  - Yellow = some on
  - Off = all off

Parameter mappings for LED mode / colour / brightness are derived from the button number you select, so you can stamp this blueprint out 5 times (one per button) on the same device with different target groups.

The blueprint waits 500 ms after firing actions before reading the new collective state — gives the Z-Wave devices time to report back so the LED reflects the actual post-action state.

**Inputs**: ZEN32 device, button number (1–5), target entities (light/switch, multiple).

[![Open in HA](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fjbowen116%2Fhomelab-ha-blueprints%2Fblob%2Fmain%2Fzooz%2Fzen32_button_group.yaml)

## Notes

- Only handles on/off state. Brightness, colour, and other dim-level state are ignored — group is "on" if `is_state(entity, 'on')` is true.
- The device selector restricts to `zwave_js` integration. Other Z-Wave drivers (deprecated `zwave` legacy, OpenZWave) are not supported by this blueprint.
- Tested on Home Assistant 2026.5.4 with Z-Wave JS UI.
