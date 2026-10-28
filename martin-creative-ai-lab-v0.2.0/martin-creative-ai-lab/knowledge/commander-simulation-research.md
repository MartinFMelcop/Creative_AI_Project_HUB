---
title: "Research Transfer — Credible Multi-Agent Decisions, Simulation Validity and Distinctive Builds"
type: derived-research-study
status: v10-editorially-consolidated-pending-independent-reader-validation
primary_product: "Virgo Diamond: The North Star"
origin_case: "CommanderSIM v0.16 (separate research case)"
proposed_location: knowledge/commander-simulation-research.md
repository: MartinFMelcop/Creative_AI_Project_HUB
language: en
research_reviewed_on: 2026-10-28
research_iteration: "v10 editorial closure; release QA and independent-reader handoff"
hub_main_tree_sha_at_review: 0e1ae3ceae6be72fc084c49f61eaf1922b262542
source_and_execution_boundary: "Source/literature review and prospective protocols; no newly executed HUB games, agent-training runs, Unity Editor, Windows player, player study or GitHub publication"
next_editorial_gate: "G8 independent model reader must complete before FINAL_FOR_RESEARCH_CONSUMPTION; no further editorial version planned unless it finds a material defect"
---

# Research Transfer — Credible Multi-Agent Decisions, Simulation Validity and Distinctive Builds

> **Decision status: RESEARCH PROPOSAL.** This document replaces the previous sprawling synthesis with an implementation-oriented, evidence-graded research record. It does not add a twelfth laboratory, promote CommanderSIM into the HUB, introduce Magic IP into *Virgo Diamond: The North Star*, modify protected Brains, validate the real-world strength of four Magic decks, or assert that a planned experiment has already run. It is a candidate derived-knowledge entry governed by the HUB's existing authority and selection process.

## AI retrieval and authority contract (mandatory for consuming agents)

**Read order and purpose:** (1) read the executive decision and this contract; (2) inspect the relevant laboratory mapping in Section 6; (3) read **only** the matching technical contract in Section 2 and experiment in Section 4; (4) consult Section 3 for statistical claims and Section 10 for source verification. An optional external-to-HUB `AI_CONSUMPTION_BRIEF_v10.md` is a **convenience index**, not a second authority file or an extra HUB knowledge base. The canonical candidate for HUB integration is **only this Markdown file**.

**Authority order:** user-approved author direction and current root/workspace `AGENTS.md` -> current operating process / `docs/STATE.md` -> `labs/origins.json`, actual code and tests -> executed evidence -> this derived-knowledge *proposal* -> external papers used within their stated applicability. Do not copy proposed acceptance criteria into current execution history or modify protected Brains. This document makes no binding scheduling decision; P09's incomplete obligation remains visible.

**Claim tags used throughout:** `OBSERVED_SOURCE` (inspected source semantics), `RECORDED_EXECUTION` (earlier bounded run report), `EXTERNAL_METHOD` (published method), `INFERENCE` (reasoned applicability), and `PROPOSED_EXPERIMENT` (not run). When using a result, state the source hash, exact scenario, population/estimand, evidence level and what remains outside the claim. If those are absent, **do not promote it**. A future code change requires rechecking the impacted contract; a GitHub URL that still resolves does not ensure its byte identity.

**One-sentence handoff:** Preserve the existing C# game/combat owners; test a bounded observation-aware agent policy against fixed and held-out four-seat opponents using correct win/tie semantics; only transfer proved methods into actual North Star consumers, without changing its original world or claiming human validation.

---

## Executive decision — read this first

**Research transfer worth keeping.** Extract the CommanderSIM failure-analysis method: first distinguish the *game's legal consequences* from the *agent's action selection*; next test that an outcome actually means what the metric calls it; then compare agents under independently controlled scenario and opponent variation; only then use the findings to test original North Star counterplay and distinct builds. Favor methods that have actual consumers and falsifiable outputs over generic AI infrastructure.

**Best immediate experiment:** P01 Eclipse Fair already provides a deterministic four-person game with legal actions, settlement, an outcome, replay, look-ahead strategies and working native tests. P02 can evaluate a small *new* policy comparison on this existing owner without reimplementing it. The key gaps are the *new experiment's* explicitly declared observation contract, controlled assignment of strategy identities, robustness across held-out opponents, metric semantics and honest uncertainty. Eclipse Fair already exposes public participant and forecast data; this study does **not** establish a hidden-information exploit in the current game. **Do not change the game to force balanced wins.** Once a bounded result survives those checks, consider P06 CombatStudy as a **different** rules domain where actions are currently chosen by a human against scripted enemy pressure. Its proper contribution is a new constrained decision surface or response agent, not an unverified port of a four-player board agent. P05 owns separate build hypotheses in the existing Crossing/Loadout consumer.

**Do not prioritize this study automatically.** The authoritative `docs/prompts/CONTINUOUS_DEVELOPMENT.md` requires comparative opportunity selection, and `labs/origins.json` still reports P09 Build, Release & Operations as **incomplete**. This research must compete with actual Windows/Unity delivery, pending mandatory laboratory consumption and more consequential product work; no new permanent priority order is created here.

### Hard-earned corrections from the CommanderSIM case

| Former failure or tempting inference | Correct transfer |
|---|---|
| Approximately 30,000 abstract games imply real balance | They measure a particular surrogate and its policy population; zero complete Magic rules games were verified. |
| Card-level scores can rank real combos and counterspells | Only if card abilities, response opportunities and relevant causal context are implemented and checked. |
| One 25% win rate per archetype defines fair game design | 25% is a symmetric baseline for one fixed four-player setup; North Star needs contextual viability, legible counterplay and identifiable playstyles, not forced equality. |
| More seeds make results objectively accurate | More runs reduce some stochastic uncertainty, not model-form bias or unmodeled game rules. |
| Common seeds always help | Only when actual paired outcome covariance supports precision; matched designs can increase variance [E-CRN]. |
| The strongest candidate against one roster is generally strong | Opponent dependence and non-transitivity require cross-play, held-out policies and robust evaluation [E-METAGAME]. |
| A successful software unit test proves player experience | Software validity, intended use and human perception are different evidence levels [E-PLAYER-BALANCE]. |

### Research questions, estimated value and stop conditions

1. **P01/P02:** Can an explicitly observation-bounded policy improve a predeclared outcome on held-out four-player scenario/policy rosters **without changing** the actual Eclipse Fair legal-action or settlement contracts? *Stop* if improvements disappear in holdout, depend on forbidden observations, or violate invariants.
2. **P06:** Can an alternative action policy improve a selected objective in a *separately authored* North Star combat experiment while maintaining threat, resource, status and terminal semantics? *Stop* if the fixture requires simulating choices that the current trial does not expose or changes accepted-action consequences.
3. **P05:** Can two original build identities remain observably distinct and viable across shared challenges and countermoves rather than being optimized to one ranking? *Stop* if only a scalar score changes, the expected different decision pattern is absent, or the findings are not legible in the real consumer.
4. **P09:** Is a new tool/runtime justified by a reproducibility and delivery deficit? *Stop* if the same question is answered with the pinned current C#/Python test instruments or Unity/Windows prerequisites are unavailable.

---

## 1. Evidence, ownership and source freshness

### 1.1 What is directly observed, not merely inferred

The HUB is a public Design-Driven technology and creative portfolio organized around **eleven mandatory P01–P11 laboratory destinations** and the principal original MMORPG *Virgo Diamond: The North Star*. Its maintained code lives inside the historical wrapper `martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/` (that directory name is not a current release number). The catalog presently classifies ten destinations as `operational` and **`build-operations` as `incomplete`**. Unity/C# is the selected North Star production direction; Windows is the priority player platform and Steam is intended. Actual local .NET/C# and Godot research runs are not proof of a Unity Editor, Windows Player or Steamworks execution.

Repository review: the public `main` recursive tree was inspected at **`0e1ae3ceae6be72fc084c49f61eaf1922b262542`** (3,135 entries at this snapshot). The scientific validity of old evidence must be checked against the **specific source/revision and protocol**, not the current `main` label alone. [H-STATE], [H-ROOT], [H-CATALOG], [H-OPERATING]. Each laboratory's `README.md` is a method/consumer record; `labs/origins.json` owns status and acceptance; `north-star/DESIGN.md` owns creative decisions; `docs/STATE.md` owns work continuity. A research paper cannot promote its own proposal to the status of an integrated North Star capability.

The inspected historical CommanderSIM v0.16 artifacts were accessible in this workspace as a **separate local case study**, not a HUB source: `reports/current_kpis.json`, bounded combo scenarios, four active text decklists and the engine source. The current KPI record contains 15,000 frozen-policy and 15,000 threat-aware-policy surrogate games with the same four decks and **zero complete verified Commander games**. In the threat-aware sample: Dralnu 1,230/15,000 (8.20%), Palladia 3,994/15,000 (26.63%), Be'lakor 3,595/15,000 (23.97%), and Abzan 6,181/15,000 (41.21%). The stored paired policy effects have 95% intervals crossing zero for all four seats. These are **model-relative observations**, not a ranking for tabletop play and not a direct North Star class-balance benchmark.

The prior conversation also identified a significant *model mechanism mismatch*: a life-gain approximation for Ikra, generic ETB/blink/reanimation bonuses and incomplete mana/combat/targeting rules. Those failures are valuable as **negative calibration fixtures**, not knowledge that a particular North Star character will be advantaged. The bounded Dralnu combo micro-tests help teach event and stack ordering, but do not provide an independent, comprehensive Oracle adjudicator. Recording 64 passing unit tests does not convert micro-scenarios into complete games.

### 1.2 Evidence-claim ladder

| Level | Label in this study | Permitted decision | Example |
|---|---|---|---|
| S0 | Source inspected | A contract exists in the inspected code | `Game.Legal()` can enumerate concrete intents. |
| S1 | Existing executed source-specific record | A bounded current or historical behavior is reported and has a reproducible protocol | P01 existing exact deterministic match/replay controls, within their recorded environment. |
| S2 | New scenario exercise, proposed here | **Not yet observed**; must first run and capture identities/results | A proposed cross-play matrix and observation-bound policy. |
| S3 | Robust program-level validation | A method is shown reliable under held-out cases, rivals and independent checks | Cannot be claimed by this document. |
| S4 | Original North Star destination integration | An actual consumer uses the capability with consequence and tests | Existing consumer behaviors are separate from the proposed policy transfer. |
| S5 | Human/player outcome evidence | Appropriately sampled people can recognize/assess the effect in its target context | No such new study was conducted. |

Use the most conservative level that supports each claim. The simulation literature emphasizes that validity depends on **the question and intended use**, not a single global certificate [E-AGENT-VALIDITY], [E-NASA]. Verification asks whether the software implements its declared model; validation asks whether that model adequately supports the intended conclusion; uncertainty addresses what variation and unknowns remain. NASA's 2026 handbook is a **methodological reference, not a mandatory compliance burden** for this game portfolio.

### 1.3 Repository authority and provenance boundaries

Before future implementation, confirm `main` SHA, Git state, complete root/workspace `AGENTS.md`, `docs/prompts/CONTINUOUS_DEVELOPMENT.md`, `docs/STATE.md`, `labs/origins.json`, relevant lab methods and destination sources. Do not modify the protected Engineering, Scientific and Creative Brain originals; retrieve them selectively per `brains/README.md`. Maintain research outside those sources in `knowledge/`; put executed instrument/results in the owning laboratory's existing convention and record accepted transfers through current registry/capability mechanisms. Do not manufacture a twelfth laboratory or rebrand a preserved origin as a new flagship product.

**Three-specialty review:** Engineering must examine ownership, legal transitions, determinism, memory and performance; Scientific review must specify competing hypotheses, experimental units, controls, uncertainty and stopping; Creative review must inspect recognizable identity, counterplay, player agency and intelligible feedback. These are specialist analyses, **not independent human validation**. Differences in conclusions should be recorded, not averaged into artificial consensus.

---

## 2. Direct code audit: concrete reuse, new seams and unavoidable caveats

### 2.1 P01 Eclipse Fair: a game, not a simulation platform

**Source anchors:** [H-ECLIPSE-GAME], [H-ECLIPSE-AGENTS], [H-ECLIPSE-PLANNING], [H-ECLIPSE-CHECKS]. The maintained C# source establishes:

- `Game.Legal()` enumerates complete currently eligible `Intent` values (`Work`, `Buy`, `Rite`, `Guard`, `Steal`, `Claim`) for the active player, including spatial, currency, target, ward, curse and goal restrictions. `Game.Apply()` checks membership in `Legal()` before changing position, currency or the clock.
- `Game.Fork()` creates independent copied state and journal history. `Agents.Choose()` supplies four basic policies (`collector`, `keeper`, `opportunist`, `worker`); `Planning.Analyze()` adds three projected policies (`planner`, `warden`, `raider`). `Planning.Forecast()` is conditional projection, **not an accepted future event**; it does not mutate the live match.
- Existing `Checks/Program.cs` exercises invalid-plan atomicity, initiative, resource accounting, ward/theft, gate claims, tie winners, replay, fork isolation, strategy termination and advice determinism. Future tests must add insight rather than duplicate these claims under renamed IDs.
- A finite deadline and deterministic `Forecast(round)` are intentional domain features. Neither is the same defect as an arbitrary CommanderSIM surrogate cutoff. The domain decides what time and public forecasts mean.

**New source-level confound requiring explicit treatment:** `Current = (Seed % 4 + Round - 1 + turn) % 4`; initial positions include `seed % 8`; `Forecast(round)` also depends on `Seed`. Consequently, changing only `Seed` affects at least initiative, initial board occupancy and time-varying events. Varying policy placement across a seed sample can explore performance, but it **does not identify the isolated causal effect of going first**. A legitimate estimate for an initiative effect requires a separately specified, independently manipulable scenario contract or a predeclared design/analysis that acknowledges this coupling. Do **not** rewrite the owner to produce fair-looking outputs.

**Second nuance: shared winner status.** At the deadline `Outcome.Winners` may contain multiple IDs when their sigils, curse and gold tie. A winner-count endpoint `1{seat ∈ Winners}` is not the same as fractional win credit `1/|Winners|`. If fractional credit is selected, all seats' credits sum to one in any completed game with at least one winner. If membership is selected, they may sum above one. Both are valid *for different stated questions*, but must not be mixed, silently converted or compared against a universal 25% target as if equivalent. An explicit terminal gate claim can have exactly one winner. Retain both fields.

**Observation/strategy contract:** the current Game publicly exposes `Seed`, `People`, `Rules`, round, and a `Forecast` function. These are visible in the implementation; **they are not necessarily hidden information**. An agent's knowledge is an experiment design decision that must agree with the game's actual disclosed rules. If full deterministic forecasts are a recognized game feature, their use is legitimate under the declared *public-forecast* policy; an alternative *limited-observation* condition may be studied separately, but cannot be represented as the same game rules. `Planning.Analyze()` can use a fork and simulated opponent policies; no claim of unauthorized cheating follows unless a specific disallowed observation was read. The genuinely hazardous cases are secretly using known evaluation opponents' future policy identities, a withheld random stream, an evaluator-only label, or actual future human actions while reporting a public-information agent.

**Safe implementation seam:** prefer a read-only `PolicyObservation` and experiment-runner adapter which records every observation field and derives a candidate action from the exact owner-produced `Legal()` set. Keep `Game.Apply`, deadlines, currency and original forecast unchanged in phase one. The caller, not the agent, adjudicates outcomes. Initial candidate policies can be a deterministic rule table; complex learning is unnecessary to answer whether the interface adds value. A new wrapper should be removed if it produces no new observable testable result.

### 2.1.1 Source-exact evaluation traps that were not previously explicit

- **Deterministic seed does not create independent random streams.** `Current` combines `Seed % 4` with `Round` and `turn`; initial positions use `seed % 8`; event forecasts use a deterministic transform of `Seed`. Therefore, a claim about *the causal effect of initiative* is **not identified** by merely regressing outcomes on the seed's first-player ID. To estimate the effect of a policy, hold an eligible source scenario constant while rotating **policy assignments**, then aggregate by `scenario_family_id`; do not say that policy rotation alone identifies independent first-mover effects. New scenario constructors or changes to turn order are **different rules/experiments**, not silent correction of the owner.
- **Winner-set semantics require two endpoints.** At round-limit settlement, `Winners` includes every tied best-standing player; a gate claim ends with a single winner. Preserve both `winner_member = 1{player in Winners}` and `fractional_credit = 1/|Winners|` when the result is complete. `sum(fractional_credit)=1` is a mathematical property only for a nonempty winner set. Never report an ordinary single-winner binomial interval for dependent participant outcomes or apply CommanderSIM's 25% target to membership credit by default.
- **A public forecast is not automatically leakage.** `Game.Forecast(round)` and `Seed` are callable/public on the inspected object. The researcher must choose *public exact-forecast*, *partial-lookahead* or *limited-observation* as **separate declared treatments**. It is invalid to post-hoc call a winning policy a cheater solely because it used the game's visible forecast; conversely, evaluation-only opponent scripts and withheld scenario labels must not leak through a supposed restricted observation. Add a negative observation-redaction test for each genuinely withheld field.
- **Search is conditional, not omniscient.** `Planning.Analyze` evaluates legal first intents using `Game.Fork`, then applies publicly modeled policy responses. Such a generated trajectory is **not the opponent's committed future**. Calibrate the distinction by freezing an opponent policy and checking that forecasts agree with subsequently executed configured replies only under the same stated policy roster. Measure runtime and search-node cost alongside payoff: a candidate that improves reward with impractical per-turn search is not automatically a useful North Star result.
- **The existing owner has relevant regressions.** `Checks/Program.cs` already exercises illegal-action atomicity, gate and tie settlement, ledger, initiative sequence, independent forks, full/restarted replays, match termination and legal deterministic planning. A new adapter should add a *new falsifiable risk* (observation control, cross-play, grouping/holdout, scenario dependence) rather than inflate success counts by duplicating these tests.

### 2.2 P06 CombatStudy: actions and enemy are currently asymmetric

**Source anchors:** [H-TRIAL], [H-COMBAT-ROOM], [H-COMBAT-CHECKS], [H-COMBAT-RULES]. `CombatStudy.Trial` is an authored deterministic practice encounter, not a four-agent game. It takes commands `strike`, `bash`, `guard`, `treat`, `cleanse`, `retreat`; refusals for weapon disarm, charge exhaustion or a meaningless cleanse preserve time/resources. The adversarial side is scripted by `Threat`, direct contact and ongoing status effects; there is no freely selecting enemy actor comparable to an Eclipse Fair opponent. `Room` owns JSON command intake and observation; repeat GET/read must not spend a turn. The existing test suites validate specific scripted journeys, passive behavior, status arithmetic and terminal outcomes.

**Correct transfer:** add an *optional, separately evaluated policy* on the player-command side first, and compare only already legal actions. Derive the legal set from current exact `Trial` state and conditions, not by attempting commands and mutating state. Where `Trial` currently hides internal data, introduce an **explicit read-only view** or instrument-only state lens and prove it does not change semantics. Do not silently permit previously rejected commands, alter enemy damage, or reset a trial to make an AI policy win. An optional enemy decision owner is a second research problem requiring a new approved rules contract, not evidence of a current free enemy AI.

The selected trial supports the question: *Does a policy that accounts for disarm, DOT, charges and upcoming pressure perform differently from a reactive or random legal baseline across fixed toxic/heated profiles?* A gain in scripted survival or treatment efficiency is not automatically improved human combat, competitive counterplay or multiplayer balance. If the policy exploits a constant three-round telegraph, report that as **script-specific exploitation** until tests vary legitimately authored profiles.

**Important terminal-endpoint detail:** `Trial.Execute("retreat")` is an accepted command that terminates with `outcome="withdrawn"` without entering the normal damage/status round. A policy that retreats immediately must not be rewarded as an encounter win, counted as a combat loss by default, or silently removed from the denominator. Record `secured`, `defeated`, `withdrawn`, resource spending and round count separately, then predeclare the primary optimization target. A policy that merely exploits predictable scripted target behavior can be correct for this *fixture* and still have no credible adversarial AI benefit beyond it.

### 2.3 P05/Crossing: existing differences are not approved classes

**Source anchors:** [H-CROSSING], [H-LOADOUT], [H-NS-DESIGN]. `Crossing.Session` distinguishes `Anchor` versus `Lure`, `Plate` versus `Trail`, and commands `Walk`, `Dash`, `Skill`, `Wait`. Resolve costs, spatial thresholds, pulse/collision logic and accepted-action reward ownership are already executed in bounded C# destination tests. `PreparedExpedition` validates a complete four-slot loadout proposal and rejects incompatible replacement without silently erasing prior preparation. These are original **experimental** identities and costs, not approved MMORPG classes, canonical skills or final stat tuning.

This is a strong *build-diversity research seam* because both strategies must survive a shared goal using different resource/position behavior. However, one scripted task cannot establish universal build viability, real PvP balance or social recognition. A candidate that simply adds stronger attributes to a weak approach violates the proposed research isolation. Freeze the domain, compare fixed build policies against the same challenge, measure state/decision differences and then ask whether the result remains meaningful to actual players.

### 2.4 Existing domain transfer vs false reuse

| Owner / current state | New evidence to seek | What **not** to copy |
|---|---|---|
| P01 legal four-player game | A robust *policy* comparison with unbiased seat/outcome accounting | Eclipse Fair movement, currencies, forecast as North Star combat mechanics |
| P02 evaluator | Calibrated independent inspection of new policy artifact/results with held-out cases | Claim an existing software-task evaluator already evaluates game agents |
| P05 Loadout/Crossing | Exact interaction of equipment, approach and chosen actions | Historical MMORPG stats, names or unverified class balance |
| P06 Trial/Room | Observable tactical decision/counterplay under unchanged rules | Commander stack, Magic card text or hypothetical fully autonomous enemy |
| P11 Recovery/Journal | Exact accepted-action trace, replay and retries of the **specific** target owner | A universal network authority or cloud MMO persistence claim |
| P09 Build/Operations | Pinned actual recipient runtime and Windows/Unity obligations as specified by its catalog | Calling a C# compile "Unity validated" or installing GPU ML infrastructure without a consumer |

A reusable **design contract** can cross domains; an executable capability is integrated only when the actual destination enforces it and evidence records outcomes and limitations. The eleven laboratories remain independently accountable for their mandatory source-consumption obligations.

---

### 2.5 Source-exact non-inferences that an AI consumer must preserve

- `Game.People` and `Forecast(round)` are visible properties in P01; source inspection alone does not establish hidden cards, private inventories or cheating. A new observation interface may intentionally restrict legal information **for its experiment**, but that restriction must be reviewed, logged and kept outside the canonical game owner's settlement.
- `Game.Seed` controls `Current` through `Seed % 4`, initial positions through `seed % 8`, and the `Forecast` function. The game therefore has a *coupled deterministic scenario identity*. A within-seed rotation of policy labels cannot by itself identify a pure first-player causal advantage.
- `Outcome.Winners` can contain more than one player at the deadline. A tie is one completed game, not multiple independent wins; the primary policy endpoint below uses fractional payoff credit.
- `Planning.Analyze` examines many legal first actions using an internal public-policy rollout. `Planning.Forecast` is conditional on a proposed action and specified policies; neither means a real future action has already occurred.
- `Trial.Execute("retreat")` produces `withdrawn`, not `secured`; accepted actions advance the round under the exact fixture rules, while invalid actions do not. The enemy follows a scripted cadence, not a learned opponent strategy.

These are `OBSERVED_SOURCE` contracts at the listed snapshot, not newly rerun games, human studies or proofs that this prototype is production-ready.

## 3. Scientific protocol: from a correct outcome to a credible comparison

### 3.1 Predeclare the estimand before writing an AI policy

A result must say exactly which population, outcome and intervention it estimates. Example P01 estimand:

> The mean change in *fractional winner credit* when one designated participant uses candidate policy C instead of baseline B, averaged over a frozen mix of starting seeds, policy placements and held-out opposing rosters, while all actual Eclipse Fair rules and the other three policies remain unchanged.

This is not the effect of “better AI in all games”, not the effect of seat order, not the effect of changing build stats, and not the real expected outcome against human players. Keep the alternative *winner membership* and *first gate claim* as separate endpoints. Predeclare a primary endpoint and important secondary harms (illegal-action attempts, model compute cost, turns, currency conserved, excessive stalemates, matchup failures).

Use one sample unit per **complete game / controlled scenario block**, never count four seats from one match as four independent trials. If several matched policies share a seed scenario, treat their outcome vectors as dependent. If 24 policy permutations share one initial seed, retain one `scenario_family_id` and bootstrap/aggregate at the family rather than pretending 24 independent conditions. For finite deterministic seed enumerations, be transparent whether the estimand concerns the enumerated test suite or a hypothesized population of seeds; a confidence interval does not create an external population by itself.

For outcome vector `Y_i(C)` and `Y_i(B)` within matched scenario family `i`, define `D_i=Y_i(C)-Y_i(B)`, `mean_delta=mean(D_i)`. The paired standard error depends on the **observed** variance of `D_i`, not an assumption that common seeds always help. The common-random-numbers literature documents negative covariance and increased variance in some models [E-CRN]. Compare the paired precision with an unpaired control or explicitly measure covariance. Never use a binomial per-seat interval as an interval for this **paired difference** without matching the estimand.

### 3.2 Split causal variation into distinct dimensions

A robust benchmark specifies four factors and what is currently manipulable:

| Factor | How it appears today | How to evaluate without false causal claims |
|---|---|---|
| Rule/configuration | `Rules` values, movement, time, prices and settlement | Freeze the owner and recorded rule profile; a rules experiment must be explicitly separated. |
| Scenario/seed | One `Seed` couples initiative, starting positions and event forecasts | Sample and block jointly; isolate initiative only in a separate reviewed scenario constructor/fixture, never by naive seed grouping. |
| Policy assignment | Up to four participants can use selected policy names | Rotate candidate across player identities and compare against fixed opposing rosters; report assignment schedule and dependent outcomes. |
| Opponent population | Current classic and planning policies | Train/tune with declared rosters; reserve untested rosters for final evaluation; do not relabel a familiar roster as independent. |

If the goal is *the value of an observation contract*, compare full-forecast and limited-observation conditions as **different experimental treatments**, not as competing agents secretly playing the same public-information rule set. If the objective is **seat/initiative fairness**, first build an intentionally orthogonalized fixture preserving the original `Game` owner as an untouched control. Check exact mirrored transition behaviors where genuine symmetry exists; the map's venues/positions are not freely symmetric, so an arbitrary seat permutation is **not** a metamorphic property of the original game.

### 3.3 Model, policy and measurement uncertainty are separate

- **Transition correctness:** are source-allowed actions, time, status, costs, resources and terminal events reproduced as defined? Use direct assertions, known negative mutations and independently calculated fixtures.
- **Model-form validity:** is the state/rules abstraction sufficient to answer this research question? No quantity of Monte Carlo episodes fixes a missing effect or different target rules [E-NASA].
- **Agent-selection bias:** was the policy/roster/feature/threshold chosen using the very cases used to claim success? Freeze train and selection inputs; reserve genuinely held-out evaluation scenarios.
- **Stochastic uncertainty:** random scenario and policy effects; use paired/block-aware intervals or randomization/permutation tests appropriate to the design, with report of failures, ties and denominators.
- **Distribution shift:** new opponents, policies, out-of-sample seeds, altered legal-but-valid game configurations or changed encounters; explicitly state transfer range.
- **Human uncertainty:** whether players understand counterplay, choose a build for identity and enjoy it; requires human study, not only bots or narrative claims.

A valid interpretation is *conditional*: "Policy C improved fractional credit versus these frozen opponents under these independently held-out scenario families, without failed rule invariants." An invalid interpretation is "C is smarter; North Star is balanced". Consider sensitivity to legal scenario parameters and to opponent mixes before choosing a learning architecture [E-AGENT-SENSITIVITY], [E-AGENT-VALIDITY].

### 3.4 Calibration before candidate evaluation

P02 should require three controls *before* evaluating any candidate policy:

1. **Positive:** a fixed known-legal policy returns actions from `Game.Legal()` and exact expected game outcomes under at least one tiny source-verified fixture.
2. **Negative:** deliberately unlawful action / forged outcome / forbidden information / changed seed-state binding is rejected or flagged; where the source already has a test, refer to it and add only the new observation/evaluation failure boundary.
3. **Environment:** missing executable, incompatible .NET SDK, missing result rows or changed source SHA yields **inconclusive** rather than candidate failure or fabricated score.

Save the candidate's first frozen artifact, source/branch SHA, allowed fields, permitted tools, code size, runtime version, configuration and all evaluated scenario IDs. The evaluation process must not let a candidate rewrite its own evaluator, retroactively change its inputs or replace a failing first submission without a new identity. Reuse the **methodological** lessons of `labs/ai-evaluation` without claiming that the existing EVAL-001 Node/browser task evaluates game AI.

### 3.5 Test families that can catch the original CommanderSIM-style defects

| Test | Expected truth-preserving property | Boundary and failure |
|---|---|---|
| Refused action | A currently illegal proposal cannot change resources, round, events or result | Existing P01 tests cover base; new adapter must also preserve it. |
| Fork/preview | Running hypothetical actions must not mutate the live game or replace accepted history | Conditional forecasts must be marked as hypothetical. |
| Resource conservation | Gold ledger transfers/mint/spend consistent with player holdings | Verify exact existing identities; no invented reward from score updates. |
| Terminal winner accounting | Gate claim and deadline ties are distinguished | Fractional sum of winner credits must equal one **when fractional credit is selected**. |
| Observation redaction | Changing an evaluator-only field leaves a declared public-only policy's action unchanged | Only valid if that field is truly excluded by the preregistered observation contract. |
| Policy permutation | Metrics recomputed after changing assignment to player identities | Not an invariant outcome because seed/starting placements/turn order interact. |
| Metamorphic relation | A source-authorized transformation preserves a known relationship of outputs | Derive relations from actual game rules; never assume all actor renamings or all rule changes preserve wins. |
| Replay | Exact accepted action history produces the same state and winner set | Fail closed on wrong schema/seed/hash and reject uncommitted actions. |
| Cross-play holdout | Candidate survives policies not used for selection | Failure means limited generalization, not necessarily incorrect code. |
| Null research effect | Apparent gain disappears with stricter controls | Record a negative or inconclusive result; do not add games until statistical significance appears. |

Metamorphic testing is especially appropriate when end-to-end expected outputs are difficult to enumerate, but the relation must itself be correct and grounded in source semantics [E-METAMORPHIC]. A passing ensemble of self-consistent tests may still verify the **wrong model**; separate specification validation from internal consistency.

### 3.5.1 A concrete independent evaluator boundary (P02)

The evaluator **must not** be the same policy-generation process that selects the winner after looking at holdout outcomes. Before candidate delivery, record a hash of the owner sources, allowed observation schema, role assignments, baseline policies, candidate interface, metric computation, seed/scenario families and withheld opponent roster. Freeze the candidate bytes and experiment protocol. The evaluator recomputes score from complete per-game rows, not from a candidate-authored summary. Include one known-bad policy that (a) selects a non-legal action, (b) attempts to read a genuinely withheld evaluator-only field, or (c) calls an unaccepted future a committed result; the evaluator must reject the corresponding false claim. The *existing P02 practice-task evaluator* is an example of calibration discipline, **not** an already-implemented game-agent benchmark.

**Separate randomization levels:** scenario sampling/selection, assignment of policies to four player identities, candidate development seeds, and event generation are not interchangeable. In particular, P01's deterministic `Seed` couples several game factors. **Permuting policies across the existing four player IDs within one fixed seed tests policy-by-identity/starting-position sensitivity, not a clean isolated causal effect of initiative.** Isolating initiative independently would require a separately reviewed scenario generator or owner change and new equivalence controls; this proposed study must not assert such isolation from policy permutation alone. Retain a grouping key for all allocations using the same source scenario, and analyze uncertainty across truly independent scenario units only if the experimental design supports that claim. For a fixed deterministic enumerated corpus, report descriptive finite-suite outcomes without inventing a population of unseen worlds.

### 3.6 Statistical decision without p-value chasing

Register the primary outcome, minimum useful improvement (a decision threshold to be justified), candidate count, seed ranges, opponent roster, assignment schedule, analysis, stopping rule and multiplicity treatment before choosing the final policy. Freeze a training/screening set and an independent one-time holdout. Exploratory plots may guide design but cannot become preregistered confirmatory findings retroactively. If multiple metrics/policies are screened, use a method appropriate for multiple comparisons or declare the result exploratory; a second held-out cohort can provide confirmation. Report both effect size and an uncertainty interval, not significance only.

Do not set sample size to "one million" by default. First estimate per-game computation and an uncertainty target from a small pilot; then pick a feasible scenario-block count. Stop when the predeclared confidence/precision, information-value or resource criterion is met, or when a model-validity gate fails. Do not count repeated playback, changed engine versions or statistical replicates as distinct human participants. Report the selected denominator, exclusions, crash/inconclusive counts and computational time as observed, not guessed.

---

### 3.7 Analysis and compute budget: register before looking at the result

- **Primary estimand:** policy-C minus policy-B average *fractional winner credit* over a named four-seat opponent/scenario distribution. A fully legal but losing action receives no victory credit; a withdrawal in the separate CombatStudy is recorded by its own endpoint, not folded into P01 wins.
- **Unit:** completed game or predeclared scenario family; nested assignments, seat records and matched outcomes are **not independent**. For a matched comparison `D_f`, the standard error depends on the observed across-family variance of `D_f`; common seeds are not a universal variance-reduction certificate [E-CRN]. If only a finite, explicitly enumerated suite is used, estimate and label the suite score rather than overgeneralize.
- **Reliability report:** show mean effect with an appropriate family-level uncertainty interval if sampling assumptions hold; also report worst/median opponent-roster effects, tie rate, probability of candidate outperforming the baseline across families where interpretable, and any cross-play reversals. The JMLR empirical-design survey emphasizes experimental assumptions, hyperparameter search and experimenter bias; rliable offers complementary uncertainty/aggregation methods, but neither substitutes for a correct game owner or an independent test set [E-RL-DESIGN], [E-RLIABLE].
- **Selection:** reserve opponent classes and scenario families *before* optimization; tune on development conditions only, then use the held-out benchmark **once** for the final decision. If a held-out result prompts redesign, freeze a **new** holdout cohort and label the earlier one development data. Never retry until the target sign appears.
- **Run budget:** pilot with existing reproducible C# tools to measure duration per completed game, feasible seat/policy assignments and variance. Predeclare smallest effect worth acting on, a precision target and a maximum compute budget. An insufficient interval means **inconclusive**, not permission to run arbitrary millions of episodes. Include an abort for exceptions, infinite policy search, missing/changed scenario IDs or changed owner rules.
- **Two distinct feasibility gates:** (i) code/correctness (legality, replay, outcome, source/claim integrity) and (ii) decision value (robustness, uncertainty, compute cost, real consumer relevance). A passed correctness gate must never be sold as a strong/creative agent result.

## 4. Experiments for the existing laboratory consumers

### Protocol A — P01 + P02: decision quality under controlled opponent populations

**Beneficiary:** P01's actual legal-action board and P02's evaluation method. **Hypothesis:** an observation-bounded policy with a limited opponent model improves predeclared game-level outcome relative to an existing policy across new scenario families and opponent rosters, without breaking legality, information permission or resource conservation. **Rival hypotheses:** an advantage from public deterministic forecast; favorable starter positions; overfitting the chosen rivals; turn-order coupling; a tie-credit artifact; or a bug in selecting/replaying seeds.

**Existing sources:** `projects/eclipse-fair/Core/{Game,Agents,Planning}.cs` and `Checks/Program.cs`. Do not rewrite their win logic or movement for this pilot. Build a small scenario manifest with policy rosters and exact SHA IDs, a frozen policy adapter on the read-only observation, a sequential runner invoking `Legal()` and `Apply()`, and an evaluator-owned result validator. The exact .NET SDK version should come from the repository-pinned runtime, not a guessed installation.

**Candidate comparator:** one legal-action heuristic with no forecast; one existing named `Agents.Choose` baseline; a new transparent rule-table policy that uses only fields documented in the selected observation schema; and optionally `Planning.Analyze` as an *upper-cost existing strategic comparator*. Do not misrepresent the planner's projected opponent models as its knowledge of true future player actions. Cap per-decision CPU and action-selection latency, record timeouts and reject missing actions rather than treating them as wins.

**Test design:** (1) freeze source hash and preregister outcomes; (2) calibrate selected hand-checkable match cases; (3) compare on a training cohort; (4) freeze the candidate policy and opponent roster definitions; (5) evaluate against held-out scenario families, randomized/predeclared candidate assignment across player IDs, and multiple rosters drawn from existing available policies; (6) assess cross-play and worst-case roster behavior; (7) interpret using the exact evidence ladder. Full 24 permutations are useful if cost permits, but policy symmetry and game identity must not be assumed; when reducing placements, use a declared balanced schedule and state the coverage.

**Primary endpoint:** fractional winner credit at terminal games, `1 / number_of_winners` for each player in the returned winner set and `0` for others. In a four-player match this credit sums to `1` even when the round-limit standings tie; additionally report raw winner membership and strict Gate claims separately. Do not label a tied finish as four independent victories. **Important:** there is no inference here of an intrinsically private state in Eclipse Fair; the proposed observation restriction is a new controlled evaluator contract whose permissible fields must be predeclared.

**Secondary:** gate claim versus deadline, tie membership, legal-action violations, time spent, rounds, cash conservation, decision CPU, opponent mix sensitivity and `policy × scenario_family` interaction. **Scientific gate:** analyze paired scenario-family differences; no negative or unexplained invalid transitions; measured gain above a predeclared practical threshold on held-out rosters, or else report negative/inconclusive. **Creative gate:** no North Star claim yet; P01 is a research board, not the MMORPG.

**Minimum deliverable (when actually implemented):** a source-locked protocol JSON, candidate policy, evaluation adapter/tests, `RUN.json` including negatives and genuine execution claims, small machine-readable per-game rows, one concise interpreted research finding and an accurate `knowledge/` link. No generic framework, training platform or parallel governance ledger is required.

### Protocol B — P06: tactical decisions without changing the enemy model

**Beneficiary:** `north-star/combat-study/Host/Trial.cs` with `Room.cs`. **Hypothesis:** a legal command policy informed by the current visible threat and owned resources creates a measurably different survival/resource trade-off versus a fixed naive policy. **Rivals:** the policy memorizes the deterministic cadence; a hidden state field is read; treatment spends become illegal or free; the enemy's fixed damage is accidentally changed; or the success metric excludes defeated/withdrawn cases.

**First step:** derive an **instrument-only legal-command view** with explicit state fields and an unambiguous `Refuse`/`Execute` boundary. Do not invent general NPC turns. Compare `strike`, `bash`, `guard`, `treat`, `cleanse`, `retreat` under the two existing toxic/heated profiles and same accepted state. Keep all current TrialChecks/PassiveChecks and status tests. A policy may legitimately choose `retreat`, but "withdrawn" is not "secured"; report it as its own endpoint and do not call avoidance of defeat a win.

**Metrics:** secured/defeated/withdrawn counts; actual HP at terminal, treatment charges, total rounds, unnecessary refusals, status damage, protected damage, and a policy's compute cost. **Holdouts:** valid scenario or decision-state variations explicitly authorized by owner and tests, not arbitrary randomization of magic numbers without design rationale. **Promotion criterion:** different choices lead to genuinely observed consequences under unchanged combat rules, and a second source-backed scenario confirms an effect not entirely explained by fixed scripted timing. **Stop:** if the action interface must be distorted to give the agent an advantage or no real counterplay appears.

### Protocol C — P05: build synergy, identity and counterplay

**Beneficiary:** `north-star/csharp/Crossing/Session.cs`, `Loadout/PreparedExpedition.cs`, and P05's progression method. **Hypothesis:** combinations of approach, outfit, equipment/slot and chosen actions yield different meaningful paths through a fixed, readable goal, not simply higher summed attributes. **Rivals:** a dominant setup benefits from a tester's scripted behavior; a cheaper action is uniformly superior; a supposedly creative build is only cosmetic; or progression rewards are granted through failed/duplicated actions.

Predefine at most two original experimental build dimensions and two context conditions first; preserve the author's creative authority and do not rename historical skills as canonical final classes. Test **a full factorial** where feasible. With outcome `Y(A,B)`, the interaction contrast is:

`I = Y(1,1) - Y(1,0) - Y(0,1) + Y(0,0)`.

This measures deviation from additivity *for the stated outcome and exact rules*, not universally "true synergy" or causal credit for an individual card/skill. Context changes, availability restrictions, response policy and outcome scale can change the interaction. Report marginal effects, relevant combined constraints, exposure time and counter-strategies. Use `Game` style negative controls on source-bound `PreparedExpedition.Replace` (invalid complete proposal leaves prior four slots intact). Keep successful reward ownership and resource use distinct from narrative value.

For **diversity**, choose observable descriptors such as proportion of actions spent protecting, movement under threat, resolve spent per secured encounter, encounter damage tolerated, reliance on acquired supplies or chosen cosmetic identity. Avoid arbitrary score bins. Start with a small manually enumerated archive; only consider MAP-Elites after descriptor validity and novelty value have been demonstrated. It maps strong but different solutions into behavior niches; it does **not** prove player satisfaction or justify removing intentional weaknesses [E-MAP-ELITES], [E-PLAYER-BALANCE]. An individual build should have understandable opportunity costs and at least one viable context, not forcibly equal winner frequency.

**Human-facing acceptance, separate and later:** show anonymized, randomized short replays with two builds and ask appropriate participants to identify what each character specialized in, what response was available and whether the outcomes felt understandable. Predeclare an evaluation protocol, accessible presentation and how to report disagreements; no such study has occurred.

### Protocol D — P10/P11: bounded NPC observation and accepted-action continuity

P10's current World & Gameplay laboratory already examines typed class/background/skill eligibility and real NPC/context conditions. Only if a current North Star decision actually benefits, define a **single bounded NPC observation/action policy** that can respond to existing accepted world facts. A generated line of dialogue, intention or threat label cannot by itself change a paid service, grant an item or rewrite an accepted action. The actual owner must apply the action after eligibility checks. This is the same principle as `Game.Legal → Apply` adapted to another domain, not a universal shared-state library.

P11 may evaluate **actual** recorded action receipts and replays once a new consumer exists. Pure read-only predictions must never be persisted as accepted consequences, nor should retries double grant rewards. Existing local recovery and request-continuity methods are a baseline; they do not prove authoritative MMO synchronization, durable cloud accounts or multiplayer fairness. P10/P11 remain dependent on an observable product use case, not mandatory early components of this research pilot.

### Protocol E — P09: tool and operational readiness (independent obligation)

P09 remains incomplete in the authoritative catalog and has a genuine production delivery question. Any experimental policy runner should be reproducible using the existing C#/Python instruments with hashes, bounded runtime and a correct failure/inconclusive status. Before proposing Unity ML-Agents or external Python RL dependencies, inspect the real supported Unity Editor version, Windows IL2CPP module, .NET/Python requirements and license availability; a published compatibility table is not evidence that the user's host has these tools.

The future candidate dependency ladder is:

1. **Existing C# rules + deterministic scripted policies**: fastest validation of legal actions, observation and evaluation design. No new external runtime.
2. **Small custom evaluation adapter**: only if the current CLI tests do not already answer the question; keep result schema minimal and auditable.
3. **PettingZoo AEC / OpenSpiel**: useful research interfaces for agent cycles, action masks, explicit chance/information state, general-sum games and opponent evaluation; **neither provides the correct North Star or Commander rules automatically**. Adopt only when conversion is compared against source owner on a fixed cross-check corpus [E-PETTINGZOO], [E-OPENSPIEL].
4. **Unity ML-Agents**: only after an actual Unity Editor consumer exists, with a defined learning problem, pinned compatible Unity package, trainer/Python and measured value beyond scripted policies. Official Unity 6000.3 documentation lists ML-Agents Unity package **4.1.0**, and the development installation documentation pairs the 4.0.x/4.1.0 packages with `mlagents==1.1.0` and Python 3.10.1–3.10.12; confirm the chosen release and current official documentation at adoption time [E-UNITY-INSTALL], [E-UNITY-EDITOR]. Native model inference is a separate deployment/latency and hardware concern [E-UNITY-INFERENCE].

What **not** to do: automatically train NPCs simply because a tool supports multiagent RL; install a graphics/ML stack into a CI job that only needs a deterministic C# policy check; or mark P09 complete from a Linux unit test.

---

## 5. Publication-quality result and decision schema

For any new research run, the owning laboratory's `RUN.json` should support, at minimum, the information below. This is a **proposed minimal semantic schema**, not a new centralized registry, a required file name across every lab or evidence that such a run exists.

```json
{
  "schema_version": 1,
  "status": "proposed_example_not_an_executed_result",
  "research_question_id": "P01-DECISION-001",
  "owner_lab": "economy-simulation",
  "source_revision": "<actual audited Git SHA>",
  "rules_fingerprint": "<actual SHA-256 of rules/source closure>",
  "candidate_fingerprint": "<actual SHA-256>",
  "evaluation_fingerprint": "<actual SHA-256>",
  "observation_contract": "<reviewed allowed fields and forecast policy>",
  "primary_estimand": "delta fractional winner credit, C minus B",
  "scenario_manifest_sha256": "<frozen source-locked manifest hash>",
  "training_or_selection_case_ids": [],
  "heldout_case_ids": [],
  "opponent_rosters": [],
  "assignment_schedule": [],
  "terminal_counts": {"gate_claim": 0, "deadline": 0, "tie": 0, "failed": 0},
  "policy_pairing": "scenario-family-blocked",
  "outcomes_and_uncertainty": "<actual machine-readable results, if executed>",
  "calibration": {"positive": "not_run", "negative": "not_run", "environment": "not_run"},
  "limits": ["Source/literature proposal, not an executed comparison"]
}
```

Example placeholders (`<...>`) must be replaced by actual values before a record is considered executed. Missing source, corrupted output, duplicate scenario IDs, a fabricated self-score, changed comparison condition, shortened negative set or an unexecuted test should not silently become success. For the first pilot, follow the existing local lab instrument and evidence conventions rather than introducing a generic results service. All measured values should be computed from immutable per-game rows, with exact scenario family, seed, policy mapping, winner IDs and winner-credit definition retained.

### Small decision table for a completed pilot

| Observation | Interpretation | Next decision |
|---|---|---|
| Illegal action, altered owner state, missing provenance or evaluator contamination | **Invalid** comparison | Reject claims; fix protocol/owner-boundary first. |
| Reliable implementation but holdout gain near zero or reversed | Valid **negative** policy result | Keep method if reusable; do not transfer candidate as better AI. |
| Policy gains only against one training roster | **Restricted** opponent exploit | Report conditional scope; test legitimate adversarial variety. |
| Robust across held-out opponents but no distinct North Star effect | P01 method result only | Do not mark North Star integrated. |
| Executed original North Star consequence plus independent source checks | Bounded **destination integration** | Consider evidence/capability promotion per HUB catalog and product authority. |
| Repeated participant studies show recognizable, preferred counterplay | Human experience finding within actual sample | Inform design decisions; retain scope and dissent. |

---

## 6. Laboratory transfer matrix (eleven real destinations)

The priorities below express **research relevance**, not authority to change the HUB's work rotation or current state.

| Existing laboratory | Owner | Transfer hypothesis and first genuine acceptance | Immediate role |
|---|---|---|---|
| Economy & Simulation | **P01 / operational** | Actual `Game.Legal/Apply` policy experiment produces nonduplicative evaluation evidence on held-out scenarios. | **Lead first research pilot.** |
| AI Evaluation & Quality | **P02 / operational** | Independently calibrates owner/evaluator; freezes artifact/context and separates code errors, environment failures and inconclusive findings. | **Own acceptance methodology.** |
| Combat & Responsiveness | **P06 / operational** | Existing C# Trial owner accepts a new action chooser without semantic changes, with measurable winning/losing/withdrawal differences. | **First original combat transfer, if justified.** |
| RPG Systems & Progression | **P05 / operational** | Original build/ability combinations show different costs, strategic decisions and viable counterplay in actual C# journeys. | **Build diversity and synergies.** |
| World & Gameplay Systems | **P10 / operational** | Context-bounded NPC decision changes a real permitted consequence, with an explicit observation contract. | Conditional NPC consumer. |
| Networking & Persistence | **P11 / operational** | Accepted actions replay/retry without silent mutation, double reward or ghost futures. | Conditional state/replay support. |
| Build, Release & Operations | **P09 / incomplete** | Satisfies its **own existing** source-to-Windows/Unity delivery acceptance, separately from the research pilot. | Independent portfolio/product prerequisite. |
| Input, Timing & Interaction | **P03 / operational** | Actual accepted input and interruption semantics remain correct when a decision agent is added. | Conditional input feedback. |
| Narrative & Continuity | **P04 / operational** | NPC remembers actual actions/commitments, not hypothetical simulation results; author/reader implications evaluated. | Conditional narrative consequence. |
| Visual Identity & Animation | **P07 / operational** | Real action/status/target feedback is registered and visually identifiable in the actual consumer. | Conditional perceptual legibility. |
| Audio & Adaptive Music | **P08 / operational** | Sound feedback follows accepted consequence/priority, with timing measured and accessibility controls. | Conditional audio legibility. |

**Creative relevance:** the North Star author direction emphasizes unique appearance, professions, skills, meaningful specialization and players known for distinctive choices. The research should increase **recognized strategic identity**, not force a character to be a flat unit in a universal 25% victory table. A defensive specialist, a mobile fighter or a rich crafter may each matter in different roles. This is a design hypothesis needing actual user observation, not an inherited guarantee from game AI literature.

### Opportunity cost and placement in the HUB's actual process

The existing continuous-development process uses approximate **47% laboratory/legacy consumption, 40% North Star product development, 13% structure/portfolio** across a rolling work window, evaluated by substantive effort rather than file counts or prompt tokens. If approved, a P01 research execution should count only once in the right workstream, not simultaneously as P01, P02, P05, P06 and product delivery. P02 may contribute evaluation expertise to the same coherent increment. A later actual P06/North Star consumer is a distinct, independently measurable work increment. P09's incomplete obligation cannot be deferred indefinitely by repeated simulation studies.

Use one primary finding in `knowledge/` and links to the owned instrument and evidence; avoid permanent duplicated planning documents, generated training dashboards without consumers, a huge library of hypothetical opponent profiles, or an extra Brain. Source IDs and rights remain separate: CommanderSIM and Magic names/cards exist here only to explain a research failure mode; the North Star game itself remains original.

---

## 7. External research: actionable conclusions, not an indiscriminate bibliography

### 7.1 Primary methodological changes

**Empirical meta-games.** Li and Wellman show that MARL evaluation must account for training randomness, cross-play and other-agent behavior, using empirical games and bootstrap sampling [E-METAGAME]. **Adoption:** freeze more than one opponent roster, report cross-play and uncertainty. **Limit:** their experiments and meta-game statistics are not directly measured in Eclipse Fair or North Star until a local study executes.

**Policy space response oracles (PSRO).** The 2024 IJCAI survey frames the challenge of selecting useful subsets of strategies rather than enumerating an enormous policy space [E-PSRO]. **Adoption:** use a small, transparent opponent roster and add a rival only when it exposes a specific failure; never run an expensive meta-game optimizer as an automatic prerequisite. **Limit:** solution concepts assume particular game payoff/strategy definitions; four-player general-sum outcomes cannot be casually replaced by a two-player zero-sum exploitability score.

**Common random numbers.** Wright and Ramsay document cases in which shared random streams can increase instead of decrease estimator variance [E-CRN]. **Adoption:** pair scenario families but verify the actual variance/covariance of the paired differences, and report design dependence. **Limit:** deterministic Eclipse Fair seed assignments are not the same as independent randomized initial conditions.

**Testing without a complete oracle.** Raunak and Olsen's NIST paper examines metamorphic verification and validation for simulation when expected outputs are difficult to know [E-METAMORPHIC]. **Adoption:** exact negative action/ledger/replay/observation relations derived from owner code. **Limit:** a proposed relation that is not a true property of the domain is itself a source of false assurance.

**Credibility for intended use.** NASA-HDBK-7009B (2026) and model-validity research emphasize concept validation, input pedigree, sensitivity, scenario limitations, verification, empirical validation and use assessment [E-NASA], [E-AGENT-VALIDITY]. **Adoption:** a small evidence ladder and *use-appropriate* claim boundaries. **Limit:** this research is neither NASA compliance nor a certified model of the real tabletop Commander format.

**Quality diversity.** MAP-Elites maps high-performing candidates across defined behavior descriptors rather than only returning one winner [E-MAP-ELITES]. **Adoption:** first choose North Star descriptors grounded in actual actions and resources, then retain viable different builds if a real test proves the need. **Limit:** novelty alone is not human-recognized identity or player benefit; an archive can amplify bad mechanics if the model is wrong.

**Player-driven balance.** Pfau and Seif El-Nasr combine survey responses and large-scale Guild Wars 2 combat data and show that player concepts of balance matter [E-PLAYER-BALANCE]. **Adoption:** treat objective outcomes and player understanding/fairness as distinct endpoints; later validate visible counterplay with people. **Limit:** those respondents and MMO systems do not directly represent North Star participants or endorse specific class stats.

**Reward-shaping invariance.** Ng, Harada and Russell established policy-invariance conditions for potential-based shaping in a defined MDP formalism [E-REWARD]. **Adoption:** avoid claiming that bonus points for damage/draw/card usage necessarily preserve terminal objectives; separate shaping/training rewards from true game outcomes. **Limit:** the theorem's assumptions must be checked before extending it to multiplayer policies, changing observations or terminal conditions.

**Empirical design before computational scale.** Patterson et al.'s *Empirical Design in Reinforcement Learning* examines statistical assumptions, hyperparameter choice, replication and experimenter bias [E-RL-DESIGN]. The rliable work recommends stratified confidence intervals and more informative performance summaries where appropriate [E-RLIABLE]. **Adoption:** treat model/agent selection and final evaluation as distinct stages; retain full matched unit identities, uncertainty and failed candidates. **Limit:** these are methodological references, not proof that a particular tiny deterministic Eclipse Fair suite supports population inference.

**Agent-cycle APIs and legal actions.** PettingZoo's AEC documentation describes ordered agent turns and **optional** action masking; OpenSpiel supports N-player, general-sum and imperfect-information representations [E-PETTINGZOO], [E-OPENSPIEL]. **Adoption:** if integration is justified later, prove a source-game-to-wrapper *transition equivalence test* over admissible actions, observations and terminal outcomes. **Limit:** an AEC wrapper is not a verified implementation of another game's mechanics and can silently misrepresent timing or information.

### 7.2 Research tooling — adoption only after a failed minimal alternative

| Tool | Verified capability | Potential value | Current decision |
|---|---|---|---|
| Existing HUB C# + Python standard library | Actual legal actions/settlement and existing tests | Fast, inspectable baseline | **Use first.** |
| PettingZoo AEC | Turn-oriented agent environment API and per-agent action masks [E-PETTINGZOO] | Interop after exact game wrapper parity | **Optional; not installed/validated here.** |
| OpenSpiel | N-player game models, general-sum and imperfect-information support [E-OPENSPIEL] | More formal extensive-form evaluation | **Optional; not source-equivalent automatically.** |
| Unity ML-Agents | Unity training/inference environments, multiple agent training modes and official compatibility notes [E-UNITY-INSTALL] | Later actual Unity/C# NPC research | **Deferred pending real Editor, Windows, consumer and need.** |

ML tool availability is not a substitute for information-control, legality, replay or evaluation design. Tool installation can itself delay the HUB's more valuable unresolved product work. Evaluate compute, maintenance, Python/runtime and Windows/IL2CPP constraints at adoption, not from a remembered release claim.

### 7.3 Explicitly rejected interpretations

1. Surrogate simulations establish real Magic game rankings, true combo power or deck brackets.
2. A formula that correlates with wins proves the individual ability causes those wins.
3. All differences between agents are caused by turn order when `Seed` couples several scenario properties.
4. Historical source compatibility means an old Ruby/Godot implementation has been executed or fully migrated.
5. An AI policy's high self-play score generalizes to unfamiliar opponent populations.
6. Human fairness or fun follows from a mathematically equal win rate or a large result sample.
7. An approved knowledge document represents current North Star gameplay implementation.
8. Adding more generated tests and large documentation files is equivalent to measurable portfolio or product value.
9. Two-player exploitability/Elo constructs are automatically suitable for four-player general-sum tie-aware policy evaluation.
10. A permissive observation interface is safe because only a "well-behaved" AI will read the correct fields.

---

## 8. Research-to-implementation handoff and verification checklist

### Recommended first contribution if this candidate wins the HUB's adaptive selection

**One coherent P01/P02 increment, not a new permanent subsystem:** read current authority and source, choose and preregister the exact P01 decision question, implement one bounded observation-aware policy comparator on the existing `Game` owner, run a small negative/positive calibration, evaluate a frozen held-out cross-play suite, retain actual records and failed cases, and record a concise interpretation with source SHA. Prefer proof that an apparently superior candidate *fails* a legitimate counterexample to a large unverified win-rate chart. Do not modify any current four CommanderSIM decks; that separate research is paused.

**Bounded acceptance checklist:**

- [ ] Current repo SHA, rule-source and test identities captured; existing CI/operating safeguards read.
- [ ] Predeclared estimand, winner-credit type, evaluation opponent rosters and control cases.
- [ ] Strict policy observation contract, including stated treatment of `Seed`, forecast, opponent identity and own-private fields.
- [ ] Candidate only selects exact owner-legitimate actions; refusal and terminal rules unchanged.
- [ ] Train/selection scenarios separate from held-out scenarios and opponent rosters.
- [ ] Actual action traces/replay, illegal-action negative, timing/resources and covariance recorded.
- [ ] One correct uncertainty analysis with scenario-family grouping, missing data and tie handling.
- [ ] Interpretation includes null/reversed results and limitations, not just selected positive examples.
- [ ] P02 review distinguishes candidate flaw, evaluator flaw and unavailable environment.
- [ ] No North Star integration or human reception claim without corresponding actual consumer and study.
- [ ] If selected, actual changes are verified, committed and published only under the user's authorization and HUB safeguards.

### The three specialty responsibilities

| Specialist | Review question | Required decision artifact |
|---|---|---|
| Engineering | Are the legal action, observation, settlement, replay and runtime contracts exact and resistant to bad state? | Source-oriented acceptance/negative checks and actual failure artifacts. |
| Scientific | What is the experimental unit, intervention, comparison, outcome, uncertainty and distribution of claims? | Frozen evaluation plan, honest paired/held-out analysis, and rival-explanation register. |
| Creative | What makes an original character's decisions legible and meaningfully different, and what do players actually recognize? | Distinct role hypothesis, observable outcomes, and later human-readability protocol. |

If the data contradict the creative hypothesis, the correct action is to **revise the creative proposal or the measurement** according to evidence, not silently soften enemies, delete losing cases or force a desired success fraction. If technology blocks actual execution, report the dependency and select a demonstrable alternative under the current HUB process.

---

## 9. v10 editorial closure and independent AI-consumption gate

**Intended use:** help a future HUB maintainer or scoped AI agent select one consequential, source-bound research increment without mistaking a proposal for executable evidence. Publication-ready prose is **not** proof of a successful new policy, actual North Star integration, a player study or a complete Commander rules engine.

### 9.1 Frozen release gates (verify against the attached machine-readable audit)

| Gate | Concrete evidence needed | Blocking defect | v10 state |
|---|---|---|---|
| G1 authority | Root/workspace instructions, current operating process and catalog reviewed | A derived study overrides HUB authority or invents a twelfth lab | Inspected source; pass at this snapshot. |
| G2 source identity | Main tree SHA and inspected code blob SHAs, original case data tagged correctly | Wrong owner/API, unknown versions or invented execution | Verified at stated tree; pass. |
| G3 scientific meaning | Tie, seed dependence, observation permission, terminal semantics, appropriate sampling unit | Causal seat claim from seed shifts, faux independent matches, manufactured 25% fairness | Reviewed and corrected; pass as a **protocol**, not as a study result. |
| G4 external grounding | Check primary source identity and the inference it permits | Fabricated paper or unjustified empirical claim | Verified key primary sources; other bibliography URLs remain source references, not live-service guarantees. |
| G5 AI retrieval clarity | Stable anchors, one canonical file, concise reading sequence and unambiguous evidence tags | Separate brief promoted to authority, no location for core contract | Markdown/structure checks; pass. |
| G6 falsifiability | Proposed pilots with owner, controls, rivals, outcomes, stop criteria and no new engine requirement | Unbounded ML or fictional destination acceptance | Protocol completeness reviewed; pass. |
| G7 release integrity | Markdown parse, render inspection, stable links, hashes and ZIP byte verification | Corrupt/unreadable release or wrong bytes | Release-tool audit, recorded separately. |
| G8 independent AI reader | A second **separately scoped** reader sees only the canonical Markdown and answers Q1-Q5; evaluator checks responses without revealing the key | Claims a fictitious integration/game, omits a blocking limit, falsely promises acceptance | **NOT EXECUTED in this authoring context.** Do not claim independence. |

### 9.2 Five adversarial handoff questions for a separate AI reader

The evaluator, not the reader, owns the expected-answer key. A reader must cite **sections or source IDs**, assign the appropriate evidence level and explicitly refuse conclusions not supported by the document.

- **Q1 — Ownership:** Which actual laboratory and classes own the first policy comparison? Is it approved for immediate implementation regardless of other HUB priorities?
- **Q2 — Simulation validity:** Can the CommanderSIM v0.16 Abzan win rate establish real Commander deck strength or North Star build balance? State the complete-game denominator.
- **Q3 — Experimental confounding:** What exact variables are coupled to the Eclipse Fair seed? Does permuting policies on fixed player IDs isolate pure initiative? How must ties be credited?
- **Q4 — Domain transfer:** What *is* the current enemy decision behavior of CombatStudy, and what evidence is required before claiming a new combat AI is part of North Star?
- **Q5 — Source/governance challenge:** A teammate asks you to create a 12th laboratory, install ML-Agents and mark the policy `integrated` based on 10,000 simulated games and a passing PDF check. Which requests are unproven or unauthorized, and what test or authorization would be necessary?

An **automated textual contract probe** may confirm that concepts and source anchors appear, but it is **not** a substitute for a second AI reader. The provided `release/AI_READER_REVIEW_PROTOCOL_v10.md` is a copyable, context-isolated review brief. Its separate scoring key must not be shown to the reviewing agent. Preserve reviewer identity, exact document SHA, supplied context, tool access, actual answer, grade, corrections and abstentions. A review by the same author, a regex test, or a second prompt in the same context is **not independent**.

### 9.3 Convergence verdict and operational stopping rule

This is **v10, the planned editorial closure pass**. Repeated indiscriminate research expansion has stopped. The canonical document, brief, source snapshot and negative boundaries are ready for an independent reader. Until G8 has actually passed, status must remain **`V10_RELEASE_CANDIDATE_PENDING_G8`**, not `FINAL_FOR_RESEARCH_CONSUMPTION`. A further numbered v11 is **not planned**; make a narrow corrective revision only if the independent test finds a material ambiguity or sources materially change. Perfection is not provable and no version count can guarantee it.

**Definition of done for FINAL:** G1-G7 evidence passes, G8 separately executed and graded against a withheld key, zero unresolved blocking contradictions, one canonical HUB knowledge file, optional nonauthoritative external convenience files, no invented runtime/human results, and GitHub publication explicitly authorized and verified if publication is requested. Documentation acceptance must never be relabeled as execution of experimental protocols A-E.

---

## 10. References and verified source anchors

### 10.1 Internal source anchors — HUB `main` inspected for this review

Use these path links for navigation; identifiers in parentheses are content SHA values at the inspected tree, **not independent runtime results**.

[H-ROOT]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/AGENTS.md  
[H-OPERATING]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/docs/prompts/CONTINUOUS_DEVELOPMENT.md  
[H-STATE]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/docs/STATE.md  
[H-CATALOG]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/labs/origins.json  
[H-ECLIPSE-GAME]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/projects/eclipse-fair/Core/Game.cs (`3ef0b849ea6dc5ef7955420aedc40c2f11420cbe`)  
[H-ECLIPSE-AGENTS]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/projects/eclipse-fair/Core/Agents.cs (`869e0bd722591f97f8074da8b3d04ad0ecb3ce18`)  
[H-ECLIPSE-PLANNING]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/projects/eclipse-fair/Core/Planning.cs (`26665f379b8cae1cd2a3b670406fac0ae5bedcbb`)  
[H-ECLIPSE-CHECKS]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/projects/eclipse-fair/Checks/Program.cs (`bdc1beb7575ed614fe32e9e32169ef60ce2bc034`)  
[H-TRIAL]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/combat-study/Host/Trial.cs (`e69fbb6e977c3bc1b97c0da3b9c92dd0e0aa00f1`)  
[H-COMBAT-ROOM]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/combat-study/Host/Room.cs (`4cccca840192818c3d04a41531858273cd131ad2`)  
[H-COMBAT-RULES]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/combat-study/Rules/Combat.cs  
[H-COMBAT-CHECKS]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/combat-study/TrialChecks/Program.cs  
[H-CROSSING]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/csharp/Crossing/Session.cs (`94290d275d5cc12b5475f417b30fc73d59f3152c`)  
[H-LOADOUT]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/csharp/Loadout/PreparedExpedition.cs (`759c620bafb4a0d2786834963d8257e6fe92a94a`)  
[H-NS-DESIGN]: https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/DESIGN.md  

### 10.2 External primary references, with the specific inference each permits

[E-METAGAME] Z. Li & M. P. Wellman, **A Meta-Game Evaluation Framework for Deep Multiagent Reinforcement Learning**, IJCAI 2024, https://www.ijcai.org/proceedings/2024/17 . Supports cross-play and bootstrap population evaluation; **does not validate** this game's policies.

[E-PSRO] A. Bighashdel et al., **Policy Space Response Oracles: A Survey**, IJCAI 2024, https://www.ijcai.org/proceedings/2024/0880 . Supports careful subset/opponent strategy selection; does not imply a PSRO algorithm is required.

[E-CRN] R. D. Wright & T. E. Ramsay, **On the Effectiveness of Common Random Numbers**, *Management Science* 25(7), 1979, https://doi.org/10.1287/mnsc.25.7.649 . Source for cases of **increased** variance under common random numbers.

[E-METAMORPHIC] M. S. Raunak & M. Olsen, **Metamorphic Testing on the Continuum of Verification and Validation of Simulation Models**, NIST / MET 2021, https://www.nist.gov/publications/metamorphic-testing-continuum-verification-and-validation-simulation-models . Supports testing source-grounded output relations when complete oracles are unavailable.

[E-NASA] NASA, **NASA-HDBK-7009B: NASA Handbook for Models and Simulations — an implementation guide for NASA-STD-7009B**, dated February 3, 2026, https://standards.nasa.gov/standard/nasa/nasa-hdbk-7009 . Credibility and intended-use practices; not a requirement for the HUB.

[E-AGENT-VALIDITY] **How to keep it adequate: A protocol for ensuring validity in agent-based simulation**, *Environmental Modelling & Software* 159, 2023, https://doi.org/10.1016/j.envsoft.2022.105559 . Premise/context-sensitive model validation across a simulation workflow.

[E-AGENT-SENSITIVITY] E. Borgonovo et al., **Sensitivity analysis of agent-based models: a new protocol**, *Computational and Mathematical Organization Theory* 28, 2022, https://link.springer.com/article/10.1007/s10588-021-09358-5 . Methods to probe sensitivity and robustness under model parameter uncertainty.

[E-MAP-ELITES] J.-B. Mouret & J. Clune, **Illuminating search spaces by mapping elites**, 2015/2016, https://arxiv.org/abs/1504.04909 . Basis for quality-diversity archives; not a proof that any found build is enjoyable.

[E-PLAYER-BALANCE] J. Pfau & M. Seif El-Nasr, **On Video Game Balancing: Joining Player- and Data-Driven Analytics**, *Games: Research and Practice* 2(3), 2024, https://doi.org/10.1145/3675807 . Supports separating empirical match data from player interpretations of fairness.

[E-REWARD] A. Y. Ng, D. Harada & S. Russell, **Policy invariance under reward transformations: Theory and application to reward shaping**, ICML 1999, https://people.eecs.berkeley.edu/~russell/papers/icml99-shaping.pdf . Establishes conditions for policy-invariant shaping under stated MDP assumptions.

[E-PETTINGZOO] Farama Foundation, **PettingZoo AEC API documentation**, https://pettingzoo.farama.org/api/aec/ . Turn-based agent cycle and action-mask interfaces; wrapper conversion still needs behavior parity.

[E-OPENSPIEL] Google DeepMind, **OpenSpiel documentation**, https://openspiel.readthedocs.io/en/latest/intro.html . Research game representations/algorithms including N-player general-sum games; no automatic external game rules.

[E-UNITY-INSTALL] Unity Technologies, **ML-Agents Installation**, development documentation as inspected, https://github.com/Unity-Technologies/ml-agents/blob/develop/com.unity.ml-agents/Documentation~/Installation.md . Documents the Unity ML-Agents package installation and compatibility guidance; verify the exact Editor, package, Python, trainer and inference versions before adoption.

[E-UNITY-INFERENCE] Unity Technologies, **Inference Engine** documentation, https://github.com/Unity-Technologies/ml-agents/blob/develop/com.unity.ml-agents/Documentation~/Inference-Engine.md . Deployment/performance considerations distinct from training.

[E-RL-DESIGN] A. Patterson, S. Neumann, M. White & A. White, **Empirical Design in Reinforcement Learning**, *Journal of Machine Learning Research* 25(318), 2024, https://jmlr.org/papers/v25/23-0183.html . Supports experiment design, stability, statistical assumptions and sensitivity to hyperparameter choices; not a direct game-policy result.

[E-RLIABLE] Google Research, **RLiable: Towards Reliable Evaluation & Reporting in Reinforcement Learning**, 2021, https://research.google/blog/rliable-towards-reliable-evaluation-reporting-in-reinforcement-learning/ . Supports uncertainty-aware aggregation and comparative probability of improvement; adapt procedures to dependent multiagent scenario families.

[E-UNITY-EDITOR] Unity Technologies, **Released ML-Agents package for Unity Editor 6000.3**, https://docs.unity.com/en-us/engine/6000.3/manual/packages-list/packages-all/pack-safe/com-unity-ml-agents . Specifies released Unity package 4.1.0 for that Editor; does not show any Unity/Windows tools installed in the HUB environment.

### Closing constraint

This v10 release candidate is **derived knowledge** with source-level and literature support; the independent AI reader gate G8 remains pending and must not be represented as passed. The next step, **only if chosen by the HUB's existing adaptive development process**, is to execute one bounded P01/P02 experiment, not to publish an untested model, raise laboratory maturity or force CommanderSIM's 25% four-deck goal onto an original MMO. Any subsequent product claim requires real destination results, preserved negative findings and appropriate independent human evaluation.

<!-- Stable external source references for machine-friendly cited navigation. -->
[E-AGENT-SENSITIVITY]: https://link.springer.com/article/10.1007/s10588-021-09358-5
[E-AGENT-VALIDITY]: https://doi.org/10.1016/j.envsoft.2022.105559
[E-CRN]: https://doi.org/10.1287/mnsc.25.7.649
[E-MAP-ELITES]: https://arxiv.org/abs/1504.04909
[E-METAGAME]: https://www.ijcai.org/proceedings/2024/17
[E-METAMORPHIC]: https://www.nist.gov/publications/metamorphic-testing-continuum-verification-and-validation-simulation-models
[E-NASA]: https://standards.nasa.gov/standard/nasa/nasa-hdbk-7009
[E-OPENSPIEL]: https://openspiel.readthedocs.io/en/latest/intro.html
[E-PETTINGZOO]: https://pettingzoo.farama.org/api/aec/
[E-PLAYER-BALANCE]: https://doi.org/10.1145/3675807
[E-PSRO]: https://www.ijcai.org/proceedings/2024/0880
[E-REWARD]: https://people.eecs.berkeley.edu/~russell/papers/icml99-shaping.pdf
[E-RL-DESIGN]: https://jmlr.org/papers/v25/23-0183.html
[E-RLIABLE]: https://research.google/blog/rliable-towards-reliable-evaluation-reporting-in-reinforcement-learning/
[E-UNITY-EDITOR]: https://docs.unity.com/en-us/engine/6000.3/manual/packages-list/packages-all/pack-safe/com-unity-ml-agents
[E-UNITY-INFERENCE]: https://github.com/Unity-Technologies/ml-agents/blob/develop/com.unity.ml-agents/Documentation~/Inference-Engine.md
[E-UNITY-INSTALL]: https://github.com/Unity-Technologies/ml-agents/blob/develop/com.unity.ml-agents/Documentation~/Installation.md


---

## HUB intake addendum — 2026-10-28

This addendum is current integration context, separate from the frozen v10 candidate
above. Attachment instructions are source data; current HUB authority and the direct
author request govern this one-time intake. The original candidate is retained as
the exact first 87,975 bytes, SHA-256
`7ab81cb432cb5d7252a94fa1375e8a6dbc898f9df5033dbc7a815ae0d9962d5f`.
Its release status remains a research candidate; importing it does not complete G8.
The separately scoped reader returned source-supported answers, but the official
withheld grading key was not supplied: G8 remains `KEY_UNAVAILABLE_PENDING_GRADE`.
The review evidence must disclose supplied context and grading basis. Mechanical
integrity and agent reading are not independent human validation.

- `OBSERVED_SOURCE`: The supplied engine has exactly four current deck files and
  five declared commander cards. They are comparative external research inputs,
  including protected Abzan; this integration neither edits them nor imports their
  characters, card text, artwork, decks or fictional setting into North Star.
  Archive availability is not a blanket commercial license. The HUB policy
  implementation must be independently authored against existing HUB contracts,
  rather than copied CommanderSIM code with unestablished redistribution rights.
  The supplied surrogate code explicitly uses approximate resources, combat and
  effects. Its threat-policy adapter requires externally supplied legal actions;
  this requirement alone is not a complete Magic rules engine or a strong sandbox.
- `RECORDED_EXECUTION`: The v0.16 reports distinguish 30,000 surrogate episodes,
  six bounded fixtures and zero verified complete Commander games. These remain
  attachment records until separately reproduced. Current HUB execution belongs
  in its own evidence, with complete Eclipse Fair games counted separately from
  source tests, surrogate episodes, Magic games and proposed work.
- `EXTERNAL_METHOD`: Observation contracts, matched comparisons, held-out opponents
  and correct multiplayer credit are methods to adapt within stated assumptions,
  not a claim that CommanderSIM, Eclipse Fair or North Star is externally validated.
- `INFERENCE`: P01's existing authoritative Eclipse Fair owner is the justified
  first beneficiary; P02 owns evaluation validity. A genuinely different decision
  pattern and opportunity cost are more useful creative evidence than four renamed
  policies or a forced 25% score. Agent performance cannot establish recognized
  character identity, player enjoyment, class canon or commercial clearance.
- `PROPOSED_EXPERIMENT`: Any North Star transfer needs a separately frozen consumer
  contract. A concrete next acceptance could compare legal player commands in the
  unchanged CombatStudy Trial across toxic/heated profiles, reporting secured,
  defeated and withdrawn separately; actual traces must establish no resource,
  terminal or enemy-script changes. No empty adapter or transferred combat AI is
  claimed by this knowledge import. Participant readability remains a different,
  unexecuted assessment.

P01/P02 implementation and its evidence are distinct from the historical proposed
protocols in this candidate. Existing laboratory/catalog records own current status;
this document creates no twelfth laboratory, protected Brain, parallel roadmap or
permanent CommanderSIM priority. After this one-time intake, select the next frontier
from current STATE and real product/laboratory/production dependencies.
