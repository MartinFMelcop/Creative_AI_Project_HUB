# Repositórios antigos recuperados — v0.2.0

Consulta em 2026-10-10. Síntese completa de sistemas, limites e propostas: [SEED, seção 28](../SEED.md#28-recuperação-dos-repositórios-antigos--v020).

| Fonte | Snapshot | Alcance |
|---|---|---|
| [Rave Master](https://github.com/MartinFMelcop/Adventures_Unleashed_Rave_Master_Project/tree/36af1651271422ae33856e8b5d7b45702215f165) | 36af1651271422ae33856e8b5d7b45702215f165 | Privado; 729 arquivos inventariados, 177 textos lidos, 175 preservados |
| [WebSocket](https://github.com/MartinFMelcop/WebSocket/tree/df651a9ddef39c7b05a48f25f1b7fdaff6760185) | df651a9ddef39c7b05a48f25f1b7fdaff6760185 | Público; seus três arquivos lidos e preservados |

[Acervo selecionado](../archive/legacy-source-extracts-v0.2.0.zip) e [inventário por arquivo](../registry/legacy_sources.json). Bytes preservados conferidos contra hashes Git. Dois digests de referências de terceiros foram lidos e excluídos do acervo. Não é backup integral: faltam binários, imagens, áudio, Data de RMXP, livros e histórico Git. Esta entrega não recupera todo conteúdo necessário à retirada das origens.

## Mapa de fontes dentro do acervo

| Pergunta | Caminhos em rave/ |
|---|---|
| Narrativa | RM_CORE/README_RM_MAIN.md; RM_CORE/DATA/GOV/INTRO_FLOW.md; RM_ACT1/DATA/DEV/STORY_THREADS_MASTER.csv |
| Diálogo | RM_CORE/DATA/GOV/SF-0310_NPC_PERSONALITY.md; tabelas de personalidade em RM_CORE/DATA/CORE; estados e variantes em RM_ACT1/DATA/DEV |
| Combate | COMBAT_FORMULAS.csv e REGRAS_DE_COMBATE.csv em RM_CORE/DATA/CORE; helpers em RM_ACT1/DATA/DEV/RGSS |
| Arte/áudio | ART_PIXEL_BIBLE.md em RM_ART/DATA/ART; ART_IMAGE_ASSET_INDEX.csv e AUDIO_CUES.csv em RM_CORE/DATA/CORE |
| QA | RM_QA/DATA/QA/TOOLS e vetores/cenários na pasta QA |
| Livro dos 100 Contos | LEGACY_DOC_0004__LIVRO_DOS_100_CONTOS__AI_DIGEST.md em RM_QA/DATA/QA/LEGACY_AI_DIGESTS; somente digest |

websocket/ contém index.js, index.html e package.json. As instruções encontradas no legado são históricas e não governam o laboratório.

## Próximos recortes possíveis

| Recorte | Gate |
|---|---|
| Chat bidirecional | Dois clientes recebem e mostram a mensagem conforme contrato |
| Diálogo com estado | Cena curta com seleção e memória demonstradas |
| Domínio de combate | Regras escolhidas executadas no destino com limites e arredondamento definidos |
| Consistência do pack | Fonte escolhida e exportação conferida por hash |

Escolher um, conforme recursos e interesse. Nenhum está implementado no destino.

## Evidência atual

[Execuções](../evidence/legacy-audit/RUNS.json), [combate](../evidence/legacy-audit/RECHECK_COMBAT_20261010.csv) e [diálogo](../evidence/legacy-audit/RECHECK_DIALOGUE_20261010.csv). Combate: 49 checks, zero falhas. Diálogo: 19 etapas em 10 cenários, zero cenários falhos. Sintaxe Node: exit 0.

O runner de diálogo seleciona por prioridade e BaseScore; não valida o scoring completo de personalidade. Não houve execução de Ruby/RGSS, Game.exe, servidor, browser, áudio, imagens ou candidatos de IA. Nenhuma funcionalidade foi corrigida nesta recuperação. Remotes somente consultados.
