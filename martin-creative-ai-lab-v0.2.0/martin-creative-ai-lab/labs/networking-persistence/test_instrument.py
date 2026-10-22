import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('recovery_instrument', Path(__file__).with_name('run.py'))
lab = importlib.util.module_from_spec(spec); spec.loader.exec_module(lab)


def sources():
    return {key: (lab.ROOT / name).read_text() for key, name in lab.SOURCE_NAMES.items()}


def state(**changes):
    row = dict(active=False, complete=False, won=False, stage=0, beat=0, position=0,
               health=0, resolve=0, attempts=0, consumed_rigs=0, transactions=0,
               level=1, xp=0, unspent=0, vitality=0, focus=0, class_id='anchor',
               background_id='workshop', rig='Unprepared', slots=['brace', None, None, None],
               inventory={'fiber': 4, 'binder': 2})
    row.update(changes); return row


def demo():
    mid = state(active=True, beat=1, position=1, health=6, resolve=10, attempts=1,
                consumed_rigs=1, transactions=3, rig='Trail', inventory={'fiber': 0, 'binder': 0, 'trail_rig': 1})
    completed = state(complete=True, won=True, stage=1, beat=6, position=4, health=11,
                      resolve=5, attempts=2, consumed_rigs=2, transactions=4, rig='Trail',
                      level=3, xp=25, unspent=2, focus=2, background_id='trailborn',
                      slots=['brace', 'dash', None, None], inventory={'fiber': 0, 'binder': 0, 'trail_rig': 0})
    boundaries = []
    for point in ['before_write', 'before_replace', 'after_replace']:
        committed = point == 'after_replace'; revision = int(committed)
        recovered = state(transactions=revision, inventory={'fiber': 2, 'binder': 1, 'trail_rig': 1}) if committed else state()
        boundaries.append(dict(point=point, child_exit=79, expected_revision=revision,
                               recovered_revision=revision, expected=copy.deepcopy(recovered), recovered=recovered,
                               state_preserved=True, retry_request_id='attempt', retry_command={'op': 'craft', 'recipe': 'trail_rig'},
                               retry_duplicate=committed, retry_accepted=True))
    return dict(schema_version=1, kind='north_star_recovery_journeys',
                mid_encounter_before_restart=mid, mid_encounter_after_restart=copy.deepcopy(mid),
                completed=completed, completed_revision=16, replay_after_restart={'duplicate': True, 'unchanged': True, 'request_id': 'craft_1', 'command': {'op': 'craft', 'recipe': 'trail_rig'}},
                conflict_rejected=True, invalid_file_rejected=True, existing_new_rejected=True,
                second_writer_rejected=True, owner_death_recovered=True, no_refund_retry_rejected=True,
                failure_boundaries=boundaries, no_refund=state(beat=3, attempts=1, consumed_rigs=1, transactions=2, rig='Trail', inventory={'fiber': 2, 'binder': 1, 'trail_rig': 0}))


class RecoveryInstrumentTests(unittest.TestCase):
    def test_actual_inspected_binding_scope(self):
        result = lab.source_assay(sources())
        self.assertTrue(all(result['bindings'].values()))
        self.assertFalse(result['material_limits']['cinder_store_explicit_file_flush_present'])
        self.assertIn('Static', result['scope'])

    def test_content_replay_conflict_binding_cannot_disappear(self):
        texts = sources(); texts['rooms_actions'] = texts['rooms_actions'].replace('if(old.command!==encoded)throw new Error', 'if(false)throw new Error')
        with self.assertRaises(ValueError): lab.source_assay(texts)

    def test_commit_before_receipt_binding_cannot_disappear(self):
        texts = sources(); texts['rooms_actions'] = texts['rooms_actions'].replace("this.db.exec('COMMIT');return {action,eventId:event.id", "return {action,eventId:event.id")
        with self.assertRaises(ValueError): lab.source_assay(texts)

    def test_replay_validation_binding_cannot_disappear(self):
        texts = sources(); texts['cinder_journal'] = texts['cinder_journal'].replace('if(!accepted)throw new InvalidDataException', 'if(false)throw new InvalidDataException')
        with self.assertRaises(ValueError): lab.source_assay(texts)

    def test_atomic_replace_and_flush_bindings_cannot_disappear(self):
        for source, old in [('cinder_journal', 'File.Move(temp,full,true);'), ('rooms_backup', 'fs.fsyncSync(fd)')]:
            texts = sources(); texts[source] = texts[source].replace(old, '')
            with self.assertRaises(ValueError): lab.source_assay(texts)

    def test_native_false_success_refused(self):
        native = dict(schema_version=1, kind='north_star_recovery_native', passed=1, failed=0, controls=['actual fixture'])
        lab.validate_native(native)
        for key, value in [('schema_version', True), ('passed', True), ('passed', 0), ('failed', False), ('failed', 1), ('controls', []), ('controls', ['']), ('kind', 'unrelated')]:
            with self.assertRaises(ValueError): lab.validate_native(dict(native, **{key: value}))

    def test_whole_gameplay_observations_reject_missing_or_false_fields(self):
        valid = dict(active=True, complete=False, won=False, stage=0, beat=1, position=0,
                     health=10, resolve=8, attempts=1, consumed_rigs=1, transactions=2,
                     level=1, xp=0, unspent=0, vitality=0, focus=0, class_id='anchor',
                     background_id='workshop', rig='Trail', slots=['brace', None, None, None],
                     inventory={'fiber': 2, 'binder': 1, 'trail_rig': 0})
        lab.validate_state(valid)
        for field, value in [('xp', True), ('health', -1), ('active', 1), ('slots', ['brace']), ('rig', 'Unknown'), ('inventory', {'fiber': True})]:
            with self.assertRaises(ValueError): lab.validate_state(dict(valid, **{field: value}))
        missing = dict(valid); del missing['transactions']
        with self.assertRaises(ValueError): lab.validate_state(missing)

    def test_actual_destination_requires_complete_prefix_and_receipt_controls(self):
        valid = demo(); lab.validate_demo(valid)
        for field, value in [('schema_version', True), ('kind', 'unrelated'), ('completed_revision', True),
                             ('second_writer_rejected', False), ('owner_death_recovered', False), ('no_refund_retry_rejected', 1)]:
            with self.assertRaises(ValueError): lab.validate_demo(dict(valid, **{field: value}))
        altered = copy.deepcopy(valid); altered['mid_encounter_after_restart']['resolve'] -= 1
        with self.assertRaises(ValueError): lab.validate_demo(altered)
        altered = copy.deepcopy(valid); altered['completed']['complete'] = False
        with self.assertRaises(ValueError): lab.validate_demo(altered)
        altered = copy.deepcopy(valid); altered['no_refund']['inventory']['trail_rig'] = 1
        with self.assertRaises(ValueError): lab.validate_demo(altered)

    def test_crash_boundaries_cannot_fake_exits_prefixes_or_receipts(self):
        valid = demo()
        for index, field, value in [(0, 'child_exit', True), (0, 'recovered_revision', 1),
                                    (1, 'point', 'before_write'), (2, 'retry_duplicate', False),
                                    (2, 'retry_accepted', 1), (2, 'state_preserved', False)]:
            altered = copy.deepcopy(valid); altered['failure_boundaries'][index][field] = value
            with self.assertRaises(ValueError): lab.validate_demo(altered)
        altered = copy.deepcopy(valid); altered['failure_boundaries'][2]['recovered']['inventory']['fiber'] = 4
        with self.assertRaises(ValueError): lab.validate_demo(altered)
        altered = copy.deepcopy(valid); altered['failure_boundaries'] = altered['failure_boundaries'][:2]
        with self.assertRaises(ValueError): lab.validate_demo(altered)

    def test_output_guard_protects_all_maintained_sources(self):
        for name in ['brains/ENGINEERING_BRAIN.md', 'docs/STATE.md', 'references/preserved.csv', 'north-star/csharp/Domain/Loadout.cs']:
            with self.assertRaises(ValueError): lab.run(lab.ROOT / name, dotnet='nonexistent-dotnet')


if __name__ == '__main__': unittest.main()
