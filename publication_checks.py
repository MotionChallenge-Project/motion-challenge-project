"""Fail a website build when a displayed score disagrees with its run evidence.

This checks publication consistency. Raw-trace verification and native-inference
review remain separate, required evaluation steps; JSON is not execution proof.
"""
import hashlib
import json
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same_number(a, b, label):
    require(math.isfinite(a) and math.isfinite(b) and
            math.isclose(a, b, rel_tol=0, abs_tol=1e-10), label)


def validate_inference(row, check, report):
    name = row['model']
    require(check['status'] == 'passed' and
            check['production_inference_alignment'] == 'identical', name+': inference approval')
    require(check['checkpoint_sha256'] == row['checkpoint_sha256'] and
            check['evaluated_adapter_commit'] == row['adapter_commit'], name+': inference identity')
    require(report['cases'] >= 160 and report['resets'] >= 4, name+': inference coverage')
    for field in ('report_url', 'code_url', 'runtime_url'):
        require('/blob/'+check['checked_adapter_commit']+'/' in check[field], name+': inference source')
    errors = report.get('max_abs_errors', report.get('max_abs_error', report.get('max_abs')))
    require(bool(errors), name+': missing inference errors')
    for key, error in errors.items():
        limit = check['limits'][key] if isinstance(check['limits'], dict) else check['limits']
        require(math.isfinite(error) and 0 <= error <= limit, name+': inference error '+key)
    require(report.get('status', 'passed') == 'passed' and
            report.get('passed', True) is True, name+': failed inference report')


def validate_row(row, model, track, evidence):
    name=row['model']; result=evidence['result']; source=result['source']
    require(evidence['model']==name, name+': wrong evidence')
    require(result['schema'] in ('MotionChallenge/unified-result-v1', 'motion-challenge/unified-result-v1') and
            result['status']=='trace_verified', name+': unverified result')
    digest=hashlib.sha256((json.dumps(result, indent=2)+'\n').encode()).hexdigest()
    require(digest==evidence['result_sha256'], name+': changed result')
    require(result['backend']=='batch' and result['mujoco_version']==track['mujoco_version'], name+': engine')
    require(row['termination_mode']=='unified' and row['mujoco_version']==result['mujoco_version'], name+': result mode')
    for field in ('suite_sha256', 'robot_profile_sha256'):
        require(result[field]==track[field], name+': '+field)
    for field in ('adapter_commit', 'core_commit'):
        require(row[field]==source[field] and row[field]==evidence['reproduction'][field], name+': source identity')
        require(row[field] in row[field.replace('_commit', '_code_url')], name+': unpinned code link')
    require(not source['adapter_dirty'] and not source['core_dirty'], name+': dirty source')
    require(evidence['summary']['source']==source and evidence['summary']['status']=='trace_verified', name+': summary')
    require(row['checkpoint_sha256']==result['checkpoint_sha256']==model['runtime']['weights_sha256'], name+': checkpoint')
    repeat=evidence['repeatability']
    require(repeat['status']=='passed' and not repeat.get('differences') and
            not repeat.get('difference_fields'), name+': repeatability')
    for mode in ('early', 'none'):
        receipt=evidence['receipts'][mode]
        require(receipt['status']=='trace_verified' and receipt['full_suite'] and
                receipt['source_unchanged_during_run'] and receipt['source']==source, name+': receipt')
        require(receipt['verification']['verification']=='trace_consistent' and
                receipt['verification']['full_suite'], name+': trajectory verification')
        if 'modes' in repeat:
            proof=repeat['modes'][mode]
            require(proof['new_result_sha256']==result['components'][mode]['result_sha256'] and
                    proof['new_receipt_sha256']==result['components'][mode]['receipt_sha256'], name+': repeat components')
    if 'first_result_sha256' in repeat:
        require(repeat['first_result_sha256']==digest, name+': repeat result identity')
    if 'result_sha256' in repeat:
        require(digest in repeat['result_sha256'].values(), name+': repeat result identity')
    clips=result['clips'];count=track['clip_count']
    require(row['total']==result['total']==len(clips)==len({c['id'] for c in clips})==count, name+': incomplete suite')
    require(row['passed']==result['success_count']==sum(c['success'] for c in clips), name+': success count')
    for clip in clips:
        require(0<=clip['completion']<=1 and clip['duration_s']>0, name+': invalid motion')
        require(0<clip['sample_count']['until_first_failure']<=clip['sample_count']['full_motion'], name+': sample ranges')
    same_number(result['macro_completion'],sum(c['completion'] for c in clips)/count,name+': completion')
    same_number(row['completion_pct'],result['macro_completion']*100,name+': displayed completion')
    for scope, prefix in (('until_first_failure',''), ('full_motion','full_')):
        for metric,value in result['metrics'][scope].items():
            same_number(value,sum(c['metrics'][scope][metric] for c in clips)/count,name+': macro '+metric)
            same_number(row[prefix+metric],value,name+': displayed '+prefix+metric)


def validate(content, rows, models, tracks):
    by_id={t['id']:t for t in tracks};seen=set()
    require(set(models)=={r['model'] for r in rows}, 'Model cards and ranked models differ')
    checks=json.loads((content/'inference_checks.json').read_text())['models']
    require(set(checks)==set(models), 'Ranked models require inference checks')
    for row in rows:
        identity=(row['track_id'],row['model'])
        require(identity not in seen, 'Duplicate model/track result');seen.add(identity)
        filename=row['evidence_file']
        require(Path(filename).name==filename, 'Evidence must be a local JSON file')
        evidence=json.loads((content/'evidence'/filename).read_text())
        validate_row(row, models[row['model']], by_id[row['track_id']], evidence)
        check=checks[row['model']]
        require(Path(check['report_file']).name==check['report_file'], 'Inference report must be local')
        raw=(content/'inference'/check['report_file']).read_bytes()
        require(hashlib.sha256(raw).hexdigest()==check['report_sha256'], row['model']+': changed inference report')
        validate_inference(row, check, json.loads(raw))
