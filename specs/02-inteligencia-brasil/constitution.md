# Constitution — Inteligência Brasil

Princípios não-negociáveis para o produto e para o squad que o constrói.

## 1. Spec antes de código

Nenhuma linha de código entra em PR sem `spec.md` + `plan.md` commitados antes. O `git log --reverse` é a prova. Isso vale para features novas, refatorações e hotfixes que mudem comportamento. Bugfixes triviais (typo, off-by-one) são exceção documentada no PR.

## 2. Idempotência obrigatória

Todo pipeline é re-executável sem efeito colateral. Mesma entrada → mesma saída, sempre. Tabelas gold são recriadas (CTAS com overwrite ou INSERT OVERWRITE por partição), nunca appendadas sem dedup. Jobs com falha parcial não deixam estado corrompido — ou completam ou revertem.

## 3. Custo-bound em Athena e BigQuery

Toda query em produção tem custo estimado antes de ir pra PR. Athena: particionamento por data obrigatório, formatos colunares (Parquet/ORC), scan máximo declarado por job. BigQuery: slot reservation onde aplicável, tabelas particionadas e clusterizadas. Query sem filtro de partição não passa em review.

## 4. Dados versionados

Tabelas bronze são append-only com `aquisition_date` como coluna de versionamento. Nunca sobrescrevemos dado bruto. Silver e gold são derivações reproduzíveis a partir da bronze. Se precisar reprocessar, reprocessa da bronze — não edita silver/gold na mão.

## 5. Contratos com consumidores

Toda tabela gold exposta para RM, Aquisição ou Originação tem schema versionado (colunas, tipos, granularidade, SLA de freshness). Mudança breaking (remover coluna, mudar tipo, mudar granularidade) passa por deprecation notice de 2 sprints antes de efetivar. Consumidores nunca leem bronze ou silver direto.

## 6. Observabilidade antes de feature

Antes de uma tabela gold ir pra produção, ela tem: teste de schema (great_expectations ou dbt test), alerta de freshness (se não atualizou em X horas, avisa), e métrica de volumetria (row count delta > 30% dispara alerta). Sem isso, não é produção — é protótipo.
