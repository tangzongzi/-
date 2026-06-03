function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

// 日度数据
const daily_dates = DATA.sales.daily.dates || DATA.sales.daily.period || [];
const daily_orders = DATA.sales.daily.order || DATA.sales.daily.total_order || [];
const daily_amounts = DATA.sales.daily.amount || DATA.sales.daily.total_amount || [];

// 周度数据
const weekly_dates = DATA.sales.weekly.weeks || DATA.sales.weekly.period || [];
const weekly_orders = DATA.sales.weekly.order || DATA.sales.weekly.total_order || [];
const weekly_amounts = DATA.sales.weekly.amount || DATA.sales.weekly.total_amount || [];

// 月度数据
const monthly_dates = DATA.sales.monthly.months || DATA.sales.monthly.period || [];
const monthly_orders = DATA.sales.monthly.order || DATA.sales.monthly.total_order || [];
const monthly_amounts = DATA.sales.monthly.amount || DATA.sales.monthly.total_amount || [];

// 1. 日度（订单+金额）
echarts.init(document.getElementById('chart-daily'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['日订单', '日金额(元)'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 60, top: 35, bottom: 50 },
  xAxis: { type: 'category', data: daily_dates, axisLabel: { color: textColor, rotate: 45, fontSize: 9 }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: [
    { type: 'value', name: '订单', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    { type: 'value', name: '金额', position: 'right', axisLabel: { color: textColor, formatter: v => (v/10000).toFixed(1)+'万' }, splitLine: { show: false } }
  ],
  dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 5, borderColor: '#e8e8e8', backgroundColor: '#fafafa', fillerColor: 'rgba(0,0,0,.06)', handleStyle: { color: '#595959' } }],
  series: [
    { name: '日订单', type: 'bar', data: daily_orders, itemStyle: { color: C.blue }, barWidth: '50%' },
    { name: '日金额(元)', type: 'line', yAxisIndex: 1, data: daily_amounts, smooth: true, lineStyle: { color: C.orange, width: 2 }, itemStyle: { color: C.orange }, areaStyle: { color: 'rgba(250,140,22,0.1)' } }
  ]
});

// 2. 周度（订单+金额）
echarts.init(document.getElementById('chart-weekly'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['周订单', '周金额(元)'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 60, top: 35, bottom: 50 },
  xAxis: { type: 'category', data: weekly_dates, axisLabel: { color: textColor, rotate: 30, fontSize: 10 }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: [
    { type: 'value', name: '订单', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    { type: 'value', name: '金额', position: 'right', axisLabel: { color: textColor, formatter: v => (v/10000).toFixed(1)+'万' }, splitLine: { show: false } }
  ],
  series: [
    { name: '周订单', type: 'bar', data: weekly_orders, itemStyle: { color: C.blue }, barWidth: '50%' },
    { name: '周金额(元)', type: 'line', yAxisIndex: 1, data: weekly_amounts, smooth: true, lineStyle: { color: C.orange, width: 2 }, itemStyle: { color: C.orange } }
  ]
});

// 3. 月度（订单+金额+客单价）
const monthly_avgs = monthly_orders.map((o, i) => monthly_amounts[i] && o ? (monthly_amounts[i] / o).toFixed(2) : 0);
echarts.init(document.getElementById('chart-monthly'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['月订单', '月金额(元)', '客单价'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 60, top: 35, bottom: 30 },
  xAxis: { type: 'category', data: monthly_dates, axisLabel: { color: textColor, fontSize: 11 }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: [
    { type: 'value', name: '订单', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    { type: 'value', name: '金额/客单', position: 'right', axisLabel: { color: textColor }, splitLine: { show: false } }
  ],
  series: [
    { name: '月订单', type: 'bar', data: monthly_orders, itemStyle: { color: C.blue }, barWidth: '40%' },
    { name: '月金额(元)', type: 'line', yAxisIndex: 1, data: monthly_amounts, smooth: true, lineStyle: { color: C.orange, width: 2 }, itemStyle: { color: C.orange } },
    { name: '客单价', type: 'line', yAxisIndex: 1, data: monthly_avgs, smooth: true, lineStyle: { color: C.cyan, width: 2, type: 'dashed' }, itemStyle: { color: C.cyan } }
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
  const DATA = await fetch('../../数据/看板数据/拼多多_综合.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();
