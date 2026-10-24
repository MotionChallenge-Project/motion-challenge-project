"""Visual policy summary with expandable exact-weight evidence."""
import html
import json


def esc(value):
    return html.escape(str(value), quote=True)


LABELS = {
    'inference_verified': 'Input verified · evaluation pending',
    'pending_verification': 'Input check pending',
    'requires_author_deployment_validation': 'Author deployment check pending',
    'incompatible_input_contract': 'Ineligible with current inputs',
}
OBSERVATIONS = [
    ('Joint state, full root orientation (including yaw), angular velocity and gravity', True),
    ('Base linear velocity, including ideal noise-free velocity', True),
    ('Local body positions and orientations from forward kinematics (FK)', True),
    ('Reference motion, world trajectory and future frames', True),
    ('Native proprioceptive history, past actions and recurrent memory', True),
    ('Actual root or body world positions, including actual height', False),
    ('Actual contacts, forces and impulses', False),
    ('Tracking errors derived from actual world position', False),
    ('Velocity integration, odometry or explicit global-position estimators', False),
]


def render(content, models, page, intro):
    data = json.loads((content / 'observation_admissions.json').read_text())
    records = data['models']
    assert set(records) == set(models)
    core = 'https://github.com/MotionChallenge-Project/MotionChallenge-Core/blob/' + data['core_commit']
    body = intro('POLICY ADMISSION', 'Policy admission',
                 'Which policies qualify, and what they may observe.')
    body += '''<div class="policy-content docs">
<section><div class="rule-cards admission-cards">
<article><span class="card-symbol" aria-hidden="true">01</span><h2>Public checkpoint</h2><p>General controller · one set of weights for the complete suite.</p></article>
<article><span class="card-symbol" aria-hidden="true">02</span><h2>Faithful inference</h2><p>Author-consistent inputs, history, timing and actions.</p></article>
<article><span class="card-symbol" aria-hidden="true">03</span><h2>Permitted inputs</h2><p>Track rules apply to reset, preprocessing and inference.</p></article>
<article><span class="card-symbol" aria-hidden="true">04</span><h2>Verified results</h2><p>Public code · complete suite · trace checks · repeated run.</p></article>
</div><p class="small">Disclose adaptations and training-data overlap. No minimum score is required; single-motion checkpoints do not qualify.</p></section>
<section id="observations"><h2>Restricted observation track</h2>
<p>Ideal proprioception, without actual world-position or contact feedback.</p>'''
    body += ('<div class="actions"><a class="button" href="' + core + '/docs/OBSERVATIONS.md">Frozen rules ↗</a>'
             '<a class="text-link" href="/benchmarks/lafan40/?track=lafan40-g1-ideal-proprioception-v1">LAFAN40 conditions ↗</a></div>')
    body += '<table class="rules-table observation-table"><thead><tr><th scope="col">Input or computation</th><th scope="col">Allowed</th></tr></thead><tbody>'
    for label, allowed in OBSERVATIONS:
        kind, symbol, text = ('allowed', '✓', 'Allowed') if allowed else ('excluded', '×', 'Not allowed')
        body += ('<tr><td>' + esc(label) + '</td><td><span class="rule-verdict rule-' + kind
                 + '" aria-label="' + text + '">' + symbol + '</span></td></tr>')
    body += '''</tbody></table>
<div class="rule-callout"><strong>Special handling</strong><p>Fixed origins, local FK and reference-only alignment require a validated author-supported path for the exact checkpoint. Arbitrary input zeroing is not accepted.</p></div>
<p class="small">Root velocities use world axes at the body origin. Rules cover initialization and history. Complete definitions and limitations are in the frozen rules.</p></section>'''
    body += ('<section id="checkpoints"><div class="section-heading"><h2>' + str(len(records))
             + ' checkpoint decisions</h2><a class="text-link" href="/data/observation-admissions.json">JSON ↓</a></div>'
             '<p class="small">For this track. Expand a model for its handling and evidence.</p>')
    for key, model in models.items():
        row = records[key]
        assert row['checkpoint_sha256'] == model['runtime']['weights_sha256']
        url = row['repository'] + '/blob/' + row['published_adapter_commit'] + '/admission.json'
        status = LABELS[row['status']]
        kind = 'pending'
        if row['status'] == 'incompatible_input_contract':
            kind = 'ineligible'
        if row.get('evaluation_progress') == 'accepted':
            status, kind = 'Admitted · full evaluation verified', 'accepted'
        body += ('<details class="admission-record" id="' + esc(key) + '"><summary>'
                 '<span class="admission-model">' + esc(model['display_name']) + '</span>'
                 '<span class="admission-status status-' + kind + '">' + esc(status) + '</span></summary><div>'
                 '<p>' + esc(row['handling']) + '</p><p class="small">SHA256 <code>'
                 + esc(row['checkpoint_sha256']) + '</code></p><div class="actions">'
                 '<a class="text-link" href="/models/' + esc(key) + '/">Model card ↗</a>'
                 '<a class="text-link" href="' + esc(url) + '">Weight, source &amp; evidence ↗</a>'
                 '</div></div></details>')
    body += '</section></div>'
    page('/admission/', 'Policy admission', body, 'Admission')
