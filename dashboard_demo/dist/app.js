const $=s=>document.querySelector(s),fmt=n=>new Intl.NumberFormat('en-GB').format(n),pct=n=>new Intl.NumberFormat('en-GB',{maximumFractionDigits:1,minimumFractionDigits:1}).format(n)+'%';
const COLORS={blue:'#175f80',pale:'#afcbd5',orange:'#e47c44',grid:'#e5ecef',text:'#718693'};
const crashLabels={'Andere of onbekend':'Other / unknown','Geen vermelding van de type aanrijding':'Not specified','Kettingbotsing (3 bestuurders of meer)':'Multi-vehicle chain','Met een voetganger':'Pedestrian','Tss. 2 best.: langs opzij (voor-/achterkant-flank)':'Angle / side impact','Tussen 2 bestuurders: Flank tegen flank':'Sideswipe','Tussen 2 bestuurders: Frontale botsing':'Head-on','Tussen 2 bestuurders: Langs achteren':'Rear-end','Weggebruiker tegen hindernis buiten rijbaan':'Off-road obstacle','Weggebruiker tegen hindernis op de rijbaan':'On-road obstacle'};
const crashLabel=x=>x?.includes('bestuurder, geen hindernis')?'Single vehicle / fall':(crashLabels[x]||x);
const roadLabels={'Autosnelweg':'Motorway','Gemeenteweg':'Municipal road','Gewestweg':'Regional road','onbekend':'Unknown'};
const regionLabels={'Brussels Hoofdstedelijk Gewest':'Brussels-Capital','Vlaams Gewest':'Flanders','Waals Gewest':'Wallonia'};
const provinceLabels={'Provincie Antwerpen':'Antwerp','Provincie Oost-Vlaanderen':'East Flanders','Provincie West-Vlaanderen':'West Flanders','Provincie Henegouwen':'Hainaut','Provincie Luik':'Liège','Provincie Vlaams-Brabant':'Flemish Brabant','Provincie Limburg':'Limburg','Provincie Namen':'Namur','Provincie Waals-Brabant':'Walloon Brabant','Provincie Luxemburg':'Luxembourg','Brussels-Capital Region':'Brussels-Capital (region)'};
const cityNames={'Brussel':'Brussels','Antwerpen':'Antwerp','Gent':'Ghent','Brugge':'Bruges','Luik':'Liège','Namen':'Namur','Bergen':'Mons','Doornik':'Tournai','Leuven':'Leuven','Mechelen':'Mechelen'};
const cityLabel=x=>cityNames[x]||x;
const displayLabel=(x,kind)=>kind==='collision'?crashLabel(x):kind==='road'?roadLabels[x]||x:kind==='region'?regionLabels[x]||x:kind==='province'?provinceLabels[x]||x:cityLabel(x);
let data,rows,shape,cats,mapMode='all',cells=[],mapTransform;
let localRanking='province';
const sel={year:$('#year'),region:$('#region'),province:$('#province'),road:$('#road'),collision:$('#collision'),severity:$('#severity'),weather:$('#weather')};
const severe=s=>s==='1'||s==='2'||s==='3';
const decode=(r)=>({year:r[0],month:r[1],region:cats.region[r[2]],road:cats.road[r[3]],collision:cats.collision[r[4]],severity:cats.severity[r[5]],municipality:cats.municipality[r[6]],valid:r[7],gx:r[8],gy:r[9],gx500:r[10],gy500:r[11],x:r[12],y:r[13],province:cats.province[r[14]],weather:cats.weather[r[15]]});
function options(el,values,kind='',first='All'){el.innerHTML=`<option value="">${first}</option>`+values.map(x=>`<option value="${x.replaceAll('&','&amp;').replaceAll('"','&quot;')}">${displayLabel(x,kind)}</option>`).join('')}
function init(){
  cats=data.meta.categories;rows=data.rows.map(decode);shape=data.shape;
  sel.year.innerHTML=data.meta.years.slice().reverse().map(y=>`<option value="${y}">${y}</option>`).join('')+'<option value="">All years</option>';
  options(sel.region,cats.region.filter(x=>x!=='Onbekend'),'region');
  options(sel.province,cats.province.slice().sort((a,b)=>displayLabel(a,'province').localeCompare(displayLabel(b,'province'))),'province');
  options(sel.road,cats.road.filter(x=>x!=='onbekend'),'road');
  options(sel.collision,cats.collision,'collision');options(sel.severity,['Fatal crashes','Severe','Slight injury']);options(sel.weather,cats.weather,'','All weather');
  sel.year.value='2024';Object.values(sel).forEach(e=>e.addEventListener('change',render));
  sel.province.addEventListener('change',()=>{if(sel.province.value)zoomProvince(sel.province.value);else mapHome()});
  $('#show-provinces').addEventListener('click',()=>setLocalRanking('province'));
  $('#show-municipalities').addEventListener('click',()=>setLocalRanking('municipality'));
  $('#reset').addEventListener('click',()=>{sel.year.value='2024';Object.values(sel).filter(x=>x!==sel.year).forEach(x=>x.value='');mapMode='all';document.querySelectorAll('[data-map]').forEach(b=>b.classList.toggle('chosen',b.dataset.map==='all'));render();mapHome()});
  document.querySelectorAll('[data-map]').forEach(b=>b.addEventListener('click',()=>{mapMode=b.dataset.map;document.querySelectorAll('[data-map]').forEach(x=>x.classList.toggle('chosen',x===b));renderMap(window.currentRows)}));
  $('#download').addEventListener('click',download);window.addEventListener('resize',()=>renderMap(window.currentRows));initMapControls();render();
}
function matches(r,withoutYear=false,withoutProvince=false,withoutWeather=false,withoutSeverity=false){return(!sel.year.value||withoutYear||r.year===+sel.year.value)&&(!sel.region.value||r.region===sel.region.value)&&(!sel.province.value||withoutProvince||r.province===sel.province.value)&&(!sel.road.value||r.road===sel.road.value)&&(!sel.collision.value||r.collision===sel.collision.value)&&(!sel.severity.value||withoutSeverity||(sel.severity.value==='Fatal crashes'?r.severity==='1':sel.severity.value==='Severe'?severe(r.severity):r.severity==='4'))&&(!sel.weather.value||withoutWeather||r.weather===sel.weather.value)}
function countBy(rs,key){let o=new Map();for(const r of rs){let k=r[key]??'Onbekend';o.set(k,(o.get(k)||0)+1)}return [...o].sort((a,b)=>b[1]-a[1])}
function render(){
  const rs=rows.filter(r=>matches(r)),base=sel.severity.value?rows.filter(r=>matches(r,false,false,false,true)):rs;
  window.currentRows=rs;
  const n=rs.length,measure=sel.severity.value?n:rs.filter(r=>severe(r.severity)).length,g=rs.filter(r=>r.valid).length;
  const label=sel.severity.value==='Fatal crashes'?'Fatal':sel.severity.value==='Slight injury'?'Slight-injury':'Severe';
  $('#scope').textContent=`${fmt(n)} records in this selection`;
  $('#kpi-count').textContent=fmt(n);
  $('#kpi-class-title').textContent=`${label} crash class`;
  $('#kpi-severe').textContent=fmt(measure);
  $('#kpi-rate-title').textContent=`${label} share`;
  $('#kpi-rate').textContent=base.length?pct(100*measure/base.length):'—';
  $('#kpi-rate-sub').textContent=sel.severity.value?'Of injury crashes under other filters':'Of selected injury crashes';
  $('#kpi-geo').textContent=n?pct(100*g/n):'—';
  $('#kpi-count-sub').textContent=sel.year.value?`Map source · ${sel.year.value}`:'Map source · 2017–2024';
  $('#kpi-severe-sub').textContent=`${fmt(measure)} of ${fmt(base.length)} crashes`;
  renderMap(rs);renderProvinceRank();renderRank(rs);renderTrend();renderRoad(rs);renderCollisions(rs);renderSeverity(rs,base);renderCoverage();renderMonth(rs);renderVehicles();renderFatality(rs);
}
function rankMeter(percent,id,fatal=false){const color=fatal?['#d47a62','#a6474f']:['#40b2ad','#175e84'];return `<svg class="rank-meter" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="${id}"><stop stop-color="${color[0]}"/><stop offset="1" stop-color="${color[1]}"/></linearGradient></defs><rect width="${Math.max(0,Math.min(100,percent))}" height="6" fill="url(#${id})"/></svg>`}
function renderRank(rs){let v=countBy(rs,'municipality').filter(([x])=>x&&x!=='Onbekend').slice(0,8),max=v[0]?.[1]||1;$('#municipality-list').innerHTML=v.length?v.map(([name,n],i)=>`<div class="rank" data-city="${name.replaceAll('&','&amp;').replaceAll('"','&quot;')}" role="button" tabindex="0" title="Zoom to ${cityLabel(name)}"><span class="index">${String(i+1).padStart(2,'0')}</span><span class="name" title="${name}">${cityLabel(name)}</span><span class="value">${fmt(n)}</span><div class="track">${rankMeter(100*n/max,'municipality-meter-'+i)}</div></div>`).join(''):'<div class="empty">No records for this selection</div>';$('#municipality-list').querySelectorAll('[data-city]').forEach(el=>{el.addEventListener('click',()=>zoomMunicipality(el.dataset.city));el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();zoomMunicipality(el.dataset.city)}})})}
function setLocalRanking(mode){localRanking=mode;$('#show-provinces').classList.toggle('chosen',mode==='province');$('#show-municipalities').classList.toggle('chosen',mode==='municipality');$('#province-list').hidden=mode!=='province';$('#municipality-list').hidden=mode!=='municipality';$('#local-title').textContent=mode==='province'?'Provinces with most crashes':'Municipalities with most crashes';$('#local-subtitle').textContent=mode==='province'?'Click a province to filter the dashboard and zoom to it.':'Click a municipality to zoom in.';$('#local-footnote').textContent=mode==='province'?'Brussels-Capital is shown as a region because it is not a province. Counts are not risk rates.':'High counts can reflect more residents or traffic. This is not a risk ranking.'}
function renderProvinceRank(){const base=rows.filter(r=>matches(r,false,true)),v=countBy(base,'province'),max=v[0]?.[1]||1;$('#province-list').innerHTML=v.length?v.map(([name,n],i)=>`<div class="rank ${sel.province.value===name?'selected':''}" data-province="${name.replaceAll('&','&amp;').replaceAll('"','&quot;')}" role="button" tabindex="0" title="Filter to ${displayLabel(name,'province')}"><span class="index">${String(i+1).padStart(2,'0')}</span><span class="name">${displayLabel(name,'province')}</span><span class="value">${fmt(n)}</span><div class="track">${rankMeter(100*n/max,'province-meter-'+i)}</div></div>`).join(''):'<div class="empty">No records for this selection</div>';$('#province-list').querySelectorAll('[data-province]').forEach(el=>{const choose=()=>{sel.province.value=sel.province.value===el.dataset.province?'':el.dataset.province;render();if(sel.province.value)zoomProvince(sel.province.value);else mapHome()};el.addEventListener('click',choose);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose()}})})}
function barChart(el,values,{height=225,maxItems=8,short=false,filter=null}={}){
  const target=$(el),v=values.slice(0,maxItems),w=650,h=height,l=short?175:115,r=55,row=(h-22)/Math.max(v.length,1),max=Math.max(1,...v.map(x=>x[1]));
  if(!v.length){target.innerHTML='<div class="empty">No data for this selection</div>';return}
  target.innerHTML=`<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Bar chart">${v.map(([name,n],i)=>{const y=12+i*row,bw=(w-l-r)*n/max,full=displayLabel(name,filter),label=full.length>(short?27:18)?full.slice(0,short?26:17)+'…':full;return `<g class="${filter?'chart-hit':''}" data-bar="${i}" ${filter?'role="button" tabindex="0"':''}><title>${full}: ${fmt(n)}</title><text x="${l-10}" y="${y+row*.56}" text-anchor="end" class="bar-label">${label.replaceAll('&','&amp;').replaceAll('<','&lt;')}</text><rect x="${l}" y="${y+row*.17}" width="${Math.max(1,bw)}" height="${row*.54}" rx="3" fill="${i===0?COLORS.blue:'#8fb4c4'}"/><text x="${Math.min(w-r+8,l+bw+7)}" y="${y+row*.57}" class="value-text">${fmt(n)}</text></g>`}).join('')}</svg>`;
  if(filter)target.querySelectorAll('[data-bar]').forEach(g=>{const choose=()=>{sel[filter].value=v[+g.dataset.bar][0];render()};g.addEventListener('click',choose);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose()}})});
}
function renderRoad(rs){barChart('#road-chart',countBy(rs,'road'),{maxItems:5,filter:'road'})}
function renderCollisions(rs){barChart('#collision-chart',countBy(rs,'collision'),{height:315,maxItems:11,short:true,filter:'collision'})}
function renderSeverity(rs,base){
  const denominator=new Map(),numerator=new Map();
  for(const r of base)denominator.set(r.collision,(denominator.get(r.collision)||0)+1);
  for(const r of rs)if(sel.severity.value||severe(r.severity))numerator.set(r.collision,(numerator.get(r.collision)||0)+1);
  const label=sel.severity.value==='Fatal crashes'?'Fatal':sel.severity.value==='Slight injury'?'Slight-injury':'Severe';
  $('#severity-chart-title').textContent=`${label} share by crash type`;
  $('#severity-chart-note').textContent=sel.severity.value?'Percentage within each type under the other active filters; at least 30 source records per type.':'Types with at least 30 selected records; percentage within each type.';
  const values=[...denominator].filter(([,n])=>n>=30).map(([name,n])=>({name,n,selected:numerator.get(name)||0,rate:100*(numerator.get(name)||0)/n})).sort((a,b)=>b.rate-a.rate);
  const target=$('#severity-chart');if(!values.length){target.innerHTML='<div class="empty">At least 30 records per type needed</div>';return}
  const w=680,h=Math.max(325,values.length*30+28),l=225,r=100,t=10,b=30,row=(h-t-b)/values.length,max=Math.max(5,Math.ceil(Math.max(...values.map(x=>x.rate))/5)*5);
  target.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${label} share by crash type">
    ${[0,max/2,max].map(v=>`<line x1="${l+(w-l-r)*v/max}" x2="${l+(w-l-r)*v/max}" y1="${t}" y2="${h-b}" stroke="${COLORS.grid}"/><text x="${l+(w-l-r)*v/max}" y="${h-7}" text-anchor="middle" class="axis-text">${pct(v)}</text>`).join('')}
    ${values.map((v,i)=>{const y=t+i*row+row*.17,width=(w-l-r)*v.rate/max,full=crashLabel(v.name),name=full.length>31?full.slice(0,30)+'…':full;return `<g><title>${full}: ${fmt(v.selected)} of ${fmt(v.n)} crashes (${pct(v.rate)})</title><text x="${l-10}" y="${y+row*.46}" text-anchor="end" class="bar-label">${name.replaceAll('&','&amp;')}</text><rect x="${l}" y="${y}" width="${Math.max(1,width)}" height="${row*.56}" rx="3" fill="${i===0?COLORS.orange:COLORS.pale}"/><text x="${Math.min(w-r+7,l+width+7)}" y="${y+row*.46}" class="value-text">${pct(v.rate)}</text></g>`}).join('')}
  </svg>`;
}
function renderTrend(){
  const counts=new Map(data.meta.years.map(y=>[y,0]));
  for(const r of rows)if(matches(r,true))counts.set(r.year,(counts.get(r.year)||0)+1);
  const v=[...counts],values=v.map(x=>x[1]),min=Math.min(...values),max=Math.max(...values),w=660,h=230,l=46,rr=16,t=25,b=34;
  const fixed=min>=25000&&max<=40000;
  const low=fixed?25000:Math.max(0,Math.floor((min-Math.max(1000,(max-min)*.2))/5000)*5000);
  const high=fixed?40000:Math.max(low+5000,Math.ceil((max+Math.max(1000,(max-min)*.2))/5000)*5000);
  const ticks=fixed?[25000,30000,35000,40000]:[low,(low+high)/2,high];
  const x=i=>l+i*(w-l-rr)/(v.length-1),y=n=>h-b-(h-b-t)*(n-low)/(high-low);
  const path=v.map(([yr,n],i)=>`${i?'L':'M'}${x(i)},${y(n)}`).join(' ');
  $('#trend').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Yearly recorded crashes, line chart">${ticks.map(n=>`<line x1="${l}" y1="${y(n)}" x2="${w-rr}" y2="${y(n)}" stroke="${COLORS.grid}"/><text x="${l-7}" y="${y(n)+4}" text-anchor="end" class="axis-text">${fmt(Math.round(n))}</text>`).join('')}<path d="${path}" fill="none" stroke="#175f80" stroke-width="3" stroke-linejoin="round"/>${v.map(([year,n],i)=>`<g class="chart-hit" data-trend-year="${year}" tabindex="0" role="button" aria-label="Select ${year}, ${fmt(n)} crashes"><circle cx="${x(i)}" cy="${y(n)}" r="${sel.year.value==year?7:5}" fill="${sel.year.value==year?COLORS.orange:COLORS.blue}" stroke="white" stroke-width="2"/><title>${year}: ${fmt(n)} crashes</title><text x="${x(i)}" y="${h-9}" text-anchor="middle" class="axis-text">${year}</text></g>`).join('')}</svg>`;
  $('#trend').querySelectorAll('[data-trend-year]').forEach(el=>{const choose=()=>{sel.year.value=el.dataset.trendYear;render()};el.addEventListener('click',choose);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose()}})});
  $('#trend-desc').textContent='Region, road type, crash type and severity stay active; click a year to select it.';
}
function download(){let selected=rows.filter(r=>matches(r)),cols=['year','month','region','province','road_type','crash_type','severity_code','weather','municipality','mappable'];let csv=[cols.join(';'),...selected.map(r=>[r.year,r.month,r.region,r.province,r.road,r.collision,r.severity,r.weather,r.municipality,r.valid?'yes':'no'].map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(';'))].join('\n');let url=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='belgian_crashes_selection.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
Promise.all(['data.json?v=fatal-filter-20261109','roads.json','vehicles.json?v=fatal-filter-20261109','fatal_routes.json?v=fatal-routes-all-years-20261109'].map(name=>fetch(name).then(r=>{if(!r.ok)throw Error(name+' unavailable');return r.json()}))).then(([x,roads,vehicles,fatalRoutes])=>{data=x;roadVectors=roads;vehicleData=vehicles;window.fatalRouteData=fatalRoutes;init()}).catch(e=>{$('#scope').textContent='Loading failed';document.querySelector('.map-wrap').innerHTML='<p class="empty">Start the local server as described in README.md to open the dashboard.</p>';console.error(e)});
