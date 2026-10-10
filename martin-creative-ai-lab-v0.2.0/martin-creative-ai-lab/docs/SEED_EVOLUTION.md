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
