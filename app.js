(async()=>{
 const base=document.querySelector('meta[name="site-base-path"]')?.content||'';
 const benchmarkControls=document.querySelector('.benchmark-controls');
 if(benchmarkControls){
  const robotChoice=document.querySelector('#benchmark-robot'),protocolChoice=document.querySelector('#benchmark-protocol');
  const templates=[...document.querySelectorAll('template[data-benchmark-track]')];
  const query=new URLSearchParams(location.search);
  if([...robotChoice.options].some(o=>o.value===query.get('robot')))robotChoice.value=query.get('robot');
  function showBenchmark(){
   const chosen=templates.find(t=>t.dataset.benchmarkTrack===protocolChoice.value);if(!chosen)return;
   document.querySelector('#benchmark-document').replaceChildren(chosen.content.cloneNode(true));
   document.querySelector('#benchmark-robot-title').textContent=chosen.dataset.robotLabel;
   document.title=benchmarkControls.dataset.benchmarkLabel+' × '+chosen.dataset.robotLabel+' · Motion Challenge';
   const params=new URLSearchParams({benchmark:benchmarkControls.dataset.benchmarkId,robot:chosen.dataset.robotId,track:chosen.dataset.benchmarkTrack});
   document.querySelector('#benchmark-results').href=base+'/leaderboard/?'+params;
   const url=new URL(location.href);url.searchParams.set('robot',chosen.dataset.robotId);url.searchParams.set('track',chosen.dataset.benchmarkTrack);history.replaceState(null,'',url);
  }
  function chooseRobot(preferred){
   protocolChoice.replaceChildren();
   for(const t of templates.filter(t=>t.dataset.robotId===robotChoice.value)){
    const option=document.createElement('option');option.value=t.dataset.benchmarkTrack;option.textContent=t.dataset.trackLabel;protocolChoice.append(option);
   }
   if([...protocolChoice.options].some(o=>o.value===preferred))protocolChoice.value=preferred;
   showBenchmark();
  }
  robotChoice.addEventListener('change',()=>chooseRobot());protocolChoice.addEventListener('change',showBenchmark);
  chooseRobot(query.get('track'));
 }
 const table=document.querySelector('#leaderboard');if(!table)return;
 const $=s=>document.querySelector(s),body=table.querySelector('tbody'),search=$('#model-search'),empty=$('#empty'),size=$('#page-size'),prev=[...document.querySelectorAll('[data-page=previous]')],next=[...document.querySelectorAll('[data-page=next]')],ranges=[...document.querySelectorAll('[data-page-range]')];
 const benchmark=$('#benchmark-select'),robot=$('#robot-select'),protocol=$('#protocol-select');
 let data=[],tracks=[],sort='passed',descending=true,page=1;
 try{const response=await fetch(base+'/data/development-summary.json?v='+encodeURIComponent(document.querySelector('meta[name="results-revision"]')?.content||''),{cache:'no-cache'});if(!response.ok)throw new Error();const payload=await response.json();data=payload.rows;tracks=payload.tracks;if(!tracks.length)throw new Error();}
 catch{empty.hidden=false;empty.textContent='Results could not be loaded. Please reload or download the summary JSON.';table.hidden=true;return;}
 const query=new URLSearchParams(location.search);
 function options(select,entries,preferred){select.replaceChildren();for(const [value,label] of new Map(entries)){const option=document.createElement('option');option.value=value;option.textContent=label;select.append(option);}if([...select.options].some(o=>o.value===preferred))select.value=preferred;}
 options(benchmark,tracks.map(t=>[t.benchmark_id,t.benchmark_label]),query.get('benchmark'));
 function setProtocols(preferred){const available=tracks.filter(t=>t.benchmark_id===benchmark.value&&t.robot_id===robot.value);options(protocol,available.map(t=>[t.id,t.label]),preferred||available.at(-1)?.id);}
 function setRobots(preferred){options(robot,tracks.filter(t=>t.benchmark_id===benchmark.value).map(t=>[t.robot_id,t.robot_label]),preferred);setProtocols(query.get('track'));}
 setRobots(query.get('robot'));
 function render(){
  const track=tracks.find(t=>t.id===protocol.value);if(!track)return;
  let sortingLabel='';
  document.querySelectorAll('[data-sort]').forEach(button=>{
   const label=button.dataset.label||(button.dataset.label=button.textContent.replace(/\s*[↑↓↕]\s*$/,'').trim());
   const active=button.dataset.sort===sort;
   button.textContent=label+' '+(active?(descending?'↓':'↑'):'↕');
   button.setAttribute('aria-pressed',String(active));
   const header=button.closest('th');
   if(active){
    header.setAttribute('aria-sort',descending?'descending':'ascending');
    const metric=sort.includes('mpjpe_');
    sortingLabel=(metric?'MPBPE · '+(sort.startsWith('full_')?'No termination':'Early termination')+' · ':'')+label;
    button.title='Sorted '+(descending?'high to low':'low to high')+'. Click to reverse.';
   }else{header.removeAttribute('aria-sort');button.title='Sort by '+label;}
  });
  const bestFirst=['passed','completion_pct'].includes(sort)?descending:!descending;
  $('#sort-caption').textContent='Sorted by '+sortingLabel+' · '+(descending?'High → low':'Low → high')+(bestFirst?' · Best first':'');
  const trackData=data.filter(r=>r.track_id===track.id&&['early_termination','unified'].includes(r.termination_mode||'early_termination')).map(r=>{
   if(r.termination_mode==='unified')return r;
   const full=data.find(f=>f.track_id===track.id&&f.model===r.model&&f.termination_mode==='no_termination'&&f.checkpoint_sha256===r.checkpoint_sha256);
   return {...r,full_evidence_file:full?.evidence_file,full_adapter_code_url:full?.adapter_code_url,...Object.fromEntries(['mpjpe_xy_yaw_aligned_m','mpjpe_xy_aligned_m','mpjpe_world_m'].map(k=>['full_'+k,full?.[k]??null]))};
  });
  $('#track-caption').textContent=`${track.benchmark_label} · ${track.robot_label} · ${track.label} · ${track.clip_count} full motions`;
  $('#track-details').href=base+'/benchmarks/'+encodeURIComponent(track.benchmark_id)+'/';
  const url=new URL(location.href);url.searchParams.set('benchmark',track.benchmark_id);url.searchParams.set('robot',track.robot_id);url.searchParams.set('track',track.id);history.replaceState(null,'',url);
  const needle=search.value.toLowerCase().trim(),limit=Number(size.value);
  const filtered=trackData.filter(r=>(r.label+' '+(r.version||'')+' '+(r.organization||'')+' '+(r.controller_type?.label||'')).toLowerCase().includes(needle)).sort((a,b)=>{
   const av=a[sort],bv=b[sort];
   if(av==null&&bv!=null)return 1;if(av!=null&&bv==null)return -1;
   return (av==null?0:descending?bv-av:av-bv)||b.completion_pct-a.completion_pct||a.label.localeCompare(b.label);
  });
  const pages=Math.max(1,Math.ceil(filtered.length/limit));page=Math.min(page,pages);
  const start=(page-1)*limit,rows=filtered.slice(start,start+limit);
  body.replaceChildren();table.hidden=!rows.length;empty.hidden=!!rows.length;empty.textContent=trackData.length?'No models match your search.':'No completed results for this protocol yet. Batch evaluation is in progress.';
  for(const range of ranges)range.textContent=filtered.length?`${start+1}–${Math.min(start+limit,filtered.length)} of ${filtered.length} · Page ${page}/${pages}`:'0 models';prev.forEach(b=>b.disabled=page<=1);next.forEach(b=>b.disabled=page>=pages);
  for(const [rowIndex,r] of rows.entries()){const tr=document.createElement('tr');
   const rank=start+rowIndex+1,medal=bestFirst&&rank<=3?['gold','silver','bronze'][rank-1]:null;
   if(medal)tr.className='podium-'+medal;
   [start+rowIndex+1,r.label,r.controller_type,r.organization||'Not listed',r.passed,r.completion_pct,r.mpjpe_xy_yaw_aligned_m,r.mpjpe_xy_aligned_m,r.mpjpe_world_m,r.full_mpjpe_xy_yaw_aligned_m,r.full_mpjpe_xy_aligned_m,r.full_mpjpe_world_m].forEach((v,i)=>{const td=document.createElement('td');
    if(i===0){td.className='rank';td.setAttribute('aria-label','Rank '+v);const badge=document.createElement('span');badge.className='rank-badge';if(medal){const icon=document.createElement('span');icon.className='rank-medal';icon.setAttribute('aria-hidden','true');icon.textContent=['🥇','🥈','🥉'][rank-1];badge.append(icon);td.title='Top '+rank+' by '+sortingLabel;}const number=document.createElement('span');number.className='rank-number';number.textContent=String(v);badge.append(number);td.append(badge);}
    else if(i===1){const a=document.createElement('a');a.href=base+'/models/'+r.model+'/';a.textContent=v;td.append(a);const links=document.createElement('small');links.className='eval-code-links';const details=document.createElement('a');details.href=base+'/evaluations/'+encodeURIComponent(track.id)+'/'+r.model+'/';details.textContent='Detailed results ↗';links.append(details);td.append(links);}
    else if(i===2){const tag=document.createElement('a');tag.className='type-tag type-'+v.id;tag.href=v.source;tag.textContent=v.label;tag.title=v.description;td.append(tag);}
    else if(i===4){td.className='score';td.textContent=(v/track.clip_count*100).toFixed(1)+'%';const small=document.createElement('small');small.textContent=v+' / '+track.clip_count+' clips';td.append(small);}
    else if(i===5)td.textContent=v.toFixed(2)+'%';else if(i>=6){
     if(v==null){td.textContent='—';td.className='pending';td.title='Full-motion evaluation not yet published';}
     else{const a=document.createElement('a');a.className='metric-evidence';a.href=base+'/evaluations/'+encodeURIComponent(track.id)+'/'+r.model+'/'+(i>=9?'#none':'#early');a.textContent=(v*1000).toFixed(2);a.title='Evaluation record, per-motion metrics and verification receipt';td.append(a);}
    }else td.textContent=v;
    tr.append(td);
   });body.append(tr);
  }
 }
 benchmark.addEventListener('change',()=>{setRobots(robot.value);page=1;render()});robot.addEventListener('change',()=>{setProtocols();page=1;render()});protocol.addEventListener('change',()=>{page=1;render()});
 search.addEventListener('input',()=>{page=1;render()});size.addEventListener('change',()=>{page=1;render()});prev.forEach(b=>b.addEventListener('click',()=>{page--;render()}));next.forEach(b=>b.addEventListener('click',()=>{page++;render()}));
 document.querySelectorAll('[data-sort]').forEach(b=>b.addEventListener('click',()=>{const key=b.dataset.sort;descending=sort===key?!descending:['passed','completion_pct'].includes(key);sort=key;page=1;render();}));render();
})();
