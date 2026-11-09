const fatalCrash=r=>r.severity==='1';
function renderFatality(rs){
  const fatal=rs.filter(fatalCrash),n=rs.length;
  $('#fatal-count').textContent=fmt(fatal.length);
  $('#fatal-share').textContent=n?pct(100*fatal.length/n):'—';
  renderFatalTrend();renderFatalWeather(rs);renderFatalTypes(fatal);
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
  const values=[...groups].filter(([,v])=>v[0]>=100).map(([name,[n,fatal]])=>({name,n,fatal,rate:100*fatal/n})).sort((a,b)=>b.rate-a.rate);
  const target=$('#fatal-weather-chart');
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
