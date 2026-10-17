"""Offline synthetic negative controls for eight non-automatable 20-percent gates."""
import copy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).parent
sp = importlib.util.spec_from_file_location('gate_guard', HERE / 'historical_external_eight_gate_auditor.py')
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)


def frozen():
    return {'jobs': [dict(family_id=k, project=v[0], external_constraint=v[1],
                          disposition='EXTERNAL_OR_POLICY_GATED')
                     for k,v in g.GATES.items()]}


def receipt():
    return {'schema_version': 1, 'gates': [dict(family_id=k, project=v[0],gate=v[1],
                                               state='BLOCKED', evidence=None)
                                           for k,v in g.GATES.items()]}


class ExternalEightFailClosed(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def audit(self, m=None, r=None):
        return g.audit(frozen() if m is None else m,
                       receipt() if r is None else r, self.root)

    def test_all_eight_missing_evidence_never_marks_completed(self):
        verdict=self.audit()
        self.assertEqual(verdict['families_evaluated'],8)
        self.assertEqual(verdict['external_business_families_auto_accepted'],0)
        self.assertFalse(verdict['historical_recovery_closed'])
        self.assertFalse(verdict['all_historical_business_gates_accepted'])

    def test_true_json_schema_boolean_rejected(self):
        x=receipt();x['schema_version']=True
        with self.assertRaisesRegex(ValueError,'INVALID_GATE_RECEIPT'):self.audit(r=x)

    def test_missing_gate_never_passes(self):
        x=receipt();x['gates'].pop()
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):self.audit(r=x)

    def test_duplicate_gate_row_rejected(self):
        x=receipt();x['gates'].append(x['gates'][0])
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):self.audit(r=x)

    def test_unknown_gate_rejected(self):
        x=receipt();x['gates'][0]['family_id']='WR-UNKNOWN'
        with self.assertRaisesRegex(ValueError,'UNKNOWN_GATE'):self.audit(r=x)

    def test_manifest_mapping_drift_is_rejected(self):
        x=frozen();x['jobs'][0]['external_constraint']='CODEX_RUN'
        with self.assertRaisesRegex(ValueError,'MAPPING_DRIFT'):self.audit(m=x)

    def test_manifest_disposition_drift_rejected(self):
        x=frozen();x['jobs'][0]['disposition']='READY_FOR_LOCAL_CODEX'
        with self.assertRaisesRegex(ValueError,'WRONG_GATED'):self.audit(m=x)

    def test_boolean_status_or_forged_approval_rejected(self):
        for state in (True,'PASS','APPROVED','DONE','VERIFIED'):
            with self.subTest(state=state):
                x=receipt();x['gates'][0]['state']=state
                with self.assertRaises(ValueError):self.audit(r=x)

    def test_real_evidence_bytes_only_establish_content_integrity(self):
        f=self.root/'synthetic-review.txt';f.write_text('synthetic architecture review, no runtime authorization\n')
        x=receipt();x['gates'][-1]['state']='REVIEW_DOCUMENTED'
        x['gates'][-1]['evidence']={'relative_path':'synthetic-review.txt',
                                    'sha256':sha256(f.read_bytes()).hexdigest()}
        verdict=self.audit(r=x)
        self.assertEqual(verdict['review_documents_checked'],1)
        self.assertEqual(verdict['local_evidence_checked'],1)
        self.assertFalse(verdict['historical_recovery_closed'])
        self.assertFalse(verdict['production_or_user_approval_authenticated'])

    def test_wool_real_gold_file_hash_does_not_auto_accept(self):
        f=self.root/'synthetic-gold.json';f.write_text('{"synthetic":true}')
        x=receipt();x['gates'][1]['state']='LOCAL_EVIDENCE_ONLY'
        x['gates'][1]['evidence']={'relative_path':f.name,'sha256':sha256(f.read_bytes()).hexdigest()}
        v=self.audit(r=x)
        self.assertEqual(v['local_evidence_checked'],1)
        self.assertTrue(v['results'][1]['needs_independent_human_or_runtime_acceptance']) if v['results'][1]['family_id']=='WR-H13' else self.assertTrue(any(i['family_id']=='WR-H13' and i['needs_independent_human_or_runtime_acceptance'] for i in v['results']))
        self.assertFalse(v['all_historical_business_gates_accepted'])

    def test_missing_evidence_file_rejected(self):
        x=receipt();x['gates'][0]['state']='LOCAL_EVIDENCE_ONLY'
        x['gates'][0]['evidence']={'relative_path':'missing.txt','sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'EVIDENCE_NOT_REGULAR'):self.audit(r=x)

    def test_modified_evidence_digest_rejected(self):
        f=self.root/'local.txt';f.write_text('changed source')
        x=receipt();x['gates'][0]['state']='LOCAL_EVIDENCE_ONLY'
        x['gates'][0]['evidence']={'relative_path':f.name,'sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):self.audit(r=x)

    def test_traversal_rejected(self):
        x=receipt();x['gates'][0]['state']='LOCAL_EVIDENCE_ONLY'
        x['gates'][0]['evidence']={'relative_path':'../secret.txt','sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'TRAVERSAL'):self.audit(r=x)

    def test_ignored_symbolic_link_to_private_data_rejected(self):
        outside=Path(self.tmp.name).parent/'synthetic-temp-secret.txt'
        outside.write_text('synthetic')
        self.addCleanup(outside.unlink, True)
        (self.root/'link.txt').symlink_to(outside)
        x=receipt();x['gates'][0]['state']='LOCAL_EVIDENCE_ONLY'
        x['gates'][0]['evidence']={'relative_path':'link.txt','sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'SYMLINK'):self.audit(r=x)

    def test_nested_symlink_dir_rejected(self):
        inside=self.root/'real';inside.mkdir();(inside/'file').write_text('synthetic')
        (self.root/'alias').symlink_to(inside,target_is_directory=True)
        x=receipt();x['gates'][0]['state']='LOCAL_EVIDENCE_ONLY'
        x['gates'][0]['evidence']={'relative_path':'alias/file','sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'SYMLINK'):self.audit(r=x)

    def test_oversized_evidence_rejected(self):
        p=self.root/'oversized';p.write_bytes(b'x'*(g.MAX_BYTES+1))
        x=receipt();x['gates'][0]['state']='LOCAL_EVIDENCE_ONLY'
        x['gates'][0]['evidence']={'relative_path':'oversized','sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'OVERSIZE'):self.audit(r=x)

    def test_review_documented_cannot_approve_nonreview_gate(self):
        f=self.root/'data';f.write_text('synthetic')
        x=receipt();x['gates'][0]['state']='REVIEW_DOCUMENTED'
        x['gates'][0]['evidence']={'relative_path':'data','sha256':sha256(f.read_bytes()).hexdigest()}
        with self.assertRaisesRegex(ValueError,'REVIEW_DOCUMENTED_ONLY'):self.audit(r=x)

    def test_strict_duplicate_nested_keys_rejected(self):
        with self.assertRaisesRegex(ValueError,'AMBIGUOUS_DUPLICATE'):
            g.strict_json(b'{"gates":[{"state":"BLOCKED","state":"APPROVED"}]}')

    def test_pathological_nested_json_fails_closed_not_crash(self):
        payload=b'['*11000 + b'0' + b']'*11000
        with self.assertRaisesRegex(ValueError, 'EXCESSIVE_JSON_NESTING'):
            g.strict_json(payload)

    def test_invalid_utf8_and_nonfinite_number_rejected(self):
        for row in (b'\xff',b'{"confidence":NaN}',b'{"confidence":Infinity}'):
            with self.subTest(row=row):
                with self.assertRaises(ValueError):g.strict_json(row)

    def test_all_eight_gates_immutable_exact_set(self):
        self.assertEqual(set(g.GATES),{'WR-H12','WR-H13','WR-H14','WR-H17',
                                       'SAM-H08','SAM-H11','SAM-H24','COORD-H07'})

if __name__=='__main__':unittest.main()

class HardenedEvidenceBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_json_exponent_overflow_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'NONFINITE_JSON_NUMBER'):
            g.strict_json(b'{"score":1e9999}')

    def test_fifo_is_not_read_or_blocked(self):
        import os
        fifo = self.root / 'synthetic_pipe'
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, 'EVIDENCE_NOT_REGULAR'):
            g._read_safe_evidence(self.root, fifo.name)

    def test_root_symlink_is_not_followed(self):
        alias = self.root.parent / (self.root.name + '_alias')
        alias.symlink_to(self.root, target_is_directory=True)
        self.addCleanup(alias.unlink)
        (self.root/'evidence').write_text('safe')
        with self.assertRaisesRegex(ValueError, 'EVIDENCE_NOT_REGULAR_OR_SYMLINK'):
            g._read_safe_evidence(alias, 'evidence')

    def test_evidence_normal_nested_path_read(self):
        directory = self.root/'nested'
        directory.mkdir()
        (directory/'data').write_bytes(b'known-good')
        self.assertEqual(g._read_safe_evidence(self.root,'nested/data'),b'known-good')

    def test_evidence_limit_exact_boundary(self):
        p=self.root/'limit'
        p.write_bytes(b'x'*g.MAX_BYTES)
        self.assertEqual(len(g._read_safe_evidence(self.root,p.name)),g.MAX_BYTES)
        p.write_bytes(b'x'*(g.MAX_BYTES+1))
        with self.assertRaisesRegex(ValueError,'OVERSIZE_EVIDENCE'):
            g._read_safe_evidence(self.root,p.name)
