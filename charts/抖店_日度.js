function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

const dates = DATA.sales.daily.period || DATA.sales.daily.dates || [];
const orders = DATA.sales.daily.total_order || DATA.sales.daily.order || [];
const amounts = DATA.sales.daily.total_amount || DATA.sales.daily.amount || [];

// 1. 日订单+日金额 双线/柱图
echarts.init(document.getElementById('chart-daily'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['日订单', '日金额(元)'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 60, top: 35, bottom: 50 },
  xAxis: { type: 'category', data: dates, axisLabel: { color: textColor, rotate: 45, fontSize: 9 }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: [
    { type: 'value', name: '订单', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    { type: 'value', name: '金额', position: 'right', axisLabel: { color: textColor, formatter: v => (v/10000).toFixed(1)+'万' }, splitLine: { show: false } }
  ],
  dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 5, borderColor: '#e8e8e8', backgroundColor: '#fafafa', fillerColor: 'rgba(0,0,0,.06)', handleStyle: { color: '#595959' } }],
  series: [
    { name: '日订单', type: 'bar', data: orders, itemStyle: { color: C.blue }, barWidth: '50%' },
    { name: '日金额(元)', type: 'line', yAxisIndex: 1, data: amounts, smooth: true, lineStyle: { color: C.orange, width: 2 }, itemStyle: { color: C.orange }, areaStyle: { color: 'rgba(250,140,22,0.1)' } }
  ]
});

// 2. 日订单热力图（按星期分布）
const heatData = [];
dates.forEach((d, i) => {
  const date = new Date(d);
  const dow = date.getDay();
  const week = Math.floor(i / 7);
  heatData.push([week, dow, orders[i] || 0]);
});
const maxOrders = Math.max(...heatData.map(d => d[2]), 1);
const weekLabels = [];
for (let w = 0; w <= Math.floor(dates.length / 7); w++) weekLabels.push('W' + (w+1));
const dowLabels = ['日', '一', '二', '三', '四', '五', '六'];

echarts.init(document.getElementById('chart-heat'), 'light').setOption({
  tooltip: { ...baseTooltip, formatter: p => dates[p.value[0]*7 + p.value[1]] + '<br>订单：' + p.value[2] },
  grid: { left: 60, right: 30, top: 20, bottom: 60 },
  xAxis: { type: 'category', data: weekLabels, axisLabel: { color: textColor, fontSize: 9 }, splitArea: { show: true } },
  yAxis: { type: 'category', data: dowLabels, axisLabel: { color: textColor, fontSize: 11 }, splitArea: { show: true } },
  visualMap: { min: 0, max: maxOrders, calculable: true, orient: 'horizontal', left: 'center', bottom: 0, textStyle: { color: textColor }, inRange: { color: ['#f0f0f0', C.blue, '#1d39c4'] } },
  series: [{ name: '订单', type: 'heatmap', data: heatData, label: { show: false }, emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } } }]
});

window.addEventListener('resize', () => {
  document.querySelectorAll('.chart, .chart-sm, .chart-lg, .chart-xl').forEach(el => {
    const inst = echarts.getInstanceByDom(el);
    if (inst) inst.resize();
  });
});
}

async function loadDataAndRender() {
  const DATA = await fetch('../../数据/看板数据/抖店_日度.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();
