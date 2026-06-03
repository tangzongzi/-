/* charts/商品日度追踪.js */
(async function() {
  const DATA = await fetch('../../数据/汇总/商品_日度追踪.json').then(r => r.json());
  const dates = DATA.summary.dates;
  let rows = DATA.data;

  // KPI strip
  const s = DATA.summary;
  const kpiHtml = [
    { label: '商品数', value: s.product_count, sub: '活跃' },
    { label: '增长', value: '↑' + s.up_count, sub: '连续3天' },
    { label: '下降', value: '↓' + s.down_count, sub: '连续3天' },
    { label: '新品', value: s.new_count || 0, sub: '≤7天' },
    { label: '衰退', value: s.decline_count || 0, sub: '预警' },
  ].map(k => '<div class="kpi-item"><span class="kpi-item-label">' + k.label + '</span><span class="kpi-item-value">' + k.value + '</span><span class="kpi-item-sub">' + k.sub + '</span></div>').join('');
  document.getElementById('kpi-strip').innerHTML = kpiHtml;

  // Badges
  document.getElementById('badge-count').textContent = rows.length + ' 个商品';
  document.getElementById('badge-trend').textContent = '↑' + s.up_count + ' ↓' + s.down_count;

  // 生命周期标签
  const lifecycleMap = {
    'new': { label: '新品', color: 'var(--primary)', bg: 'var(--primary-bg)' },
    'growth': { label: '成长', color: 'var(--success)', bg: 'var(--success-bg)' },
    'mature': { label: '成熟', color: 'var(--text-2)', bg: 'var(--bg-hover)' },
    'decline': { label: '衰退', color: 'var(--danger)', bg: 'var(--danger-bg)' },
  };

  // 控件
  const controlsHtml = '<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">' +
    '<input id="search-input" type="text" placeholder="搜索商品..." style="padding:6px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--bg-card);color:var(--text-1);font-size:13px;width:220px;">' +
    '<select id="sort-select" style="padding:6px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--bg-card);color:var(--text-1);font-size:13px;">' +
    '<option value="last_desc">昨日订单 ↓</option>' +
    '<option value="total_desc">总订单 ↓</option>' +
    '<option value="mom_desc">环比增长 ↓</option>' +
    '<option value="avg_desc">日均 ↓</option>' +
    '<option value="age_asc">新品优先</option>' +
    '<option value="decline">衰退预警</option>' +
    '</select>' +
    '<select id="lifecycle-filter" style="padding:6px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--bg-card);color:var(--text-1);font-size:13px;">' +
    '<option value="all">全部生命周期</option>' +
    '<option value="new">新品 (≤7天)</option>' +
    '<option value="growth">成长 (8-30天)</option>' +
    '<option value="mature">成熟 (>30天)</option>' +
    '<option value="decline">衰退预警</option>' +
    '</select>' +
    '<span id="filter-count" style="font-size:12px;color:var(--text-3);"></span>' +
    '</div>';
  document.getElementById('table-container').insertAdjacentHTML('beforebegin', controlsHtml);

  function render() {
    const search = document.getElementById('search-input').value.toLowerCase();
    const sort = document.getElementById('sort-select').value;
    const lifecycle = document.getElementById('lifecycle-filter').value;

    let filtered = rows.filter(r => {
      if (search && !r.product.toLowerCase().includes(search)) return false;
      if (lifecycle !== 'all' && r.lifecycle !== lifecycle) return false;
      return true;
    });

    const sortFns = {
      'last_desc': (a, b) => b.last_day_order - a.last_day_order,
      'total_desc': (a, b) => b.total_order - a.total_order,
      'mom_desc': (a, b) => (b.mom_pct || -999) - (a.mom_pct || -999),
      'avg_desc': (a, b) => (b.total_order / dates.length) - (a.total_order / dates.length),
      'age_asc': (a, b) => (a.age_days || 999) - (b.age_days || 999),
      'decline': (a, b) => (b.decline_days || 0) - (a.decline_days || 0),
    };
    filtered.sort(sortFns[sort] || sortFns['last_desc']);

    document.getElementById('filter-count').textContent = filtered.length + '/' + rows.length;

    let html = '<table><thead><tr><th style="position:sticky;left:0;background:var(--bg-card);z-index:1;min-width:160px;">商品</th>' +
      '<th style="text-align:center;">状态</th>';
    dates.forEach(d => { html += '<th style="text-align:center;min-width:38px;">' + d.substring(5) + '</th>'; });
    html += '<th style="text-align:center;">趋势</th><th style="text-align:right;">日均</th><th style="text-align:right;">环比</th></tr></thead><tbody>';

    filtered.forEach(r => {
      const lc = lifecycleMap[r.lifecycle] || lifecycleMap['mature'];
      const trendIcon = r.trend === 'up' ? '↑' : r.trend === 'down' ? '↓' : '→';
      const trendColor = r.trend === 'up' ? 'var(--success)' : r.trend === 'down' ? 'var(--danger)' : 'var(--text-3)';

      html += '<tr>';
      html += '<td style="position:sticky;left:0;background:var(--bg-card);z-index:1;font-weight:500;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + r.product + '">' + r.product.substring(0, 16) + '</td>';
      html += '<td style="text-align:center;"><span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;background:' + lc.bg + ';color:' + lc.color + ';">' + lc.label + '</span></td>';
      dates.forEach(d => {
        const v = r.daily[d] || 0;
        const bg = v > 0 ? 'rgba(22,93,255,' + Math.min(v / 20, 1) * 0.12 + ')' : 'transparent';
        html += '<td style="text-align:center;background:' + bg + ';font-size:12px;">' + (v || '-') + '</td>';
      });
      html += '<td style="text-align:center;color:' + trendColor + ';font-weight:600;">' + trendIcon + '</td>';
      html += '<td style="text-align:right;">' + (r.total_order / dates.length).toFixed(1) + '</td>';
      html += '<td style="text-align:right;">' + (r.mom_pct !== null ? r.mom_pct + '%' : '-') + '</td>';
      html += '</tr>';
    });
    html += '</tbody></table>';
    document.getElementById('table-container').innerHTML = html;
  }

  render();
  document.getElementById('search-input').addEventListener('input', render);
  document.getElementById('sort-select').addEventListener('change', render);
  document.getElementById('lifecycle-filter').addEventListener('change', render);
})();
