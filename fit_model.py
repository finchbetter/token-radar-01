#!/usr/bin/env python3
"""Token Radar value model — draft fit for @finchbetter, bounty token-radar-01.
Reads ONLY kit/input/snapshot.json (frozen DefiLlama 2026-11-14).
No submission, no GitHub repo, no skill.md. All numbers are computed here;
nothing is invented. Cost figures in the farm plans are stated ASSUMPTIONS,
labelled as such in MODEL.md — they are not snapshot data.
"""
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
WL = list(snap['watchlist'])
WLSET = set(WL)

EXCH = ['Binance', 'Coinbase', 'Bybit', 'Kraken', 'Bitget', 'OKX', 'Bitfinex', 'Gemini']
EXCL_CAT = {'Bridge', 'Canonical Bridge', 'Liquid Staking', 'Liquid Restaking', 'Restaked BTC', 'CEX'}
VER_RE = re.compile(r'\s(V\d+(\.\d+)?|v\d+(\.\d+)?|\d+\.\d+)$')
WRAP_RE = re.compile(r'\b(wrapped|staked|staking)\b', re.I)

def reasons(p):
    r = []
    if p['category'] in EXCL_CAT:
        r.append('category:' + p['category'])
    if WRAP_RE.search(p['name']):
        r.append('wrapped/staked-word')
    if any(p['name'].startswith(e) for e in EXCH):
        r.append('exchange-prefix')
    if VER_RE.search(p['name']):
        r.append('versioned-name')
    return r

def notoken(p):
    return p['gecko_id'] is None and p['symbol'] is None

def age_days(p):
    return (ASOF - date.fromisoformat(p['listed_at'])).days if p['listed_at'] else None

def med(v):
    return float(np.median(np.array(v, dtype=float)))

def r2_oos(y, pred):
    y = np.asarray(y, float); pred = np.asarray(pred, float)
    ss_res = float(np.sum((y - pred) ** 2)); ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')

def medae(y, pred):
    return float(np.median(np.abs(np.asarray(y, float) - np.asarray(pred, float))))

# ---------------------------------------------------------------- census
nt = [p for p in prots if notoken(p)]
tb = [p for p in prots if not notoken(p)]
elig_nt = [p for p in nt if not reasons(p)]
inelig_nt = [p for p in nt if reasons(p)]
mcap_present = [p for p in prots if p['mcap_usd'] is not None]
mcap_zero = [p for p in mcap_present if p['mcap_usd'] == 0]
comps_raw = [p for p in prots if p['mcap_usd'] and p['mcap_usd'] > 0]
excl_comps = [p for p in comps_raw if reasons(p)]
clean = [p for p in comps_raw if not reasons(p)]
excl_reason_tags = Counter()
for p in excl_comps:
    for r in reasons(p):
        excl_reason_tags[r] += 1
inelig_tags = Counter()
for p in inelig_nt:
    for r in reasons(p):
        inelig_tags[r] += 1

print(f"census: total={len(prots)} token-bearing={len(tb)} no-token={len(nt)}")
print(f"no-token eligible={len(elig_nt)} ineligible={len(inelig_nt)}")
print(f"mcap present={len(mcap_present)} zero={len(mcap_zero)} >0={len(comps_raw)}")
print(f"comps raw={len(comps_raw)} excluded-wrapped/staked={len(excl_comps)} clean={len(clean)}")
print("excluded-comp reason tags:", dict(excl_reason_tags))
print("ineligible no-token reason tags:", dict(inelig_tags))
print("clean comps listed_at null:", sum(1 for p in clean if p['listed_at'] is None),
      "change_7d null:", sum(1 for p in clean if p['change_7d'] is None))
print("no-token listed_at null:", sum(1 for p in nt if p['listed_at'] is None),
      "change_7d null:", sum(1 for p in nt if p['change_7d'] is None))

# ---------------------------------------------------------------- design
CAT_MIN = 4
cat_counts = Counter(p['category'] for p in clean)
POOLED = sorted([c for c, n in cat_counts.items() if n >= CAT_MIN])
print("pooled categories (n>=4 in clean comps):", [(c, cat_counts[c]) for c in POOLED])
print("other categories pooled into reference 'Other':",
      sorted(set(p['category'] for p in clean) - set(POOLED)))
MED_CHG = med([p['change_7d'] for p in clean if p['change_7d'] is not None])
MED_LOGAGE = med([math.log(age_days(p)) for p in clean if age_days(p) is not None])
print(f"median change_7d (clean comps)={MED_CHG:.4f}  median log-age={MED_LOGAGE:.4f}")

def cat_group(cat):
    return cat if cat in POOLED else 'Other'

def encode(rows, terms):
    """terms subset of ['logtvl','cat','chg','age']. Returns X, colnames."""
    cols, names = [], ['const']
    n = len(rows)
    cols.append(np.ones(n))
    if 'logtvl' in terms:
        cols.append(np.array([math.log(p['tvl_usd']) for p in rows])); names.append('log_tvl')
    if 'cat' in terms:
        for c in POOLED:
            cols.append(np.array([1.0 if cat_group(p['category']) == c else 0.0 for p in rows]))
            names.append('cat:' + c)
    if 'chg' in terms:
        cols.append(np.array([(p['change_7d'] if p['change_7d'] is not None else MED_CHG)
                              for p in rows])); names.append('change_7d')
    if 'age' in terms:
        cols.append(np.array([(math.log(age_days(p)) if age_days(p) is not None else MED_LOGAGE)
                              for p in rows])); names.append('log_age')
        cols.append(np.array([0.0 if age_days(p) is not None else 1.0 for p in rows]))
        names.append('age_missing')
    return np.column_stack(cols), names

def ols_fit(rows, terms):
    y = np.array([math.log(p['mcap_usd']) for p in rows])
    X, names = encode(rows, terms)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return {'beta': beta, 'names': names, 'terms': terms,
            'resid_sd': float(np.std(resid, ddof=X.shape[1])), 'n': len(rows)}

def ols_pred(model, rows):
    X, _ = encode(rows, model['terms'])
    return X @ model['beta']

def flat_pred(train_rows, test_rows):
    """Flat-multiple baseline: log(mcap) = log(TVL) + median(log(mcap/TVL)) on train."""
    c = med([math.log(p['mcap_usd']) - math.log(p['tvl_usd']) for p in train_rows])
    return np.array([math.log(p['tvl_usd']) + c for p in test_rows]), c

def eval_all(models, train_rows, test_rows, label):
    y = np.array([math.log(p['mcap_usd']) for p in test_rows])
    out = {}
    bp, bc = flat_pred(train_rows, test_rows)
    out['M0_flat'] = {'medae': medae(y, bp), 'r2': r2_oos(y, bp), 'n_test': len(test_rows)}
    for k, m in models.items():
        pr = ols_pred(m, test_rows)
        out[k] = {'medae': medae(y, pr), 'r2': r2_oos(y, pr), 'n_test': len(test_rows)}
    print(f"[{label}] " + " | ".join(
        f"{k}: MedAE={v['medae']:.3f} R2={v['r2']:.3f}" for k, v in out.items()))
    return out

# ---------------------------------------------------------------- models
SPECS = {
    'M1_tvl': ['logtvl'],
    'M2_tvl+cat': ['logtvl', 'cat'],
    'M3_+chg': ['logtvl', 'cat', 'chg'],
    'M4_+age': ['logtvl', 'cat', 'chg', 'age'],
}
full = {k: ols_fit(clean, v) for k, v in SPECS.items()}
for k, m in full.items():
    y = np.array([math.log(p['mcap_usd']) for p in clean])
    pr = ols_pred(m, clean)
    print(f"FULL {k}: in-sample MedAE={medae(y, pr):.3f} residSD={m['resid_sd']:.3f} "
          f"R2={r2_oos(y, pr):.3f}")
    print("   coefs:", {n: round(float(b), 3) for n, b in zip(m['names'], m['beta'])})

# ---- held-out (a): time split by listed_at, older train / newer test
cut = '2024-01-01'
tr_a = [p for p in clean if p['listed_at'] and p['listed_at'] < cut]
te_a = [p for p in clean if p['listed_at'] and p['listed_at'] >= cut]
null_a = [p for p in clean if not p['listed_at']]
print(f"time split: train(listed<{cut}) n={len(tr_a)}, test(>={cut}) n={len(te_a)}, "
      f"listed_at-null excluded n={len(null_a)}")
fit_a = {k: ols_fit(tr_a, v) for k, v in SPECS.items()}
res_a = eval_all(fit_a, tr_a, te_a, 'time-split older->newer')

# ---- held-out (b): leave-one-category-group-out (pooled groups + Other)
groups = POOLED + ['Other']
loco_rows = []  # (true y, pred per model, group)
loco_detail = {}
for g in groups:
    te = [p for p in clean if cat_group(p['category']) == g]
    tr = [p for p in clean if cat_group(p['category']) != g]
    if not te:
        continue
    fits = {k: ols_fit(tr, v) for k, v in SPECS.items()}
    y = np.array([math.log(p['mcap_usd']) for p in te])
    bp, _ = flat_pred(tr, te)
    d = {'n': len(te), 'M0_flat': {'medae': medae(y, bp), 'r2': r2_oos(y, bp)}}
    for k, m in fits.items():
        pr = ols_pred(m, te)
        d[k] = {'medae': medae(y, pr), 'r2': r2_oos(y, pr)}
    loco_detail[g] = d
    for k in list(SPECS) + ['M0_flat']:
        pass
    loco_rows.append((g, te, fits, tr))
# pooled LOCO: collect all test predictions
def pooled_loco():
    out = {}
    ys, preds = {}, {}
    for g, te, fits, tr in loco_rows:
        y = np.array([math.log(p['mcap_usd']) for p in te])
        ys.setdefault('y', []).append(y)
        bp, _ = flat_pred(tr, te)
        preds.setdefault('M0_flat', []).append(bp)
        for k, m in fits.items():
            preds.setdefault(k, []).append(ols_pred(m, te))
    yall = np.concatenate(ys['y'])
    for k, plist in preds.items():
        pall = np.concatenate(plist)
        out[k] = {'medae': medae(yall, pall), 'r2': r2_oos(yall, pall), 'n_test': len(yall)}
    return out
res_b = pooled_loco()
print("[LOCO pooled] " + " | ".join(f"{k}: MedAE={v['medae']:.3f} R2={v['r2']:.3f}"
                                    for k, v in res_b.items()))
for g, d in loco_detail.items():
    print(f"  LOCO group {g} (n={d['n']}): " + " | ".join(
        f"{k}: MedAE={v['medae']:.2f} R2={v['r2']:.2f}" for k, v in d.items() if k != 'n'))

# ---- term survival: each added term must beat the model without it on BOTH tests (MedAE)
def survives(new_key, old_key):
    a_ok = res_a[new_key]['medae'] < res_a[old_key]['medae']
    b_ok = res_b[new_key]['medae'] < res_b[old_key]['medae']
    return a_ok and b_ok, a_ok, b_ok
surv = {}
for new, old, term in [('M2_tvl+cat', 'M1_tvl', 'category'),
                       ('M3_+chg', 'M2_tvl+cat', 'change_7d'),
                       ('M4_+age', 'M3_+chg', 'age')]:
    s, a_ok, b_ok = survives(new, old)
    surv[term] = {'survives_both': bool(s), 'time_split_better': bool(a_ok),
                  'loco_better': bool(b_ok),
                  'd_medae_time': round(res_a[old]['medae'] - res_a[new]['medae'], 4),
                  'd_medae_loco': round(res_b[old]['medae'] - res_b[new]['medae'], 4)}
    print(f"term {term}: survives={s} (time {a_ok}, loco {b_ok}) "
          f"dMedAE time={surv[term]['d_medae_time']:+.3f} loco={surv[term]['d_medae_loco']:+.3f}")
kept_terms = ['logtvl']
if surv['category']['survives_both']:
    kept_terms.append('cat')
if surv['change_7d']['survives_both']:
    kept_terms.append('chg')
if surv['age']['survives_both']:
    kept_terms.append('age')
print("FINAL SPEC terms:", kept_terms)
final_model = ols_fit(clean, kept_terms)
y_clean = np.array([math.log(p['mcap_usd']) for p in clean])
pr_clean = ols_pred(final_model, clean)
final_insample = {'medae': medae(y_clean, pr_clean), 'r2': r2_oos(y_clean, pr_clean),
                  'resid_sd': final_model['resid_sd']}
print("FINAL full-fit coefs:", {n: round(float(b), 4) for n, b in
                                zip(final_model['names'], final_model['beta'])})
print("FINAL in-sample:", final_insample)

# ---- walk-forward: expanding listed_at cohorts, test next cohort
wf_folds = [ ('<=2022', '2023', '2022-12-31', '2023-01-01', '2024-01-01'),
             ('<=2023', '2024', '2023-12-31', '2024-01-01', '2025-01-01'),
             ('<=2024', '2025-26', '2024-12-31', '2025-01-01', '2099-01-01') ]
wf = []
for label_tr, label_te, cut_tr, lo, hi in wf_folds:
    tr = [p for p in clean if p['listed_at'] and p['listed_at'] <= cut_tr]
    te = [p for p in clean if p['listed_at'] and lo <= p['listed_at'] < hi]
    if len(tr) < 10 or len(te) < 3:
        wf.append({'train': label_tr, 'test': label_te, 'n_train': len(tr), 'n_test': len(te),
                   'note': 'too few rows, skipped'})
        continue
    m = ols_fit(tr, kept_terms)
    y = np.array([math.log(p['mcap_usd']) for p in te])
    pr = ols_pred(m, te)
    bp, _ = flat_pred(tr, te)
    wf.append({'train': label_tr, 'test': label_te, 'n_train': len(tr), 'n_test': len(te),
               'medae': medae(y, pr), 'r2': r2_oos(y, pr),
               'baseline_medae': medae(y, bp), 'baseline_r2': r2_oos(y, bp)})
    print(f"WF train {label_tr} (n={len(tr)}) -> test {label_te} (n={len(te)}): "
          f"MedAE={wf[-1]['medae']:.3f} R2={wf[-1]['r2']:.3f} | flat MedAE={wf[-1]['baseline_medae']:.3f}")
# pooled walk-forward (all test rows across folds)
wf_y, wf_p, wf_b = [], [], []
for (label_tr, label_te, cut_tr, lo, hi), fold in zip(wf_folds, wf):
    if 'medae' not in fold:
        continue
    tr = [p for p in clean if p['listed_at'] and p['listed_at'] <= cut_tr]
    te = [p for p in clean if p['listed_at'] and lo <= p['listed_at'] < hi]
    m = ols_fit(tr, kept_terms)
    wf_y.append(np.array([math.log(p['mcap_usd']) for p in te]))
    wf_p.append(ols_pred(m, te))
    bp, _ = flat_pred(tr, te)
    wf_b.append(bp)
wf_pooled = {}
if wf_y:
    ya, pa, ba = np.concatenate(wf_y), np.concatenate(wf_p), np.concatenate(wf_b)
    wf_pooled = {'n_test': int(len(ya)), 'medae': medae(ya, pa), 'r2': r2_oos(ya, pa),
                 'baseline_medae': medae(ya, ba), 'baseline_r2': r2_oos(ya, ba)}
    print("WF pooled:", wf_pooled)

# save intermediate results for part 2
json.dump({
    'kept_terms': kept_terms, 'surv': surv,
    'res_a': res_a, 'res_b': res_b, 'loco_detail': loco_detail,
    'wf': wf, 'wf_pooled': wf_pooled, 'final_insample': final_insample,
    'final_coefs': {n: float(b) for n, b in zip(final_model['names'], final_model['beta'])},
    'pooled_cats': POOLED, 'med_chg': MED_CHG, 'med_logage': MED_LOGAGE,
    'n_clean': len(clean), 'n_comps_raw': len(comps_raw), 'n_excl_comps': len(excl_comps),
    'excl_comp_tags': dict(excl_reason_tags), 'inelig_tags': dict(inelig_tags),
    'n_train_time': len(tr_a), 'n_test_time': len(te_a), 'n_null_time': len(null_a),
}, open(f'{BASE}/fit_part1.json', 'w'), indent=1)
print("part 1 saved")
