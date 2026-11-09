const fatalCrash=r=>r.severity==='1';
function renderFatality(rs){
  const fatal=rs.filter(fatalCrash),baseline=rows.filter(r=>matches(r,false,false,false,true));
  $('#fatal-count').textContent=fmt(fatal.length);
  $('#fatal-share').textContent=baseline.length?pct(100*fatal.length/baseline.length):'—';
  renderFatalBreakdowns(fatal,baseline);renderFatalTrend();renderFatalWeather(rs);renderFatalTypes(fatal);
}
function fatalRank(targetId,items,labelKind,filterKey){
  const target=$(targetId),max=items[0]?.count||1,esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
  if(!items.length){target.innerHTML='<div class="empty">No fatal crashes under these filters</div>';return}
  target.innerHTML=items.map((item,i)=>{
    const label=labelKind?displayLabel(item.name,labelKind):item.name;
    const detail=item.detail||(item.total?`${pct(100*item.count/item.total)} of ${fmt(item.total)} injury crashes`:'');
    return `<div class="fatal-rank ${filterKey?'chart-hit':''}" data-rank="${i}" ${filterKey?'role="button" tabindex="0"':''} title="${esc(label)}: ${fmt(item.count)} fatal crashes${detail?' · '+esc(detail):''}"><span class="fatal-rank-label">${esc(label)}</span><strong>${fmt(item.count)}</strong><span class="fatal-rank-track"><span style="width:${100*item.count/max}%"></span></span>${detail?`<small>${esc(detail)}</small>`:''}</div>`
  }).join('');
  if(filterKey)target.querySelectorAll('[data-rank]').forEach(el=>{const choose=()=>{const value=items[+el.dataset.rank].name;if(filterKey==='municipality'){zoomMunicipality(value)}else{sel[filterKey].value=value;render()}};el.addEventListener('click',choose);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose()}})});
}
function renderFatalBreakdowns(fatal,baseline){
  for(const [key,target,limit] of [['road','#fatal-road-chart',4],['region','#fatal-region-chart',3],['municipality','#fatal-municipality-chart',10]]){
    const totals=new Map(countBy(baseline,key)),counts=countBy(fatal,key);
    fatalRank(target,counts.filter(([name])=>key!=='road'||name!=='onbekend').slice(0,limit).map(([name,count])=>({name,count,total:key==='municipality'?null:totals.get(name)||0})),key,key);
  }
  const target=$('#fatal-route-chart');
  if(!window.fatalRouteData){target.innerHTML='<div class="empty">Route matches unavailable</div>';return}
  const selected=window.fatalRouteData.rows.filter(r=>(!sel.year.value||r.year===+sel.year.value)&&(!sel.region.value||r.region===sel.region.value)&&(!sel.province.value||r.province===sel.province.value)&&(!sel.road.value||r.road===sel.road.value)&&(!sel.collision.value||r.collision===sel.collision.value)&&(!sel.weather.value||r.weather===sel.weather.value)&&(!sel.severity.value||sel.severity.value!=='Slight injury'));
  const counts=new Map();for(const r of selected)counts.set(r.ref,(counts.get(r.ref)||0)+1);
  fatalRank('#fatal-route-chart',[...counts].sort((a,b)=>b[1]-a[1]).slice(0,8).map(([name,count])=>({name,count,detail:'Approximate nearby OSM route match'})),null,null);
  const total=fatal.filter(r=>r.road==='Autosnelweg').length;
  $('#fatal-route-note').textContent=`${fmt(selected.length)} named-route matches of ${fmt(total)} fatal motorway-class crashes in this selection. Missing coordinates and unmatched roads are excluded. A nearby OSM route is not a verified crash road.`;
}
function renderFatalTrend(){
  const years=data.meta.years,counts=years.map(y=>rows.reduce((n,r)=>n+(r.year===y&&matches(r,true)&&fatalCrash(r)?1:0),0));
  const target=$('#fatal-trend-chart');
  if(!counts.some(Boolean)){target.innerHTML='<div class="empty">No fatal crashes under these filters. Clear the severity filter if it is set to Slight injury.</div>';return}
  const w=660,h=240,l=42,r=20,t=18,b=39,max=Math.max(100,Math.ceil(Math.max(...counts)/100)*100);
  const x=i=>l+i*(w-l-r)/(years.length-1),y=v=>h-b-(h-b-t)*v/max;
  target.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Fatal crashes by year">
    ${[0,max/2,max].map(v=>`<line x1="${l}" x2="${w-r}" y1="${y(v)}" y2="${y(v)}" stroke="#e5ecef"/><text x="${l-7}" y="${y(v)+4}" text-anchor="end" class="axis-text">${fmt(v)}</text>`).join('')}
    <path d="${counts.map((v,i)=>`${i?'L':'M'}${x(i)},${y(v)}`).join(' ')}" fill="none" stroke="#c85740" stroke-width="3" stroke-linejoin="round"/>
    ${counts.map((v,i)=>`<g data-fatal-year="${years[i]}" class="chart-hit" role="button" tabindex="0" aria-label="Select ${years[i]}, ${fmt(v)} fatal crashes"><circle cx="${x(i)}" cy="${y(v)}" r="${sel.year.value==years[i]?7:5}" fill="${sel.year.value==years[i]?'#e47c44':'#c85740'}" stroke="white" stroke-width="2"/><title>${years[i]}: ${fmt(v)} fatal crashes</title><text x="${x(i)}" y="${h-10}" text-anchor="middle" class="axis-text">${years[i]}</text></g>`).join('')}
  </svg>`;
  target.querySelectorAll('[data-fatal-year]').forEach(el=>{const choose=()=>{sel.year.value=el.dataset.fatalYear;render()};el.addEventListener('click',choose);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose()}})});
}
function renderFatalWeather(rs){
  const groups=new Map();for(const r of rs){const v=groups.get(r.weather)||[0,0];v[0]++;if(fatalCrash(r))v[1]++;groups.set(r.weather,v)}
  if(sel.severity.value==='Fatal crashes'){
    const values=[...groups].filter(([,v])=>v[1]>0).map(([name,[,fatal]])=>({name,fatal})).sort((a,b)=>b.fatal-a.fatal);
    const target=$('#fatal-weather-chart');
    $('#fatal-weather-title').textContent='Fatal crashes by weather';
    $('#fatal-weather-note').textContent='Counts of selected fatal crashes by recorded weather; no traffic-exposure denominator.';
    if(!values.length){target.innerHTML='<div class="empty">No fatal crashes under these filters</div>';return}
    const w=660,h=Math.max(240,values.length*34+45),l=130,r=75,t=12,b=32,row=(h-t-b)/values.length,max=values[0].fatal;
    target.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Fatal crashes by weather">
      ${[0,max/2,max].map(v=>`<line x1="${l+(w-l-r)*v/max}" x2="${l+(w-l-r)*v/max}" y1="${t}" y2="${h-b}" stroke="#e5ecef"/><text x="${l+(w-l-r)*v/max}" y="${h-7}" text-anchor="middle" class="axis-text">${fmt(Math.round(v))}</text>`).join('')}
      ${values.map((v,i)=>{const y=t+i*row+row*.18,width=(w-l-r)*v.fatal/max;return `<g><title>${v.name}: ${fmt(v.fatal)} fatal crashes</title><text x="${l-10}" y="${y+row*.47}" text-anchor="end" class="bar-label">${v.name}</text><rect x="${l}" y="${y}" width="${Math.max(1,width)}" height="${row*.58}" rx="3" fill="${i===0?'#c85740':'#d99877'}"/><text x="${Math.min(w-r+8,l+width+7)}" y="${y+row*.47}" class="value-text">${fmt(v.fatal)}</text></g>`}).join('')}
    </svg>`;
    return;
  }
  const values=[...groups].filter(([,v])=>v[0]>=100).map(([name,[n,fatal]])=>({name,n,fatal,rate:100*fatal/n})).sort((a,b)=>b.rate-a.rate);
  const target=$('#fatal-weather-chart');
  $('#fatal-weather-title').textContent='Fatal-crash share by weather';
  const scope=sel.severity.value?` The ${sel.severity.value.toLowerCase()} filter also changes the denominator.`:'';
  $('#fatal-weather-note').textContent=(sel.weather.value?'Weather filter is active; clear it to compare conditions.':'Share within each recorded weather category; minimum 100 selected crashes.')+scope;
  if(!values.length){target.innerHTML='<div class="empty">At least 100 selected crashes per weather category are needed</div>';return}
  const w=660,h=Math.max(240,values.length*34+45),l=130,r=112,t=12,b=32,row=(h-t-b)/values.length,max=Math.max(2,Math.ceil(Math.max(...values.map(x=>x.rate))/2)*2);
  target.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Fatal-crash share by weather">
    ${[0,max/2,max].map(v=>`<line x1="${l+(w-l-r)*v/max}" x2="${l+(w-l-r)*v/max}" y1="${t}" y2="${h-b}" stroke="#e5ecef"/><text x="${l+(w-l-r)*v/max}" y="${h-7}" text-anchor="middle" class="axis-text">${pct(v)}</text>`).join('')}
    ${values.map((v,i)=>{const y=t+i*row+row*.18,width=(w-l-r)*v.rate/max;return `<g><title>${v.name}: ${fmt(v.fatal)} fatal of ${fmt(v.n)} injury crashes (${pct(v.rate)})</title><text x="${l-10}" y="${y+row*.47}" text-anchor="end" class="bar-label">${v.name}</text><rect x="${l}" y="${y}" width="${Math.max(1,width)}" height="${row*.58}" rx="3" fill="${i===0?'#c85740':'#d99877'}"/><text x="${Math.min(w-r+8,l+width+7)}" y="${y+row*.47}" class="value-text">${pct(v.rate)} · n=${fmt(v.n)}</text></g>`}).join('')}
  </svg>`;
}
function renderFatalTypes(fatal){
  const groups=new Map();for(const r of fatal)groups.set(r.collision,(groups.get(r.collision)||0)+1);
  const values=[...groups].sort((a,b)=>b[1]-a[1]),target=$('#fatal-type-chart');
  if(!values.length){target.innerHTML='<div class="empty">No fatal crashes under these filters</div>';return}
  const w=750,h=Math.max(300,values.length*31+20),l=205,r=82,t=8,b=12,row=(h-t-b)/values.length,max=values[0][1];
  target.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Fatal crashes by collision type">
    ${values.map(([name,n],i)=>{const y=t+i*row+row*.18,width=(w-l-r)*n/max,label=crashLabel(name);return `<g><title>${label}: ${fmt(n)} fatal crashes</title><text x="${l-10}" y="${y+row*.48}" text-anchor="end" class="bar-label">${label}</text><rect x="${l}" y="${y}" width="${Math.max(1,width)}" height="${row*.57}" rx="3" fill="${i===0?'#c85740':'#d99877'}"/><text x="${Math.min(w-r+8,l+width+8)}" y="${y+row*.48}" class="value-text">${fmt(n)}</text></g>`}).join('')}
  </svg>`;
}
