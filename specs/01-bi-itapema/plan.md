# Plan — Análise Itapema (Parte 1)

## Passos de execução

### Fase 0 — Setup do projeto
- Inicializar `uv` + `pyproject.toml` com dependências: polars, duckdb, matplotlib/plotly
- Estrutura `analysis/src/` com módulos separados por responsabilidade
- Configurar DuckDB para leitura direta dos CSVs em `data/`
- **Entregável:** `uv run python analysis/src/main.py` roda tudo de ponta a ponta
- **Dependência:** nenhuma

### Fase 1 — Ingestão e qualidade dos dados
- Carregar os 5 CSVs com Polars, tipar colunas (datas, floats, categorias)
- Auditoria de qualidade: nulos, duplicatas, outliers, cardinalidade
- Mesh: deduplicar por listing (manter snapshot mais recente)
- Price_AV: validar a estrutura de 3 aquisições × N datas de estadia
- Contagem de listings com preço vs. sem preço (cobertura)
- **Entregável:** relatório de qualidade em `analysis/output/data_quality.md`
- **Dependência:** Fase 0

### Fase 2 — Feature engineering
- **Join master:** Details + Hosts + Mesh (mais recente) → tabela `listings_enriched`
- **Receita estimada por listing:**
  1. Partir do Price_AV snapshot 2025-01-20 (mais resolvido)
  2. Para cada listing: somar preços das noites disponíveis no período
  3. Estimar ocupação: noites sem preço no range / total de noites
  4. Receita bruta = soma_preços × (1 − taxa_vacância)
- **Delta de preço entre snapshots:** aquisição 06→07 e 07→20 por listing×data_estadia
- **Normalização por m²:** cruzar bedrooms com m² mediano do VivaReal para mesma tipologia
- **Entregável:** tabela `listings_revenue` com todas as features
- **Dependência:** Fase 1

### Fase 3 — Análise por pergunta

#### P1: Melhor perfil de imóvel
- Group by (bedrooms, listing_type): mediana receita, RevPAN, ocupação
- Normalizar por m² estimado
- Ranking + visualização
- **Dependência:** Fase 2

#### P2: Melhor localização
- Group by suburb: mediana receita, volume de listings, ocupação
- Filtro: suburbs com ≥ 20 listings
- Mapa de calor se possível (lat/long do Mesh)
- **Dependência:** Fase 2

#### P3: Características das melhores receitas
- Top 20% receita vs. restante: comparar star_rating, superhost, reviews, amenidades
- Feature importance (correlação ou modelo simples)
- **Dependência:** Fase 2

#### P4-P5: Prédio de 50 aptos + ROI
- Definir suburb e tipologia (output de P1+P2)
- Custo de aquisição: m² VivaReal × área projetada × 50 unidades + terreno
- Receita projetada: diária mediana × ocupação × 365 × 50
- Sazonalidade: alta (jan-mar) dados observados, baixa (abr-dez) estimativa conservadora
- ROI = (receita líquida anual − custos operacionais) / investimento total
- Projetar 2025, 2026, 2027 com premissas de valorização e inflação
- Análise de sensibilidade: ocupação ±10%, diária ±15%
- **Dependência:** Fase 3

### Fase 4 — Output e documentação
- Gerar visualizações finais (gráficos em PNG/SVG ou dashboard)
- Compilar respostas em markdown estruturado
- Medir tempo de execução por etapa (exigido no desafio)
- **Dependência:** Fase 3

---

## Dependências entre fases

```
Fase 0 (setup)
  └── Fase 1 (ingestão + qualidade)
        └── Fase 2 (features + receita)
              ├── Fase 3 — P1 (perfil)
              ├── Fase 3 — P2 (localização)
              ├── Fase 3 — P3 (características)
              └── Fase 3 — P4/P5 (ROI) ← depende de P1+P2
                    └── Fase 4 (output)
```

---

## Riscos e mitigação

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Dados de preço cobrem só alta temporada (jan-abr) | ROI superestimado se extrapolar direto | Aplicar fator sazonal conservador (literatura + dados Airbnb públicos de SC) |
| Muitos listings sem preço no Price_AV (cobertura parcial) | Amostra enviesada para ativos mais populares | Quantificar cobertura; reportar viés explicitamente |
| m² não existe em Details (Airbnb não publica) | Não dá pra normalizar receita/m² direto | Estimar via VivaReal: mediana m² por (suburb, bedrooms) |
| Outliers de preço (listings de luxo ou erro de scraping) | Distorcem médias | Usar mediana; aplicar winsorization em P95 |
| Join Mesh × Details pode ter listings sem geolocalização | Perda de dados para análise espacial | Quantificar; analisar com e sem esses listings |

---

## Estimativa de tempo

| Fase | Estimativa |
|------|-----------|
| Fase 0 — Setup | 30 min |
| Fase 1 — Ingestão e qualidade | 1-2h |
| Fase 2 — Feature engineering | 2-3h |
| Fase 3 — Análises (P1-P5) | 3-4h |
| Fase 4 — Output e documentação | 1-2h |
| **Total** | **~8-12h** |
