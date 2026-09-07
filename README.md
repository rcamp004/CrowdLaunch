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

## Crowd forecasting (v1)

The responsive dashboard now accepts a GO/NO-GO call, a 0–100% liftoff probability,
reasoning and an optional HTTPS evidence link. Payload-loss estimates are optional:
contributors who only judge launch readiness do not silently acquire assumed loss values.

**Shared persistence:** the form prepares a public GitHub issue. The contributor signs
in to GitHub and submits it there. This website contains no GitHub token and never
claims that preparing a link has saved a forecast. Each account's latest valid forecast
per question gets equal weight. Multiple accounts can still represent the same person;
these are self-selected opinions, not an independent expert panel.

The `Refresh crowd forecasts` workflow reads all issues, validates their contents and
writes `site/data/crowd.json` back to the default branch. It runs on issue changes,
hourly and manually. Issues and Actions must be enabled; Actions needs permission to
push that file. A protected branch may require a separate write arrangement. This
workflow does not deploy a website or alter DNS. The UI refreshes the shared snapshot
from GitHub and falls back explicitly to its bundled snapshot when unavailable.
If the default branch changes, update `BRANCH` in `site/app.js`.

### Fixed questions and cutoffs

Maintain questions in `config/questions.json`. Every question has an immutable ID,
opening/closing timestamps, a precise UTC launch interval and a physical-loss definition.
The starter question is USSF-153 on 10 September 2026, based on the existing manifest;
its date has not been independently reverified by this implementation. Forecasts close
at the beginning of that UTC day. Do not silently move the interval: create a new ID
for a retargeted launch. Retain old questions for the existing forecast archive.

To revise a forecast, submit a new issue before the cutoff. GitHub supplies account
identity and update time; values in the JSON cannot impersonate another contributor
or backdate a submission. Already observed pre-cutoff versions are retained if an
issue changes after closing. An issue first collected after a late edit is rejected;
the collector cannot recover unseen earlier versions. This is an MVP snapshot log,
not a complete immutable event ledger. Git history preserves collected snapshots.
Maintainers can label an issue `crowd-exclude` to remove it from aggregation. Deleting
an issue withdraws it on refresh; closing it alone does not withdraw it. Previously
public issues and repository snapshots may remain accessible in history.

### Loss illustration and scoring

All inputs are percentages. For each loss contributor, using fractions:

- conditional expected physical payload loss = `p_total_loss + p_partial_loss * partial_severity`
- interval expected loss = `p_go * conditional expected physical payload loss`

We average individual results, not the products of crowd-average inputs. Report both
GO contributors and loss contributors separately. Total and partial physical loss
are mutually exclusive. Remaining probability is no physical payload loss.
A scrub means no physical launch loss in that interval, not no risk for a rescheduled
mission. This excludes booster recovery, post-deployment operations and insurance
policy interpretation. The dollar illustration scales the conditional loss fraction
by a user-entered payload value. It is uncalibrated and excludes deductibles, terms,
capital, expenses, profit and insurance pricing calibration.

To score a resolved launch question, replace `resolution: null` with
`{"go": 1, "source_url": "https://official-source.example/outcome"}` (or `go: 0`
for no liftoff in the interval), using a real supporting source, then refresh the
snapshot. Brier scoring is for liftoff only. Loss-outcome scoring and credibility
weighting require additional verified outcomes and are not implemented.

### Local build and checks

Python 3.12 and a static web server suffice; there are no package dependencies.

```sh
python scripts/export_public_data.py
python -m unittest discover -s tests -v
python scripts/crowd.py  # refresh from public GitHub issues; optional GITHUB_TOKEN
python -m http.server 8000 --directory site
```

The exporter accepts the committed `.sqlite.gz` directly, uses explicit public
columns, and rejects a missing database rather than creating an empty one. For an
uncompressed database, pass `--db path/to/file.sqlite`; it is opened read-only.
Deploy only `site/` when hosting is configured. Keep future proprietary underwriting
values in a separate private database, never in the public compressed evidence file.

### Featured launch interface

The home page combines a cinematic featured-launch banner, selected mission details,
a forecast-deadline countdown, data-derived summary counts, upcoming opportunity
cards, the working forecast form, crowd distribution, and a searchable evidence
archive. It responds to phone and desktop widths. No sample forecasts, live flight
telemetry or invented success statistics are displayed.

`site/assets/launch-hero.png` is AI-generated illustrative artwork, not a photograph
of the featured mission. It was generated as an unbranded coastal rocket launch at
dusk, with dark negative space for the headline. The page labels this explicitly.

To add verified footage, set `question_id` and `video_url` in
`site/data/featured.json`. Supported URLs are HTTPS YouTube watch URLs or youtu.be
links with an 11-character video ID. The matching selected question gets a
click-to-load privacy-enhanced YouTube embed. The player has no autoplay, unloads
when closed, and is hidden for other questions. Until footage is linked, the hero
links to the launch source for coverage. An embed does not imply a live mission.
