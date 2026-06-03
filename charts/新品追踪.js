/* charts/新品追踪.js */
(async function() {
  const DATA = await fetch('../../数据/汇总/新品_追踪.json').then(r => r.json());
  let rows = DATA.data;

  // KPI strip
  const kpiHtml = [
    { label: '新品数', value: DATA.summary.new_product_count, sub: '近14天' },
    { label: '新品订单', value: DATA.summary.total_new_orders, sub: '累计' },
    { label: '新品金额', value: '¥' + (DATA.summary.total_new_amount / 10000).toFixed(2) + '万', sub: '累计' },
  ].map(k => '<div class="kpi-item"><span class="kpi-item-label">' + k.label + '</span><span class="kpi-item-value">' + k.value + '</span><span class="kpi-item-sub">' + k.sub + '</span></div>').join('');
  document.getElementById('kpi-strip').innerHTML = kpiHtml;

  // Badges
  document.getElementById('badge-count').textContent = rows.length + ' 个新品';
  document.getElementById('badge-orders').textContent = '累计 ' + DATA.summary.total_new_orders + ' 单';

  // 控件
  const controlsHtml = '<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;">' +
    '<input id="search-input" type="text" placeholder="搜索新品..." style="padding:6px 12px;border:1px solid var(--border-color);border-radius:var(--radius-sm);background:var(--bg-elevated);color:var(--text-primary);font-size:13px;width:240px;">' +
    '<select id="sort-select" style="padding:6px 12px;border:1px solid var(--border-color);border-radius:var(--radius-sm);background:var(--bg-elevated);color:var(--text-primary);font-size:13px;">' +
    '<option value="date_desc">最新上架 ↓</option>' +
    '<option value="date_asc">最早上架 ↑</option>' +
    '<option value="orders_desc">累计订单 ↓</option>' +
    '<option value="orders_asc">累计订单 ↑</option>' +
    '<option value="amount_desc">累计金额 ↓</option>' +
    '<option value="avg_desc">日均订单 ↓</option>' +
    '</select>' +
    '<span id="filter-count" style="font-size:12px;color:var(--text-tertiary);"></span>' +
    '</div>';
  document.getElementById('table-container').insertAdjacentHTML('beforebegin', controlsHtml);

  function render() {
    const search = document.getElementById('search-input').value.toLowerCase();
    const sort = document.getElementById('sort-select').value;

    let filtered = rows.filter(r => !search || r.product.toLowerCase().includes(search));

    const sortFns = {
      'date_desc': (a, b) => b.first_seen.localeCompare(a.first_seen),
      'date_asc': (a, b) => a.first_seen.localeCompare(b.first_seen),
      'orders_desc': (a, b) => b.total_order - a.total_order,
      'orders_asc': (a, b) => a.total_order - b.total_order,
      'amount_desc': (a, b) => b.total_amount - a.total_amount,
      'avg_desc': (a, b) => b.avg_daily - a.avg_daily,
    };
    filtered.sort(sortFns[sort] || sortFns['date_desc']);

    document.getElementById('filter-count').textContent = filtered.length + '/' + rows.length;

    let html = '<table><thead><tr><th>商品</th><th>首次出现</th><th>上新天数</th><th style="text-align:right">累计订单</th><th style="text-align:right">累计金额</th><th style="text-align:right">日均</th></tr></thead><tbody>';
    filtered.forEach(r => {
      const daysClass = r.days_since <= 3 ? ' style="color:var(--success);font-weight:600;"' : '';
      html += '<tr>';
      html += '<td title="' + r.product + '">' + r.product.substring(0, 30) + '</td>';
      html += '<td>' + r.first_seen + '</td>';
      html += '<td' + daysClass + '>' + r.days_since + ' 天</td>';
      html += '<td style="text-align:right">' + r.total_order + '</td>';
      html += '<td style="text-align:right">¥' + r.total_amount.toLocaleString() + '</td>';
      html += '<td style="text-align:right">' + r.avg_daily + '</td>';
      html += '</tr>';
    });
    html += '</tbody></table>';
    document.getElementById('table-container').innerHTML = html;
  }

  render();
  document.getElementById('search-input').addEventListener('input', render);
  document.getElementById('sort-select').addEventListener('change', render);

  // 图表：新品销售趋势（Top 5）
  if (rows.length > 0) {
    const allDates = new Set();
    rows.forEach(r => Object.keys(r.daily).forEach(d => allDates.add(d)));
    const dates = [...allDates].sort();
    const top5 = rows.slice().sort((a, b) => b.total_order - a.total_order).slice(0, 5);

    echarts.init(document.getElementById('chart-new'), 'light').setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: top5.map(r => r.product.substring(0, 15)), type: 'scroll' },
      grid: { left: 50, right: 20, top: 40, bottom: 30 },
      xAxis: { type: 'category', data: dates.map(d => d.substring(5)) },
      yAxis: { type: 'value', name: '订单数' },
      series: top5.map(r => ({
        name: r.product.substring(0, 15),
        type: 'line',
        smooth: true,
        data: dates.map(d => r.daily[d] || 0),
      }))
    });
  }
})();
