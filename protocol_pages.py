"""Brief protocol overview, with versioned details linked to Core."""
import json
import admission_pages


def render(content, page, intro, github):
    data = json.loads((content / 'observation_admissions.json').read_text())
    core = github + '/MotionChallenge-Core/blob/' + data['core_commit']
    body = intro('EVALUATION PROTOCOL', 'Evaluation protocol',
                 'Evaluation conditions, permitted observations and scoring.')
    body += '''<div class="docs-layout"><aside>
<a href="#contract">Evaluation</a><a href="#observations">Observation rules</a>
<a href="#alignment">Metrics</a><a href="#evidence">Model requirements</a>
</aside><article class="docs">
<section id="contract"><h2>Evaluation</h2>
<p>The Core fixes data, robot, physics, reset, failures and scoring. Each controller keeps its author's inference, history and control timing.</p>
<p><strong>LAFAN40 · G1:</strong> 40 complete motions, MuJoCo 3.17.0 batch, no noise or randomization, friction 1. Start at the first reference pose and velocity; continue to the final frame without resetting after failure.</p>
<table class="rules-table"><thead><tr><th scope="col">Failure condition</th><th scope="col">Threshold</th></tr></thead><tbody>
<tr><td>Absolute torso height error</td><td>&gt; 0.25 m</td></tr>
<tr><td>Absolute projected-gravity Z difference: actual vs reference torso</td><td>&gt; 0.8</td></tr>
<tr><td>Maximum wrist or ankle world-height error</td><td>&gt; 0.25 m</td></tr>
</tbody></table>
<p class="small">Any condition records the first failure. No XY or yaw threshold. <a href="/benchmarks/lafan40/#failure-conditions">Exact definitions ↗</a></p>
</section>
<section id="observations"><h2>Restricted observation track</h2>
<p>Ideal proprioception, without actual world-position or contact feedback. Rules apply to initialization, preprocessing, history and inference.</p>'''
    body += admission_pages.observation_table()
    body += '''<p class="small">Root velocities use world axes at the body origin. Fixed origins, local FK and reference-only alignment require a validated author-supported path for the exact checkpoint. Arbitrary input zeroing is not accepted.</p>'''
    body += ('<div class="actions"><a class="button" href="' + core + '/docs/OBSERVATIONS.md">Frozen rules ↗</a>'
             '<a class="text-link" href="/models/">Model-specific handling ↗</a></div></section>')
    body += '''<section id="alignment"><h2>Metrics</h2>
<ul><li><strong>Success ↑:</strong> fraction of complete motions without failure.</li>
<li><strong>Completion ↑:</strong> average fraction of duration reached before first failure.</li>
<li><strong>MPBPE ↓:</strong> mean position error over 14 body origins, in mm; average frames within each motion, then weight motions equally.</li></ul>
<table class="rules-table"><thead><tr><th scope="col">Alignment</th><th scope="col">Removed before measuring error</th></tr></thead><tbody>
<tr><td>XY + yaw</td><td>Per-frame horizontal root translation and heading difference</td></tr>
<tr><td>XY only</td><td>Per-frame horizontal root translation</td></tr>
<tr><td>None</td><td>Nothing; compare world positions directly</td></tr>
</tbody></table>
<p><strong>Six error views:</strong> each alignment is measured through the first failure (including that frame), and over the full motion (including post-failure states). Alignment does not change success or completion.</p>
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
