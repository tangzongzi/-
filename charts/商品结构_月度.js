function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

// month_changes 是数组 [{month, pool_size, new_count, gone_count, kept_count, incomplete}]
const monthArr = DATA.product.month_changes || [];
const months = monthArr.map(m => m.month);
const pools = monthArr.map(m => m.pool_size || 0);
const news = monthArr.map(m => m.new_count || 0);
const gones = monthArr.map(m => -(m.gone_count || 0));
const kepts = monthArr.map(m => m.kept_count || 0);
const grayNews = monthArr.map(m => m.incomplete ? null : m.new_count);
const grayGones = monthArr.map(m => m.incomplete ? null : -(m.gone_count || 0));
const grayKepts = monthArr.map(m => m.incomplete ? null : m.kept_count);

echarts.init(document.getElementById('chart-month'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['商品池', '新增', '淘汰', '留存'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 50, top: 35, bottom: 30 },
  xAxis: { type: 'category', data: months, axisLabel: { color: textColor, formatter: v => { const m = monthArr.find(x => x.month === v); return m && m.incomplete ? v + ' ⚠️' : v; } }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: { type: 'value', name: '商品数', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
  series: [
    { name: '商品池', type: 'line', data: pools, smooth: true, lineStyle: { color: C.purple, width: 3 }, itemStyle: { color: C.purple }, areaStyle: { color: 'rgba(167,139,250,0.2)' } },
    { name: '新增', type: 'bar', data: grayNews, itemStyle: { color: C.green }, barWidth: '20%' },
    { name: '淘汰', type: 'bar', data: grayGones, itemStyle: { color: C.red }, barWidth: '20%' },
    { name: '留存', type: 'bar', data: grayKepts, itemStyle: { color: C.cyan }, barWidth: '20%' }
  ]
});

window.addEventListener('resize', () => {
  document.querySelectorAll('.chart, .chart-sm, .chart-lg, .chart-xl').forEach(el => {
    const inst = echarts.getInstanceByDom(el);
    if (inst) inst.resize();
  });
});

}

// === 数据-视图分离（数据驱动渲染）===
async function loadDataAndRender() {
  const DATA = await fetch('../../数据/看板数据/商品结构_月度.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();
