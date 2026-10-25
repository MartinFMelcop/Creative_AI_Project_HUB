#!/usr/bin/env python3
"""Inspect exact historical item/tool contracts and execute the SAME identity cases in C#.

Protected CSVs are read as source data. Quarantine is explicit; it does not repair,
activate or import source prices, quests, skills, fiction or consumable effects.
"""
from __future__ import annotations
import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = 'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/'
ITEMS = SOURCE+'RM_CORE/DATA/CORE/ITENS_MASTER.csv'
RECIPES = SOURCE+'RM_CORE/DATA/CORE/CRAFTING_RECIPE.csv'
CLASSES = SOURCE+'RM_CORE/DATA/CORE/ITEM_CLASS_RULES.csv'
ALIASES = SOURCE+'RM_CORE/DATA/CORE/ALIASES_ITEMS.csv'
QA = SOURCE+'RM_QA/DATA/QA/RPT_ITEMID_DUP.csv'
UNLOCKS = SOURCE+'RM_CORE/DATA/CORE/PERICIA_UNLOCKS.csv'
DIST_UNLOCKS = SOURCE+'RM_DIST/RMXP_BASE/Data/RM_CSV/PERICIA_UNLOCKS.csv'
QUESTS = SOURCE+'RM_ACT1/DATA/DEV/SIDEQUESTS_EM_CONSTRUCAO.csv'
DIST_QUESTS = SOURCE+'RM_DIST/RMXP_BASE/Data/RM_CSV/SIDEQUESTS_EM_CONSTRUCAO.csv'
SOURCES = (ITEMS, RECIPES, CLASSES, ALIASES, QA, UNLOCKS, DIST_UNLOCKS, QUESTS, DIST_QUESTS)
ITEM_HEADER = 'ItemID,Nome,Tipo,Categoria,Slot,Subtipo,Raridade,StackMax,DescricaoCurta,Efeito_Texto,Duracao_Turnos,Tags,Fonte,Canon,NotaCanon,Empunhadura,Pode_MaoSecundaria,Score,Letalidade_Base,Escala_STR,Escala_DEX,Escala_AGI,Escala_INT,Valor,StatusPreco,Moeda,PDEF,MDEF,EVA,Dano_Tipos,NotasBalance,Consumivel_Categoria,Potencia,Alvo,HP_Recupera,SP_Recupera,Remove_Status,Aplica_Status,Dano_Tipo,Dano_Valor,Notas,Origem_Bloco,Origem_ColStart,Nome_EN,TipoRegistro,Valor_Base_B,Validacao_Obrigatorios,FAE_Tags'.split(',')
RECIPE_HEADER = 'RecipeID,NomeReceita,Output_ItemID,Output_Nome,Output_Qtd,CraftingID,Workstation_Tipo,WorkstationID_Referencia,Ingredientes,Ferramentas_Requeridas,Pericia_Usada,DC_Padrao,Tempo_Seg,XP_Crafting,Unlock_Tipo,Unlock_Refs,Ato,StatusImplementacao,Notas_Dev,FAE_Tags'.split(',')
BAG = 'ITM_BOLSA_DE_FERRAMENTAS_COMUM'
ESSENCE = 'CON_ESSENCIA_ESPIRITUAL_COMUM'
QUARANTINE_IDS = {'LGT_TOCHA_PADRAO', 'LGT_LANTERNA_AVANCADA'}
AMBIGUOUS_RECIPES = {'RCP-CUL-002','RCP-OFI-004','RCP-TEX-002','RCP-GOL-001'}


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(text, headers=None):
    raw = list(csv.reader(io.StringIO(text)))
    require(bool(raw) and len(raw[0]) == len(set(raw[0])), 'Missing or duplicate source columns')
    if headers is not None: require(raw[0] == headers, 'Unexpected source header')
    require(all(len(row) == len(raw[0]) for row in raw[1:]), 'Ragged strict source table')
    return [dict(zip(raw[0], row)) for row in raw[1:]]


def item_catalog(text):
    raw = list(csv.reader(io.StringIO(text)))
    require(raw and raw[0] == ITEM_HEADER, 'Unexpected item source header')
    require(len(raw)-1 == 372, 'Item source record count changed; inspect before rebasing')
    known, valid, quarantine, identities = [], {}, [], set()
    for ordinal, row in enumerate(raw[1:], 1):
        require(row and re.fullmatch(r'[A-Za-z0-9_-]{1,64}',row[0]) is not None, 'Invalid literal source item ID')
        identifier = row[0]
        require(identifier not in identities, 'Duplicate literal item ID')
        identities.add(identifier)
        if len(row) != len(ITEM_HEADER):
            quarantine.append({'record_ordinal':ordinal,'item_id':identifier,'fields':len(row),'expected_fields':len(ITEM_HEADER),'reason':'Ragged record: only the literal first-field ID is observed; no shifted columns are interpreted or repaired.'})
            continue
        known.append(identifier);valid[identifier]=dict(zip(ITEM_HEADER,row))
    require(len(known) == 370 and len(quarantine) == 2 and {x['item_id'] for x in quarantine} == QUARANTINE_IDS
            and all(x['fields'] == 47 for x in quarantine), 'Quarantine changed; inspect rather than silently accepting or dropping source rows')
    return known, valid, quarantine


def inspect_sources(root=ROOT):
    texts = {name:(root/name).read_text(encoding='utf-8-sig') for name in SOURCES}
    known, valid, quarantine = item_catalog(texts[ITEMS])
    recipes = rows(texts[RECIPES],RECIPE_HEADER)
    require(len(recipes) == 21 and len({r['RecipeID'] for r in recipes}) == 21, 'Recipe count/identity changed')
    classes = {r['RuleID']:r for r in rows(texts[CLASSES],['RuleID','Condicao','Classificacao','Exemplo_ItemID','Exemplo_Nome','Observacao'])}
    require(len(classes) == 12 and classes['R7']['Exemplo_ItemID'] == BAG and 'não consumida' in classes['R7']['Condicao'], 'Required nonconsumed tool contract changed')
    require(classes['R8']['Exemplo_ItemID'] == ESSENCE and 'uso duplo' in classes['R8']['Condicao'].lower()
            and 'permitir uso em Ingredientes' in classes['R8']['Classificacao'], 'Dual-use ingredient identity contract changed')
    require(not rows(texts[ALIASES],['alias','canonico','Tipo','motivo','ocorrencias_alias','onde_aparece_alias']), 'Alias source now has mappings; inspect before retaining header-only policy')
    require(not rows(texts[QA],['ItemID','Ocorrencias','Detalhes']), 'Historical QA now has results; inspect before retaining header-only claim')
    refs=[];tools=[];ambiguous=[];deprecated=[];statuses={}
    for recipe in recipes:
        recipe_id=recipe['RecipeID'];statuses[recipe['StatusImplementacao']]=statuses.get(recipe['StatusImplementacao'],0)+1
        require(re.fullmatch(r'[1-9][0-9]*',recipe['Output_Qtd']) is not None, 'Invalid output quantity')
        refs.append({'id':recipe_id+'/output','item_id':recipe['Output_ItemID'],'expected':True})
        for index, token in enumerate(recipe['Ingredientes'].split('|')):
            parsed=re.fullmatch(r'([A-Za-z0-9_-]{1,64})\*([1-9][0-9]*)',token)
            require(parsed is not None and int(parsed.group(2)) <= 1000000, 'Invalid literal ingredient quantity/reference')
            refs.append({'id':recipe_id+'/input/'+str(index),'item_id':parsed.group(1),'expected':True})
        if recipe['Ferramentas_Requeridas']:
            for index, tool in enumerate(recipe['Ferramentas_Requeridas'].split('|')):
                require(re.fullmatch(r'[A-Za-z0-9_-]{1,64}',tool) is not None, 'Invalid literal tool ID')
                refs.append({'id':recipe_id+'/tool/'+str(index),'item_id':tool,'expected':True})
                tools.append({'recipe_id':recipe_id,'item_id':tool,'consumed':False})
        if ';' in recipe['Unlock_Refs']:
            ambiguous.append({'recipe_id':recipe_id,'raw_refs':recipe['Unlock_Refs'],'resolution':'UNRESOLVED AND/OR; not converted to a grant'})
        if 'SDQ-0001' in recipe['Unlock_Refs'].split(';'): deprecated.append(recipe_id)
    require(len(refs) == 81 and all(ref['item_id'] in valid for ref in refs), 'Unresolved actual item reference; inspect source rather than inventing replacements')
    require(tools == [{'recipe_id':'RCP-OFI-001','item_id':BAG,'consumed':False},{'recipe_id':'RCP-OFI-004','item_id':BAG,'consumed':False}], 'Actual required-tool references changed')
    require({r['recipe_id'] for r in ambiguous} == AMBIGUOUS_RECIPES, 'Ambiguous unlock reference set changed')
    require(set(deprecated) == {'RCP-ALQ-001','RCP-OFI-004'}, 'Deprecated quest reference set changed')
    require(valid[BAG]['StackMax'] == '1.0' and Decimal(valid[BAG]['StackMax']) == 1
            and valid[BAG]['StatusPreco'] == 'Backlog' and valid[BAG]['Valor'] == '', 'Observed tool metadata changed; blank price cannot become free')
    require(valid[ESSENCE]['Tipo'] == 'Consumível' and 'Faltando' in valid[ESSENCE]['Validacao_Obrigatorios'], 'Retained dual-use effect limitation changed')
    require(texts[UNLOCKS] == texts[DIST_UNLOCKS], 'CORE/DIST skill unlock source disagreement')
    unlocks=rows(texts[UNLOCKS],['UnlockID','PericiaID','PericiaNome','LevelReq','UnlockType','UnlockKey','DescricaoCurta','Tags','Notes'])
    require(len(unlocks) == 78, 'Skill unlock source count changed')
    skill_names={}
    for row in unlocks:
        require(row['PericiaID'] not in skill_names or skill_names[row['PericiaID']] == row['PericiaNome'], 'Source skill name conflict')
        skill_names[row['PericiaID']]=row['PericiaNome']
    missing_skill_ids=sorted({r['Pericia_Usada'] for r in recipes}-set(skill_names),key=int)
    require(missing_skill_ids == ['20','22','23','28'] and skill_names['11'] == 'Alquimia do Pântano'
            and skill_names['15'] == 'Ritos do Véu', 'Retained skill namespace disagreement changed')
    quest_variants=[]
    for name in (QUESTS,DIST_QUESTS):
        quests=rows(texts[name]);require(len(quests) == 45, 'Quest source count changed')
        selected={r['IdQuest']:r for r in quests if r['IdQuest'] in ('SDQ-0001','SDQ-0007')}
        require(set(selected) == {'SDQ-0001','SDQ-0007'} and '[DESCONSIDERAR]' in selected['SDQ-0001']['Descrição Resumida']
                and 'DESCONSIDERAR' in selected['SDQ-0001']['NotaCanon'], 'Deprecated quest must not become an implicit unlock grant')
        quest_variants.append({'path':name,'sdq_0001_status':'DESCONSIDERAR; unresolved rewrite, no automatic grant',
                               'sdq_0007_status':'Source quest declaration only; its return/sell outcome is not a destination unlock event'})
    negatives=[
        ('quarantined-torch','LGT_TOCHA_PADRAO'),('quarantined-lantern','LGT_LANTERNA_AVANCADA'),
        ('case-is-not-identity',BAG.lower()),('substring-is-not-identity','ITM_BOLSA_DE_FERRAMENTAS'),
        ('unknown-is-not-placeholder','UNKNOWN_ITEM_0001'),('unprovided-alias-is-not-identity','MAT_ESSENCIA_ESPIRITUAL')]
    for case,identifier in negatives:
        require(identifier not in valid, 'Predeclared negative became a source identity; inspect before rebasing')
        refs.append({'id':'negative/'+case,'item_id':identifier,'expected':False})
    catalog={'schema_version':1,'known_ids':known,'references':refs}
    assay={'item_records':372,'structurally_valid_identity_records':370,'quarantined_records':quarantine,
           'recipe_records':21,'actual_resolved_literal_references':81,'same_identity_cases':len(refs),'required_tools':tools,
           'recipe_implementation_statuses':statuses,'ambiguous_unlock_references':ambiguous,'deprecated_quest_recipe_references':deprecated,
           'skill_unlock_records':78,'core_dist_unlocks_identical':True,'recipe_skill_ids_missing_in_unlock_namespace':missing_skill_ids,
           'skill_namespace_example':{'recipe_alchemy_skill':'15','unlock_15_name':skill_names['15'],'unlock_alchemy_skill':'11','resolution':'UNRESOLVED namespaces; no numeric normalization'},
           'quest_variants':quest_variants,'quest_variants_byte_identical':texts[QUESTS] == texts[DIST_QUESTS],
           'header_only_alias_rows':0,'header_only_qa_rows':0,
           'tool_price':'Blank Backlog; not free or an implemented price',
           'dual_use_effect':'Consumable ingredient identity exists; required effect is explicitly missing',
           'normalized_scope':'Exact item identities only. No unlock grants, prices, effects, source fiction, inventory state or recipe activation are serialized.',
           'scope':'Source-bound CSV interpretation and quarantine, not historical game/Ruby/RMXP execution, full item semantics, author policy or human assessment.'}
    return assay,catalog


def compare_results(catalog,result):
    require(isinstance(result,dict) and set(result) == {'schema_version','references','passed','failed'} and result['schema_version'] == 1, 'Unexpected C# catalogue output fields/schema')
    expected=catalog['references'];actual=result['references']
    require(isinstance(actual,list) and len(actual) == len(expected), 'C# catalogue result count mismatch')
    for source,observed in zip(expected,actual):
        require(observed == {'id':source['id'],'item_id':source['item_id'],'actual':source['expected'],'expected':source['expected'],'passed':True}, 'False, reordered or misbound C# catalogue result')
    require(result['passed'] == len(expected) and result['failed'] == 0, 'C# catalogue totals disagree')


def input_hashes(root=ROOT):
    names=set(SOURCES)|{'north-star/csharp/global.json'}
    for folder in (root/'north-star/tooling-study/Rules',root/'north-star/tooling-study/Checks',root/'north-star/csharp/Domain',root/'labs/economy-simulation/tooling'):
        for p in folder.rglob('*'):
            if {'bin','obj','__pycache__'} & set(p.parts):continue
            if p.suffix in ('.cs','.csproj','.py','.json'):names.add(str(p.relative_to(root)))
    for name in names:
        p=root/name;require(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root), 'Invalid source/instrument input')
    return {name:sha(root/name) for name in sorted(names)}


def run(output,dotnet):
    output=output.resolve();require(not output.is_relative_to(ROOT), 'Keep execution outside maintained workspace');output.mkdir(parents=True,exist_ok=False)
    sdk=shutil.which(str(dotnet));require(sdk is not None,'Actual SDK unavailable')
    before=input_hashes();commands=[]
    def save(name,value):(output/name).write_text(json.dumps(value,indent=2)+'\n')
    def execute(command,cwd=ROOT/'north-star/csharp',timeout=180):
        r=subprocess.run([str(x) for x in command],cwd=cwd,capture_output=True,text=True,timeout=timeout,
                         env=dict(os.environ,DOTNET_PROCESSOR_COUNT='2',DOTNET_NOLOGO='1',DOTNET_CLI_TELEMETRY_OPTOUT='1'))
        commands.append({'command':[str(x) for x in command],'cwd':str(cwd),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});save('commands.json',commands)
        require(r.returncode == 0,(r.stdout+r.stderr)[-5000:]);return r.stdout
    require(execute([sdk,'--version']).strip() == '10.0.401','Actual SDK differs from existing pin')
    assay,catalog=inspect_sources();save('source-assay.json',assay);save('source-catalog.json',catalog)
    execute(['python3',HERE/'test_instrument.py'],cwd=ROOT)
    project=ROOT/'north-star/tooling-study/Checks/NorthStar.ToolingChecks.csproj'
    execute([sdk,'build',project,'-c','Release','-m:1','--disable-build-servers'])
    dll=project.parent/'bin/Release/net10.0/NorthStar.ToolingChecks.dll'
    execute([sdk,dll,'--catalog',output/'source-catalog.json',output/'csharp-catalog.json'])
    execute([sdk,dll,'--native',output/'native.json'])
    comparison=json.loads((output/'csharp-catalog.json').read_text());compare_results(catalog,comparison)
    require(input_hashes() == before,'Source, library or instrument changed during execution')
    save('results.json',{'schema_version':1,'checks':{'passed':len(catalog['references']),'failed':0},'same_identity_cases':len(catalog['references']),
                         'actual_source_references':81,'source_assay':assay,'source_hashes':before,'source_stable':True,
                         'native':json.loads((output/'native.json').read_text()),
                         'scope':'Exact item identity/quarantine and actual portable C# retained-tool contract; no full source recipe/unlock/effect implementation, historical runtime, Unity/Windows or human assessment.'})
    print('PASS: SAME '+str(len(catalog['references']))+' Python/C# identity cases;81actual references,370known IDs,2quarantined records;native contract controls')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:run(a.output,a.dotnet)
    except(OSError,ValueError,KeyError,subprocess.SubprocessError)as e:p.exit(1,'FAIL: '+str(e)+'\n')
