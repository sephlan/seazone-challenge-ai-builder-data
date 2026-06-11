# Relatório de Qualidade dos Dados

## details
- **Shape:** 4441 linhas × 35 colunas
- **Nulos (top 10):**
  - `space`: 2527 (56.9%)
  - `is_new_listing`: 874 (19.7%)
  - `check_out`: 842 (19.0%)
  - `check_in`: 446 (10.0%)
  - `can_instant_book`: 355 (8.0%)
  - `is_professional`: 355 (8.0%)
  - `ad_description`: 54 (1.2%)
- **Chave `airbnb_listing_id`:** sem duplicatas

## hosts
- **Shape:** 4440 linhas × 11 colunas
- **Nulos (top 10):**
  - `response_rate_shown`: 4440 (100.0%)
  - `response_time_shown`: 4440 (100.0%)
- **Duplicatas em `owner_id`:** 1383 (4440 total, 3057 únicos)

## mesh
- **Shape:** 4441 linhas × 8 colunas
- **Nulos:** nenhum
- **Chave `airbnb_listing_id`:** sem duplicatas

## price
- **Shape:** 118839 linhas × 4 colunas
- **Nulos:** nenhum
- **Datas de aquisição:** ['2025-01-06', '2025-01-07', '2025-01-20']
- **Range de estadia:** 2025-01-06 a 2025-04-20
- **Listings únicos com preço:** 1005

## vivareal
- **Shape:** 8329 linhas × 22 colunas
- **Nulos (top 10):**
  - `rental_price`: 8327 (100.0%)
  - `rental_period`: 8327 (100.0%)
  - `yearly_iptu`: 2714 (32.6%)
  - `monthly_condo_fee`: 2490 (29.9%)
  - `suburb`: 98 (1.2%)
  - `state`: 2 (0.0%)
- **Duplicatas em `listing_id`:** 36 (8329 total, 8293 únicos)
