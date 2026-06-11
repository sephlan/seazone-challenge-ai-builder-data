# Desafio AI Builder — Seazone (Senior AI Builder, squad Data Edge)

## Candidato

**Flander** — Senior AI Engineer

---

## Como rodar

### Pré-requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- Git

### Parte 1 — Análise Itapema

```bash
cd analysis
uv sync
uv run python -m src.main
```

O output é gerado em `analysis/output/`:

| Arquivo | Conteúdo |
|---|---|
| `data_quality.md` | Relatório de qualidade dos 5 CSVs |
| `p1_perfil_imovel.csv` | Ranking de perfil por bedrooms × listing_type |
| `p2_localizacao.csv` | Ranking de suburbs por receita mediana |
| `p3_drivers_receita.csv` | Comparação top 20% vs. restante |
| `p4p5_roi_predio.csv` | ROI projetado 2025-2027 |
| `p4p5_premissas.csv` | Premissas explícitas do modelo de ROI |

Tempo de execução total: ~0.2s (medido no script).

### Parte 2 — Spec Inteligência Brasil

Sem código. Documentação em `specs/02-inteligencia-brasil/`:

- `constitution.md` — princípios não-negociáveis
- `spec.md` — produto completo (consumidores, inputs/outputs, modelo de dados, SLAs)
- `plan.md` — fases de entrega com squads, dependências e riscos

### Parte 3 — Code Review do PR sintético

- **Comentários inline no PR:** [PR #1](https://github.com/sephlan/seazone-challenge-ai-builder-data/pull/1)
- **Sumário do review:** `reviews/01-system-price-v2.md`

### Parte 4 — Plano de Squad

Documento em `plano-squad/30-60-90.md`.

---

## Estrutura do repositório

```
.
├── README.md
├── data/                          # CSVs do desafio (Itapema)
│   ├── Details_Itapema.csv
│   ├── Hosts_ids_Itapema.csv
│   ├── Mesh_Ids_Data_Itapema.csv
│   ├── Price_AV_Itapema.csv
│   └── VivaReal_Itapema.csv
├── specs/
│   ├── 01-bi-itapema/
│   │   ├── spec.md                # Hipóteses, métricas, modelagem
│   │   └── plan.md                # Plano de execução
│   └── 02-inteligencia-brasil/
│       ├── constitution.md        # Princípios não-negociáveis
│       ├── spec.md                # Produto Inteligência Brasil
│       └── plan.md                # Fases de entrega
├── analysis/                      # Código Parte 1
│   ├── pyproject.toml             # uv-managed
│   └── src/
│       ├── main.py                # Orquestrador com medição de tempo
│       ├── ingest.py              # Ingestão + qualidade
│       ├── features.py            # Joins + receita estimada
│       └── analysis.py            # Análises P1-P5 + ROI
├── reviews/
│   └── 01-system-price-v2.md      # Sumário do code review
├── plano-squad/
│   └── 30-60-90.md                # Plano 30/60/90 + underperformance
├── ai-sessions/
│   ├── 01-discovery.md            # Sessão: exploração dos dados
│   ├── 02-modelagem.md            # Sessão: decisões de spec
│   └── 03-roi.md                  # Sessão: pipeline + ROI
└── report/
    └── relatorio.pdf              # Relatório consolidado
```

---

## Stack

| Tecnologia | Uso |
|---|---|
| Python 3.11+ | Linguagem principal |
| uv + pyproject.toml | Gerenciamento de dependências |
| Polars | Wrangling de dados (substituindo pandas) |
| DuckDB | Queries SQL locais |
| matplotlib / plotly | Visualizações |

---

## Decisões técnicas relevantes

- **Polars ao invés de pandas:** mais rápido para o volume de dados (~118k linhas de preço), API mais expressiva para group_by e window functions.
- **Tratamento da dupla data em Price_AV:** usamos o snapshot mais recente (2025-01-20) como preço resolvido e calculamos delta entre snapshots como sinal de yield management. Detalhes em `specs/01-bi-itapema/spec.md`.
- **Ocupação estimada como proxy:** sem dados reais de reserva, usamos noites sem preço como proxy de noites ocupadas/bloqueadas. Limitação documentada.
- **Sazonalidade explícita:** dados cobrem apenas alta temporada (jan-abr). ROI anualizado usa fator conservador para baixa temporada (ocupação a 40%, diária a 70% da alta).

---

## IA no fluxo

Ferramenta principal: **Claude** (claude.ai)

Transcripts completos em `ai-sessions/`. Resumo do uso:

- **Discovery:** exploração de schema e qualidade dos 5 CSVs
- **Modelagem:** definição operacional dos termos vagos do desafio, tratamento da dupla data
- **Pipeline:** geração do código modular, debugging de join explosion e paths

Detalhes no AI Co-author Log do relatório PDF.
