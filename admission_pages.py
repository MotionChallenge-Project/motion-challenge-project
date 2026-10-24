"""Observation rules and per-weight admission, separate from score acceptance."""
import html,json

def esc(v):return html.escape(str(v),quote=True)
LABELS={'inference_verified':'Inference verified · fresh evaluation pending',
 'pending_verification':'Input verification pending',
 'requires_author_deployment_validation':'Author deployment path pending',
 'incompatible_input_contract':'Not eligible with the current inference path'}

def render(content,models,page,intro):
 data=json.loads((content/'observation_admissions.json').read_text())
 records=data['models'];assert set(records)==set(models)
 core='https://github.com/MotionChallenge-Project/MotionChallenge-Core/blob/'+data['core_commit']
 body=intro('OBSERVATION ADMISSION','Ideal proprioception','No global position feedback. A separate, frozen observation track with per-checkpoint inference evidence.')
 body+='<section class="section docs"><p><strong>Contract:</strong> <code>ideal-proprioceptive-no-position-v1</code>. Noise-free inputs; physics, references, reset, failure conditions and all six tracking-error views remain unchanged. Existing privileged-state scores stay in their original track. No previous score is copied into this track.</p>'
 body+='<div class="actions"><a class="button" href="'+core+'/docs/OBSERVATIONS.md">Frozen rules ↗</a><a class="text-link" href="/benchmarks/lafan40/?track=lafan40-g1-ideal-proprioception-v1">LAFAN40 conditions ↗</a><a class="text-link" href="/data/observation-admissions.json">Per-checkpoint records (JSON) ↓</a></div>'
 body+='<h2>Permitted inputs</h2><ul><li>Joint angles and velocities; full root orientation, including yaw.</li><li>Ideal linear and angular velocity at the root body origin, expressed in world axes.</li><li>Gravity projection and local forward kinematics derived from those inputs and fixed robot geometry.</li><li>Reference motion, including world coordinates, velocities and the declared history/future window.</li><li>Previous actions and author-native proprioceptive or recurrent history.</li></ul>'
 body+='<h2>Excluded information</h2><p>Actual global root XYZ, including height; actual global body positions; contact flags, forces and impulses; actual-position tracking errors; explicit velocity integration into displacement, odometry and root-position estimators. These restrictions also apply to initialization, reset, history caches, reference alignment and preprocessing.</p>'
 body+='<h2>Special handling</h2><p>Local FK or a synthetic fixed origin must preserve the released inference numerically, or implement a documented author deployment path for the exact checkpoint. Reference-only anchoring must be disclosed. A required actor input cannot simply be zeroed to obtain admission. Training critic or reward privilege does not determine deployment eligibility.</p><p>The Core removes forbidden fields before reset and action messages reach the adapter. Source audit, input-dependency tests, author inference comparison and a fresh complete verified evaluation are separate checks. Native recurrent state is permitted; this rule does not prove that a network never implicitly infers displacement. Ideal inputs do not establish real-world sensor feasibility.</p></section>'
 body+='<section class="section"><h2>29 checkpoint decisions</h2><p class="small">Status describes this observation track only. A pending or ineligible checkpoint retains its original, explicitly privileged-state result.</p>'
 for key,model in models.items():
  row=records[key];assert row['checkpoint_sha256']==model['runtime']['weights_sha256']
  url=row['repository']+'/blob/'+row['published_adapter_commit']+'/admission.json'
  status=LABELS[row['status']]
  if row.get('evaluation_progress')=='accepted':status='Admitted · fresh full-suite and repeat verified'
  body+='<article class="admission-record" id="'+esc(key)+'"><h3><a href="/models/'+esc(key)+'/">'+esc(model['display_name'])+'</a></h3><p class="small"><strong>'+esc(status)+'</strong> · SHA256 <code>'+esc(row['checkpoint_sha256'][:12])+'…</code></p><p>'+esc(row['handling'])+'</p><a class="text-link" href="'+esc(url)+'">Exact weight, source and decision ↗</a></article>'
 body+='</section>'
 page('/admission/','Observation admission',body,'Protocol')
