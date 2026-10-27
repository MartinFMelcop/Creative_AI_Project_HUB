#!/usr/bin/env python3
"""Inspect selected passive prose/rule contracts without executing preserved Ruby."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source'
NAMES=['RM_ACT1/DATA/CORE/ACT1_PASSIVES_CANON.csv','RM_DIST/RMXP_BASE/Data/RM_CSV/ACT1_PASSIVES_CANON.csv','RM_CORE/DATA/CORE/PASSIVE_EQUIP_RULES.csv','RM_DIST/RMXP_BASE/Data/RM_CSV/PASSIVE_EQUIP_RULES.csv','RM_ACT1/DATA/DEV/RGSS/RM_UI_PASSIVE_EQUIP_RUNTIME.rb','RM_DIST/RMXP_BASE/ScriptsCustom/RM_UI_PASSIVE_EQUIP_RUNTIME.rb']
def identities():return {str((SOURCE/n).relative_to(ROOT)):hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
def inspect():
    before=identities();tables=[(SOURCE/n).read_bytes() for n in NAMES]
    if tables[0]!=tables[1] or tables[2]!=tables[3] or tables[4]==tables[5]:raise ValueError('Source variant observations changed')
    reader=csv.DictReader((SOURCE/NAMES[0]).open());rows=list(reader)
    if len(rows)!=77 or len(reader.fieldnames)!=28 or any(None in r or any(v is None for v in r.values()) for r in rows):raise ValueError('Actual passive table shape changed')
    selected={r['PassiveID']:r for r in rows if r['PassiveID'] in {'WARRIOR_PAS_005','WARRIOR_PAS_007','ROGUE_MALE_PAS_006','KNIGHT_PAS_001'}}
    exact={'WARRIOR_PAS_005':'Reduz 10% do dano físico com armadura pesada equipada.','WARRIOR_PAS_007':'Sobrevive a um golpe fatal com 1 HP, uma vez por combate.','ROGUE_MALE_PAS_006':'20% de chance de sobreviver a golpe fatal com 1 de HP. (1x por combate)','KNIGHT_PAS_001':'Reduz 10% do dano recebido enquanto não estiver sob efeito de controle.'}
    if set(selected)!=set(exact) or any(selected[k]['Efeito']!=v for k,v in exact.items()):raise ValueError('Selected source prose differs')
    rules=list(csv.DictReader((SOURCE/NAMES[2]).open()))
    if len(rules)!=1 or rules[0]['MaxEquipped']!='1' or rules[0]['SwapContext']!='OUT_OF_COMBAT_ONLY' or rules[0]['SlotGroup']!='PASSIVE_MAIN':raise ValueError('Selected rule differs')
    dev,dist=tables[4].decode(),tables[5].decode()
    if any('$game_system.rm_passive_equipped_id = pid' not in t for t in [dev,dist]) or 'def self.equip_rule_for(pid)' not in dev or 'def self.equip_rule_for(pid)' in dist:raise ValueError('Source UI observations changed')
    if before!=identities():raise ValueError('Source changed during inspection')
    return {'schema_version':1,'kind':'selected_passive_source_inspection','source_sha256':before,'source_stable':True,'passive_rows_per_copy':77,'passive_columns':28,'tables_identical':True,'ui_helpers_identical':False,'selected_rows':selected,'rule':rules[0],'ui_interpretation':'Both helpers store one scalar selected ID. DEV displays the equip-rule string; DIST lacks that parser. Neither inspected assignment branch checks combat/cutscene/class/level or applies/removes Efeito. This is static source interpretation, not observed RGSS gameplay.','adapted':'One explicit preparation slot and selected heavy10%/fatal1HP-once behavior in actual C# consumer.','preserved_alternatives':'Rogue20% stochastic rescue and Knight10% while uncontrolled remain distinct unimplemented policies; do not normalize them into chosen effects.','destination_policy':['Study preset availability does not grant source RequiredLevel/class/gender eligibility.','Only typed physical DIRECT contact receives Lining; DOT exclusion is a destination category decision, not a source assertion that bleed is nonphysical.','Guard before passive; integer remaining damage rounds away from zero.','Fatal eligible direct hit once; no DOT interception, no HP0 resurrection; later DOT remains payable.','Only explicit new practice begins a fresh encounter; no active swap/rearm.'],'limits':'Prose/table/source-helper inspection plus separately executed C# adaptation, not Ruby/RGSS/RMXP, full effect/armor/learning catalogs, source balance, human validation or canon.'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.write_text(json.dumps(inspect(),ensure_ascii=False,indent=2)+'\n');print('PASS: selected2effect contracts,1slot rule;77rows/2differentUIhelpers inspected, no Ruby execution')
