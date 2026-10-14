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

## ADR-017 — adapt one recovered dialogue scene into a playable destination

**Date:** 2026-10-11 (environment UTC date). **Status:** P10 CLI 0.1.0.

P02's snapshot increment is complete; independent candidate and P11 human review
remain evidence gaps. P10 has inspected, preserved NPC dialogue data but no
working destination. Choose one creative slice that can actually execute here:
an English Waystone scene in Python's standard library. Avoid missing game/media
baseline reconstruction, engine binding and another evaluation task inventory.

Reuse nine NPC-0007 priorities, deltas, moods, flags/events and initial
state/relations with verified source hashes. Replace expression evaluation with
closed predicates. New framing, a one-time herbs prerequisite, one apology per
unresolved lie, four endings and a 12-turn budget are explicit adaptation rules.
Use the catalog's stress-80 gate, not the profile's threshold 88; use its five-turn
cooldown and define expiry to WARY after five accepted waits. No claim of full
personality scoring or legacy-game equivalence follows from those retained fields.

Nineteen behavior/CLI/source checks and recorded command playthroughs support
bounded M4. Human creative quality, usability, balance and portability remain
unverified. The seed patch records this durable destination/workstream change;
P02/P11 stay unchanged. Keep the archive read-only and cross-project transfers
as candidates until a second destination proves actual use.

**Revisit:** reader feedback, another scene consumer, persistence, different
memory/selection semantics or an engine requirement with its own runtime evidence.

## ADR-018 — let apology repair harm and require resolving deception

**Date:** 2026-10-11 (environment UTC date). **Status:** P10 CLI 0.1.1.

Observed 0.1.0 grants passage with an unresolved false order. Three lie/apology
cycles also increase trust 45 to 63; at trust 39, one cycle crosses the threshold.
The single-apology gate stops repeats of one apology but leaves manufactured
new faults profitable. Correct this scene behavior without changing the archive
or claiming the legacy design itself is defective.

Remember trust when the first unresolved lie opens. Retain that ceiling through
additional lies and outbursts. Cap the catalog's +6 apology recovery at this
ceiling, then clear the obligation/ceiling. Each new episode remembers current
trust. Require no unresolved lie for cooperation. A higher-priority scene refusal
asks for correction and takes a turn; a refused last-turn agreement reaches dusk.
Trace origin distinguishes that new response from the nine retained records.

Four new regression methods produce five failures on committed 0.1.0, including
both initial-trust subtests. All 23 behavior/CLI/source checks pass on 0.1.1.
Human dramatic quality and balance remain unreviewed. This stays within the
existing P10 destination, so seed version 0.4.6 and bounded M4 do not change.

**Revisit:** reader feedback or an honest trust-gaining action. Future unrelated
trust effects need an explicit recovery rule instead of silently expanding this cap.

## ADR-019 — run existing bounded contracts on GitHub changes

**Date:** 2026-10-11 (environment UTC date). **Status:** shared lab CI.

The three active destinations have executable regressions but no GitHub workflow.
Use two Ubuntu 24.04 jobs for integrity/dialogue and chat/evaluation, triggered by
main pushes, pull requests to main and manual dispatch. Keep the project versions,
starter contract, maturity and seed version unchanged. CI is a shared QA consumer,
not a new product, evaluation task or automatic creative-development loop.

Pin actions to verified commits, grant only contents-read, disable persisted
checkout credentials and impose job deadlines. Fetch full history because P02
materializes historical starter/evaluator snapshots. Install the existing locked
npm graph and its Playwright Chromium; fail browser setup rather than skip it.

A small standard-library command exports two temporary workspaces and requires
the original 15/17 rejection and pinned reference 17/17 acceptance, including
complete counts and the behavior gate. Unexpected or inconclusive outcomes fail
the job. Preserve JSON diagnostics as artifacts for 14 days. Controlled references
are never independent candidates or model scores. Human creative/usability review,
other operating systems and deployment remain separate evidence gates.

**Revisit:** runtime/dependency changes, explicit evaluator recalibration or a
required branch-protection policy. Adding a workflow does not enable protection.

The first hosted run passed the chat suite but exposed a P02 test-only `/proc`
race during child reaping. Read stat directly; treat FileNotFoundError and
ProcessLookupError as absence, while preserving live-state assertions and other
read errors. A controlled real-child probe fails on the published assertion and
passes after correction; 23 runner regressions cover the retained cleanup gate.
The runner implementation, task contract and project version are unchanged.

## ADR-020 — page activity participates in local unread state

**Date:** 2026-10-11 (client date; America/Sao_Paulo). **Status:** P11 0.1.4.

The published client clears arrivals at the bottom even when its page lacks
focus. Count an arrival as unseen when the page is hidden, lacks focus or is
browsing earlier text. Preserve existing near-bottom following and anchoring;
activity controls marking arrivals read, not transport or history retention.
Show the same bounded count in the tab title and Jump to latest.

Focus/visibility changes and scrolling clear only on a visible, focused page
within 24 pixels of the bottom. Returning to earlier text retains the count and
anchor. Explicit Jump to latest restores the title and existing focus destination.
The count remains capped at 200 retained arrivals. No notification permission,
persistence, identity, new package or P02 task requirement is introduced.

Three regression checks disable Playwright's forced-focus override and activate
real Chromium tabs; a fourth explicitly controls the Page Visibility API because
headless tabs stay visible. All four fail on the published 0.1.3 client. This
proves the local policy at those boundaries, not minimized windows, human
attention, assistive technology or other browsers. P02 retains its own snapshot.

**Revisit:** human review, a different browser, resize/zoom semantics or an
explicit durable read-receipt/notification requirement.

## ADR-021 — preserve reading intent before viewport reflow

**Date:** 2026-10-11 (environment UTC date). **Status:** P11 0.1.5.

The published client loses the live edge on height reduction and changes the
visible message when long text wraps at a narrow width. Remember whether the
reader follows live text, or their first visible retained message and pixel
offset, together with the conversation's last dimensions. ResizeObserver restores
that position when width/height changes. Ignore reflow-generated scroll events
until restoration; ordinary scrolling updates the remembered reading position.
Reconcile a pending resize before a broadcast, and reuse the same restoration
logic for retained-history eviction. Keep fractional correction and the existing
fallback when an anchor expires.

Unread clearing still requires a visible, focused page near the bottom. Retain
inactive counts through resizing. This choice preserves a message and offset
where the scroll range permits, rather than a word/line after wrapping. It adds
no dependencies or P02 requirements. Three real-viewport regressions fail on
committed 0.1.4 and pass on the correction, including subsequent eviction and
native tab focus. Seed version and bounded maturity do not change.

**Revisit:** human reading feedback, browser zoom, font-only reflow or another
browser. The current evidence covers viewport geometry in Chromium.

## ADR-022 — require manifest completeness before validating digests

**Date:** 2026-10-11 (environment UTC date). **Status:** shared lab integrity gate.

The existing CI hash command accepts a manifest after an entry is removed;
matching listed hashes do not prove coverage. Compare the manifest with Git's
tracked plus nonignored untracked inventory under the nested lab, excluding only
the manifest itself. This matches the maintained-file generation convention.
Tracked ignored files remain required; normal installation/cache outputs remain
outside the inventory. Stage deletions before refreshing the list.

A standard-library checker rejects omitted or stale entries, duplicates,
malformed/noncanonical paths, linked or missing files and byte mismatches. Keep
the registry/link/archive validator separate. Replace CI's hash-only command and
run 11 new real-Git regressions, including before/after staging and an alternative
manifest that leaves the maintained file intact. The workflow remains read-only.

Scope is the nested lab; the root workflow is outside its manifest. Hashes prove
consistency with a maintained list, not authenticity, game behavior or model
quality. Existing project versions, seed 0.4.6, maturity and task contracts stay
unchanged. Preserve all prior execution records and historical sources.

**Revisit:** a changed ownership/ignore policy, escaped filenames, repository-wide
coverage or a signed-artifact requirement.

## ADR-023 — render P10 dialogue from existing action history

**Date:** 2026-10-11 (client date, America/Sao_Paulo). **Status:** P10 0.1.2.

The CLI's successful negotiation asks for a case already made; help sounds like
agreement before the actual gates. Repeated lies and cooldown waits hide useful
state behind generic responses. Correct wording and speaker attribution through
one pure renderer reading pre-turn help, trust, unresolved-fault and historical
lie/outburst memory. Keep legacy variant identities/effects separate from newly
authored scene wording. Establish the loose rune, blocked bench and council
meeting as explicit adaptation fiction. No trait model or new state is needed.

Six new regression methods fail on the published baseline; 29 checks pass.
All reachable default-state transitions preserve menus, effects and endings.
Same-agent editorial comparison does not establish human preference or balance.
Seed 0.4.6 and bounded M4 remain unchanged. Revisit only after reader feedback on
clarity, the simple cooperative path or five-turn recovery pacing.

## ADR-024 — observe retained text reflow as well as panel resizing

**Date:** 2026-10-11 (environment UTC date). **Status:** P11 0.1.6.

Panel-only observation misses text-size/spacing changes inside an unchanged
conversation. Three real-browser user-style checks reproduce lost live text and
earlier anchors. Extend the existing ResizeObserver to retained message items,
unobserve each evicted item, and remember content height alongside dimensions.
Reuse restoration before observer delivery or new broadcasts; reflow scroll
events must not overwrite the saved anchor. Keep the near-bottom, fractional
offset, eviction fallback and inactive unread rules.

The set stays bounded to 200 messages plus the panel; no new UI, dependency or
protocol is needed. This preserves a message/offset where scroll range permits,
not the same word after wrapping. P02 keeps its snapshot and task contract;
controlled working-client compatibility is not an independent evaluation.
Seed 0.4.6 and bounded maturity stay unchanged. Revisit after human text-reading
feedback, native zoom, another browser or changing content that this contract
does not cover.

## ADR-025 — check installed direct versions before artifact verdicts

**Date:** 2026-10-11 (environment UTC date). **Status:** P02 runner 0.2.1.

A controlled evaluator-owned Socket.IO metadata mismatch still yields an accepted
17/17 artifact with runner 0.2.0, despite its recorded version disagreeing with
the pinned lock. Compare all installed direct runtime/dev version declarations
with the committed evaluator lock after preflight and before behavior tests.
Keep expected and actual versions in the record; missing/malformed reports or
mismatches are inconclusive environment failures, never artifact rejections.

Two new regression methods cover four package mismatches and six invalid reports;
25 runner checks pass. Known calibration and all nine exports remain unchanged.
No installation, new dependency, task revision, maturity promotion or model score
is introduced. This checks version metadata only: installed bytes and transitive
versions remain unverified. Revisit if a new pinned package prevents reading its
metadata or stronger dependency provenance becomes an actual requirement.

## ADR-026 — close P10 dialogue invitations at the existing deadline

**Date:** 2026-10-11 (environment UTC date). **Status:** P10 CLI 0.1.3.

Five CLI paths invite unavailable follow-up actions on terminal dusk. Render
final requests from the existing turn clock and memory; announce listening after
cooldown only if another turn remains. Keep the Keeper's practical voice, the
cleared bench and unresolved fault relevant. Preserve last-turn agreement and
departure, source records and every rule. Exhaustive comparison changes text only
at DUSK. This corrects continuity without changing balance; reader preference and
five-wait pacing still require independent human feedback.

## ADR-027 — retain an earlier uncertain attempt without replacing current typing

**Date:** 2026-10-11 (client date, America/Sao_Paulo). **Status:** P11 0.1.7.

Controlled drop/broadcast probes show that a timed-out attempt disappears from
the input after new typing, while feedback still promises retention. Reuse the
send callback's captured text in existing feedback when the values differ.
Keep current input, literal content, wrapping and explicit uncertainty. One
feedback message persists until another submission or reload; no retry, history
store, clipboard permission or recovery control is added. Thirty-eight chat
checks pass, with unchanged dependency graph and pinned task. Human readability,
manual recovery and assistive-technology review remain unverified.


## ADR-028 — complete the crossing instead of extending maintenance loops

**Date:** 2026-10-11 (America/Sao_Paulo). **Status:** P10 adventure 0.2.0.
**Authority:** Martin explicitly requests meaningful portfolio implementation and
normal publication to main; selection, implementation and review by Codex.

Recent work repeatedly polished P11/P02 and P10's single conversation. Choose a
complete rescue operation because P10 has executable source and a specific missing
experience: passage is granted in text without player-controlled travel or results.
Other creative masters are unavailable; candidate evaluation needs independent
context; a service chat product would introduce unrelated operational dependencies.

Keep `Scene` unchanged as the workshop. An adjacent standard-library adventure
owns the shared flood clock, two-item kit, river routes, residents/cargo, forecast
current and adaptive endings. Cooperative dialogue grants a rune rather than
automatic passage in this mode. Early ferry departure is also viable. Nine flood
beats and the original twelve dialogue turns are separate limits. Rescues completed
on their deadline win before abandonment; invalid/diagnostic input spends neither.
No universal shared framework, engine, media generation or new documentation system.

The implemented cargo-order comparison preserves four arrivals while changing
medicine condition. Hand rescue can preserve rope for a temporary crossing.
These demonstrate consequence, not human enjoyment. Revisit balance/pacing after
unprompted reader sessions; preserve sources and publish the honest prototype
rather than claiming a commercial game or imposing further maintenance gates.


## ADR-029 — build a complete rhythm stage around an actual original score

**Date:** 2026-10-11 (America/Sao_Paulo). **Status:** P03/P08 0.1.0.
**Authority:** Martin's explicit portfolio development and main publication request.

P10 now has a complete operation; the dormant P03 seed specifies a tractable
four-lane rhythm slice while P08 lacks delivered media. Create one original
69-second synthesized instrumental, master/export and instrument-aligned charts.
This is new implementation, not reconstruction of an unavailable historical ZIP.
Use buildless browser-local HTML/JS, Web Audio as the song clock, a small pure
judgment model and actual results/replay. Keep all game assets local to P03;
P08 records production and its verified consumer. No shared framework or model API.

Pulse consumes earned aura to preserve two missed-note combos for eight seconds;
accuracy and score still record the misses. A note's deadline determines protection,
not the time a rendering frame happens to observe it. Focus loss pauses actual
audio; resumption is explicit. Calibration is personal tap-derived offset, not
a hardware measurement. Native Sites identity remains owner-private; GitHub is
the maintained repository. Missing local helper scripts permit a documented
native credential/normal Git/static archive fallback; never persist credentials.

Technical checks and scripted full playback do not establish human enjoyment or
musical quality. Revisit note density, arrangement and timing after unassisted
hardware play/listening. Preserve the P10 operation and independent P02/P11 gates.


## ADR-030 — a static, resumable browser edition of the complete rescue

**Date:** 2026-10-11 (America/Sao_Paulo). **Status:** P10 browser 0.3.0.
**Authority:** Martin's explicit portfolio development and main publication request.

The complete Python rescue is a stronger source for an accessible demonstration
than further chat guards or another evidence-only increment. Build a static
browser edition with original situational SVG, actual action risk, journal,
local resume and portable saves. No backend, framework, remote font/image or
new shared engine is needed. A Python-backed server would retain a runtime
installation barrier; an ES-module port can be distributed as static files.

Preserve Python as the rule reference and terminal option. Export its dialogue
catalogue and compare real choices, all trace fields, state and epilogues across
representative workshop histories and the complete successor graph of twelve
specified river entries. This bounds duplication risk without claiming all
possible workshop histories. A later Python rule change must update the port.

Saves store accepted actions, not trusted state snapshots. Rebuild a fresh game
before an explicit replacement, reject unavailable actions and version/size
mismatches, and keep file export usable when localStorage fails. No undo, account,
cloud sync or future schema migration. Preserve the nine-beat flood and separate
twelve-turn dialogue window; explain a flooded landing rather than changing rules.
The map is a new diagram, not recovered art; no broad P07/rights claim follows.

Use a separate retained owner-private Sites identity for P10. Source helpers are
unavailable in this executor; native credentials on hidden stdin, normal Git and
an archive from the pushed source provide the bounded fallback. No audience
change, credentials in files, full RPG restoration or commercial approval.
Revisit comprehension/pacing through unassisted play and build a connected morning
operation from the actual outcomes rather than collecting unrelated features.


## ADR-031 — turn night outcomes into a playable relief morning

**Date:** 2026-10-11 (America/Sao_Paulo). **Status:** campaign 0.4.0.
**Authority:** explicit development/main publication and retained private-demo authorization.

Night rescue, browser delivery and original rhythm production are already real.
Choose connected gameplay/content over further narrow guards: a six-work-slot
morning uses actual residents, medicine, road/ferry, Iven and the council record.
The slow ridge fallback permits continued play after every ending. Grain, clinic
timing, seed, reserve and routes remain separate outcomes; do not collapse them
into a morality score. Remove redundant replacement when dry medicine is available.

Keep the flood engine/Python and its trace unchanged. New JavaScript Morning
owns daytime rules/scenes; Campaign connects it after a completed night. Python
parity covers the night only. A public record correction enables new supervised
repair without retroactively changing trust or historical apology. New grain,
planting and relief fiction is an adaptation, not recovered historical canon.

Senn's planting requires the full mill party; absent characters do not deliver
lines/actions. Clinic time is a fictional deadline, not a casualty model; seed
sown is not a harvest. Structural transport viability carries over, while morning
work abstracts calm return trips rather than reusing night surge damage.

Night-only schema-1 saves stay readable/exportable; after entering morning,
schema 2 records the complete accepted action journal. Replay validates fresh
state across both days and ignores supplied snapshots. Preserve the existing
owner-private Site identity and explicit session authorization. Revisit priorities,
pacing and voices through unassisted play before expanding another chapter.


## ADR-032 — realize P06 as an executed native combat trial

**Date:** 2026-10-12 (America/Sao_Paulo). **Status:** Veilbreak 0.1.0.
**Authority:** explicit portfolio development, technology assessment and main publication.

Recent browser concentration merits comparison with a dormant native seed.
Choose one complete two-phase arena over a new catalogue/framework. Godot 4.6.3
standard is installed and actually executes physics/Canvas/Controls; Unity,
its historical starter and .NET are absent. GDScript serves this coherent 2D
milestone; adopting C#/3D later requires a product reason and real tools/sources.

Create original Bell Warden geometry and deterministic sweep/charge/wave patterns.
Projectile pressure, counters, cover and a delayed phase-two echo produce connected
choices. Do not copy historical random accuracy/crit or level mitigation merely
to claim reuse; the P10-to-P06 transfer remains a candidate. Preserve the archive.

Deliver source and an exported, independently executed PCK requiring Godot.
Platform export templates are unavailable; this is not a standalone OS executable.
CI pins/verifies the official engine archive and tests source, shipped and rebuilt
packs. Synthetic legal input and actual OpenGL captures establish execution, not
human timing/enjoyment, accessibility, hardware performance or commercial approval.
No Sites publication or new engine binary redistribution is part of this work.


## ADR-033 — persist project conversations without replacing the lab protocol

**Date:** 2026-10-12 (UTC). **Status:** Project Rooms 0.2.0.
**Authority:** explicit continuous portfolio development and normal main publication.

Select P11's missing project/identity/history workflow after comparing P01, native
P06 and the existing creative games. Node/Express/Socket.IO remain appropriate;
Node 24 built-in SQLite adds ordered relational persistence without a new package,
service or stack rewrite. The separate rooms entry requires Node 24; the legacy
package minimum/lock graph stay compatible with P02's pinned evaluator.

Namespace `/studio` owns saved project entries; `/` retains the exercise protocol.
Commit before broadcast; immutable participant/attempt IDs deduplicate explicit
retries. Recover snapshots on join, keep drafts/uncertain attempts per participant
and room, and preserve newer typing. Chosen names are not verified accounts;
all trusted workspace participants can open every room. No privacy/roles inference.

JSON export is a full consumable record, not a restore tool. A stopped SQLite
file preserves continuation; a running WAL main file alone is not a backup.
Public operation requires an actual account/access/retention/backup contract and
user evidence. No hosted deployment, independent usability or market claim.


## ADR-034 — a new C# economy destination for P01

**Date:** 2026-10-12 (UTC). **Status:** Eclipse Fair 0.1.0.
**Authority:** continuous portfolio development and normal main publication.

P01 has a usable economic/party seed but no source package here. Create eight
venues and one participant/three agents rather than claiming restoration of
48 tiles, old RPG scripts or minigames. C#/.NET serves deterministic transactions,
previews, replay and batch comparisons with an actual terminal consumer. Install
published SDK 10.0.401 with its official digest; no external NuGet or new framework.
Godot is available for a later board presentation; no engine build is inferred.

Validate whole plans before mutation. Buying raises curse; rites, wards/theft,
route cost and changing wages compete with objective progress. Rotate initiative.
Twenty rounds replace the historical candidate fifteen after tested policies
failed to claim the Gate; this is a new design, not human balance validation.

Journals replay accepted actions in a fresh match; failed writes preserve play.
Compare common seeds with all four policy/seat rotations and fractional tie credits.
Fixed relative policy order and heuristic agents limit balance conclusions.
Deliver own compiled DLL/config/rules/example ZIP requiring .NET 10, not a runtime
binary or self-contained/graphical product. Human play and a native presentation
remain separate gates; no transfer or commercial claim is promoted.


## ADR-035 — connect native combat to real visual and audio production

**Date:** 2026-10-12 (UTC). **Status:** Veilbreak 0.2.0.
**Authority:** continuous portfolio development and normal main publication.

Select P06's silent/provisional presentation after comparing P01's completed
workbench, P03 content, P11 access and missing P04 manuscript. Keep the actual
Godot physics/Canvas/AudioServer architecture; installed .NET is not a reason
for migration. Integrate P07/P08 assets without a general shared engine.

Generate three original PNGs; correct the first Warden's cropped framing through
image_gen and retain accepted outputs unchanged. Keep hazards/state labels native
and reserve illustration space outside the collision floor without changing rules.
Synthesize original bell motifs, fourteen cues and two aligned 24s transports;
apply endpoint envelopes, positional voice pooling, phase crossfade and explicit
mute/pause/restart. Measure actual post-limiter output, including gain stress.

Pack and execute textures/audio with the complete trial outside source. Register
bounded production-to-consumer transfers, not historical asset recovery or AI
learning. Static poses, small-detail/alpha review, physical listening/input,
audience approval and commercial clearance remain separate gates. Preserve all
other project sources, previous encounter evidence and archive; no Sites update.


## ADR-036 — deliver a new standalone P04 reading edition

**Date:** 2026-10-12 (America/Sao_Paulo). **Status:** Darsen story 0.1.0.
**Authority:** continuous portfolio development and normal main publication.

Choose a complete literary artifact after comparing P03 music, P01 presentation,
P06 animation and P11 operations. Historical manuscript/ZIP is unavailable here;
write from qualified seed premises rather than claim restoration or a literary
judgment of unread prose. Preserve Baldino/Aevren/Darsen and identify new local
characters, incident, waterworks and corpse-binding rules. No canon ratification.

Use Portuguese for the creative work, English for maintained technical records.
Five scenes connect misconduct, loss, expertise, constrained emergency permission,
physical rescue and aftermath. Read/edit actual scenes; format tests cannot grade
literature or stand in for independent readers.

Markdown/Pandoc/ReportLab suit source/reflow/print, without an engine/browser app.
Embed licensed unchanged DejaVu Serif after font-substitution problems; retain
notices in source/PDF. Compare source/EPUB/PDF content and run official EPUBCheck.
A small publisher serves this real story, not a promoted shared framework.
Physical devices, assistive technology, reader/canon approval, exclusive rights
and commercial interest require separate evidence. No Sites deployment.


## ADR-037 — bind the C# economy to a real native board

**Date:** 2026-10-12 (America/Sao_Paulo). **Status:** Eclipse Fair board 0.2.0.
**Authority:** continuous portfolio development and normal main publication.

Choose P01 spatial/pacing/continuation workflow after comparing P03 music, P11
service needs, P06 animation and P04 reading. Preserve core/CLI 0.1.0. Godot .NET
4.6.3 directly references the net10.0 Core and unchanged journal source; do not
translate/reimplement rules, add a IPC/web bridge or claim drop-in Unity support.
Install official Mono archive with release digest; .NET SDK 10.0.401 is available.

Venue inspection does not spend turns. Forecast real forked actions, confirm,
recompute legality through Core, then save accepted actions. Pace rivals visibly
and stop auto on focus-out. Invalid load keeps live play; failed writes keep
accepted memory progress with feedback. New fair restores baseline rules/policies;
first turn or explicit Save replaces the old slot. No undo/automatic backup.

Deliver owned compiled assemblies plus editable project/configuration, consuming
installed engine APIs. Execute outside source using runtime-only .NET/no NuGet.
No engine/API/runtime redistribution, full multi-platform templates or OS export.
Native scene tests drive controls/keyboard and timing, not a human playtest.
Inspect actual OpenGL frames; hardware/accessibility/balance/enjoyment and market
validation remain separate. No Sites deployment or cross-project promotion.


## ADR-038 — complete a second musical stage with performed sustains

**Date:** 2026-10-12 (America/Sao_Paulo). **Status:** P03 0.2.0 / P08 0.3.0.
**Authority:** continuous portfolio development and normal main publication.

Select distinct P03 content/interaction after comparing P11 restore, P06 animation
and P04 readers. Keep existing browser audio clock/core; available Godot is useful
for native products but does not require replacing this distribution/timing loop.
Python/NumPy/ffmpeg render original Rain Circuit with no external samples/MIDI.
Align chart heads/tails to actual performed instrument events, not arbitrary counts.

A carried hold earns its timed-head judgment once, at its tail; an early release
misses with bounded Pulse protection. Resolve due misses/tails in song order,
not iteration/frame order. Pause freezes; allow pre-held resume or 200ms re-grab,
and fail abandoned holds. Do not automatically reward cleared physical input.
Two tracks available immediately; separate bests keep the original storage keys.
Selection/next stage owns audio buffer/clock/reset; no new shared framework.

Keep first soundtrack/score/producer and other projects byte-preserved. Extend
existing P08-to-P03 integration and register real AUD-003. Full real-audio-clock
synthetic inputs, signal measurements and score/visual review verify contracts,
not independent music/enjoyment/accessibility or commercial quality. No Sites
redeployment; physical play/listening and catalogue expansion remain separate.

## ADR-039 — recover a workspace through private local savepoints

**Date:** 2026-10-12 (America/Sao_Paulo). **Status:** P11 0.3.0.

Select complete P11 recovery after comparing native P06 animation, two-stage P03
feedback and P04 reading. Persistent work has value worth preserving; consumable
JSON lacks identity/attempt state and a live main-file copy can omit WAL data.
Node 24's online backup fits the existing SQLite service without new dependencies.
Use a local operator CLI, private schema-1 bundle and inventory/checksum inspection;
retain the public room export contract and legacy namespace. No backup HTTP route.

Validate the exact schema, data/foreign-key/integrity contracts, sequence and
inventory. Recheck staged bytes, then publish exclusively to a NEW database;
refuse existing main/sidecars instead of replacing a live store. Keep originals
for comparison. The manifest is not signed. Browser tokens/drafts are separate;
same-origin continuation needs retained browser storage. Later writes are excluded.

Real CLI and Chromium restore after simulated file loss preserve authorship,
project links, idempotency, pagination and new work. Synthetic fixtures are not
human collaboration or power-loss evidence. Scheduled/off-site/encrypted recovery,
public accounts/retention and commercial validation remain separate milestones.
Other sources/assets and P02's pinned task remain unchanged. GitHub source only.

## ADR-040 — connect native poses to committed combat contact

**Date:** 2026-10-12 (UTC). **Status:** P06 0.3.0 / P07 0.2.0.

Select P06/P07 motion after comparing completed P11 recovery, P01 strategy,
P10 progression and P03/P04 feedback. Static poses and instant radial blade hits
limit the real native experience. Standard Godot/GDScript retains the existing
physics/audio/presentation consumer without a web or language migration.

Generate two 16-pose reference-edited atlases from current portraits; reject
crowded cells, preserve accepted PNG bytes and derive foot pivots/scale natively.
Use actual displacement and combat clocks; freeze on pause/results and clear on
restart. Blade locks aim and lands at 100ms; seal gathers 75ms. One action, slowed
movement and visible recovery make commitment observable. Dodge/damage cancels
unfinished contact without refund. Damage/cue/pose share the emission event.

Preserve resource costs/cooldowns, nominal damage, boss patterns/echo and original
media. Same controller still wins both versions, with greater damage taken in the
new bounded run; this is not human balance evidence. Actual source/PCK execution
and OpenGL frames/movie verify integration. Four-keyframe generated clips retain
proportion variation and only mirror horizontally. No hand-animation/directional
completeness, independent art/enjoyment approval or standalone OS build. Extend
TR-013/add VIS-002 only; other projects and historical sources remain intact.

## ADR-041 — give P05 a bounded native tactical campaign

**Date:** 2026-10-12 (America/Sao_Paulo). **Status:** Cinderwatch 0.1.0.

Select a missing P05 destination after comparing P01 strategy, P10 scenes,
P03/P04 audience feedback and completed P06/P11 milestones. No P05 game sources
are present; do not claim recovery or borrow P10 provenance. Rename and scope
the AGI/rows/states seed to three roles/encounters and two salvage decisions.

C#/.NET 10 separates deterministic rules from Godot .NET 4.6.3 presentation.
Both tools execute; Unity was not located. No duplicate web/domain bridge or
cross-project shared framework. Stable per-round order, locked enemy intent,
screening, finite interrupts/treatment and shield/scorch expiry create decisions.
Dead locked targets waste attacks. Gout bypasses Cover. Adapt the ending to down
heroes instead of assigning them impossible actions. Retain historical sources.

Preview forks the actual domain; confirmation accepts one action. Inspection and
enemy pacing are deliberate; no automated player turns. Replay accepted actions
for a one-slot save; illegal/unsupported saves keep live play, failed writes keep
memory with feedback. No undo/cloud save or power-loss durability claim.

Compile/import/execute native controls and the owned-assembly pack outside source
with runtime-only .NET, inspect real OpenGL frames. Supply tuning and comparisons
are implementing-agent fixtures, not human balance approval. Functional UI has no
soundtrack/animated characters. Independent play, alternative strategies, OS
exports, production art/audio and demand remain separate milestones. GitHub only.

## ADR-042 — connect decisions to assigned action outcomes

**Date:** 2026-10-13 (UTC). **Status:** P11 0.4.0.

Choose P11's missing execution handoff after comparing P01 immediate-action rivals,
P04 reader needs and recent native milestones. Keep Node 24/SQLite/Socket.IO for
the actual collaborative consumer. Ownership coordinates responsibility; trusted
participants still access/edit every room. Done is a stated outcome, not external
artifact certification. Keep decision sources and complete revision authorship.

Commit revision plus event atomically; check expected version and deduplicate the
immutable attempt before stale-version checks. Recover accepted receipts without
regressing a newer board. Compare/reapply drafts explicitly; never send offline
changes automatically or replace pending drafts. Peer updates preserve reading.
Reopening requires a new reason. Keep one resumable draft per participant/room.

Migrate database schema 1 to 2 transactionally; preserve old savepoints and support
both in backup format 1. Verify exact schemas, contiguous audit/attempt snapshots
and new-file restore. Older apps cannot read schema 2. Public JSON remains schema
1 with additive action histories. Preserve the legacy/P02 graph and archive.
Actual browser/old-runtime checks and Codex frames are not independent team use,
scale, account/market approval or public hosting. Reassess those needs after use.

## ADR-043 — score native rival plans by complete race outcomes

**Date:** 2026-10-13 (UTC). **Status:** P01 native 0.3.0.

Select P01's verified one-step rival limitation after comparing P11 handoffs,
P04 prose and P10 relief scenes. Retain C#/Godot .NET, game transactions and four
classic policies. Add Planner/Warden/Raider without silently upgrading old saves.

A three-own-turn beam with local resource/protection weights performed worse
against the matched Collector proxy. Reject it. Compare every legal first action
by projecting the actual Gate/deadline under public classic policy models; prefer
win credit, earlier completion and actual standings. Replan after accepted turns.
Stable ties preserve the corresponding classic move. No recursive search or
knowledge of future human input. Show three considered moves as assumptions.

The response dialog executes actual configured profiles through the next human
turn in a fork, including initiative rotation and early endings. Compare choices
explicitly; stop auto rivals and keep live state intact. Cache advice per live
game/accepted-turn count. Classic mode and loaded profile names preserve continuity;
new names need the current consumer while rule/journal schema stays 0.1.0.

Deliver and run owned compiled sources/assemblies outside checkout with runtime-only
.NET. Preserve previous packs. Matched synthetic results and Codex frames establish
this bounded capability, not optimal play, human enjoyment, OS exports or demand.

## ADR-044 — let characters answer the actual relief outcome

**Date:** 2026-10-13 (UTC). **Status:** P10 browser 0.5.0.

Choose the verified list-only P10 finale over automatic continuation of completed
P01 planning/P11 workflows or literary expansion without readers. Reuse the static
JavaScript/replay consumer: a conversation needs no physics or native migration.

Dain requests a ready boat or channel guide. Hear actual present characters;
Iven must offer before being assigned. Lending the ferry changes local routes;
sending Iven changes ferry pace, preserving morning facts. Terms create a dusk
obligation or open loan, never an invented return. Refusal/review stay distinct.
No morality meter or new relief clock. Characters want specific work to continue;
no guaranteed happy ending or distant casualties are inferred from the loan.

A public order withdrawal is a new record, not retroactive trust repair or an
absent Keeper signature. Preserve night/morning sources and schema 1/2; only a
handover journal uses schema 3/version 0.5.0. Replay accepted actions and ignore
supplied snapshots. Old consumers do not support schema 3.

Execute actual baseline/current comparisons, complete browser journeys and the
six-history reachable graph; inspect prose/frames. Same-agent creative judgment
is not independent player approval. GitHub source publication only; preserve the
historical archive/other projects and the private demo's audience/deployment.

## ADR-045 — distribute the native trial and its mapped-pad flow

**Date:** 2026-10-13 (UTC). **Status:** P06 0.4.0.

Choose the verified editor/input access barrier over automatic continuation of
P10/P01 or more service rules. P05 has a valuable .NET delivery opportunity;
P06's standard runtime and complete media support a smaller coherent first player.
Retain Godot/GDScript and combat rules. No new web consumer or shared framework.

Keep pad actions separate from keyboard actions. Native mapping supports analog
strength/deadzone, D-pad and fresh combat/menu presses; meaningful events switch
hints. Active-pad loss clears only pad input and pauses audio/gameplay. Keyboard
continuation and explicit reconnection/focus resume remain deliberate.

Verify official TPZ/template digests and import a fresh staging project. Catch
GDScript errors even when Godot exits zero; publish no failed build. Package the
actual release ELF/PCK with permissions, checksums, Godot/third-party notices and
existing asset provenance. No new license grant or commercial clearance is inferred.

Release templates omit the script executor. Test the actual exported resources
with the editor and operate the final release window through X11 separately;
never present those as a physical controller or independent human playtest.
Preserve historical sources/other products. GitHub source/player publication is
authorized; physical output, other OS, accessibility and demand need later evidence.

## ADR-046 — rehearse a musical phrase using the existing audio clock

**Date:** 2026-10-13 (UTC). **Status:** P03 0.3.0.

Choose P03's verified whole-song/original-speed retry gap after comparing native
distribution, completed strategy/narrative/workflow and missing audience sources.
Retain the actual JavaScript/Web Audio consumer and original score/master bytes.

Partition heads into four-bar phrases. Include one preceding bar and four click
nodes; preserve tails crossing the boundary. Convert charts into performance
seconds so rate changes keep real judgment/offset/release/re-hold windows.
Slower buffer playback also lowers pitch; do not claim time-stretch quality.

Finish each take for explicit review/repeat rather than unattended looping.
Separate rehearsal exports/identity and full-run bests. Compare only the preceding
identical song/chart/phrase/rate/offset; never imply human learning from synthetic
results. Full results link actual note judgments/lost holds to playable passages.
Preserve full runs and historical scores. No new shared framework or media assets.

Real source-node/clock and old-artifact checks, full regressions and same-agent
frames establish integration, not physical listening, independent usability,
learning benefit or commercial demand. GitHub publication only; Sites unchanged.

## ADR-047 — attach original media to accepted native transactions

**Date:** 2026-10-13 (UTC). **Status:** P05 0.2.0.

Choose the verified text-only/silent P05 campaign gap over continuing completed
P03/P06 systems or expanding prose/services without audience sources. Keep C#/
Godot .NET and exact Core/save rules. No historic source/art restoration.

One original 4×2 image_gen PNG supplies eight static portraits; native regions
leave the source pixels unchanged. Seven deterministic PCM cues provide action
feedback. Before/after accepted states drive HP/shield/row/Pin/scorch markers;
selection and effects spend no turn. Restore keyboard focus after acceptance.
No animation queue, invented damage, soundtrack or full actor clips.

Reuse cards/actions and instance-owned styles; dispose media/material wrappers.
Load raw PNG/WAV so the compiled project needs no import cache/SDK. Stop playback
and drain the mixer before test/OS window shutdown. Inspect actual visible lines,
not only line-height arithmetic. Preserve old ZIP and Core/save identities.

Real native/mixer/window execution and original-version comparison prove bounded
integration; Codex frames are same-agent creative judgment. Original unsafe C#
binding abort was not reproduced: clean runs do not prove every GC/platform case.
Physical listening, independent play/accessibility and commercial rights/demand
remain separate. GitHub source/package publication is authorized; no Sites update.

## ADR-048 — retrieve immutable project records without a derived index

**Date:** 2026-10-14 (UTC). **Status:** P11 0.5.0.

Choose the verified P11 retrieval gap over another completed game/media subsystem
or prose expansion without reader evidence. Keep Node 24/SQLite and schema 2;
room/capacity bounds support direct literal matching without an FTS index,
search service or backup-format migration. Unicode compatibility/case/diacritic
normalization applies to 1–8 words; punctuation has no operator semantics.

Search notes/decisions and immutable action-event snapshots, not only current
actions. Order by saved time, stream and ID; cursors bind room/query/type, pin both
ceilings and retain the first page. Concurrent writes flag explicit refresh.
Context labels the actual revision and separately reads its source/current work;
board navigation keeps the highest known revision and does not replace drafts.
Late HTTP responses cannot cross room/identity/query generations. No auto-save.

Actual old/current HTTP comparison and 81 tests prove bounded behavior. A local
20,000-record sample justifies this cost here, not concurrent service scale.
Reconsider indexing from real latency/usage evidence with a concrete migration
and recovery contract. Trusted identities/ownership remain chosen names rather
than private-room roles; real team benefit and commercial demand are unverified.

## ADR-049 — translate the complete source into distinct reading editions

**Date:** 2026-10-14 (UTC). **Status:** P04 0.2.0.

Choose a full English translation of the inspected Portuguese story over another
nearby game/service feature. This creates actual creative content for reader
assessment; it does not establish an audience or commercial rights/demand.
Keep original PT text/metadata/editions/styles/fonts unchanged. A two-profile
catalogue drives the existing Python/Pandoc/ReportLab producer/checker; default PT
and old filenames remain, English has distinct language/identity/front matter.
No browser product, new engine, sequel or unavailable manuscript restoration.

Translate descriptive Salt Street, retain personal/Darsen/saelir names, and
separate wash valve from ledger, corridor grille from outlet screen, drain from
inlet/outlet. Preserve contact/intact joints, limited permission, book loss,
injury, daughter ignorance and pending consequences. Interpret the awkward guard/
beam line against the following order; record that choice and inferred shrouding.
Do not promote either to author-approved canon or an independent translator result.

Exact artifact text, metadata/navigation/fonts and official EPUBCheck establish
format integrity. Full paired source and raster/reflow review are by Codex;
paragraph/name correspondence is not semantic proof. Seek independent linguistic/
literary and device/accessibility evidence before calling this a release-quality
translation or deciding further expansion.

## ADR-050 — separate local controls from replayable economy rules

**Date:** 2026-10-14 (UTC). **Status:** P01 native 0.4.0.

Choose any-seat/shared-device play from the current portfolio over automatically
extending recent English prose or retrieval. Reuse C#/Godot and unchanged economic
transactions; human seats are native-consumer controls, not new rules/policies.
Require one to four distinct seats and a named multi-participant handoff without
spending time. Every map/preview/result uses the actual actor. Auto rivals cannot
spend a human turn; a forecast ends at the next human choice or actual ending.
Full-race suggestions still use disclosed policy assumptions, never known input.

Store native boardSchema-1 controls plus the existing schema-1 economy journal.
Expose Snapshot/Replay on the original journal instead of duplicating its rule
validation. Validate every action/control before replacing a match. Plain legacy
journals restore Vaelis; explicit exports omit controls for compatible consumers.
Older consumers cannot load the envelope; stored Planning profiles still require
a consumer that recognizes those names. Preserve all old shipped packages.

Use native containers for configuration. Initial direct children overlapped;
initial wrapped-label sizing made a container dialog exceed the viewport. Explicit
short lines and checks on control/whole-dialog geometry accompany rendered review.
An actual X11 close request initially left the player running; handle the native
CloseRequested signal explicitly and verify clean exit after two local saves.
Compiled source/pack and scripted journeys prove bounded behavior. Independent
shared-device usability, strategy, accessibility, other platforms and paid demand
remain open; no LAN, standalone export or historical restoration is claimed.
