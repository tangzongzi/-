function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

const dates = DATA.sales.weekly.period || DATA.sales.weekly.week_start || DATA.sales.weekly.weeks || [];
const orders = DATA.sales.weekly.total_order || DATA.sales.weekly.order || [];
const amounts = DATA.sales.weekly.total_amount || DATA.sales.weekly.amount || [];

echarts.init(document.getElementById('chart-weekly'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['周订单', '周金额(元)'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 60, top: 35, bottom: 50 },
  xAxis: { type: 'category', data: dates, axisLabel: { color: textColor, rotate: 30, fontSize: 10 }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: [
    { type: 'value', name: '订单', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    { type: 'value', name: '金额', position: 'right', axisLabel: { color: textColor, formatter: v => (v/10000).toFixed(1)+'万' }, splitLine: { show: false } }
  ],
  dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 5, borderColor: '#e8e8e8', backgroundColor: '#fafafa', fillerColor: 'rgba(0,0,0,.06)', handleStyle: { color: '#595959' } }],
  series: [
    { name: '周订单', type: 'bar', data: orders, itemStyle: { color: C.blue }, barWidth: '50%' },
    { name: '周金额(元)', type: 'line', yAxisIndex: 1, data: amounts, smooth: true, lineStyle: { color: C.orange, width: 2 }, itemStyle: { color: C.orange }, areaStyle: { color: 'rgba(250,140,22,0.1)' } }
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
  const DATA = await fetch('../../数据/看板数据/拼多多_周度.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();
