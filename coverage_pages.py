"""Dated coverage gaps, separate from scored model cards."""
import html
import json


def render(content, models, page, intro):
    catalog=json.loads((content/'coverage.json').read_text())
    esc=html.escape
    families=len({m['family'] for m in models.values()})
    body=intro('MODEL COVERAGE','Coverage status',
               'Author sources, evaluation progress and concrete gaps for representative controllers.')
    body+=f'<section class="section docs"><p>{len(models)} evaluated checkpoint versions across {families} model families. Updated {esc(catalog["updated"])}.</p>'
    body+='<p>'+esc(catalog['scope'])+'</p><p>'+esc(catalog['selection'])+'</p>'
    body+='<p>Ranked results use one versioned protocol, public inference code and trace verification. Author attribution does not imply that the authors submitted or endorsed these evaluations.</p></section>'
    body+='<section class="section docs"><h2>Remaining work</h2>'
    for item in catalog['entries']:
        body+=f'<article class="metric-box"><h3>{esc(item["name"])}</h3><p><strong>{esc(item["status"])}</strong> · {esc(item["gap"])}</p><p>Next: {esc(item["next_step"])}</p>'
        body+=f'<p><a href="{esc(item["author_source"],quote=True)}">Author source ↗</a>'
        if item.get('evaluation_code'):
            body+=f' · <a href="{esc(item["evaluation_code"],quote=True)}">Adaptation code ↗</a>'
        body+='</p></article>'
    body+='</section><p class="small">Report an official release or a missing controller in the <a href="https://github.com/MotionChallenge-Project/MotionChallenge-Core/issues">public issue tracker</a>.</p>'
    page('/coverage/','Coverage status',body,'Models')
