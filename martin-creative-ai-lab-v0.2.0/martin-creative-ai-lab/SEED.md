# SEED — Martin Creative AI Lab

**Version:** 0.16.0
**Data-base:** 10 de outubro de 2026  
**Autor e responsável pelo portfólio:** Martin Melcop Neto  
**Working language:** English for new documentation, plans, code comments, UI, and reports. Preserve original creative titles and historical source languages.
**Current state:** P11 Project Rooms 0.3.0 adds a private operator backup/inspect/restore workflow for live SQLite/WAL data. New-file recovery preserves projects, authorship, identities and attempts; actual Chromium continuation is executed. P03/P08 two-stage music and other destinations remain preserved; human use and commercial quality remain unverified.

> Construir um laboratório autoral em Git que transforma ideias, obras e experimentos em produtos pequenos, sistemas reutilizáveis e evidências técnicas verificáveis. A IA participa da criação e execução; Martin desenvolve sua capacidade de especificar, compreender, selecionar, corrigir, validar e explicar os resultados.

### Navegação

| Para encontrar | Seções |
|---|---|
| Iniciar e entender a direção | [0 — sessão](#0-como-começar-uma-sessão), [1 — mandato](#1-mandato-do-autor-tudo-pode-evoluir), [2 — portfólio](#2-tese-de-portfólio) |
| Perfil, fontes e projetos | [3 — Martin](#3-base-profissional-de-martin), [4 — fontes](#4-fontes-confiança-e-limites-deste-levantamento), [5 — inventário](#5-inventário-de-projetos-como-matéria-prima) |
| Organização e aprendizado entre projetos | [6 — arquitetura](#6-arquitetura-do-laboratório), [7 — transferências](#7-como-os-projetos-aprendem-entre-si), [8 — prioridades](#8-decidir-em-que-trabalhar) |
| Evidências, agentes, avaliação e QA | [9 — estados](#9-modelo-de-estados-e-evidências), [10 — IA](#10-operação-com-ia), [11 — evaluation](#11-protocolo-de-ai-evaluation), [12 — QA](#12-qa-e-engenharia-proporcionais) |
| Dados, mídias e tecnologia | [13 — simulação](#13-simulação-economia-e-dados), [14 — criação](#14-narrativa-imagens-áudio-e-adaptação), [15 — stack](#15-stack-e-migração), [16 — Git](#16-git-assets-e-publicação) |
| Medidas, cases, fases e autonomia | [17 — métricas](#17-medir-o-trabalho-sem-inventar-produtividade), [18 — cases](#18-transformar-trabalho-em-portfólio), [19 — roadmap](#19-roadmap-por-gates), [20 — aprendizado](#20-aprendizado-de-martin) |
| Recuperação de fontes e evolução | [28 — repositórios antigos](#28-recuperação-dos-repositórios-antigos--v020) |
| Operação posterior | [21 — riscos](#21-riscos-e-gatilhos-de-replanejamento), [22 — modelos](#22-modelos-de-registro), [23 — prompts](#23-prompts-de-continuidade), [24 — tarefas](#24-primeiras-tarefas-propostas), [25 — sucesso](#25-definição-de-sucesso) |

## 0. Como começar uma sessão

Leia esta seção, `docs/STATE.md`, `registry/projects.json` e as instruções de `AGENTS.md`. Depois consulte somente os capítulos desta seed e os arquivos do projeto necessários à tarefa. Não carregue todos os manuscritos, imagens e logs em toda sessão.

Se apenas este arquivo estiver disponível, ele é suficiente para iniciar a Fase 0 descrita na seção 19. Os arquivos auxiliares são uma estrutura recomendada, não uma dependência para compreender a proposta.

### Contrato inicial com o agente

1. Identifique a fase solicitada, o projeto e o entregável verificável.
2. Inspecione o estado real dos arquivos e a capacidade do ambiente antes de prometer execução.
3. Diferencie fatos profissionais, legado recuperado, artefatos inspecionados, hipóteses e trabalho proposto.
4. Escolha uma unidade de trabalho que consiga encerrar com evidência ou uma limitação documentada.
5. Produza ou altere os arquivos necessários; explicação no chat não substitui entregável solicitado.
6. Execute as verificações proporcionais ao que mudou. Registre o que não conseguiu executar.
7. Atualize o estado, as decisões relevantes e a próxima ação concreta.
8. Resuma o resultado em linguagem simples: mudança, motivo, evidência, limites e próximo passo.

**Nunca declarar como realizado o que foi apenas planejado, gerado em texto, compilado parcialmente ou descrito por um agente anterior.**

### Current state for the next session

| Field | Current evidence |
|---|---|
| Repository | MartinFMelcop/Creative_AI_Project_HUB; actual Git root `/workspace/Creative_AI_Project_HUB`; lab remains nested in its original package directory |
| Preserved sources | 175 Rave Master texts and 3 WebSocket files; unchanged ZIP and inventory; not a complete RMXP backup |
| Primary workstream | P11 0.3.0 consistent workspace backup, inspection and safe new-file recovery |
| Runtime execution | Node 24 built-in SQLite online backup; separate operator CLI and actual Chromium recovery; no dependency or engine migration |
| Current verification | Live WAL, data/CLI boundaries, simulated file loss and restored two-participant browser continuation; `evidence/realtime-chat/RECOVERY_RUN.json` |
| Historical verification | Earlier project evidence retained; legacy chat/rooms regressions executed; P02's pinned practice task remains independent |
| Next action | Compare real recovery use with P06 animation, physical P03 play/listening and independent P04 readers |
| Other seeds | P01 0.2.0, P03 0.2.0, P04 0.1.0, P06 0.2.0, P07 0.1.0, P08 0.3.0, P10 0.4.0 and P02 0.2.1 preserved |
| Transfer / shared status | Existing TR-009/012/013/014 boundaries retained; no shared engine or new cross-project transfer |
| Portfolio / attribution | Clean `32f70ea` matched fetched main. Martin authorizes portfolio/main; Codex implementation/review and fictional synthetic workflow. No human approval or hosting deployment |

Registry evidence paths must resolve to existing files inside the lab; working
paths must be directories and legacy-source IDs must exist. This documentary
gate does not validate report contents or promote project maturity. See
[the QA contract](docs/REGISTRY_VALIDATION.md) for checks and limits.

Maintained [assessment](docs/ASSESSMENT.md) and [plan](docs/IMPROVEMENT_PLAN.md)
continue the recovery. Preserve the historical source archive; adaptations and
translations belong in working projects. Read [state](docs/STATE.md) for the
current unit and evidence, rather than assuming the v0.2.0 recovery is current.

## 1. Mandato do autor: tudo pode evoluir

Esta iniciativa não é um museu de versões antigas. Os projetos existentes entram como matéria-prima.

A autorização de Martin em 10/10/2026 permite alterar **todas as informações pertencentes aos projetos**: premissa, personagens, nomes, mecânicas, mídias, linguagem, engine, estrutura, escopo e destino. Jogos em RPG Maker XP podem migrar para Unity/C#; um livro pode originar jogo, narrativa interativa ou animação; poemas e sons podem originar músicas e álbuns; sistemas podem ser transferidos; projetos podem ser fundidos, compactados, divididos ou encerrados.

Essa autorização supera, para o trabalho neste laboratório, antigas regras de preservação criativa que entrariam em conflito com ela. O que antes era canon ou identidade protegida continua registrado como **origem histórica**, sem veto automático à nova direção. Uma nova decisão explícita de Martin pode voltar a proteger um elemento.

Liberdade criativa não altera fatos históricos: uma obra pode ganhar outro nome; uma experiência profissional não pode ganhar empregador, título, resultado ou data inventados. Um sistema pode ser refeito; um teste não executado não pode ser convertido retroativamente em teste aprovado.

### O que permanece como compromisso de trabalho

- Honestidade sobre autoria, uso de IA, capacidades e evidências.
- Rastreabilidade suficiente para compreender decisões e reproduzir resultados importantes.
- Desenvolvimento de competências de Martin junto com desenvolvimento de artefatos.
- Qualidade do material entregue a quem lê, joga, escuta, assiste ou avalia.
- Uso do tempo e do dinheiro compatível com recursos reais, ainda a levantar.

Nome do laboratório, organização e prioridades deste documento também são revisáveis. Esta seed é uma hipótese de trabalho estruturada, não um regulamento imutável.

### Critério para transformar um projeto

Uma transformação deve responder: qual problema ela resolve, o que reaproveita, o que perde, qual evidência produzirá e por que merece investimento agora. Não precisa pedir confirmação para toda escolha reversível já abrangida pelo pedido; precisa registrar mudanças de direção relevantes e respeitar os limites reais de acesso e execução.

## 2. Tese de portfólio

O portfólio deve demonstrar que Martin consegue transformar um pedido aberto em requisitos, decisões, implementação ou direção técnica, validação e resultado compreensível.

Sua vantagem inicial está na experiência em **análise de negócio, operações de entrega, processos, requisitos, coordenação e avaliação crítica**. A criação de jogos, mundos, imagens e áudio fornece um terreno autoral para provar essas habilidades e desenvolver outras.

### Posicionamento de trabalho

**PT-BR:** profissional de entrega e análise de negócio construindo sistemas criativos, protótipos de jogos e processos de avaliação com IA, com foco em requisitos, qualidade e evidências.

**EN, rascunho factual:** “Agile delivery and business analysis professional building creative systems, game prototypes and AI evaluation workflows, with a focus on clear requirements, validation and reproducible evidence.”

Esse texto não atribui experiência comercial em games ou AI Evaluation. Títulos mais especializados serão sustentados por demonstrações e experiência efetiva.

### Perguntas que cada case precisa responder

1. Qual problema real ou hipótese de projeto motivou o trabalho?
2. Qual era a condição inicial?
3. Que restrições e critérios de aceitação foram definidos?
4. Quais alternativas foram consideradas e por que uma foi escolhida?
5. O que a IA produziu e o que Martin efetivamente fez?
6. Como a solução foi validada e em qual ambiente?
7. O que mudou, com quais limitações?
8. Outra pessoa consegue inspecionar ou reproduzir a parte central?

### Dois públicos, dois percursos

| Público | Necessidade | Percurso desejado |
|---|---|---|
| Recrutador/cliente | Entender competência e resultado rapidamente | README → case curto → demo ou relatório verificável |
| Revisor técnico | Avaliar implementação, raciocínio e confiabilidade | Case → especificação → código/dados → testes → evidência |
| Colaborador criativo | Entender linguagem e direção | Amostra final → direção artística/narrativa → processo de seleção |
| Martin e agentes | Retomar trabalho sem perder decisões | STATE → projeto → decisões → tarefas e evidências pertinentes |

A apresentação pública deve ser pequena e selecionada, mesmo que o laboratório cresça muito. O número de projetos ativos não precisa corresponder ao número de assuntos que Martin gosta de explorar.

## 3. Base profissional de Martin

### Informações documentadas no currículo consultado

Fonte: `ResumeMartinFMelcopNeto.pdf`, disponibilizado em 06/10/2026 e lido para preparar esta seed. “Documentado no currículo” significa informação apresentada por Martin, sem verificação externa de empregadores ou certificação.

| Campo | Informação |
|---|---|
| Nome | Martin Melcop Neto |
| Localização profissional | Sorocaba, São Paulo, Brasil |
| Formação | Ciência da Computação, Universidade de Sorocaba, 2017–2021 |
| Certificação informada | Professional Scrum Master I — PSM I |
| Idiomas informados | Português nativo/bilíngue; inglês profissional pleno |
| Experiência agregada informada | Mais de sete anos em tecnologia, análise de negócio, processos e entrega |
| Busca profissional registrada | Oportunidades internacionais remotas em entrega, operações, BA, AI Operations, AI Evaluation e gestão de projetos |

### Trajetória

| Organização | Período informado | Função e trabalho relevante |
|---|---|---|
| Tata Consultancy Services | abr/2023–jun/2026 | Scrum Master / Agile Master; operações de entrega e análise funcional; cerimônias, riscos, dependências, stakeholders, KPIs, treinamento; Jira e ServiceNow |
| Target Software | mar/2020–fev/2023 | Business Analyst; requisitos funcionais e não funcionais, regras de negócio, BDD, backlog, jornadas, processos, dashboards e validação |
| Target Software | fev/2019–mar/2020 | Estágio em Business Analysis; engenharia de requisitos, cenários de teste, ER/UML/casos de uso, fluxos e roadmaps |
| CTA Eletrônica | nov/2018–fev/2019 | Estágio em software e operações; LMS, páginas/interfaces, suporte, conteúdo, banco de dados e ativos visuais |
| Global Electronics | ago/2018–nov/2018 | Estágio em desenvolvimento web e dados; WordPress, interfaces, MySQL e iniciativas digitais |

Ferramentas mencionadas: Jira, ServiceNow, Power BI, Excel, Azure DevOps, Azure Data Factory, SQL Server, Visio, WordPress, MySQL, Photoshop e Illustrator. Uma ferramenta no currículo comprova familiaridade declarada; não define automaticamente domínio avançado de todos os seus recursos.

### Contexto profissional adicional relatado anteriormente

Martin descreveu apoio a quatro squads, com aproximadamente 28 pessoas, gestão de esforço versus valor de negócio, KPIs, dependências e treinamento. Há relato de melhoria de spillover de aproximadamente 40% em uma squad e de períodos com entrega acima do compromisso inicial, chegando a cerca de 120% do planejado.

Esses números permanecem **relatos históricos a contextualizar**. Antes de usá-los em case público, definir período, denominador, métrica, mudança de escopo, qualidade, comparabilidade e evidência disponível. Entregar 120% do plano não prova, isoladamente, aumento de produtividade ou previsibilidade. Metas antigas como “+15% de velocidade” não são resultados realizados.

### Competências transferíveis e lacunas

| Base existente | Aplicação no laboratório | Evidência a construir |
|---|---|---|
| Requisitos e BDD | Feature specs, regras, falhas e critérios | Especificação ligada a testes e resultado |
| Riscos/dependências | Auditoria e priorização | Mapa que altera uma decisão concreta |
| Backlog e delivery | MVP, milestones, release gates | Fatia encerrada com cortes de escopo claros |
| KPIs, SQL e BI | Simulação, economia, telemetry | Dados reproduzíveis e interpretação correta |
| Treinamento e comunicação | Documentação para adoção | Outra pessoa consegue usar o artefato |
| Uso frequente de IA | Geração, crítica e iteração | Histórico de outputs, falhas e correções |
| Interesse em sistemas e arte | Mecânicas, mundos e direção | Pequeno produto com qualidade percebida |

Lacunas relevantes: autonomia atual em C#/Unity; execução local e debugging; disciplina de Git; testes de engine; estatística aplicada; pipeline de áudio; avaliação técnica de imagens; publicação e manutenção de produtos. Essas lacunas são perguntas de diagnóstico, não juízo definitivo sobre sua capacidade.

Não publicar dados pessoais de contato, documentos completos ou material corporativo apenas porque foram usados como fonte de trabalho. Selecionar o que tem função no portfólio; usar exemplos anonimizados ou simulados quando necessário.

## 4. Fontes, confiança e limites deste levantamento

### Classes de informação

| Rótulo | Significado | Uso adequado |
|---|---|---|
| `USER_DIRECTIVE` | Orientação atual explícita de Martin | Direção do trabalho |
| `RESUME_REPORTED` | Informação apresentada no currículo | Bio factual com atribuição adequada |
| `SOURCE_INSPECTED` | Arquivo cujo conteúdo foi efetivamente lido | Descrição limitada ao que foi inspecionado |
| `EXECUTION_OBSERVED` | Execução realizada e resultado registrado neste levantamento | Afirmação limitada ao ambiente, inputs e check correspondente |
| `HISTORICAL_CONTEXT` | Conversa ou versão antiga recuperada | Seed e pista para localizar fontes |
| `ASSISTANT_REPORTED` | Entrega/teste alegado anteriormente por IA | Revalidar antes de tratar como resultado |
| `PROPOSED` | Escolha ou experiência nova sugerida | Planejamento explícito |
| `UNKNOWN` | Falta de informação suficiente | Registrar lacuna e próxima ação |

### Fontes efetivamente usadas e recuperadas

- Pedido de Martin em 10/10/2026: monorepositório evolutivo, projetos como seeds, transformação irrestrita e mistura de arte com aplicação técnica de IA.
- Conversa recente de carreira fornecida: trilhas de produção, AI Evaluation, QA, dados, economia, technical design, protótipos, localização, workflows e toolkits. Faixas salariais e vagas citadas ali não foram revalidadas para esta seed e não são promessas de renda.
- Currículo acima, lido integralmente em texto.
- Pacote `Lightnovel Darkfantasy v0.4.48.zip`, localizado e aberto: `_project/SEED.md`, `README.md`, `MANIFEST.md`, `_project/PROJECT_STATE.md` e `_project/CANON_REGISTRY_v0.4.48.md` foram lidos. O manuscrito completo, PDF e documentos restantes não foram auditados nesta fundação.
- Contexto histórico de Artemyra/ArtemiZ4, The Dark Knight, Véu Partido e Tokyo 80s. Os executáveis e códigos completos desses projetos não foram importados nem executados nesta entrega.
- Histórico de AI Evaluation com cases simulados. Os PDFs completos anteriores não foram recuperados nesta fundação; não copiar suas alegações sem inspeção.
- Interesse declarado em imagens, sons, poemas e música. Existem referências históricas de ilustrações e direção visual; não foi recuperado um catálogo concreto de sons, poemas ou álbuns finalizados.

O pacote Lich v0.4.48 é o pacote recente **localizado e inspecionado**, não garantia de que nenhuma versão posterior exista. Nomes e números de versões dos demais projetos são breadcrumbs históricos, não certificação de versão vigente.

A v0.2.0 acrescenta os snapshots de Rave Master e WebSocket: 180 arquivos textuais lidos, 178 preservados e verificações atuais identificadas na seção 28. O acervo inclui planos de áudio e metadados de arte, sem masters sonoros ou inspeção visual dos arquivos de imagem. Isso amplia a base factual sem alterar os limites dos demais projetos.

### Lacunas prioritárias de inventário

1. Localizar o último material útil de cada jogo e comparar com versões que Martin realmente abriu.
2. Recuperar fontes editáveis, não apenas screenshots e ZIPs acumulados.
3. Catalogar samples de imagem e verificar finalidade, qualidade e origem.
4. Identificar quais ferramentas de som/música foram usadas e quais arquivos existem.
5. Recuperar poemas, letras e textos autorizados para transformação.
6. Verificar o material de AI Evaluation publicável e os problemas das versões anteriores.
7. Levantar disponibilidade semanal, hardware, sistema operacional e orçamento.
8. Executar um diagnóstico técnico curto com Martin, sem IA na primeira tentativa.

## 5. Inventário de projetos como matéria-prima

Identificadores persistem mesmo quando nomes mudam. Um projeto arquivado pode continuar como fonte de dados, arte, narrativa ou conhecimento.

| ID | Seed | Matéria-prima principal | Destinos possíveis | Estado nesta fundação |
|---|---|---|---|---|
| P01 | Artemyra / Eclipse Fair | Typed economy and native C# presentation | Godot .NET board, terminal workbench, replay and comparison | Native 0.2.0; core/CLI 0.1.0 retained, no historical restoration |
| P02 | AI Evaluation & QA Lab (historical Unity proposal) | Requirements, reproduced bugs, artifact checks | Bounded practice tasks and later independent evaluation | EVAL-001 runner 0.2.0 uses pinned snapshots, starter 0.1.0; M4 harness scope, no model candidate |
| P03 | Tokyo 80s | Original music, timing and sustained interaction | Midnight Signal and Rain Circuit with track selection/transition | P03 0.2.0 / P08 0.3.0 real media; human play/listening pending |
| P04 | O Lich mais velho da tumba mais antiga | Romance, mundo, personagens, arte e continuidade | Narrativa interativa, amostra editorial, jogo, animatic | Historical summary only here; new standalone story/EPUB/PDF 0.1.0 delivered |
| P05 | The Dark Knight | Combate por turnos, classes, progressão, conteúdo | Laboratório de combate e balanceamento | Legado RMXP descrito |
| P06 | Véu Partido / Veilbreak | Native combat trial; historical 3D RPG seed | Playable two-phase Godot arena, source and executed PCK | New destination; missing Unity starter remains historical |
| P07 | Visual Generation & Asset Lab | Capas, ilustrações, sprites e direção | Assets consistentes, pipeline e estudo de seleção | Material visual histórico; inventário pendente |
| P08 | Audio, Poetry & Music Lab | Original musical production and integration | Two P03 stages and P06 native soundscape | Real masters/exports/scores; no album or human listening approval |
| P09 | AI Delivery & Operations Cases | Carreira real e avaliação simulada | Case de entrega, análise de workflow e rubricas | Base profissional lida; cases anteriores pendentes |
| P10 | Adventures Unleashed / Rave Master | Narrative, NPCs and recovered systems | Two-day browser rescue/relief campaign with local resume and portable saves | Campaign 0.4.0; Python adventure 0.2.0 / standalone 0.1.3; bounded evidence in registry |
| P11 | Real-time Integration Lab / Project Rooms | Node/Socket.IO/SQLite | Trusted local project conversations, decisions, export and workspace recovery | Workspace 0.3.0; original protocol and P02 snapshot preserved; no public service |

P02 agrupa evaluation e QA porque podem compartilhar a mesma aplicação pequena. Não criar dois projetos Unity idênticos apenas para apresentar títulos diferentes. P01 pode abrigar produção, economia e analytics como cases distintos de uma fonte comum.

### P01 — Artemyra / ArtemiZ4

[Eclipse Fair](projects/eclipse-fair/README.md) 0.2.0 adds a native Godot .NET
board: clickable routes, actual forecasts/action previews, confirmation, paced
rivals, focus-out stop, full Gate/deadline results, autosave and replay resume.
The 0.1.0 domain/CLI/journal/compiled workbench and comparisons remain unchanged.
Source and a runtime-dependent compiled project pack execute in Godot; the pack
works outside source with .NET runtime only, using the installed engine APIs.
No duplicated engine rules, OS export, LAN/minigames, historic restoration,
human balance or commercial approval. See native evidence/README for boundaries.
The historical context below remains direction, not current runtime.

**Núcleo histórico:** party RPG competitivo originado em RPG Maker XP/RGSS. Quatro jogadores, MVP com um humano contra três IAs, tabuleiro, minigames e recursos temporários. O histórico inclui formatos FFA e propostas de 2v2, sem campanha e com LAN como expansão.

**Vocabulário e sistemas recuperados:** Feira do Eclipse, Sigilos do Véu, Óbolos, Maldição, Ritos, familiares, roubo, distritos e progressão durante a partida. Versões antigas mencionam 48 casas, quatro distritos, oito personagens de MVP, meta de três sigilos e limite de 15 turnos. Esses números são parâmetros candidatos, não exigências para a reconstrução.

**Roster histórico:** Vaelis, Madra/Madra Nym, Zareth, Lyrien, Thessa, Beryon, Morrak e Nira. Há nomes e contagens de diferentes fases; não fundir dados conflitantes sem registrar a escolha. Familares históricos incluem corvo, lobo, aranha e coruja; Valak foi proposto como aliado excepcional com custos e condições. Isso oferece exemplos para constraints e análise de poder, sem impor implementação de todo o conteúdo.

**Oportunidade principal:** usar um projeto de escopo excessivo para demonstrar julgamento de produção, separar especificação de funcionamento e extrair uma economia testável.

**Primeira fatia sugerida:** quatro agentes de jogo; um grafo pequeno; moeda; compra de objetivo; encerramento; logging. Sem minigames gráficos, LAN, roster completo ou árvore de especialização até o loop básico ser verificável.

**Três entregas independentes possíveis:**

1. Auditoria de estado e MVP com requisitos rastreados a arquivos e limitações.
2. Simulador de economia com baseline, mudança e análise de sensibilidade.
3. Protótipo visual que usa a regra aprovada, em engine escolhida após avaliação.

**Risco aprendido:** etapas anteriores reportaram checks estáticos e simulações textuais sem execução do Game.exe. Houve correções de boot/menu e reconstrução de namespace. O histórico também contém confirmações pontuais de playtest pelo usuário; uma confirmação antiga não valida todos os incrementos posteriores.

**Extrações candidatas:** state machine de partida; grafo de tabuleiro; transação de compra; fontes/sumidouros; perfis de agentes; progressão curta; catálogo de minigames; instrumentação.

**Gate de continuação:** regras básicas compreendidas, importação selecionada, estado real registrado e uma hipótese de case definida. Se a migração integral for cara, extrair a regra e construir um protótipo novo menor.

### P02 — AI Evaluation & QA Lab

**Origin:** the Unity AI Evaluation & QA Lab proposal, derived from Martin's
interest in requirements, QA and AI evaluation; not commercial evaluation work.
The earlier stamina-after-respawn example remains a possible engine task, not
the current implementation or a requirement to create a duplicate Unity app.

**Working slice:** EVAL-001, chat send buffering, in
`evaluations/chat-send-buffering/`. Python exports a fresh allowlisted P11 0.1.0
starter and checks only a submitted client with the pinned Node/Chromium suite.
Candidate exports exclude reference, tests, Git history, knowledge and evidence.
The existing P11 app owns the runtime; no engine migration or new dependency.

**Current evidence:** runner 0.2.1 executes its committed evaluator snapshot,
checks installed direct versions and preserves the known 15/17 baseline and
17/17 reference outcomes. Its 25 regressions and calibration are prior verified
results; current hosted gates establish new execution. The nine-file starter
contract remains 0.1.0. P11's Project Rooms addition does not repin the task or
change its dependency graph. This is M4 for a calibrated harness, not independent
model performance, secrecy or OS isolation.

**Gate:** record an independently produced artifact, actual candidate identity,
tools, context, attempts and available cost; execute the evaluator separately.
Public reference/history is discoverable. Bundle separation is not secrecy,
OS isolation or a security sandbox. Recalibrate after changes to the pinned
suite; reject scope violations and preserve incomplete outcomes as inconclusive.
See ADR-010/ADR-011/ADR-012 and `evidence/realtime-chat/READING_RUN.json`; timeout evidence stays historical. Process-group
cleanup is not isolation; escaped sessions remain outside its tested contract.

### P03 — Tokyo 80s

[Tokyo 80s Night Shift](projects/tokyo80s/README.md) 0.2.0 now has two original
tracks. Rain Circuit adds 84.5s at 96 BPM with performed hold tails, Practice/Arcade,
track transitions and per-song bests while preserving Midnight Signal media and
old scores. Tail scoring, early release, pause/re-hold and chronological misses
are connected to actual musical envelopes and real browser audio-clock runs.
No engine migration, recovered ZIP or human musical/play approval is claimed.


**Núcleo histórico:** Tóquio dos anos 1980, city pop/wave, arcade, dança como luta, aura e poderes evocando stands/personas. Protagonista associado a top score e topete azul-noite. O projeto anterior recebeu o nome `TOKYO80s_RhythmGame_v0.0.1.zip`; seu runtime não foi inspecionado aqui.

**Identidade a explorar:** domínio do ritmo como expressão de personagem; cidade e música informando mecânica. Referências culturais orientam atmosfera, sem exigir copiar personagens, músicas ou propriedade intelectual de terceiros.

**Primeira fatia proposta:** uma faixa original ou utilizável; quatro lanes; chart curto; judgment; combo; aura; uma habilidade; restart; resultados. Escopo sugerido de 60–90 segundos, ajustável após diagnóstico. Duração não é um resultado validado.

**Problemas técnicos interessantes:** clock de áudio; offsets de dispositivo e input; pausa; mudança de foco; entradas simultâneas; notas não consumidas duas vezes; desempenho em diferentes frame rates; dados de chart; telemetria de erro temporal.

**O que pode virar outro produto:** núcleo de judgment puro, editor/importador simples de chart, ferramenta de calibração, feedback visual, sample de áudio adaptativo e minigame de ritmo para P01.

**Riscos:** expandir para campanha e catálogo musical cedo; escolher arte antes de validar o timing; usar música sem origem clara; confundir aparência fluida com sincronização correta.

**Gate de continuação:** o loop executa e reinicia; judgments têm comportamento de fronteira especificado; há validação do clock e uma sessão de playtest em hardware registrado.

### P04 — O Lich mais velho da tumba mais antiga

**Current destination:** [A água sob Darsen](projects/lich-cistern/README.md) 0.1.0
is a complete five-scene Portuguese story with EPUB/PDF. It is newly written from
this summary: the historical ZIP/manuscript is not available in this checkout.
Baldino/Aevren/Darsen remain; new characters/waterworks/rules are scoped adaptation
choices. Narrative continuity and reader formats were reviewed by Codex, not an
independent audience or author canon approval.

**Origem histórica:** light novel de dark fantasy em vasto universo; referência de estrutura e ambição associada a Overlord, múltiplas linhas narrativas e passado extenso. Baldino como narrador; Aevren/Garran em rascunhos, Dorian, Elira, Maelis e Orvek entre personagens recorrentes.

**Estado lido no pacote v0.4.48:** fase de worldbuilding/timeline; B01 pausado, com última versão literária v0.4.47; B02–B10 e OVAs tratados como quarry, ou material de mineração. A seed local original protegia somente nome e estilo, separando canon ratificado em registro próprio. A nova autorização deste laboratório permite rever também esses elementos, preservando a origem documental.

**Mundo registrado nesse pacote:** Transição Primordial; Celestiais ligados a condições da realidade e ausentes na época relevante; múltiplas linhagens conscientes; vida natural e alma; divindades ascendidas; guerra antiga de cerca de seis milênios; último Dragão Primordial e filha do Rei Demônio; tradições fragmentadas das artes das trevas; Aevren reconstrói conhecimento em vez de inventar todo o sistema do mundo.

**Escala do autor:** Ano 0 como referência aproximada a 3000 a.C.; era antiga de Aevren/Dorian em torno de Ano 3800–3900; presente em torno de Ano 4500. São equivalências de autor e intervalos aproximados, não um calendário cristão dentro da obra.

**Nomes de trabalho de povos:** Vharzai, Azhurath, Rhazir, Saelir, Nharuun, Eldren, Gharok, Dhorren, Brogath, Mourai, Kherai, Orrakai, Aruvanos, Iriath e Velari. Evitar substituir a diversidade por um mundo que existe somente para humanos ou para Aevren. Darsen antiga cosmopolita e sua transformação são material histórico útil; detalhes do corpus antigo precisam ser escolhidos para cada nova versão.

**Convenção de narração:** Baldino pode narrar depois de morrer; isso não comprova que exista como fantasma. Uma adaptação precisa decidir a interface narrativa e as regras do mundo separadamente.

**Aprendizados editoriais históricos:** reduzir prosa autoconsciente, teses recitadas, frases de trailer, simbolismo automático de objetos e excesso de documentação dentro da narrativa. Mostrar ação, rotina, consequências e relações específicas. Auditoria antiga de B01 v0.1.49 é registro de diagnóstico de outra versão, não lista automaticamente atual de defeitos.

**Direção visual histórica:** dark fantasy, menos aparência anime/Disney; capas psicodélicas e simbólicas; portal e estátua de gesso com cor por volume; atenção à repetição de poses e poluição. Tudo revisável conforme novo produto.

**Primeira adaptação recomendada como hipótese:** uma cena interativa de 5–10 minutos ou um animatic curto, com um conflito e uma regra de mundo demonstrada. Não adaptar dez livros de uma vez. Exemplo candidato: manutenção de uma dungeon seguida de uma invasão, mostrando Baldino por aquilo que observa e faz.

**Competências que pode evidenciar:** modelagem de domínio, continuidade, narrativa interativa, avaliação de geração textual, direção de arte, localização, ferramentas de apoio à autoria e adaptação entre mídias.

**Extrações candidatas:** ontologia de entidades; regras de persistência de corpo/alma/memória; diálogo ramificado; continuidade temporal; instrumento de comparação de versões; brief de arte consistente. Um validador pode detectar datas ou nomes conflitantes; qualidade literária exige leitura e julgamento.

**Gate de continuação:** escolher uma finalidade e público, uma fatia e um conjunto de regras vigente. Manter contraditórios como variantes de origem até decisão; não fundir todo o legado em uma suposta versão definitiva.

### P05 — The Dark Knight

**Legado histórico:** RPG Maker XP; combate com uma ação por turno, AGI, linhas e estados; 21 classes, cinco raças, curva de nível 1–180 e itens em sete tiers em planos anteriores. Há pacotes históricos de Sprint 100 divididos em core e áudio, além de referências de openings e ilustrações.

Contagem de sprints não comprova produto final ou estabilidade. Sem auditarmos fontes e runtime, esse material é reservatório de sistemas e conteúdo.

**Destino técnico candidato:** núcleo de combate por turnos em C# separado da apresentação; uma arena pequena com duas ou três classes para demonstrar ordem de ações, status, alvo e balanceamento.

**Perguntas a resolver:** como AGI desempata; quando estados expiram; se a ordem é recalculada; o que ocorre quando um alvo morre; como efeitos simultâneos se resolvem; quais regras de linha são legíveis ao jogador.

**Extrações:** effect resolver, catálogo de estados, curva de XP, tiers de itens, cálculo de dano e regras de turno. Não transportar automaticamente 180 níveis e 21 classes para provar uma única mecânica.

**Risco:** nome genérico ou associado a obras existentes, conteúdo excessivo e dificuldade de atribuição de ativos. Renomear é permitido e pode tornar o produto mais distintivo.

### P06 — Véu Partido / Veilbreak

Historical direction: Unity 3D supernatural combat, damage taxonomy, boss/crafting
plans and the breadcrumb `VeuPartido_UnityStarter_v0.0.47.zip`. The starter is not
present, and plans are not executable evidence. No restored Unity code or franchise
characters enter the new destination.

[Veilbreak: The Bell Warden](projects/veil-arena/README.md) 0.2.0 is a new native
Godot 2D trial with painted characters/courtyard, fourteen semantic cues and two
aligned phase-responsive music loops. P07/P08 assets are actually imported, mixed
and packed; M/mouse mute and pause/resume/restart govern their lifecycle. One opponent has locked sweep/charge/wave warnings, a faster second
phase with delayed charge echo, and a ward pressured by projectile seals. Native
movement/collisions, resolve, blade counters, results/pause/restart are connected.
The actual engine and resource pack were executed. This is a bounded native
prototype; no standalone platform build, human balance or commercial claim.

Godot/GDScript suits the small physics/presentation loop and available standard
editor. Unity/editor/starter remain absent; .NET is now installed for P01, but
compiling a C# domain alone would not demonstrate
this playable milestone. A browser rewrite adds little after recent P10/P03 work.
Future Unity/3D adoption remains a product decision requiring real sources/tools,
not an automatic migration or language quota.

### P07 — Visual Generation & Asset Lab

**Current destination:** [P06 media](projects/veil-arena/media/provenance.json)
contains three actual PNG paintings with a shared style/reference and one framing
correction. Native rendering and wall/HUD review establish bounded integration.
Each actor has one static pose; no complete animation set or audience approval.

**Origem:** geração e revisão de imagens para Lich e outros interesses criativos; capas, ilustrações em ação e correções de personagens/gênero/consistência relatadas. Ainda falta inventário das fontes de melhor qualidade.

**Tese técnica:** direção visual consistente pode ser especificada, avaliada e integrada a um produto. Uma galeria de imagens atraentes não demonstra sozinha um pipeline utilizável.

**Primeira fatia:** brief visual de um personagem; três poses ou estados coerentes; uma imagem de cena ou asset de UI; integração em uma amostra do projeto escolhido; relatório das falhas corrigidas.

**Critérios:** identidade; silhueta; anatomia apropriada ao projeto; pose e leitura; luz; paleta; contraste; acabamento; bordas/alpha quando necessário; dimensões; consistência entre frames; legibilidade na escala final; aderência ao brief.

**Comparações úteis:** geração sem contexto versus referência estruturada; imagens selecionadas antes/depois de correção; asset bonito isoladamente versus asset legível na UI. Registrar número de tentativas e rejeições sem transformar volume em mérito.

**Extrações:** brief, paleta, ficha de personagem, rubrica, metadados de produção e fluxo de integração. Componentes visuais só viram “asset técnico” quando têm finalidade, formato e validação dentro do produto.

**Gate:** pacote pequeno consistente, proveniência registrada e avaliação no tamanho real de uso. Não gerar centenas de imagens antes de verificar esse fluxo.

### P08 — Audio, Poetry & Music Lab

Current 0.3.0 also delivers [Rain Circuit](projects/tokyo80s/media/rain-provenance.json):
actual master/Vorbis, original score/producer, played durations consumed by P03
holds and measured decoded loudness/peak. Prior P03/P06 media stays intact.


**Current destinations:** P03 retains Midnight Signal. [P06 media](projects/veil-arena/media/provenance.json)
adds fourteen original cues and two aligned 24s music loops, masters/producer and
actual AudioServer/compiled-pack consumption. No physical listening/album claim.

**Origem atual:** Martin autoriza transformar sons e poemas em músicas e álbuns. Não há, neste levantamento, nomes de álbuns, letras completas, ferramentas específicas ou gravações suficientes para alegar catálogo publicado.

**Primeira ação:** inventariar fontes existentes e identificar o que é poema, letra, interpretação, composição, efeito sonoro, loop, stem, render final ou referência. Sem fonte, criar um brief novo claramente identificado como proposta.

**Primeira fatia candidata:** uma peça curta ligada ao P03 ou P04, com versão de escuta e versão de integração. Alternativa: poema autoral → letra adaptada → composição curta → análise do que foi preservado/perdido.

**Perguntas de direção:** emoção, função, instrumentação, andamento, idioma, duração, voz, dinâmica, densidade e lugar no produto. Um álbum é uma evolução possível após existir linguagem musical coerente; não é a primeira obrigação.

**Critérios técnicos:** duração e pontos de loop; formato e sample rate; clipping; ruído indesejado; inteligibilidade quando houver voz; equilíbrio; loudness adequado ao destino; início/fim; variação entre stems; transições; consumo de memória. Definir metas de loudness e loudness integrado somente conforme uso concreto e medição disponível.

**Critérios criativos:** estrutura, intenção, fraseado, prosódia, letra, unidade e contraste. Métricas de arquivo não comprovam qualidade musical.

**Experimento candidato:** comparar geração direta de faixa com produção por etapas — brief, letra, composição, seleção, edição e integração. Avaliar consistência, tempo ativo humano, custo e retrabalho com o mesmo objetivo.

**Reutilização:** um motivo musical pode gerar tema e variação; um loop pode alimentar ritmo ou áudio adaptativo; um poema pode originar monólogo, lore ou canção. Manter IDs e relação de derivação; registrar se há voz real, consentimento aplicável e origem das referências.

### P09 — AI Delivery & Operations Cases

**Base:** trajetória profissional de Martin e portfólio anterior de avaliação. O histórico distingue experiência profissional real de três cases simulados de AI Evaluation. Não apresentar simulações como contratos pagos ou experiência formal de avaliador.

**Problema histórico:** versões v1.4/v1.5 e Recruiter Brief foram discutidas; havia recomendação de revisão antes de publicar por mistura de conteúdo interno e excesso de informações. Não importar os PDFs como showcase pronto.

**Estrutura de avaliação recuperada:** evidência → classificação → scoring → decisão → correção.

**Primeiro case candidato:** uma auditoria de requisito ou bug criada em P01/P02, mostrando baseline, output de IA, defeito, evidência e correção. Outro case possível é um relato profissional anonimizado com limites quantitativos claros.

**Extrações:** taxonomy de falhas, rubricas, decisão de aceite, decomposição de tarefas, custo de workflow e relatórios para stakeholders.

**Gate:** caso autossuficiente, origem declarada e afirmações sustentadas. Martin deve conseguir defender o raciocínio sem depender do texto gerado.

### P10 — Adventures Unleashed / Rave Master

Reservatório recuperado de RPG Maker XP/RGSS: narrativa, personalidade e diálogo de NPCs, combate, progressão, crafting, reputação, planejamento de arte/áudio e QA. A extração completa, os estados e limites estão na seção 28.2. Não é um novo compromisso de terminar um RPG extenso nem uma fusão automática com os outros RPGs do inventário.

[The Last Waystone](projects/waystone-dialogue/browser/README.md) is a complete
browser rescue operation with equipment, Keeper negotiation, two routes,
forecast current, residents/cargo and five consequential shelter endings.
Campaign 0.4.0 includes the original live SVG diagram, action risks, journal,
local resume and replay-validated saves. A new morning consumes night outcomes
for clinic timing, stranded crew, grain, seed and restoration. Existing night
saves continue into the chapter; Python parity applies to the preserved night. The Python adventure 0.2.0 and standalone
scene 0.1.3 remain unchanged. Its oracle compares actual choices, trace/state and
epilogues; browser checks execute the complete workflow. No full RPG equivalence,
independent reader approval, shared engine or commercial product is claimed.

### P11 — Real-time Integration Lab / WebSocket

The historical snapshot only logs incoming messages. P11 0.3.0 now has
[Project Rooms](projects/realtime-integration-lab/README.md): local participant,
create/share/switch projects, saved notes/decisions, history recovery, drafts,
explicit idempotent retries, complete JSON export and operator workspace recovery.
Node 24 built-in SQLite adds persistence and consistent live WAL backup without
another dependency/service. Inspect private bundles, restore into a new database
and resume from retained browser identities; later writes and browser storage are
outside the snapshot. Existing files/sidecars are refused. Original ephemeral
protocol remains unchanged. All trusted participants can open all rooms; chosen
names are not verified accounts. Human usability, power-loss/off-site recovery
and public operation remain unverified. P02 retains its pinned snapshot/dependency
graph and calibrated TR-009; no evaluation task/transfer is automatically expanded.

## 6. Arquitetura do laboratório

Um monorepositório permite descoberta e troca de conhecimento. Cada projeto mantém fronteira própria para não virar um único sistema impossível de executar.

### Estrutura proposta

| Caminho | Responsabilidade |
|---|---|
| `README.md` | Entrada e apresentação selecionada |
| `SEED.md` | Fundamentos, inventário e direção evolutiva |
| `AGENTS.md` | Instruções curtas de operação para agentes |
| `docs/STATE.md` | Estado atual e próxima unidade de trabalho |
| `docs/ASSESSMENT.md`, `docs/IMPROVEMENT_PLAN.md` | Maintained evidence overview, selected scope, priorities, and acceptance |
| `docs/DECISIONS.md` | Decisões relevantes e alternativas |
| `docs/ROADMAP.md` | Fases e gates, sem promessa de calendário |
| `docs/SEED_EVOLUTION.md` | Manutenção da seed e continuidade por fases |
| `docs/LEGACY_REPOSITORIES.md` | Guia das fontes recuperadas e próximos recortes |
| `registry/legacy_sources.json` | Snapshots, inventário e hashes das fontes antigas |
| `archive/` | Acervo seletivo de fontes históricas, separado da implementação ativa |
| `registry/projects.json` | IDs, estado e relações de projetos |
| `registry/transfers.json` | Transferências de conhecimento/componentes |
| `registry/assets.json` | Metadados de imagens, áudio e outros ativos |
| `projects/<slug>/` | Fonte e documentos locais de cada projeto |
| `shared/` | Componentes promovidos após reutilização comprovada |
| `knowledge/` | Lições aplicáveis com evidências e limites |
| `experiments/` | Hipóteses, protocolos e registros de execução |
| `evaluations/` | Tasks, candidatos e avaliações de IA |
| `showcase/` | Cases selecionados para apresentação |
| `templates/` | Modelos de registros, tasks e cases |
| `tools/` | Utilitários do laboratório |
| `evidence/` | Amostras e evidências pequenas selecionadas |

Diretórios aparecem quando houver material que os justifique. A v0.2.0 inclui fontes históricas selecionadas e relatórios de dois runners offline; não inclui um jogo funcional ou assets fictícios para preencher pastas.

### Fronteira de projeto

Cada projeto executável deve declarar: propósito; responsável; linguagem; versão; dependências; instalação; execução; testes; entradas e saídas; licenças relevantes; estado conhecido; critérios de conclusão da fase. Um leitor deve conseguir trabalhar nele sem instalar todos os outros.

Em Unity, o diretório do projeto deve conter as pastas e configurações necessárias ao próprio Editor. Pacotes compartilhados entram por referência compatível e versão definida. Não assumir que várias pastas de scripts arbitrárias compõem um projeto Unity válido.

### Política de dependências

Fluxo desejado: bibliotecas de domínio e formatos → adaptação de engine → produto. Um simulador não deve depender da UI Unity; a rule engine não deve depender de personagens literários só porque uma demonstração usa esses personagens.

Não permitir dependência circular entre projetos. Se P01 e P03 precisam do mesmo timing, extrair um componente mínimo após testar os dois usos, ou manter uma duplicação deliberada temporária com motivo. Não criar uma abstração universal por medo de duas cópias pequenas.

### Separação entre dados e representação

- Regras de domínio: validação, recursos, dano, estados, turnos e condições.
- Dados: parâmetros e catálogos com schema e unidades.
- Apresentação: UI, arte, áudio, animação e texto exibido.
- Instrumentação: eventos e logs com contrato explícito.
- Conteúdo narrativo: fatos do mundo e suas variantes, sem contaminar invariantes do motor.

O mesmo conceito pode existir em vários projetos com semânticas diferentes. “Maldição” em P01 não precisa ser a magia de P04. Relacionar por padrão de design quando útil; não declarar universo compartilhado por coincidência de nome.

## 7. Como os projetos aprendem entre si

“Aprender” aqui significa produzir conhecimento registrado, testar sua transferência e atualizar implementações e decisões. Arquivos no mesmo diretório não treinam automaticamente um modelo nem garantem que uma nova sessão leia todo o histórico.

### Unidade de aprendizado

Uma lição útil contém: problema observado, contexto, evidência, decisão, resultado, limite de aplicação e destino candidato. “Usar event bus” ou “IA economiza tempo” são opiniões genéricas até existir contexto e comparação.

### Ciclo de transferência

1. Projeto A apresenta um problema e uma solução verificável.
2. Registrar a lição e classificar: conceito, dado, código, asset, teste ou workflow.
3. Identificar um problema semelhante em B e diferenças relevantes.
4. Transferir uma parte pequena, com adaptação explícita.
5. Validar em B e verificar se A continua funcionando quando houver mudança compartilhada.
6. Promover para `shared/` somente quando houver contrato estável e benefício real.
7. Registrar versão, consumidores e custo de manutenção.

### Mapa inicial de transferências candidatas

| Origem → destino | O que transfere | Adaptação necessária | Prova de transferência |
|---|---|---|---|
| P01 → P02 | Compra de sigilo e transação | Isolar regra de dinheiro, inventário e estado | Regressão de compra parcial falha antes e passa depois |
| P02 → todos executáveis | Bug report e avaliação | Adequar ao domínio e ao ambiente | Outro projeto encerra uma falha com o mesmo protocolo |
| P03 → P01 | Minigame de timing | Reduzir duração, definir resultado e retorno ao board | Partida entra e sai do minigame sem perder estado |
| P03 → shared | Judgment/clock | Separar algoritmo puro e integração de áudio | Dois consumidores testam a mesma API |
| P05 → P06 | Pipeline de dano/status | Ordem de turnos versus tempo real | Casos comuns mantêm semântica documentada |
| P04 → P06 | Encontro e regra de mundo | Converter narrativa em comportamento jogável | Jogador compreende uma regra pela interação |
| P07 → P03/P04 | Brief e ativos visuais | Estética, formato e tamanho de destino | Asset integrado passa leitura visual no produto |
| P08 → P03 | Música/loops | Chart, sync, pontos de transição | Timing validado com áudio escolhido |
| P08 → P04 | Motivo/voz/poema | Função dramática e continuidade | Amostra funciona na cena, não só isolada |
| P09 → P01/P02 | Riscos, aceitação e workflow | Escala de projeto pessoal | Documento altera priorização ou decisão de aceite |

Todos os itens acima começam como **candidatos**. Não registrar “transferência concluída” sem artefato de destino e evidência.

### Fusão, divisão e encerramento

Fusão é útil quando dois projetos resolvem o mesmo problema, têm público/stack compatíveis e compartilhar manutenção reduz esforço. Não fundir apenas porque ambos são RPGs.

Divisão é útil quando um componente resolve problema independente e outro usuário consegue adotá-lo. Extração para marketplace é consequência dessa utilidade, não motivo suficiente para chamar um script de produto.

Encerramento é sucesso quando elimina uma hipótese fraca e preserva aprendizado. Registrar motivo, o que reaproveitar e o que deixa de ser mantido. Um projeto extinto não precisa manter um backlog artificial.

## 8. Decidir em que trabalhar

### Critério de seleção

Avaliar candidatos com notas internas de 0 a 5:

| Fator | Peso sugerido | Pergunta |
|---|---:|---|
| Alinhamento profissional | 25 | Demonstra habilidade exigida pela direção escolhida? |
| Evidência possível | 25 | Pode terminar com algo inspecionável/reproduzível? |
| Viabilidade | 20 | Cabe em ambiente, autonomia e tempo reais? |
| Reaproveitamento | 15 | Serve a outro problema concreto? |
| Motivação autoral | 15 | Martin quer sustentar o trabalho até o fim? |

Score interno = soma de peso × nota/5, total de 0–100. Este modelo serve para explicitar tradeoffs, não para fingir precisão de mercado. Não atribuir notas de candidatos ausentes nem publicar essa nota como qualidade técnica do produto.

Antes do score, verificar bloqueios: fontes inacessíveis; execução impossível; trabalho dependente de dado não disponível; requisito sem finalidade; custo fora de orçamento. Um score alto não remove bloqueio.

### Recomendação inicial, com razão

**Historical order:** v0.1.0 recommended P01 discovery; v0.2.0 recovered concrete P10/P11 sources. Under the current request to select and implement an increment, Codex prioritized P11 because its defect and full local interaction can be verified here. ADR-008 records the choice; the assessment and plan preserve alternatives without activating them. This is not a claim that Martin individually selected or tested P11.

**Current work order:** reassess the portfolio every session. P06 now has a native
trial, P01 a native economy board, P11 a recoverable persistent workspace, P10 two playable days and P03 two original rhythm stages.
Compare unassisted native/play/listening evidence, P11's account/retention/off-site needs,
independent P02 context and recovered-source opportunities before choosing again.
Recent browser concentration is a reason to investigate alternatives, not a quota.

The former P01/P03-first order is historical planning, not a current mandate.
Reassess actual portfolio opportunities and technologies; P06 now has its own
native destination. Related projects should contribute only to a concrete result.

Se Martin escolher arte e música como prioridade principal, reorganizar a rota: uma peça criativa final + processo de geração/seleção + integração pequena. A estrutura não obriga todos os interesses a servirem a uma única carreira de games.

### Regras contra dispersão

- Uma frente principal ativa; no máximo uma auxiliar com resultado limitado.
- Uma unidade encerrada antes de iniciar outra de escopo semelhante.
- Separar ideias desejáveis de compromissos da fase.
- Não transformar toda lição em biblioteca, todo poema em álbum ou todo personagem em jogo.
- Não expandir roster/conteúdo para compensar core loop fraco.
- Não aumentar número de documentos quando a lacuna é execução.
- Replanejar quando a evidência contradizer a hipótese, não só quando surgir uma ideia nova.

## 9. Modelo de estados e evidências

### Estado de atividade

`seed`, `triage`, `active`, `paused`, `archived` ou `retired`. No registro, `phase` explica a fase atual e `next_action` descreve o próximo trabalho. Estado de atividade não é qualidade nem maturidade.

### Maturidade do artefato

| Código | Evidência necessária |
|---|---|
| M0 — seed | Ideia, origem, propósito e lacunas |
| M1 — especificado | Escopo, comportamento e aceitação suficientemente claros |
| M2 — implementado | Arquivos existem e foram inspecionados; execução ainda pode estar pendente |
| M3 — executado | Fluxo principal rodou em ambiente registrado |
| M4 — validado | Critérios relevantes verificados com resultados e limites |
| M5 — demonstrável | Amostra selecionada, instruções e evidências prontas para público |
| M6 — mantido | Uso posterior, feedback e correções efetivamente registrados |

Não pular M2→M5 porque uma screenshot foi produzida. Uma demo pode ser publicável com limitações; o estado de cada afirmação continua explícito.

### Tipos de verificação

| Tipo | Prova | Limite |
|---|---|---|
| Revisão de conteúdo | Leitura de fonte/documento | Não demonstra execução |
| Análise estática | Schema, sintaxe, referências e ferramentas | Não demonstra comportamento de runtime |
| Teste de domínio | Regra executada isoladamente | Não valida ciclo da engine |
| Integração | Componentes executados juntos | Depende do ambiente e caminhos testados |
| Playtest/escuta/leitura | Experiência humana registrada | Amostra e subjetividade precisam de contexto |
| Benchmark | Protocolo e condições controladas | Não generaliza automaticamente para o mercado |

### Identidade de uma execução

Cada execução relevante registra data, ID, projeto, versão ou commit, configuração, versões de ferramentas, comando/procedimento, entradas, seed aleatória quando aplicável, resultados e artefatos. Antes de existir commit, usar hash do arquivo/configuração e informar ausência de commit.

Não misturar configuração chamada “seed” de RNG com esta SEED de projeto. RNG seed é apenas um parâmetro de execução. Seeds iguais não garantem resultados iguais entre engines, versões, ordens de chamadas ou hardware.

### Afirmações ligadas a evidências

Exemplo de forma: “A compra com saldo insuficiente não altera saldo, sigilos e maldição nos testes de domínio da execução RUN-012.” Isso tem escopo claro. “Sistema seguro e pronto para produção” exige muito mais evidência e provavelmente não é conclusão adequada a um laboratório inicial.

## 10. Operação com IA

### Papéis por tarefa

| Papel | Responsabilidade | Evidência produzida |
|---|---|---|
| Planejador | Decompor objetivo, critérios e dependências | Brief e escopo da fase |
| Implementador | Produzir solução limitada à tarefa | Diff e artefatos |
| Revisor | Procurar falhas e testar entendimento | Achados ligados a linhas/regras |
| Avaliador | Aplicar protocolo de aceitação | Resultado e evidência |
| Martin | Definir intenção, acompanhar decisões, validar de fato e desenvolver autonomia | Julgamento atribuído corretamente |

Um mesmo agente pode exercer papéis em etapas distintas, mas isso não constitui independência. Usar agentes distintos somente se o pedido e as ferramentas autorizarem; não presumir orquestração paralela. Separação de papéis também pode acontecer com sessões isoladas e revisão humana.

### Contexto por tarefa

Entregar ao implementador: objetivo, arquivos permitidos, interfaces, comportamento, restrições, critérios, instruções de execução e exemplos necessários. Evitar histórico inteiro, material obsoleto e solução de referência de task de avaliação.

O avaliador recebe o protocolo e a evidência necessários. Quando houver checks reservados, manter a separação definida na seção 11.

### Registro de contribuição

Para cada case, escrever ações concretas:

- IA: propôs decomposição; gerou código inicial; sugeriu testes; gerou variantes visuais.
- Martin: definiu requisito; executou a build; encontrou problema; selecionou uma variante; alterou um cálculo; aprovou ou rejeitou com motivo.
- Ferramentas: executaram testes, mediram áudio, produziram render ou calcularam estatísticas.

Não usar declaração padrão de “toda validação feita por mim” quando Martin ainda não executou essa validação. Texto público pode ser: “AI assisted with implementation. The documented checks were run in the recorded environment; independent human playtesting remains pending.” Adequar ao que ocorreu.

### Memória persistente

`STATE.md` guarda situação atual. Decisões duráveis vão para `DECISIONS.md`. Evidências ficam nos registros de execução. Lições transferíveis vão para `knowledge/`. A seed só muda quando fundamentos, inventário ou estratégia mudam; não anexar todo chat ao final dela.

Atualizar esses arquivos no encerramento permite que uma nova sessão retome o trabalho mesmo sem memória da conversa. Conexão ao GitHub não garante leitura automática, escrita, execução ou push: o agente verifica acesso e capacidades presentes e informa limitações.

### Comportamento diante de falhas

- Arquivo ausente: registrar ausência e trabalhar no que não depende dele; não inventar conteúdo.
- Engine indisponível: executar o que for possível fora dela e deixar gate de runtime pendente.
- Teste falhou: manter resultado, diagnosticar e corrigir dentro da fase.
- Teste foi pulado: registrar “não executado”, sem tratá-lo como aprovação.
- Ambiente perdeu contexto: ler estado e fonte vigente antes de continuar.
- Resultado ambíguo: reduzir a afirmação e definir verificação que resolva a dúvida.
- Orçamento esgotado: encerrar com aprendizados e artefatos existentes; não prometer geração futura já realizada.

## 11. Protocolo de AI Evaluation

Current implemented task: [P02 EVAL-001](evaluations/chat-send-buffering/README.md), a calibrated public practice harness without an independent candidate/model result. The examples below remain design guidance.

### Anatomy de uma task

Uma task precisa de problema significativo, baseline reproduzível, instruções suficientes, resultado esperado, método de aceitação e referência que realmente resolva o problema. Não exige grande aplicação.

| Artefato | Conteúdo |
|---|---|
| Brief | Contexto, bug/feature, reprodução e restrições |
| Baseline | Código/configuração inicial identificado por commit/hash |
| Aceitação | Comportamentos observáveis e invariantes |
| Referência | Solução demonstrada e explicação da causa |
| Tests/checks | Verificações proporcionais, incluindo regressão |
| Rubrica | Critérios, pesos, gates e evidências necessárias |
| Candidate record | Modelo/ferramenta disponível, data, contexto, tentativas, custo conhecido |
| Evaluation record | Resultados, falhas, score quando aplicável e decisão |

### Exemplo trabalhado de desenho, ainda não executado

**EVAL-004 — regeneração após respawn.**

Brief: “Quando o jogador morre com stamina esgotada e reaparece, a regeneração não retorna. Diagnostique e corrija preservando consumo, cooldown e comportamento normal.”

Aceitação proposta:

1. O fluxo de morte→respawn restaura os componentes previstos.
2. Sem input de consumo, stamina volta a regenerar após o atraso especificado.
3. Stamina respeita seus limites.
4. Respawns repetidos não duplicam regeneração ou callbacks.
5. Consumo e cooldown normais mantêm comportamento.
6. Alteração não elimina a morte nem força stamina máxima a cada frame para mascarar o bug.

A taxa, o atraso e o estado inicial são parâmetros definidos antes da avaliação. A solução não está codificada nesta seed. Nenhum modelo recebeu nota; nenhum teste desse cenário foi executado nesta entrega.

### Rubrica inicial sugerida

| Critério | Peso | Como avaliar |
|---|---:|---|
| Correção do comportamento | 40 | Checks da task e reprodução |
| Preservação de invariantes/regressões | 25 | Cenários normais e limites |
| Aderência ao escopo | 15 | Diff, arquivos e regras |
| Clareza/manutenibilidade | 10 | Revisão justificada, sem exigir preferência pessoal |
| Explicação e evidência | 10 | Diagnóstico consistente com alteração e execução |

**Gates:** solução não compila/executa quando essa execução é exigida → rejeitada; solução adultera checks ou remove a feature → rejeitada; violação de invariante crítica → rejeitada. Score parcial pode ser útil ao diagnóstico, mas não converte rejeição em aceite. Sem ambiente para o gate, resultado é inconclusivo.

### Independência e vazamento

Para avaliações reais, referência e checks reservados não ficam disponíveis ao agente de solução. Uma pasta chamada `hidden/` em repositório público não é escondida. Usar material fora do workspace/contexto do candidato ou um mecanismo de acesso efetivamente restrito.

Quando tudo for publicado, classificar como tarefa aberta e informar a data de exposição. É útil para portfólio e reprodução, mas não sustenta alegação de benchmark cego. Branches e tags são conveniências de versão, não barreiras de acesso a respostas em um clone.

### Comparação de candidatos

- Mesmo baseline, brief, ferramentas permitidas, limites e checks para todos.
- Registrar diferenças de contexto, modelo/versionamento disponível e condições.
- Não comparar uma tentativa sem assistência com outra com referência acessível.
- Repetições quando o objetivo exigir caracterizar variabilidade; registrar a amostra.
- Avaliação humana sem identificação do candidato quando viável e útil.
- Divergências entre avaliadores devem gerar discussão de critérios e evidências.
- Com uma task ou poucos candidatos, concluir somente sobre os casos observados.

### Taxonomia inicial de falhas

Requisito mal interpretado; suposição não registrada; arquivo errado; regressão; estado inconsistente; evento duplicado; erro temporal; serialização incompleta; teste inadequado; prova inventada; solução mascarada; documentação desatualizada; explicação desconectada do código.

## 12. QA e engenharia proporcionais

### Estratégia

Testar primeiro o risco da mudança. Regras de dinheiro, progressão, dano e timing se beneficiam de testes de domínio. Lifecycle, cenas, prefabs, input e integração exigem verificações de engine. Sensação de jogo, arte e música exigem avaliação humana.

Não adicionar centenas de testes que apenas repetem a implementação. Não usar cobertura como substituto de cenários relevantes.

### Exemplos de invariantes úteis

- Compra insuficiente é atômica: nenhum campo muda.
- Um input só consome uma nota compatível.
- Health e stamina respeitam limites especificados.
- Turno avança exatamente uma vez por resolução.
- Um status expira no momento definido, não no momento conveniente ao código.
- Save/load preserva campos de domínio suportados.
- Arquivo inválido gera comportamento de erro previsto, sem perda silenciosa do save íntegro.
- Carregar ou reiniciar não mantém inscrições duplicadas de eventos.

### Bug report

ID; título observável; versão/ambiente; precondições; passos; resultado esperado; observado; frequência; impacto; evidência; suspeita separada de diagnóstico confirmado; critério de fechamento.

Severidade descreve impacto; prioridade descreve ordem de trabalho. Um defeito cosmético pode ter alta prioridade para uma apresentação próxima sem virar falha crítica de sistema.

### Release gate de uma fatia executável

Entrar no fluxo principal; completar; reiniciar; não encontrar bloqueadores conhecidos no fluxo mostrado; listar limitações; fornecer instruções; registrar verificações; incluir build somente se produzida. A presença de um arquivo de configuração de CI não comprova que CI rodou.

## 13. Simulação, economia e dados

### Pergunta inicial recomendada

“No modelo simplificado de Artemyra, uma regra de catch-up reduz a vantagem acumulada sem tornar o resultado aleatório demais?”

Esse enunciado limita a conclusão ao modelo. Não afirmar comportamento de jogadores reais com partidas sintéticas.

### Contrato do simulador

Entradas: regras, starting resources, custo de objetivos, recompensas, penalidades, horizonte, políticas dos agentes, seed de RNG e versão do modelo.

Saídas: partida resumida, log de eventos, transações e agregados. Registrar schema e unidades. Separar configuração de código para comparar alternativas sem editar lógica a cada cenário.

Construir primeiro um smoke run pequeno; medir tempo/memória; só então subir para 10 mil ou 100 mil partidas quando houver pergunta que justifique a amostra. Esses volumes são candidatos de planejamento, não datasets já gerados.

### Métricas candidatas com definições

| Métrica | Definição inicial | Cuidado |
|---|---|---|
| Vitória por posição | Vitórias da posição / partidas válidas daquela posição | Rotacionar personagens e políticas |
| Tempo ao objetivo | Turnos até condição terminal | Separar partidas encerradas por limite |
| Saldo líquido de economia | Recursos criados − recursos removidos | Transferência entre jogadores não cria moeda |
| Spread de riqueza | Diferença entre percentis de saldo por rodada | Agregar por estado comparável |
| Vantagem do líder | Relação entre liderança em turno definido e vitória final | Declarar turno, empates e seleção |
| Comeback | Vitória de jogador com déficit pré-definido em marco definido | Evitar escolher marco após olhar resultado |
| Concentração de objetivos | Distribuição de sigilos entre jogadores | Distinguir regra de comportamento do agente |
| Snowball | Persistência/crescimento de vantagem sob definição prévia | Não chamar um número arbitrário de padrão universal |

### Método de comparação

1. Fixar baseline e uma hipótese antes de alterar parâmetros.
2. Implementar uma mudança principal de cada vez.
3. Rotacionar posições, personagens e políticas.
4. Controlar aleatoriedade; seeds pareadas só geram comparação pareada útil se o protocolo realmente alinhar cenários. Se chamadas divergem, explicar a perda de pareamento.
5. Escolher unidade de análise: normalmente partida, não cada evento como observação independente.
6. Apresentar efeito e incerteza quando a amostra e o método permitirem; bootstrap por partida/bloco se apropriado.
7. Testar sensibilidade a políticas, duração e parâmetros.
8. Documentar limites de representatividade e uma possível verificação com humanos.

**IAs de gameplay** são políticas de agentes no modelo. **Modelos generativos avaliados** são candidatos resolvendo tasks. Não misturar suas métricas.

### Telemetria e SQL

Eventos candidatos: `match_started`, `turn_started`, `space_landed`, `currency_gained`, `currency_spent`, `sigil_bought`, `curse_changed`, `minigame_started`, `minigame_finished`, `battle_started`, `battle_finished`, `match_finished`.

Contrato mínimo de evento: ID único, schema version, match ID, sequence, jogador quando aplicável, timestamp ou tempo de simulação, tipo, payload e versão de regras. Ordenação por sequence evita assumir que timestamps possuem precisão suficiente.

Usar tabelas dimensionais/factuais conforme necessidade. Começar em formato local simples e SQL acessível; data warehouse e dashboard complexo entram quando há volume e pergunta reais.

Retenção D1/D7 exige identidade/coorte e observação entre dias definidos. Partidas sintéticas de 15 turnos não são retenção. Dados simulados podem demonstrar uma query de retenção em dataset artificial explicitamente construído para isso, sem atribuir o resultado a jogadores de Artemyra.

## 14. Narrativa, imagens, áudio e adaptação

### Pipeline criativo comum

Brief → referência contextual → geração ou criação → seleção → correção → integração → avaliação no destino → registro de origem e lição.

Cada etapa deve servir à peça. Não obrigar toda criação a nascer de métrica; documentar decisão estética quando ela muda o resultado e pode ser explicada.

### Narrativa

Separar: fatos escolhidos do mundo; versões alternativas; eventos; conhecimento dos personagens; forma de narração. Um personagem ignorar uma verdade não é erro de continuidade; duas versões incompatíveis do mesmo fato precisam de decisão ou enquadramento.

Em adaptação, registrar o que muda com a mídia: informação que era monólogo pode virar ambiente; combate descrito pode exigir regra; lore pode ser omitido; narrativa longa pode virar uma única cena. Fidelidade ao efeito desejado pode valer mais que transposição literal.

Qualidade de texto: clareza, causalidade, voz, ação, ritmo, especificidade e emoção. LLMs podem sugerir problemas; Martin seleciona o que serve à obra e lê a versão final.

### Imagens

Um brief precisa identificar função, assunto, composição, estilo, paleta, escala, formato e restrições de uso. Referências não devem ser automaticamente copiadas para assets publicáveis.

Guardar preview leve e metadados no Git. Masters grandes têm destino próprio, com referência e hash. Quando uma correção alterar um personagem ou paleta compartilhada, registrar consumidores afetados.

Avaliar imagens já integradas: thumbnail de capa, texto sobre fundo, sprite em movimento, contraste em UI, consistência de personagem em cenas. A imagem isolada pode esconder o defeito que surge no produto.

### Áudio e música

Manter master, renders de integração e stems identificados. Se não houver stems, registrar sua ausência; não alegar produção por stems porque a ferramenta retorna uma faixa pronta.

Para rhythm game, documentar beat grid, offsets, chart version e o clock. Em Unity, considerar o relógio de áudio da engine e validar pausa, agendamento e offsets no hardware escolhido. Precisão do relógio não elimina latência perceptiva de dispositivo ou input.

Para áudio adaptativo, começar com duas camadas ou dois estados e transição definida. Medir se há corte, descontinuidade e comportamento incorreto no restart. Não escrever sistema amplo para uma única troca de música.

### Metadados de asset

ID; tipo; fonte; criador; ferramenta/modelo quando conhecido; data; arquivos; hash; projeto consumidor; função; parâmetros úteis; edição humana; uso autorizado/licença conhecida; restrições/pendências; estado de seleção e validação.

Ferramenta e licença desconhecidas ficam como desconhecidas. Origem gerada por IA não resolve automaticamente todos os direitos de referências, voz ou música.

### Localização

P03/P04 oferecem amostras de EN↔PT-BR. Criar master strings, contexto, glossário e revisão dentro do produto. Verificar placeholders, gênero, plural, quebras, limites de UI, tom e consistência. Tradução automática é etapa de produção, não aceite final.

## 15. Stack e migração

### Direção técnica proposta

| Área | Escolha inicial candidata | Motivo | Gate de adoção |
|---|---|---|---|
| Games/integração | Unity e C# | Direção profissional discutida e legado Unity | Ambiente abre projeto e gera execução mínima |
| Regras de jogo | C# separado da engine quando viável | Clareza e testes | Contrato simples e consumidor real |
| Simulação/dados | Python e SQL | Iteração quantitativa e base de BA/BI | Instalação e run reproduzíveis |
| Dashboards | Power BI ou relatório leve | Experiência existente e comunicação | Dataset e pergunta definidos |
| Conteúdo estruturado | JSON/CSV/Markdown | Revisão e diffs acessíveis | Schema, unidades e fonte de verdade |
| Controle de versão | Git/GitHub | Histórico e inspeção | Clone limpo e revisão de diff |
| Testes Unity | Unity Test Framework | EditMode/PlayMode e integração | Pacote/assemblies compatíveis e execução real |
| Mídia | Ferramentas disponíveis ao autor | Dependem das fontes e orçamento | Origem, exportação e validação conhecidas |

Versões de engine e bibliotecas devem ser fixadas após diagnóstico. Não instalar versões “mais recentes” por hábito nem escrever comandos incompatíveis com o ambiente real. Consultar documentação da versão escolhida e registrar upgrade como mudança técnica.

### Regra para migração RMXP → Unity

1. Extrair regras e dados úteis.
2. Identificar comportamento realmente observado no legado.
3. Definir o comportamento desejado na nova versão.
4. Escolher uma fatia independente de menus e conteúdo excessivo.
5. Reimplementar com contratos claros.
6. Comparar por invariantes e cenários, não por contagem de arquivos.
7. Integrar apresentação e testar na engine.
8. Encerrar quando a fatia provar o objetivo; não prometer paridade total.

RGSS/Ruby não deve ser traduzido mecanicamente linha por linha se carregar acoplamentos da engine antiga. Mapas e áudio não são automaticamente reutilizáveis só porque existem no pacote.

### Quando escolher outro formato

Uma amostra narrativa pode funcionar melhor como página estática ou ferramenta simples; uma prova de economia não precisa de Unity; um poema adaptado não precisa de jogo. Escolher a menor tecnologia que prove a hipótese e mantenha o artefato acessível.

## 16. Git, assets e publicação

### Fonte de verdade

Arquivos editáveis e histórico no Git; builds distribuíveis em releases ou destino adequado; grandes masters sob política explícita. Evitar commitar ZIP completo a cada alteração: isso impede compreender diffs e acumula duplicação.

Git LFS é candidato para binários selecionados, com instalação e política de custos verificadas antes do uso. Um pointer LFS não contém o asset; disponibilidade dos objetos deve fazer parte da verificação de clone. Não ativar LFS automaticamente para todos os arquivos de mídia sem avaliar tamanho e necessidade.

### O que versionar em Unity

Fontes, assets selecionados, respectivos `.meta`, `Packages` e `ProjectSettings` necessários. Ignorar caches locais como `Library`, `Temp`, logs e builds conforme projeto. Não ignorar `.meta` nem a pasta `Assets` inteira.

### Commits e revisões

Uma mudança coerente por commit quando possível; mensagem que descreva comportamento ou artefato. Não confundir número da release do laboratório com versão de todos os projetos.

Branches de trabalho e PRs podem tornar mudanças reviewáveis. Não reescrever histórico, apagar fontes antigas, fazer force-push ou publicar automaticamente por causa desta seed. Reorganização local reversível está no escopo; ações externas seguem a autorização concreta da sessão.

### Público, interno e externo

Pastas chamadas `private/`, `internal/` ou `hidden/` dentro de repositório público continuam públicas. A fronteira é permissão real do repositório/armazenamento, não nome de pasta.

Começar com workspace que Martin possa avaliar e apresentar só o que tem finalidade. Para materiais reservados ou checks de avaliação, usar acesso efetivamente separado. README público não deve conter análise pessoal sensível, prompt cru com dados corporativos ou todos os rascunhos de candidatura.

### Licenças

Escolher licença de código e regras de conteúdo quando houver intenção de distribuição. A escolha pode diferir entre código, imagens, música, narrativa e ativos externos. Não aplicar uma licença permissiva a conteúdo de terceiros sem autorização. O pacote inicial não decide licenciamento comercial por Martin.

## 17. Medir o trabalho sem inventar produtividade

### Métricas de produção úteis

Tempo ativo humano; tempo total; custos conhecidos; tentativas; retrabalho; defeitos detectados; critérios aprovados; tarefas encerradas; componentes reutilizados em consumidor real; feedback externo; limitações remanescentes.

Separar tempo de espera de ferramenta, tempo de execução e tempo ativo. Tokens/valores indisponíveis ficam desconhecidos, não zero. Medir economia de tempo exige baseline comparável; sensação de rapidez não vira percentual.

### Definições candidatas

- Taxa de aceite: entregas aprovadas / entregas avaliadas sob mesmo protocolo.
- Retrabalho: tempo ou alterações para atender critérios já definidos; mudanças de escopo separadas.
- Defeitos por severidade: falhas observadas por versão e procedimento, sem somar duplicatas.
- Reuso confirmado: componente/lesson aplicado e validado em segundo contexto.
- Custo por resultado aceito: custos conhecidos da execução / resultados aceitos, com custos excluídos declarados.

### Experimento de workflow candidato

Comparar dois fluxos de uma task equivalente: contexto mínimo versus especificação com critérios e checkpoints. Não utilizar a segunda execução, já aprendida, como prova automática de que o novo fluxo causou ganho. Registrar ordem, complexidade e experiência; preferir tarefas equivalentes diferentes ou múltiplas execuções quando a conclusão exigir.

O melhor resultado pode ser “IA ajudou a gerar alternativas, mas aumentou retrabalho nesta etapa”. Esse achado é valioso para consultoria e avaliação.

## 18. Transformar trabalho em portfólio

### Unidade pública: o case

Um case é menor que o projeto. Deve permitir entender uma decisão e um resultado sem ler centenas de páginas.

Estrutura recomendada: Problem → Requirements → Approach/Architecture → AI contribution → Human contribution → Validation → Results → Demo/Artifacts → Limitations → Lessons.

Se não houve participação humana em uma etapa, não usar a seção para atribuí-la artificialmente. Se a experiência é simulada, indicar no início.

### Seleção inicial de cases

| Case | Fonte | O que deve provar |
|---|---|---|
| Production audit | P01 | Diagnóstico, corte de escopo e prioridade baseada em evidência |
| Respawn evaluation task | P02 | Task verificável, regressão e julgamento de output de IA |
| Economy experiment | P01 | Modelo, análise e interpretação de limites |
| Rhythm vertical slice | P03 | Implementação integrada, timing e experiência jogável |
| Creative asset/adaptation study | P04/P07/P08 | Direção, seleção, consistência e integração entre mídias |

Essa é uma rota de candidatos; publicar somente os casos efetivamente desenvolvidos. Não criar cinco cartões com demos inexistentes.

### Tradução para funções profissionais

| Direção | Evidência de maior valor | Lacuna a desenvolver |
|---|---|---|
| Technical/Game Producer | Auditoria, backlog e gate encerrado | Pipeline real de game e release |
| AI Game Evaluation | Task, referência, candidato e avaliação | Diagnóstico de código/engine autônomo |
| QA/automação | Reprodução, teste e regressão | C#/engine/execução e triagem prática |
| Dados/produto | Dataset e análise que mudam decisão | Estatística e comportamento real quando disponível |
| Systems/economia | Simulação e tradeoff de regras | Balanceamento em contexto jogável |
| AI Workflow | Experimento de processo e custo | Baseline honesto e repetição suficiente |
| Technical Game Design | Spec→build→playtest | Prototipagem e integração |
| Prototype Developer | Build pequena e source utilizável | Debugging, empacotamento e manutenção |
| Localização/LQA | Strings contextualizadas e bugs na UI | Pipeline e avaliação dentro da build |
| Toolkit Publisher | Segundo consumidor e instalação por outra pessoa | API, suporte, compatibilidade e produto |

Funções criativas também podem ser atendidas por amostras e processos próprios; não exigir que literatura e música finjam ser engenharia para ter valor.

### Critério de apresentação

Um leitor consegue identificar o problema em menos de um minuto; encontra a amostra principal com poucos cliques; entende o que foi validado; sabe qual foi a contribuição de Martin. Essa meta orienta edição, não é métrica já medida.

Dados do trabalho real devem ser anonimizados sem inventar resultados. Cases simulados podem mostrar capacidade, mas não devem usar logotipos de empresas para insinuar contrato.

## 19. Roadmap por gates

Fases não são promessa de semanas. O calendário será construído após diagnóstico de disponibilidade, ambiente e esforço. Cada fase encerra com artefato e um gate; continuar significa escolher a próxima unidade, não crescer todas as frentes juntas.

### Fase 0 — descoberta e baseline

Objetivo: saber o que existe, o que funciona e qual direção vem primeiro.

Entregas: inventário pequeno; fonte selecionada por projeto prioritário; mapa de evidências; diagnóstico de ambiente; disponibilidade/orçamento; estado atualizado; uma fase de execução proposta.

Gate: arquivos recuperados ou lacunas explícitas; nenhuma versão antiga promovida por suposição; uma frente escolhida; critérios da próxima entrega claros.

### Fase 1 — auditoria de produção de P01

Objetivo: converter legado de Artemyra em uma decisão de MVP.

Entregas: estado atual; riscos; mapa de dependências; MVP; backlog curto; critérios de aceitação; release gates; case em rascunho. Consolidar documentos se isso reduzir redundância.

Gate: recomendações ligadas à inspeção; runtime testado quando disponível ou marcado pendente; escopo realizável; Martin compreende e consegue defender as três decisões mais relevantes.

### Fase 2 — primeira task de P02

Objetivo: demonstrar especificação, código pequeno e avaliação.

Entregas: aplicação mínima; uma falha controlada; referência; checks; um candidato real ou execução de solução por Martin; avaliação com evidências.

Gate: task reproduzível; referência resolve; checks detectam o bug; contexto da avaliação identificado; nenhuma nota inventada. Sem candidato avaliado, publicar apenas a task/reference e informar essa limitação.

### Fase 3 — experimento de economia de P01

Objetivo: testar uma hipótese simples com dados e decidir uma regra.

Entregas: modelo; configuração; baseline; variante; logs/amostra; script de agregação; análise; recomendação.

Gate: reprodução documentada; unidade de análise correta; limites da simulação; sensibilidade básica; resultado não apresentado como comportamento real de jogadores.

### Fase 4 — vertical slice de P03

Objetivo: unir mecânica, UI, áudio, arte e QA.

Entregas: uma faixa/chart; timing; combo/aura; uma habilidade; build; specs; testes; playtest; sample visual e áudio.

Gate: loop completo; comportamento de pausa/restart; origem dos assets; timing validado; vídeo ou amostra só se produzidos.

### Fase 5 — adaptação criativa pequena

Objetivo: usar P04/P07/P08 em uma peça com valor autoral próprio.

Entregas candidatas: cena interativa, animatic, poema musicado ou peça de áudio adaptativo. Escolher uma, com brief e critérios apropriados.

Gate: começo/meio/fim ou função completa; coerência criativa; qualidade no destino; proveniência; registro das perdas e ganhos da adaptação.

### Fase 6 — transferência e promoção

Objetivo: demonstrar que uma solução serve a mais de um contexto.

Entregas: duas aplicações verificadas; componente ou lição consolidada; contrato; exemplos; teste proporcional; custo de manutenção.

Gate: segundo consumidor real; reuso não artificial; nenhuma dependência circular; benefício maior que custo.

### Fase 7 — curadoria pública e validação externa

Objetivo: tornar poucos cases claros e utilizáveis.

Entregas: README curado; cases curtos; demos existentes; instruções; seleção de evidências; feedback de pessoa externa quando disponível; correções relevantes.

Gate: links funcionam; clone/execução verificados quando aplicável; claims corretos; material adequado ao público; Martin consegue explicar decisões e limitações.

### Fase 8 — produto ou serviço

Objetivo: experimentar uso profissional real quando houver evidências suficientes.

Possibilidades: audit de escopo definido, task de avaliação, protótipo pequeno, toolkit ou serviço criativo. Definir proposta, entregáveis, suporte, limites e custo real antes de preço. Não usar estimativas de remuneração da conversa como compromisso comercial.

Gate: alguém consegue utilizar o resultado; revisão de escopo e manutenção; aprendizado de feedback; histórico comercial declarado somente após acontecer.

## 20. Aprendizado de Martin

O portfólio precisa aumentar sua capacidade de atuar. Não basta acumular outputs que só a IA consegue explicar.

### Ciclo por unidade de trabalho

1. Martin tenta explicar o problema e o comportamento esperado.
2. IA ajuda a estruturar ou implementar.
3. Martin lê o diff e identifica as partes fundamentais.
4. Martin executa ou acompanha execução, conforme capacidade real.
5. Martin diagnostica um defeito pequeno sem outra IA na primeira tentativa.
6. Registrar o que consegue fazer sozinho e o que ainda exige assistência.

### Diagnóstico sugerido, sem nota de empregabilidade

Abrir projeto; localizar regra; prever output; alterar parâmetro; ler erro; executar teste; interpretar falha; corrigir bug simples; revisar diff; explicar tradeoff; gerar build quando houver engine.

O resultado é um mapa de próximos estudos. Não usar percentuais de autonomia fabricados. “Consegui explicar e corrigir este bug” é mais informativo que “sou intermediário em Unity”.

### Trilhas conectadas aos projetos

| Trilha | Estudo aplicado |
|---|---|
| C#/Unity | Classes, interfaces, coleções, eventos, lifecycle, cenas/prefabs, serialização, input, debugger |
| QA | Teste de domínio, EditMode/PlayMode, reprodução, regressão, impacto e evidência |
| Dados | SQL, agregação, window functions quando necessárias, probabilidade, simulação e incerteza |
| Git | Diff, commit, branch, PR, tags e recuperação de mudança |
| Narrativa/arte | Brief, voz, continuidade, seleção, composição, consistência e integração |
| Música/áudio | Forma, prosódia, exportação, loops, medição e integração |
| AI Evaluation | Task, rubrica, leakage, protocolo, evidência e julgamento |

Estudar o que destrava a próxima fatia. Não transformar a preparação em curso infinito antes de produzir a primeira evidência.

## 21. Riscos e gatilhos de replanejamento

| Risco | Sinal concreto | Resposta |
|---|---|---|
| Escopo cresce sem execução | Novos sistemas antes do primeiro loop | Cortar fase e encerrar uma fatia |
| Canon por repetição | Agente trata rascunho como fato porque aparece em muitos arquivos | Recuperar origem e decisão vigente |
| Progresso documental substitui produto | Mais roadmaps, nenhuma verificação nova | Escolher tarefa de execução |
| Arquitetura prematura | Framework com um consumidor hipotético | Implementar caso concreto primeiro |
| Dependência excessiva da IA | Martin não consegue explicar o diff | Reduzir unidade e fazer diagnóstico guiado |
| Benchmark contaminado | Resposta/check reservado está no contexto do candidato | Invalidar condição e refazer protocolo |
| Estatística enganosa | Eventos tratados como partidas ou retenção sintética como real | Corrigir unidade e reduzir conclusão |
| Reuso piora qualidade | Componente genérico força domínio errado | Adaptar, separar ou desfazer extração |
| Mídia inconsistente | Cada peça parece pertencer a obra distinta | Fixar brief e validar conjunto pequeno |
| Falta de origem | Asset sem fonte/uso conhecido | Registrar pendência e substituir se necessário |
| Custo sem visibilidade | Muitas gerações/retries sem resultado aceito | Medir custo conhecido e limitar experiência |
| Portfólio afirma experiência inexistente | Case simulado parece trabalho contratado | Corrigir apresentação e contribuição |
| Fonte desaparece | Dependência exclusiva de conversa ou link temporário | Preservar fonte útil e contexto em arquivos |
| Projeto perde finalidade | Nenhum público ou problema permanece claro | Pausar, fundir ou encerrar com aprendizado |

## 22. Modelos de registro

Os modelos abaixo são mínimos. Criar arquivos só quando usados; não preencher campos com fatos inventados para parecer completo.

### Project charter

```yaml
id: PXX
name: Nome atual
origin: Fonte histórica ou criação nova
purpose: Problema e público
status: seed
phase: triage
maturity: M0
current_slice: Entrega delimitada
inputs: []
outputs: []
constraints: []
acceptance: []
dependencies: []
evidence: []
unknowns: []
next_action: Ação verificável
```

### Execução/experimento

```yaml
id: RUN-XXX
project: PXX
date: null
hypothesis: null
baseline_commit_or_hash: null
environment: null
config: null
random_seed: null
procedure: null
metrics_definition: null
result: not_run
artifacts: []
limitations: []
decision: null
```

### Decisão

```yaml
id: ADR-XXX
date: null
scope: null
problem: null
options: []
evidence: []
decision: null
tradeoffs: []
revisit_trigger: null
supersedes: null
```

### Transferência

```yaml
id: XFER-XXX
source_project: PXX
target_project: PYY
kind: concept
status: candidate
source_evidence: []
adaptation: null
target_validation: []
shared_component: null
limitations: []
```

### Asset

```yaml
id: ASSET-XXX
kind: image
origin: null
creator: null
tool_or_model: null
files: []
sha256: null
license_or_usage_status: unknown
human_edits: []
consumer_projects: []
status: candidate
validation: []
```

### Conhecimento transferível

Problema → contexto → evidência → decisão → resultado → limites → destinos candidatos → resultado da transferência. Não registrar generalização sem listar limites.

## 23. Prompts de continuidade

### Iniciar o repositório a partir desta seed

> Leia SEED.md, AGENTS.md e docs/STATE.md. Execute a Fase 0 dentro das capacidades reais do ambiente. Inspecione os arquivos disponíveis, diferencie origem histórica de evidência atual e atualize o inventário. Selecione uma frente principal com base na proposta e nos materiais acessíveis. Produza o diagnóstico e uma fase de execução pequena com entregáveis e critérios. Não invente fontes, builds, métricas ou resultados. Registre lacunas e avance no trabalho que não depende delas.

### Planejar uma fase específica

> Planeje a próxima fase de [projeto/objetivo]. Leia o estado e os documentos pertinentes; não reconstrua decisões já registradas sem motivo. Defina problema, fatia, dependências, artefatos, aceitação, riscos e cortes. Diferencie opções de compromissos. Prepare uma tarefa que possa ser executada e verificada no ambiente disponível.

### Desenvolver e verificar

> Execute a fase aprovada de [projeto]. Inspecione a fonte real, implemente a menor solução coerente, verifique riscos relevantes e registre os resultados. Preserve as alterações anteriores do autor. Atualize estado e decisões importantes. Entregue artefatos, evidências e limites, sem substituir execução por explicação.

### Fazer os projetos aprenderem entre si

> Examine as lições e os componentes de [origem] e o problema atual de [destino]. Escolha no máximo uma transferência útil. Registre diferenças, adapte e valide no destino. Promova para shared apenas se houver necessidade real e contrato claro. Relate também transferências descartadas e por quê.

### Avaliar um candidato de IA

> Use o protocolo da task [ID]. Verifique baseline, ambiente, contexto e ausência de vazamento. Execute os checks disponíveis, examine o diff e aplique gates e rubrica com evidências. Se faltar condição essencial, marque a avaliação como inconclusiva. Não conceda score ou aceite a comportamento não observado.

### Curar um case público

> Transforme [trabalho encerrado] em case curto para [público/função]. Use somente afirmações sustentadas. Mostre problema, decisão, contribuição real da IA e de Martin, validação, resultado, amostra e limites. Remova material interno sem função para o público. Verifique os links e não apresente simulação como experiência comercial.

### Retomar em outra sessão

> Leia o estado atual e o handoff. Identifique a última unidade concluída, bloqueios e próxima ação. Verifique os arquivos necessários antes de agir. Continue a unidade definida; se a fonte ou o ambiente mudou, registre a diferença e ajuste a execução.

### Revisar a própria seed

> Revise SEED.md à luz das decisões e evidências novas. Atualize inventário, direção ou regras que estejam superadas; preserve a origem e explique mudanças relevantes. Não acrescente todo histórico de execução. Reduza redundância e mantenha o arquivo útil para iniciar trabalho.

## 24. Primeiras tarefas propostas

| ID | Trabalho | Saída concreta | Dependência |
|---|---|---|---|
| BOOT-001 | Definir recursos disponíveis | Diagnóstico de ambiente, tempo e orçamento | Martin/ambiente |
| BOOT-002 | Recuperar um pacote de Artemyra | Inventário e baseline selecionado | Fonte acessível |
| BOOT-003 | Separar especificado de executado | Matriz de evidência do P01 | BOOT-002 |
| BOOT-004 | Definir MVP de auditoria | Escopo, riscos e critérios | BOOT-003 |
| BOOT-005 | Diagnosticar C#/Unity | Uma execução pequena e mapa de autonomia | Ambiente compatível |
| BOOT-006 | Recuperar material de AI Evaluation | Lista de cases utilizáveis e correções necessárias | Arquivos anteriores |
| BOOT-007 | Catalogar amostras criativas | Pequena seleção visual/áudio/texto com proveniência | Fontes disponíveis |
| BOOT-008 | Encerrar a Fase 0 | STATE atualizado e próximo entregável definido | Tarefas essenciais acima |

Não fazer todas as tarefas dependerem de todos os projetos. BOOT-002–004 podem avançar antes do catálogo completo de poemas; BOOT-007 pode usar três amostras, sem inventariar milhares de ativos na primeira fase.

## 25. Definição de sucesso

Este laboratório terá sucesso quando Martin possuir um conjunto pequeno de trabalhos que consegue explicar, demonstrar, adaptar e manter, apoiado por fontes e registros que outra pessoa consegue inspecionar.

A obra criativa deve valer a experiência de quem a consome. A parte técnica deve tornar o processo e o comportamento verificáveis. A colaboração com IA deve mostrar escolhas, correções e aprendizado. Nenhum desses objetivos é atendido apenas pelo tamanho do diretório.

### Critérios observáveis

- Uma fase produz artefato útil e estado retomável.
- Um case mostra resultado e limites de forma honesta.
- Uma task detecta uma falha antes da correção e verifica o comportamento depois.
- Um experimento altera uma decisão com método compreensível.
- Uma transferência funciona em um segundo contexto.
- Uma amostra criativa é integrada e avaliada no destino.
- Martin desenvolve capacidade de diagnosticar e explicar o núcleo do trabalho.
- Um revisor encontra poucos cases claros em vez de um catálogo de promessas.

## 26. Referências técnicas consultadas

Consultadas em 10/10/2026. São apoio aos pontos técnicos, não pesquisa de mercado ou validação dos projetos. Verificar a documentação da versão efetivamente adotada ao implementar.

- [Unity — AudioSettings.dspTime](https://docs.unity3d.com/ScriptReference/AudioSettings-dspTime.html): relógio do sistema de áudio baseado em samples, apropriado para investigar sincronização.
- [Unity — Automated tests with Unity Test Framework](https://unity.com/how-to/automated-tests-unity-test-framework): estratégias e integração de testes na engine.
- [GitHub — About Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage): objetos grandes separados de pointers versionados.
- [GitHub — About large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github): limitações e distribuição de binários por releases.

## 27. Histórico desta seed

### 0.1.0 — 10/10/2026

- Fundação do monorepositório a partir da autorização de transformação integral.
- Consolidação de perfil profissional, nove linhas de projeto e limites de evidência.
- Incorporação do estado de worldbuilding de Lich v0.4.48, superando pressupostos de versões antigas.
- Proposta de transferência de conhecimento, fases, critérios, operação com IA, avaliação, dados, mídias e portfólio.
- Criação de pacote documental inicial, sem importar fontes completas ou alegar execução dos projetos.

### 0.2.0 — 10/10/2026

- Inspeção de dois snapshots GitHub e inventário de 732 arquivos.
- Leitura de 180 fontes textuais e preservação seletiva de 178, com hashes de origem conferidos.
- Integração de P10/P11, sistemas recuperados, limitações, dívida técnica e transferências candidatas.
- Reprodução de dois runners Python e verificação sintática do servidor Node.
- Substituição do tutorial de envio ao Git por instruções de evolução da seed.
- Nenhuma alteração, exclusão ou aposentadoria aplicada aos remotes.

### 0.3.0 — 2026-10-10

- Selected P11 as one executable increment under the current user request.
- Reproduced the original missing receive/render behavior, then implemented a local chat in a working project while preserving the historical ZIP and inventory.
- Added locked dependencies, explicit event/outage rules, and 15 protocol/browser tests; recorded current environment and artifact hashes outside the seed.
- Added maintained assessment and priorities, updated project continuity, and corrected the manifest's absent-file references.
- Recorded transfer lessons as candidates; no model evaluation, public deployment, game migration, or shared abstraction was claimed.

### 0.4.2 — 2026-10-11

- Corrected P11 reading disruption during broadcasts and retention eviction;
  five new checks reproduce three failures on 0.1.1; all 22 chat checks pass.
- Carried fractional correction after measured 4.0625-pixel drift; preserved
  dependencies, transport and the 200-message window.
- Recalibrated P02 runner 0.1.2 without changing its 17 tests, nine export files
  or contract 0.1.0. No independent candidate or human review is claimed.
- Preserved sources/evidence; current state records authorized publication
  after checking remote Git refs.

### 0.4.1 — 2026-10-10

- Corrected P02 timeout/launch records and inherited-process cleanup; 15 tests
  pass, with 7 new methods failing against the recorded old runner.
- Kept starter contract 0.1.0 byte-identical; runner 0.1.1 identifies the change.
  Old exports retain known 15/17 and 17/17 calibration outcomes.
- Preserved previous evidence and sources; no independent model, sandbox,
  game runtime, human review, or new publication claim.

### 0.4.0 — 2026-10-10

- Implemented P02 EVAL-001 export and artifact checker using pinned P11 sources/tests.
- Calibrated baseline at 15/17 and reference at 17/17; 8 runner regressions passed;
  missing-browser probe stayed inconclusive; exported starter install/CLI verified.
- Validated TR-009 for task adaptation only. No independent model attempt, score,
  shared framework, Unity execution, human review, or new publication claimed.
- Corrected current Git state: previous P11 commits are published in `df1bd59`;
  this iteration remains local. Historical archives and earlier evidence preserved.

### 0.3.1 — 2026-10-10

- Continued from committed P11 0.1.0 instead of repeating the original recovery.
- Reproduced connected-send loss during live polling congestion and a controlled stale-state reconnect queue; the same tests fail on the recorded old client and pass on 0.1.1.
- Kept normal live-transport buffering while clearing the distinct reconnect queue, retaining draft and uncertain-delivery semantics without retry or persistence.
- Verified 17 current protocol/browser tests and unchanged dependency resolutions; updated existing assessment, plan, state, and candidate lessons.
- Preserved historical archives, source inventory, and earlier execution evidence. No human review, destination transfer, model evaluation, or remote publication was attributed.

**Next action recorded at 0.3.1:** Martin's local two-tab review remains pending before portfolio selection. A bounded P02 task with candidate/reference isolation can be prepared independently; no evaluation or transfer is implied. P01 baseline recovery remains pending if that workstream is selected.

## 28. Recuperação dos repositórios antigos — v0.2.0

### 28.1. Mandato, alcance e preservação

Martin solicitou a inspeção de dois repositórios que considera aposentar e a incorporação de informações úteis à seed. Aposentar uma origem pode simplificar a produção; preservar sua informação útil evita recomeçar do zero. A migração realizada nesta versão é documental e seletiva, com preservação de fontes textuais. Não houve arquivamento, exclusão, alteração ou publicação dos repositórios de origem.

| Fonte | Snapshot inspecionado | Inventário | Conteúdo lido | Conteúdo preservado |
|---|---|---|---|---|
| Adventures_Unleashed_Rave_Master_Project | `main`, commit `36af1651271422ae33856e8b5d7b45702215f165` | 729 arquivos; árvore retornada completa | 177 arquivos textuais selecionados | 175 arquivos textuais |
| WebSocket | `main`, commit `df651a9ddef39c7b05a48f25f1b7fdaff6760185` | 3 arquivos; árvore retornada completa | Os 3 arquivos | Os 3 arquivos |

**Fontes primárias:** [Rave Master no snapshot](https://github.com/MartinFMelcop/Adventures_Unleashed_Rave_Master_Project/tree/36af1651271422ae33856e8b5d7b45702215f165) e [WebSocket no snapshot](https://github.com/MartinFMelcop/WebSocket/tree/df651a9ddef39c7b05a48f25f1b7fdaff6760185). O Rave era privado no momento da consulta; seus links exigem acesso correspondente. O WebSocket era público. Preservação para o laboratório e disponibilidade pública são decisões distintas.

No pacote desta versão, `registry/legacy_sources.json` registra todos os caminhos e hashes Git dos snapshots, quais conteúdos foram lidos e quais foram preservados. `archive/legacy-source-extracts-v0.2.0.zip` preserva os 178 arquivos selecionados, com bytes conferidos pelos hashes Git; os prefixos `rave/` e `websocket/` identificam a origem. Foram excluídos dois digests sobre material de terceiros: manual RGSS e light novels de Overlord. O acervo não inclui livros integrais, binários do jogo, imagens, áudio, histórico Git, branches ou um backup integral do Rave.

Esta seção é autossuficiente como síntese de direção. O acervo é necessário somente para reexaminar uma fonte exata. Não declarar um arquivo antigo preservado se o inventário disser apenas que seu caminho foi identificado. Um snapshot de `main` não descreve automaticamente branches, versões locais ou conteúdo excluído anteriormente.

### 28.2. P10 — Adventures Unleashed / Rave Master como reservatório

**Natureza recuperada:** projeto RPG Maker XP/Ruby RGSS, com produção orientada a dados e forte documentação para IA. O conteúdo útil se distribui por `RM_CORE` (regras e contratos), `RM_ACT1` (conteúdo e scripts de desenvolvimento), `RM_QA` (cenários, relatórios e ferramentas), `RM_ART` (direção e registros de assets), `RM_DIST` (estrutura de distribuição RMXP) e `RM_LEGACY` (referências). O README da raiz é uma entrada genérica; a documentação substantiva inclui `RM_CORE/README_RM_MAIN.md`, especificações e tabelas.

P10 entra como fonte recuperada, com duas verificações offline reproduzidas. Não é compromisso de concluir o RPG inteiro. Uma futura versão pode eliminar sua marca, reduzir seu mundo a uma vila, transformar o diálogo em aplicativo ou transportar combate para C# sem preservar engine, escala ou canon. Também não há evidência suficiente para declarar que P10, The Dark Knight, Artemyra, Véu Partido e Lich são o mesmo projeto ou compartilham universo. Similaridade de regras e faixas de nível não prova identidade.

#### Narrativa, mundo e exploração

O Ato I combina quatro linhas de trabalho: investigação de Rose (`TH_ROSE`), vida e serviços da vila (`VILA_ROSE_LIFE`), Mago Louco (`MAD_MAGE_ARC`) e Ruínas Goblin (`GOBLIN_RUINS_ARC`). A vila, os mentores e a reputação ligam história à exploração e ao aprendizado de combate. O Mago Louco oferece um registro de personalidade preguiçosa e sarcástica, associado a Waystones, golem e teleporte. Esses elementos podem originar cenas, sistemas ou um conto; não exigem reconstruir toda a campanha.

O fluxo documentado inclui introdução em slideshow na capital, criação de personagem e entrada na vila. Há endereços de chunk como `24R0_I` e uma âncora de sandbox `23T3`; seu papel precisa ser entendido antes de migrar mapas. A especificação de topologia estabelece um pai e até três filhos por chunk, com entradas/saídas e ligações de interiores. Isso é um contrato do mundo antigo, não uma regra universal para o board de Artemyra. A ideia transferível é validar conexões, retorno e continuidade espacial.

O digest do **Livro dos 100 Contos** apresenta páginas colecionáveis, fraturas temporais, calendário, Calamidades e Waystones. Páginas podem calibrar acesso a eventos; os eventos Eco tornam repetição uma propriedade do mundo. Foi recuperado um digest, não o manuscrito integral do livro nem uma comprovação independente de autoria. É uma origem candidata para narrativa interativa, contos, exploração ou composição musical em P04/P08. Nomes e povos desse material não entram automaticamente no canon de Lich.

O modelo distingue eventos ativos de instâncias Eco sempre disponíveis. O Eco reduz eficiência e oferece recuperação de acesso: os multiplicadores históricos são 0,75 para recompensa, 0,90 para tokens e 0,85 para drops. A oportunidade de design é permitir que o jogador recupere conteúdo ou recursos sem depender de uma janela perdida. Os números são parâmetros candidatos, não balanceamento comprovado nem obrigação de introduzir temporadas em um produto pequeno.

#### Personalidade, diálogo e memória

O desenho separa personalidade estável, estado transitório, relações e contexto social. Existem **10 eixos de 0 a 100**: empatia, assertividade, necessidade de ordem, novidade, risco, paciência, volatilidade, confiança basal, pragmatismo e franqueza. Há 16 arquétipos, incluindo Guardian, Opportunist, Diplomat, Hothead, Stoic, Scholar, Rebel, Caretaker e Explorer. Arquétipo pode oferecer um ponto de partida; não deve reduzir todo personagem a um rótulo.

Estado inclui stress, medo e mood; relações incluem confiança, respeito e dívida; facções e cultura oferecem normas. Intenções de diálogo selecionam variantes preescritas com condições, prioridade e pontuação. Flags e eventos recentes com tempo de vida oferecem memória limitada. Essa arquitetura é útil para distinguir “quem é o NPC”, “como ele está” e “o que aconteceu entre os participantes”.

O piloto `NPC-0007` explora absorção de tensão, explosão e afastamento, com condições de manipulação, obsessão e flags temporárias. Pode gerar uma cena interativa curta na qual Martin e um avaliador expliquem por que uma resposta foi escolhida. O estado recuperado não demonstra conversa livre com LLM, modelo treinado ou personagem autônomo aprendendo online.

**Limite importante:** o runner Python de cenários usa a ordem `(Priority, BaseScore)` para escolher variantes elegíveis. Ele não prova a implementação completa da personalidade ponderada descrita pela especificação. O runtime Ruby e o runner também possuem abordagens diferentes de interpretação de condições. Uma extração deve definir uma gramática explícita de expressões e casos de equivalência, sem presumir que parsers diferentes tenham comportamento idêntico.

**Primeira fatia candidata:** um NPC, três intenções, poucas variantes e dois estados transitórios; inspeção de candidatos e motivo da escolha; evento que altera a resposta; expiração demonstrada da memória. Gate: entrada conhecida produz resposta e transição esperadas; condições inválidas têm comportamento definido; um revisor entende o resultado sem ler centenas de tabelas.

#### Combate, progressão e economia

O acervo inclui 134 registros de regras de combate, fórmulas, tabelas de XP e scripts de domínio. Dez classes aparecem no canon do Ato I: Knight, Warrior, Berserker, Rogue, Ranger, Pyromancer, Cryomancer, Druid, Cleric e Shaman. Há 14 registros de raças no arquivo de construção; isso não significa 14 raças jogáveis no Ato I. A curva de personagem cobre níveis 1–180, e a de perícia, 1–99. Essa escala oferece dados para análise de curva e testes de limites; a nova fatia pode usar dez níveis e duas classes.

| Regra recuperada | Semântica útil | Decisão necessária na extração |
|---|---|---|
| Acerto | Razão ACC/(ACC+EVA), fator de diferença de nível e limites de 5–95% | Denominador zero, valores inválidos e controle de aleatoriedade |
| Crítico | CRIT percentual, chance limitada a 50%, multiplicador histórico 1,5 | Relação com defesa, letalidade e ordem das operações |
| Dano bruto | Atributo ofensivo × escala × (1 + letalidade) | Tipos físicos/mágicos usados na pequena fatia |
| Mitigação | K = 100 + 10 × nível defensor; fator K/(K + defesa) | Mínimo de dano e domínio admissível de defesa |
| Aplicação de status | Razão EFF/(EFF+RES), limites de 5–95% | Separação de chance de acerto e chance de aplicar |
| Duração | Base alterada por duração aplicada e tenacidade; mínimo 1 | Unidade de tempo, arredondamento e reaplicação |
| Dano periódico | Regras percentuais e soma de duração na reaplicação | Ordem de tick, morte, cleanse e limites de acumulação |

As fórmulas recuperadas são uma baseline histórica. O módulo Ruby de combate oferece helpers e documenta integração de batalha pendente; tabelas declaradas não significam que todos os seus parâmetros sejam carregados dinamicamente pelo runtime. Alguns helpers têm defaults codificados. Ao migrar Python/Ruby/C#, explicitar arredondamento, tipos e limites: um teste aproximado de fórmula não substitui uma regra de execução comum.

Receitas de crafting, estações, recursos, desbloqueios e respawn por dias de jogo oferecem outro recorte. Uma boa primeira tarefa testa uma transação inteira: validar requisitos, consumir materiais, conceder produto e XP ou falhar sem consumo parcial. Separar relógio de jogo de relógio real, escopo de cooldown e bônus de primeira realização. P01 pode aproveitar esse conhecimento sem herdar toda a economia do RPG.

Reputação regional tem efeitos explícitos em loja, spawn, aggro, diálogo e acesso, com composição por substituição, multiplicação, soma ou máximo. A escala antiga `-3, -2, -1, +1, +2, +3` não usa zero. Esse detalhe deve ser revisado se um novo produto precisar de neutralidade. A ideia transferível é ligar consequência narrativa a parâmetros verificáveis, com regras de composição declaradas.

#### Arte, som e conteúdo planejado

A direção de pixel art especifica grid de 32 pixels, frames de 32×48 e spritesheet de 128×192 com 4×4 frames; inclui coerência de luz, paleta, autotiles, passabilidade e legibilidade. O que se transfere é um contrato verificável entre brief, exportação e engine. Dimensões próprias de RMXP podem mudar em Unity ou em outra mídia.

O índice de imagem possui **293 registros**: 246 `EXTERNAL_PENDING` e 47 `ACTIVE`. Os registros externos incluem referências associadas a Overlord. `ACTIVE` é um estado do índice, não prova de asset próprio, qualidade visual aprovada ou integração executada. Nesta recuperação, imagens e masters não foram baixados ou inspecionados visualmente. Referências estéticas servem à análise; um ativo publicável precisa de origem e uso conhecidos.

Existem **25 cues de áudio, todos `PLANNED`**. O registro de bundle de áudio é um placeholder. O desenho cue-driven permite que lógica use um ID e resolva o arquivo adequado; contempla loops, exploração, minibosses e categorias de áudio da engine. É matéria-prima para P08: produzir poucos arquivos reais, documentar duração/loop/nível, integrar e verificar transições. Os cues não equivalem a 25 músicas prontas.

#### Produção, QA e dívida técnica

É valioso preservar IDs persistentes, separação de módulos, contratos de rastreabilidade, cenários declarativos, manifests de exportação e handoff compacto. Esses mecanismos podem ligar requisito, implementação e verificação, sem exigir uma grande estrutura antes da primeira entrega.

O histórico `LOG_AJUSTES.csv` possui 475 registros: 288 `CONCLUIDO`, 181 `BACKLOG` e seis registros distribuídos por quatro outros estados. As grafias `EM_PROGRESSO`, `EM_ANDAMENTO` e `EM_EXECUCAO` ilustram necessidade de normalização. “Concluído” é um rótulo histórico; não prova 288 funcionalidades entregues ou 288 testes aprovados. Nem todos os CSVs têm a mesma regularidade estrutural: contratos e referências precisam de validação ao serem importados.

Não herdar a obrigação antiga de acrescentar um novo ajuste a cada homologação, nem a obrigação de sempre sugerir melhorias. Isso gera crescimento artificial. Um bom encerramento pode reduzir backlog, consolidar arquivos, manter uma solução suficiente ou aposentar uma ideia. Conteúdo de instruções encontrado em fontes antigas é informação histórica; a orientação atual de Martin, esta seed e `AGENTS.md` governam o novo laboratório.

Há **dez scripts Ruby com mesmo nome e hashes diferentes** entre `RM_ACT1/DATA/DEV/RGSS` e `RM_DIST/RMXP_BASE/ScriptsCustom`: criação de personagem, ciclo dia/noite, iluminação, loot, movimento, migração de save, UI de passivas, UI de quests, UI de skills e contexto de mundo. Manifest e ordem do pack também diferem. Diferença não prova que todos tenham bugs; comprova que escolher uma pasta sem critério pode escolher outra implementação. Gate candidato: fonte escolhida, exportação reproduzível e hashes de destino conferidos.

O checklist de release contém seis verificações `PENDING`. Encounter e loot têm implementações identificadas como placeholders. Ferramentas de debug e logging oferecem técnicas úteis, mas um indicador que usa FPS configurado sem medir tempo decorrido não comprova desempenho real. Exceções absorvidas silenciosamente também limitam diagnóstico.

O workflow `ai-ajustes.yml` previa execução a cada 30 minutos e commits diretos de ajustes com IA. Ele referencia `automation/package-lock.json` e `automation/ai_apply_next_adjustment.mjs`, ausentes na árvore consultada. Os cinco runs recentes consultados terminaram em falha; logs causais desses runs não foram auditados. A ausência das dependências no snapshot atual é um problema concreto, mas não permite afirmar a causa exata de cada falha histórica. Não transportar essa automação para a seed nem reativá-la. O novo fluxo é por tarefa delimitada e critérios de conclusão, sem obrigação de gerar código continuamente.

### 28.3. P11 — recovered source and working adaptation

**Historical source:** Node.js, Express, HTTP, and Socket.IO exercise, commit
`df651a9ddef39c7b05a48f25f1b7fdaff6760185`. The snapshot contains only
`index.js`, `index.html`, and `package.json`. It uses Socket.IO rather than a
manual WebSocket implementation. The server logs `chat message`; it does not
broadcast, and the page has no receive/render listener. The historical package
has no lockfile and its test script is a failing placeholder. Its declared ISC
metadata does not establish licensing for unrelated material.

**Historical working increment (0.1.2):** [P11 — Live exchange](projects/realtime-integration-lab/README.md),
version 0.1.2, separate from the unchanged historical archive. Retain the event
name and string payload. Accept trimmed non-empty text, enforce 500 UTF-16 code
units before trimming, broadcast to all connected clients including the sender,
and render text nodes. Rejection and connection state are visible. A single
broadcast path prevents an optimistic duplicate. Retain at most 200 items per
page; no server history, accounts, rooms, offline buffering, or automatic retry.
Acknowledgement loss leaves delivery uncertain and keeps the draft. Manual
resubmission may duplicate an already delivered message.

The 0.1.1 correction permits the live Engine.IO write queue to drain during
polling congestion, then clears Socket.IO's distinct reconnect buffer. Two new
checks fail against the recorded 0.1.0 client: volatile emission discards a
connected form submission behind an in-flight polling write, and heartbeat expiry
can queue a packet before `connected` becomes false. This correction preserves
the no-replay policy without adding automatic retry or durable delivery.

**Historical evidence at 0.1.2:** the same browser delivery check fails against the preserved source
and passes against the adaptation. Twenty-two current tests (6 protocol, 16 Chromium)
verify accepted/rejected payloads, two-way rendering, literal markup, drafts,
rejoining/new clients, automatic transport reconnect, bounded history,
acknowledgement behavior, live polling congestion, stale-state reconnect policy,
and retained reading position with a 24-pixel following threshold.
The original CLI startup smoke remains prior evidence; the unchanged server was
not restarted separately in this correction session. See
[current reading evidence](evidence/realtime-chat/READING_RUN.json),
[prior transport evidence](evidence/realtime-chat/POLLING_SEND_RUN.json) and
[original adaptation evidence](evidence/realtime-chat/RUN.json). This is local automated validation,
not human usability review, public hosting, a game playtest, or a model benchmark.

**Destination status:** P02 now uses these defects in EVAL-001, with an allowlisted
starter and calibrated artifact gates. TR-009 is verified for that adaptation;
no independent model was evaluated. P01 lobby reuse still needs its own state and
recovery contract. No shared library was introduced. Martin supplied direction;
Codex implemented/tested the slices. Martin's manual two-tab review remains pending.

### 28.4. Historical verification from the v0.2.0 recovery

| Verificação atual | Resultado | O que prova | O que permanece fora do alcance |
|---|---|---|---|
| Runner Python de vetores de combate | 49 checks; zero falhas; exit 0 | Os vetores selecionados atendem às expectativas do runner nesse ambiente | Integração Ruby, batalha RMXP, comportamento Unity e balanceamento com jogadores |
| Runner Python de cenários de diálogo | 19 etapas em 10 cenários; zero cenários falhos; exit 0 | Seleção/transição esperadas para os dados e o subconjunto do runner | Scoring completo por personalidade, equivalência RGSS e qualidade narrativa |
| `node --check index.js` | Exit 0 em Node 24.19.0 | Sintaxe do arquivo aceita pelo Node usado | Resolução de dependências, rede, UI e comunicação entre clientes |
| Preservação textual | 178 conteúdos conferidos contra hashes Git de origem | Acervo selecionado corresponde aos blobs dos snapshots | Backup de binários, conteúdo de branches e histórico completo |

Ambiente dos runners: Python 3.12.14, em cópia local selecionada dos arquivos. Ruby não estava disponível, e o RPG Maker XP não foi executado. Relatórios atuais estão em `evidence/legacy-audit/`; os relatórios antigos dentro do acervo mantêm seu status histórico. O sucesso atual também precisa de contexto: um runner que aceita zero vetores ou um cenário sem etapas pode produzir PASS sem evidência suficiente. Ao torná-lo gate do laboratório, exigir a quantidade mínima esperada e identificar exatamente o que foi verificado.

### 28.5. Transferências candidatas e ordem de decisão

| Origem → destino | Unidade útil | Primeira prova | Limite |
|---|---|---|---|
| P10 → P02 | Vetores de combate e comportamento de diálogo | Bug controlado detectado antes e corrigido depois | Não alegar avaliação de modelo sem executar candidatos |
| P10 → P04 | Estado, memória e escolhas de NPC | Cena curta com consequência observável | Não fundir universos por semelhança |
| P10 → P05/P06 | Fórmula de dano/status e casos de fronteira | Um domínio puro reproduz vetores escolhidos | Integração na engine é outra verificação |
| P10 → P01 | Transação, crafting ou acesso por recursos | Regra adaptada funciona em contexto do board | Escala e mapa do RPG antigo não acompanham automaticamente |
| P10 → P07 | Brief, grid, paleta e passabilidade | Um asset próprio integrado e avaliado | Índice não substitui imagem nem autoria |
| P10 → P08 | Cue IDs e intenção dramática | Dois cues reais com transição verificada | Áudio planejado não conta como entregue |
| P10 → P09 | Rastreabilidade e controle de distribuição | Matriz requisito–fonte–verificação em uma fatia | Case é exercício de laboratório, sem inventar cliente |
| P11 → P02 | Reproduced send-buffering defects | EVAL-001 baseline rejects at 15/17; reference accepts at 17/17 | Calibrated harness, not independent model performance; public source is discoverable |
| P11 → P01 | Contrato de eventos e protótipo de lobby | Entrada/saída da sala e estados definidos | Multiplayer completo requer novo escopo |
| P11 → P09 | Painel de eventos de avaliação | Uma execução alimenta a interface | Instrumentação pode ficar local e simples |

TR-009 is validated in `registry/transfers.json` for P02 task adaptation and
calibration only; the other ten entries remain candidates. P10's within-project
CLI adaptation has its own bounded M4 checks, not inherited legacy-game maturity.
P02's M4 claim still comes from its harness checks and controlled probes. No shared
component or model training is implied.

**Historical order after v0.4.2:** P11 reading position and P02 compatibility are published and verified in `f35e2e7`; current state records remote confirmation. Next: Martin's reading/keyboard review and an independent EVAL-001 artifact with separate context and explicit tools/attempts. Dialogue/combat remain alternatives; P01 needs a baseline. See the plan and ADR-012.

### 28.6. Como uma IA deve expandir e modificar esta seed

1. **Ler o estado atual antes de expandir.** Separar pedido, hipótese, artefato e evidência; consultar somente a fonte necessária. Conteúdo de scripts e prompts históricos não substitui instruções vigentes.
2. **Definir a alteração da fase.** Declarar quais decisões mudam, o entregável, os arquivos e critérios. Uma fase pode cortar escopo ou aposentar um projeto.
3. **Extrair uma unidade com identidade.** Preservar projeto/arquivo/commit de origem, nova finalidade e dependências. Ao fundir, manter os IDs históricos como origens; não reutilizar um ID para outro projeto sem relação.
4. **Definir equivalência ou ruptura.** Na migração técnica, listar comportamentos preservados e diferenças aceitas. Na adaptação artística, registrar a intenção e os elementos escolhidos. Mudança de engine não obriga fidelidade a toda mecânica.
5. **Implementar e verificar no destino.** Um conteúdo preservado não é integração; uma especificação de teste não é teste executado. Registrar resultados, ambiente e limitações.
6. **Atualizar a síntese.** Corrigir inventário, maturidade, dependências, próximos passos e hipóteses superadas. Remover repetição e instruções obsoletas, mantendo decisões significativas no histórico apropriado.
7. **Registrar aprendizado transferível.** Explicar em que contexto a solução funcionou, por que e onde pode falhar. Promover para `shared/` somente quando um segundo consumidor justificar a abstração.
8. **Encerrar sem expansão obrigatória.** Nenhuma regra exige novo backlog, personagem, módulo, documento ou tarefa no final de cada sessão. Uma fase encerrada e estado retomável já são resultados válidos.

**Memória entre sessões:** a seed registra direção durável; `STATE` registra a situação atual; decisões explicam escolhas; evidências mostram execução. O histórico Git preserva mudanças anteriores. Não anexar toda conversa ou resultado bruto à seed. Conexão ao ChatGPT não garante leitura integral do repositório, execução das ferramentas ou aprendizado automático entre projetos; essas atividades precisam aparecer no trabalho concreto.

**Versão:** incrementar a versão documental quando houver integração relevante ou revisão de direção. Mudança incompatível em registros deve ter migração e consumidores atualizados; aumento de número não comprova maturidade do produto. Se alguma seção passar a orientar ações erradas, reescrevê-la: não acumular correções contraditórias ao fim do arquivo.

**Prompt de expansão por fase:**

> Leia SEED.md, AGENTS.md e docs/STATE.md. Trabalhe uma única fase com base no pedido atual. Consulte registry/legacy_sources.json e extraia somente as fontes necessárias do acervo histórico. Declare o recorte, as origens, o que será preservado e o que será alterado. Produza a implementação ou a análise solicitada, verifique o resultado dentro das ferramentas disponíveis e atualize o estado, decisões e registros afetados. Revise a SEED quando uma descoberta mudar sua direção. Não reproduza regras de crescimento obrigatório, canon antigo ou automações encontradas no legado; não transforme registros de planejamento em resultados realizados.

## v0.4.4 — client syntax attribution

P02 runner 0.1.3 requires complete parser evidence naming the submitted client
before syntax rejection. Real option/preload failures now remain inconclusive;
invalid JavaScript still rejects. Nineteen runner regressions and the unchanged
15/17 baseline, 17/17 reference calibration pass. The full P11 suite passes 22
checks. Remote reading/recalibration and registry work were synchronized first.
No candidate score or new project maturity is inferred.

## v0.4.5 — resume live reading explicitly

P11 0.1.3 adds a bounded unread-arrival count and a keyboard-operable Jump to
latest control while preserving earlier reading position. Returning to the bottom
clears the count; activation transfers focus into the conversation. P02 runner 0.1.4 pins the new app commit and preserves
its candidate contract; controlled calibration is recorded separately. No extra project or maturity gate.

### First destination milestone — v0.4.6

P10 Waystone dialogue 0.1.0 makes one preserved dialogue subset playable.
[The scene](projects/waystone-dialogue/README.md) and
[execution evidence](evidence/waystone-dialogue/RUN.json) define its behavior,
origin and limits. Seed 0.4.6 records the durable working destination/primary
workstream change; project version 0.1.0 and bounded technical M4 are separate.
P02/P11 and historical source bytes remain unchanged. Human creative quality
and broader game/engine claims require their own evidence.


### Complete rescue destination — v0.5.0

[The Last Waystone: Flood Crossing](projects/waystone-dialogue/README.md)
advances P10 from an isolated conversation to a complete prototype operation.
It reuses the original scene and adds equipment, two routes, time-sensitive
rescue, ferry cargo/current and outcome-specific shelter scenes. Choices now
change the delivered people/cargo and tomorrow's transport. Original sources and
standalone behavior remain preserved. [Milestone evidence](evidence/waystone-dialogue/ADVENTURE_RUN.json)
distinguishes executed technical checks, implementing-agent review and pending
reader/commercial validation. No media asset, full RPG migration or model score.


### Original playable rhythm destination — v0.6.0

[Tokyo 80s: Midnight Signal](projects/tokyo80s/README.md) is a new browser stage,
not recovery of the unavailable historical ZIP. A real original P08 instrumental
is rendered, exported, registered and consumed by two instrument-aligned charts.
Audio-clock judgment, aura, calibration, pause/focus, results and replay complete
one player workflow. TR-012 records actual production/consumer integration.
[Evidence](evidence/tokyo80s/RUN.json) distinguishes synthetic full playback,
implementing-agent review and pending human play/listening. P10 and historical
source bytes remain preserved; no commercial product or exclusive rights claim.


### Browser rescue destination — v0.7.0

[P10 Flood Crossing browser](projects/waystone-dialogue/browser/README.md) makes
both rescue routes consumable as a static game with original situational drawing,
connected flood/cargo feedback and durable local play. Decision-journal replay
preserves the unchanged Python rules and dialogue memory; the UI clarifies
forecast risks without supplying solved paths. [Execution](evidence/waystone-dialogue/BROWSER_RUN.json)
records real Python comparisons, Chromium journeys and implementing-agent review.
Human understanding, screen-reader/other-browser behavior and paid demand remain
unverified. Historical sources and P03/P08, P11 and P02 stay preserved.


### Connected relief morning — v0.8.0

P10 campaign 0.4.0 turns the night epilogue's transport, medicine and resident
facts into another playable operation. Six work slots force priorities among
recovery, clinical care, grain, seed and route restoration. New scenes preserve
character presence and night memory; dry, spoiled and abandoned medicine differ.
[Execution](evidence/waystone-dialogue/CAMPAIGN_RUN.json) records actual two-day
journeys, saves and implementing-agent design review. No independent reader,
commercial, harvest, clinical casualty or Python morning execution claim.


### Native combat destination — v0.9.0

P06 now delivers an actual Godot encounter, rather than an unavailable starter
reference. [Execution](evidence/veil-arena/RUN.json) distinguishes source/editor
import, physics gameplay, OpenGL rendering, PCK build/run and unverified standalone
platform/human/commercial outcomes. Procedural geometry is actual runtime visual
work, not a recovered asset catalogue. No historical combat transfer is promoted.
