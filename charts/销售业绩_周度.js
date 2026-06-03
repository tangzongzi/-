function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

echarts.init(document.getElementById('chart-weekly'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['周订单数', '周金额(元)'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 60, top: 35, bottom: 50 },
  xAxis: { type: 'category', data: DATA.sales.weekly.week_start, axisLabel: { color: textColor, rotate: 30, fontSize: 10 }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: [
    { type: 'value', name: '订单', position: 'left', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    { type: 'value', name: '金额', position: 'right', axisLabel: { color: textColor, formatter: v => (v/10000).toFixed(1)+'万' }, splitLine: { show: false } }
  ],
  series: [
    { name: '周订单数', type: 'bar', data: DATA.sales.weekly.order, itemStyle: { color: C.blue }, barWidth: '50%' },
    { name: '周金额(元)', type: 'line', yAxisIndex: 1, data: DATA.sales.weekly.amount, smooth: true, lineStyle: { color: C.orange, width: 2 }, itemStyle: { color: C.orange }, areaStyle: { color: 'rgba(251,146,60,0.15)' } }
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
  const DATA = await fetch('../../数据/看板数据/销售业绩_周度.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();