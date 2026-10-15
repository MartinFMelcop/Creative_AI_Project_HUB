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

The 0.1.0 session read the three `LEGACY-002` source files from the unchanged
archive, verified its archive/file hashes, and extracted only those files to
a temporary directory. A browser check executed the baseline with Express
4.22.3 and Socket.IO 4.8.4, both within its declared semver ranges. The working
adaptation lives outside the archive; see its
[origin and differences](../projects/realtime-integration-lab/README.md) and
[execution record](../evidence/realtime-chat/RUN.json). No additional remote
legacy repository was downloaded or retired in this session.

## P11 send-path correction — 0.1.1

This session starts from committed working revision `66041e7`. No historical
files were extracted. Existing source provenance is retained; the new
[execution record](../evidence/realtime-chat/POLLING_SEND_RUN.json) identifies
both the committed baseline client and tested correction. The pinned installed
Socket.IO 4.8.4 source and exported `sendBuffer` declaration were inspected to
distinguish live Engine.IO writes from reconnect buffering. Dependency versions,
checksums, and trust configuration remain unchanged.

## One-time integration — 2026-10-15 UTC

Current source inspection and the new [reference catalog](../references/catalog.json)
are distinct from the original 2026-10-10 survey. Rave current public main/history
still selects `36af1651271422ae33856e8b5d7b45702215f165`: 729 paths observed,
589 original readable text/code/data files imported, 140 individually excluded.
All 175 earlier selected bytes match; the original ZIP and preservation counters
are unchanged. Current visibility does not rewrite the prior private observation.
See [source discovery/rights limits](../references/rave-master/README.md).

Supplied attachment filename `Lightnovel%20Darkfantasy%20v0.4.1.zip` (display name
Lightnovel Darkfantasy v0.4.1.zip) was refused by `download_file`: above its 32 MiB
transfer limit. No attachment bytes were available; detected version, SHA-256,
file count, manuscript/OVA paths and authority are unknown, not imported. Earlier
v0.4.48 records remain historical and are not superseded by a filename hint.
[Literary recovery](../references/literature/lich/README.md) gives the exact boundary;
P04's separate adaptation/source/editions remain intact. No full original ZIP
host or fictitious download link was created. No historical script was executed.

## Individual main literary PDFs — 2026-10-15 UTC

Martin supplied ten separate PDF attachments after the ZIP transfer failure.
[Library and per-book links](../references/literature/lich/README.md) preserve
all ten original PDFs, 1,646 physical pages and embedded covers, with per-file
hashes and ten Poppler text derivatives. These are actual readable sources,
distinct from the unavailable ZIP and the older v0.4.48 inspection report.
Title pages say v0.2.87; Producer/Subject fields say v0.2.88/noncanonical drafts.
No package-version reconciliation, ZIP-membership proof or canon approval.
`_project/AUTHORITY_POLICY.md`, editable manuscripts and OVAs were not supplied.
[Evidence](../evidence/reference-integration/LICH_MAIN_PDFS.json) distinguishes
full extraction/byte preservation from limited opening/ending/visual inspection,
which is not a complete literary audit or independent rights validation.
