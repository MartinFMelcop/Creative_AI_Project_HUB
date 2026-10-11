# Roadmap por gates

Detalhamento: [SEED, seção 19](../SEED.md).

| Fase | Entrega | Gate |
|---|---|---|
| 0 — descoberta | Inventário, baseline, diagnóstico e próxima tarefa | Fonte selecionada ou ausência explícita; frente definida |
| 1 — produção P01 | Audit, riscos, MVP e backlog curto | Recomendações ligadas à evidência |
| 2 — evaluation P02 | Uma task, referência e checks | Bug reproduzível e correção demonstrada |
| 3 — economia P01 | Baseline/variante e análise | Modelo reproduzível e conclusões limitadas ao modelo |
| 4 — ritmo P03 | Vertical slice integrada | Loop, timing, restart e playtest verificados |
| 5 — criação | Uma adaptação pequena | Peça completa e avaliada no destino |
| 6 — transferência | Solução usada em dois contextos | Segundo consumidor real e benefício claro |
| 7 — apresentação | Poucos cases, demos e instruções | Links, claims e amostras corretos |
| 8 — uso profissional | Serviço/produto delimitado | Adoção, manutenção e feedback reais |

Sem calendário contratado. Definir esforço e ordem conforme recursos e objetivo atual. Uma frente principal por vez; outra frente somente com finalidade delimitada.

## Current progress — v0.4.6

P10 has its first playable destination: [The Last Waystone](../projects/waystone-dialogue/README.md),
a bounded CLI scene using nine verified dialogue variants, stateful consequences,
four endings and restart. Version 0.1.1 requires resolving a lie before agreement
and caps apology recovery at pre-fault trust; twenty-three behavior/CLI/source
checks validate the contract. The creative slice follows the completed P02 snapshot increment;
it does not start the other creative seeds or complete an engine migration.

Next: a reader reviews the dialogue and consequences on cooperative/conflict
paths. Independent EVAL-001 provenance and Martin's P11 review remain separate
gates. The earlier progress sections below are historical milestones.

## Atualização v0.2.0

A recuperação seletiva de P10/P11 encerrou uma unidade documental da descoberta. Ambiente de Martin e seleção da primeira frente continuam pendentes. A Fase 2 pode usar uma task Node/Socket.IO de P11 ou domínio puro de P10, identificando a stack real; isso não equivale a executar Unity. Fases posteriores continuam condicionais, não compromissos simultâneos.

## Current progress — v0.4.2

P11 0.1.2 preserves reading position during live updates; 22 automated checks
pass. P02 runner 0.1.2 pins the tested runtime and retains its 17-check task scope,
starter contract 0.1.0 and known artifact outcomes. [The plan](IMPROVEMENT_PLAN.md)
and [state](STATE.md) record evidence and publication confirmation.

Next: Martin's reading/keyboard review and one independently produced EVAL-001
client with explicit context/tools/attempts. Neither is implied by this increment.
Engine/media recovery stays conditional; no calendar or task-count target is added.

## QA contract — v0.4.3

Registry evidence, working directories and source IDs now have executable
reference validation. See [the contract](REGISTRY_VALIDATION.md) and
[current state](STATE.md). This closes an integrity gap without adding a phase,
task inventory, project maturity claim or product version. The existing human
review and independent EVAL-001 candidate gates remain next.

## Current progress — v0.4.4

P02 runner 0.1.3 distinguishes client parser errors from Node configuration,
preload and signal failures. Starter 0.1.0 and the recalibrated P11 0.1.2 suite
pin remain unchanged. Independent candidate provenance is still the next gate.

## Current progress — v0.4.5

P11 0.1.3 makes paused reading visible with an unread count and explicit return
to live text. The same bounded chat remains the product scope. P02 runner 0.1.4 pins the new runtime with the same
candidate contract; human review and independent candidate provenance
remain the next gates, without new task inventory.

P02 runner 0.2.0 now materializes the evaluator from its fixed Git commit, so
working app source updates do not require another pin change. Dependency and
evaluator contract changes still require explicit calibration. Existing human
review and independent-candidate gates remain unchanged.
