(async()=>{
 const base=document.querySelector('meta[name="site-base-path"]')?.content||'';
 const table=document.querySelector('#leaderboard');if(!table)return;
 const $=s=>document.querySelector(s),body=table.querySelector('tbody'),search=$('#model-search'),empty=$('#empty'),size=$('#page-size'),prev=$('#previous-page'),next=$('#next-page'),range=$('#page-range');
 const benchmark=$('#benchmark-select'),robot=$('#robot-select'),protocol=$('#protocol-select');
 let data=[],tracks=[],sort='passed',descending=true,page=1;
 try{const response=await fetch(base+'/data/development-summary.json?v='+encodeURIComponent(document.querySelector('meta[name="results-revision"]')?.content||''),{cache:'no-cache'});if(!response.ok)throw new Error();const payload=await response.json();data=payload.rows;tracks=payload.tracks;if(!tracks.length)throw new Error();}
 catch{empty.hidden=false;empty.textContent='Results could not be loaded. Please reload or download the summary JSON.';table.hidden=true;return;}
 const query=new URLSearchParams(location.search);
 function options(select,entries,preferred){select.replaceChildren();for(const [value,label] of new Map(entries)){const option=document.createElement('option');option.value=value;option.textContent=label;select.append(option);}if([...select.options].some(o=>o.value===preferred))select.value=preferred;}
 options(benchmark,tracks.map(t=>[t.benchmark_id,t.benchmark_label]),query.get('benchmark'));
 function setProtocols(preferred){options(protocol,tracks.filter(t=>t.benchmark_id===benchmark.value&&t.robot_id===robot.value).map(t=>[t.id,t.label]),preferred);}
 function setRobots(preferred){options(robot,tracks.filter(t=>t.benchmark_id===benchmark.value).map(t=>[t.robot_id,t.robot_label]),preferred);setProtocols(query.get('track'));}
 setRobots(query.get('robot'));
 function render(){
  const track=tracks.find(t=>t.id===protocol.value);if(!track)return;
  const trackData=data.filter(r=>r.track_id===track.id&&(r.termination_mode||'early_termination')==='early_termination').map(r=>{
   const full=data.find(f=>f.track_id===track.id&&f.model===r.model&&f.termination_mode==='no_termination'&&f.checkpoint_sha256===r.checkpoint_sha256);
   return {...r,full_evidence_file:full?.evidence_file,...Object.fromEntries(['mpjpe_xy_yaw_aligned_m','mpjpe_xy_aligned_m','mpjpe_world_m'].map(k=>['full_'+k,full?.[k]??null]))};
  });
  $('#track-caption').textContent=`${track.benchmark_label} · ${track.robot_label} · ${track.label} · ${track.clip_count} full motions`;
  $('#track-details').href=base+'/benchmarks/'+encodeURIComponent(track.benchmark_id)+'/';
  const url=new URL(location.href);url.searchParams.set('benchmark',track.benchmark_id);url.searchParams.set('robot',track.robot_id);url.searchParams.set('track',track.id);history.replaceState(null,'',url);
  const needle=search.value.toLowerCase().trim(),limit=Number(size.value);
  const filtered=trackData.filter(r=>(r.label+' '+(r.version||'')+' '+(r.organization||'')).toLowerCase().includes(needle)).sort((a,b)=>{
   const av=a[sort],bv=b[sort];
   if(av==null&&bv!=null)return 1;if(av!=null&&bv==null)return -1;
   return (av==null?0:descending?bv-av:av-bv)||b.completion_pct-a.completion_pct||a.label.localeCompare(b.label);
  });
  const pages=Math.max(1,Math.ceil(filtered.length/limit));page=Math.min(page,pages);
  const start=(page-1)*limit,rows=filtered.slice(start,start+limit);
  body.replaceChildren();table.hidden=!rows.length;empty.hidden=!!rows.length;empty.textContent=trackData.length?'No models match your search.':'No completed results for this protocol yet. Batch evaluation is in progress.';
  range.textContent=filtered.length?`${start+1}–${Math.min(start+limit,filtered.length)} of ${filtered.length} · Page ${page}/${pages}`:'0 models';prev.disabled=page<=1;next.disabled=page>=pages;
  for(const [rowIndex,r] of rows.entries()){const tr=document.createElement('tr');
   [start+rowIndex+1,r.label,r.organization||'Not listed',r.passed,r.completion_pct,r.mpjpe_xy_yaw_aligned_m,r.mpjpe_xy_aligned_m,r.mpjpe_world_m,r.full_mpjpe_xy_yaw_aligned_m,r.full_mpjpe_xy_aligned_m,r.full_mpjpe_world_m].forEach((v,i)=>{const td=document.createElement('td');
    if(i===0){td.className='rank';td.textContent=String(v).padStart(2,'0');}
    else if(i===1){const a=document.createElement('a');a.href=base+'/models/'+r.model+'/';a.textContent=v;td.append(a);}
    else if(i===3){td.className='score';td.textContent=(v/track.clip_count*100).toFixed(1)+'%';const small=document.createElement('small');small.textContent=v+' / '+track.clip_count+' clips';td.append(small);}
    else if(i===4)td.textContent=v.toFixed(2)+'%';else if(i>=5){
     if(v==null){td.textContent='—';td.className='pending';td.title='Full-motion evaluation not yet published';}
     else{const a=document.createElement('a');a.className='metric-evidence';a.href=base+'/data/evidence/'+(i>=8?r.full_evidence_file:r.evidence_file);a.textContent=(v*1000).toFixed(2);a.title='Per-motion metrics and verification receipt';td.append(a);}
    }else td.textContent=v;
    tr.append(td);
   });body.append(tr);
  }
 }
 benchmark.addEventListener('change',()=>{setRobots(robot.value);page=1;render()});robot.addEventListener('change',()=>{setProtocols();page=1;render()});protocol.addEventListener('change',()=>{page=1;render()});
 search.addEventListener('input',()=>{page=1;render()});size.addEventListener('change',()=>{page=1;render()});prev.addEventListener('click',()=>{page--;render()});next.addEventListener('click',()=>{page++;render()});
 document.querySelectorAll('[data-sort]').forEach(b=>b.addEventListener('click',()=>{const key=b.dataset.sort;descending=sort===key?!descending:['passed','completion_pct'].includes(key);sort=key;page=1;document.querySelectorAll('th').forEach(x=>x.removeAttribute('aria-sort'));b.closest('th').setAttribute('aria-sort',descending?'descending':'ascending');render();}));render();
})();
