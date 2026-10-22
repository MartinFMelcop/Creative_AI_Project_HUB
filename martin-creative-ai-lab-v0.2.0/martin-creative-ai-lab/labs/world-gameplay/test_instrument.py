import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('world_instrument', Path(__file__).with_name('run.py'))
lab = importlib.util.module_from_spec(spec); spec.loader.exec_module(lab)
CLASSES = 'ClassKey\nA\nB\n'
BACKGROUNDS = 'AntecedenteID,AntecedenteKey\n1,ONE\n2,TWO\n'
RELATIONS = 'ClassKey,AntecedenteID,Allowed\nA,1,1\nB,2,1\n'
SKILLS = 'SkillID,ClassKey,NivelAprendizado,ClassVariant\na_skill,A,1,\nb_skill,B,2,FEMALE\n'
ACT1 = '''SLOTS = 4
next if allowed_class && class_key && class_key != allowed_class
def self.skill_ids; @cache ||= _load; @cache[0]; end
eq_hash[i] = nil unless allowed.include?(sid)
'''
DIST = 'SLOTS = 4\ndef self.skill_ids; @cache ||= _load; @cache[0]; end\n'


def data(): return lab.catalog(CLASSES, BACKGROUNDS, RELATIONS, SKILLS)


class InstrumentTests(unittest.TestCase):
    def test_valid_catalog_exhaustive_reference(self):
        d = data()
        self.assertEqual(sum(r['allowed'] for r in d['class_background']), 2)
        self.assertEqual(sum(r['allowed'] for r in d['class_skill']), 2)
        self.assertEqual((len(d['class_background']), len(d['class_skill'])), (4, 4))

    def test_missing_duplicate_headers_and_width(self):
        for text in ['bad\nA\n', 'ClassKey,ClassKey\nA,A\n', 'ClassKey\nA,extra\n', '']:
            with self.assertRaises(ValueError): lab.catalog(text, BACKGROUNDS, RELATIONS, SKILLS)

    def test_duplicate_source_ids_rejected(self):
        for c, b, r, s in [(CLASSES + 'A\n', BACKGROUNDS, RELATIONS, SKILLS),
                            (CLASSES, BACKGROUNDS + '1,THREE\n', RELATIONS, SKILLS),
                            (CLASSES, BACKGROUNDS + '3,ONE\n', RELATIONS, SKILLS),
                            (CLASSES, BACKGROUNDS, RELATIONS, SKILLS + 'a_skill,A,1,\n')]:
            with self.assertRaises(ValueError): lab.catalog(c, b, r, s)

    def test_foreign_keys_relations_enum_and_duplicates(self):
        for r in [RELATIONS.replace('A,1,1', 'UNKNOWN,1,1'), RELATIONS.replace('A,1,1', 'A,9,1'),
                  RELATIONS.replace('A,1,1', 'A,1,true'), RELATIONS + 'A,1,1\n']:
            with self.assertRaises(ValueError): lab.catalog(CLASSES, BACKGROUNDS, r, SKILLS)
        with self.assertRaises(ValueError): lab.catalog(CLASSES, BACKGROUNDS, RELATIONS, SKILLS.replace('a_skill,A', 'a_skill,UNKNOWN'))

    def test_invalid_level_and_identifier(self):
        for value in ['0', '-1', '1.5', 'true', '4097', '01']:
            with self.assertRaises(ValueError): lab.positive(value)
        for value in ['', 'with space', 'bad:id', 'a' * 65]:
            with self.assertRaises(ValueError): lab.identifier(value)

    def test_variant_metadata_not_invented_restriction(self):
        self.assertEqual(data()['skills'], lab.catalog(CLASSES, BACKGROUNDS, RELATIONS, SKILLS.replace('FEMALE', 'MALE'))['skills'])

    def test_helper_variant_models_preserve_negative_and_prior_choice(self):
        result = lab.helper_assay(ACT1, DIST, '', data())
        self.assertTrue(result['bindings']['act1']['class_filter'])
        self.assertFalse(result['bindings']['distributed']['class_filter'])
        self.assertEqual(result['stale_cache_model']['incompatible_retained'], ['a_skill'])
        self.assertEqual(result['silent_erasure_model']['after_legacy_cleanup_model'], [None] * 4)
        self.assertEqual(result['silent_erasure_model']['after_transactional_rejection'], ['a_skill', None, None, None])
        with self.assertRaises(ValueError): lab.helper_assay(ACT1.replace('SLOTS = 4', 'SLOTS = 5'), DIST, '', data())

    def test_protocol_includes_independent_level_boundaries(self):
        protocol, expected = lab.study_protocol(data())
        self.assertEqual(len(expected), 11)  # 4 pairs +4 ownership +3 level controls
        self.assertEqual(len(protocol['cases']), len(expected))
        self.assertTrue(all(len(row['slots']) == 4 for row in protocol['cases']))
        self.assertEqual([r['level'] for r in protocol['cases'] if r['id'].startswith('level_')], [1, 1, 2])
        result = dict(schema_version=1, kind='loadout_compatibility_results', rows=expected)
        lab.validate_study(result, expected)
        altered = copy.deepcopy(result); altered['rows'][0]['accepted'] = 1
        with self.assertRaises(ValueError): lab.validate_study(altered, expected)
        altered = copy.deepcopy(result); altered['rows'][0]['accepted'] = not altered['rows'][0]['accepted']
        with self.assertRaises(ValueError): lab.validate_study(altered, expected)
        with self.assertRaises(ValueError): lab.validate_study(dict(result, rows=expected[:-1]), expected)

    def test_native_report_cannot_fabricate_boolean_counts_or_labels(self):
        valid = dict(schema_version=1, kind='north_star_loadout_native', passed=1, failed=0, controls=['real fixture'])
        lab.validate_native(valid)
        for key, value in [('schema_version', True), ('passed', True), ('passed', 0), ('failed', False), ('failed', 1), ('controls', []), ('controls', ['']), ('kind', 'other')]:
            with self.assertRaises(ValueError): lab.validate_native(dict(valid, **{key: value}))

    def test_destination_protocol_rejects_false_journeys(self):
        row = dict(active=False, complete=True, won=True, stage=1, beat=6, position=4, health=7,
                   resolve=4, attempts=2, consumed_rigs=2, transactions=4, xp=25, level=3,
                   unspent=2, vitality=2, focus=0, inventory={}, slots=['brace', 'dash', None, None],
                   class_id='anchor', background_id='trailborn', rig='Trail')
        earned = dict(row, complete=False, xp=10, level=2)
        empty = dict(earned, slots=[None] * 4, consumed_rigs=0)
        failed = dict(empty, won=False, health=0)
        demo = dict(schema_version=1, kind='north_star_loadout_journeys', earned_level2=earned,
                    anchor_trail_complete=row, lure_plate_complete=dict(row, class_id='lure', rig='Plate'),
                    empty_survey_success=empty, empty_crossing_failure=failed,
                    invalid_proposal_rejected=True, invalid_proposal_unchanged=True)
        lab.validate_demo(demo)
        for key, field, value in [('anchor_trail_complete', 'complete', False),
                                  ('lure_plate_complete', 'rig', 'Trail'),
                                  ('earned_level2', 'level', True),
                                  ('empty_survey_success', 'consumed_rigs', 1),
                                  ('empty_crossing_failure', 'health', 1),
                                  ('anchor_trail_complete', 'slots', ['brace'])]:
            altered = copy.deepcopy(demo); altered[key][field] = value
            with self.assertRaises(ValueError): lab.validate_demo(altered)
        with self.assertRaises(ValueError): lab.validate_demo(dict(demo, invalid_proposal_unchanged=1))

    def test_output_cannot_overwrite_protected_or_other_maintained_files(self):
        for name in ['brains/ENGINEERING_BRAIN.md', 'docs/STATE.md', 'north-star/csharp/Domain/Progression.cs', 'references/snapshot.csv']:
            with self.assertRaises(ValueError): lab.run(lab.ROOT / name, dotnet='nonexistent-dotnet')

    def test_actual_preserved_catalog_counts_and_compatibility(self):
        texts = {key: (lab.SOURCE / name).read_text(encoding='utf-8-sig') for key, name in lab.NAMES.items()}
        d = lab.catalog(*(texts[key] for key in ['classes', 'backgrounds', 'relations', 'skills']))
        self.assertEqual((len(d['classes']), len(d['backgrounds']), len(d['allowed_pairs']), len(d['skills'])), (10, 11, 52, 166))
        self.assertEqual((len(d['class_background']), len(d['class_skill'])), (110, 1660))
        protocol, expected = lab.study_protocol(d); self.assertEqual(len(expected), 2090)
        helpers = lab.helper_assay(texts['act1_skills'], texts['dist_skills'], texts['act1_creation'], d)
        self.assertTrue(helpers['bindings']['creation']['stray_regex_fragment'])
        self.assertTrue(helpers['bindings']['creation']['missing_relation_all_background_fallback'])


if __name__ == '__main__': unittest.main()
