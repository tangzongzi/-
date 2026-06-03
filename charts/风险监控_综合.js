function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

// close_rate_month 是 [{month, total, closed, close_rate_pct}] 数组
const crmArr = DATA.risk.close_rate_month || [];
const months = crmArr.map(x => x.month);
const rates = crmArr.map(x => (x.close_rate_pct || 0).toFixed(2));
const closes = crmArr.map(x => x.closed || 0);
const totals = crmArr.map(x => x.total || 0);

echarts.init(document.getElementById('chart-close'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['关闭率%', '关闭订单数'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 60, top: 35, bottom: 30 },
  xAxis: { type: 'category', data: months, axisLabel: { color: textColor }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: [
    { type: 'value', name: '关闭率%', axisLabel: { color: textColor, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    { type: 'value', name: '关闭订单数', position: 'right', axisLabel: { color: textColor }, splitLine: { show: false } }
  ],
  series: [
    { name: '关闭率%', type: 'line', data: rates, smooth: true, lineStyle: { color: C.red, width: 3 }, itemStyle: { color: C.red }, areaStyle: { color: 'rgba(248,113,113,0.2)' }, markLine: { data: [{ yAxis: 15, name: '15% 告警线' }], lineStyle: { color: C.yellow, type: 'dashed' } } },
    { name: '关闭订单数', type: 'bar', yAxisIndex: 1, data: closes, itemStyle: { color: C.orange }, barWidth: '40%' }
  ]
});

// 待确认订单时效分布
const wait = DATA.risk.wait || { count: 0, aging: [], by_shop: [] };
const agingData = wait.aging || [];
if (agingData.length > 0 && document.getElementById('chart-wait-aging')) {
  echarts.init(document.getElementById('chart-wait-aging'), 'light').setOption({
    tooltip: { ...baseTooltip, trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: p => `${p[0].name}<br><b>${p[0].value}</b> 笔` },
    grid: { left: 60, right: 30, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: agingData.map(a => a.range), axisLabel: { color: textColor }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
    yAxis: { type: 'value', name: '笔数', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    series: [{
      name: '待确认',
      type: 'bar',
      data: agingData.map(a => ({ value: a.count, itemStyle: { color: a.min_hours >= 72 ? C.red : a.min_hours >= 24 ? C.orange : C.green } })),
      barWidth: '50%',
      label: { show: true, position: 'top', color: textColor, formatter: '{c}' }
    }]
  });
}

// 待确认订单店铺分布表
const waitShopTbody = document.querySelector('#wait-shop-table tbody');
if (waitShopTbody) {
  const shops = (wait.by_shop || []).slice(0, 5);
  const total = wait.count || 1;
  waitShopTbody.innerHTML = shops.map((s, i) => {
    const pct = ((s.count / total) * 100).toFixed(1);
    const barW = Math.max((s.count / shops[0].count) * 100, 2);
    return `<tr><td>${i+1}</td><td><b>${s.name}</b></td><td>${s.count.toLocaleString()}</td><td><div style="display:flex;align-items:center;gap:6px"><div style="background:#1677ff;height:6px;width:${barW}%"></div><span>${pct}%</span></div></td></tr>`;
  }).join('');
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
  const DATA = await fetch('../数据/看板数据/风险监控_综合.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();
