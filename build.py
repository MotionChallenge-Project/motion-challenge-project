from pathlib import Path
import json,html,shutil,os,re,hashlib
from datetime import datetime, timezone
import benchmark_pages
import model_pages
import publication_checks
import admission_pages
import protocol_pages
ROOT=Path(__file__).parent;D=ROOT/'docs';D.mkdir(exist_ok=True)
# These folders contain only generated pages and exported evidence.
for generated in ('models','evaluations','data/evidence','assets/model-icons','overview','coverage'):
 path=D/generated
 if path.exists():shutil.rmtree(path)
GH='https://github.com/MotionChallenge-Project'
BASE=os.environ.get('SITE_BASE_PATH','/motionchallenge').rstrip('/')
SITE_URL='https://motionchallenge-project.github.io'+BASE
WEBSITE_SOURCE=GH+'/motionchallenge/tree/website'
UPDATED=datetime.now(timezone.utc).replace(second=0,microsecond=0)
UPDATE_TIME=f'<time datetime="{UPDATED.isoformat()}">{UPDATED.strftime("%d %b %Y, %H:%M UTC")}</time>'
NAMES={'grit':'GRIT','heft':'HEFT','sonic':'SONIC','mimic-lite':'MimicLite','scalebfm':'ScaleBFM','holomotion':'HoloMotion','humanoid-gpt':'Humanoid-GPT','protomotions':'ProtoMotions','bfm-zero':'BFM-Zero','twist2':'TWIST2'}
CONTENT=ROOT/'content'
CITATION=(CONTENT/'citation.bib').read_text()
MODELS=json.loads((CONTENT/'models.json').read_text())
NAMES={k:m['display_name'] for k,m in MODELS.items()}
TRACKS=json.loads((CONTENT/'tracks.json').read_text())
BENCHMARKS=benchmark_pages.load_catalog(CONTENT,TRACKS)
TRACK_BY_ID={t['id']:t for t in TRACKS}
RESULTS=json.loads((CONTENT/'results.json').read_text())
RESULTS_REVISION=hashlib.sha256((CONTENT/'results.json').read_bytes()+(CONTENT/'models.json').read_bytes()+(CONTENT/'tracks.json').read_bytes()+(CONTENT/'observation_admissions.json').read_bytes()).hexdigest()[:12]
ASSET_REVISION=hashlib.sha256((ROOT/'style.css').read_bytes()+(ROOT/'app.js').read_bytes()).hexdigest()[:12]
rows=RESULTS['rows']
publication_checks.validate(CONTENT,rows,MODELS,TRACKS)
for row in rows:
 for field in ('adapter_code_url', 'core_code_url'):
  row[field]=model_pages.repository_location(row[field])
assert all(r['mujoco_version']=='3.17.0' and r.get('adapter_code_url') and r.get('core_code_url') for r in rows), 'Only batch 3.17 results with pinned code may be published'
EVALUATED=len(set(r['model'] for r in rows))
for r in rows:
 r['icon']=MODELS[r['model']]['icon'];r['icon_label']=MODELS[r['model']]['icon_label'];r['icon_source']=MODELS[r['model']]['icon_source'];r['controller_type']=MODELS[r['model']]['controller_type'];r['label']=NAMES[r['model']];r['version']=MODELS[r['model']]['version'];r.setdefault('checkpoint_sha256',MODELS[r['model']]['runtime']['weights_sha256']);r['organization']=MODELS[r['model']]['organization'];r['organization_source']=MODELS[r['model']]['organization_source'];r['submitter']='MotionChallenge';r['status']='Trace verified';r['date']=json.loads((CONTENT/'evidence'/r['evidence_file']).read_text())['summary']['finished_utc'][:10];r['rank']=None;track=TRACK_BY_ID[r['track_id']];r['benchmark_id']=track['benchmark_id'];r['robot_id']=track['robot_id']
(D/'data').mkdir(exist_ok=True)
(D/'data/development-summary.json').unlink(missing_ok=True)
(D/'data/results.json').write_text(json.dumps({'benchmarks':BENCHMARKS,'tracks':TRACKS,'rows':rows},indent=2))
nav=[('Leaderboard','/'),('Benchmarks','/benchmarks/'),('Models','/models/'),('Protocol','/protocol/'),('Submit','/submit/')]
def page(path,title,body,active,canonical_path=None):
 body=model_pages.repository_location(body)
 folder=D/path.strip('/');folder.mkdir(exist_ok=True,parents=True)
 links=''.join(f'<a href="{url}" '+('aria-current="page"' if label==active else '')+f'>{label}</a>' for label,url in nav)
 (folder/'index.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · MotionChallenge</title><meta name="site-base-path" content="{BASE}"><meta name="results-revision" content="{RESULTS_REVISION}"><link rel="canonical" href="{SITE_URL}{canonical_path or path}"><link rel="icon" type="image/png" href="/assets/favicon.png"><meta name="description" content="An open, reproducible benchmark for humanoid motion tracking. Shared evaluation rules, public code and verified results."><link rel="stylesheet" href="/style.css?v={ASSET_REVISION}"><script src="/app.js?v={ASSET_REVISION}" defer></script></head><body><a class="skip" href="#main">Skip to content</a><header><a class="brand" href="/"><span class="mark">m<span>c</span></span><span>MotionChallenge</span></a><nav aria-label="Main navigation">{links}</nav><a class="github" href="{GH}/MotionChallenge-Core">GitHub ↗</a></header><main id="main">{body}</main><footer><div><a class="brand" href="/">MotionChallenge</a><p>Open evaluation. Reproducible evidence.</p></div><div><a href="{GH}/MotionChallenge-Core">Core repository ↗</a><a href="/submit/">Contribute a controller</a><a href="/about/">About &amp; acknowledgments</a><a href="/#citation">Cite MotionChallenge</a><a href="{WEBSITE_SOURCE}">Website source ↗</a></div><small>Open protocols · Public evidence<br>Last updated · {UPDATE_TIME}</small></footer></body></html>''')
def intro(kicker,title,text,decoration=''):
 heading=f'<h1>{title}</h1>'
 if decoration:heading=f'<div class="heading-with-logo">{heading}{decoration}</div>'
 return f'<section class="pagehead"><p class="eyebrow">{kicker}</p>{heading}<p class="lede">{text}</p></section>'
page('/benchmarks/','Benchmarks',benchmark_pages.directory(BENCHMARKS,TRACKS,intro),'Benchmarks')
for benchmark in BENCHMARKS:
 title,body=benchmark_pages.detail(CONTENT,benchmark,TRACKS)
 page('/benchmarks/'+benchmark['id']+'/',title,body,'Benchmarks')

leaderboard_body=intro('BENCHMARK RESULTS','MotionChallenge Leaderboard','An open, reproducible benchmark for humanoid motion tracking.')+'''<section class="board-section"><div class="track-selectors"><label>Benchmark<select id="benchmark-select" aria-label="Benchmark"></select></label><label>Robot<select id="robot-select" aria-label="Robot"></select></label><a id="track-details" href="/benchmarks/lafan40/">Dataset &amp; failure conditions ↗</a><a href="/protocol/#observations">Observation rules ↗</a></div><div class="toolbar"><div><p id="track-caption" class="small">Loading benchmark…</p><p id="sort-caption" class="sort-caption" aria-live="polite"></p></div><label class="search">Find a model <input id="model-search" type="search" placeholder="Model, type or organization…"></label></div><div class="pagination pagination-top" aria-label="Table pagination"><label>Show <select id="page-size" aria-label="Models shown"><option value="5">Top 5</option><option value="10">Top 10</option><option value="15">Top 15</option><option value="25">Top 25</option><option value="all" selected>Top All</option></select></label><div><span data-page-range aria-live="polite"></span><button data-page="previous" aria-label="Previous page">← Previous</button><button data-page="next" aria-label="Next page">Next →</button></div></div><div class="table-scroll"><table id="leaderboard"><colgroup><col class="col-rank"><col class="col-model"><col class="col-type"><col class="col-org"><col class="col-success"><col class="col-completion"><col span="6" class="col-metric"></colgroup><thead><tr><th rowspan="3" scope="col">Rank</th><th rowspan="3" scope="col">Model</th><th rowspan="3" scope="col"><abbr title="Control policy family used by the evaluated checkpoint">Type</abbr></th><th rowspan="3" scope="col">Organization</th><th rowspan="3" scope="col"><button data-sort="passed">Success ↑</button></th><th rowspan="3" scope="col"><button data-sort="completion_pct">Completion ↑</button></th><th colspan="6" scope="colgroup" class="metric-title">Mean per-body position error · MPBPE <span>mm ↓</span><small>14 key bodies · lower is better</small></th></tr><tr><th colspan="3" scope="colgroup" class="metric-group">Early termination<small>Until first failure, including the failure frame</small></th><th colspan="3" scope="colgroup" class="metric-group full-motion">No termination<small>Entire motion, including post-failure states</small></th></tr><tr><th scope="col"><button data-sort="mpjpe_xy_yaw_aligned_m">XY + yaw ↓</button></th><th scope="col"><button data-sort="mpjpe_xy_aligned_m">XY only ↓</button></th><th scope="col"><button data-sort="mpjpe_world_m">No alignment ↓</button></th><th scope="col"><button data-sort="full_mpjpe_xy_yaw_aligned_m">XY + yaw ↓</button></th><th scope="col"><button data-sort="full_mpjpe_xy_aligned_m">XY only ↓</button></th><th scope="col"><button data-sort="full_mpjpe_world_m">No alignment ↓</button></th></tr></thead><tbody></tbody></table><p id="empty" hidden>No models match your search.</p></div><div class="pagination pagination-bottom" aria-label="Table pagination"><div><span data-page-range aria-live="polite"></span><button data-page="previous" aria-label="Previous page">← Previous</button><button data-page="next" aria-label="Next page">Next →</button></div></div><p class="table-note"><strong>Type:</strong> Dense = continuous dense policies (MLP, convolutional, graph or Transformer); FSQ = finite scalar quantization; MoE = mixture of experts; FB = forward-backward latent policy; Flow = flow matching. Sources are linked from each model card.</p><p class="table-note">Each MuJoCo 3.17.0 batch evaluation reports success, completion and six tracking-error views. Only MuJoCo 3.17.0 batch results are published. <a href="https://github.com/MotionChallenge-Project/MotionChallenge-Core">Published evaluator ↗</a></p><p class="table-note"><strong>Shared rules. Public code. Reproducible runs.</strong> Within each benchmark, robot and protocol, the core fixes data, physics, failures and scoring. Each entry identifies its checkpoint and inference implementation.</p><p class="table-note">Rank follows the selected metric, always best first: higher success or completion, lower tracking error. The default is success, then completion. Medals mark the top three. MPBPE averages 14 body-origin distances over frames, then equally over 40 clips. Early-termination errors cover the observed prefix. No-termination errors cover the entire motion. </p><a class="text-link" href="/data/results.json" download>Download results (JSON) ↓</a></section><section class="section three"><article><h3>Success</h3><p>A clip passes only if it reaches the final reference frame without any declared failure. All 40 clips use the same checkpoint.</p></article><article><h3>Completion</h3><p>Mean fraction of motion completed before failure. Reported alongside tracking error to describe how much of each motion was completed.</p></article><article><h3>Six tracking-error views</h3><p>Each rollout protocol reports XY + yaw, XY only and no alignment. These remove horizontal translation and heading, translation only, or neither. Height is retained in all six views.</p><a href="/protocol/#alignment">Metric definitions →</a></article></section>'''
leaderboard_body=leaderboard_body.replace('class="pagehead"','class="pagehead leaderboard-head"',1)
leaderboard_body=leaderboard_body.replace('</section>',f'<p class="site-updated">Last updated · {UPDATE_TIME}</p></section>',1)
leaderboard_body+=f'''<section class="section citation" id="citation" aria-labelledby="citation-heading"><div class="citation-heading"><div><h2 id="citation-heading">Citation</h2><p>If you use MotionChallenge in your research, please cite:</p></div><div class="citation-actions"><button type="button" data-copy-citation aria-live="polite">Copy BibTeX</button></div></div><pre><code id="citation-code" class="language-bibtex">{html.escape(CITATION)}</code></pre></section>'''
page('/','Leaderboard',leaderboard_body,'Leaderboard')
page('/leaderboard/','Leaderboard',leaderboard_body,'Leaderboard',canonical_path='/')
RANKED={k:m for k,m in MODELS.items() if k in {r['model'] for r in rows}}
model_pages.render(RANKED, rows, TRACKS, CONTENT, GH, page, intro)
shutil.copyfile(CONTENT/'observation_admissions.json',D/'data/observation-admissions.json')
protocol_pages.render(CONTENT, page, intro, GH)
page('/submit/','Submit a controller',intro('CONTRIBUTE TO THE BENCHMARK','Make your result reproducible.','A model repository, a pinned checkpoint, and a verifiable run. LAFAN40 is the first suite; the integration contract is shared.')+f'''<section class="section three steps"><article><span class="step">01</span><h3>Adapt inference</h3><p>Create your own repository with the core as a root-level submodule. Implement reset, act and close. Preserve the author's deployment behavior.</p><a href="{GH}/MotionChallenge-Core/blob/main/docs/ADAPTERS.md">SDK and adapter guide ↗</a></article><article><span class="step">02</span><h3>Run the whole suite</h3><p>Use one checkpoint and the fixed protocol. Keep outputs outside Git. Submit full pose traces, hashes, receipts and inference-parity evidence.</p><a href="/protocol/">Read the evaluation protocol →</a></article><article><span class="step">03</span><h3>Request review</h3><p>Open an issue linking your adapter and external result artifacts. Include the actual submitter, source/checkpoint versions, training-data overlap and any adaptations.</p><a href="{GH}/MotionChallenge-Core/issues/new">Open a submission issue ↗</a></article></section><section class="section tint"><h2>A small adapter. A shared kernel.</h2><pre><code>MotionChallenge-your-model/
├── MotionChallenge-Core/  # pinned core submodule
├── adapter.py         # inference only
├── runtime.json       # clocks, artifacts, input contract
├── provenance.json    # source and review evidence
├── evaluate.py        # shared core entrypoint
├── pyproject.toml
└── uv.lock</code></pre><p>The core owns datasets, physics, metrics and verification. Model repositories do not copy or override evaluation logic. Checkpoints, data and results live in local caches or external artifact storage.</p></section><section class="section" id="datasets"><h2>Propose another dataset</h2><p>Publish a manifest with immutable source revisions, file hashes, frame rate, joint order and the complete motion set. Define a distinct protocol version and benchmark identity. Preserve difficult clips, document licensing and overlap, and keep scores in their own track.</p><a class="text-link" href="{GH}/MotionChallenge-Core/blob/main/docs/BENCHMARKS.md">Dataset integration contract ↗</a></section>''','Submit')
page('/about/','About MotionChallenge',intro('ABOUT MOTIONCHALLENGE','Motion tracking, openly evaluated.','An open, reproducible benchmark for humanoid motion tracking.')+f'''<section class="section docs"><h2>MotionChallenge</h2><p>Public checkpoints, shared evaluation rules and independently verified results. Each model has a reproducible adapter with pinned source, weights and dependencies. LAFAN40 is our first dataset.</p><p>Model cards describe the released inference path and any benchmark adaptation. Detailed results include per-motion scores, the exact evaluated code and verification records.</p><a class="text-link" href="{GH}/MotionChallenge-Core/issues">Discuss a result ↗</a><h2>Acknowledgments</h2><p>Thanks to the controller authors, LAFAN1 and LAFAN1 Retargeting Dataset, MuJoCo and mjlab. The website draws presentation ideas from <a href="https://robotwin-platform.github.io/leaderboard">RoboTwin</a>, <a href="https://robocasa.ai/">RoboCasa</a>, <a href="https://robochallenge.ai/home">RoboChallenge</a> and <a href="https://github.com/Roboparty/MimicLite">MimicLite</a>.</p></section>''','About')
shutil.copytree(CONTENT/'evidence',D/'data/evidence',dirs_exist_ok=True)
shutil.copytree(ROOT/'assets/model-icons',D/'assets/model-icons',dirs_exist_ok=True,ignore=shutil.ignore_patterns('README.md'))
shutil.copy2(ROOT/'app.js',D/'app.js')
shutil.copy2(ROOT/'style.css',D/'style.css')
(D/'citation.bib').unlink(missing_ok=True)
shutil.copy2(ROOT/'assets/favicon.png',D/'assets/favicon.png')
(D/'.nojekyll').write_text('')
legacy=D/'admission';legacy.mkdir(exist_ok=True)
legacy_target=BASE+'/protocol/#observations'
(legacy/'index.html').write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={legacy_target}"><link rel="canonical" href="{SITE_URL}/protocol/"><title>Observation rules · MotionChallenge</title></head><body><a href="{legacy_target}">Observation rules →</a></body></html>')
for document in D.rglob('*.html'):
 if document==legacy/'index.html':continue
 text=document.read_text()
 text=re.sub(r'(href|src)="/(?!/)',lambda m:m.group(1)+'="'+BASE+'/',text)
 document.write_text(text)
print('Built',len(list(D.rglob('index.html'))),'pages')
