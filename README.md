# homelab-ha-blueprints

Home Assistant blueprints for products running in my homelab. Organized by integration / product — pick a directory below.

## What's here

- **[`mammotion/`](mammotion/)** — Blueprints for the [Mammotion-HA integration](https://github.com/mikey0000/Mammotion-HA). Tested on a Yuka Mini 2.
  - Notify on mow completion
  - Critical alert when the mower is stranded
  - Alert when the mower is lifted mid-mow

More products will land here over time. Each subdirectory has its own README with per-blueprint details, inputs, and one-click "Import to HA" badges.

## How to import a blueprint

Two options:

1. **Use the badge** in the per-product README — opens the blueprint import flow directly in your Home Assistant instance.
2. **Manual**: in HA go to *Settings → Automations & Scenes → Blueprints → Import Blueprint*, then paste the raw URL of any `.yaml` file in this repo.

## Conventions

- Blueprints take a primary entity (e.g. `lawn_mower.your_mower`) and derive related entity IDs from the slug. This works as long as you haven't renamed the auto-generated entity IDs of the integration.
- Critical-alert payloads (iOS-specific) are gated behind a boolean input so the blueprint is usable with non-iOS notifiers.
- Defaults match what works on the hardware I've tested. Tweak the inputs to fit your setup.

## License

MIT. See [`LICENSE`](LICENSE).
