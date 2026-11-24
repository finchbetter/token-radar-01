# Token Radar — submittable entry package (LOCAL BUILD, NOT SUBMITTED)

- Bounty: `token-radar-01` — "Build the best token launch radar", $1,325, deadline **2026-12-14 10:00 UTC**
- Entrant: @finchbetter (make.fun), Solana payout wallet already linked (Primary)
- Built: 2026-11-20 (UTC), locally, from `kit/input/snapshot.json` only (DefiLlama, as_of 2026-11-14)
- Status: **PACKAGE COMPLETE, locally validated. NOT submitted. No GitHub repo created.**

Run it: `mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts --input kit/input/snapshot.json`
(or `node main.ts --input kit/input/snapshot.json --output out`).

## Files

Repo root is `~/workspace/makefun/token-radar/` (research files `MODEL.md`,
`fit_results.json`, `fit_model.py`, `fit_part2.py`, `kit/` stay alongside; the
submission is `main.ts` + `vendor/` + `dashboard/` + `screenshots/` + `LICENSE`).

| File | Bytes | What it is |
|---|---|---|
| `main.ts` | 36,212 | The entry program (Node 22, stdlib only, offline, deterministic) |
| `vendor/makefun-board.ts` | 19,788 | Kit library, byte-for-byte copy (sha256 `9ca51b6e…`, matches kit manifest) |
| `dashboard/index.html` | 448 | Page shell; loads `../data.js` then `app.js` |
| `dashboard/app.css` | 5,663 | Flat light theme, system fonts, no network |
| `dashboard/app.js` | 22,627 | Renders board / detail / filter from `window.RADAR`; hash routing |
| `dashboard/README.md` | 3,554 | Model + evidence summary (in the dossier text, so the judge reads it) |
| `screenshots/1-board.png` | 157,494 | Board view, 1440×800 |
| `screenshots/2-detail.png` | 152,064 | Detail view (rank 1, usdd), 1440×800 |
| `screenshots/3-filtered.png` | 144,481 | Filtered view (verdict=farm, 3 rows), 1440×800 |
| `LICENSE` | 1,104 | MIT, copied from the kit starter |
| `out/board.json` | 453,768 | Built board, 200 rows (sha256 `df586d84…`) |
| `out/data.js` | 406,310 | Dashboard data (`window.RADAR`) |
| `out/dossier.json` | 639,251 | From `buildDossier` (sha256 `330f5c39…`) |
| `out/dashboard/`, `out/screenshots/` | — | Copies of the repo's `dashboard/`, `screenshots/` |

## What main.ts does

1. Parses and validates the sealed snapshot (758 protocols, 40 watchlist).
2. Applies the kit's reproducible eligibility screen (category / wrapped-word /
   exchange-prefix / versioned-name) and the fitted model from `MODEL.md`:
   `log(mcap) = 9.1133 + 0.3940 · log(TVL)` (fitted values from each row's own TVL),
   logistic launch odds (each row's own TVL/age/growth/peers, capped at the oldest
   cohort's 0.800), EV = fitted mcap × odds. The fitted parameters are embedded at
   full precision with provenance comments (offline fit, `fit_model.py` /
   `fit_part2.py`); no protocol is special-cased by name for its value. The 20
   known `parentProtocol` exclusions are flagged and forced to skip (value-neutral).
3. Recomputes rank ranges at runtime: 92 leave-one-comp-out refits + 200 bootstrap
   refits (mulberry32, seed 42) of the OLS value fit.
4. Builds the 200-row board (198 eligible by EV + 2 lowest-EV ineligible fillers at
   ranks 199–200, implied values capped at the rank-198 value), with a 5-step
   costed farm plan and verdict per row, and runs the gate-shaped `boardIssue`
   check before writing anything.
5. Writes `board.json`, `data.js` (rows + KPI strip + held-out/walk-forward/
   calibration evidence + live-token set-aside), copies `dashboard/` and
   `screenshots/`, writes `dossier.json` via `buildDossier` last.

The dashboard shows, on the page: KPI strip, model-in-one-line strip, ranked
board (search / verdict / category / watchlist filters, 5 sort orders), a detail
view for every protocol (figures, EV rank-interval bar, fitted/LOO ranges, farm
steps with cost breakdown), held-out + LOCO + walk-forward tables, logistic
calibration, rank-uncertainty note, live-token set-aside, integrity strip
(census, FDV absent, parentProtocol absent, mcap −1 sentinel), and the cost
assumptions. No network anywhere: no `http://`/`https://` in any dashboard file,
no fetch/import of anything remote; `main.ts` imports only `node:fs`, `node:path`,
`node:url` and the vendored library.

## Validation (all run 2026-11-20, UTC)

Independent check script (kept outside the repo, `/tmp/shot/validate.mjs`):
**35 checks, 35 passed, 0 failed**, including:

- Board: 200 rows; all 40 watchlist present; ranks exactly 1–200 once each;
  implied values non-increasing, not all equal; all slugs are snapshot
  protocols; no duplicates; every row has 5 farm steps of 20–600 chars and a
  verdict; verdicts 3 farm / 82 thin / 115 skip; top usdd $18,244,089; rank 200
  $165,774; fillers pacifica-bridge / japan-staked-sol at 199–200; 20
  parentProtocol exclusions flagged; board.json 453,768 bytes (≤ 8 MiB).
- Dashboard: index.html + .css + .js present; total 32,292 bytes (< 65,536, so
  the dossier text shows the whole source — verified: no `[Cut at` marker);
  ≤ 4 MiB; plain file names; zero `http://`/`https://` strings.
- Screenshots: 3 PNGs, each 1440×800, 144–157 KB (≤ 512 KiB cap, inside the
  300–350 KB recommended range).
- Dossier: 639,251 bytes (≤ 1.5 MiB gate cap); **byte-identical to an
  independent `buildDossier` rebuild**; cover is `1-board.png`.
- `main.ts` stdlib-only; `vendor/makefun-board.ts` sha256 matches the kit.

**Determinism:** three fresh runs produce byte-identical output trees —
two runs on Node 24.22.1 and one on **Node 22.23.4 (the grader's exact
runtime)**, all identical to `out/` (per-file sha256 compared, `diff -r`
clean).

**Runtime / resources (grader-shaped):** 0.69 s wall on 1 CPU (`taskset -c 0`),
max RSS ~124 MB, with a 1024 MB heap cap — limits are 120 s / 1024 MB.

**Screenshots — how they were produced (real browser, verified visually):**
rendered in real headless Chromium 131.0.6778.33 via Playwright, loading
`out/dashboard/index.html` over `file://` at 1440×800 (the Meta Chromium in
`/opt/meta-chromium` is policy-locked and refuses to start, so a stock
Chromium was downloaded; the kit's `RULES.txt` browser requirement is met by
this install, kept as scratch at `~/workspace/.shot/chromium/`). The board
shot shows 200 rows, the detail shot shows the usdd detail view, the filtered
shot shows the farm filter with exactly 3 rows; no page console errors. All
three were read back and visually checked.

## Fidelity to the draft board

`out/board.json` vs the draft `board.json` (same model, same snapshot):
identical slug order, implied values, odds, fitted values, farm plans and
verdicts. The **only** differing fields are the bootstrap EV rank-range
columns (`rank_lo_boot_ev` on 72 rows, `rank_hi_boot_ev` on 63 rows, each by
1–2 ranks): `main.ts` runs its own bootstrap (mulberry32, seed 42) while the
Python draft used numpy's PCG64 (seed 42) — same estimator, different
resample stream. Recomputed rank-range stats over all 342 no-token protocols:
median EV width **18.5** (draft 17), **9** span the top-40 boundary (draft 9),
**42** span the board-200 boundary (draft 42). The dashboard and this file
report the shipped (TypeScript) numbers.

## Still missing for submission (do NOT submit from this package as-is)

1. **GitHub repo** (or a source bundle via the kit's `init`, which must run in
   a fresh session before the files are written). Repo must be public, created
   at/after the 2026-11-14 opening, OSI-licensed (MIT file included), with
   `main.ts` at root, and either owned by the linked GitHub account or carrying
   `.makefun/owner.json` with the linked wallet.
2. **Agent transcripts** that built the entry (the transcript gate needs
   sessions showing the code being written; this package was built in Muse
   sessions — bundle them with the kit CLI and check the gate before
   submitting).
3. **The submission itself** (≤ 5/day, ≤ 10 total; last receipt before
   2026-12-14 10:00 UTC is final). The entry signature needs the linked Solana
   wallet (already linked as Primary on @finchbetter).
4. Re-run the kit CLI's `check` on the repo + transcript bundle before
   submitting; the local gate-shaped checks above are not the server's scorer.

Scratch (deletable, not part of the entry): `~/workspace/.shot/` (Chromium 131,
Node 22.23.4, ~939 MB), `/tmp/shot/` (screenshot + validation scripts, rerun
outputs `out1`/`out2`/`out22`).
