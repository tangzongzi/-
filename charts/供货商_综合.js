function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

const supps = DATA.supplier.top_suppliers.slice(0, 15);
const names = supps.map(s => s.name.length > 15 ? s.name.slice(0, 13) + '..' : s.name);
const amts = supps.map(s => s.amount / 10000);
echarts.init(document.getElementById('chart-supp'), 'light').setOption({
  tooltip: { ...baseTooltip, formatter: p => p.name + '<br>金额: ¥' + p.value.toFixed(1) + '万' },
  grid: { left: 120, right: 50, top: 10, bottom: 30 },
  xAxis: { type: 'value', name: '万元', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
  yAxis: { type: 'category', data: names.reverse(), axisLabel: { color: textColor, fontSize: 10 }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  series: [{ type: 'bar', data: amts.reverse(), itemStyle: { color: C.purple }, barWidth: '60%' }]
});

// 重渲染供货商表格：加 "风险" 和 "关闭率" 两列
const tableEl = document.getElementById('supp-table');
if (tableEl) {
  const max = supps[0] ? supps[0].amount : 1;
  const colorMap = { red: '#ff4d4f', yellow: '#fa8c16', green: '#52c41a', gray: '#d9d9d9' };
  const tagLabel = { 红: '高', 中: '中', 低: '低' };
  // 修正 tagLabel：用 risk_tag 本身
  tableEl.innerHTML = `<thead><tr><th>#</th><th>供货商</th><th>订单</th><th>金额</th><th>客单价</th><th>占比条</th><th>关闭率</th><th>风险</th></tr></thead><tbody>${supps.map((s, i) => {
    const pct = (s.close_rate_pct || 0).toFixed(2);
    const color = colorMap[s.risk_color] || '#d9d9d9';
    const tag = s.risk_tag || '—';
    return `<tr><td>${i+1}</td><td><b>${s.name}</b></td><td>${(s.order||0).toLocaleString()}</td><td>¥${((s.amount||0)/10000).toFixed(1)}万</td><td>¥${(s.avg_price||0).toFixed(2)}</td><td><div class="bar" style="width:${((s.amount||0)/max*100).toFixed(1)}%"></div></td><td>${pct}%</td><td><span style="background:${color};color:#fff;padding:2px 8px;border-radius:3px;font-size:12px;">${tag}</span></td></tr>`;
  }).join('')}</tbody>`;
}

window.addEventListener('resize', () => {
  document.querySelectorAll('.chart, .chart-sm, .chart-lg, .chart-xl').forEach(el => {
    const inst = echarts.getInstanceByDom(el);
    if (inst) inst.resize();
  });
});

}

// === 数据-视图分离（数据驱动渲染）===
async function loadDataAndRender() {
  const DATA = await fetch('../数据/看板数据/供货商_综合.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();
