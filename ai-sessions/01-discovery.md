# Sessão IA 01 — Discovery dos dados

**Ferramenta:** Claude (claude.ai)  
**Data:** 2026-06-11  
**Duração aproximada:** 30 min  
**Objetivo:** Explorar os 5 CSVs, entender schema, qualidade, relacionamentos e armadilhas.

---

## Prompt inicial

> "Tenho 5 CSVs de dados de Itapema (SC) — Airbnb listings, hosts, geolocalização, preços e VivaReal. Preciso entender a estrutura de cada um antes de montar o spec da análise."

## O que a IA fez

Rodou `head -3` e `wc -l` em cada arquivo para mapear schema e volume:

- **Details_Itapema.csv** — 4.530 linhas, 35 colunas. Chave: `airbnb_listing_id`. Tipos: apartamento (83%), casa, hotel, outros. Bedrooms: 3q é moda (1.922), seguido de 2q (1.482).
- **Hosts_ids_Itapema.csv** — 4.441 linhas. Chave: `owner_id`. Campos: superhost, reviews, anos como host, response rate.
- **Mesh_Ids_Data_Itapema.csv** — 4.442 linhas. Chave: `airbnb_listing_id`. Geolocalização com `suburb`. Múltiplos snapshots por listing (99 datas de aquisição).
- **Price_AV_Itapema.csv** — 118.840 linhas. Chave composta: `airbnb_listing_id × date × aquisition_date`. **3 datas de aquisição** (06/jan, 07/jan, 20/jan) capturando o mesmo período de estadia (06/jan a 20/abr).
- **VivaReal_Itapema.csv** — 8.330 linhas. Chave: `listing_id`. Dados de venda. Preço mediano ~R$ 1,75M.

Depois rodou análise de distribuição:

```python
# Suburbs mais frequentes (Airbnb)
Meia Praia: 2860, Centro: 657, Morretes: 441, Tabuleiro dos Oliveiras: 129

# Suburbs mais frequentes (VivaReal)
Meia Praia: 3452, Morretes: 1777, Centro: 1009
```

## Achados importantes

1. **Meia Praia domina** tanto em Airbnb (64%) quanto em VivaReal (41%).
2. **Price_AV tem dupla data** — o desafio avisa explicitamente que tratar como "preço atual" reprova. São 3 snapshots do mesmo período, modelando yield management.
3. **Mesh tem múltiplas datas por listing** — precisa deduplicar pegando snapshot mais recente.
4. **Hosts tem owner_id duplicado** — 509 owners com múltiplos registros. Precisa deduplicar antes do join ou explode o número de linhas.
5. **Details não tem m²** — Airbnb não publica área. Precisa estimar via VivaReal cruzando por (suburb, bedrooms).
6. **Price_AV cobre só 1.005 listings únicos** dos 4.441 do Details — cobertura de ~22%. Viés para listings mais ativos/populares.

## Onde a IA acelerou

O mapeamento rápido de schema + distribuições que manualmente levaria 1-2h foi feito em minutos. A identificação do problema de duplicatas no Hosts foi imediata a partir do `n_unique` vs. `shape[0]`.

## Onde a IA errou

Não errou factualmente nesta sessão, mas inicialmente não mencionou a baixa cobertura do Price_AV (22%). Só apareceu depois quando o pipeline rodou. Se eu tivesse confiado cegamente no pipeline sem olhar os números, teria analisado só 999 listings achando que eram todos.

---

*Transcript resumido da interação real com Claude.*
