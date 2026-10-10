# Fontes e alcance do levantamento

**Data:** 2026-10-10.

| Fonte | Acesso usado | Limite |
|---|---|---|
| Pedido atual de Martin | Texto direto | Autoriza transformação dos projetos, sem alterar fatos profissionais |
| Conversa de carreira fornecida | Texto recebido | Recomendações e benchmarks antigos de mercado não revalidados |
| ResumeMartinFMelcopNeto.pdf | Quatro páginas lidas em texto | Informações declaradas no currículo; sem verificação externa |
| Lightnovel Darkfantasy v0.4.48.zip | ZIP aberto; seed, README, manifesto, estado e canon lidos | Manuscrito e demais documentos não auditados nesta fundação |
| Artemyra/ArtemiZ4 | Contexto histórico recuperado | Fontes completas e Game.exe não executados |
| The Dark Knight | Contexto histórico disponível | Pacotes Sprint 100 não auditados |
| Véu Partido | Contexto histórico disponível | Starter v0.0.47 não executado |
| Tokyo 80s | Contexto histórico disponível | Pacote v0.0.1 não executado |
| AI Evaluation anterior | Histórico recuperado | PDFs completos não inspecionados; cases eram simulados |
| Imagens/sons/poemas | Intenção atual e histórico visual | Catálogo de áudio e poesia ainda pendente |

A v0.1.0 não redistribuiu os arquivos-fonte acima. A v0.2.0 incorpora uma seleção textual dos dois repositórios fornecidos depois, conforme o registro abaixo. A imagem anexada à conversa foi inspecionada; contém somente a inscrição “Pensou por 2m 28s” e não acrescenta dados dos projetos.

Fontes técnicas externas e links estão no fim de [SEED.md](../SEED.md). A existência de uma versão encontrada não prova que seja a última. Registrar fonte e hash quando houver importação efetiva.

## Recuperação v0.2.0

Rave Master: commit 36af1651271422ae33856e8b5d7b45702215f165; 729 arquivos inventariados, 177 textos lidos e 175 preservados. WebSocket: commit df651a9ddef39c7b05a48f25f1b7fdaff6760185; os três arquivos lidos e preservados. Snapshots consultados pelo acesso autenticado ao GitHub, em 2026-10-10.

Ver [síntese e limites](LEGACY_REPOSITORIES.md), [inventário](../registry/legacy_sources.json) e [execuções atuais](../evidence/legacy-audit/RUNS.json). Conteúdos textuais preservados conferidos contra hashes Git. O acesso a repositório privado não equivale a autorização de publicação geral. Os relatórios dentro do acervo são históricos; os relatórios em evidence/legacy-audit foram produzidos nesta recuperação.

## P11 working adaptation — 2026-10-10

The current session read the three `LEGACY-002` source files from the unchanged
archive, verified its archive/file hashes, and extracted only those files to
a temporary directory. A browser check executed the baseline with Express
4.22.3 and Socket.IO 4.8.4, both within its declared semver ranges. The working
adaptation lives outside the archive; see its
[origin and differences](../projects/realtime-integration-lab/README.md) and
[execution record](../evidence/realtime-chat/RUN.json). No additional remote
legacy repository was downloaded or retired in this session.
