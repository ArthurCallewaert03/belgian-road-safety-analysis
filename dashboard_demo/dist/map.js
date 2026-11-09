// All geometry and crash locations use Lambert 72 (EPSG:31370).
let roadVectors = null;
let mapScene = 'heat';
const mapCanvas = $('#map');
const mapView = {cx:null, cy:null, zoom:1, scale:1, drag:null, cells:[], points:[], cities:[], cache:null, selectedRoute:null};
const heatStops = [[255,248,224],[254,215,133],[253,141,60],[220,73,62],[132,45,91]];
const polygonParts = () => shape.type === 'Polygon' ? [shape.coordinates] : shape.coordinates;

function mapBounds() {
  let minx=Infinity,miny=Infinity,maxx=-Infinity,maxy=-Infinity;
  for (const poly of polygonParts()) for (const ring of poly) for (const [x,y] of ring) {
    minx=Math.min(minx,x); maxx=Math.max(maxx,x); miny=Math.min(miny,y); maxy=Math.max(maxy,y);
  }
  return {minx,miny,maxx,maxy};
}
function mapColor(t) {
  const q=Math.max(0,Math.min(.999,t))*(heatStops.length-1),i=Math.floor(q),f=q-i;
  return `rgb(${heatStops[i].map((v,j)=>Math.round(v+(heatStops[i+1][j]-v)*f)).join(',')})`;
}
function screen(x,y,w,h) {return [w/2+(x-mapView.cx)*mapView.scale,h/2-(y-mapView.cy)*mapView.scale]}
function world(x,y,w,h) {return [mapView.cx+(x-w/2)/mapView.scale,mapView.cy-(y-h/2)/mapView.scale]}
function baseScale(w,h) {const b=mapBounds();return Math.min((w-36)/(b.maxx-b.minx),(h-36)/(b.maxy-b.miny))}
function setScene(scene) {
  mapScene=scene;
  mapView.selectedRoute=null;
  $('#route-panel').innerHTML='<div><span class="sectionlabel">ROUTE INSPECTOR</span><h3>Click a road on the map</h3><p>Inspect its OSM name and crash records near the clicked location. Zoom in for local streets around Brussels.</p></div>';
  document.querySelectorAll('[data-scene]').forEach(b=>b.classList.toggle('chosen',b.dataset.scene===scene));
  $('#map-modes').hidden=scene==='network';
  if(scene==='network') mapHome();
  else if(scene==='detail') zoomBrusselsWindow();
  else renderMap(window.currentRows);
}
function zoomAt(factor,px,py) {
  const r=mapCanvas.getBoundingClientRect(),x=px??r.width/2,y=py??r.height/2;
  const [wx,wy]=world(x,y,r.width,r.height);
  mapView.zoom=Math.max(1,Math.min(80,mapView.zoom*factor));mapView.scale=baseScale(r.width,r.height)*mapView.zoom;
  mapView.cx=wx-(x-r.width/2)/mapView.scale;mapView.cy=wy+(y-r.height/2)/mapView.scale;
  renderMap(window.currentRows);
}
function mapHome() {
  const b=mapBounds();mapView.cx=(b.minx+b.maxx)/2;mapView.cy=(b.miny+b.maxy)/2;mapView.zoom=1;
  $('#city').value='';renderMap(window.currentRows);
}
function zoomToBox(minx,miny,maxx,maxy) {
  const r=mapCanvas.getBoundingClientRect();mapView.cx=(minx+maxx)/2;mapView.cy=(miny+maxy)/2;
  mapView.zoom=Math.max(1,Math.min(80,Math.min((r.width-55)/(maxx-minx),(r.height-55)/(maxy-miny))/baseScale(r.width,r.height)));
  renderMap(window.currentRows);
}
function zoomBrusselsWindow() {
  $('#city').value='Brussel';zoomToBox(140000,160000,160000,180000);
  $('#map-section').scrollIntoView({behavior:'smooth',block:'start'});
}
function zoomMunicipality(city) {
  const points=rows.filter(r=>r.valid&&r.municipality===city&&r.x!=null);
  if(!points.length)return;
  let minx=Infinity,miny=Infinity,maxx=-Infinity,maxy=-Infinity;
  for(const p of points){minx=Math.min(minx,p.x);maxx=Math.max(maxx,p.x);miny=Math.min(miny,p.y);maxy=Math.max(maxy,p.y)}
  $('#city').value=city;
  zoomToBox(minx-1500,miny-1500,maxx+1500,maxy+1500);
  $('#map-section').scrollIntoView({behavior:'smooth',block:'start'});
}
function zoomProvince(province) {
  const points=rows.filter(r=>r.valid&&r.province===province&&r.x!=null);
  if(!points.length)return;
  let minx=Infinity,miny=Infinity,maxx=-Infinity,maxy=-Infinity;
  for(const p of points){minx=Math.min(minx,p.x);maxx=Math.max(maxx,p.x);miny=Math.min(miny,p.y);maxy=Math.max(maxy,p.y)}
  $('#city').value='';
  zoomToBox(minx-5000,miny-5000,maxx+5000,maxy+5000);
}
function initMapControls() {
  const city=$('#city');city.innerHTML='<option value="">Choose a municipality…</option>'+cats.municipality.filter(x=>x&&x!=='Onbekend').map(x=>`<option value="${escapeMapText(x)}">${escapeMapText(cityLabel(x))}</option>`).join('');
  city.addEventListener('change',()=>city.value?zoomMunicipality(city.value):mapHome());
  $('#zoom-brussels').addEventListener('click',zoomBrusselsWindow);
  $('#zoom-in').addEventListener('click',()=>zoomAt(1.6));$('#zoom-out').addEventListener('click',()=>zoomAt(1/1.6));$('#zoom-home').addEventListener('click',mapHome);
  document.querySelectorAll('[data-scene]').forEach(b=>b.addEventListener('click',()=>setScene(b.dataset.scene)));
  mapCanvas.addEventListener('wheel',e=>{e.preventDefault();const r=mapCanvas.getBoundingClientRect();zoomAt(e.deltaY<0?1.35:1/1.35,e.clientX-r.left,e.clientY-r.top)},{passive:false});
  mapCanvas.addEventListener('pointerdown',e=>{mapView.drag={x:e.clientX,y:e.clientY,cx:mapView.cx,cy:mapView.cy};mapCanvas.setPointerCapture(e.pointerId);mapCanvas.classList.add('dragging')});
  mapCanvas.addEventListener('pointermove',e=>{if(mapView.drag){mapView.cx=mapView.drag.cx-(e.clientX-mapView.drag.x)/mapView.scale;mapView.cy=mapView.drag.cy+(e.clientY-mapView.drag.y)/mapView.scale;renderMap(window.currentRows)}else hoverMap(e)});
  mapCanvas.addEventListener('pointerup',e=>{const moved=mapView.drag&&Math.hypot(e.clientX-mapView.drag.x,e.clientY-mapView.drag.y);mapView.drag=null;mapCanvas.classList.remove('dragging');if(moved<5)inspectRoute(e)});
  mapCanvas.addEventListener('pointercancel',()=>{mapView.drag=null;mapCanvas.classList.remove('dragging')});
  mapCanvas.addEventListener('pointerleave',()=>$('#map-tip').hidden=true);
}
function drawRoads(ctx,paths,color,width,w,h) {
  if(!paths)return;
  ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();
  const minx=mapView.cx-w/(2*mapView.scale),maxx=mapView.cx+w/(2*mapView.scale),miny=mapView.cy-h/(2*mapView.scale),maxy=mapView.cy+h/(2*mapView.scale);
  for(const line of paths){let first=true;
    for(const [x,y] of line){if(x<minx-3000||x>maxx+3000||y<miny-3000||y>maxy+3000){first=true;continue}
      const [px,py]=screen(x,y,w,h);first?ctx.moveTo(px,py):ctx.lineTo(px,py);first=false}
  }
  ctx.stroke();
}
function aggregateMap(rs,detail) {
  if(mapView.cache?.rows===rs&&mapView.cache.detail===detail&&mapView.cache.mode===mapMode)return mapView.cache;
  const size=detail?500:5000,keyX=detail?'gx500':'gx',keyY=detail?'gy500':'gy',grid=new Map(),cities=new Map(),points=[];
  for(const row of rs){if(!row.valid||row[keyX]==null)continue;
    if(mapMode==='severe'&&!severe(row.severity))continue;
    if(mapMode==='fatal'&&row.severity!=='1')continue;
    if(mapMode==='ped'&&row.collision!=='Met een voetganger')continue;
    const key=row[keyX]+','+row[keyY];let cell=grid.get(key);
    if(!cell){cell={x:row[keyX],y:row[keyY],n:0,severe:0,fatal:0,cities:new Map(),roads:new Map(),types:new Map()};grid.set(key,cell)}
    cell.n++;if(severe(row.severity))cell.severe++;if(row.severity==='1')cell.fatal++;
    for(const [m,k] of [[cell.cities,row.municipality],[cell.roads,row.road],[cell.types,row.collision]])m.set(k,(m.get(k)||0)+1);
    let city=cities.get(row.municipality)||{n:0,sx:0,sy:0};city.n++;city.sx+=row.x;city.sy+=row.y;cities.set(row.municipality,city);
    if(row.x!=null)points.push(row);
  }
  let max=1;for(const c of grid.values())max=Math.max(max,c.n);
  mapView.cache={rows:rs,detail,mode:mapMode,grid,cities,points,max,size};return mapView.cache;
}
function renderMap(rs) {
  if(!rs||!shape)return;
  const rect=mapCanvas.getBoundingClientRect(),w=Math.max(300,rect.width),h=Math.max(270,rect.height),dpr=window.devicePixelRatio||1;
  mapCanvas.width=Math.round(w*dpr);mapCanvas.height=Math.round(h*dpr);
  const ctx=mapCanvas.getContext('2d');ctx.scale(dpr,dpr);
  const b=mapBounds();if(mapView.cx==null){mapView.cx=(b.minx+b.maxx)/2;mapView.cy=(b.miny+b.maxy)/2}
  mapView.scale=baseScale(w,h)*mapView.zoom;
  ctx.fillStyle='#e6f0f5';ctx.fillRect(0,0,w,h);
  const border=new Path2D();for(const poly of polygonParts())for(const ring of poly){ring.forEach(([x,y],i)=>{const [px,py]=screen(x,y,w,h);i?border.lineTo(px,py):border.moveTo(px,py)});border.closePath()}
  ctx.fillStyle='#f7f9f7';ctx.fill(border);ctx.save();ctx.clip(border);
  const detail=mapView.zoom>=7,agg=aggregateMap(rs,detail);
  mapView.cells=[];mapView.points=[];
  if(mapScene==='heat'){
    ctx.globalAlpha=.83;
    for(const cell of agg.grid.values()){const [x,y]=screen(cell.x*agg.size,(cell.y+1)*agg.size,w,h),s=agg.size*mapView.scale;
      if(x+s<0||y+s<0||x>w||y>h)continue;
      ctx.fillStyle=mapColor(Math.log1p(cell.n)/Math.log1p(agg.max));ctx.fillRect(x,y,s+.6,s+.6);
      mapView.cells.push({...cell,px:x,py:y,ps:s})}
    ctx.globalAlpha=1;
  }
  const local=mapView.zoom>=5&&mapView.cx>130000&&mapView.cx<170000&&mapView.cy>150000&&mapView.cy<190000;
  if(local)drawRoads(ctx,roadVectors?.brussels_local,'#bbcad0',.55,w,h);
  drawRoads(ctx,roadVectors?.major,mapScene==='network'?'#8199a8':'#a6b8be',mapView.zoom<5?.55:.75,w,h);
  drawRoads(ctx,roadVectors?.motorways,'#165b82',mapView.zoom<5?1.15:1.7,w,h);
  if(mapView.selectedRoute){const line=mapView.selectedRoute.route[2];ctx.strokeStyle='#f5b547';ctx.lineWidth=4;ctx.beginPath();line.forEach(([xx,yy],i)=>{const [px,py]=screen(xx,yy,w,h);i?ctx.lineTo(px,py):ctx.moveTo(px,py)});ctx.stroke();const [px,py]=screen(mapView.selectedRoute.x,mapView.selectedRoute.y,w,h);ctx.beginPath();ctx.arc(px,py,5,0,Math.PI*2);ctx.fillStyle='#e4733d';ctx.fill()}
  if(mapScene==='detail'){
    ctx.fillStyle='rgba(220,93,48,.48)';
    for(const row of agg.points){const [x,y]=screen(row.x,row.y,w,h);if(x<0||y<0||x>w||y>h)continue;
      ctx.beginPath();ctx.arc(x,y,mapView.zoom>18?2.5:1.8,0,Math.PI*2);ctx.fill();mapView.points.push({x,y,row})}
  }
  ctx.restore();ctx.strokeStyle='#7595a2';ctx.lineWidth=1.2;ctx.stroke(border);
  mapView.cities=[];
  if(mapView.zoom<8){for(const [name,c] of [...agg.cities].sort((a,b)=>b[1].n-a[1].n).slice(0,7)){
    const [x,y]=screen(c.sx/c.n,c.sy/c.n,w,h);if(x<20||x>w-85||y<20||y>h-20)continue;
    ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fillStyle='#11364c';ctx.fill();ctx.font='600 11px sans-serif';ctx.lineWidth=3;ctx.strokeStyle='#fff';ctx.strokeText(cityLabel(name),x+7,y-6);ctx.fillStyle='#11364c';ctx.fillText(cityLabel(name),x+7,y-6);mapView.cities.push({name,x,y,n:c.n})}}
  drawScale(ctx,w,h);
  const visible=mapScene==='detail'?mapView.points.length:mapScene==='heat'?mapView.cells.reduce((s,c)=>s+c.n,0):agg.points.length;
  $('#map-note').textContent=mapScene==='detail'?`${fmt(visible)} crash points in view · points are not assigned to roads`:mapScene==='network'?'OSM road network: motorways and main / secondary roads':`${fmt(visible)} locations in view · ${fmt(mapView.cells.length)} ${detail?'500 m':'5 km'} cells`;
  $('#map-legend').hidden=mapScene!=='heat';$('#local-key').hidden=!local;
  $('#zoom-level').textContent=`${$('#city').value?cityLabel($('#city').value):sel.province.value?displayLabel(sel.province.value,'province'):'Belgium'} · ${mapView.zoom.toFixed(1)}×`;
  $('#map-subtitle').textContent=mapScene==='detail'?'Brussels: local streets and individual crash points from the active selection. Click a road for its route details.':mapScene==='network'?'Main roads reveal the network; click a route, or zoom near Brussels for local streets.':`Recorded locations in ${detail?'500 m':'5 km'} cells; colour uses a logarithmic scale. Click a road to inspect it.`;
  if(mapView.selectedRoute)renderRoutePanel();
}
function drawScale(ctx,w,h){const km=mapView.zoom>=7?5:50,px=km*1000*mapView.scale;if(px>w*.4)return;const x=w-35-px,y=h-28;ctx.strokeStyle='#203e50';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+px,y);ctx.stroke();ctx.fillStyle='#203e50';ctx.font='600 10px sans-serif';ctx.fillText(km+' km',x+px/2-12,y-6);ctx.fillText('N ↑',w-38,26)}
function inspectRoute(e){
  const rect=mapCanvas.getBoundingClientRect(),px=e.clientX-rect.left,py=e.clientY-rect.top,w=rect.width,h=rect.height;
  const local=mapView.zoom>=5&&mapView.cx>130000&&mapView.cx<170000&&mapView.cy>150000&&mapView.cy<190000;
  const candidates=[...(roadVectors?.named_major||[]),...(local?roadVectors?.named_brussels_local||[]:[])];
  let best=null,bestDist=9;
  for(const route of candidates){const line=route[2];for(let i=1;i<line.length;i++){
    const [ax,ay]=screen(line[i-1][0],line[i-1][1],w,h),[bx,by]=screen(line[i][0],line[i][1],w,h);
    if(Math.max(ax,bx)<px-9||Math.min(ax,bx)>px+9||Math.max(ay,by)<py-9||Math.min(ay,by)>py+9)continue;
    const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((px-ax)*dx+(py-ay)*dy)/Math.max(.0001,dx*dx+dy*dy)));
    const d=Math.hypot(px-(ax+t*dx),py-(ay+t*dy));
    if(d<bestDist){bestDist=d;best={route,x:line[i-1][0]+t*(line[i][0]-line[i-1][0]),y:line[i-1][1]+t*(line[i][1]-line[i-1][1])}}
  }}
  if(!best){$('#route-panel').innerHTML='<div><span class="sectionlabel">ROUTE INSPECTOR</span><h3>No named road at this point</h3><p>Click a visible motorway or road. Zoom in around Brussels to inspect local streets.</p></div>';return}
  mapView.selectedRoute=best;renderMap(window.currentRows);
}
function renderRoutePanel(){
  const selected=mapView.selectedRoute;if(!selected)return;
  const [name,kind]=selected.route,radius=mapView.zoom>=7?500:2000,near=[];
  for(const p of window.currentRows||[])if(p.valid&&p.x!=null&&Math.abs(p.x-selected.x)<=radius&&Math.abs(p.y-selected.y)<=radius&&Math.hypot(p.x-selected.x,p.y-selected.y)<=radius)near.push(p);
  const severeCount=near.filter(p=>severe(p.severity)).length,fatalCount=near.filter(p=>p.severity==='1').length,types=new Map();for(const p of near)types.set(p.collision,(types.get(p.collision)||0)+1);
  const top=types.size?crashLabel([...types].sort((a,b)=>b[1]-a[1])[0][0]):'—';
  const roadKind=kind.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
  $('#route-panel').innerHTML=`<div><span class="sectionlabel">SELECTED OSM ROAD</span><h3>${escapeMapText(name)}</h3><p>${escapeMapText(roadKind)} · click location EPSG:31370 ${fmt(Math.round(selected.x))}, ${fmt(Math.round(selected.y))}</p></div><div class="route-stats"><span><strong>${fmt(near.length)}</strong> crashes within ${fmt(radius)} m</span><span><strong>${fmt(severeCount)}</strong> severe class</span><span><strong>${fmt(fatalCount)}</strong> fatal class</span><span><strong>${escapeMapText(top)}</strong> most common type</span></div><p class="route-caveat">Proximity around the clicked point in the active selection; crashes are not matched to this road or its full route. No traffic exposure denominator is available.</p>`;
}
function escapeMapText(x){return String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
function topLabel(m){return [...m].sort((a,b)=>b[1]-a[1])[0]?.[0]||'Unknown'}
function hoverMap(e){const r=mapCanvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top,tip=$('#map-tip');
  const point=mapScene==='detail'?mapView.points.find(p=>Math.hypot(p.x-x,p.y-y)<6):null;
  const city=mapView.cities.find(c=>Math.hypot(c.x-x,c.y-y)<12);
  const cell=mapScene==='heat'?mapView.cells.find(c=>x>=c.px&&x<=c.px+c.ps&&y>=c.py&&y<=c.py+c.ps):null;
  if(!point&&!cell&&!city){tip.hidden=true;return}
  if(point){const p=point.row;tip.innerHTML=`<strong>${escapeMapText(cityLabel(p.municipality))}</strong><br>${p.year} · ${escapeMapText(crashLabel(p.collision))}<br>${escapeMapText(displayLabel(p.road,'road'))} · ${p.severity==='1'?'fatal class':severe(p.severity)?'severe class':'slight injury'} · ${escapeMapText(p.weather)}<br><small>Location rounded to 10 m · ${fmt(p.x)}, ${fmt(p.y)}</small>`}
  else if(cell){tip.innerHTML=`<strong>${escapeMapText(cityLabel(topLabel(cell.cities)))}</strong><br>${fmt(cell.n)} crashes · ${fmt(cell.severe)} severe · ${fmt(cell.fatal)} fatal<br>${escapeMapText(crashLabel(topLabel(cell.types)))}<br>${escapeMapText(displayLabel(topLabel(cell.roads),'road'))}<br><small>Grid centre EPSG:31370</small>`}
  else tip.innerHTML=`<strong>${escapeMapText(cityLabel(city.name))}</strong><br>${fmt(city.n)} selected locations`;
  tip.style.left=Math.max(8,Math.min(x+13,r.width-265))+'px';tip.style.top=Math.max(8,Math.min(y+13,r.height-115))+'px';tip.hidden=false;
}
