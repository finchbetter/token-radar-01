# Token Radar kit inspection — @finchbetter / token-radar-01

- Bounty: `token-radar-01` — "Build the best token launch radar", $1,325, deadline **2026-12-14 10:00 UTC**
- Entrant: @finchbetter (make.fun)
- Inspected: 2026-11-20 (UTC) — kit downloaded and verified this day
- Status: **inspection only. No submission made, no GitHub repo created, no skill.md instructions followed.**

## 1. Kit provenance (official sources only)

The kit download endpoint was found in the official competition API response
(`https://make.fun/api/competitions/token-radar-01`, top-level `kit` field), not guessed:

```json
"kit": {"json": "/api/competitions/token-radar-01/kit",
        "tarball": "/c/token-radar-01/kit", "final": null}
```

The bounty page's rules text says the same: "Download the kit from this
competition's page (/c/token-radar-01/kit) and unpack it."

| Item | Value |
|---|---|
| Kit metadata | `https://make.fun/api/competitions/token-radar-01/kit` → saved as `kit.json` |
| Kit tarball | `https://make.fun/c/token-radar-01/kit` → saved as `kit.tar.gz` (7,026,585 bytes) |
| Tarball sha256 (downloaded bytes) | `7d0dd00f36548789e56fee94ba76a6c3b57ded0b1af225749255233e03d92efa` |
| Kit format | `agent-fun/kit/v1`, phase `dev` |
| `bundle_sha256` | `ea1c9dccab78e6846655e81b921a79465c7267677ea2e0908624ddbc8a012d43` (matches the `bundleSha256` in the competition API response) |
| `dataset_sha256` | `null` |
| `harness_version` | `harness@eaddce115e6147e3b388dbfd3a9bb492fb2f37c8e3a9c4df37cec51e92058c0a node v26.13.1` |
| `pricing_rev` | `6a262a9d0245fc1bb135c62775a6abd481aace3029ff2857a45310eb172ac899` |

**Integrity: all 20 files in the tarball match the sha256 manifest in `kit.json`
exactly (0 missing, 0 mismatched).** The extracted `kit/kit.json` is byte-identical
in content to the API-served `kit.json`.

One unexplained discrepancy, recorded not resolved: the HTTP response header
`x-kit-sha256` was `00ee9d3a…c9c`, which matches **neither** the downloaded
`.tar.gz` sha256 (`7d0dd00f…`) **nor** the sha256 of the decompressed tar stream
(`3d36117e…`). It is not the `bundle_sha256` either. Integrity therefore rests on
the per-file manifest check above, which passed fully — the header value is not
relied on.

Kit contents (20 files): `RULES.txt`, `competition.yaml`, `cli/makefun.mjs`,
`cli/site.json`, `harness/` (CODE/SOURCES sha lists + harness-src tarball),
`input/README.md`, `input/snapshot.json` (247,940 bytes), `starter/` (LICENSE,
dashboard, `lib/model.ts`, `main.ts`, screenshots, `vendor/makefun-board.ts`).

## 2. Snapshot identity

`kit/input/snapshot.json`, per its own `input/README.md` (the kit's field guide):

- `as_of`: **2026-11-14**
- `source`: `DefiLlama https://api.llama.fi/protocols, fetched 2026-11-14T01:18:33.201Z`
- `floor_usd`: **$50,000,000** (watchlist floor)
- Frozen: one fetch, same bytes for every run and for grading; read-only, never updated.
- Top-level keys: `as_of`, `source`, `floor_usd`, `protocols`, `watchlist`.

## 3. Schema — exact fields (all verified present)

Every one of the 758 protocol objects carries **exactly these 10 fields, no others**
(verified: single field-set across all 758 rows).

| Field | Type | Meaning (per README) | Present? |
|---|---|---|---|
| `slug` | string | DefiLlama slug, unique; `watchlist` names protocols by it | Yes — 758, 0 duplicates, sorted ascending |
| `name` | string | Protocol name as DefiLlama writes it | Yes — all 758 |
| `category` | string or null | e.g. `Dexs`, `Lending`, `Bridge` | Yes — **0 nulls** |
| `chains` | string[] | Chains TVL is counted on | Yes — all non-empty |
| `tvl_usd` | number | TVL in whole USD, truncated toward zero | Yes — all 758; range $5,007,171 – $116,083,653,379 |
| `change_7d` | number or null | TVL change over 7 days, in % (12.5 = +12.5%), 4 dp | Yes — **4 nulls** (`contango-v2`, `estate-protocol`, `kinetiq-elysium-bridge`, `swan-dao`) |
| `mcap_usd` | number or null | Token market cap in whole USD, truncated; null when no token / no mcap | Yes — **614 nulls**, 144 present, of which **15 are exactly 0** |
| `listed_at` | string `YYYY-MM-DD` or null | UTC day DefiLlama began tracking the protocol | Yes — **113 nulls** |
| `gecko_id` | string or null | Token's CoinGecko id; null when no token recorded | Yes — **600 nulls** |
| `symbol` | string or null | Token ticker; null when no token recorded (`-` written as null) | Yes — **342 nulls** |

### Fields that do NOT exist in the snapshot

- **FDV — absent.** There is no `fdv` / fully-diluted-valuation field on any row
  (verified: no key contains `fdv`). The only `fdv` substring in the file is inside
  the slug `dfdv-staked-sol`. Any "log FDV vs log TVL" model must therefore use
  **`log(mcap_usd)` as the dependent variable**, not FDV — or state explicitly that
  FDV is being proxied by market cap.
- **`parentProtocol` — absent.** The README states it is DefiLlama's record and
  "not one of the ten fields this file carries". This matters: 20 watchlist
  exclusions cannot be reproduced from the snapshot alone (see §5).
- **No-token age — no direct field.** Derivable only as `as_of − listed_at`
  (days since DefiLlama first tracked the protocol); uncomputable for the 113
  rows with `listed_at` null, including 2 watchlist rows (`lightning-network`, `noble`).
- **No ranking, implied value, farm plan, or airdrop flag.** The snapshot carries
  none of these; deriving them is the entry's work.
- Wording rule from the kit: say a protocol **"records no token"**, never that it
  "has none" — a listed protocol may still have a token its DefiLlama record
  does not carry.

## 4. Counts (all computed from the inspected snapshot; see `counts.json`)

| Count | Value |
|---|---|
| Total protocols | **758** |
| Watchlist size | **40** |
| TVL ≥ $50M (floor) | 319 |
| No token (both `gecko_id` AND `symbol` null) | **342** |
| `gecko_id` null alone | 600 |
| `symbol` null alone | 342 |
| Symbol present but `gecko_id` null (mismatch — token-ish, no CoinGecko id) | 258 (all 258 have `mcap_usd` null) |
| No token AND TVL ≥ $50M | 132 |
| No token AND TVL < $50M | 210 |
| Token-bearing (not both-null) | 416 |
| `mcap_usd` present | 144 (all 144 have `gecko_id` set) |
| `mcap_usd` = 0 (present but zero — unusable in logs) | 15 |
| Log-fittable comps (`mcap_usd` > 0) | **128** |

### 758 verification — CONFIRMED

The entrant-reported total of **758 protocols is exact**: the snapshot holds 758
protocol objects, all at or above $5,000,000 TVL (minimum observed $5,007,171),
and the kit's own `competition.yaml` states the same ("758 protocols at or above
$5,000,000 of TVL, 40 on the watchlist"). @sudhan's "every one of 758 protocols
accounted for" matches the file.

Note on entrant titles claiming "198-row" / "226-row" / "250-row" boards: those are
the entrants' **expanded boards**, not the house watchlist. The house watchlist is
40; a valid `board.json` needs **at least 100 rows**, so at least 60 rows must name
protocols outside the watchlist (see §7).

## 5. Wrapped / staked exclusions — 92 excluded, 20 of them opaque

Of the 132 no-token protocols at/above the $50M floor, **40 are on the watchlist
and 92 are excluded**. Re-applying the README's reproducible rules to those 92:

| Exclusion reason (reproducible from the 10 fields) | Rows tagged* |
|---|---|
| `category` = CEX | 27 |
| `category` = Liquid Staking | 18 |
| `category` = Bridge | 15 |
| Name begins with an exchange name (Binance, Coinbase, Bybit, Kraken, Bitget, OKX, Bitfinex, Gemini) | 13 |
| `category` = Canonical Bridge | 8 |
| Name contains whole word `wrapped` / `staked` / `staking` | 8 |
| `category` = Restaked BTC | 2 |
| Versioned name (trailing `V2` / `v2` / `2.0` etc.) | 2 |
| **Rows with ≥ 1 reproducible reason** | **72** |
| **Rows with NO reproducible reason — excluded only by `parentProtocol`, which is not in the file** | **20** |

\* A row can carry more than one tag (93 tags across 72 rows).

The 20 parentProtocol-only exclusions (slugs): `arcus-perps`, `avant-avusd`,
`azverse-perps`, `bitfi-basis`, `cian-yield-layer`, `circle-gateway`,
`defi-saver-asset-management`, `extended-perps`, `figure-markets-exchange`,
`figure-markets-prime`, `ipor-fusion`, `loopscale-lending`, `mellow-core`,
`nado-spot`, `polymarket-international`, `sentora-curator`, `solv-strategies`,
`stellar-defi-hub`, `theo-network-thusd`, `usdcx`.

For reference, among **all** 342 no-token protocols (any TVL): versioned names 11,
excluded categories 128, wrapped/staked word in name 20, exchange-prefix names 14.
(`Liquid Restaking` contributed 0 exclusions among the ≥$50M no-token set.)

Worked examples of the rule (from the inspected rows): `wbtc` (Bridge), `binance-staked-eth`
(Liquid Staking + staked-word + exchange-prefix), `aera-v3` (versioned name),
`rocketswap-anubis-v2` (versioned name). The README's own examples: WBTC is Bitcoin
on Ethereum; Binance staked ETH is ETH in Binance's staking product.

## 6. Watchlist profile (the 40)

- TVL range: **$51,272,081 – $2,753,981,495**. Largest by TVL (inspected rows):
  `steakhouse-financial` $2,753,981,495 (Risk Curators), `gauntlet` $1,577,685,462
  (Risk Curators), `veda` $1,563,415,482 (Onchain Capital Allocator).
- Categories: Risk Curators 12, RWA 7, Onchain Capital Allocator 3, Basis Trading 2,
  Lending 2, Chain 2, Yield 2, and 1 each of Restaking, Dexs, CeDeFi, Insurance,
  Payments, Governance Incentives, Staking Pool, Stablecoin Wrapper, Collateral
  Markets, CDP.
- Age (`as_of` − `listed_at`): median **511.5 days**, range 45–1,563 days;
  `listed_at` null for 2 (`lightning-network`, `noble`).
- `change_7d`: null for 0 of the 40; `category`: null for 0 of the 40.
- Chains per protocol: min 1, median 2.5, max 23.
- Whole-universe top categories (all 758): Dexs 99, Liquid Staking 78, Lending 75,
  CEX 56, Bridge 55, Risk Curators 39, Yield 39, RWA 33, Canonical Bridge 32,
  Onchain Capital Allocator 29, Derivatives 26, Yield Aggregator 23.

## 7. Board constraints (from the kit's `competition.yaml` — needed to plan the fit)

- `board.json`: 100–4,000 rows, ≤ 8 MiB; each row `slug` (one of the snapshot's
  protocols), non-empty `name`, `rank` (positive whole number, exactly 1..N once
  each), `implied_value_usd` (positive whole dollars, ≤ 10^14), `farm_steps`
  (3–12 strings, each 20–600 chars).
- `implied_value_usd` must not rise as rank ascends (rank 1 = most valuable);
  a board whose implied values are all equal is refused.
- **Every one of the 40 watchlist slugs must appear**; at least 60 rows must name
  protocols outside the watchlist.
- The starter writes 200 rows (40 watchlist + 160 early ones below the floor).
- Deliverables also include `dashboard/` (static, no network), 3 screenshots,
  `dossier.json` from `vendor/makefun-board.ts`, `main.ts` (Node 22) at repo root.

## 8. Exploratory baseline fit (NOT the final model)

Quick OLS on the 128 log-usable live-token comps, for calibration only:

- `log(mcap_usd) = 6.96 + 0.52 · log(tvl_usd)`, residual SD **2.08** (log points —
  a typical error of ~8×), n = 128.
- Split-half check (fit on even slugs, test on odd, and vice versa): slopes
  0.508 / 0.520, held-out RMSE 2.09 / 2.08. Slope is stable; precision is poor.
- Median mcap/TVL ratio among the 144 mcap-present comps: 0.169; p10 0.0
  (the 15 zero-mcap rows), p90 2.20.

Interpretation: TVL alone explains little of the variation in token value —
category effects and the other fields (growth, age, chains) have to carry real
weight, or the board will be a TVL ranking in disguise. Do not ship the
single-regressor fit.

## 9. Next steps for the value model

1. **Dependent variable: `log(mcap_usd)`** — FDV does not exist in the snapshot.
   Fit on the 128 comps with `mcap_usd > 0`; treat the 15 zero-mcap comps as a
   separate case (exclude from logs, or model P(mcap = 0) separately) — do not
   silently drop them without noting it.
2. **Specification:** `log(mcap) ~ log(TVL) + category` (category dummies; pool
   rare categories — 17 categories appear in the watchlist, several with n = 1).
   Add `change_7d` (growth) and age (`as_of − listed_at`, log-age) as candidates;
   test whether each survives held-out validation before keeping it. Handle the
   4 null `change_7d` and 113 null `listed_at` rows with an explicit missing
   indicator, not silent imputation.
3. **Held-out twice:** split the 128 comps by slug hash (or by category-stratified
   halves) into A/B; fit on A, score on B, then reverse. Require the slope and
   category effects to be stable and the held-out RMSE to beat the TVL-only
   baseline (2.08) on both halves before accepting the model.
4. **Walk-forward:** the snapshot is a single frozen cross-section (one fetch,
   2026-11-14) — there is no time series to walk forward on. The honest analogue
   is a **listed_at cohort split**: fit on protocols listed before a cutoff date,
   test on protocols listed after it (e.g. pre-2024 vs 2024+), and check the
   ranking holds for the younger cohort. Do not claim a time-series walk-forward
   the data cannot support.
5. **Board construction:** rank all 40 watchlist rows plus ≥ 60 more no-token
   rows below the $50M floor (the 210 below-floor no-token protocols are the
   "early ones" the radar exists to find); aim for the starter's 200-row shape.
   Every row needs 3–12 farm steps of 20–600 chars, derived from the protocol's
   own chains/category — no invented TVL, no invented token, no invented airdrop.
6. **Watchlist-coverage audit before any submit:** assert all 40 watchlist slugs
   present, ranks 1..N unique, implied values non-increasing with rank, no slug
   outside the 758, no row with `implied_value_usd` ≤ 0.
7. **Do not re-derive the watchlist from the 10 fields and expect 40.** The
   20 parentProtocol-only exclusions are not reproducible from the snapshot; use
   the shipped `watchlist` array as given.

## 10. Files in this workspace

- `~/workspace/makefun/token-radar/kit-inspection.md` — this file
- `~/workspace/makefun/token-radar/counts.json` — all counts in §4–§5, machine-readable
- `~/workspace/makefun/token-radar/kit.tar.gz` — downloaded kit (7,026,585 bytes)
- `~/workspace/makefun/token-radar/kit.json` — kit manifest (API-served)
- `~/workspace/makefun/token-radar/kit/` — extracted kit (20 files, manifest-verified)
- `~/workspace/makefun/token-radar/competition.json` — competition API response (2026-11-20)
- `~/workspace/makefun/token-radar/requirements.json` — requirements API response (2026-11-20)
- `~/workspace/makefun/token-radar/bounty.html` — bounty page (2026-11-20)

No submission, no GitHub repo, no skill.md content was used. All counts above were
computed from `kit/input/snapshot.json` as downloaded; no snapshot rows were invented.
