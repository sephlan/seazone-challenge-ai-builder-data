# Spec — Inteligência Brasil

## Quem usa e que decisão substitui

| Consumidor | Decisão que toma hoje manualmente | Frequência |
|---|---|---|
| **Revenue Management (RM)** | Ajustar diária por imóvel/região baseado em "feeling" + planilha | Diária/semanal |
| **Aquisição** | Decidir em quais cidades/bairros captar novos proprietários | Mensal |
| **Originação** | Escolher onde construir/converter prédios para short stay | Trimestral |

Hoje cada decisão exige um analista rodando queries ad-hoc, montando planilha e apresentando. Isso não escala para 3.000+ imóveis em dezenas de cidades. O produto substitui o processo manual por tabelas gold autoatualizadas + dashboards consumíveis diretamente.

---

## Inputs

### Datalake (automatizado)

- **Scrapers Airbnb** (já existentes): listings, preços, disponibilidade, reviews → ingestão diária no bronze
- **Scrapers VivaReal/ZAP** (já existentes): listings de venda, preço/m², características → ingestão diária
- **Geolocalização (Mesh)**: lat/long + bairro por listing → ingestão incremental
- **Dados operacionais Seazone**: imóveis geridos, receita real, ocupação real, custos → fonte interna (ERP/banco operacional)

### Externos (a integrar)

- **FIPEZAP**: índice de valorização por cidade/bairro → ingestão mensal via API
- **IBGE/SIDRA**: dados demográficos, turismo, PIB municipal → ingestão trimestral
- **Clima/sazonalidade**: calendário de feriados + dados climáticos por região → estático com refresh anual

### Manual (fase 1 apenas)

- Custo de construção regional (CUB por estado) → planilha atualizada trimestralmente pelo time de Originação
- Regulação municipal de short stay → catalogação manual por cidade

---

## Outputs

### Tabelas gold (consumo direto)

| Tabela | Granularidade | Atualização | Consumidor primário |
|---|---|---|---|
| `gold.market_intelligence_suburb` | suburb × mês | Diária | RM, Aquisição |
| `gold.investment_scoring_suburb` | suburb × tipologia | Semanal | Originação |
| `gold.price_benchmark` | suburb × bedrooms × semana | Diária | RM |
| `gold.occupancy_estimation` | listing × mês | Diária | RM |
| `gold.roi_projection` | suburb × tipologia × horizonte | Mensal | Originação |

### Dashboards

- **Mapa de calor Brasil**: receita mediana × ocupação × preço/m² por polígono. Consumido por Aquisição e Originação
- **Painel RM por cidade**: benchmark de diária vs. mercado, ocupação estimada vs. portfólio Seazone
- **Scorecard de investimento**: ranking de suburbs por ROI projetado, atualizado mensalmente

### API/MCP (fase 2+)

- Endpoint para consulta programática de benchmark por suburb/tipologia
- MCP tool para Claude Code do squad consultar dados sem sair do fluxo

---

## Granularidade espacial e temporal

### Espacial

**Escolha: suburb (bairro) como unidade primária, com H3 resolução 8 como camada de detalhamento.**

Justificativa:
- Suburb é o nível que o negócio pensa ("Meia Praia", "Centro") e que os dados de scraping já trazem
- H3 res 8 (~460m de diâmetro) permite análise intra-bairro sem complexidade desnecessária
- Municipal é grosseiro demais (Itapema inteira perde a diferença entre Meia Praia e Casa Branca)
- CEP não tem semântica geográfica consistente entre cidades

Implementação: cada listing recebe o H3 index a partir de lat/long. Agregações são feitas no nível suburb (default) com drill-down para H3 quando o consumidor precisa de detalhamento.

### Temporal

- **Bronze**: timestamp de ingestão (aquisition_date), preserva todos os snapshots
- **Silver**: normalizado para data de referência (data de estadia para preços, data de snapshot para listings)
- **Gold**: agregado por semana (RM) ou mês (Aquisição/Originação), com campo `as_of_date` indicando quando o dado foi calculado

---

## Modelo de dados

```
BRONZE (append-only, Parquet particionado por aquisition_date)
├── bronze.airbnb_listings       ← Details scraper
├── bronze.airbnb_prices         ← Price scraper (dupla data preservada)
├── bronze.airbnb_hosts          ← Hosts scraper
├── bronze.geolocation           ← Mesh
├── bronze.vivareal_listings     ← VivaReal scraper
└── bronze.seazone_operations    ← dados internos

SILVER (dedup, tipado, joins resolvidos)
├── silver.listings_enriched     ← listing + host + geo, dedup por snapshot mais recente
├── silver.prices_resolved       ← preço resolvido (último snapshot por listing×date)
├── silver.prices_yield_delta    ← delta entre snapshots (yield management signal)
├── silver.vivareal_normalized   ← preço/m², tipologia normalizada
└── silver.occupancy_estimated   ← ocupação inferida por listing×mês

GOLD (agregado, consumível)
├── gold.market_intelligence_suburb
├── gold.investment_scoring_suburb
├── gold.price_benchmark
├── gold.occupancy_estimation
└── gold.roi_projection
```

---

## SLA/SLO

| Métrica | Mínimo viável (fase 1) | Ideal (fase 3+) |
|---|---|---|
| Freshness das tabelas gold | D+1 (dados de ontem disponíveis hoje às 9h) | D+0 (near real-time, <4h de lag) |
| Cobertura de cidades | Top 10 cidades Seazone | Todas as cidades com ≥50 listings |
| Uptime do pipeline | 95% (toleramos falha de 1 dia/mês com reprocessamento) | 99.5% |
| Custo Athena/BQ por mês | < R$ 5.000 | < R$ 15.000 (com 10x mais dados) |
| Tempo de resposta dashboard | < 10s para qualquer filtro | < 3s |
| Acurácia de ocupação estimada | ±15% vs. dados reais Seazone | ±8% (calibrado com dados internos) |

---

## O que NÃO está em escopo

- **Precificação automática**: o produto informa benchmark, não define preço. Isso é domínio do RM com algoritmo próprio
- **CRM/captação de proprietários**: os dados alimentam a decisão, mas o outreach é processo de Aquisição
- **Previsão de demanda (forecasting)**: fase futura; o MVP é descritivo/diagnóstico, não preditivo
- **Dados de concorrentes além de Airbnb e VivaReal**: Booking, TripAdvisor etc. ficam para expansão futura
- **App mobile**: dashboards são web-first, consumidos em desktop
- **Multi-idioma**: produto interno, tudo em português
