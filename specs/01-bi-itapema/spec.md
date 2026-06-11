# Spec — Análise Itapema (Parte 1)

## Objetivo

Responder se Itapema é um bom investimento para short stay e definir o perfil ótimo de imóvel, localização e projeção de ROI para um prédio de 50 apartamentos.

---

## Definições operacionais

Os termos do desafio são deliberadamente vagos. Aqui estão as definições que adoto e justifico.

### "Melhor perfil de imóvel"

**Definição:** combinação de `number_of_bedrooms`, `listing_type`, `number_of_guests` e amenidades-chave que maximiza a **receita líquida anual por m²**, controlando por taxa de ocupação.

**Justificativa:** receita bruta sozinha engana — um imóvel de 4 quartos fatura mais que um de 2, mas custa mais pra construir e manter. Normalizar por m² (estimado via VivaReal) equaliza a comparação.

### "Melhor localização em termos de receita"

**Definição:** `suburb` (de Mesh_Ids_Data) com maior **receita mediana por listing ativo**, filtrado por volume mínimo de listings (≥ 20) para significância estatística.

**Justificativa:** usar mediana em vez de média evita distorção por outliers de luxo. Filtro de volume mínimo evita que um bairro com 3 listings puxe o ranking.

### "Características e razões das melhores receitas"

**Definição:** análise de correlação e segmentação entre receita e variáveis como: `star_rating`, `is_superhost`, `number_of_reviews`, `is_guest_favorite`, `can_instant_book`, amenidades específicas (piscina, churrasqueira, ar-condicionado, vista mar), proximidade da praia (lat/long).

### "ROI projetado"

**Definição:** (Receita líquida anual − Custos operacionais) / Custo de aquisição do imóvel.

- **Receita líquida** = receita bruta × taxa de ocupação estimada − taxa de limpeza − comissão plataforma (~15%)
- **Custo de aquisição** = preço mediano m² VivaReal no suburb escolhido × m² projetado por unidade
- **Custos operacionais** = condomínio + IPTU + manutenção + gestão (~20-25% da receita bruta, benchmark Seazone)

---

## Tratamento crítico: Price_AV_Itapema.csv (dupla data)

Este arquivo tem **3 snapshots de aquisição** (2025-01-06, 2025-01-07, 2025-01-20) capturando preços para o **mesmo período de estadia** (2025-01-06 a 2025-04-20, alta temporada SC).

**Abordagem:**

1. **Não tratar como "preço atual"** — isso reprova.
2. Para cada par (listing, date_estadia), haverá até 3 preços (um por aquisição). Isso modela **yield management**: o anfitrião ajusta preço conforme a data de consulta se aproxima.
3. **Estratégia de agregação:**
   - Usar o **último snapshot disponível** (2025-01-20) como preço mais "resolvido" para estimar receita potencial (reflete decisão final do host).
   - Calcular **delta de preço entre snapshots** (06→07, 07→20) para entender a dinâmica de precificação — listings que sobem preço perto da data podem ter demanda alta.
   - Identificar listings que **desaparecem entre snapshots** (vendidos/ocupados) como proxy de ocupação real.
4. **Taxa de ocupação estimada:** proporção de datas de estadia com preço > 0 no último snapshot vs. total de datas no range. Datas sem registro = ocupadas ou bloqueadas.

---

## Hipóteses a validar

| # | Hipótese | Como testar | Dados |
|---|----------|-------------|-------|
| H1 | Aptos de 2-3 quartos têm melhor receita/m² que 1 ou 4+ | Receita mediana por bedroom × m² estimado | Price_AV + Details + VivaReal |
| H2 | Meia Praia lidera receita por localização | Receita mediana por suburb | Price_AV + Mesh |
| H3 | Superhosts têm receita significativamente maior | Teste de medianas superhost vs. não | Price_AV + Details + Hosts |
| H4 | Preço sobe conforme data de estadia se aproxima (yield) | Delta preço entre snapshots por listing | Price_AV |
| H5 | Guest favorites e instant book correlacionam com ocupação | Ocupação estimada vs. flags | Price_AV + Details |
| H6 | Proximidade da praia (longitude mais a leste) eleva receita | Correlação receita × longitude por suburb | Price_AV + Mesh |

---

## Métricas-chave a produzir

1. **Receita bruta estimada por listing** (soma de preços × ocupação estimada, período jan-abr 2025)
2. **Receita bruta anualizada** (extrapolação com sazonalidade: alta jan-mar, baixa abr-nov)
3. **RevPAN** (Revenue per Available Night) — receita / noites disponíveis
4. **Ocupação estimada** por listing e por suburb
5. **Preço mediano por noite** por suburb × bedrooms
6. **Custo de aquisição estimado** (m² via VivaReal por suburb)
7. **ROI projetado** 2025, 2026, 2027 com premissas explícitas de valorização e inflação

---

## Modelagem do ROI (prédio de 50 aptos)

### Inputs

- **Suburb escolhido:** definido pela análise (provável Meia Praia ou Centro)
- **Tipologia:** definida pela análise de perfil ótimo
- **m² por unidade:** estimado via mediana VivaReal para a tipologia
- **Custo construção:** benchmark regional SC (~R$ 4.500-6.000/m², CUB-SC + margem)
- **Terreno:** estimado via preço/m² VivaReal para terrenos ou inferido

### Premissas a explicitar

- Taxa de ocupação: baseada nos dados (alta temporada) + ajuste sazonal (baixa ~40-50%)
- Diária média: por tipologia e suburb, dos dados
- Valorização imobiliária: FIPEZAP litoral SC (~5-8% a.a. nominal)
- Inflação: IPCA projetado (~4.5%)
- Taxa de desconto: CDI + spread (~12-14% a.a.)

### Riscos da projeção

- Dados cobrem apenas alta temporada (jan-abr) — sazonalidade estimada, não observada
- Mercado de Itapema pode estar saturando (verificar crescimento de listings)
- Custo de construção volátil (materiais, mão de obra)
- Regulação de short stay pode mudar

---

## Dados e joins

```
Details (airbnb_listing_id, owner_id)
  ├── JOIN Hosts (owner_id)
  ├── JOIN Mesh (airbnb_listing_id) → suburb, lat/long confiável
  └── JOIN Price_AV (airbnb_listing_id) → preço × data_estadia × data_aquisição

VivaReal (suburb) → custo de aquisição por região (sem join direto, agregação por suburb)
```

**Atenção:** Mesh tem múltiplas datas por listing (99 snapshots). Usar a **data mais recente** por listing para lat/long e suburb.

---

## Stack

- **Python 3.11+** com `uv` + `pyproject.toml`
- **Polars** para wrangling (justificativa: mais rápido que pandas para 118k+ linhas, API mais expressiva para group_by/window)
- **DuckDB** para queries SQL locais e prototipagem
- **Sem Jupyter Notebook**
- Scripts `.py` executáveis via CLI
- Output: relatório em markdown + dashboard opcional (Streamlit ou Lovable)
