import importlib.util
import copy
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('economy_instrument', Path(__file__).with_name('run.py'))
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
STATION = 'WorkstationID,Tipo,Acesso_Tipo,DC_Padrao,StatusImplementacao\nWKS_A,Forge,Inner,10,Implementar\n'
RECIPE = 'RecipeID,Output_Qtd,Ingredientes,WorkstationID_Referencia,Workstation_Tipo,Unlock_Tipo,StatusImplementacao\nRCP_A,1,MAT_IRON*2|MAT_COAL*1,WKS_A,Forge,Quest,Implementar\n'


class InstrumentTests(unittest.TestCase):
    def test_valid_fixture(self):
        self.assertTrue(lab.assay(STATION, RECIPE)['typed_direct_adapter']['accepted'])

    def test_width_rival_misses_semantic_shift(self):
        shifted = STATION.replace('Forge,Inner,10,Implementar', 'Forge,description,15|20,CAP_01')
        result = lab.assay(shifted, RECIPE)
        self.assertTrue(result['width_only_rival']['accepted'])
        self.assertFalse(result['typed_direct_adapter']['accepted'])
        self.assertEqual(len(result['typed_direct_adapter']['errors']), 3)
        self.assertEqual(result['recipes_referencing_invalid_stations'], ['RCP_A'])

    def test_missing_and_duplicate_headers_rejected(self):
        for text in ['x\n1\n', 'WorkstationID,WorkstationID\na,a\n', '']:
            with self.assertRaises(ValueError): lab.assay(text, RECIPE)

    def test_width_mismatch_rejected(self):
        with self.assertRaises(ValueError): lab.assay(STATION.replace('WKS_A,', 'WKS_A,extra,'), RECIPE)

    def test_station_reference_and_type(self):
        for replacement, reason in [('WKS_B,Forge', 'missing_station'), ('WKS_A,Kitchen', 'station_type_mismatch')]:
            result = lab.assay(STATION, RECIPE.replace('WKS_A,Forge', replacement))
            self.assertIn(reason, [row['reason'] for row in result['typed_direct_adapter']['errors']])

    def test_quantities_and_ingredient_collision(self):
        for invalid in ['MAT_IRON*0', 'MAT_IRON*-1', 'MAT_IRON*2|MAT_IRON*3', 'MAT_IRON', 'MAT_IRON*1.5', 'MAT_IRON*1000001', 'MAT_IRON*9999999999']:
            with self.assertRaises(ValueError): lab.ingredients(invalid)
        self.assertEqual(lab.ingredients('MAT_IRON*2|MAT_COAL*1'), {'MAT_IRON': 2, 'MAT_COAL': 1})

    def test_duplicate_ids_rejected(self):
        result = lab.assay(STATION + STATION.splitlines()[1] + '\n', RECIPE + RECIPE.splitlines()[1] + '\n')
        self.assertEqual(sum(row['reason'] == 'missing_or_duplicate_id' for row in result['typed_direct_adapter']['errors']), 2)

    def test_recipe_enum_and_output_quantity(self):
        for text in [RECIPE.replace('RCP_A,1,', 'RCP_A,0,'), RECIPE.replace(',Quest,', ',Unknown,'), RECIPE.replace(',Implementar', ',DONE')]:
            self.assertFalse(lab.assay(STATION, text)['typed_direct_adapter']['accepted'])

    def test_preserved_negative_is_semantic_not_width(self):
        result = lab.assay(*( (lab.SOURCE / name).read_text(encoding='utf-8-sig') for name in ['CRAFTING_STATION.csv', 'CRAFTING_RECIPE.csv']))
        self.assertEqual((result['station_rows'], result['recipe_rows']), (15, 21))
        self.assertTrue(result['width_only_rival']['accepted'])
        self.assertFalse(result['typed_direct_adapter']['accepted'])
        self.assertIn('mostra DC/risco.', [row['value'] for row in result['typed_direct_adapter']['errors']])

    def test_runtime_protocol_rejects_false_success(self):
        complete = dict(active=False, complete=True, won=True, attempts=2, consumed_rigs=2, transactions=4, health=1, xp=25, inventory={})
        failure = dict(active=False, complete=False, won=False, attempts=1, consumed_rigs=0, transactions=0, health=0, xp=0, inventory={})
        rig_failure = dict(failure, consumed_rigs=1, inventory={'trail_rig': 0})
        retry = dict(rig_failure, active=True, attempts=2)
        demo = dict(schema_version=1, kind='north_star_crafting_journeys', trail_complete=complete, plate_complete=complete,
                    mixed_complete=dict(complete, consumed_rigs=1, inventory={'fiber': 2, 'binder': 1}),
                    unprepared_survey_success=dict(failure, won=True, health=2), unprepared_walking_failure=failure, failed_trail_no_refund=rig_failure, unprepared_retry=retry, missing_rig_rejected=True)
        native = dict(schema_version=1, kind='north_star_crafting_native', passed=1, failed=0, controls=['fixture'])
        lab.validate_destination(native, demo)
        for key, value in [('passed', True), ('passed', 0), ('failed', False), ('failed', 1), ('schema_version', True), ('kind', 'other'), ('controls', []), ('controls', [''])]:
            with self.assertRaises(ValueError): lab.validate_destination(dict(native, **{key: value}), demo)
        for key, field, value in [('trail_complete', 'complete', False), ('plate_complete', 'consumed_rigs', 1),
                                  ('failed_trail_no_refund', 'inventory', {'trail_rig': 1}),
                                  ('unprepared_walking_failure', 'won', True), ('unprepared_retry', 'active', False)]:
            altered = copy.deepcopy(demo); altered[key][field] = value
            with self.assertRaises(ValueError): lab.validate_destination(native, altered)
        with self.assertRaises(ValueError): lab.validate_destination({}, {})


if __name__ == '__main__': unittest.main()
