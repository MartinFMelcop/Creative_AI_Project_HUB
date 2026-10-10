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

## Current progress — v0.3.1

The paragraph above records the v0.2.0 recovery. The current workstream is P11:
one local chat interaction implemented and automatically validated in this
cloud machine. Correction 0.1.1 verifies connected sends during polling congestion
and no reconnect replay after controlled heartbeat expiry. [The maintained plan](IMPROVEMENT_PLAN.md) selects the scope and
[state](STATE.md) identifies the next action. This is technical sample production,
not a Unity milestone or model evaluation. Presentation still requires Martin's
review; transfer still requires a second verified destination. P01 recovery
remains conditional on selecting that workstream.
