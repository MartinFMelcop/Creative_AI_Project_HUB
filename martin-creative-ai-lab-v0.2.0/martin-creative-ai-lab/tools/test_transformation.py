#!/usr/bin/env python3
"""Mutant controls for transformation claims; fixtures are not research evidence."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import check_transformation as contract


class TransformationClaims(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);self.root=Path(folder.name)
        for name in ('labs/rpg-systems/run.py','labs/combat-response/run.py','north-star/domain/Encounter.cs','source/runtime.rb'):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('# Structural fixture only; never executed as research.\n')
        result=self.root/'evidence/result.json';result.parent.mkdir()
        source=self.root/'north-star/domain/Encounter.cs'
        result.write_text(json.dumps({'fixture':True,'kind':'destination_execution',
                                     'consumer_paths':['north-star/domain/Encounter.cs'],
                                     'commands':[{'command':['fixture-only-never-executed'],'exit_code':0}],
                                     'checks':{'passed':1,'failed':0},
                                     'source_artifacts':[{'local_path':'north-star/domain/Encounter.cs',
                                                          'size_bytes':source.stat().st_size,
                                                          'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]})+'\n')
        self.sha=hashlib.sha256(result.read_bytes()).hexdigest()
        metadata=self.root/'north-star/capabilities.json';metadata.write_text('{"engine_selection":"Unity"}')
        self.data={'schema_version':2,'updated_at':'2026-10-22','baseline_commit':'a'*40,'scope':'Structural fixture only.',
                   'allocation':{'legacy_labs':47,'north_star':40,'repository':13},
                   'direction':{'stack':'Unity/C#','player_platform':'Windows','distribution':'Steam',
                                'unity_execution':'not_executed','windows_execution':'not_executed','execution_evidence':[]},
                   'origins':[{'id':f'P{i:02d}','source_paths':['source/runtime.rb'],'execution_evidence':[],
                               'extraction_next':'Resolve real source semantics before integration.'} for i in range(1,12)],
                   'labs':[],'consumption':[]}
        for i,name in enumerate(contract.LAB_IDS,1):
            row={'id':name,'owner_origin':f'P{i:02d}','origin_projects':[f'P{i:02d}'],'status':'incomplete',
                 'domain':'Fixture domain','question':'Does the structural validator reject false claims?',
                 'source_paths':['source/runtime.rb'],'consumer_paths':['north-star/domain/Encounter.cs'],
                 'validity_boundary':'Fixture identity checks only.','next_objective':'Execute the real instrument.'}
            if name in ('rpg-systems','combat-response'):
                row.update(status='operational',path='labs/'+name,instrument='labs/'+name+'/run.py',
                           controls=['Fixture positive and negative controls'],evidence=['evidence/result.json'],
                           evidence_sha256={'evidence/result.json':self.sha})
            self.data['labs'].append(row)
        self.data['consumption']=[{'id':'fixture-build','laboratory_id':'rpg-systems','origin_projects':['P05'],
                                  'source_paths':['source/runtime.rb'],'status':'UNRESOLVED',
                                  'decision':'Test fixture, not a consumed legacy capability.',
                                  'next_action':'Investigate exact old/new semantics.'}]

    def invalid(self,expected):
        with self.assertRaisesRegex(ValueError,expected):contract.check(self.root,self.data)

    def lab(self,name='rpg-systems'):
        return next(row for row in self.data['labs'] if row['id']==name)

    def bind(self,row,name='evidence/result.json'):
        row.update(evidence=[name],evidence_sha256={name:hashlib.sha256((self.root/name).read_bytes()).hexdigest()})

    def test_truthful_destinations_and_bound_methods_are_valid(self):
        result=contract.check(self.root,self.data)
        self.assertEqual((result['laboratories'],result['operational'],result['incomplete']),(11,2,9))
        self.assertEqual(result['consumption'],{'INTEGRATED':0,'REJECTED':0,'UNRESOLVED':1})

    def test_current_authority_cannot_downgrade_to_optional_schema(self):
        self.data['schema_version']=1;self.invalid('schema_version 2')

    def test_all_eleven_destinations_and_unique_ownership_are_required(self):
        original=copy.deepcopy(self.data)
        self.data['labs'].pop();self.invalid('eleven named')
        self.data=copy.deepcopy(original);self.lab()['owner_origin']='P01';self.lab()['origin_projects']=['P01']
        self.invalid('owner_origin must match')
        self.data=copy.deepcopy(original);self.data['labs'][0]['id']='placeholder'
        self.invalid('eleven named')

    def test_allocation_and_selected_stack_are_not_advisory(self):
        original=copy.deepcopy(self.data)
        for field,value in [('legacy_labs',40),('repository',13.0)]:
            self.data=copy.deepcopy(original);self.data['allocation'][field]=value;self.invalid('47/40/13')
        for field,value in [('stack','undecided'),('player_platform','Linux'),('distribution','unknown')]:
            self.data=copy.deepcopy(original);self.data['direction'][field]=value;self.invalid('selected direction')

    def test_product_engine_must_agree_with_direction(self):
        (self.root/'north-star/capabilities.json').write_text('{"engine_selection":"undecided"}')
        self.invalid('engine selection conflicts')

    def test_renaming_incomplete_to_operational_is_rejected(self):
        self.lab('economy-simulation')['status']='operational';self.invalid('invalid local path')

    def test_operational_means_method_controls_consumer_and_results(self):
        original=copy.deepcopy(self.data)
        for field,message in [('instrument','invalid local path'),('controls','invalid controls'),
                              ('consumer_paths','invalid consumer_paths'),('evidence','invalid evidence')]:
            self.data=copy.deepcopy(original);self.lab().pop(field);self.invalid(message)

    def test_incomplete_cannot_claim_an_instrument_or_execution(self):
        self.lab('economy-simulation')['instrument']='labs/rpg-systems/run.py'
        self.invalid('incomplete destination cannot claim')

    def test_readme_or_empty_json_is_not_execution(self):
        row=self.lab();path=self.root/'evidence/note.md';path.write_text('Claim only.\n');self.bind(row,'evidence/note.md')
        self.invalid('nonempty JSON evidence')
        path=self.root/'evidence/empty.json';path.write_text('{}');self.bind(row,'evidence/empty.json')
        self.invalid('empty or non-object')

    def test_evidence_and_required_source_bytes_cannot_disappear(self):
        (self.root/'evidence/result.json').write_text('{"changed":true}');self.invalid('evidence hash mismatch')
        (self.root/'source/runtime.rb').unlink();self.invalid('missing local target')

    def test_consumption_requires_real_destination_or_justified_rejection(self):
        row=self.data['consumption'][0];row['status']='INTEGRATED';self.bind(row)
        self.invalid('invalid consumer_paths')
        row['consumer_paths']=['north-star/domain/Encounter.cs'];self.assertEqual(contract.check(self.root,self.data)['consumption']['INTEGRATED'],1)
        row['status']='REJECTED';row.pop('evidence');row.pop('evidence_sha256');self.invalid('invalid evidence')

    def test_unrelated_result_cannot_claim_destination_integration(self):
        row=self.data['consumption'][0];row.update(status='INTEGRATED',consumer_paths=['north-star/domain/Encounter.cs'])
        path=self.root/'evidence/unrelated.json';path.write_text('{"checks":{"passed":1,"failed":0}}')
        self.bind(row,'evidence/unrelated.json');self.invalid('integration requires successful destination execution')

    def test_unresolved_cannot_be_counted_consumed_or_lose_next_action(self):
        row=self.data['consumption'][0];row['consumed']=True;self.invalid('cannot be called consumed')
        row.pop('consumed');row.pop('next_action');self.invalid('missing next_action')

    def test_documentation_cannot_stand_in_for_destination_code(self):
        document=self.root/'north-star/README.md';document.write_text('Not executable.')
        self.lab()['consumer_paths']=['north-star/README.md'];self.invalid('actual consumer code')

    def test_removed_or_escaping_sources_and_linked_instruments_fail(self):
        original=copy.deepcopy(self.data)
        self.lab()['source_paths']=['../outside.rb'];self.invalid('noncanonical')
        self.data=copy.deepcopy(original);instrument=self.root/'labs/rpg-systems/run.py';instrument.unlink();instrument.symlink_to(self.root/'source/runtime.rb')
        self.invalid('linked path')

    def runtime(self,key,run):
        path=self.root/'evidence/runtime.json';path.write_text(json.dumps(run))
        self.data['direction'][key]='executed'
        self.data['direction']['execution_evidence']=[{'runtime':'unity' if key=='unity_execution' else 'windows',
                                                      'path':'evidence/runtime.json',
                                                      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}]

    def test_unity_scaffold_or_dotnet_build_is_not_editor_execution(self):
        self.data['direction']['unity_execution']='executed';self.invalid('needs actual runtime evidence')
        self.runtime('unity_execution',{'runtime':'.NET','executed':True,'checks':{'passed':4,'failed':0}})
        self.invalid('unexecuted Unity scaffolding')

    def test_cross_compile_or_boolean_check_count_is_not_windows_execution(self):
        self.runtime('windows_execution',{'platform':'Linux','executed':True,'artifact_sha256':'a'*64,'checks':{'passed':3,'failed':0}})
        self.invalid('cross-compilation is not Windows execution')
        self.runtime('windows_execution',{'platform':'Windows','executed':True,'artifact_sha256':'a'*64,'checks':{'passed':True,'failed':0}})
        self.invalid('cross-compilation is not Windows execution')

    def test_real_runtime_record_contract_is_distinct_from_direction(self):
        self.runtime('unity_execution',{'runtime':'Unity Editor','editor_version':'fixture-version','executed':True,'checks':{'passed':1,'failed':0}})
        self.assertEqual(contract.check(self.root,self.data)['operational'],2)

    def test_cli_rejects_malformed_authority_without_traceback(self):
        path=self.root/'labs/origins.json';path.write_text('[]')
        result=subprocess.run([sys.executable,str(Path(contract.__file__)),'--root',str(self.root)],capture_output=True,text=True)
        self.assertEqual(result.returncode,1);self.assertIn('schema_version 2',result.stderr);self.assertNotIn('Traceback',result.stderr)


if __name__=='__main__':unittest.main()
