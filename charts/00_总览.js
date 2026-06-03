function renderDashboard(DATA) {
const C = { blue:'#1677ff', purple:'#722ed1', cyan:'#13c2c2', orange:'#fa8c16', green:'#52c41a', red:'#ff4d4f', magenta:'#eb2f96' };
const text = 'rgba(0,0,0,.45)';
const tip = { backgroundColor:'rgba(255,255,255,.96)', borderColor:'#1f1f1f', textStyle:{color:'rgba(0,0,0,.88)'}, borderWidth:1 };

echarts.init(document.getElementById('chart-trend'), 'light').setOption({
  tooltip:{ trigger:'axis', ...tip, axisPointer:{ type:'cross', lineStyle:{color:'#e8e8e8'} } },
  legend:{ data:['日订单','日金额'], textStyle:{color:text}, top:0, right:0 },
  grid:{ left:50, right:60, top:35, bottom:50 },
  xAxis:{ type:'category', data:DATA.sales.daily.dates, axisLabel:{color:text,rotate:45,fontSize:9}, axisLine:{lineStyle:{color:'#e8e8e8'}} },
  yAxis:[
    { type:'value', name:'订单', position:'left', axisLabel:{color:text}, splitLine:{lineStyle:{color:'#f0f0f0'}} },
    { type:'value', name:'金额', position:'right', axisLabel:{color:text,formatter:v=>(v/10000).toFixed(1)+'万'}, splitLine:{show:false} }
  ],
  dataZoom:[{type:'inside'},{type:'slider',height:16,bottom:5,borderColor:'#1f1f1f',backgroundColor:'#141414',fillerColor:'rgba(22,119,255,.15)',handleStyle:{color:'#1677ff'}}],
  series:[
    { name:'日订单', type:'bar', data:DATA.sales.daily.order, itemStyle:{color:C.blue}, barWidth:'50%' },
    { name:'日金额', type:'line', yAxisIndex:1, data:DATA.sales.daily.amount, smooth:true, lineStyle:{color:C.orange,width:2}, itemStyle:{color:C.blue}, areaStyle:{color:C.blue} }
  ]
});

const plats = DATA.sales.platforms.filter(p=>p.order>50);
echarts.init(document.getElementById('chart-plat'), 'light').setOption({
  tooltip:{ trigger:'axis', ...tip },
  legend:{ data:['订单数','金额(万)'], textStyle:{color:text}, top:0, right:0 },
  grid:{ left:50, right:60, top:35, bottom:30 },
  xAxis:{ type:'category', data:plats.map(p=>p.店铺平台), axisLabel:{color:text}, axisLine:{lineStyle:{color:'#e8e8e8'}} },
  yAxis:[
    { type:'value', name:'订单', axisLabel:{color:text}, splitLine:{lineStyle:{color:'#f0f0f0'}} },
    { type:'value', name:'金额(万)', position:'right', axisLabel:{color:text}, splitLine:{show:false} }
  ],
  series:[
    { name:'订单数', type:'bar', data:plats.map(p=>p.order), itemStyle:{color:C.blue}, barWidth:'35%', barGap:'10%' },
    { name:'金额(万)', type:'bar', yAxisIndex:1, data:plats.map(p=>+(p.amount/10000).toFixed(1)), itemStyle:{color:C.blue}, barWidth:'35%' }
  ]
});

// Top 10 店铺（按订单）
const topShops = DATA.sales.shops.slice().sort((a,b)=>b.order-a.order).slice(0,10);
echarts.init(document.getElementById('chart-shop'), 'light').setOption({
  tooltip:{ trigger:'axis', axisPointer:{type:'shadow'}, ...tip, formatter:function(p){
    const i = p[0].dataIndex;
    const s = topShops[i];
    return `<b>${s.name}</b><br>平台：${s.plat}<br>订单：${s.order.toLocaleString()}<br>金额：¥${(s.amount/10000).toFixed(1)}万<br>客单价：¥${s.avg_price.toFixed(2)}`;
  } },
  grid:{ left:90, right:30, top:10, bottom:20 },
  xAxis:{ type:'value', axisLabel:{color:text,fontSize:9}, splitLine:{lineStyle:{color:'#f0f0f0'}}, axisLine:{show:false}, axisTick:{show:false} },
  yAxis:{ type:'category', data:topShops.map(s=>s.name.length>10?s.name.slice(0,9)+'…':s.name).reverse(), axisLabel:{color:text,fontSize:10}, axisLine:{lineStyle:{color:'#e8e8e8'}}, axisTick:{show:false} },
  series:[{
    name:'订单数', type:'bar', data:topShops.map(s=>s.order).reverse(),
    itemStyle:{color:function(p){
      const colors=[C.blue,C.purple,C.cyan,C.orange,C.green];
      return colors[p.dataIndex%colors.length];
    }, borderRadius:[0,3,3,0]},
    barWidth:'55%',
    label:{ show:true, position:'right', color:text, fontSize:9, formatter:p=>topShops[p.dataIndex].order.toLocaleString() }
  }]
});

window.addEventListener('resize',()=>{ document.querySelectorAll('.chart,.chart-sm,.chart-lg,.chart-xl').forEach(el=>{ const i=echarts.getInstanceByDom(el); if(i)i.resize(); }); });
}

async function loadDataAndRender(){ const DATA=await fetch('数据/看板数据/00_总览.json').then(r=>r.json()); if(typeof renderDashboard==='function')renderDashboard(DATA); }
loadDataAndRender();