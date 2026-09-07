# CrowdLaunch

CrowdLaunch is an open launch-risk dashboard and manifest for tracking launch evidence and collecting probability forecasts from the crowd.

The public project separates **observable evidence and crowd forecasts** from any future proprietary underwriting calibration or insurance pricing model.

## What is public

- launches and launch attempts
- scheduled opportunities, scrubs and aborts when documented
- vehicle/platform/component architecture
- booster/stage heritage and reuse observations
- failure/anomaly events and source-backed root causes
- FAA range, airspace, mishap and corrective-action observations
- source provenance and confidence
- crowd forecasts and forecast scoring (planned)

## What is not intended to be public

Future proprietary insurance pricing and portfolio logic should remain outside this repository, including calibrated loss probabilities, severity distributions, dependency/correlation assumptions, capital loads, insurer-specific terms and technical pricing.

The current `underwriting_snapshot` table is only a schema placeholder and contains no calibrated underwriting model.

## Repository layout

- `data/launch_architecture_underwriting.sqlite.gz` — compressed normalized public evidence database
- `schema/schema.sql` — SQLite schema for inspection/rebuilds
- `scripts/export_public_data.py` — exports public database tables to JSON for a static website
- `site/index.html` — GitHub Pages-ready starter dashboard
- `site/data/` — generated JSON output (created by the export script)

## Data principles

1. Unknown values remain `NULL`; they are not guessed.
2. Schedule retargets are not classified as failures unless a source states a cause.
3. Root-cause links and failure-causality edges require explicit evidence.
4. Operational GO probability is kept separate from conditional mission success.
5. Every material observation should retain provenance and confidence.

## Crowd forecasting model

CrowdLaunch is designed to collect separate forecasts for questions such as:

- `P(launch in current window)`
- `P(vehicle clears launch phase | launch)`
- `P(payload reaches intended deployment/insertion | launch)`
- `P(recovery success | recovery attempted)`
- `P(primary mission objective achieved | launch)`

Forecasts can later be scored with proper scoring rules such as the Brier score and aggregated into equal-weight and skill-weighted crowd estimates.

## Status

Early public prototype. The historical source census is not yet fully materialized and the underwriting model is not calibrated for insurance quoting.
