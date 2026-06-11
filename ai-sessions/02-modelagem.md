# Sessão IA 02 — Modelagem da resposta principal

**Ferramenta:** Claude (claude.ai)  
**Data:** 2026-06-11  
**Duração aproximada:** 45 min  
**Objetivo:** Definir como responder cada pergunta do desafio e montar spec.md + plan.md.

---

## Prompt inicial

> "O desafio pede: melhor perfil de imóvel, melhor localização, características das melhores receitas, onde construir 50 aptos e ROI 2025-2027. Os termos são vagos de propósito. Me ajuda a definir operacionalmente cada um e montar o spec."

## Decisões de modelagem tomadas com a IA

### "Melhor perfil de imóvel"

**Debate:** receita bruta absoluta ou receita por m²?

- Receita bruta favorece imóveis grandes (4q > 2q sempre em valor absoluto)
- Receita por m² equaliza a comparação e é o que um investidor quer saber

**Decisão:** receita líquida anual por m², com m² estimado via VivaReal. Mediana ao invés de média pra evitar distorção de outliers.

### "Melhor localização"

**Debate:** qual métrica e qual filtro mínimo?

- Média por suburb é distorcida por apartamentos de luxo em Meia Praia
- Bairros com 3-5 listings não são estatisticamente significativos

**Decisão:** mediana de receita por suburb, filtro mínimo de ≥20 listings.

### Tratamento do Price_AV (dupla data)

Este foi o ponto mais crítico. A IA propôs 3 abordagens:

1. **Usar só o último snapshot (2025-01-20)** como preço "resolvido" — reflete a decisão final do host
2. **Calcular delta entre snapshots** (06→20) como sinal de yield management — hosts que sobem preço perto da data têm demanda alta
3. **Listings que desaparecem entre snapshots** = proxy de ocupação (foram reservados)

**Decisão:** combinar as 3. Preço resolvido para receita, delta para análise de drivers, desaparecimento para ocupação.

### Ocupação estimada

**Debate:** como estimar ocupação sem dados reais de reserva?

- Opção 1: noites sem preço = ocupadas (conservador)
- Opção 2: noites sem preço = bloqueadas pelo host (pode não ser reserva)

**Decisão:** usar como proxy, mas documentar a limitação. No spec, campo se chama `ocupacao_estimada` e nunca `ocupacao_real`.

### Sazonalidade

**Problema:** dados cobrem só alta temporada (jan-abr). ROI anual exige projeção da baixa.

**Decisão:** fator sazonal explícito — baixa temporada (mai-dez) com ocupação a 40% da alta e diária a 70% da alta. Premissas expostas no output.

## O que a IA gerou

- `spec.md` completo com definições, hipóteses testáveis (H1-H6), métricas-chave e modelagem do ROI
- `plan.md` com 5 fases, dependências, riscos e estimativa de tempo

## Onde a IA acelerou

A estruturação do spec com hipóteses numeradas e tabela de riscos saiu pronta em uma passada. Manualmente eu teria escrito algo menos organizado e provavelmente esquecido de explicitar premissas do ROI.

## Onde a IA errou/desviou

1. **Estimativa de m² para 0 quartos no VivaReal deu 275m²** — claramente são terrenos ou salas comerciais categorizados errado. Precisaria filtrar ou tratar como outlier.
2. **A IA sugeriu inicialmente dois repositórios** (um fork pra Parte 3, outro novo pra entrega). Reli o enunciado e percebi que o fork serve pra tudo — a IA corrigiu quando apontei.

## Correções manuais

- Ajustei a definição de "melhor perfil" para incluir `number_of_guests` como variável, que a IA tinha omitido inicialmente
- Adicionei na seção de riscos do plan.md que o mercado pode estar saturando (crescimento de listings), que a IA não mencionou

---

*Transcript resumido da interação real com Claude.*
