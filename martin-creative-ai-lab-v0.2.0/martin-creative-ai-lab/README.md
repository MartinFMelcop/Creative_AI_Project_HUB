# Martin Creative AI Lab

Laboratório autoral de jogos, narrativas, imagens, áudio, dados e avaliação de IA de **Martin Melcop Neto**.

A proposta é transformar projetos existentes em seeds evolutivas: construir fatias pequenas, validar o comportamento, registrar decisões e reaproveitar conhecimento entre contextos. O histórico profissional em Agile Delivery e Business Analysis orienta requisitos, produção e qualidade; as competências técnicas e criativas serão demonstradas por trabalhos concretos.

**Estado atual: seed v0.2.0 com recuperação seletiva de legado.** Inclui 178 fontes textuais preservadas, inventário dos snapshots e dois runners Python reexecutados. Não contém jogo migrado, benchmark de modelos ou músicas finalizadas.

## Comece aqui

- [SEED.md](SEED.md): base completa, perfil, inventário, direção, fases, métodos e prompts.
- [Estado atual](docs/STATE.md): frente recomendada, lacunas e próxima ação.
- [Roadmap](docs/ROADMAP.md): fases definidas por entregas e gates.
- [Instruções para agentes](AGENTS.md): operação e continuidade.
- [Registro de projetos](registry/projects.json): IDs e estado inicial.
- [Registro de fontes](docs/SOURCES.md): o que foi lido e o que permanece legado.
- [Evolução da seed](docs/SEED_EVOLUTION.md): continuidade, revisão e expansão com IA.
- [Fontes recuperadas](docs/LEGACY_REPOSITORIES.md): Rave Master e WebSocket, evidências e recortes.
- [Inventário de legado](registry/legacy_sources.json): snapshots e conteúdos preservados.

## Fontes criativas e técnicas

| Seed | Explorações possíveis |
|---|---|
| Artemyra / ArtemiZ4 | Produção, economia, board, minigames e agentes de jogo |
| Unity AI Evaluation & QA Lab | Bugs verificáveis, tasks, testes e avaliação |
| Tokyo 80s | Ritmo, aura, timing e áudio interativo |
| O Lich mais velho da tumba mais antiga | Narrativa, continuidade, adaptação e direção visual |
| The Dark Knight / Véu Partido | Combate, progressão, status, bosses e extração de sistemas |
| Visual / Audio / Poetry Labs | Assets, música, poemas e integração entre mídias |
| AI Delivery & Operations Cases | Processo, requisitos, avaliação e evidência |
| Rave Master | Diálogo, personalidade, combate, mundo, crafting e QA |
| WebSocket / Real-time Lab | Eventos cliente/servidor, debugging e integrações |

Os projetos podem mudar de nome, mídia, linguagem, engine e escopo. A origem permanece documentada; a próxima versão não precisa reproduzir integralmente o legado.

## AI-assisted workflow

AI may assist with planning, implementation, creative variants and review. Every case must state the actual contribution of the tools and Martin, the checks performed and the remaining limitations. Simulated work is identified as simulated; implementation is distinguished from runtime validation.

## Verificação documental

Com Python 3.9 ou superior disponível, na raiz:

```bash
python3 tools/validate_repo.py
```

O comando verifica registros JSON, referências, links locais e integridade do acervo textual preservado. Não executa jogos nem valida a qualidade das obras.

## Primeiro trabalho recomendado

Selecionar uma única fatia usando fontes recuperadas: chat bidirecional, diálogo com estado ou domínio de combate. Se Artemyra continuar prioritário, recuperar seu baseline. Verificar ambiente e definir aceitação antes do desenvolvimento.

Os cases públicos entrarão em [showcase](showcase/README.md) quando houver artefatos e evidências. Licenciamento de distribuição de código e conteúdo será decidido conforme o material efetivamente publicado.
