# Plan — Inteligência Brasil

## Fase 1 — MVP vertical (semanas 1-6)

**Objetivo:** Itapema + top 5 cidades Seazone funcionando end-to-end com dados reais.

### Entregas
- Pipeline bronze→silver→gold para Airbnb (listings + prices + hosts + geo) em Athena
- Pipeline bronze→silver para VivaReal em Athena
- Tabelas gold: `market_intelligence_suburb`, `price_benchmark`, `occupancy_estimation`
- Dashboard Lovable com mapa de calor e painel RM para as 5 cidades
- Testes de schema + alertas de freshness para todas as tabelas gold

### Squads
- **Data Edge** (owner): pipelines de scraping → bronze, silver de preços e ocupação, tabelas gold
- **Data Core**: infraestrutura Athena/S3, particionamento, orquestração (Airflow/Step Functions)
- **Data Acquisition**: não entra nesta fase

### Dependências
- Scrapers de Airbnb e VivaReal já rodando em produção (confirmar com Core)
- Acesso ao banco operacional Seazone para dados reais de ocupação (calibração)
- Bucket S3 + catálogo Glue configurados para o novo datalake

### Marcos de validação
1. **Semana 2**: bronze populada com dados de 5 cidades, RM valida que "reconhece" os números
2. **Semana 4**: tabelas gold consumíveis, RM faz primeiro teste de decisão real usando o dashboard
3. **Semana 6**: pipeline rodando diariamente sem intervenção manual por 7 dias consecutivos

### Riscos
| Risco | Mitigação |
|---|---|
| Scrapers instáveis mudam schema sem aviso | Teste de schema na ingestão; alerta imediato; bronze aceita schema evolution |
| Dados de ocupação real da Seazone difíceis de extrair | Fase 1 usa estimativa por scraping; calibração com dados reais é melhoria incremental |
| Athena lento para queries interativas no dashboard | Pré-agregar em gold; materializar views; se não resolver, avaliar BigQuery para camada de serving |

---

## Fase 2 — Escala horizontal (semanas 7-14)

**Objetivo:** Expandir para todas as cidades com ≥50 listings; adicionar scoring de investimento.

### Entregas
- Pipeline generalizado para N cidades (parametrizado, não duplicado por cidade)
- Tabelas gold: `investment_scoring_suburb`, `roi_projection`
- Integração FIPEZAP para valorização imobiliária
- Dashboard de Originação com scorecard de investimento
- API/MCP endpoint para consulta programática

### Squads
- **Data Edge** (owner): scoring de investimento, ROI, integração FIPEZAP
- **Data Core**: escalar orquestração para N cidades, otimização de custo Athena
- **Data Acquisition**: começa a consumir os dados; feedback sobre formato e granularidade

### Dependências
- Fase 1 estável por ≥2 semanas
- API FIPEZAP acessível (verificar licenciamento)
- Originação define critérios de scoring (reunião de kickoff na semana 7)

### Marcos de validação
1. **Semana 9**: pipeline rodando para 20+ cidades sem degradação de performance
2. **Semana 11**: Originação usa scorecard para decisão real de prospecção de prédio
3. **Semana 14**: custo mensal Athena dentro do budget (< R$ 5.000)

### Riscos
| Risco | Mitigação |
|---|---|
| Custo Athena escala linear com cidades | Particionamento agressivo; compactação de Parquet; avaliar migração de serving pra BigQuery |
| FIPEZAP não cobre cidades menores | Fallback: estimativa por regressão com variáveis proxy (IBGE, preço VivaReal) |
| Scoring de ROI muito sensível a premissas | Análise de sensibilidade obrigatória; mostrar range (otimista/base/pessimista), não número único |

---

## Fase 3 — Maturidade e automação (semanas 15-24)

**Objetivo:** Produto self-service; reduzir intervenção humana; near real-time.

### Entregas
- Freshness D+0 (pipeline triggered por chegada de dado, não por schedule)
- Calibração automática de ocupação estimada vs. dados reais Seazone (feedback loop)
- Alertas inteligentes: "bairro X teve queda de 20% em ocupação vs. mês anterior"
- Dados IBGE/demográficos integrados
- Documentação completa para onboarding de novos consumidores

### Squads
- **Data Edge**: feedback loop de calibração, alertas
- **Data Core**: event-driven pipelines, otimização de custo
- **Data Acquisition**: onboarding autônomo; criam seus próprios filtros e views

### Dependências
- Fases 1 e 2 estáveis
- Acesso consistente aos dados operacionais Seazone (ETL do ERP)
- Budget aprovado para escalar infra

### Marcos de validação
1. **Semana 18**: pipeline event-driven funcionando para top 5 cidades
2. **Semana 21**: erro de ocupação estimada < 10% vs. dados reais (medido em backtest)
3. **Semana 24**: Aquisição e Originação tomam decisão sem pedir query ad-hoc ao squad de dados

### Riscos
| Risco | Mitigação |
|---|---|
| Event-driven pipeline complexo demais pra manter | Fallback: manter schedule diário; event-driven só para tabelas críticas de RM |
| Calibração com dados reais revela que estimativa de ocupação é ruim | Isso é aprendizado, não falha. Ajustar modelo; comunicar incerteza |
| Squad sobrecarregado com suporte a consumidores | Self-service docs + office hours semanal; não virar service desk |
