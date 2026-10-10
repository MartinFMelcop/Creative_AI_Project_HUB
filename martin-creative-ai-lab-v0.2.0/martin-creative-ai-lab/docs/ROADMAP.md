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

## Atualização v0.2.0

A recuperação seletiva de P10/P11 encerrou uma unidade documental da descoberta. Ambiente de Martin e seleção da primeira frente continuam pendentes. A Fase 2 pode usar uma task Node/Socket.IO de P11 ou domínio puro de P10, identificando a stack real; isso não equivale a executar Unity. Fases posteriores continuam condicionais, não compromissos simultâneos.

## Current progress — v0.4.1

P11 0.1.1 is completed and Git-published in merge `df1bd59`. P02's first practice
task now has a fresh starter export and pinned evaluator. Calibration rejects
the known baseline and accepts the existing correction. [The plan](IMPROVEMENT_PLAN.md)
and [state](STATE.md) distinguish this validated harness from independent model
evaluation. Next: one candidate-produced client with explicit context/tools and
recorded attempts. Human P11 UI review and engine/media recovery remain separate.
No calendar, parallel project activation, or task-count target is added.

P02 runner 0.1.1 now preserves incomplete-run diagnostics and bounds cleanup of
inherited process groups. Starter exports remain byte-identical to 0.1.0. An
independent candidate remains the next gate; the correction does not satisfy it.
