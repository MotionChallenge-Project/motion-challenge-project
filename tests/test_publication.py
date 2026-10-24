import copy
import json
from pathlib import Path
import unittest
from publication_checks import validate, validate_row, validate_inference

CONTENT=Path(__file__).resolve().parents[1]/'content'
class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.models=json.loads((CONTENT/'models.json').read_text())
        self.rows=json.loads((CONTENT/'results.json').read_text())['rows']
        self.tracks=json.loads((CONTENT/'tracks.json').read_text())
        self.row=next(r for r in self.rows if r['model']=='grit')
        self.evidence=json.loads((CONTENT/'evidence'/self.row['evidence_file']).read_text())
    def test_all_current_evidence_matches(self):
        validate(CONTENT,self.rows,self.models,self.tracks)
    def test_forged_displayed_score_is_rejected(self):
        row=copy.deepcopy(self.row);row['passed']+=1
        with self.assertRaisesRegex(ValueError,'success count'):
            validate_row(row,self.models['grit'],self.tracks[0],self.evidence)
    def test_rule_drift_is_rejected(self):
        track=dict(self.tracks[0],robot_profile_sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'robot_profile'):
            validate_row(self.row,self.models['grit'],track,self.evidence)
    def test_altered_trace_summary_is_rejected(self):
        evidence=copy.deepcopy(self.evidence);evidence['result']['clips'].pop()
        with self.assertRaisesRegex(ValueError,'changed result'):
            validate_row(self.row,self.models['grit'],self.tracks[0],evidence)
    def test_failed_repeat_cannot_be_published(self):
        evidence=copy.deepcopy(self.evidence);evidence['repeatability']['status']='different'
        with self.assertRaisesRegex(ValueError,'repeatability'):
            validate_row(self.row,self.models['grit'],self.tracks[0],evidence)
    def test_nonfinite_metric_is_rejected(self):
        row=dict(self.row,mpjpe_world_m=float('nan'))
        with self.assertRaisesRegex(ValueError,'displayed'):
            validate_row(row,self.models['grit'],self.tracks[0],self.evidence)
    def test_inference_checkpoint_mismatch_is_rejected(self):
        check=json.loads((CONTENT/'inference_checks.json').read_text())['tracks'][self.row['track_id']]['grit']
        report=json.loads((CONTENT/'inference'/check['report_file']).read_text())
        check['checkpoint_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'inference identity'):
            validate_inference(self.row,check,report)
    def test_excessive_inference_error_is_rejected(self):
        check=json.loads((CONTENT/'inference_checks.json').read_text())['tracks'][self.row['track_id']]['grit']
        report=json.loads((CONTENT/'inference'/check['report_file']).read_text())
        report['max_abs_error']['motor_command']=1.0
        with self.assertRaisesRegex(ValueError,'inference error'):
            validate_inference(self.row,check,report)

    def test_privileged_score_cannot_be_relabelled_as_restricted(self):
        for state in (None,'privileged-state-v0'):
            evidence=copy.deepcopy(self.evidence)
            evidence['result']['state_access']=state
            with self.assertRaisesRegex(ValueError,'observation access'):
                validate_row(self.row,self.models['grit'],self.tracks[0],evidence)

    def test_restricted_admission_and_protocol_are_bound_to_evidence(self):
        row=next(r for r in self.rows if r['track_id']=='lafan40-g1-ideal-proprioception-v1')
        evidence=json.loads((CONTENT/'evidence'/row['evidence_file']).read_text())
        track=next(t for t in self.tracks if t['id']==row['track_id'])
        altered=copy.deepcopy(evidence)
        altered['observation_admission']['checkpoint_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'admission source hash'):
            validate_row(row,self.models[row['model']],track,altered)
        altered_track=dict(track,protocol_sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'protocol identity'):
            validate_row(row,self.models[row['model']],altered_track,evidence)
