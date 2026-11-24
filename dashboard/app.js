/* Token Radar dashboard: renders window.RADAR (written by main.ts) with no network.
   Views by hash: #<slug> opens that protocol's detail view; #filter=farm|thin|skip|
   watchlist shows a filtered board; anything else shows the full board. */
(function () {
  var R = window.RADAR;
  var main = document.getElementById('board');
  if (!R || !R.rows) {
    main.setAttribute('aria-busy', 'false');
    main.innerHTML = '<section><h2>Token Radar</h2><p>No radar data was loaded. main.ts writes data.js beside this page; open the built output, not this file on its own.</p></section>';
    return;
  }
  var rows = R.rows;
  var bySlug = {};
  rows.forEach(function (r) { bySlug[r.slug] = r; });
  var state = { q: '', verdict: 'all', watchlistOnly: false, category: 'all', sort: 'rank' };
  var cats = [];
  rows.forEach(function (r) { if (r.category && cats.indexOf(r.category) < 0) cats.push(r.category); });
  cats.sort();

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function money(n) {
    var s = String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return '$' + s;
  }
  function num(n, dp) { return Number(n).toFixed(dp); }
  function pct(n) { return (n * 100).toFixed(1) + '%'; }
  function pill(v) { return '<span class="pill ' + v + '">' + v + '</span>'; }
  function median(vals) {
    var s = vals.slice().sort(function (a, b) { return a - b; });
    var n = s.length;
    return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2;
  }

  function kpiHTML() {
    var k = R.kpi, v = k.verdicts;
    function tile(n, l) { return '<div class="kpi"><div class="n">' + n + '</div><div class="l">' + l + '</div></div>'; }
    return '<section aria-label="Key figures"><div class="kpis">'
      + tile(k.total_protocols, 'protocols in the sealed snapshot')
      + tile(k.no_token, 'record no token')
      + tile(k.watchlist_on_board + ' / 40', 'watchlist covered by the board')
      + tile(k.board_rows, 'rows on the board')
      + tile(v.farm + ' farm · ' + v.thin + ' thin · ' + v.skip + ' skip', 'farm verdicts')
      + tile(money(k.top_implied), 'top implied value (rank 1)')
      + '</div></section>';
  }

  function modelStripHTML() {
    var e = R.evidence;
    return '<section aria-label="Model in one line"><p style="margin:0"><b>Model:</b> '
      + '<span class="mono">' + esc(e.model.formula) + '</span> (n=92 clean comps) &nbsp;·&nbsp; '
      + '<b>Held-out MedAE</b> 0.712 vs flat 1.508 (time split) &nbsp;·&nbsp; '
      + '<b>Walk-forward pooled</b> 0.878 vs 1.584 &nbsp;·&nbsp; '
      + '<b>Launch-odds Brier</b> 0.252 vs 0.385 base rate &nbsp;·&nbsp; '
      + '<b>EV = fitted mcap &times; launch odds.</b> Category, growth and age were tested and dropped: none beats the flat baseline on both held-out tests.</p></section>';
  }

  function detailHTML(r) {
    var c = r.farm_cost;
    var reason = '';
    if (r.exclusion_reasons.length) {
      reason = '<p><b>Why skip:</b> ' + esc(r.exclusion_reasons.join('; ')) + '.</p>';
    } else if (r.verdict === 'farm') {
      reason = '<p><b>Why farm:</b> expected receipt ' + money(c.expected_receipt_usd) + ' covers the ' + money(c.total_cost_usd)
        + ' out-of-pocket cost at ' + money(c.dollars_per_hour) + '/hour over ' + c.hours + ' hours.</p>';
    } else if (r.verdict === 'thin') {
      reason = '<p><b>Why thin:</b> expected receipt ' + money(c.expected_receipt_usd) + ' just covers the ' + money(c.total_cost_usd)
        + ' cost at ' + money(c.dollars_per_hour) + '/hour — worth it only if your time is cheap.</p>';
    } else {
      reason = '<p><b>Why skip:</b> expected receipt ' + money(c.expected_receipt_usd) + ' does not cover the ' + money(c.total_cost_usd)
        + ' cost (' + money(c.dollars_per_hour) + '/hour).</p>';
    }
    var lo = r.rank_lo_boot_ev, hi = r.rank_hi_boot_ev;
    var left = ((lo - 1) / 199 * 100).toFixed(1), width = (Math.max(hi - lo, 1) / 199 * 100).toFixed(1);
    var mark = ((r.rank - 1) / 199 * 100).toFixed(1);
    var steps = r.farm_steps.map(function (s, i) { return '<li>' + esc(s) + '</li>'; }).join('');
    return '<section aria-label="Protocol detail"><p class="backlink"><a href="#">&larr; Back to the board</a></p>'
      + '<div class="detail-head"><h2>' + esc(r.name) + '</h2><span class="mono">' + esc(r.slug) + '</span>'
      + '<span>Rank #' + r.rank + '</span>' + pill(r.verdict)
      + (r.watchlist ? '<span class="badge">WATCHLIST</span>' : '')
      + (r.known_parentprotocol_exclusion ? '<span class="flag">parentProtocol exclusion (field absent from snapshot)</span>' : '')
      + '</div>'
      + '<div class="figs">'
      + '<div class="fig"><div class="n">' + money(r.implied_value_usd) + '</div><div class="l">implied value (rank ' + r.rank + ' of 200)</div></div>'
      + '<div class="fig"><div class="n">' + money(r.fitted_mcap_usd) + '</div><div class="l">fitted mcap — exp(9.1133 + 0.3940 · log TVL)</div></div>'
      + '<div class="fig"><div class="n">' + num(r.launch_odds, 4) + '</div><div class="l">launch odds (logistic, capped at 0.800)</div></div>'
      + '<div class="fig"><div class="n">' + money(r.tvl_usd) + '</div><div class="l">TVL · ' + esc(r.category || 'no category') + ' · ' + esc(r.chains.join(', ')) + '</div></div>'
      + '</div>'
      + '<div class="figs">'
      + '<div class="fig"><div class="n">' + money(c.dollars_per_hour) + '/h</div><div class="l">expected $/hour, ' + c.hours + ' h over 12 weeks</div></div>'
      + '<div class="fig"><div class="n">' + money(c.total_cost_usd) + '</div><div class="l">out-of-pocket cost ($' + c.deposit_usd + ' deposit returned)</div></div>'
      + '<div class="fig"><div class="n">' + money(c.expected_receipt_usd) + '</div><div class="l">expected farmer receipt (EV × 1e-5)</div></div>'
      + '<div class="fig"><div class="n">' + num(c.break_even_share_pct, 4) + '%</div><div class="l">break-even share of token supply</div></div>'
      + '</div>'
      + '<h3>Rank uncertainty — bootstrap EV rank, 5–95%</h3>'
      + '<div class="rangebar"><div class="span" style="left:' + left + '%;width:' + width + '%"></div><div class="mark" style="left:' + mark + '%"></div></div>'
      + '<div class="range-labels"><span>rank 1</span><span>interval ranks ' + lo + '–' + hi + (r.spans_top40_ev ? ' · spans the top-40 boundary' : '') + (r.spans_board200_ev ? ' · spans the board-200 boundary' : '') + '</span><span>rank 200</span></div>'
      + '<p class="small">Fitted-value rank range (bootstrap): ' + r.rank_lo_boot_fitted + '–' + r.rank_hi_boot_fitted
      + ' · leave-one-comp-out: ' + r.rank_lo_loo_fitted + '–' + r.rank_hi_loo_fitted
      + '. The fitted ranking is exactly the TVL ranking (the model is monotone in TVL), so the fitted ranges are degenerate; the honest uncertainty is the residual noise (SD 1.95 log points) and the odds, which is what the EV interval shows.'
      + (r.age_days == null ? ' Age unknown (listed_at null); odds use the median age.' : ' Age ' + r.age_days + ' days since first tracked.')
      + (r.change_7d == null ? ' 7-day change unreported.' : ' 7-day TVL change ' + num(r.change_7d, 2) + '%.')
      + '</p>' + reason
      + '<h3>How to farm it — 5 steps, costed</h3><ol class="steps">' + steps + '</ol>'
      + '<p class="small">Cost assumptions (not snapshot data): 10 transactions; gas by first chain (Ethereum $12, Solana $0.05, Base / Arbitrum / Optimism / Polygon $0.50, other $2); $12 bridge fee when the protocol spans more than one chain; $250 working capital returned on exit; opportunity cost 5% APR × 12 weeks. Each step says “if a token is ever recorded” — no airdrop is claimed to exist.</p>'
      + '</section>';
  }

  function filteredRows() {
    var out = rows.filter(function (r) {
      if (state.verdict !== 'all' && r.verdict !== state.verdict) return false;
      if (state.watchlistOnly && !r.watchlist) return false;
      if (state.category !== 'all' && r.category !== state.category) return false;
      if (state.q) {
        var q = state.q.toLowerCase();
        if (r.slug.indexOf(q) < 0 && r.name.toLowerCase().indexOf(q) < 0) return false;
      }
      return true;
    });
    var key = state.sort;
    out.sort(function (a, b) {
      if (key === 'tvl') return b.tvl_usd - a.tvl_usd;
      if (key === 'odds') return b.launch_odds - a.launch_odds;
      if (key === 'fitted') return b.fitted_mcap_usd - a.fitted_mcap_usd;
      if (key === 'dph') return b.farm_cost.dollars_per_hour - a.farm_cost.dollars_per_hour;
      return a.rank - b.rank;
    });
    return out;
  }

  function boardTableHTML(list) {
    var body = list.map(function (r) {
      return '<tr data-slug="' + esc(r.slug) + '" class="' + (r.watchlist ? 'watch' : '') + '">'
        + '<td>' + r.rank + '</td>'
        + '<td class="name"><b>' + esc(r.name) + '</b><span>' + esc(r.slug) + '</span></td>'
        + '<td>' + esc(r.category || '—') + '</td>'
        + '<td>' + esc(r.chains.slice(0, 2).join(', ')) + (r.chains.length > 2 ? ' +' + (r.chains.length - 2) : '') + '</td>'
        + '<td>' + money(r.tvl_usd) + '</td>'
        + '<td>' + money(r.fitted_mcap_usd) + '</td>'
        + '<td>' + num(r.launch_odds, 3) + '</td>'
        + '<td><b>' + money(r.implied_value_usd) + '</b></td>'
        + '<td class="' + (r.farm_cost.dollars_per_hour < 0 ? 'neg' : '') + '">' + money(r.farm_cost.dollars_per_hour) + '</td>'
        + '<td>' + pill(r.verdict) + '</td></tr>';
    }).join('');
    return '<div style="overflow-x:auto"><table class="board"><thead><tr>'
      + '<th>Rank</th><th>Protocol</th><th>Category</th><th>Chains</th><th>TVL</th><th>Fitted mcap</th><th>Odds</th><th>Implied value</th><th>$/hour</th><th>Verdict</th>'
      + '</tr></thead><tbody>' + body + '</tbody></table></div>';
  }

  function evidenceHTML() {
    var e = R.evidence;
    function heldoutRow(label, m, hl) {
      return '<tr' + (hl ? ' class="hl"' : '') + '><td>' + label + '</td><td>' + num(m.medae, 3) + '</td><td>' + num(m.r2, 3) + '</td></tr>';
    }
    function heldoutTable(title, h) {
      return '<h3>' + title + '</h3><p class="small">' + esc(h.label) + '. Median absolute log error (lower is better) and out-of-sample R². The shipped model is the log(TVL) row.</p>'
        + '<table class="ev"><thead><tr><th>Model</th><th>MedAE</th><th>OOS R²</th></tr></thead><tbody>'
        + heldoutRow('Flat multiple (mcap = TVL × median ratio)', h.flat, false)
        + heldoutRow('Shipped: log(TVL) only', h.shipped, true)
        + heldoutRow('+ category', h.m2_cat, false)
        + heldoutRow('+ change_7d', h.m3_chg, false)
        + heldoutRow('+ age', h.m4_age, false)
        + '</tbody></table>';
    }
    var wf = e.walk_forward.folds.map(function (f) {
      return '<tr><td>' + esc(f.train) + ' → ' + esc(f.test) + '</td><td>' + f.n_train + ' / ' + f.n_test + '</td><td>' + num(f.medae, 3) + '</td><td>' + num(f.r2, 3) + '</td><td>' + num(f.base_medae, 3) + '</td><td>' + num(f.base_r2, 3) + '</td></tr>';
    }).join('');
    var terms = e.term_survival.map(function (t) {
      return '<tr><td>' + esc(t.term) + '</td><td>' + num(t.d_medae_time, 3) + '</td><td>' + num(t.d_medae_loco, 3) + '</td><td>' + (t.survives_both ? 'kept' : 'DROPPED') + '</td></tr>';
    }).join('');
    var live = R.live.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.category || '—') + '</td><td>' + money(p.tvl_usd) + '</td><td>' + (p.mcap_usd == null ? '—' : money(p.mcap_usd)) + '</td></tr>';
    }).join('');
    var medFitWidth = median(rows.map(function (r) { return r.rank_hi_boot_fitted - r.rank_lo_boot_fitted; }));
    return '<section aria-label="Model and evidence"><h2>The model, and the evidence for it</h2>'
      + '<p><b>Value model.</b> <span class="mono">' + esc(e.model.formula) + '</span>, fitted on ' + e.model.n_clean_comps
      + ' clean comps (token-bearing protocols with mcap &gt; 0, wrapped / staked / bridged / CEX rows excluded). '
      + 'In-sample median absolute log error ' + e.model.insample_medae + ' (≈3.2×), R² ' + e.model.insample_r2
      + ', residual SD ' + e.model.resid_sd + ' log points. ' + esc(e.model.note) + '</p>'
      + '<p><b>Launch odds.</b> Logistic P(token-bearing) on all 758 protocols; features '
      + esc(e.logistic.features.join(', ')) + '; L2 penalty 1.0; odds capped at the oldest cohort rate ('
      + e.logistic.oldest_cohort.rate + ', n=' + e.logistic.oldest_cohort.n + ', ' + e.logistic.oldest_cohort.n_capped
      + ' rows capped). Odds on the no-token rows: ' + e.logistic.odds_on_notoken.min + ' – ' + e.logistic.odds_on_notoken.max
      + ', median ' + e.logistic.odds_on_notoken.median + '. This is cross-sectional token presence, not a launch-time hazard: the snapshot has no launch dates.</p>'
      + '<h3>Term survival — a term is kept only if it lowers MedAE on both held-out tests</h3>'
      + '<table class="ev"><thead><tr><th>Term added</th><th>ΔMedAE time split</th><th>ΔMedAE LOCO</th><th>Kept?</th></tr></thead><tbody>' + terms + '</tbody></table>'
      + heldoutTable('Held-out (a): time split', e.heldout_time)
      + heldoutTable('Held-out (b): leave-one-category-group-out', e.heldout_loco)
      + '<h3>Walk-forward — listed_at cohorts, expanding window</h3><p class="small">' + esc(e.walk_forward.label) + '. Pooled (n=54): MedAE ' + num(e.walk_forward.pooled.medae, 3) + ', R² ' + num(e.walk_forward.pooled.r2, 3) + ' vs flat baseline MedAE ' + num(e.walk_forward.pooled.base_medae, 3) + ', R² ' + num(e.walk_forward.pooled.base_r2, 3) + '. The shipped model beats the flat baseline in every fold and pooled.</p>'
      + '<table class="ev"><thead><tr><th>Fold</th><th>Train / test n</th><th>MedAE</th><th>R²</th><th>Flat MedAE</th><th>Flat R²</th></tr></thead><tbody>' + wf + '</tbody></table>'
      + '<h3>Launch-odds calibration</h3><p>Time-split Brier ' + e.logistic.time_split.brier + ' vs base-rate Brier ' + e.logistic.time_split.base_rate_brier
      + ' (train n=' + e.logistic.time_split.n_train + ', test n=' + e.logistic.time_split.n_test + '); mean predicted '
      + e.logistic.time_split.mean_pred + ' vs observed ' + e.logistic.time_split.observed + ' — ' + esc(e.logistic.time_split.note)
      + ' 5-fold random CV Brier ' + e.logistic.cv5.brier_mean + ' (folds ' + e.logistic.cv5.folds.join(', ') + ') vs base rate ' + e.logistic.cv5.base_mean
      + '. Treat the odds as relative scores for ranking, not as calibrated launch probabilities.</p>'
      + '<h3>Rank uncertainty — recomputed by main.ts at runtime</h3><p>200 bootstrap refits + 92 leave-one-comp-out refits of the value fit (bootstrap seed 42), over all 342 protocols that record no token. '
      + 'Median bootstrap EV rank width: ' + R.kpi.median_boot_width_ev + ' ranks; ' + R.kpi.n_spans_top40_ev
      + ' protocols span the top-40 boundary, ' + R.kpi.n_spans_board200_ev + ' span the board-200 boundary. '
      + 'Median bootstrap fitted-value rank width: ' + medFitWidth + ' ranks — degenerate, because the model is monotone in TVL, so coefficient resampling cannot reorder fitted values at all. The honest uncertainty is the residual noise (SD 1.95 log points, ≈7×), which would swamp any coefficient-based interval.</p>'
      + '<h3>Live tokens, set aside</h3><p class="small">These already trade, so the board shows the market\u2019s own values for them, never a model\u2019s. Top 12 by market cap (CEX excluded):</p>'
      + '<table class="ev"><thead><tr><th>Protocol</th><th>Category</th><th>TVL</th><th>Market cap</th></tr></thead><tbody>' + live + '</tbody></table>'
      + '</section>';
  }

  function integrityHTML() {
    var k = R.kpi, c = R.evidence.census;
    return '<section aria-label="Integrity"><h2>Integrity — every protocol accounted for</h2>'
      + '<div class="integrity"><span><b>758</b> protocols = <b>416</b> token-bearing + <b>342</b> record no token</span>'
      + '<span><b>342</b> no-token = <b>198</b> screen-eligible + <b>144</b> ineligible</span>'
      + '<span><b>92</b> clean comps (128 mcap &gt; 0, minus 36 wrapped / staked)</span>'
      + '<span><b>' + k.mcap_zero + '</b> rows record mcap = 0 (excluded from logs)</span>'
      + '<span><b>' + k.mcap_negative_sentinel + '</b> row records mcap = −1 (autofinance, a DefiLlama sentinel — excluded, disclosed)</span></div>'
      + '<p><span class="flag">FDV is absent from the snapshot — no fdv field on any row, so the model uses log(mcap_usd).</span> '
      + '<span class="flag">parentProtocol is absent — 20 watchlist exclusions cannot be re-derived; all 20 are flagged in the board and forced to skip.</span> '
      + '<span class="flag">listed_at null for ' + k.listed_at_null + ' rows; change_7d null for ' + k.change_7d_null + ' rows — imputed at medians with missing indicators where the odds model uses them.</span></p>'
      + '<p class="small">Wording rule, from the kit: a protocol “records no token”, never “has none” — a listed protocol may still have a token its DefiLlama record does not carry. The board\u2019s implied value is this entry\u2019s own claim, never make.fun\u2019s. No ranking, implied value, farm plan or airdrop flag exists in the snapshot; all are derived here, and no TVL, token or airdrop was invented for any row.</p>'
      + '</section>';
  }

  function renderShell() {
    var m = R.meta;
    main.setAttribute('aria-busy', 'false');
    main.innerHTML = '<header><h1>Token Radar</h1><p class="sub">Which pre-token protocol is worth farming next, and what do I do about it — ranked by expected value from the sealed DefiLlama snapshot of '
      + esc(m.as_of) + '. Entry <b>@finchbetter</b> for <b>token-radar-01</b> ($1,325, deadline 2026-12-14 10:00 UTC). Snapshot source: DefiLlama protocols, fetched 2026-11-14T01:18:33Z.</p></header>'
      + kpiHTML() + modelStripHTML()
      + '<div id="detail-slot"></div>'
      + '<section aria-label="Board"><h2>The board — 200 rows by implied value</h2>'
      + '<div class="controls">'
      + '<div><label for="q">Search name or slug</label><input id="q" type="search" placeholder="e.g. usdd, veda…" autocomplete="off"></div>'
      + '<div><label for="verdict">Verdict</label><select id="verdict"><option value="all">All verdicts</option><option value="farm">farm</option><option value="thin">thin</option><option value="skip">skip</option></select></div>'
      + '<div><label for="cat">Category</label><select id="cat"><option value="all">All categories</option>' + cats.map(function (c) { return '<option value="' + esc(c) + '">' + esc(c) + '</option>'; }).join('') + '</select></div>'
      + '<div><label for="sort">Sort display by</label><select id="sort"><option value="rank">Board rank</option><option value="tvl">TVL</option><option value="odds">Launch odds</option><option value="fitted">Fitted mcap</option><option value="dph">$/hour</option></select></div>'
      + '<label class="check"><input id="wl" type="checkbox"> Watchlist only</label>'
      + '</div><p class="count-line" id="count-line"></p><div id="table-slot"></div>'
      + '<p class="small">Sort reorders the display; Rank is the board\u2019s claim. Click any row for its detail view and farm plan. ★ marks a watchlist row. Ranks 199–200 are filler rows (the screen-eligible universe is 198); their implied values are capped at the rank-198 value.</p></section>'
      + evidenceHTML() + integrityHTML()
      + '<footer><p><b>Cost assumptions</b> (not snapshot data): 10 transactions; gas by first chain; $12 bridge fee when a protocol spans more than one chain; $250 working capital, returned on exit; opportunity cost 5% APR × 12 weeks; expected farmer receipt = EV × 1e-5 (5% of supply shared among 5,000 assumed farmers). Change the assumption and the verdicts move — the model says so.</p>'
      + '<p>Built by main.ts (Node 22, standard library only, offline, deterministic): it reads the sealed snapshot, refits nothing by hand — the fitted model in MODEL.md — and writes this page\u2019s data. Two runs write the same bytes.</p></footer>';
    document.getElementById('q').addEventListener('input', function (e) { state.q = e.target.value; renderTable(); });
    document.getElementById('verdict').addEventListener('change', function (e) {
      state.verdict = e.target.value;
      location.hash = state.verdict === 'all' ? '' : 'filter=' + state.verdict;
      renderTable();
    });
    document.getElementById('cat').addEventListener('change', function (e) { state.category = e.target.value; renderTable(); });
    document.getElementById('sort').addEventListener('change', function (e) { state.sort = e.target.value; renderTable(); });
    document.getElementById('wl').addEventListener('change', function (e) { state.watchlistOnly = e.target.checked; renderTable(); });
    document.getElementById('table-slot').addEventListener('click', function (e) {
      var tr = e.target.closest ? e.target.closest('tr[data-slug]') : null;
      if (tr) { location.hash = tr.getAttribute('data-slug'); }
    });
  }

  function renderTable() {
    var list = filteredRows();
    var slot = document.getElementById('table-slot');
    var count = document.getElementById('count-line');
    if (!slot) return;
    slot.innerHTML = boardTableHTML(list);
    count.textContent = 'Showing ' + list.length + ' of 200 rows'
      + (state.verdict !== 'all' ? ' · verdict: ' + state.verdict : '')
      + (state.watchlistOnly ? ' · watchlist only' : '')
      + (state.category !== 'all' ? ' · category: ' + state.category : '')
      + (state.q ? ' · matching "' + state.q + '"' : '') + '.';
  }

  function renderFromHash() {
    var h = location.hash.replace(/^#/, '');
    var slot = document.getElementById('detail-slot');
    if (!slot) return;
    var detail = null;
    if (h && h.indexOf('filter=') === 0) {
      var f = h.slice(7);
      if (f === 'farm' || f === 'thin' || f === 'skip') { state.verdict = f; state.watchlistOnly = false; }
      else if (f === 'watchlist') { state.verdict = 'all'; state.watchlistOnly = true; }
      var sel = document.getElementById('verdict'); if (sel) sel.value = state.verdict;
      var wl = document.getElementById('wl'); if (wl) wl.checked = state.watchlistOnly;
    } else if (h && bySlug[h]) {
      detail = bySlug[h];
    }
    slot.innerHTML = detail ? detailHTML(detail) : '';
    renderTable();
    if (detail) window.scrollTo(0, 0);
  }

  renderShell();
  renderFromHash();
  window.addEventListener('hashchange', renderFromHash);
})();
