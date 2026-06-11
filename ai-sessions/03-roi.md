# Sessão IA 03 — Construção do pipeline e cálculo de ROI

**Ferramenta:** Claude (claude.ai)  
**Data:** 2026-06-11  
**Duração aproximada:** 60 min  
**Objetivo:** Implementar o pipeline em Polars, debugar problemas nos joins e produzir o cálculo de ROI.

---

## Prompt inicial

> "Gera o código Python completo com Polars: ingestão dos 5 CSVs, feature engineering (joins + receita estimada), análises P1-P5 e cálculo de ROI. Estrutura modular com pyproject.toml + uv."

## O que a IA gerou

Estrutura de 4 módulos:

```
analysis/
  pyproject.toml
  src/
    __init__.py
    main.py       # orquestrador com medição de tempo por fase
    ingest.py     # carrega CSVs + relatório de qualidade
    features.py   # joins + receita estimada + yield delta
    analysis.py   # P1 a P5 + ROI
```

Pipeline end-to-end funcional na primeira geração.

## Bugs encontrados e corrigidos

### Bug 1: Join explosion (CRÍTICO)

**Problema:** Hosts tem 509 `owner_id` duplicados. O join `Details × Hosts` sem dedup gerou 30.822 linhas a partir de 4.441 — multiplicou ~7x.

**Como detectei:** o output mostrou "Listings enriquecidos: 30822 linhas" quando eu sabia que Details tem ~4.500.

**Correção da IA:** deduplicar Hosts por `owner_id` mantendo o registro com mais reviews antes do join.

```python
hosts = (
    hosts
    .sort("number_of_reviews_host", descending=True, nulls_last=True)
    .group_by("owner_id")
    .first()
)
```

**Lição:** nunca confiar cegamente em join sem validar cardinalidade antes e depois.

### Bug 2: hatchling não encontrava o pacote

**Problema:** `uv sync` falhava com "Unable to determine which files to ship inside the wheel".

**Causa:** `pyproject.toml` não informava ao hatchling onde estava o código.

**Correção:** adicionar ao pyproject.toml:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src"]
```

### Bug 3: OUTPUT_DIR no caminho errado

**Problema:** output ia parar em `analysis/src/output/` ao invés de `analysis/output/`.

**Causa:** `Path(__file__).parent` resolve para `src/`, não `analysis/`.

**Correção:** `Path(__file__).resolve().parent.parent / "output"`.

## Resultados do pipeline

```
Tempos de execução:
  fase1_ingestao: 0.10s
  fase2_features: 0.05s
  fase3_analises: 0.01s
  TOTAL: 0.16s
```

### P1 — Melhor perfil:
- 4q apartamento: receita mediana R$ 57.364, diária R$ 988
- 3q apartamento: receita mediana R$ 39.468, diária R$ 660
- 2q apartamento: receita mediana R$ 26.917, diária R$ 464

### P2 — Melhor localização:
- Tabuleiro dos Oliveiras: receita mediana R$ 60.913 (382 listings)
- Morretes: R$ 46.160 (996 listings)
- Meia Praia: R$ 44.637 (4.994 listings) — maior volume

### P4/P5 — ROI do prédio:
- Local: Tabuleiro dos Oliveiras, 2 quartos, 69m²
- Investimento total: R$ 22,77M
- ROI 2025: 2,04% | 2026: 2,13% | 2027: 2,23%

## Onde a IA acelerou

- Pipeline de 4 módulos com ~400 linhas gerado de uma vez, funcional na estrutura
- Medição de tempo já embutida (exigência do desafio)
- Tratamento da dupla data do Price_AV implementado corretamente (snapshot mais recente + delta entre snapshots)

## Onde a IA errou

1. **Join explosion** — o bug mais grave. A IA não verificou cardinalidade dos Hosts antes do join. Eu peguei pelo número absurdo no output.
2. **Paths relativos** — errou 2 vezes (DATA_DIR e OUTPUT_DIR) porque assumiu estrutura de diretório diferente. Precisou de 2 correções.
3. **Não sugeriu `.gitignore` para `analysis/output/`** — outputs gerados não deveriam ir pro repo, mas pra este desafio específico faz sentido incluir pra o avaliador ver.
4. **Superhost com receita MENOR** — o resultado mostra que superhosts têm receita mediana menor (R$ 32.675 vs R$ 44.030). A IA não flagou isso como contraintuitivo. Possível explicação: superhosts em Itapema são hosts mais antigos com imóveis menores/mais baratos, enquanto gestoras profissionais (não-superhost) operam imóveis maiores e mais caros.

## Estimativa de speedup

Sem IA: ~6-8h para pipeline completo (setup, debugging, iteração)  
Com IA: ~2h (incluindo debugging dos 3 bugs acima)  
**Speedup: ~3-4x**

O ganho maior foi na estruturação (módulos, pyproject.toml, medição de tempo). O debugging dos joins eu teria que fazer de qualquer forma — a IA introduziu o bug e eu detectei.

---

*Transcript resumido da interação real com Claude.*
