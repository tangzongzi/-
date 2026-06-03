function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

// month_changes 是数组 [{month, pool_size, new_count, gone_count, kept_count, net_change, incomplete, days_with_data}]
const monthArr = DATA.product.month_changes || [];
const months = monthArr.map(m => m.month);
const pools = monthArr.map(m => m.pool_size || 0);
const news = monthArr.map(m => m.new_count || 0);
const gones = monthArr.map(m => -(m.gone_count || 0));
const nets = monthArr.map(m => m.net_change || 0);
// 不完整月：淘汰柱变灰、net 柱变灰
const grayNews = monthArr.map(m => m.incomplete ? null : m.new_count);
const grayGones = monthArr.map(m => m.incomplete ? null : -(m.gone_count || 0));
const grayNets = monthArr.map(m => m.incomplete ? null : m.net_change);

echarts.init(document.getElementById('chart-month'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['商品池规模', '新增', '淘汰', '净变化'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 50, top: 35, bottom: 30 },
  xAxis: { type: 'category', data: months, axisLabel: { color: textColor, formatter: v => { const m = monthArr.find(x => x.month === v); return m && m.incomplete ? v + ' ⚠️' : v; } }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: { type: 'value', name: '商品数', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
  series: [
    { name: '商品池规模', type: 'line', data: pools, smooth: true, lineStyle: { color: C.purple, width: 3 }, itemStyle: { color: C.purple }, areaStyle: { color: 'rgba(167,139,250,0.2)' } },
    { name: '新增', type: 'bar', data: grayNews, itemStyle: { color: C.green }, barWidth: '25%' },
    { name: '淘汰', type: 'bar', data: grayGones, itemStyle: { color: C.red }, barWidth: '25%' },
    { name: '净变化', type: 'line', data: grayNets, lineStyle: { color: C.orange, width: 2 }, itemStyle: { color: C.orange } }
  ]
});

// concentration 是 { top10_pct, top20_pct }（单期数据）
const conc = DATA.product.concentration || { top10_pct: 0, top20_pct: 0 };
echarts.init(document.getElementById('chart-conc'), 'light').setOption({
  tooltip: { ...baseTooltip, trigger: 'axis', formatter: '{b}: {c}%' },
  grid: { left: 50, right: 50, top: 35, bottom: 30 },
  xAxis: { type: 'category', data: ['Top 10%', 'Top 20%'], axisLabel: { color: textColor }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: { type: 'value', max: 100, name: '占比%', axisLabel: { color: textColor, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
  series: [
    { name: '销售集中度', type: 'bar', data: [(conc.top10_pct || 0).toFixed(1), (conc.top20_pct || 0).toFixed(1)], itemStyle: { color: function(p){ return [C.blue, C.purple][p.dataIndex]; } }, barWidth: '40%', label: { show: true, position: 'top', color: textColor, formatter: '{c}%' } }
  ]
});

// distribution_5 是 [{range, count}] 数组
const distArr = DATA.product.distribution_5 || [];
const distMap = {};
distArr.forEach(d => { distMap[d.range] = d.count; });
echarts.init(document.getElementById('chart-dist'), 'light').setOption({
  tooltip: { trigger: 'item', ...baseTooltip, formatter: '{b}: {c} 个 ({d}%)' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    label: { color: textColor, fontSize: 12 },
    data: [
      { name: '1单', value: distMap['1'] || 0, itemStyle: { color: '#7f1d1d' } },
      { name: '2-5单', value: distMap['2-5'] || 0, itemStyle: { color: C.red } },
      { name: '6-20单', value: distMap['6-20'] || 0, itemStyle: { color: C.orange } },
      { name: '21-100单', value: distMap['21-100'] || 0, itemStyle: { color: C.blue } },
      { name: '100+单', value: distMap['100+'] || 0, itemStyle: { color: C.green } }
    ]
  }]
});

window.addEventListener('resize', () => {
  document.querySelectorAll('.chart, .chart-sm, .chart-lg, .chart-xl').forEach(el => {
    const inst = echarts.getInstanceByDom(el);
    if (inst) inst.resize();
  });
});
}

async function loadDataAndRender() {
  const DATA = await fetch('../数据/看板数据/商品结构_综合.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();
