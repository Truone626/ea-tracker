# Elite Academy League Tracker

Standings, schedules, results and results-based rankings for every Elite Academy League club (EA, EA National, EA2, U11–U19).

Independent project. Not affiliated with or endorsed by the Elite Academy League or Modular11.

## How it updates

`.github/workflows/update.yml` runs twice a day (about 5 AM and 8 PM Pacific). To refresh right away: **Actions** tab → **Update tracker** → **Run workflow**.

Each run:
1. pulls the public schedule and standings from Modular11 (`scripts/pull.mjs`),
2. downloads any new club crests into `crests/` (clubs without one show initials),
3. builds the site (`build.py` + `template.html`) and checks every official table line against the match results; mismatches appear on the site's Data notes page,
4. saves the data to `data/latest.json`, the day's national rankings to `data/history/` (used for weekly movement), and publishes the site to GitHub Pages.

If a run fails (Modular11 down, page layout changed, match count suddenly drops more than 10%), the site keeps showing the last good data and GitHub emails the repository owner.

## New season

Update `SEASON` in `scripts/pull.mjs` (event id and dates) and the `season` label in `build.py`.
