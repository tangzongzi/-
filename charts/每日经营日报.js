/* charts/每日经营日报.js */
(async function() {
  const DATA = await fetch('../../数据/汇总/经营_每日日报.json').then(r => r.json());
  const rows = DATA.data;
  const s = DATA.summary;

  // KPI strip
  const kpiHtml = [
    { label: '近7天销售额', value: '¥' + (s.recent_7d_sales / 10000).toFixed(2) + '万', sub: '7天' },
    { label: '近7天订单', value: s.recent_7d_orders.toLocaleString(), sub: '7天' },
    { label: '近7天退款', value: '¥' + s.recent_7d_refund.toLocaleString(), sub: '7天' },
  ].map(k => '<div class="kpi-item"><span class="kpi-item-label">' + k.label + '</span><span class="kpi-item-value">' + k.value + '</span><span class="kpi-item-sub">' + k.sub + '</span></div>').join('');
  document.getElementById('kpi-strip').innerHTML = kpiHtml;

  // Badges
  document.getElementById('badge-latest').textContent = s.latest_date;
  document.getElementById('badge-days').textContent = s.total_days + ' 天';

  // 销售走势图
  const dates = rows.map(r => r.date.substring(5));
  const sales = rows.map(r => r.sales_amount);
  const orders = rows.map(r => r.orders);

  echarts.init(document.getElementById('chart-daily'), 'light').setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['销售额', '订单数'], top: 0, right: 0 },
    grid: { left: 60, right: 60, top: 35, bottom: 30 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 45, fontSize: 9 } },
    yAxis: [
      { type: 'value', name: '金额', axisLabel: { formatter: v => (v/10000).toFixed(0) + '万' } },
      { type: 'value', name: '订单', position: 'right' }
    ],
    series: [
      { name: '销售额', type: 'bar', data: sales, itemStyle: { color: '#1677ff' } },
      { name: '订单数', type: 'line', yAxisIndex: 1, data: orders, smooth: true, itemStyle: { color: '#fa8c16' } }
    ]
  });

  // 退款走势图
  const refundAmounts = rows.map(r => r.refund_amount);
  const closeAmounts = rows.map(r => r.close_amount);

  echarts.init(document.getElementById('chart-refund'), 'light').setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['退款金额', '关闭损失'], top: 0, right: 0 },
    grid: { left: 60, right: 20, top: 35, bottom: 30 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 45, fontSize: 9 } },
    yAxis: { type: 'value', name: '金额' },
    series: [
      { name: '退款金额', type: 'bar', data: refundAmounts, itemStyle: { color: '#ff4d4f' } },
      { name: '关闭损失', type: 'bar', data: closeAmounts, itemStyle: { color: '#d9d9d9' } }
    ]
  });

  // 表格
  let html = '<table><thead><tr><th>日期</th><th style="text-align:right">订单</th><th style="text-align:right">销售额</th><th style="text-align:right">退款</th><th style="text-align:right">关闭损失</th><th style="text-align:right">商品数</th><th>增长 Top3</th><th>下降 Top3</th></tr></thead><tbody>';
  rows.slice(-14).reverse().forEach(r => {
    const growth = (r.growth_top5 || []).slice(0, 3).map(g => '<span style="color:var(--success)">' + g.product.substring(0, 8) + ' +' + g.mom_pct + '%</span>').join('<br>');
    const decline = (r.decline_top5 || []).slice(0, 3).map(g => '<span style="color:var(--danger)">' + g.product.substring(0, 8) + ' ' + g.mom_pct + '%</span>').join('<br>');
    html += '<tr>';
    html += '<td>' + r.date + '</td>';
    html += '<td style="text-align:right">' + r.orders.toLocaleString() + '</td>';
    html += '<td style="text-align:right">¥' + r.sales_amount.toLocaleString() + '</td>';
    html += '<td style="text-align:right">' + (r.refund_amount > 0 ? '¥' + r.refund_amount.toLocaleString() : '-') + '</td>';
    html += '<td style="text-align:right">' + (r.close_amount > 0 ? '¥' + r.close_amount.toLocaleString() : '-') + '</td>';
    html += '<td style="text-align:right">' + r.product_count + '</td>';
    html += '<td style="font-size:11px;">' + (growth || '-') + '</td>';
    html += '<td style="font-size:11px;">' + (decline || '-') + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('table-container').innerHTML = html;
})();
