"""Current default batch entrypoint vs scalar inference, with slot lifecycle checks."""
import dataclasses,importlib,json,sys,time
from pathlib import Path
import numpy as np
from motion_challenge.sdk import StateBatch,ReferenceBatch
from motion_challenge.runtime.policy import PolicyBatch
from motion_challenge.runtime.observations import controller_state,PROPRIOCEPTIVE
from motion_challenge.simulation.physics import World,forward_kinematics
from motion_challenge.data.dataset import load_csv_motion
from motion_challenge.resources import lafan_paths
repo,data,out=map(Path,sys.argv[1:4]);sys.path.insert(0,str(repo))
rt=json.loads((repo/'runtime.json').read_text());rt['adapter_root']=str(repo)
module,factory=rt['entrypoint'].split(':');create=getattr(importlib.import_module(module),factory)
def arrays(ss,rr):
 sa=StateBatch(joint_names=ss[0].joint_names,**{f.name:np.array([getattr(s,f.name) for s in ss]) for f in dataclasses.fields(StateBatch) if f.name!='joint_names'})
 body_map={'body_position_world_m':'position_world_m','body_orientation_xyzw':'orientation_xyzw','body_linear_velocity_world_m_s':'linear_velocity_world_m_s','body_angular_velocity_world_rad_s':'angular_velocity_world_rad_s'}
 kwargs={'body_names':tuple(b.name for b in rr[0][0].bodies)}
 for f in dataclasses.fields(ReferenceBatch):
  if f.name=='body_names':continue
  if f.name in body_map:kwargs[f.name]=np.array([[[getattr(b,body_map[f.name]) for b in r.bodies] for r in refs] for refs in rr])
  else:kwargs[f.name]=np.array([[getattr(r,f.name) for r in refs] for refs in rr])
 return sa,ReferenceBatch(**kwargs)
paths=lafan_paths();suite=json.loads(paths['suite'].read_text());worlds=[];singles=[];n=8;rng=np.random.default_rng(421027)
for i in range(n):
 w=World(paths['robot']);w.reset(load_csv_motion(data/suite['files'][i]['path'],suite['joint_names'],suite['source_fps']));worlds.append(w);singles.append(create(repo,rt))
allids=list(range(n));batch=None;maxerr=0.;count=resets=0;start=time.monotonic()
try:
 for step in range(24):
  ids=allids if step==0 else list(map(int,rng.permutation(n)[:(1,3,8)[step%3]]))
  ss=[];rr=[]
  for i in ids:
   w=worlds[i];t=step*.02 if step<16 else w.motion.duration_s+(step-20)*.02
   frame=w.reference(t);w.data.qpos[:]=w._qpos(frame);w.data.qpos[w.qadr]+=rng.normal(0,.02,29);w.data.qvel[:]=rng.normal(0,.3,w.model.nv);w.data.time=t;forward_kinematics(w.model,w.data)
   ss.append(controller_state(w.state(),PROPRIOCEPTIVE));rr.append(tuple(w.reference(t+o) for o in rt['reference_offsets_s']))
  sa,ra=arrays(ss,rr)
  if batch is None:batch=PolicyBatch(repo/'runtime.json',n,sa,ra,out.with_suffix('.policy.log'))
  if step==0 or step%7==0:
   seeds=[22000+i for i in ids];batch.call_arrays('reset',ids,sa,ra,seeds);resets+=len(ids)
   for i,s,r,seed in zip(ids,ss,rr,seeds):singles[i].reset(s,r,seed)
  actual=batch.call_arrays('act',ids,sa,ra)
  expected=[]
  for i,s,r in zip(ids,ss,rr):
   cmd=singles[i].act(s,r);expected.append([getattr(cmd,f.name) for f in dataclasses.fields(cmd)])
  delta=float(np.max(np.abs(actual-np.asarray(expected))));maxerr=max(maxerr,delta);count+=len(ids)
  assert delta<=1e-5,(step,delta)
 result={'status':'passed','cases':count,'reset_slots':resets,'max_command_abs_error':maxerr,'exact':maxerr==0.,'tolerance':1e-5,'wall_s':time.monotonic()-start,'checks':['default PolicyBatch array transport','1/3/8 active slots','reordered slots','independent partial resets and seeded RNG','reference endpoint clamping','all five motor command fields'],'checkpoint_sha256':rt['weights_sha256']}
except Exception as e:
 result={'status':'failed','cases':count,'max_command_abs_error':maxerr,'error':repr(e)};raise
finally:
 if batch:batch.close()
 for p in singles:p.close()
 out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
