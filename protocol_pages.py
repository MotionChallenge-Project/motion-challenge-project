"""Brief protocol overview, with versioned details linked to Core."""
import json
import admission_pages


def render(content, page, intro, github):
    data = json.loads((content / 'observation_admissions.json').read_text())
    core = github + '/MotionChallenge-Core/blob/' + data['core_commit']
    body = intro('EVALUATION PROTOCOL', 'Evaluation protocol',
                 'Evaluation conditions, permitted observations and scoring.')
    body += '''<div class="docs-layout"><aside>
<a href="#contract">Evaluation</a><a href="#failure-conditions">Failure rules</a>
<a href="#observations">Observation rules</a>
<a href="#alignment">Metrics</a><a href="#coverage">Tracking-error coverage</a>
<a href="#evidence">Model requirements</a>
</aside><article class="docs">
<section id="contract"><h2>Evaluation</h2>
<p>The Core fixes data, robot, physics, reset, failures and scoring. Each controller keeps its author's inference, history and control timing.</p>
<p>Each benchmark declares its motion set, robot, simulator settings, initialization and failure conditions. Evaluate every declared motion with one checkpoint, from first frame to endpoint; record the first failure and continue without resetting.</p>
<p><a class="text-link" href="/benchmarks/">Dataset &amp; benchmark conditions ↗</a></p>
</section>
<section id="failure-conditions"><h2>Tracking failure rules</h2>
<p>Default conditions for motion tracking. Compare actual and reference states at the same timestamp; any exceeded limit marks a failure.</p>
<table class="rules-table"><thead><tr><th scope="col">Condition</th><th scope="col">Measurement</th><th scope="col">Default limit</th></tr></thead><tbody>
<tr><td>Torso height</td><td>Absolute world-Z position difference</td><td>&gt; 0.25 m</td></tr>
<tr><td>Torso inclination</td><td>Absolute difference between the local Z components of projected unit gravity</td><td>&gt; 0.8</td></tr>
<tr><td>End-effector height</td><td>Maximum absolute world-Z difference across designated end effectors</td><td>&gt; 0.25 m</td></tr>
</tbody></table>
<p>Height is relative to the reference. Inclination is dimensionless and does not measure yaw or the full relative rotation. No XY or yaw alignment is applied to failure checks.</p>
<p class="small">Equality passes; a failure at the final sample still counts. Each benchmark declares its torso and end-effector bodies and freezes its thresholds. Different thresholds require a separately versioned configuration.</p>
</section>
<section id="observations"><h2>Restricted observation track</h2>
<p>Ideal proprioception, without actual world-position or contact feedback. Rules apply to initialization, preprocessing, history and inference.</p>'''
    body += admission_pages.observation_table()
    body += '''<p class="small">Root velocities use world axes at the body origin. Fixed origins, local FK and reference-only alignment require a validated author-supported path for the exact checkpoint. Arbitrary input zeroing is not accepted.</p>'''
    body += ('<div class="actions"><a class="text-link" href="' + core + '/docs/OBSERVATIONS.md">Frozen rules ↗</a>'
             '<a class="text-link" href="/models/">Model-specific handling ↗</a></div></section>')
    body += '''<section id="alignment"><h2>Metrics</h2>
<table class="rules-table"><thead><tr><th scope="col">Metric</th><th scope="col">Definition</th></tr></thead><tbody>
<tr><td>Success ↑</td><td>Fraction of complete motions without failure</td></tr>
<tr><td>Completion ↑</td><td>Last valid sample time before first failure divided by motion duration; averaged equally across motions. Successful motions count as 100%.</td></tr>
<tr><td>MPBPE ↓ · mm</td><td>Mean per-body position error over the benchmark’s declared body origins; average bodies and samples within each motion, then weight motions equally.</td></tr>
</tbody></table>
<table class="rules-table"><thead><tr><th scope="col">Alignment</th><th scope="col">Removed before measuring error</th></tr></thead><tbody>
<tr><td>XY + yaw</td><td>Per-frame horizontal root translation and the closest relative rotation about world Z</td></tr>
<tr><td>XY only</td><td>Per-frame horizontal root translation</td></tr>
<tr><td>None</td><td>Nothing; compare world positions directly</td></tr>
</tbody></table>
<p>Height and tilt are retained in all three views. Alignment does not change success or completion.</p>
</section>
<section id="coverage"><h2>Tracking-error coverage</h2>
<table class="rules-table"><thead><tr><th scope="col">Time range</th><th scope="col">Samples included</th></tr></thead><tbody>
<tr><td>Early termination</td><td>Through the first failing sample, including that sample; the entire motion if no failure occurs.</td></tr>
<tr><td>No termination</td><td>The entire motion through its exact endpoint, including post-failure states, without resetting.</td></tr>
</tbody></table>
<p>Two time ranges × three alignments give six tracking-error views. Success and completion always use the first failure; later recovery does not erase it.</p>
</section>
<section id="evidence"><h2>Model requirements</h2>
<ul><li>Public general-controller checkpoint; the same weights for the complete suite.</li>
<li id="inference">Author-faithful inference and permitted observations; disclose adaptations and training-data overlap.</li>
<li>Public adapter, pinned Core and dependencies; complete traces, independent verification and a repeated run.</li></ul>
<p class="small">Single-motion checkpoints do not qualify. No minimum score is required. Each model card links its exact-weight handling and evidence.</p>
<div class="actions">'''
    body += ('<a class="text-link" href="' + core + '/docs/PROTOCOL.md">Full protocol ↗</a>'
             '<a class="text-link" href="' + core + '/docs/ADAPTERS.md">Adapter requirements ↗</a>'
             '<a class="text-link" href="/data/observation-admissions.json">Checkpoint records (JSON) ↓</a>')
    body += '</div></section></article></div>'
    page('/protocol/', 'Evaluation protocol', body, 'Protocol')
