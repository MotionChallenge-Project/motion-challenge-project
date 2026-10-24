"""Checkpoint catalog and protocol-specific evaluation records."""
import html
import json
import re
from collections import defaultdict


def esc(value):
    return html.escape(str(value), quote=True)


def repository_location(value):
    """Resolve moved repositories while preserving evaluated revisions."""
    value = re.sub(r'(https://github\.com/|git@github\.com:)(?:MotionChallenge|motion-challenge-project)/',
                   r'\1MotionChallenge-Project/', value, flags=re.IGNORECASE)
    return re.sub(r'(MotionChallenge-Project/)motion-challenge(?![\w-])',
                  r'\1MotionChallenge-Core', value)


def link(url, label, css=''):
    return f'<a class="{css}" href="{esc(repository_location(url))}">{esc(label)}</a>'


def model_icon(model):
    if model.get('icon'):
        return f'<img class="model-icon" src="{esc(model["icon"])}" width="40" height="40" alt="" title="{esc(model["icon_label"])}">'
    return f'<span class="model-icon model-initial" aria-hidden="true">{esc(model["display_name"][0].upper())}</span>'


def facts(items):
    return '<dl class="facts">' + ''.join(f'<div><dt>{esc(k)}</dt><dd>{v}</dd></div>' for k, v in items) + '</dl>'


def evaluation_path(track_id, model_id):
    return f'/evaluations/{track_id}/{model_id}/'


def evaluation_record(results, track, key, content, github):
    """One score table, source block and command for an evaluation."""
    unified = next((r for r in results if r.get('termination_mode') == 'unified'), None)
    early = unified or next((r for r in results if r.get('termination_mode', 'early_termination') == 'early_termination'), None)
    full = unified or next((r for r in results if r.get('termination_mode') == 'no_termination'), None)
    assert early is not None
    if full:
        assert early['passed'] == full['passed'] and abs(early['completion_pct']-full['completion_pct']) < 1e-7
    fields = [('XY + yaw', 'mpjpe_xy_yaw_aligned_m'), ('XY only', 'mpjpe_xy_aligned_m'), ('No alignment', 'mpjpe_world_m')]
    text = '<section class="section evaluation-mode" id="results"><h2>Results</h2>'
    text += f'<div class="evaluation-score"><strong>{early["passed"]} / {early["total"]}</strong><span>motions passed</span><span>Completion {early["completion_pct"]:.2f}%</span></div>'
    text += '<p>Success and completion use the first declared failure. MPBPE reports 14 key-body position errors with three alignments over two time ranges.</p>'
    text += '<div class="table-scroll"><table class="evaluation-metrics"><caption>Mean per-body position error · MPBPE · mm ↓</caption><thead><tr><th colspan="3" scope="colgroup" id="early">Until first failure</th><th colspan="3" scope="colgroup" id="none">Entire motion</th></tr><tr>'
    text += ''.join('<th scope="col">'+label+'</th>' for label, _ in fields*2)+'</tr></thead><tbody><tr>'
    for row, prefix in [(early, ''), (full, 'full_' if unified else '')]:
        text += ''.join('<td>'+ (f'{row[prefix+field]*1000:.2f}' if row is not None else '—') +'</td>' for _, field in fields)
    text += '</tr></tbody></table></div><p class="small">The first range includes the failure frame; the full-motion range includes every frame after failure through the final reference frame, without resetting.</p>'
    common = [('Benchmark', esc(track['benchmark_label']+' × '+track['robot_short_label']+' · '+track['label'])),
              ('Engine', 'MuJoCo '+esc(early['mujoco_version'])+' · official CPU batch'),
              ('Checkpoint SHA256', '<code>'+esc(early['checkpoint_sha256'])+'</code>')]
    repo = early.get('adapter_repository', github+'/motion-challenge-'+key)
    if unified:
        evidence = json.loads((content/'evidence'/unified['evidence_file']).read_text())
        common += [('Evaluated adapter', link(unified['adapter_code_url'], unified['adapter_commit'])),
                   ('Evaluated core', link(unified['core_code_url'], unified['core_commit'])),
                   ('Verification', 'Both trajectory ranges recomputed · repeatability checked')]
        commands = []
        for command in evidence['reproduction']['commands']:
            if command.startswith('git submodule update'):
                commands.append('git config submodule.motion-challenge.url https://github.com/MotionChallenge-Project/MotionChallenge-Core.git')
            commands.append(repository_location(command))
        downloads = link('/data/evidence/'+unified['evidence_file'], 'Complete results, source & verification (JSON) ↗', 'text-link')
        title = 'Reproduce this run'
        note = 'One command produces success, completion and all six MPBPE values in one result.json.'
    else:
        # Preserve actual old sources until a new shared-source run passes comparison.
        source_items = []
        downloads = ''
        for row, label in [(early, 'Until first failure'), (full, 'Entire motion')]:
            if row is None:
                continue
            source_items.append(esc(label)+': '+link(row['adapter_code_url'], 'adapter '+row['adapter_commit'][:7])+' · '+link(row['core_code_url'], 'core '+row['core_commit'][:7]))
            downloads += link('/data/evidence/'+row['evidence_file'], label+' evidence (JSON) ↗', 'text-link')+' '
        common.append(('Recorded source versions', '<br>'.join(source_items)))
        reruns = json.loads((content/'unified_reruns.json').read_text())
        revision = reruns[key]['commit']
        commands = ['git clone '+repo+'.git', 'cd motion-challenge-'+key, 'git checkout '+revision,
                    'git submodule update --init --recursive', 'uv sync --locked', 'uv run evaluate.py']
        title = 'Run the unified evaluation'
        note = 'The one-command rerun is being checked against these recorded scores. Its source and complete result will replace the previous records after verification.'
    text += '<div class="evaluation-details">'+facts(common)+'<div><h3>'+title+'</h3><pre><code>'+esc('\n'.join(commands))+'</code></pre><p class="small">'+note+'</p>'+downloads+'</div></div></section>'
    return text


def render(models, rows, tracks, content, github, page, intro):
    track_by_id = {t['id']: t for t in tracks}
    groups = defaultdict(list)
    for row in rows:
        groups[row['track_id'], row['model']].append(row)
    notes_path = content / 'evaluation_notes.json'
    notes = json.loads(notes_path.read_text()) if notes_path.exists() else {}

    cards = ''.join(
        f'<a class="model-card" href="/models/{esc(k)}/"><div class="model-card-label">{model_icon(m)}<span class="tag">CHECKPOINT</span></div>'
        f'<h2>{esc(m["display_name"])}<span>↗</span></h2><p>{esc(m["organization"])}</p></a>'
        for k, m in models.items()
    )
    page('/models/', 'Models', intro('MODEL CATALOG', 'Models',
        'Released model versions, checkpoint artifacts and inference interfaces.')
        + f'<section class="section model-grid">{cards}</section>', 'Models')

    for key, model in models.items():
        rt, provenance = model['runtime'], model['provenance']
        repo = model.get('adapter_repository', f'{github}/motion-challenge-{key}')
        revision = provenance.get('source_commit')
        source = provenance['upstream']
        source_url = source.rstrip('/') + '/tree/' + revision if revision else source
        model_facts = [
            ('Organization', link(model['organization_source'], model['organization'])),
            ('Type', link(model['controller_type']['source'], model['controller_type']['label']) + '<br><span class="small">' + esc(model['controller_type']['description']) + '</span>'),
            ('Version', esc(model['version']) + '<br><span class="small">' + esc(model['version_kind']) + '</span>'),
            ('Robot support', esc(' · '.join(model.get('supported_robots', ['Unitree G1 · 29 DoF'])))),
            ('Author source revision', link(source_url, revision or 'Not recorded')),
        ]
        description = model.get('description', 'Checkpoint artifacts and an independent Motion Challenge inference adapter.')
        detail = f'<section class="section split"><div><h2>Model</h2><p>{esc(description)}</p><div class="actions">'
        detail += link(model.get('project_url') or source, 'Author source ↗', 'button') + link(repo, 'Inference adapter ↗', 'text-link') + '</div>'
        if model.get('training_data'):
            training = model['training_data']
            detail += '<h3>Training data</h3><p>' + esc(training['description']) + '</p>' + link(training['source'], 'Author documentation ↗', 'text-link')
        detail += '</div>' + facts(model_facts) + '</section>'
        artifacts = [('Policy checkpoint', rt['weights_url'], rt['weights_sha256'])]
        artifacts += [(name, a['url'], a['sha256']) for name, a in rt.get('artifacts', {}).items() if a.get('url')]
        detail += '<section class="section model-artifacts"><h2>Checkpoint artifacts</h2>'
        origin = provenance.get('checkpoint_origin', {})
        if origin:
            detail += facts([
                ('Author release', link(origin['author_release_url'], origin['author_release_label'] + ' ↗')),
                ('Artifact type', esc(origin['kind_label'])),
                ('Original file', link(origin['artifact_page_url'], origin['original_filename'] + ' ↗')),
            ])
            detail += '<p class="small">' + esc(origin['verification']) + '</p>'
            if origin.get('verification_url'):
                detail += link(origin['verification_url'], 'Checkpoint comparison ↗', 'text-link')
        detail += ''.join('<p class="small">' + esc(note) + '</p>' for note in model.get('artifact_notes', []))
        detail += '<p class="small">Download links deliver the adapter files. The release links and verification notes distinguish author files from conversions; SHA256 identifies the bytes used.</p>'
        for name, url, sha in artifacts:
            detail += f'<div class="artifact-row"><div>{esc(name)}<br>{link(url, "Download ↗")}</div><code>{esc(sha)}</code></div>'
        detail += '</section><section class="section split"><div><h2>Inference interface</h2><p>The adapter declares its control clock and reference window below. Source and configuration describe the observation and action transforms.</p><div class="actions">'
        detail += link(repo + '/blob/main/adapter.py', 'Inference implementation ↗', 'text-link')
        detail += link(repo + '/blob/main/provenance.json', 'Provenance ↗', 'text-link') + '</div></div>'
        detail += facts([
            ('Control interval', f'{rt["control_period_s"] * 1000:g} ms'),
            ('Reference history', f'{rt.get("reference_history_s", 0) * 1000:g} ms'),
            ('Reference preview', f'{rt["reference_preview_s"] * 1000:g} ms'),
            ('Output interface', esc(rt.get('action_mode', 'See runtime contract'))),
            ('Configuration', link(repo + '/blob/main/' + rt['inference_config'], rt['inference_config'])),
        ]) + '</section>'
        related = [(track_by_id[tid], evaluation_path(tid, key)) for tid, mid in groups if mid == key]
        detail += '<section class="section model-evaluations"><h2>Evaluations</h2>'
        if related:
            detail += '<div class="evaluation-links">' + ''.join(link(path, t['benchmark_label'] + ' × ' + t['robot_short_label'] + ' · ' + t['label'] + ' ↗', 'text-link') for t, path in related) + '</div>'
        else:
            detail += '<p>No published evaluation record.</p>'
        detail += '</section>'
        page('/models/' + key + '/', model['display_name'], intro('MODEL / CHECKPOINT', model['display_name'], model['organization']) + detail, 'Models')

    for (track_id, key), results in groups.items():
        track, model = track_by_id[track_id], models[key]
        assert len({r.get('termination_mode', 'early_termination') for r in results}) == len(results), 'Duplicate rollout mode'
        assert len({r['checkpoint_sha256'] for r in results}) == 1, 'Rollout modes must use the same checkpoint'
        heading = track['benchmark_label'] + ' × ' + track['robot_short_label']
        detail = '<section class="section evaluation-overview"><div class="actions">'
        detail += link('/models/' + key + '/', 'Model card ↗', 'text-link')
        detail += link('/benchmarks/' + track['benchmark_id'] + '/?robot=' + track['robot_id'] + '&track=' + track_id, 'Benchmark conditions ↗', 'text-link')
        detail += link('/?track=' + track_id + '&benchmark=' + track['benchmark_id'] + '&robot=' + track['robot_id'], 'Leaderboard ↗', 'text-link') + '</div>'
        detail += '<p class="small">Evaluated by Motion Challenge using the shared protocol. This is an independent evaluation, not an author submission.</p></section>'
        key_notes = notes.get(track_id, {}).get(key, [])
        if key_notes:
            detail += '<section class="section evaluation-context"><h2>Evaluation context</h2>' + ''.join('<p>' + esc(n['text']) + (' ' + link(n['source'], 'Source ↗', 'text-link') if n.get('source') else '') + '</p>' for n in key_notes) + '</section>'
        detail += evaluation_record(results, track, key, content, github)
        page(evaluation_path(track_id, key), model['display_name'] + ' · ' + heading, intro('EVALUATION RECORD', model['display_name'], heading + ' · ' + track['label']) + detail, 'Leaderboard')
