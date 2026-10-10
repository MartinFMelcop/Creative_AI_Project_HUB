# Decisões

## ADR-001 — projetos como seeds transformáveis

**Data:** 2026-10-10. **Origem:** orientação explícita de Martin.

O laboratório aceita transformação integral dos projetos, incluindo engine, mídia, nomes, conteúdo, fusões e encerramentos. A origem deve ser preservada como histórico, sem canon automático. Antigas proteções criativas conflitantes são superadas por essa autorização no escopo deste laboratório.

**Limite:** fatos profissionais e resultados não podem ser reescritos como ficção.

## ADR-002 — monorepositório com fronteiras por projeto

**Data:** 2026-10-10. **Estado:** proposta inicial de implementação.

Usar um diretório comum para estado, conhecimento e descoberta, com fontes e execução isoladas por projeto. Promover componentes compartilhados após uso concreto, evitando dependências circulares.

**Revisitar:** manutenção, tamanho, acesso público/reservado ou execução tornarem a estrutura imprática.

## ADR-003 — evidência antes de claims

**Data:** 2026-10-10. **Estado:** regra de operação inicial.

Separar legado, inspeção de arquivos, implementação, execução, validação e apresentação. Cases simulados e contribuição humana devem ser identificados corretamente. Relatos antigos de IA não são evidência de runtime vigente.

## ADR-004 — auditoria de Artemyra como primeira frente recomendada

**Data:** 2026-10-10. **Estado:** recomendação, não decisão posterior do autor.

Começar por inventário e auditoria aproveita requisitos, BA e delivery, e revela o que pode sustentar economia e protótipo. P02 desenvolve avaliação e autonomia técnica depois do diagnóstico do ambiente.

**Alternativa:** priorizar peça criativa ou outra frente se Martin escolher esse objetivo.

## ADR-005 — preservação seletiva de legado

**Data:** 2026-10-10. **Estado:** aplicado na v0.2.0.

Incorporar P10/P11 como reservatórios em triagem, preservando seleção textual com commits e hashes e mantendo inventário completo dos snapshots. Não reconstruir todos os projetos nem duplicar binários no laboratório. A seleção não é backup integral; a possível aposentadoria remota permanece fora desta entrega.

## ADR-006 — não herdar crescimento obrigatório ou automação antiga

**Data:** 2026-10-10. **Estado:** aplicado.

Extrair rastreabilidade e handoff úteis do Rave sem copiar regras de novo backlog a cada homologação, AI_ONLY, canon imutável ou commits automáticos a cada 30 minutos. A tarefa atual e o mandato de transformação governam o laboratório. Uma fase pode reduzir escopo ou encerrar uma ideia.

## ADR-007 — alternativas de primeira fatia com fontes disponíveis

**Data:** 2026-10-10. **Estado:** recomendação, sem seleção de Martin.

Chat bidirecional, diálogo com estado e domínio de combate são alternativas pequenas após a recuperação. A recomendação original de P01 continua válida caso essa prioridade seja mantida, mas depende de localizar Artemyra. Nenhuma nova frente foi ativada nesta entrega.

**Subsequent decision:** ADR-008 selects P11 for the current increment. This
paragraph remains the historical v0.2.0 recommendation, not the current state.

## ADR-008 — complete P11 before expanding the portfolio

**Date:** 2026-10-10. **Status:** implemented and locally validated.
**Authority:** Martin's current request to assess, prioritize, and implement
one meaningful increment; selection and execution by Codex.

Choose P11's missing chat interaction because all three source files are
available, the defect is inspectable and reproducible, and Node plus Chromium
can verify the full browser path here. P10's combat/dialogue extraction is a
useful alternative; the other historical games and creative masters require
baseline recovery. This choice changes the current work order, not their origins.

Retain Express 4 and Socket.IO 4, pin current compatible versions, and work in
`projects/realtime-integration-lab`. Keep the recovered ZIP and its source
registry immutable. Add one local room with explicit payload, acknowledgement,
rejoin, and rendering rules. A single broadcast path includes the sender.
Bound UI history; preserve drafts on rejection/uncertain delivery. No game
engine migration, persistence, model evaluation, or shared framework is needed.

The baseline browser delivery check fails on the original source and passes
on the adaptation. Fifteen targeted tests and a CLI startup smoke demonstrate
the local contract; evidence records source and working artifact hashes.
P11 reaches M4 for this slice. Other projects and candidate transfers do not
inherit that maturity. Correct the lab manifest's absent-file entries from
actual maintained files instead of fabricating missing source contents. The
validator now excludes installed dependency documentation; three regression
checks preserve working-project link and archive-integrity enforcement.

**Revisit:** Martin's usability review, a real second consumer, or a requirement
for persistent/reliable delivery changes the contract. P02 evaluation work
must keep candidate and reference contexts separate; a public repository alone
does not provide that separation.
