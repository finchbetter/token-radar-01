# Token Radar — value model and draft board (MODEL.md)

- Bounty: `token-radar-01` — "Build the best token launch radar", $1,325, deadline **2026-12-14 10:00 UTC**
- Entrant: @finchbetter (make.fun)
- Snapshot: DefiLlama, `as_of` **2026-11-14**, frozen; source `DefiLlama https://api.llama.fi/protocols, fetched 2026-11-14T01:18:33.201Z`
- Built: 2026-11-20 (UTC), locally, from `kit/input/snapshot.json` only
- Status: **DRAFT. Not submitted. No GitHub repo created, no dashboard, no screenshots, no dossier, no `main.ts` yet — this file covers the model and the draft board only.**
- Scripts: `fit_model.py` (value fit + held-out tests + walk-forward), `fit_part2.py` (rank ranges, launch odds, board build), `fit_results.json` (all numbers, machine-readable)

## 0. Headline

The snapshot cannot support a rich value model. After testing every candidate term on **two** held-out splits, the only term that survives is `log(TVL)`:

```
log(mcap_usd) = 9.1133 + 0.3940 * log(tvl_usd)     n = 92 clean comps
```

In-sample median absolute log error **1.164** (a typical error of ~e^1.16 ≈ 3.2×), residual SD **1.95** log points, R² **0.104**. TVL explains about 10% of the variation in log market cap. Fitted values are order-of-magnitude estimates, and the board is therefore a TVL ranking reweighted by launch odds — that is stated, not hidden. The board still passes the submit gate defined in §9, because the gate tests the shipped model against the flat-multiple baseline, and the shipped model beats it on every held-out check.

## 1. Census — all 758 protocols accounted for

| Group | Count |
|---|---|
| Total protocols in snapshot | 758 |
| Token-bearing (gecko_id or symbol present) | 416 |
| Records no token (both gecko_id AND symbol null) | 342 |
| — of which pass the reproducible eligibility screen (§2) | 198 |
| — of which fail it (wrapped / staked / bridged / CEX / versioned) | 144 |
| mcap_usd present | 144 |
| mcap_usd present but exactly 0 (unusable in logs) | 15 |
| mcap_usd > 0 (log-fittable) | 128 |
| — of which excluded as wrapped/staked (§2) | 36 |
| — clean comps used for the fit | 92 |

Reconciliation: 758 = 416 token-bearing + 342 no-token. 342 no-token = 198 screen-eligible + 144 screen-ineligible. 144 mcap-present = 128 mcap > 0 + 15 mcap = 0 + 1 mcap = **−1** (`autofinance`, a negative sentinel, presumably a DefiLlama placeholder). The −1 row is excluded from the fit with the zeros: the log fit uses exactly the 128 rows with `mcap_usd > 0`.

Watchlist: 40 slugs, used exactly as shipped. Not re-derived: 20 exclusions are opaque because `parentProtocol` is not in the snapshot (see §7).

## 2. Comps set — 128 → 92

Start: 128 protocols with `mcap_usd > 0`. Excluded 36 as wrapped / staked / bridged products of a token that already trades, by the same reproducible rules as the watchlist (category in Bridge / Canonical Bridge / Liquid Staking / Liquid Restaking / Restaked BTC / CEX; name contains whole word wrapped / staked / staking; name begins with an exchange name; versioned name). Exclusion tags among the 36 (a row can carry more than one):

| Reason | Rows |
|---|---|
| category: CEX | 9 |
| category: Liquid Staking | 9 |
| category: Canonical Bridge | 8 |
| category: Bridge | 6 |
| category: Liquid Restaking | 2 |
| wrapped/staked word in name | 1 |
| exchange-prefix name | 1 |
| versioned name | 1 |

Examples excluded: `lido`, `rocket-pool`, `renzo` (Liquid Staking), `okx`, `gate`, `mexc` (CEX), `cbridge`, `polygon-bridge` (Bridge / Canonical Bridge), `aave-v2` (versioned name). Remaining **clean comps: 92**. The 15 zero-mcap rows are excluded from logs (log 0 undefined) and noted, not silently dropped: they are token-bearing rows whose recorded market cap is 0.

Clean-comp coverage gaps (affects §3): `listed_at` null for 22 of 92, `change_7d` null for 0 of 92. Category counts in the clean comps: Lending 14, Dexs 11, Yield 9, RWA 9, Basis Trading 7, Cross Chain Bridge 4, Yield Aggregator 4, and 21 further categories with n ≤ 3 (including Risk Curators n = 1 and Onchain Capital Allocator n = 2 — the watchlist's two largest categories, 12 and 3 of 40, have almost no clean-comp support, so no category effect for them is identified).

## 3. Value model — specification search and term survival

Dependent variable: `log(mcap_usd)`. FDV does not exist in the snapshot, so market cap is the dependent variable — stated, not proxied silently. Candidates, tested in nested order:

- M1: `log(mcap) ~ log(TVL)`
- M2: M1 + category dummies (categories with n ≥ 4 in clean comps get their own dummy: Basis Trading, Cross Chain Bridge, Dexs, Lending, RWA, Yield, Yield Aggregator; all other categories pooled into reference "Other")
- M3: M2 + `change_7d` (raw percent; 0 missing among clean comps, so no missing-indicator estimable; no-token rows with null `change_7d` are imputed at the clean-comp median −9.1126 for prediction)
- M4: M3 + `log(age)` where age = `as_of − listed_at` in days, plus an `age_missing` indicator (22 of 92 clean comps have no `listed_at`; their log-age is imputed at the clean-comp median log-age 6.7517)

Full-fit coefficients (M4, for the record — **not** the shipped model):

| Term | Coefficient |
|---|---|
| const | 11.226 |
| log_tvl | 0.335 |
| cat: Basis Trading | 1.173 |
| cat: Cross Chain Bridge | 0.539 |
| cat: Dexs | −0.053 |
| cat: Lending | −1.121 |
| cat: RWA | 0.290 |
| cat: Yield | −0.934 |
| cat: Yield Aggregator | −1.080 |
| change_7d | −0.039 |
| log_age | −0.178 |
| age_missing | −0.356 |

### Held-out test (a): time split by listed_at — older train, newer test

Train: listed before 2024-01-01 (n = 29); test: listed 2024-01-01 or later (n = 41); listed_at-null rows (n = 22) cannot be assigned to a cohort and are excluded from this split. Metric: median absolute log error (primary) and out-of-sample R² (vs the test-set mean).

| Model | MedAE | OOS R² |
|---|---|---|
| M0 flat multiple (mcap = TVL × median ratio) | 1.508 | -0.42 |
| M1 log(TVL) only | 0.712 | -0.01 |
| M2 + category | 1.015 | -0.05 |
| M3 + change_7d | 1.103 | -0.12 |
| M4 + age | 2.195 | -1.09 |

### Held-out test (b): leave-one-category-group-out (LOCO), pooled

Each pooled category group (7 dummies + "Other") is held out in turn; a held-out category is predicted with the reference ("Other") coefficient, as an unseen category would be. Pooled over all 92 rows:

| Model | MedAE | OOS R² |
|---|---|---|
| M0 flat multiple | 1.504 | -0.16 |
| M1 log(TVL) only | 1.383 | -0.06 |
| M2 + category | 1.238 | -0.07 |
| M3 + change_7d | 1.230 | -0.12 |
| M4 + age | 1.090 | -0.18 |

Per-group LOCO MedAE (M0 / M1 / M2 / M3 / M4):

| Basis Trading | 7 | 1.54 | 0.68 | 0.44 | 0.80 | 0.63 |
| Cross Chain Bridge | 4 | 1.22 | 1.38 | 1.33 | 1.26 | 1.29 |
| Dexs | 11 | 1.95 | 1.62 | 1.48 | 1.28 | 1.48 |
| Lending | 14 | 1.43 | 1.73 | 1.72 | 2.03 | 2.01 |
| RWA | 9 | 0.62 | 0.56 | 0.41 | 0.71 | 0.49 |
| Yield | 9 | 1.44 | 1.38 | 1.58 | 1.69 | 1.59 |
| Yield Aggregator | 4 | 1.13 | 0.81 | 1.03 | 1.10 | 0.81 |
| Other | 34 | 2.04 | 1.63 | 1.50 | 1.56 | 1.77 |

### Term survival — the rule and the result

A term is kept only if adding it lowers MedAE on **both** held-out tests. Results:

| Term added | ΔMedAE time-split | ΔMedAE LOCO | Survives both? |
|---|---|---|---|
| category | -0.303 | 0.145 | False |
| change_7d | -0.088 | 0.008 | False |
| age (log-age + missing) | -1.092 | 0.140 | False |

(ΔMedAE is the MedAE of the model without the term minus the MedAE with it; positive = the term helps. Category helps LOCO by 0.145 but hurts the time split by 0.303; change_7d helps LOCO by 0.008 — negligible — and hurts the time split by 0.088; age helps LOCO by 0.140 but hurts the time split by 1.092, the worst failure. The time-split training set is small (n = 29), so the richer models overfit it; that is itself the finding.)

**Dropped: category, change_7d, age. Shipped model: M1, `log(mcap) = 9.1133 + 0.3940 · log(TVL)`.** Fitted value is `exp(predicted log mcap)` — the median fitted value, not the log-normal mean (the mean would multiply every fitted value by the same exp(σ²/2) ≈ 6.7× and change no rank, so the median is used and stated).

Why the OOS R² values are negative: the test sets are small and the residual variance is large (SD ≈ 1.95 log points), so every model — including the flat baseline — predicts worse than the test-set mean in variance terms, while still beating the baseline on median absolute error. MedAE is the primary metric for that reason; R² is reported alongside and the model beats the flat baseline on both metrics on both tests (time-split R² −0.011 vs −0.424; LOCO R² −0.063 vs −0.159).

## 4. Walk-forward (listed_at cohorts, expanding window)

Refit on expanding listed_at cohorts, test the next cohort. This is a cohort walk-forward on a single frozen cross-section — there is no time series in the snapshot, and no time-series walk-forward is claimed.

| <=2022 → 2023 | 16 | 13 | 1.034 | -0.19 | 1.644 | -0.67 |
| <=2023 → 2024 | 29 | 12 | 0.678 | 0.02 | 1.456 | -0.14 |
| <=2024 → 2025-26 | 41 | 29 | 0.796 | -0.34 | 1.585 | -0.87 |

Pooled walk-forward (n = 54 test rows): MedAE **0.878**, OOS R² -0.09; flat-multiple baseline MedAE 1.584, R² -0.47. The shipped model beats the flat baseline in every fold and pooled.

## 5. Rank ranges — LOO + 200 bootstrap refits

92 leave-one-comp-out refits and 200 bootstrap refits (resample the 92 clean comps with replacement, seed 42), each refit predicting fitted values for all 342 no-token protocols; ranks are within the 342 by fitted value (rank 1 = highest).

**Fitted-value rank ranges are degenerate — and that is informative, not a bug.** The shipped model is monotone in TVL with a positive slope in every refit, so coefficient resampling cannot reorder fitted values at all: bootstrap 5–95% rank width median **0**, LOO rank width median **0**, max 0; 0 protocols span the top-40 boundary on fitted value. The honest uncertainty in a protocol's rank is the residual noise (SD 1.95 log points ≈ 7×), which would swamp any coefficient-based interval — these ranges measure coefficient uncertainty only, and they show the fitted ranking is exactly the TVL ranking. The meaningful rank uncertainty is therefore reported on **expected value** (fitted value × launch odds, §6), where the odds differ per protocol:

| Quantity | Value |
|---|---|
| EV rank range, bootstrap 5–95%, median width | 17 ranks |
| Protocols whose EV rank range spans the top-40 boundary | 9 |
| Protocols whose EV rank range spans the board-200 boundary | 42 |

Top-40 boundary spanners (EV rank 5–95% interval crosses rank 40): `bingx`, `bitfi-basis`, `cian-yield-layer`, `gauntlet`, `nexus-btc`, `rsk-bridge`, `sentora-curator`, `steakhouse-financial`, `zksync-era-txbridge`.

Board-200 boundary spanners (interval crosses rank 200 — these are the least certain inclusions/exclusions): `arcus-perps`, `axis`, `azverse-perps`, `bdex-v3`, `bend`, `bitvavo`, `bulbaswap-v3`, `byreal`, `coin8`, `d2-finance`, `decibel`, `exinpool`, `forward-industries-sol`, `granite`, `growihf`, `hubra-staked-sol`, `hylo-lsts`, `inceptionlrt-(isolated-restaking)`, `lbank`, `marginfi-lst`, `metalx-swap`, `morph-bridge`, `nonce-capital`, `nucleus`, `orangex`, `phase-delegation`, `potatoswap-v2`, `re7-labs`, `rockawayx`, `sceptre-liquid`, `starknet-btc-staking`, `stellar-defi-hub`, `sygnum-fiusd-liquidity-fund`, `syncswap`, `tempo-stablecoin-dex`, `theo-network-thusd`, `tulipa-capital`, `txflow-bridge`, `valos`, `valr`, `wemix.fi-staking`, `yieldfi`.

Per-row rank ranges (bootstrap 5–95% and LOO min–max, fitted and EV) are in `board.json` for every row (`rank_lo_boot_ev`, `rank_hi_boot_ev`, `spans_top40_ev`, `spans_board200_ev`). Ranks near either boundary should be treated as unstable.

## 6. Launch odds — logistic P(token-bearing)

**What this is:** a cross-sectional model of token *presence* in the snapshot (416 token-bearing vs 342 no-token), used as a relative launch-odds score. It is **not** a launch-time hazard: the snapshot has no launch dates and no time-to-launch data, so no claim is made about *when* a token appears. Features (standardised, L2 penalty λ = 1.0): log(TVL), log-age (winsorised at the 99th percentile, 7.51), age-missing indicator, change_7d (winsorised to [−50, +100] — 4 of 758 rows clipped: `shift-defi` +4448.5%, `monolith-market` +162.9%, `nuva` +160.8%, `anemoy-capital` −72.7%; without this, `shift-defi`'s +4448% drives its logit to −∞ and its odds to ~0), change-missing indicator, peers-with-token (leave-one-out token rate within the protocol's own category; overall rate 0.549 for singleton categories). Missing `listed_at` (113 rows) and `change_7d` (4 rows) are imputed at the all-rows medians (log-age 6.5177, change_7d -8.2334) with missing indicators carried.

Standardised coefficients (full fit, n = 758):

| Feature | Coefficient |
|---|---|
| log_tvl | 0.149 |
| log_age (winsorised) | 0.527 |
| age_missing | 0.345 |
| change_7d (winsorised) | -0.219 |
| change_missing | 0.098 |
| peers_token_rate | 0.536 |
| intercept | 0.206 |

Older protocols, higher TVL, and categories whose peers mostly have tokens score higher odds; fast recent TVL growth scores *lower* (negative change_7d coefficient) — new, fast-growing protocols are less likely to already record a token, which is consistent with growth preceding a launch rather than following one.

**Cap at the oldest cohort:** predicted odds are capped at the empirical token rate of the oldest listed_at cohort (listed before 2022-01-01, n = 15, rate 0.800). 8 of 342 no-token rows are capped. Odds on the 342 no-token rows after capping: min 0.023, median 0.473, max 0.800.

### Held-out calibration

Time split (train listed < 2024, n = 172; test listed ≥ 2024, n = 473): **Brier 0.2518** vs base-rate Brier 0.3848; mean predicted 0.519 vs observed 0.406 — the model **overpredicts on the newer cohort** (it was trained on older protocols, which are more likely to have tokens). 5-fold random CV: **Brier 0.2111** (folds 0.1865, 0.1987, 0.2108, 0.2134, 0.2460) vs base-rate 0.2482. The odds beat the base rate on both checks but are miscalibrated across time — treat them as relative scores for ranking, not as calibrated launch probabilities.

Decile reliability on the time-split test set (mean predicted vs observed token rate):

| Decile | n | Mean predicted | Observed |
|---|---|---|---|
| 1 | 47 | 0.092 | 0.234 |
| 2 | 47 | 0.249 | 0.298 |
| 3 | 47 | 0.358 | 0.213 |
| 4 | 48 | 0.466 | 0.354 |
| 5 | 47 | 0.527 | 0.426 |
| 6 | 47 | 0.586 | 0.426 |
| 7 | 48 | 0.635 | 0.396 |
| 8 | 47 | 0.686 | 0.511 |
| 9 | 47 | 0.750 | 0.638 |
| 10 | 48 | 0.832 | 0.562 |

## 7. Expected value and the draft board

Expected value = fitted mcap × launch odds. Board: **200 rows** — all 40 watchlist slugs plus 160 more, ranked by expected value, ranks 1–200 unique, implied values non-increasing with rank. Implied value = round(expected value), range **$18,244,089** (rank 1) to **$165,774** (rank 200). Board composition:

- 40 watchlist rows (all present, verified).
- 158 further no-token rows passing the reproducible eligibility screen.
- 2 filler rows at ranks 199–200 (`pacifica-bridge`, category Bridge; `japan-staked-sol`, Liquid Staking + staked word) — the screen-eligible no-token universe is exactly 198, so 2 rows are needed to reach 200. Both are flagged with their exclusion reasons, verdict `skip`, and their implied values are capped at the rank-198 value ($165,774) to keep the board monotone. They are the lowest-EV ineligible rows, chosen to minimise the distortion.
- **20 rows in the board carry a known `parentProtocol` exclusion** (the house watchlist rule; the field is absent from the snapshot, so these cannot be re-derived — they are the 20 opaque exclusions verified in `kit-inspection.md` §5, and all 20 fall inside the top 200 by EV): `defi-saver-asset-management`, `polymarket-international`, `sentora-curator`, `cian-yield-layer`, `bitfi-basis`, `figure-markets-prime`, `loopscale-lending`, `circle-gateway`, `figure-markets-exchange`, `extended-perps`, `mellow-core`, `nado-spot`, `avant-avusd`, `ipor-fusion`, `solv-strategies`, `theo-network-thusd`, `arcus-perps`, `stellar-defi-hub`, `azverse-perps`, `usdcx`. Each is flagged `known_parentprotocol_exclusion: true`, carries the exclusion reason, and is forced to verdict `skip` — they are child/wrapped products of a protocol whose token trades, so the board ranks them by EV but tells the reader not to farm them. The fully clean universe is therefore 198 − 20 = 178 rows, not 198; the board does not hide that.

Top 10 by expected value:

| Rank | Slug | Implied value | Fitted mcap | Odds | Verdict |
|---|---|---|---|---|---|
| 1 | usdd | $18,244,089 | $32,593,338 | 0.560 | farm |
| 2 | veda | $17,726,536 | $38,045,564 | 0.466 | thin |
| 3 | defi-saver-asset-management | $15,377,077 | $19,221,347 | 0.800 | skip |
| 4 | steakhouse-financial | $15,010,191 | $47,553,596 | 0.316 | thin |
| 5 | lightning-network | $14,001,432 | $17,501,790 | 0.800 | farm |
| 6 | polymarket-international | $13,370,245 | $20,369,070 | 0.656 | skip |
| 7 | b14g | $12,684,081 | $16,016,125 | 0.792 | thin |
| 8 | sentora-curator | $12,648,074 | $47,578,106 | 0.266 | skip |
| 9 | symbiotic | $11,806,670 | $18,590,518 | 0.635 | skip |
| 10 | cian-yield-layer | $11,445,588 | $19,328,174 | 0.592 | skip |

Notes on the top 10: `usdd` (rank 1) is on the house watchlist itself (TVL $1,055,793,606, CDP) and is ranked by the snapshot's record, which records no token for it — the kit's wording rule is followed ("records no token", never "has none"). `lightning-network` (rank 5) has `listed_at` null, so its age is imputed and its odds (0.800, the oldest-cohort cap) rest on TVL and peers, not age. `defi-saver-asset-management`, `polymarket-international`, `sentora-curator`, `cian-yield-layer` (ranks 3, 6, 8, 10) are parentProtocol exclusions — high EV, verdict skip.

Verdicts (farm / thin / skip): **3 / 82 / 115** of 200. Watchlist rows: 3 farm, 21 thin, 16 skip. Every row carries its fitted mcap, odds, expected value, bootstrap/LOO rank ranges and cost breakdown in `board.json`.

## 8. Farm plans — cost model (ASSUMPTIONS, not snapshot data)

No gas price, fee, deposit, airdrop size or farmer count exists in the snapshot. Every cost figure below is a **stated assumption** used to net each row's plan; change the assumption and the verdicts move, and the model says so. The plan itself (5 steps per row, 186–247 characters each, generated from the row's own name, primary chain, category and TVL) never claims an airdrop exists — each step says "if a token is ever recorded".

| Item | Assumption |
|---|---|
| Transactions | 10 (1 deposit + 8 weekly interactions + 1 claim/exit) |
| Gas per tx | Ethereum $12.00; Solana $0.05; Base / Arbitrum / Optimism / Polygon $0.50; any other chain $2.00 |
| Bridge fee | $12.00 flat, only when the protocol spans > 1 chain |
| Deposit / working capital | $250.00, returned on exit — counted as capital at risk, **not** as a cost |
| Opportunity cost of deposit | 5% APR × 12 weeks = $2.88 |
| Total out-of-pocket cost | 10 × gas + bridge fee + $2.88 (per-row, in `board.json` as `farm_cost`) |
| Time | 3.0 h setup/research + 0.5 h per chain |
| Expected farmer receipt | EV × 1e-5 (assumes 5% of supply airdropped, shared among 5,000 farmers) |
| $/hour | (expected receipt − total cost) / hours |
| Break-even | cost / EV, as % of token supply a farmer must receive to cover costs |
| Verdict | `farm` if $/hour ≥ $25; `thin` if $/hour ≥ $0; `skip` if $/hour < $0; forced `skip` for any row with an exclusion reason |

Worked example (rank 1, `usdd`, Ethereum, 1 chain): gas 10 × $12 = $120, bridge $0, opportunity $2.88 → cost $122.88; hours 3.5; EV $18,244,089 → receipt $182.44 → $/hour $32.79 → `farm`. A Solana row with the same EV would cost ~$3.38 and clear `farm` far more easily — the verdicts are chain-cost sensitive by design.

## 9. Submit gate — PASS (model/board draft only)

| # | Criterion | Result |
|---|---|---|
| 1 | Out-of-sample beats the flat-multiple baseline | **PASS** — MedAE: time-split 0.712 vs 1.508; LOCO 1.383 vs 1.504; walk-forward pooled 0.878 vs 1.584. R² also better on all three (time −0.011 vs −0.424; LOCO −0.063 vs −0.159; WF −0.089 vs −0.471). |
| 2 | Every term in the shipped model survives two held-out tests | **PASS** — shipped model has one term, log(TVL); it beats the flat baseline on both held-out tests. Category, change_7d and age were tested and **dropped** (each failed at least one test, §3). |
| 3 | Census complete | **PASS** — all 758 protocols classified (§1), including the one `mcap_usd = −1` sentinel row (`autofinance`), disclosed in §1. |
| 4 | Every row has a netted farm plan | **PASS** — 200/200 rows carry 5 farm steps (20–600 chars), a full cost breakdown (fees + gas + deposit + opportunity cost), break-even, $/hour and a verdict. |

**Overall: GATE PASS for the draft board.** Scope limit: this gate covers the value model and the draft `board.json` only. It does **not** certify submission readiness — a submittable entry additionally needs a public GitHub repo, `main.ts`, the dashboard, 3 screenshots, `dossier.json` and transcripts, none of which are built here. No submission has been made.

## 10. Missing data — reported, not filled

- **FDV: absent.** No `fdv` field exists on any row; the model uses `log(mcap_usd)`, stated in §3.
- **parentProtocol: absent.** 20 watchlist exclusions (and possibly more below the floor) cannot be reproduced from the snapshot; the 20 known ones are flagged in §7, the rest are unknowable from this file.
- **listed_at null: 113 of 758** (24 of 342 no-token, including 2 watchlist rows `lightning-network` and `noble`; 22 of 92 clean comps). Age is imputed at the median with a missing indicator where the model uses it; the shipped model does not use age.
- **change_7d null: 4 of 758** (`contango-v2`, `estate-protocol`, `kinetiq-elysium-bridge`, `swan-dao`; 2 of them no-token). Imputed at the median for the odds model; the shipped value model does not use it.
- **mcap_usd null: 614 of 758** (272 token-bearing rows record a token but no market cap; 342 no-token rows). The fit uses the 128 with mcap > 0.
- **mcap_usd = 0: 15 rows.** Excluded from logs; token-bearing rows with a recorded zero market cap.
- **No ranking, implied value, farm plan or airdrop flag in the snapshot.** All are derived here; no TVL, token or airdrop was invented for any row.

## Files

- `board.json` — draft board, 200 rows (457,123 bytes)
- `fit_results.json` — every number in this file, machine-readable
- `fit_model.py`, `fit_part2.py`, `write_model_md.py` — the fit, reproduced from `kit/input/snapshot.json`
- `fit_part1.json` — intermediate held-out results
- `kit-inspection.md`, `counts.json` — snapshot inspection this model builds on
