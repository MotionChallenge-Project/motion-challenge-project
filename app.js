(async()=>{
 const base=document.querySelector('meta[name="site-base-path"]')?.content||'';
 const table=document.querySelector('#leaderboard');if(!table)return;
 const $=s=>document.querySelector(s),body=table.querySelector('tbody'),search=$('#model-search'),empty=$('#empty'),size=$('#page-size'),prev=$('#previous-page'),next=$('#next-page'),range=$('#page-range');
 const benchmark=$('#benchmark-select'),robot=$('#robot-select'),protocol=$('#protocol-select');
 let data=[],tracks=[],sort='passed',descending=true,page=1;
 try{const response=await fetch(base+'/data/development-summary.json');if(!response.ok)throw new Error();const payload=await response.json();data=payload.rows;tracks=payload.tracks;if(!tracks.length)throw new Error();}
 catch{empty.hidden=false;empty.textContent='Results could not be loaded. Please reload or download the summary JSON.';table.hidden=true;return;}
 const query=new URLSearchParams(location.search);
 function options(select,entries,preferred){select.replaceChildren();for(const [value,label] of new Map(entries)){const option=document.createElement('option');option.value=value;option.textContent=label;select.append(option);}if([...select.options].some(o=>o.value===preferred))select.value=preferred;}
 options(benchmark,tracks.map(t=>[t.benchmark_id,t.benchmark_label]),query.get('benchmark'));
 function setProtocols(preferred){options(protocol,tracks.filter(t=>t.benchmark_id===benchmark.value&&t.robot_id===robot.value).map(t=>[t.id,t.label]),preferred);}
 function setRobots(preferred){options(robot,tracks.filter(t=>t.benchmark_id===benchmark.value).map(t=>[t.robot_id,t.robot_label]),preferred);setProtocols(query.get('track'));}
 setRobots(query.get('robot'));
 function render(){
  const track=tracks.find(t=>t.id===protocol.value);if(!track)return;
  const trackData=data.filter(r=>r.track_id===track.id),ranked=[...trackData].sort((a,b)=>b.passed-a.passed||b.completion_pct-a.completion_pct),ranks=new Map(ranked.map((r,i)=>[r.model,i+1]));
  $('#track-caption').textContent=`${track.benchmark_label} · ${track.robot_label} · ${track.label} · ${track.clip_count} full motions`;
  $('#track-details').href=base+'/benchmarks/'+encodeURIComponent(track.benchmark_id)+'/';
  const url=new URL(location.href);url.searchParams.set('benchmark',track.benchmark_id);url.searchParams.set('robot',track.robot_id);url.searchParams.set('track',track.id);history.replaceState(null,'',url);
  const needle=search.value.toLowerCase().trim(),limit=Number(size.value);
  const filtered=trackData.filter(r=>(r.label+' '+(r.version||'')+' '+(r.organization||'')).toLowerCase().includes(needle)).sort((a,b)=>(descending?b[sort]-a[sort]:a[sort]-b[sort])||b.completion_pct-a.completion_pct);
  const pages=Math.max(1,Math.ceil(filtered.length/limit));page=Math.min(page,pages);
  const start=(page-1)*limit,rows=filtered.slice(start,start+limit);
  body.replaceChildren();table.hidden=!rows.length;empty.hidden=!!rows.length;empty.textContent='No models match your search.';
  range.textContent=filtered.length?`${start+1}–${Math.min(start+limit,filtered.length)} of ${filtered.length} · Page ${page}/${pages}`:'0 models';prev.disabled=page<=1;next.disabled=page>=pages;
  for(const r of rows){const tr=document.createElement('tr');
   [ranks.get(r.model),r.label,r.organization||'Not listed',r.passed,r.completion_pct,r.mpjpe_xy_yaw_aligned_m,r.mpjpe_xy_aligned_m,r.mpjpe_world_m].forEach((v,i)=>{const td=document.createElement('td');
    if(i===0){td.className='rank';td.textContent=String(v).padStart(2,'0');}
    else if(i===1){const a=document.createElement('a');a.href=base+'/models/'+r.model+'/';a.textContent=v;td.append(a);}
    else if(i===3){td.className='score';td.textContent=(v/track.clip_count*100).toFixed(1)+'%';const small=document.createElement('small');small.textContent=v+' / '+track.clip_count+' clips';td.append(small);}
    else if(i===4)td.textContent=v.toFixed(2)+'%';else if(i>=5)td.textContent=(v*1000).toFixed(2);else td.textContent=v;
    tr.append(td);
   });body.append(tr);
  }
 }
 benchmark.addEventListener('change',()=>{setRobots(robot.value);page=1;render()});robot.addEventListener('change',()=>{setProtocols();page=1;render()});protocol.addEventListener('change',()=>{page=1;render()});
 search.addEventListener('input',()=>{page=1;render()});size.addEventListener('change',()=>{page=1;render()});prev.addEventListener('click',()=>{page--;render()});next.addEventListener('click',()=>{page++;render()});
 document.querySelectorAll('[data-sort]').forEach(b=>b.addEventListener('click',()=>{const key=b.dataset.sort;descending=sort===key?!descending:['passed','completion_pct'].includes(key);sort=key;page=1;document.querySelectorAll('th').forEach(x=>x.removeAttribute('aria-sort'));b.closest('th').setAttribute('aria-sort',descending?'descending':'ascending');render();}));render();
})();
