# Token Radar — @finchbetter, token-radar-01

A program plus the dashboard it writes. `main.ts` (Node 22, standard library only,
offline, deterministic) reads the sealed DefiLlama snapshot of 2026-11-14 (758
protocols, 40 on the watchlist), scores every protocol that records no token, and
writes `board.json` (200 rows), `data.js` (this page's data) and `dossier.json`.

## The model

- **Value:** `log(mcap_usd) = 9.1133 + 0.3940 * log(tvl_usd)`, OLS on 92 clean comps
  (token-bearing, mcap > 0, wrapped / staked / bridged / CEX rows excluded).
  In-sample MedAE 1.164 log points, R² 0.104, residual SD 1.95. The fitted value is
  exp(predicted log mcap) — a median, not a log-normal mean.
- **Dropped, not hidden:** category, 7-day growth and age were each tested and dropped.
  None lowers the median absolute error on BOTH held-out tests (time split by
  listed_at; leave-one-category-group-out), so the shipped model has one term.
- **Launch odds:** logistic P(token-bearing) on all 758 protocols (log TVL, log-age,
  age-missing, change_7d winsorised to [-50, 100], change-missing, peer token rate;
  L2 penalty 1.0), capped at the oldest cohort's token rate, 0.800. Cross-sectional
  token presence, not a launch-time hazard — the snapshot has no launch dates.
- **Expected value:** fitted mcap × launch odds. The board ranks 200 rows by EV:
  the 198 screen-eligible no-token protocols, plus the 2 lowest-EV ineligible rows
  as fillers at ranks 199–200 (implied values capped at the rank-198 value).
- **Verdicts:** farm if $/hour ≥ $25, thin if ≥ $0, skip if < $0; any row with an
  exclusion reason is forced to skip. Board: 3 farm / 82 thin / 115 skip.

## Held-out evidence (same sealed snapshot, offline fit)

- Time split (train listed < 2024, n=29; test ≥ 2024, n=41): shipped MedAE 0.712,
  OOS R² −0.011, vs flat-multiple baseline 1.508 / −0.424.
- Leave-one-category-group-out (n=92): shipped MedAE 1.383, R² −0.063, vs flat
  1.504 / −0.159.
- Walk-forward, listed_at cohorts, pooled (n=54): MedAE 0.878, R² −0.089, vs flat
  1.584 / −0.471. The shipped model beats the flat baseline in every fold.
- Launch-odds calibration: time-split Brier 0.252 vs base rate 0.385; 5-fold CV
  Brier 0.211 vs 0.248. The odds overpredict on the newer cohort — treat them as
  relative scores, not calibrated probabilities.

## Integrity

758 = 416 token-bearing + 342 recording no token; 342 = 198 eligible + 144
ineligible. FDV is absent from the snapshot (the model uses log mcap). parentProtocol
is absent: 20 watchlist exclusions cannot be re-derived; all 20 are flagged in the
board and forced to skip. One row records mcap = −1 (autofinance, a sentinel);
15 record mcap = 0. Say "records no token", never "has none".

## Farm costs (stated assumptions, not snapshot data)

10 transactions; gas by first chain (Ethereum $12, Solana $0.05, Base / Arbitrum /
Optimism / Polygon $0.50, other $2); $12 bridge fee when a protocol spans more than
one chain; $250 working capital, returned on exit; opportunity cost 5% APR × 12
weeks; expected farmer receipt = EV × 1e-5. No airdrop is claimed to exist: every
step says "if a token is ever recorded".

## Rank uncertainty

200 bootstrap refits + 92 leave-one-comp-out refits, recomputed by main.ts at
runtime (bootstrap seed 42). The fitted ranking is exactly the TVL ranking, so the
fitted-value rank ranges are degenerate (median width 0); the honest uncertainty
is the residual noise (SD 1.95 log points) and the odds, shown per row as the EV
rank interval.
