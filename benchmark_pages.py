"""Data-driven benchmark directory and dataset × robot documentation.

The renderer knows document structure, not dataset names, failure formulas,
robot names or metric counts. Protocol values are read through explicit bindings.
"""
import html
import json
import re
from urllib.parse import urlencode


def esc(value):
    return html.escape(str(value), quote=True)


def load_catalog(content, tracks):
    catalog = json.loads((content/'benchmarks.json').read_text())
    ids = [b['id'] for b in catalog]
    assert len(ids) == len(set(ids)), 'Duplicate benchmark ID'
    assert all(re.fullmatch(r'[a-z0-9-]+', i) for i in ids)
    assert all(t['benchmark_id'] in ids for t in tracks), 'Unknown benchmark in track'
    return catalog


def section_html(section, bindings):
    def text(value):
        return esc(value.format_map(bindings))
    slug = section['id']
    assert re.fullmatch(r'[a-z0-9-]+', slug), 'Invalid section ID'
    body = ''.join('<p>'+text(p)+'</p>' for p in section.get('paragraphs', []))
    if table := section.get('table'):
        headers = ''.join('<th scope="col">'+text(h)+'</th>' for h in table['headers'])
        rows = []
        for row in table['rows']:
            assert len(row) == len(table['headers']), 'Table column mismatch'
            rows.append('<tr>'+''.join(
                ('<th scope="row">' if i == 0 else '<td>')+text(cell)+
                ('</th>' if i == 0 else '</td>') for i,cell in enumerate(row))+'</tr>')
        body += '<div class="table-scroll"><table class="benchmark-table"><thead><tr>'+headers+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
    if notes := section.get('notes'):
        body += '<ul class="benchmark-notes">'+''.join('<li>'+text(n)+'</li>' for n in notes)+'</ul>'
    if links := section.get('links'):
        body += '<div class="benchmark-sources">'+''.join(
            '<a href="'+esc(link['url'])+'">'+text(link['label'])+' ↗</a>' for link in links)+'</div>'
    return '<section class="benchmark-section" id="'+slug+'"><h2>'+esc(section['title'])+'</h2>'+body+'</section>'


def render_document(content, benchmark, track):
    dataset = json.loads((content/benchmark['document']).read_text())
    doc = json.loads((content/track['documentation']).read_text())
    protocol = json.loads((content/track['protocol_file']).read_text())
    bindings = {}
    for name, path in doc.get('bindings', {}).items():
        value = protocol
        for key in path.split('.'):
            value = value[key]
        bindings[name] = ', '.join(map(str,value)) if isinstance(value,list) else value
    sections = dataset['sections'] + doc['sections']
    assert len({s['id'] for s in sections}) == len(sections), 'Duplicate section anchor'
    toc = '<aside aria-label="Benchmark sections">'+''.join(
        '<a href="#'+esc(s['id'])+'">'+esc(s['title'])+'</a>' for s in sections)+'</aside>'
    return '<div class="docs-layout benchmark-layout">'+toc+'<article class="benchmark-doc">'+''.join(section_html(s,bindings) for s in sections)+'</article></div>'


def directory(catalog, tracks, intro):
    cards = []
    for b in catalog:
        available = [t for t in tracks if t['benchmark_id']==b['id']]
        robots = list(dict.fromkeys(t['robot_label'] for t in available))
        cards.append('<article class="benchmark-card"><div><p class="eyebrow">'+esc(b['task'])+'</p><h2><a href="/benchmarks/'+b['id']+'/">'+esc(b['label'])+' <span>↗</span></a></h2><p>'+esc(b['summary'])+'</p></div><div class="benchmark-card-meta"><span>'+esc(b['extent'])+'</span><span>'+esc(' · '.join(robots))+'</span><a href="/benchmarks/'+b['id']+'/">Protocol & results →</a></div></article>')
    return intro('EVALUATION','Benchmarks',
        'Select a dataset and robot to see the evaluation protocol and results.')+'''
<section class="section benchmark-directory"><div class="benchmark-catalog">'''+''.join(cards)+'''</div>
<p class="benchmark-contribute"><a href="/submit/#datasets">Propose a benchmark →</a></p></section>'''



def detail(content, benchmark, tracks):
    available = [t for t in tracks if t['benchmark_id']==benchmark['id']]
    assert available, 'Benchmark must have a documented track'
    first = available[0]
    dataset = json.loads((content/benchmark['document']).read_text())
    short = first.get('robot_short_label',first['robot_label'])
    title = benchmark['label']+' × '+short
    header = '<section class="pagehead benchmark-heading"><a class="benchmark-back" href="/benchmarks/">← All benchmarks</a><p class="eyebrow">'+esc(benchmark['task'])+'</p><h1><span>'+esc(benchmark['label'])+'</span><span class="benchmark-times" aria-label="on">×</span><span id="benchmark-robot-title">'+esc(short)+'</span></h1><p class="lede">'+esc(dataset['intro'])+'</p></section>'
    stats = '<section class="stats">'+''.join('<div><strong>'+esc(s['value'])+'</strong><span>'+esc(s['label'])+'</span></div>' for s in dataset['stats'])+'</section>'
    robots = dict((t['robot_id'],t['robot_label']) for t in available)
    selectors = '<section class="benchmark-controls" data-benchmark-id="'+esc(benchmark['id'])+'" data-benchmark-label="'+esc(benchmark['label'])+'"><label>Robot<select id="benchmark-robot">'+''.join('<option value="'+esc(i)+'">'+esc(label)+'</option>' for i,label in robots.items())+'</select></label><label>Protocol<select id="benchmark-protocol">'+''.join('<option value="'+esc(t['id'])+'">'+esc(t['label'])+'</option>' for t in available if t['robot_id']==first['robot_id'])+'</select></label><a class="button" id="benchmark-results" href="/leaderboard/?'+esc(urlencode({'benchmark':benchmark['id'],'robot':first['robot_id'],'track':first['id']}))+'">View results ↗</a></section>'
    documents = [render_document(content,benchmark,t) for t in available]
    templates = ''.join('<template data-benchmark-track="'+esc(t['id'])+'" data-robot-id="'+esc(t['robot_id'])+'" data-robot-label="'+esc(t.get('robot_short_label',t['robot_label']))+'" data-track-label="'+esc(t['label'])+'">'+doc+'</template>' for t,doc in zip(available,documents))
    return title, header+stats+selectors+'<div id="benchmark-document">'+documents[0]+'</div>'+templates
