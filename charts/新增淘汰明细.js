function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

const top = DATA.product.top_products.slice(0, 15);
const names = top.map(p => p.name.length > 18 ? p.name.slice(0, 16) + '..' : p.name);
const orders = top.map(p => p.order);
echarts.init(document.getElementById('chart-top'), 'light').setOption({
  tooltip: { ...baseTooltip, formatter: p => p.name + '<br>订单: ' + p.value.toLocaleString() },
  grid: { left: 120, right: 30, top: 10, bottom: 30 },
  xAxis: { type: 'value', axisLabel: { color: textColor, formatter: v => v.toLocaleString() }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
  yAxis: { type: 'category', data: names.reverse(), axisLabel: { color: textColor, fontSize: 10 }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  series: [{ type: 'bar', data: orders.reverse(), itemStyle: { color: C.purple }, barWidth: '60%' }]
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
  const DATA = await fetch('../../数据/看板数据/新增淘汰明细.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();