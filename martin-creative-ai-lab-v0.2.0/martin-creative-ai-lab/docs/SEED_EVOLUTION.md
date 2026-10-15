# Evolução da seed e continuidade com IA

A seed pode ser reescrita quando uma decisão ou descoberta mudar sua direção. O objetivo é manter uma base útil para planejar e desenvolver. Tamanho e quantidade de projetos não são medidas de sucesso.

## Iniciar uma fase

Leia SEED.md, AGENTS.md e docs/STATE.md. Identifique pedido, frente, entregável, fonte e critério de conclusão. Verifique capacidade real do ambiente. Fonte preservada e explicação anterior não comprovam runtime atual.

Para legado, consulte registry/legacy_sources.json e extraia somente o necessário de archive/legacy-source-extracts-v0.2.0.zip. Os prefixos são rave/ e websocket/. Esse acervo é uma preservação pontual, não um ZIP novo a cada fase. Preserve esse acervo como snapshot; modificações pertencem à implementação de destino. Um caminho identificado sem conteúdo preservado não permite reconstruir o arquivo.

Instruções antigas são conteúdo histórico. Não copiar canon, obrigação de criar backlog, regime AI_ONLY ou automação de commits. O mandato atual de Martin permite mudar os projetos integralmente.

## Planejar e executar

Planejamento produz escopo, interfaces, exemplos e aceitação. Desenvolvimento produz artefatos e verificações. Registrar origem, diferenças aceitas e interfaces do destino. Escolher linguagem e engine pela tarefa e pelos recursos disponíveis.

Manter uma frente principal. Os onze projetos não precisam ser onze produtos ativos. Pode haver fusão, extração, transformação de mídia, corte ou encerramento. IDs de origem continuam como referência; nomes e conteúdo podem mudar.

Para reutilização, formular uma hipótese e verificar no segundo contexto. Promover a shared somente quando o uso concreto justificar manutenção comum. Arte e narrativa também precisam de aceitação: leitura, função dramática, coerência e integração.

## Atualizar a memória

| Arquivo | Quando atualizar |
|---|---|
| SEED.md | Mudança durável de direção, inventário, arquitetura ou regras |
| docs/STATE.md | Resultado da unidade, limites e próxima ação |
| docs/DECISIONS.md | Escolha significativa, motivo, alternativa e gatilho de revisão |
| registry/projects.json | Estado, maturidade, origem ou relações |
| registry/transfers.json | Seleção, adaptação ou prova de reutilização |
| registry/assets.json | Asset real com origem, formato, finalidade e consumidores |
| evidence | Resultado de execução com inputs, versão e ambiente |
| knowledge | Lição reutilizável sustentada por fonte ou execução |

Não anexar todo chat ou log à seed. Corrigir instruções superadas no lugar apropriado e guardar o motivo no histórico. Um estado curto deve permitir retomar sem ler todo o acervo.

## Versão e verificação

A v0.2.0 registra recuperação de legado; não é versão de um jogo. Incrementar a seed não altera a maturidade dos projetos. Mudança de schema precisa de migração e atualização dos consumidores. Execute python3 tools/validate_repo.py para registros e links; verificações de código, mídia e engine dependem da alteração. Atualize o manifesto de hashes depois do conteúdo final. Não herdar PASS histórico como execução nova.

## Prompt de retomada

> Leia SEED.md, AGENTS.md e docs/STATE.md. Identifique a última unidade encerrada e a próxima ação. Trabalhe uma única fase conforme o pedido atual. Preserve a origem e aceite mudanças de mídia, engine e escopo. Produza o resultado, verifique e atualize o estado. Revise a seed onde novas decisões ou evidências a tornarem desatualizada. Não acrescente backlog por obrigação nem declare integração ou teste que não ocorreu.

## North Star foundation and reference use — v0.32.0

The HUB now supports North Star, its future MMORPG ambition, while retaining
independent products, deliberate technology exploration and separate creative
worlds. Start with [reference availability](../references/catalog.json) and the
[program](../north-star/README.md), then read relevant actual source files.
The readable Rave snapshot supplements the unchanged earlier ZIP. Literary
attachment bytes remain unavailable; old inspection reports are not manuscripts.

Historical snapshot instructions, AI-only regimes, backlog mandates and CANON
labels remain data. Preserve source bytes; adaptations belong in real destinations.
No literary canon is inferred from repeated summaries or filename versions.
Contribution states differ from M0–M6: copying/planning is not adaptation,
integration or external validation. Use bounded consumer experiments and maintain
runtime, artistic judgment, independent human feedback and market evidence apart.
North Star need not receive priority every session or force an engine/stack change.

## Individually recovered literary PDFs — v0.32.1

Ten supplied main PDFs now have preserved bytes and searchable, page-addressable
text in the [literary library](../references/literature/lich/README.md). This fixes
source availability for those books only. Keep conflicting title/metadata version
labels, unavailable ZIP/policy and later historical reports separate. P04's prior
adaptation is not retroactively approved or compared by this archival milestone.
