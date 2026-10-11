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

## ADR-012 — preserve the viewport and recalibrate the pinned consumer

**Date:** 2026-10-11. **Status:** implemented and locally verified.
**Authority:** current development/publication request; work by Codex.

The published chat jumps to the latest text on every broadcast. Three Chromium
checks reproduce disrupted reading. Choose a usable UI correction before more
task inventory; independent candidate evidence remains unperformed.

Follow within 24 CSS pixels of the bottom. Otherwise anchor the first visible
message and its offset, adjusting after the 200-item window removes earlier text.
If the anchor expires, keep the earliest retained text visible. Own browser
anchoring and carry fractional correction: the initial implementation drifted
4.0625 pixels across ten variable-height evictions. Five geometry checks now meet
one pixel. Preserve transport, markup/style, retention and dependencies.

P11 package 0.1.2 changes runtime metadata. P02's guard correctly refuses it until
recalibrated. Pin the tested P11 commit in runner 0.1.2; keep the existing 17
send-policy tests, brief and nine-file contract 0.1.0. The five reading tests
belong to P11 and add no candidate requirements. Controlled artifacts recalibrate
at 15/17 and 17/17. Publish the combined verified commits, preserving history,
rather than an incompatible intermediate. No shared component/model result.

**Revisit:** human feedback, resize/zoom/other browsers, rich media, retention
rules or repeated runtime changes that justify an isolated evaluator fixture.
Keep pixel geometry distinct from human usability.

## ADR-013 — validate registry references without evaluating their claims

**Date:** 2026-10-10 (client date). **Status:** implemented and locally verified.
**Authority:** current development/publication request; work by Codex.

Missing registry evidence could pass the documentary gate. Use a common literal
lab-relative path checker for evidence files and optional working directories,
resolving symlinks before containment checks; cross-check project source IDs.
Require project/transfer evidence lists; retain optional asset evidence and empty
lists for seeds/candidates. Schema version 1 and existing registries remain valid.

Eight new regression methods fail against the recorded implementation. All 11
current methods pass. Existence/type checking is deliberately bounded: parsing
heterogeneous evidence and imposing maturity rules would require separate
contracts. No external-link fetching, new dependency or framework is justified.

**Revisit:** another evidence format, external evidence policy, maturity gate or
registry schema migration. Keep source integrity distinct from claim validation.

## ADR-014 — attribute syntax rejection to the submitted client

**Date:** 2026-10-10 (client date). **Status:** implemented, P02 runner 0.1.3.

A real invalid NODE_OPTIONS probe rejected the unchanged valid starter with exit
9. Missing preloads also fail with exit 1; exit status alone cannot identify an
artifact defect. Require complete exit-1 parser diagnostics naming the evaluator's
temporary client before rejecting syntax. Unknown failures remain inconclusive
and retain command evidence. Do not erase inherited runtime options to conceal
configuration failures. Starter, suite, dependencies and P11 remain unchanged.

Revisit on Node diagnostic-format changes; conservative inconclusive outcomes
require investigation, rather than guessing candidate failure. This is attribution
of observed diagnostics, not a security boundary for hostile runtime injection.

## ADR-015 — give browsing readers an explicit return to live text

**Date:** 2026-10-10 (client date). **Status:** implemented, P11 0.1.3.

Preserved reading position needs a discoverable way to return to new arrivals.
Show one native button outside the message list, with a count bounded to its
200-item retained window. Keep existing anchoring and the 24-pixel follow rule.
Clear arrivals when following resumes manually or via the button; move focus
into the keyboard-focusable conversation before hiding the activated control.
Use no identity, persistence, extra live region or shared library.

P02's app-artifact guard requires a new suite pin and calibration after the P11
commit. Publish the verified commits together; keep its 17 candidate checks and
0.1.0 starter unchanged. Human and assistive-technology review remain separate
from executed Chromium keyboard/geometry checks. Revisit on actual feedback,
new retention requirements, another browser or a need for per-reader identity.

## ADR-016 — execute evaluator sources from the pinned commit

**Date:** 2026-10-10 (client date). **Status:** P02 runner 0.2.0.

Two P11 updates required P02 repinning because the checker consumed working app
files. Materialize the existing evaluator allowlist from its fixed Git commit
in each temporary runtime instead. Link evaluator-owned installed modules only
when dependency locks match, ignoring app version metadata alone. Reject no
artifact merely because a dependency environment is unavailable. Preserve the
17 checks and nine-file starter; no new shared package or network installation.

This supersedes the working-file guard in ADR-010/012/015. Pin/dependency changes
still need calibration. Lock compatibility is not verification of installed
module bytes; symlink portability and stronger execution isolation remain
unverified. Revisit when changing dependencies, OS or evaluator contract.
