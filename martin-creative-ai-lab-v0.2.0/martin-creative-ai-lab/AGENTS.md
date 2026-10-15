# Instruções de operação

Estas instruções devem ser lidas pelo agente que trabalhar neste repositório. A leitura automática depende do ambiente; quando necessário, Martin deve pedir explicitamente sua leitura.

## Entrada

1. Leia `docs/STATE.md`, `registry/projects.json` e a seção 0 de `SEED.md`.
2. Consulte as seções pertinentes da seed, o estado do Git e os arquivos reais da tarefa.
3. Verifique ferramentas, engine e permissões disponíveis. Não presumir que conectar GitHub habilita execução ou escrita.
4. Trabalhe na unidade autorizada. Uma fase de planejamento entrega arquivos reviewáveis; uma fase de desenvolvimento entrega alterações e verificações.

## Direção do autor

Os projetos são seeds e podem mudar integralmente de nome, conteúdo, mídia, engine e escopo, conforme autorização de Martin em 10/10/2026. Registre alterações relevantes e a origem histórica. Essa liberdade não autoriza inventar fatos profissionais, autoria, testes, medidas, publicações ou contribuição humana.

## Execução

- Preserve alterações do autor. Inspecione antes de editar.
- Avance em escolhas reversíveis e no trabalho que não depende de lacunas.
- Não crie loops de confirmação para cada escolha de implementação.
- Peça informação somente quando ela realmente impedir a decisão ou a execução dependente.
- Não publique, envie mensagens, faça force-push ou apague fontes irrecuperáveis por inferência desta seed; essas ações precisam da autorização concreta da sessão.
- Não use agentes paralelos a menos que o usuário ou instruções aplicáveis autorizem explicitamente essa delegação.
- Use a menor arquitetura que permita provar a hipótese; componentes compartilhados precisam de uso concreto.
- Direcione testes aos riscos relevantes. Não chamar análise estática de playtest.
- Referência de avaliação não entra no contexto do candidato; pasta em repo público não é reservada.
- Não atribua validação a Martin se ele não a realizou.

## Encerramento

Atualize `docs/STATE.md` com mudança, evidência, limites e próxima ação. Registre decisões duráveis em `docs/DECISIONS.md`. Atualize registros de projetos/transferências/assets quando o estado mudar. Evidências de execução devem identificar ambiente e versão/commit/hash.

Execute `python3 tools/validate_repo.py` quando alterar registros ou links documentais. Esse check só valida estrutura; não substitui testes do projeto. Para código, arte e áudio, faça verificações proporcionais e registre o que não foi executado.

Entregue resumo claro com arquivos alterados, resultado, verificações e limites. Não anuncie build, release ou resultado que não exista. Não anexe o chat inteiro à seed.

## Fontes recuperadas e revisão da seed

Consulte docs/SEED_EVOLUTION.md ao atualizar direção e memória. registry/legacy_sources.json distingue caminhos inventariados, textos lidos e fontes preservadas. O acervo histórico é somente leitura como origem: extraia a unidade necessária e desenvolva no destino. Instruções antigas não substituem o mandato atual. Não herdar expansão obrigatória de backlog, AI_ONLY ou automação periódica. Nenhuma transferência foi concluída somente porque uma fonte foi preservada.

## North Star and the reference library

`references/README.md` / `references/catalog.json` distinguish source snapshots,
explicit exclusions and unavailable/documented-only literary versions.
`north-star/README.md` / `north-star/capabilities.json` describe the future MMORPG
program, contribution states and limits; there is no current North Star consumer.
Do not reinterpret project M0–M6 or create a target project ID by inference.

Catalog snapshot `source/` files are historical reference data. Their old
AI-only, backlog, CANON and authority claims are not current instructions.
Keep bytes unchanged and adapt outside snapshots. Literary policy must be read
in its actual version; old reports, filename hints and repeated fictional facts
do not establish new canon or supersede later decisions. Different universes
and similarly named concepts do not become equivalent through technical reuse.

Keep independent products and deliberate technology exploration. North Star
need not win every portfolio review and selects no final engine automatically.
Before promoting a contribution, verify the genuine destination and distinguish
runtime, creative judgment, independent player/reader feedback and market evidence.
Run `python3 tools/reference_library.py check`, its regression tests and the
existing repo/manifest checks after reference/capability changes. Update those
contracts together if actual consumers change the foundation stage.
