# Walmart Sales BI

Projeto da disciplina de GDIC: dashboards interativos no Tableau sobre as vendas semanais do Walmart (45 lojas, 81 departamentos, fev/2010 a out/2012), com sazonalidade, feriados e fatores externos.

**Apresentação: 19/11/2026.**

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `dados/` | `walmart_sales_analitico_br.csv`: base integrada (vendas + lojas + indicadores), separador `;` e decimal `,` |
| `tableau/` | `Walmart Sales BI.twb`: pasta de trabalho do Tableau |
| `docs/` | `andamento-do-projeto.pdf`: etapas, planejamento dos dashboards e estrutura do relatório |
| `analises/` | `explorar.py`: números de apoio para cada gráfico; a saída fica em `explorar_saida.txt` |

Para gerar os números de novo:

```bash
uv run analises/explorar.py
```

## Dashboards planejados

1. **Visão geral das vendas:** vendas totais, evolução semanal, vendas por tipo de loja, ranking das lojas e participação dos departamentos.
2. **Sazonalidade e feriados:** semanas com e sem feriado, comportamento mensal e semanas de maior faturamento.
3. **Fatores associados às vendas:** temperatura, combustível, desemprego, CPI, MarkDowns e tamanho da loja. É uma análise exploratória, sem presumir causalidade.

## Gráficos

| Análise | Visualização | Status | O que os dados mostram |
|---|---|---|---|
| Vendas totais | KPI | Feito | US$ 6,74 bi no período |
| Evolução semanal | Linha | Feito | Picos em novembro e dezembro, nos dois anos |
| Vendas por tipo de loja | Barras | Feito | Tipo A: 49% das lojas e 64% das vendas. Tipo C: 6% das vendas |
| Ranking das lojas | Barras horizontais | | A loja 20 vende 8,1 vezes mais que a 33. O top 5 é todo de lojas tipo A grandes |
| Vendas por departamento | Barras (Pareto) | | 10 dos 81 departamentos fazem 46% das vendas, e 20 fazem 68% |
| Semanas de feriado | Barras comparativas | | Feriado tem média 8% maior, mas só por causa do Thanksgiving. Super Bowl e Labor Day ficam na média, e a semana de Natal marcada como feriado fica abaixo dela |
| Sazonalidade mensal | Mapa de calor ano × mês | | Dezembro é cerca de 22% acima da média, janeiro é o pior mês, e o padrão se repete nos três anos |
| Tamanho da loja | Dispersão | | Correlação de 0,81: é o fator que mais explica as vendas |
| Temperatura × vendas | Dispersão | | Quase nenhuma relação (−0,06) |
| Indicadores econômicos × vendas | Dispersão | | Combustível, CPI e desemprego ficam com correlação perto de zero |
| MarkDowns × vendas | Exploratória | | Só cerca de 30% das loja-semanas têm o dado, e só a partir de nov/2011. MD1 e MD5 têm correlação de 0,55 e 0,60, mas isso provavelmente vem do tamanho da loja |
| Previsão de vendas | Série temporal com previsão | | Fica para o fim. A sazonalidade anual é forte, então a previsão nativa do Tableau ou um modelo sazonal simples resolve |

## Limitações

- Os MarkDown1 a MarkDown5 estão quase todos vazios antes de novembro de 2011. Os valores foram mantidos sem imputação.
- 1.285 linhas têm venda semanal negativa, provavelmente devoluções.
- O feriado `IsHoliday` cai na semana de **sexta** anterior. Por isso, a semana do Natal marcada como feriado (31/12) é pós-Natal, e o pico de verdade está em 24/12, numa semana que não aparece como feriado.
- Correlação não é causalidade. O tamanho da loja confunde quase todas as outras relações.
