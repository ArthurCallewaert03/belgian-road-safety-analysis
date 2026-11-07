// Twee aanvullende grafieken voor een logisch onderzoekspad: datakwaliteit en seizoen.
function renderCoverage(){
  const years=data.meta.years, values=years.map(y=>{let n=0,g=0;for(const r of rows)if(r.year===y){n++;if(r.valid)g++}return {year:y,pct:n?100*g/n:0}});
  const w=660,h=230,l=40,r=18,t=20,b=35,x=i=>l+i*(w-l-r)/(years.length-1),y=v=>h-b-(v-50)*(h-b-t)/50;
  const line=values.map((v,i)=>`${i?'L':'M'}${x(i)},${y(v.pct)}`).join(' ');
  $('#coverage-chart').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Location coverage by year">${[50,60,70,80,90,100].map(n=>`<line x1="${l}" x2="${w-r}" y1="${y(n)}" y2="${y(n)}" stroke="#e5ecef"/><text x="${l-6}" y="${y(n)+4}" text-anchor="end" class="axis-text">${n}%</text>`).join('')}<path d="${line}" fill="none" stroke="#208aa3" stroke-width="3"/>${values.map((v,i)=>`<g class="chart-hit" data-year="${v.year}" tabindex="0" role="button" aria-label="Select ${v.year}, location coverage ${pct(v.pct)}"><circle cx="${x(i)}" cy="${y(v.pct)}" r="${sel.year.value==v.year?7:5}" fill="${sel.year.value==v.year?'#e47c44':'#208aa3'}" stroke="white" stroke-width="2"/><title>${v.year}: ${pct(v.pct)} usable</title><text x="${x(i)}" y="${h-10}" text-anchor="middle" class="axis-text">${v.year}</text></g>`).join('')}</svg><div class="chart-callout">Location coverage improves from 2022. Click a year to filter the dashboard.</div>`;
  $('#coverage-chart').querySelectorAll('[data-year]').forEach(el=>{const choose=()=>{sel.year.value=el.dataset.year;render()};el.addEventListener('click',choose);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose()}})});
}
function renderMonth(rs){
  const counts=Array(12).fill(0);for(const r of rs)if(r.month>=1&&r.month<=12)counts[r.month-1]++;
  const names=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],w=660,h=230,l=20,r=10,b=33,t=22,gap=8,bw=(w-l-r)/12,max=Math.max(1,...counts);
  $('#month-chart').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Recorded crashes by month">${[0,.5,1].map(fr=>`<line x1="${l}" x2="${w-r}" y1="${h-b-(h-b-t)*fr}" y2="${h-b-(h-b-t)*fr}" stroke="#e5ecef"/>`).join('')}${counts.map((n,i)=>{const bh=(h-b-t)*n/max,x=l+i*bw+gap/2;return `<rect x="${x}" y="${h-b-bh}" width="${bw-gap}" height="${bh}" rx="4" fill="${i===counts.indexOf(max)?'#e47c44':'#6aa9b9'}"><title>${names[i]}: ${fmt(n)} crashes</title></rect><text x="${x+(bw-gap)/2}" y="${h-10}" text-anchor="middle" class="axis-text">${names[i]}</text>`}).join('')}</svg>`;
}
