let vehicleData;
const vehicleNames={
  'Stadswagens':'City cars',"Compacte auto's":'Compact cars',
  'Motoren en bromfietsen':'Motorcycles & mopeds','SUV':'SUVs','sedans':'Sedans',
  'Monovolumes (klein en groot) en ludospace':'MPVs & people carriers',
  'Pick-up, bestelwagen, bestelwagen of bedrijfswagen':'Vans & pick-ups',
  'Vrachtwagens en bussen':'Trucks & buses','Sportwagens':'Sports cars',
  'Onbekend':'Unknown'
};
const mixTypes=[
  ['Pedestrian','Met een voetganger'],['Rear-end','Tussen 2 bestuurders: Langs achteren'],
  ['Side impact','Tss. 2 best.: langs opzij (voor-/achterkant-flank)'],
  ['Multi-vehicle','Kettingbotsing (3 bestuurders of meer)'],
  ['Off-road object','Weggebruiker tegen hindernis buiten rijbaan'],
  ['Head-on','Tussen 2 bestuurders: Frontale botsing'],
  ['Sideswipe','Tussen 2 bestuurders: Flank tegen flank'],
  ['Single / fall','single-fall']
];
const vehicleOrder=['City cars','Compact cars','SUVs','Sedans','Vans & pick-ups','Trucks & buses','Motorcycles & mopeds','MPVs & people carriers','Sports cars'];
function vehicleRows(){
  const c=vehicleData.meta.categories;
  return vehicleData.rows.map(r=>({year:r[0],region:c.region[r[1]],province:c.province[r[2]],road:c.road[r[3]],collision:c.collision[r[4]],severity:c.severity[r[5]],weather:c.weather[r[6]],vehicle:vehicleNames[c.vehicle[r[7]]]||c.vehicle[r[7]],count:r[8]}));
}
function vehicleMatches(r,withoutSeverity=false){
  return (!sel.year.value||r.year===+sel.year.value)&&(!sel.region.value||r.region===sel.region.value)
    &&(!sel.province.value||r.province===sel.province.value)&&(!sel.road.value||r.road===sel.road.value)
    &&(!sel.collision.value||r.collision===sel.collision.value)
    &&(!sel.weather.value||r.weather===sel.weather.value)
    &&(!sel.severity.value||withoutSeverity||(sel.severity.value==='Fatal crashes'?r.severity==='met doden':sel.severity.value==='Severe'?vehicleSevere(r.severity):r.severity==='met lichtgewonden'));
}
function vehicleSevere(s){return s==='met zwaargewonden'||s==='met doden'||s==='met dodelijk gewonden'}
function vehicleEmpty(id){$(id).innerHTML='<div class="empty">No vehicle records for this selection</div>'}
function vehicleBars(id,values,percent=false,measureLabel='severe'){
  const w=780,h=362,l=218,r=145,t=10,b=35,row=(h-t-b)/Math.max(values.length,1);
  const max=Math.max(1,...values.map(x=>percent?x.rate:x.n));
  const axisMax=percent?Math.max(5,Math.ceil(max/5)*5):Math.ceil(max/1000)*1000;
  const ticks=percent?[0,axisMax/2,axisMax]:[0,axisMax/2,axisMax];
  $(id).innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${percent?measureLabel+' share':'Involved vehicles'} by vehicle type">
    ${ticks.map(v=>`<line x1="${l+(w-l-r)*v/axisMax}" x2="${l+(w-l-r)*v/axisMax}" y1="${t}" y2="${h-b}" stroke="#e5ecef"/><text x="${l+(w-l-r)*v/axisMax}" y="${h-8}" text-anchor="middle" class="axis-text">${percent?pct(v):fmt(Math.round(v))}</text>`).join('')}
    ${values.map((v,i)=>{const width=(w-l-r)*(percent?v.rate:v.n)/axisMax,y=t+i*row+row*.18,accent=percent?(v.name==='Trucks & buses'||v.name==='Motorcycles & mopeds'):(v.name==='Motorcycles & mopeds'||v.name==='SUVs');return `<g><title>${v.name}: ${percent?`${pct(v.rate)} ${measureLabel.toLowerCase()} (${fmt(v.selected)} of ${fmt(v.n)} involved vehicles)`:`${fmt(v.n)} involved vehicles`}</title><text x="${l-12}" y="${y+row*.47}" text-anchor="end" class="bar-label">${v.name}</text><rect x="${l}" y="${y}" width="${Math.max(1,width)}" height="${row*.60}" rx="4" fill="${accent?'#e47c44':'#2186a0'}"/><text x="${Math.min(w-r+9,l+width+9)}" y="${y+row*.47}" class="value-text">${percent?`${pct(v.rate)} · n=${fmt(v.n)}`:fmt(v.n)}</text></g>`}).join('')}
  </svg>`;
}
function vehicleMix(rs,summary){
  const target=$('#vehicle-mix-chart');
  const types=sel.collision.value?mixTypes.filter(([,raw])=>raw===sel.collision.value||(raw==='single-fall'&&sel.collision.value.includes('geen hindernis'))):mixTypes;
  if(!types.length){vehicleEmpty('#vehicle-mix-chart');return}
  const names=vehicleOrder.filter(name=>(summary.get(name)?.n||0)>0);
  const lookup=new Map();
  for(const r of rs){const key=r.vehicle+'|'+r.collision;lookup.set(key,(lookup.get(key)||0)+r.count)}
  const w=900,l=190,r=22,t=28,b=52,row=43,h=t+names.length*row+b,cell=(w-l-r)/types.length;
  target.innerHTML=`<div class="vehicle-heat-scroll"><svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Collision type shares by vehicle type">
    ${types.map(([name],j)=>`<text x="${l+(j+.5)*cell}" y="18" text-anchor="middle" class="axis-text">${name}</text>`).join('')}
    ${names.map((name,i)=>`<text x="${l-10}" y="${t+i*row+row*.57}" text-anchor="end" class="bar-label">${name}</text>${types.map(([,raw],j)=>{const n=raw==='single-fall'?[...lookup].filter(([key])=>key.startsWith(name+'|')&&key.includes('geen hindernis')).reduce((sum,[,v])=>sum+v,0):(lookup.get(name+'|'+raw)||0);const share=100*n/summary.get(name).n,alpha=.12+.78*Math.min(share/40,1);return `<g><title>${name} · ${raw==='single-fall'?'Single vehicle / fall':crashLabel(raw)}: ${pct(share)} (${fmt(n)} of ${fmt(summary.get(name).n)} vehicles)</title><rect x="${l+j*cell+2}" y="${t+i*row+2}" width="${cell-4}" height="${row-4}" rx="5" fill="rgba(22,103,137,${alpha.toFixed(3)})"/><text x="${l+(j+.5)*cell}" y="${t+i*row+row*.58}" text-anchor="middle" class="heat-value ${share>18?'light':''}">${Math.round(share)}%</text></g>`}).join('')}`).join('')}
    <text x="${l}" y="${h-14}" class="axis-text">Percent of all selected records in each vehicle type</text>
  </svg></div>`;
}
function renderVehicles(){
  if(!vehicleData)return;
  const all=vehicleRows(),rs=all.filter(r=>vehicleMatches(r)),base=sel.severity.value?all.filter(r=>vehicleMatches(r,true)):rs;
  const summary=new Map(),denominators=new Map();let selected=0,unknown=0;
  for(const r of rs){selected+=r.count;if(r.vehicle==='Unknown'){unknown+=r.count;continue}const v=summary.get(r.vehicle)||{name:r.vehicle,n:0};v.n+=r.count;summary.set(r.vehicle,v)}
  for(const r of base){if(r.vehicle==='Unknown')continue;const v=denominators.get(r.vehicle)||{name:r.vehicle,n:0,selected:0};v.n+=r.count;if(!sel.severity.value&&vehicleSevere(r.severity))v.selected+=r.count;denominators.set(r.vehicle,v)}
  if(sel.severity.value)for(const r of rs){if(r.vehicle!=='Unknown')denominators.get(r.vehicle).selected+=r.count}
  $('#vehicle-scope').textContent=`${fmt(selected)} involved vehicles in this selection · ${sel.year.value||'2017–2024'}${unknown?` · ${fmt(unknown)} unknown type omitted from charts`:''}`;
  const label=sel.severity.value==='Fatal crashes'?'Fatal-crash':sel.severity.value==='Slight injury'?'Slight-injury':'Severe-crash';
  $('#vehicle-severity-title').textContent=`${label} share by vehicle type`;
  $('#vehicle-severity-note').textContent=sel.severity.value?'Share within each vehicle type under the other active filters.':'Share of involved vehicles linked to a crash with serious injury or death.';
  if(!summary.size){['#vehicle-count-chart','#vehicle-severity-chart','#vehicle-mix-chart'].forEach(vehicleEmpty);return}
  vehicleBars('#vehicle-count-chart',[...summary.values()].sort((a,b)=>b.n-a.n));
  const rates=[...denominators.values()].map(v=>({...v,rate:100*v.selected/v.n})).sort((a,b)=>b.rate-a.rate);
  vehicleBars('#vehicle-severity-chart',rates,true,label);
  vehicleMix(rs,summary);
}
