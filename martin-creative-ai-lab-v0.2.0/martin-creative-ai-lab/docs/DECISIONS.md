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

## ADR-009 — separate live writes from reconnect replay

**Date:** 2026-10-10. **Status:** implemented and locally verified in P11 0.1.1.
**Authority:** current portfolio increment request; diagnosis and correction by Codex.

The committed 0.1.0 client used volatile emission to prevent offline buffering.
Two new browser checks show that the policy was incomplete: a connected polling
transport drops a form message while its previous write is in flight, and a
stale connected flag can still leave a Socket.IO reconnect packet when the
heartbeat predicate reports expiry. Both checks fail against the recorded old
client and pass against the correction.

Use ordinary acknowledged emission to retain the live Engine.IO write queue,
then immediately clear Socket.IO's separate reconnect `sendBuffer`. Keep the
offline guard, timeout feedback, draft handling, and no automatic retry policy.
This corrects text delivery during local congestion without introducing durable
delivery, server persistence, message identities, or a new shared abstraction.
The exported buffer property and pinned client implementation were inspected;
dependency resolutions and server code remain unchanged.

The polling regression uses real HTTP writes. Heartbeat expiry is explicitly
injected at a pinned internal predicate, restored immediately, and followed by
an actual reconnect; it is not a network-loss or timing study. The full suite
passes 17 tests. The historical source archive and prior run record are preserved.
Transfers to P02/P01 remain candidates; no destination consumer has been verified.

**Revisit:** upgrade Socket.IO, introduce retries or another outgoing event,
or require outage recovery. Recheck queue lifetimes and acknowledgement behavior
before changing the policy. Martin's UI review remains separate and unperformed.

## ADR-010 — adapt a reproduced P11 defect into a bounded P02 task

**Date:** 2026-10-10. **Status:** implemented and locally calibrated.
**Authority:** current continuous-development request; selection and execution by Codex.

P11's working slice is already published and validated. P02 has only guidance,
while the environment can reproduce a real client defect without Unity or model
credentials. Choose one send-policy repair task rather than creating another app
or manufacturing a candidate score. P02 becomes AI Evaluation & QA Lab; Unity
stays its historical proposal and remains conditional on an actual engine task.

Export an explicit allowlist from committed P11 0.1.0 (`66041e7`), plus brief and
hashes, into a fresh workspace. Do not include Git, solution, tests, evidence, or
knowledge. Keep the evaluator's pinned server and 17 tests in P11; load only the
submitted client bytes through the existing route. Support-file mutations are
rejected; altered evaluator artifacts require recalibration. Output records and
existing workspaces cannot be overwritten. A missing browser or incomplete run
is inconclusive, distinct from a rejected artifact.

The known baseline fails exactly two checks and the known correction passes all
17; eight harness regressions pass. This validates TR-009's task adaptation into
P02, with no shared abstraction or change to P11. These controlled probes are
not independent candidate/model attempts. Public source remains discoverable;
export separation is not a secrecy guarantee, OS isolation, or a security sandbox.

**Revisit:** a real independent candidate, new test/suite version, additional
editable files, reserved material, engine integration, or a requirement to execute
untrusted artifacts. Record actual identity/context/attempts before performance
claims. Never infer model training or knowledge transfer from co-located files.

## ADR-011 — retain incomplete command evidence and bound process cleanup

**Date:** 2026-10-10. **Status:** implemented and locally verified, P02 runner 0.1.1.
**Authority:** current development request; diagnosis/correction by Codex.

The published runner omitted timeout/launch attempts from result records. An
actual timeout probe lost both diagnostic streams, and an inherited child remained
alive after the direct process was stopped. A delayed-return hypothesis was not
reproduced on Python 3.12 POSIX; do not inherit it as an observed defect.

Use stdlib Popen with a private POSIX process group. Preserve attempted command,
both captured streams, elapsed/deadline values, actual exit/launch state and capture
completeness. Request SIGTERM, then forced shutdown and bounded draining; do not
wait indefinitely for an escaped pipe holder. Every timed-out gate is inconclusive,
including a late passing summary. Keep nonzero exits and genuine syntax rejection.
Non-POSIX direct-process fallback remains unverified. Group cleanup cannot contain
descendants that create another group/session; it does not establish a sandbox.

Separate runner 0.1.1 from starter/task contract 0.1.0 so the correction does not
invalidate existing exports. All nine export files are unchanged. Fifteen current
runner tests pass; seven new methods fail against the recorded runner. Known old
and corrected clients retain the 15/17 and 17/17 calibration outcomes.

**Revisit:** independently produced code, another OS, stronger isolation, different
deadline requirements, changed suite/runtime or a new output consumer. Record
tested limits instead of assuming process-group termination controls a browser tree.
