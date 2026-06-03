function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const textColor = 'rgba(0,0,0,.45)';
const baseTooltip = { backgroundColor: '#fafafa', borderColor: '#e8e8e8', textStyle: { color: 'rgba(0,0,0,.65)' } };

const weeks = DATA.product.weeks;
const wpc = DATA.product.week_prod_count;
const wn = DATA.product.week_new;
const wg = DATA.product.week_gone;
const net = wn.map((n,i) => n - wg[i]);

echarts.init(document.getElementById('chart-pace'), 'light').setOption({
  tooltip: { trigger: 'axis', ...baseTooltip, axisPointer: { type: 'cross' } },
  legend: { data: ['商品池规模', '新增', '淘汰', '净变化'], textStyle: { color: textColor }, top: 0 },
  grid: { left: 50, right: 50, top: 35, bottom: 60 },
  xAxis: { type: 'category', data: weeks, axisLabel: { color: textColor, rotate: 30, fontSize: 10 }, axisLine: { lineStyle: { color: '#e8e8e8' } } },
  yAxis: [
    { type: 'value', name: '商品池', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    { type: 'value', name: '新增/淘汰', position: 'right', axisLabel: { color: textColor }, splitLine: { show: false } }
  ],
  series: [
    { name: '商品池规模', type: 'line', data: wpc, smooth: true, lineStyle: { color: C.purple, width: 3 }, itemStyle: { color: C.purple }, areaStyle: { color: 'rgba(167,139,250,0.2)' }, markPoint: { data: [{ type: 'max', name: '峰值' }, { type: 'min', name: '谷值' }] } },
    { name: '新增', type: 'bar', yAxisIndex: 1, data: wn, itemStyle: { color: C.green }, barWidth: '25%' },
    { name: '淘汰', type: 'bar', yAxisIndex: 1, data: wg.map(x => -x), itemStyle: { color: C.red }, barWidth: '25%' },
    { name: '净变化', type: 'line', yAxisIndex: 1, data: net, lineStyle: { color: C.yellow, width: 2 }, itemStyle: { color: C.yellow } }
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
  const DATA = await fetch('../../数据/看板数据/商品结构_周度.json').then(r => r.json());
  if (typeof renderDashboard === 'function') renderDashboard(DATA);
}

loadDataAndRender();