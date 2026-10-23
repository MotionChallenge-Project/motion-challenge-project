"""Checkpoint catalog and protocol-specific evaluation records."""
import html
import json
from collections import defaultdict


def esc(value):
    return html.escape(str(value), quote=True)


def link(url, label, css=''):
    return f'<a class="{css}" href="{esc(url)}">{esc(label)}</a>'


def facts(items):
    return '<dl class="facts">' + ''.join(f'<div><dt>{esc(k)}</dt><dd>{v}</dd></div>' for k, v in items) + '</dl>'


def evaluation_path(track_id, model_id):
    return f'/evaluations/{track_id}/{model_id}/'


def render(models, rows, tracks, content, github, page, intro):
    track_by_id = {t['id']: t for t in tracks}
    groups = defaultdict(list)
    for row in rows:
        groups[row['track_id'], row['model']].append(row)
    notes_path = content / 'evaluation_notes.json'
    notes = json.loads(notes_path.read_text()) if notes_path.exists() else {}

    cards = ''.join(
        f'<a class="model-card" href="/models/{esc(k)}/"><span class="tag">CHECKPOINT</span>'
        f'<h2>{esc(m["display_name"])}<span>↗</span></h2><p>{esc(m["organization"])}</p></a>'
        for k, m in models.items()
    )
    page('/models/', 'Models', intro('MODEL CATALOG', 'Models',
        'Released model versions, checkpoint artifacts and inference interfaces.')
        + f'<section class="section model-grid">{cards}</section>', 'Models')

    for key, model in models.items():
        rt, provenance = model['runtime'], model['provenance']
        repo = f'{github}/motion-challenge-{key}'
        revision = provenance.get('source_commit')
        source = provenance['upstream']
        source_url = source.rstrip('/') + '/tree/' + revision if revision else source
        model_facts = [
            ('Organization', link(model['organization_source'], model['organization'])),
            ('Version', esc(model['version']) + '<br><span class="small">' + esc(model['version_kind']) + '</span>'),
            ('Robot support', esc(' · '.join(model.get('supported_robots', ['Unitree G1 · 29 DoF'])))),
            ('Author source revision', link(source_url, revision or 'Not recorded')),
        ]
        description = model.get('description', 'Checkpoint artifacts and an independent Motion Challenge inference adapter.')
        detail = f'<section class="section split"><div><h2>Model</h2><p>{esc(description)}</p><div class="actions">'
        detail += link(source, 'Author source ↗', 'button') + link(repo, 'Inference adapter ↗', 'text-link') + '</div>'
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
        detail += '<p class="small">Download links deliver the adapter files. The author release above establishes their origin; SHA256 identifies the bytes used.</p>'
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
        detail += link('/leaderboard/?track=' + track_id + '&benchmark=' + track['benchmark_id'] + '&robot=' + track['robot_id'], 'Leaderboard ↗', 'text-link') + '</div>'
        detail += '<p class="small">Evaluated by Motion Challenge using the shared protocol. This is an independent evaluation, not an author submission.</p></section>'
        key_notes = notes.get(track_id, {}).get(key, [])
        if key_notes:
            detail += '<section class="section evaluation-context"><h2>Evaluation context</h2>' + ''.join('<p>' + esc(n['text']) + (' ' + link(n['source'], 'Source ↗', 'text-link') if n.get('source') else '') + '</p>' for n in key_notes) + '</section>'
        for mode, label, anchor in [('early_termination', 'Early termination', 'early'), ('no_termination', 'No termination', 'none')]:
            result = next((r for r in results if r.get('termination_mode', 'early_termination') == mode), None)
            detail += f'<section class="section evaluation-mode" id="{anchor}"><p class="eyebrow">{esc(heading)}</p><h2>{label}</h2>'
            if result is None:
                detail += '<p>No verified result has been published for this rollout mode.</p></section>'
                continue
            evidence = json.loads((content / 'evidence' / result['evidence_file']).read_text())
            receipt = evidence['receipt']
            verification = receipt.get('verification', {})
            scope = 'Entire motion, including post-failure states.' if mode == 'no_termination' else 'Observed prefix through the first failure frame.'
            detail += f'<div class="evaluation-score"><strong>{result["passed"]} / {result["total"]}</strong><span>motions passed</span><span>Completion {result["completion_pct"]:.2f}%</span></div>'
            detail += '<p>' + scope + ' Success and completion use the first declared failure.</p>'
            metrics = [('XY + yaw', 'mpjpe_xy_yaw_aligned_m'), ('XY only', 'mpjpe_xy_aligned_m'), ('No alignment', 'mpjpe_world_m')]
            detail += '<div class="table-scroll"><table class="evaluation-metrics"><caption>Mean per-body position error · MPBPE · mm ↓</caption><thead><tr>' + ''.join('<th scope="col">' + label_ + '</th>' for label_, _ in metrics) + '</tr></thead><tbody><tr>'
            detail += ''.join(f'<td>{result[field] * 1000:.2f}</td>' for _, field in metrics) + '</tr></tbody></table></div>'
            detail += '<div class="evaluation-details">' + facts([
                ('Protocol', '<code>' + esc(result.get('protocol_id') or (track['no_termination_protocol_id'] if mode == 'no_termination' else track['protocol_id'])) + '</code>'),
                ('Engine', 'MuJoCo ' + esc(result['mujoco_version']) + ' · official CPU batch'),
                ('Checkpoint SHA256', '<code>' + esc(result['checkpoint_sha256']) + '</code>'),
                ('Evaluated adapter', link(result['adapter_code_url'], result['adapter_commit'])),
                ('Evaluated core', link(result['core_code_url'], result['core_commit'])),
                ('Finished (UTC)', esc(receipt.get('finished_utc', 'Not recorded'))),
                ('Trace verification', esc(verification.get('verification', result.get('verification', 'Not recorded'))) + ' · ' + esc(verification.get('samples', '—')) + ' samples'),
            ]) + '<div><h3>Reproduce this run</h3><pre><code>' + esc('\n'.join(evidence['reproduction']['commands'])) + '</code></pre>'
            detail += link('/data/evidence/' + result['evidence_file'], 'Per-motion results, receipt & commands (JSON) ↗', 'text-link')
            detail += '<p class="small">Trace verification recomputes timing, failure conditions and metrics. It does not establish author-inference parity; adapter provenance records that separately.</p></div></div></section>'
        page(evaluation_path(track_id, key), model['display_name'] + ' · ' + heading, intro('EVALUATION RECORD', model['display_name'], heading + ' · ' + track['label']) + detail, 'Leaderboard')
