"""Observation rules and model-specific handling, shared by protocol and model pages."""
import html
import json


def esc(value):
    return html.escape(str(value), quote=True)


OBSERVATIONS = [
    ('Joint state, full root orientation (including yaw), base linear and angular velocity, and gravity', True),
    ('Local body positions and orientations from forward kinematics (FK)', True),
    ('Reference motion, world trajectory and future frames', True),
    ('Native proprioceptive history, past actions and recurrent memory', True),
    ('Robot world positions (root and bodies, including height)', False),
    ('Robot contact states, forces and impulses', False),
    ('Tracking errors derived from robot world position', False),
    ('Velocity integration, odometry or explicit global-position estimators', False),
]



def observation_table():
    body = '<table class="rules-table observation-table"><thead><tr><th scope="col">Input or computation</th><th scope="col">Allowed</th></tr></thead><tbody>'
    for label, allowed in OBSERVATIONS:
        kind, symbol, text = ('allowed', '✓', 'Allowed') if allowed else ('excluded', '×', 'Not allowed')
        body += ('<tr><th scope="row">' + esc(label) + '</th><td><span class="rule-verdict rule-' + kind
                 + '" aria-label="' + text + '">' + symbol + '</span></td></tr>')
    return body + '</tbody></table>'


def model_handling(key, model, record):
    assert record['checkpoint_sha256'] == model['runtime']['weights_sha256']
    assert record['status'] == 'inference_verified'
    url = record['repository'] + '/blob/' + record['published_adapter_commit'] + '/admission.json'
    return ('<div class="model-observation-note" id="observations"><h3>Observation requirements</h3>'
            '<p class="small"><a href="/protocol/#observations">Observation rules ↗</a></p>'
            '<details><summary>Model-specific handling</summary><p>' + esc(record['handling']) + '</p>'
            '<a class="text-link" href="' + esc(url) + '">Exact checkpoint &amp; evidence ↗</a>'
            '</details></div>')
