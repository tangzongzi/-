function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

const months = DATA.sales.monthly.months || DATA.sales.monthly.period || [];
const orders = DATA.sales.monthly.total_order || DATA.sales.monthly.order || [];
const amounts = DATA.sales.monthly.total_amount || DATA.sales.monthly.amount || [];

// 月度订单+金额 双线/柱
echarts.init(document.getElementById('chart-stack'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['月订单', '月金额(元)'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 60, top: 35, bottom: 30 },
  xAxis: { type: 'category', data: months, axisLabel: { color: textColor, fontSize: 11 }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: [
    { type: 'value', name: '订单', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    { type: 'value', name: '金额', position: 'right', axisLabel: { color: textColor, formatter: v => (v/10000).toFixed(1)+'万' }, splitLine: { show: false } }
  ],
  series: [
    { name: '月订单', type: 'bar', data: orders, itemStyle: { color: C.blue }, barWidth: '40%' },
    { name: '月金额(元)', type: 'line', yAxisIndex: 1, data: amounts, smooth: true, lineStyle: { color: C.orange, width: 2 }, itemStyle: { color: C.orange }, areaStyle: { color: 'rgba(250,140,22,0.15)' } }
  ]
});

window.addEventListener('resize', () => {
  document.querySelectorAll('.chart, .chart-sm, .chart-lg, .chart-xl').forEach(el => {
    const inst = echarts.getInstanceByDom(el);
    if (inst) inst.resize();
  });
});
}

async function loadDataAndRender() {
  const DATA = await fetch('../../数据/看板数据/拼多多_月度.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();
