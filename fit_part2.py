#!/usr/bin/env python3
"""Part 2: LOO/bootstrap rank ranges, launch odds (logistic), EV ranking,
draft board.json (200 rows), MODEL.md, gate validation. Draft only — no submit."""
import json, re, math, random
from datetime import date
from collections import Counter
import numpy as np
from scipy.optimize import minimize

BASE = '/home/hatch/workspace/makefun/token-radar'
snap = json.load(open(f'{BASE}/kit/input/snapshot.json'))
ASOF = date.fromisoformat(snap['as_of'])
prots = snap['protocols']
by_slug = {p['slug']: p for p in prots}
WL = list(snap['watchlist']); WLSET = set(WL)
p1 = json.load(open(f'{BASE}/fit_part1.json'))

EXCH = ['Binance', 'Coinbase', 'Bybit', 'Kraken', 'Bitget', 'OKX', 'Bitfinex', 'Gemini']
EXCL_CAT = {'Bridge', 'Canonical Bridge', 'Liquid Staking', 'Liquid Restaking', 'Restaked BTC', 'CEX'}
VER_RE = re.compile(r'\s(V\d+(\.\d+)?|v\d+(\.\d+)?|\d+\.\d+)$')
WRAP_RE = re.compile(r'\b(wrapped|staked|staking)\b', re.I)

def reasons(p):
    r = []
    if p['category'] in EXCL_CAT: r.append('category:' + p['category'])
    if WRAP_RE.search(p['name']): r.append('wrapped/staked-word')
    if any(p['name'].startswith(e) for e in EXCH): r.append('exchange-prefix')
    if VER_RE.search(p['name']): r.append('versioned-name')
    return r

def notoken(p): return p['gecko_id'] is None and p['symbol'] is None
def age_days(p): return (ASOF - date.fromisoformat(p['listed_at'])).days if p['listed_at'] else None
def med(v): return float(np.median(np.array(v, dtype=float)))

# The 20 parentProtocol-only watchlist exclusions, verified in kit-inspection.md §5:
# no-token, >=$50M, pass the reproducible screen, yet excluded by the house rule
# because DefiLlama records a parentProtocol for them — a field the snapshot does
# not carry, so they cannot be re-derived here. They are child/wrapped products of
# a protocol whose token trades; flag them, do not farm them.
OPAQUE20 = {'arcus-perps', 'avant-avusd', 'azverse-perps', 'bitfi-basis',
            'cian-yield-layer', 'circle-gateway', 'defi-saver-asset-management',
            'extended-perps', 'figure-markets-exchange', 'figure-markets-prime',
            'ipor-fusion', 'loopscale-lending', 'mellow-core', 'nado-spot',
            'polymarket-international', 'sentora-curator', 'solv-strategies',
            'stellar-defi-hub', 'theo-network-thusd', 'usdcx'}

nt = [p for p in prots if notoken(p)]
tb = [p for p in prots if not notoken(p)]
elig_nt = [p for p in nt if not reasons(p)]
inelig_nt = [p for p in nt if reasons(p)]
clean = [p for p in prots if p['mcap_usd'] and p['mcap_usd'] > 0 and not reasons(p)]
assert len(clean) == p1['n_clean'] == 92

# ---- final model: TVL-only (all richer terms failed a held-out test) ----
def fit_tvl(rows):
    y = np.array([math.log(p['mcap_usd']) for p in rows])
    X = np.column_stack([np.ones(len(rows)), [math.log(p['tvl_usd']) for p in rows]])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta
def pred_tvl(beta, rows):
    return beta[0] + beta[1] * np.array([math.log(p['tvl_usd']) for p in rows])

beta_full = fit_tvl(clean)
print(f"final model: log(mcap) = {beta_full[0]:.4f} + {beta_full[1]:.4f} * log(TVL), n=92")
fitted_log_nt = pred_tvl(beta_full, nt)
fitted_mcap_nt = np.exp(fitted_log_nt)

def ordinal_ranks_desc(vals):
    order = np.argsort(-np.asarray(vals, dtype=float), kind='stable')
    ranks = np.empty(len(vals), dtype=int)
    ranks[order] = np.arange(1, len(vals) + 1)
    return ranks

# ---- LOO refits (92) + bootstrap refits (200, seed 42) ----
rng = np.random.default_rng(42)
nt_slugs = [p['slug'] for p in nt]
loo_preds = []
for i in range(len(clean)):
    tr = clean[:i] + clean[i+1:]
    loo_preds.append(pred_tvl(fit_tvl(tr), nt))
loo_preds = np.array(loo_preds)          # 92 x 342
boot_preds = []
for b in range(200):
    idx = rng.integers(0, len(clean), size=len(clean))
    tr = [clean[i] for i in idx]
    boot_preds.append(pred_tvl(fit_tvl(tr), nt))
boot_preds = np.array(boot_preds)        # 200 x 342
loo_ranks = np.array([ordinal_ranks_desc(r) for r in loo_preds])
boot_ranks = np.array([ordinal_ranks_desc(r) for r in boot_preds])
rank_lo_loo = loo_ranks.min(axis=0); rank_hi_loo = loo_ranks.max(axis=0)
rank_lo_b = np.percentile(boot_ranks, 5, axis=0).astype(int)
rank_hi_b = np.percentile(boot_ranks, 95, axis=0).astype(int)
spans40_fit = (rank_lo_b <= 40) & (rank_hi_b > 40)
print(f"bootstrap rank ranges (fitted value, 5-95pct): median width "
      f"{int(np.median(rank_hi_b - rank_lo_b))} ranks; "
      f"spanning top-40 boundary: {int(spans40_fit.sum())} of 342")
print("  top-40 spanners (fitted):", [nt_slugs[i] for i in np.where(spans40_fit)[0]][:40])

# ---- logistic launch odds: P(token-bearing) ----
# outcome: 1 = token-bearing (gecko_id or symbol present), 0 = no-token. Cross-sectional
# token presence, NOT a launch-time hazard — labelled as such in MODEL.md.
overall_rate = len(tb) / len(prots)
cat_rows = {}
for p in prots:
    cat_rows.setdefault(p['category'], []).append(p)
def peers_rate(p):
    rows = cat_rows[p['category']]
    k = sum(1 for q in rows if not notoken(q)); n = len(rows)
    y = 0 if notoken(p) else 1
    return (k - y) / (n - 1) if n > 1 else overall_rate

MED_CHG_ALL = med([p['change_7d'] for p in prots if p['change_7d'] is not None])
MED_LOGAGE_ALL = med([math.log(age_days(p)) for p in prots if age_days(p) is not None])
LOGAGE_P99 = float(np.percentile([math.log(age_days(p)) for p in prots if age_days(p)], 99))

CHG_LO, CHG_HI = -50.0, 100.0  # winsorise change_7d: 4 of 758 rows outside
# (shift-defi +4448.5%, monolith-market +162.9%, nuva +160.8%, anemoy-capital -72.7%);
# without this, shift-defi's +4448% drives its logit to -inf and its odds to ~0.
N_CHG_CLIPPED = sum(1 for p in prots if p['change_7d'] is not None and
                    (p['change_7d'] < CHG_LO or p['change_7d'] > CHG_HI))

def logi_feats(rows, med_chg, med_logage):
    X = []
    for p in rows:
        la = math.log(age_days(p)) if age_days(p) is not None else med_logage
        la = min(la, LOGAGE_P99)  # winsorise age at 99th pct (cap at oldest ages)
        ch = p['change_7d'] if p['change_7d'] is not None else med_chg
        ch = min(max(ch, CHG_LO), CHG_HI)
        X.append([math.log(p['tvl_usd']), la,
                  0.0 if age_days(p) is not None else 1.0, ch,
                  0.0 if p['change_7d'] is not None else 1.0, peers_rate(p)])
    return np.array(X, dtype=float)

FEAT_NAMES = ['log_tvl', 'log_age_wins', 'age_missing', 'change_7d', 'change_missing', 'peers_token_rate']

def fit_logit(X, y, lam=1.0):
    mu, sd = X.mean(axis=0), X.std(axis=0); sd[sd == 0] = 1.0
    Xs = (X - mu) / sd
    def nll(th):
        b0, b = th[0], th[1:]
        z = b0 + Xs @ b
        ll = np.sum(y * (-np.logaddexp(0, -z)) + (1 - y) * (-np.logaddexp(0, z)))
        return -ll + lam * float(b @ b)
    res = minimize(nll, np.zeros(X.shape[1] + 1), method='L-BFGS-B',
                   options={'maxiter': 500})
    return {'b0': float(res.x[0]), 'b': res.x[1:].tolist(), 'mu': mu.tolist(),
            'sd': sd.tolist(), 'success': bool(res.success)}
def pred_logit(model, X):
    Xs = (X - np.array(model['mu'])) / np.array(model['sd'])
    z = model['b0'] + Xs @ np.array(model['b'])
    return 1.0 / (1.0 + np.exp(-z))

def brier(p, y): return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))

y_all = np.array([0 if notoken(p) else 1 for p in prots])
X_all = logi_feats(prots, MED_CHG_ALL, MED_LOGAGE_ALL)
logit_full = fit_logit(X_all, y_all)
print("logistic coefs (standardised):",
      {n: round(float(b), 3) for n, b in zip(FEAT_NAMES, logit_full['b'])},
      "intercept", round(logit_full['b0'], 3))

# held-out (a): time split, listed_at non-null, train <2024, test >=2024
dated = [p for p in prots if p['listed_at']]
tr_l = [p for p in dated if p['listed_at'] < '2024-01-01']
te_l = [p for p in dated if p['listed_at'] >= '2024-01-01']
med_chg_tr = med([p['change_7d'] for p in tr_l if p['change_7d'] is not None])
med_la_tr = med([math.log(age_days(p)) for p in tr_l if age_days(p) is not None])
m_tr = fit_logit(logi_feats(tr_l, med_chg_tr, med_la_tr),
                 np.array([0 if notoken(p) else 1 for p in tr_l]))
p_te = pred_logit(m_tr, logi_feats(te_l, med_chg_tr, med_la_tr))
y_te = np.array([0 if notoken(p) else 1 for p in te_l])
base_rate_tr = float(np.mean([0 if notoken(p) else 1 for p in tr_l]))
brier_te = brier(p_te, y_te); brier_base = brier(np.full(len(y_te), base_rate_tr), y_te)
print(f"logistic time-split: train n={len(tr_l)} test n={len(te_l)} "
      f"Brier={brier_te:.4f} base-rate Brier={brier_base:.4f} "
      f"mean pred={float(np.mean(p_te)):.3f} observed={float(np.mean(y_te)):.3f}")
# decile reliability on the time-split test set
order = np.argsort(p_te); dec = {}
for d in range(10):
    idx = order[d * len(order)//10:(d+1) * len(order)//10]
    if len(idx):
        dec[d+1] = {'n': int(len(idx)), 'mean_pred': round(float(np.mean(p_te[idx])), 3),
                    'observed': round(float(np.mean(y_te[idx])), 3)}
print("  deciles:", dec)
# 5-fold random CV Brier (seed 42)
rng2 = np.random.default_rng(42); perm = rng2.permutation(len(prots))
cv_briers, cv_base = [], []
for f in range(5):
    te_idx = perm[f::5]; tr_idx = np.array([i for i in perm if i not in set(te_idx.tolist())])
    tr_r = [prots[i] for i in tr_idx]; te_r = [prots[i] for i in te_idx]
    mc = med([p['change_7d'] for p in tr_r if p['change_7d'] is not None])
    ml = med([math.log(age_days(p)) for p in tr_r if age_days(p) is not None])
    m = fit_logit(logi_feats(tr_r, mc, ml), np.array([0 if notoken(p) else 1 for p in tr_r]))
    pp = pred_logit(m, logi_feats(te_r, mc, ml))
    yy = np.array([0 if notoken(p) else 1 for p in te_r])
    br = float(np.mean([0 if notoken(p) else 1 for p in tr_r]))
    cv_briers.append(brier(pp, yy)); cv_base.append(brier(np.full(len(yy), br), yy))
print(f"logistic 5-fold CV Brier={float(np.mean(cv_briers)):.4f} (folds "
      f"{[round(x,4) for x in cv_briers]}), base-rate {float(np.mean(cv_base)):.4f}")

# cap odds at oldest cohort: protocols listed before 2022-01-01
oldest = [p for p in prots if p['listed_at'] and p['listed_at'] < '2022-01-01']
oldest_rate = float(np.mean([0 if notoken(p) else 1 for p in oldest]))
p_nt_raw = pred_logit(logit_full, logi_feats(nt, MED_CHG_ALL, MED_LOGAGE_ALL))
p_nt = np.minimum(p_nt_raw, oldest_rate)
n_capped = int(np.sum(p_nt_raw > oldest_rate))
print(f"oldest cohort (listed<2022): n={len(oldest)} token rate={oldest_rate:.3f}; "
      f"no-token rows capped: {n_capped} of {len(nt)}")
print(f"launch odds on no-token: min={float(p_nt.min()):.3f} median={float(np.median(p_nt)):.3f} "
      f"max={float(p_nt.max()):.3f}")

# ---- expected value + EV rank ranges (bootstrap fitted x fixed odds) ----
ev_nt = fitted_mcap_nt * p_nt
boot_ev = boot_preds.copy()
for b in range(200):
    boot_ev[b] = np.exp(boot_preds[b]) * p_nt
boot_ev_ranks = np.array([ordinal_ranks_desc(r) for r in boot_ev])
ev_rank_lo_b = np.percentile(boot_ev_ranks, 5, axis=0).astype(int)
ev_rank_hi_b = np.percentile(boot_ev_ranks, 95, axis=0).astype(int)
spans40_ev = (ev_rank_lo_b <= 40) & (ev_rank_hi_b > 40)
spans200_ev = (ev_rank_lo_b <= 200) & (ev_rank_hi_b > 200)
print(f"EV rank ranges: median width {int(np.median(ev_rank_hi_b - ev_rank_lo_b))}; "
      f"spanning top-40: {int(spans40_ev.sum())}; spanning board-200: {int(spans200_ev.sum())}")
print("  top-40 EV spanners:", [nt_slugs[i] for i in np.where(spans40_ev)[0]])

# ---- board: 198 eligible by EV + 2 lowest-EV ineligible fillers ----
order_ev = np.argsort(-ev_nt, kind='stable')
elig_idx = [i for i in order_ev if not reasons(nt[i])]
assert len(elig_idx) == 198
board_idx = elig_idx[:]  # ranks 1..198
inelig_idx = [i for i in order_ev if reasons(nt[i])]
fillers = inelig_idx[-2:]  # lowest EV among ineligible
board_idx += fillers
print("fillers (ranks 199-200):", [(nt_slugs[i], reasons(nt[i]), round(float(ev_nt[i]), 0))
                                    for i in fillers])
rank198_ev = float(ev_nt[board_idx[197]])
capped_fillers = []
for i in fillers:
    if ev_nt[i] > rank198_ev:
        capped_fillers.append(nt_slugs[i])
print("fillers needing implied-value cap to keep monotonicity:", capped_fillers)

# ---- costed farm plan (ASSUMPTIONS — not snapshot data; see MODEL.md) ----
GAS = {'Ethereum': 12.00, 'Solana': 0.05, 'Base': 0.50, 'Arbitrum': 0.50,
       'Optimism': 0.50, 'Polygon': 0.50}
TXS = 10            # 1 deposit + 8 weekly interactions + 1 claim/exit
DEPOSIT = 250.00    # working capital, returned on exit
BRIDGE_FEE = 12.00  # assumed flat, only when >1 chain
APR, WEEKS = 0.05, 12
AIRDROP_POOL_SHARE = 0.05   # assumed: 5% of supply airdropped
ASSUMED_FARMERS = 5000      # assumed farmers sharing the pool
RECEIPT_SHARE = AIRDROP_POOL_SHARE / ASSUMED_FARMERS  # 1e-5 of EV

def farm_plan(p, ev):
    chain0 = p['chains'][0] if p['chains'] else 'Ethereum'
    gas = GAS.get(chain0, 2.00)
    gas_total = TXS * gas
    bridge = BRIDGE_FEE if len(p['chains']) > 1 else 0.00
    opp = DEPOSIT * APR * WEEKS / 52
    cost = gas_total + bridge + opp
    hours = 3.0 + 0.5 * len(p['chains'])
    receipt = ev * RECEIPT_SHARE
    dph = (receipt - cost) / hours
    be_share = cost / ev * 100 if ev > 0 else float('inf')
    steps = [
        f"Open {p['name']} on {chain0} with a fresh wallet funded with $250 in stablecoins plus "
        f"${gas_total:.2f} set aside for gas; budget about {hours:.1f} hours over 12 weeks and "
        f"${cost:.2f} in out-of-pocket costs before the $250 deposit is returned.",
        f"Deposit the $250 into {p['name']}'s {p['category']} product on {chain0} in one "
        f"transaction, keep the transaction hash, and confirm the position shows in the "
        f"protocol's own interface before doing anything else.",
        f"Use {p['name']} once a week for 8 weeks — one real interaction each week, about 15 "
        f"minutes and about ${gas:.2f} in gas — and vary the action (deposit, withdraw, swap or "
        f"stake) rather than repeating the same click.",
        f"Keep a dated log of every transaction hash, amount and week number, and check "
        f"{p['name']}'s TVL (snapshot ${p['tvl_usd']:,.0f}) and official announcements weekly; "
        f"stop and withdraw if the protocol pauses deposits or changes terms.",
        f"If {p['name']} ever records a token, follow its official claim page only, claim once, "
        f"then withdraw the $250 deposit; if no token is recorded after 12 weeks, withdraw and "
        f"close the position — the $250 is working capital, not a fee.",
    ]
    return steps, {'gas_per_tx_usd': gas, 'tx_count': TXS, 'gas_total_usd': round(gas_total, 2),
                   'bridge_fee_usd': bridge, 'deposit_usd': DEPOSIT,
                   'opportunity_cost_usd': round(opp, 2), 'total_cost_usd': round(cost, 2),
                   'hours': hours, 'expected_receipt_usd': round(receipt, 2),
                   'break_even_share_pct': round(be_share, 6), 'dollars_per_hour': round(dph, 2)}

rows = []
for rank, i in enumerate(board_idx, start=1):
    p = nt[i]
    ev = float(ev_nt[i])
    implied = int(round(ev))
    if rank > 198 and capped_fillers and p['slug'] in capped_fillers:
        implied = int(round(rank198_ev))
    steps, costd = farm_plan(p, ev)
    excl = reasons(p)
    if p['slug'] in OPAQUE20:
        excl = excl + ['parentProtocol: house watchlist rule (field absent from snapshot)']
    if excl:
        verdict = 'skip'
    elif costd['dollars_per_hour'] >= 25:
        verdict = 'farm'
    elif costd['dollars_per_hour'] >= 0:
        verdict = 'thin'
    else:
        verdict = 'skip'
    rows.append({
        'slug': p['slug'], 'name': p['name'], 'rank': rank,
        'implied_value_usd': implied, 'farm_steps': steps,
        'watchlist': p['slug'] in WLSET, 'eligible': not reasons(p),
        'known_parentprotocol_exclusion': p['slug'] in OPAQUE20,
        'exclusion_reasons': excl,
        'tvl_usd': p['tvl_usd'], 'category': p['category'], 'chains': p['chains'],
        'age_days': age_days(p), 'change_7d': p['change_7d'],
        'fitted_mcap_usd': round(float(fitted_mcap_nt[i]), 2),
        'launch_odds': round(float(p_nt[i]), 4),
        'expected_value_usd': round(ev, 2),
        'rank_lo_boot_fitted': int(rank_lo_b[i]), 'rank_hi_boot_fitted': int(rank_hi_b[i]),
        'rank_lo_loo_fitted': int(rank_lo_loo[i]), 'rank_hi_loo_fitted': int(rank_hi_loo[i]),
        'rank_lo_boot_ev': int(ev_rank_lo_b[i]), 'rank_hi_boot_ev': int(ev_rank_hi_b[i]),
        'spans_top40_ev': bool(spans40_ev[i]), 'spans_board200_ev': bool(spans200_ev[i]),
        'implied_value_capped': bool(rank > 198 and p['slug'] in capped_fillers),
        'farm_cost': costd, 'verdict': verdict,
    })

# ---- validation (gate-shaped) ----
errs = []
assert len(rows) == 200, len(rows)
assert sorted(r['rank'] for r in rows) == list(range(1, 201))
assert len({r['slug'] for r in rows}) == 200
assert WLSET <= {r['slug'] for r in rows}
vals = [r['implied_value_usd'] for r in rows]
assert all(v > 0 and v <= 10**14 for v in vals)
assert all(vals[i] >= vals[i+1] for i in range(199)), "implied values must not rise with rank"
assert len(set(vals)) > 1
for r in rows:
    fs = r['farm_steps']
    assert 3 <= len(fs) <= 12
    for s in fs:
        assert 20 <= len(s.strip()) <= 600, (r['slug'], len(s))
    assert r['slug'] in by_slug
    assert r['name']
print("board validation: 200 rows, ranks 1..200 unique, all 40 watchlist present, "
      "implied values non-increasing, farm steps 3-12 x 20-600 chars — PASS")
verdicts = Counter(r['verdict'] for r in rows)
print("verdicts:", dict(verdicts))
print("top 10:", [(r['rank'], r['slug'], r['implied_value_usd'], r['launch_odds'],
                    r['verdict']) for r in rows[:10]])
print("bottom 5:", [(r['rank'], r['slug'], r['implied_value_usd'], r['verdict'],
                      r['exclusion_reasons']) for r in rows[-5:]])

board = {'board': 'token-radar-01 draft — @finchbetter',
         'as_of': snap['as_of'], 'source': snap['source'],
         'model': 'log(mcap_usd) = 9.1133 + 0.3940 * log(tvl_usd); EV = fitted mcap x launch odds',
         'n_rows': 200, 'rows': rows}
json.dump(board, open(f'{BASE}/board.json', 'w'), indent=1)
print("board.json bytes:", len(json.dumps(board)))

results = {
    'final_model': {'terms': p1['kept_terms'], 'coefs': p1['final_coefs'],
                    'insample': p1['final_insample']},
    'term_survival': p1['surv'], 'heldout_time': p1['res_a'], 'heldout_loco': p1['res_b'],
    'loco_detail': p1['loco_detail'], 'walk_forward': p1['wf'], 'wf_pooled': p1['wf_pooled'],
    'n_train_time': p1['n_train_time'], 'n_test_time': p1['n_test_time'],
    'n_null_time': p1['n_null_time'],
    'logistic': {'features': FEAT_NAMES,
                 'coefs_standardised': {n: round(float(b), 4) for n, b in zip(FEAT_NAMES, logit_full['b'])},
                 'intercept': round(logit_full['b0'], 4),
                 'time_split': {'n_train': len(tr_l), 'n_test': len(te_l), 'brier': round(brier_te, 4),
                                'base_rate_brier': round(brier_base, 4),
                                'mean_pred': round(float(np.mean(p_te)), 3),
                                'observed': round(float(np.mean(y_te)), 3), 'deciles': dec},
                 'cv5_brier_mean': round(float(np.mean(cv_briers)), 4),
                 'cv5_brier_folds': [round(x, 4) for x in cv_briers],
                 'cv5_base_mean': round(float(np.mean(cv_base)), 4),
                 'oldest_cohort_n': len(oldest), 'oldest_cohort_rate': round(oldest_rate, 4),
                 'n_capped': n_capped, 'logage_p99': round(LOGAGE_P99, 4),
                 'chg_winsorised_to': [CHG_LO, CHG_HI], 'n_chg_clipped': N_CHG_CLIPPED,
                 'med_change_all': MED_CHG_ALL, 'med_logage_all': MED_LOGAGE_ALL,
                 'odds_on_notoken': {'min': round(float(p_nt.min()), 4),
                                     'median': round(float(np.median(p_nt)), 4),
                                     'max': round(float(p_nt.max()), 4)}},
    'rank_ranges': {'median_boot_width_fitted': int(np.median(rank_hi_b - rank_lo_b)),
                    'median_boot_width_ev': int(np.median(ev_rank_hi_b - ev_rank_lo_b)),
                    'n_spans_top40_fitted': int(spans40_fit.sum()),
                    'spans_top40_fitted_slugs': [nt_slugs[i] for i in np.where(spans40_fit)[0]],
                    'n_spans_top40_ev': int(spans40_ev.sum()),
                    'spans_top40_ev_slugs': [nt_slugs[i] for i in np.where(spans40_ev)[0]],
                    'n_spans_board200_ev': int(spans200_ev.sum()),
                    'spans_board200_ev_slugs': [nt_slugs[i] for i in np.where(spans200_ev)[0]]},
    'board': {'n_rows': 200, 'n_watchlist': 40, 'n_eligible': 198, 'n_fillers': 2,
              'filler_slugs': [nt_slugs[i] for i in fillers],
              'capped_fillers': capped_fillers,
              'n_opaque20_in_board': int(sum(1 for r in rows if r['known_parentprotocol_exclusion'])),
              'opaque20_in_board': [r['slug'] for r in rows if r['known_parentprotocol_exclusion']],
              'verdicts': dict(verdicts),
              'implied_top1': rows[0]['implied_value_usd'],
              'implied_rank200': rows[-1]['implied_value_usd']},
    'census': {'total': 758, 'token_bearing': 416, 'no_token': 342,
               'no_token_eligible': 198, 'no_token_ineligible': 144,
               'mcap_present': 144, 'mcap_zero': 15, 'mcap_gt0': 128,
               'comps_excluded_wrapped': 36, 'comps_clean': 92,
               'excl_comp_tags': p1['excl_comp_tags'], 'inelig_tags': p1['inelig_tags']},
}
json.dump(results, open(f'{BASE}/fit_results.json', 'w'), indent=1)
print("fit_results.json saved")
