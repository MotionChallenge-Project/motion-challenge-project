(async()=>{
 const base=document.querySelector('meta[name="site-base-path"]')?.content||'';
 const copyCitation=document.querySelector('[data-copy-citation]');
 copyCitation?.addEventListener('click',async()=>{
  const code=document.querySelector('#citation-code');
  try{
   await navigator.clipboard.writeText(code.textContent);
   copyCitation.textContent='Copied!';
  }catch{
   const range=document.createRange();range.selectNodeContents(code);
   const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);
   copyCitation.textContent='Selected — copy manually';
  }
  setTimeout(()=>{copyCitation.textContent='Copy BibTeX'},2500);
 });
 const benchmarkControls=document.querySelector('.benchmark-controls');
 if(benchmarkControls){
  const robotChoice=document.querySelector('#benchmark-robot');
  const templates=[...document.querySelectorAll('template[data-benchmark-track]')];
  const query=new URLSearchParams(location.search);
  if([...robotChoice.options].some(o=>o.value===query.get('robot')))robotChoice.value=query.get('robot');
  function showBenchmark(){
   const chosen=templates.find(t=>t.dataset.robotId===robotChoice.value);if(!chosen)return;
   document.querySelector('#benchmark-document').replaceChildren(chosen.content.cloneNode(true));
   document.querySelector('#benchmark-robot-title').textContent=chosen.dataset.robotLabel;
   document.title=benchmarkControls.dataset.benchmarkLabel+' × '+chosen.dataset.robotLabel+' · MotionChallenge';
   const params=new URLSearchParams({benchmark:benchmarkControls.dataset.benchmarkId,robot:chosen.dataset.robotId,track:chosen.dataset.benchmarkTrack});
   document.querySelector('#benchmark-results').href=base+'/?'+params;
   const url=new URL(location.href);url.searchParams.set('robot',chosen.dataset.robotId);url.searchParams.set('track',chosen.dataset.benchmarkTrack);history.replaceState(null,'',url);
  }
  robotChoice.addEventListener('change',showBenchmark);
  showBenchmark();
 }
 const table=document.querySelector('#leaderboard');if(!table)return;
 const $=s=>document.querySelector(s),body=table.querySelector('tbody'),search=$('#model-search'),empty=$('#empty'),size=$('#page-size'),prev=$('[data-page=previous]'),next=$('[data-page=next]');
 const benchmark=$('#benchmark-select'),robot=$('#robot-select');
 let data=[],tracks=[],sort='passed',page=1;
 try{const response=await fetch(base+'/data/results.json?v='+encodeURIComponent(document.querySelector('meta[name="results-revision"]')?.content||''),{cache:'no-cache'});if(!response.ok)throw new Error();const payload=await response.json();data=payload.rows;tracks=payload.tracks;if(!tracks.length)throw new Error();}
 catch{empty.hidden=false;empty.textContent='Results could not be loaded. Please reload or download the summary JSON.';table.hidden=true;return;}
 const query=new URLSearchParams(location.search);
 function options(select,entries,preferred){select.replaceChildren();for(const [value,label] of new Map(entries)){const option=document.createElement('option');option.value=value;option.textContent=label;select.append(option);}if([...select.options].some(o=>o.value===preferred))select.value=preferred;}
 options(benchmark,tracks.map(t=>[t.benchmark_id,t.benchmark_label]),query.get('benchmark'));
 function setRobots(preferred){options(robot,tracks.filter(t=>t.benchmark_id===benchmark.value).map(t=>[t.robot_id,t.robot_label]),preferred);}
 setRobots(query.get('robot'));
 function render(){
  const track=tracks.find(t=>t.benchmark_id===benchmark.value&&t.robot_id===robot.value);if(!track)return;
  let sortingLabel='';
  const descending=['passed','completion_pct'].includes(sort);
  document.querySelectorAll('[data-sort]').forEach(button=>{
   const label=button.dataset.label||(button.dataset.label=button.textContent.replace(/\s*[↑↓↕]\s*$/,'').trim());
   const active=button.dataset.sort===sort;
   button.textContent=label+' '+(['passed','completion_pct'].includes(button.dataset.sort)?'↓':'↑');
   button.setAttribute('aria-pressed',String(active));
   const header=button.closest('th');
   if(active){
    header.setAttribute('aria-sort',descending?'descending':'ascending');
    const metric=sort.includes('mpjpe_');
    sortingLabel=(metric?'MPBPE · '+(sort.startsWith('full_')?'No termination':'Early termination')+' · ':'')+label;
    button.title='Sorted best first: '+(descending?'high to low':'low to high')+'.';
   }else{header.removeAttribute('aria-sort');button.title='Sort by '+label+' · best first';}
  });
  const sortColumn=['passed','completion_pct','mpjpe_xy_yaw_aligned_m','mpjpe_xy_aligned_m','mpjpe_world_m','full_mpjpe_xy_yaw_aligned_m','full_mpjpe_xy_aligned_m','full_mpjpe_world_m'].indexOf(sort)+4;
  $('#sort-caption').textContent='Sorted by '+sortingLabel+' · '+(descending?'High → low':'Low → high')+' · Best first';
  const trackData=data.filter(r=>r.track_id===track.id&&r.termination_mode==='unified');
  $('#track-details').href=base+'/benchmarks/'+encodeURIComponent(track.benchmark_id)+'/';
  const url=new URL(location.href);url.searchParams.set('benchmark',track.benchmark_id);url.searchParams.set('robot',track.robot_id);url.searchParams.set('track',track.id);history.replaceState(null,'',url);
  const needle=search.value.toLowerCase().trim(),limit=size.value==='all'?Math.max(1,trackData.length):Number(size.value);
  const filtered=trackData.filter(r=>(r.label+' '+(r.version||'')+' '+(r.organization||'')+' '+(r.controller_type?.label||'')).toLowerCase().includes(needle)).sort((a,b)=>{
   const av=a[sort],bv=b[sort];
   if(av==null&&bv!=null)return 1;if(av!=null&&bv==null)return -1;
   return (av==null?0:descending?bv-av:av-bv)||(b.completion_pct-a.completion_pct||a.label.localeCompare(b.label));
  });
  const pages=Math.max(1,Math.ceil(filtered.length/limit));page=Math.min(page,pages);
  const start=(page-1)*limit,rows=filtered.slice(start,start+limit);
  prev.disabled=page<=1;next.disabled=page>=pages;prev.hidden=next.hidden=pages<=1;
  body.replaceChildren();table.hidden=!rows.length;empty.hidden=!!rows.length;empty.textContent=trackData.length?'No models match your search.':'No completed results for this protocol yet. Batch evaluation is in progress.';
  for(const [rowIndex,r] of rows.entries()){const tr=document.createElement('tr');
   const rank=start+rowIndex+1,medal=rank<=3?['gold','silver','bronze'][rank-1]:null;
   if(medal)tr.className='podium-'+medal;
   [rank,r.label,r.controller_type,r.organization||'Not listed',r.passed,r.completion_pct,r.mpjpe_xy_yaw_aligned_m,r.mpjpe_xy_aligned_m,r.mpjpe_world_m,r.full_mpjpe_xy_yaw_aligned_m,r.full_mpjpe_xy_aligned_m,r.full_mpjpe_world_m].forEach((v,i)=>{const td=document.createElement('td');
    if(i===0){td.className='rank';td.setAttribute('aria-label','Rank '+v);const badge=document.createElement('span');badge.className='rank-badge';if(medal){const icon=document.createElement('span');icon.className='rank-medal';icon.setAttribute('aria-hidden','true');icon.textContent=['🥇','🥈','🥉'][rank-1];badge.append(icon);td.title='Top '+rank+' by '+sortingLabel;}const number=document.createElement('span');number.className='rank-number';number.textContent=String(v);badge.append(number);td.append(badge);}
    else if(i===1){const entry=document.createElement('div');entry.className='model-entry';const icon=document.createElement(r.icon?'img':'span');icon.className='model-icon'+(r.icon?'':' model-initial');if(r.icon){icon.src=base+r.icon;icon.alt='';icon.width=32;icon.height=32;icon.title=r.icon_label;}else{icon.textContent=r.label[0].toUpperCase();icon.setAttribute('aria-hidden','true');}const text=document.createElement('div');text.className='model-entry-text';const a=document.createElement('a');a.href=base+'/models/'+r.model+'/';a.textContent=v;a.title=v;text.append(a);const links=document.createElement('small');links.className='eval-code-links';const details=document.createElement('a');details.href=base+'/evaluations/'+encodeURIComponent(track.id)+'/'+r.model+'/';details.textContent='Detailed results ↗';links.append(details);text.append(links);entry.append(icon,text);td.append(entry);}
    else if(i===2){const tag=document.createElement('span');tag.className='type-tag type-'+v.id;tag.textContent=v.label;tag.title=v.description;td.append(tag);}
    else if(i===4){td.className='score';td.textContent=(v/track.clip_count*100).toFixed(1)+'%';const small=document.createElement('small');small.textContent=v+' / '+track.clip_count+' clips';td.append(small);}
    else if(i===5)td.textContent=v.toFixed(2)+'%';else if(i>=6){
     if(v==null){td.textContent='—';td.className='pending';td.title='Full-motion evaluation not yet published';}
     else{const a=document.createElement('a');a.className='metric-evidence';a.href=base+'/evaluations/'+encodeURIComponent(track.id)+'/'+r.model+'/'+(i>=9?'#none':'#early');a.textContent=(v*1000).toFixed(2);a.title='Evaluation record, per-motion metrics and verification receipt';td.append(a);}
    }else{td.textContent=v;if(i===3)td.title=v;}
    if(i===sortColumn)td.classList.add('sorted-column');
    tr.append(td);
   });body.append(tr);
  }
 }
 benchmark.addEventListener('change',()=>{setRobots(robot.value);page=1;render()});robot.addEventListener('change',()=>{page=1;render()});
 search.addEventListener('input',()=>{page=1;render()});size.addEventListener('change',()=>{page=1;render()});
 prev.addEventListener('click',()=>{page--;render()});next.addEventListener('click',()=>{page++;render()});
 document.querySelectorAll('[data-sort]').forEach(b=>b.addEventListener('click',()=>{const key=b.dataset.sort;if(sort===key)return;sort=key;page=1;render();}));render();
})();
