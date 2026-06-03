function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

echarts.init(document.getElementById('chart-monthly'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['订单数', '金额(元)', '客单价'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 60, top: 35, bottom: 30 },
  xAxis: { type: 'category', data: DATA.sales.monthly.months, axisLabel: { color: textColor }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: [
    { type: 'value', name: '订单/金额', axisLabel: { color: textColor, formatter: v => v >= 10000 ? (v/10000).toFixed(1)+'万' : v }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    { type: 'value', name: '客单价', position: 'right', axisLabel: { color: textColor }, splitLine: { show: false } }
  ],
  series: [
    { name: '订单数', type: 'bar', data: DATA.sales.monthly.order, itemStyle: { color: C.blue }, barWidth: '30%' },
    { name: '金额(元)', type: 'bar', data: DATA.sales.monthly.amount, itemStyle: { color: C.orange }, barWidth: '30%' },
    { name: '客单价', type: 'line', yAxisIndex: 1, data: DATA.sales.monthly.order.map((o,i) => (DATA.sales.monthly.amount[i]/o).toFixed(2)), lineStyle: { color: C.cyan, width: 2 }, itemStyle: { color: C.cyan } }
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
  const DATA = await fetch('../../数据/看板数据/销售业绩_月度.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();