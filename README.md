# Walmart Sales BI

Projeto da disciplina de GDIC: dashboards interativos no Tableau sobre as vendas semanais do Walmart (45 lojas, 81 departamentos, fev/2010 a out/2012), com sazonalidade, feriados e fatores externos.

**Apresentação: 19/11/2026.**

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `dados/` | `walmart_sales_analitico_br.csv`: base integrada (vendas + lojas + indicadores), separador `;` e decimal `,` |
| `tableau/` | `Walmart Sales BI.twbx`: **o arquivo para abrir**, com os dados dentro. `Walmart Sales BI.twb` é o mesmo conteúdo sem os dados. `gerar_workbook.py` monta os dois a partir de `original-victor.twb` (as três planilhas do Victor, sem alteração) |
| `docs/` | `andamento-do-projeto.pdf`: etapas, planejamento dos dashboards e estrutura do relatório. `insights.md`: insights de cada gráfico. `graficos-e-narrativa.pdf`: todos os gráficos, as decisões sobre os dados e a narrativa da apresentação. `prints/`: imagens das planilhas e dos dashboards |
| `analises/` | `explorar.py`: números de apoio para cada gráfico; a saída fica em `explorar_saida.txt` |

Para gerar os números de novo:

```bash
uv run analises/explorar.py
```

Para gerar o `.twb` e o `.twbx` de novo:

```bash
python3 tableau/gerar_workbook.py
```

## Dashboards

Os três têm filtros de loja, tipo de loja, departamento e ano, que valem para todos os gráficos.

1. **Visão geral das vendas:** vendas totais, evolução semanal, vendas por tipo de loja, ranking das lojas e participação dos departamentos.
2. **Sazonalidade e feriados:** semanas de feriado, mapa de calor ano × mês e previsão de vendas.
3. **Fatores associados às vendas:** temperatura, combustível, desemprego, CPI, MarkDowns e tamanho da loja. É uma análise exploratória, sem presumir causalidade.

## Gráficos

| Análise | Visualização | Status | O que os dados mostram |
|---|---|---|---|
| Vendas totais | KPI | Feito | US$ 6,74 bi no período |
| Evolução semanal | Linha | Feito | Picos em novembro e dezembro, nos dois anos |
| Vendas por tipo de loja | Barras | Feito | Tipo A: 49% das lojas e 64% das vendas. Tipo C: 6% das vendas |
| Ranking das lojas | Barras horizontais | Feito | A loja 20 vende 8,1 vezes mais que a 33. O top 5 é todo de lojas tipo A grandes |
| Vendas por departamento | Barras (Pareto) | Feito | 10 dos 81 departamentos fazem 46% das vendas, e 20 fazem 68% |
| Semanas de feriado | Barras comparativas | Feito | Feriado tem média 8% maior, mas só por causa do Thanksgiving. Super Bowl e Labor Day ficam na média, e a semana de Natal marcada como feriado fica abaixo dela |
| Sazonalidade mensal | Mapa de calor ano × mês | Feito | Dezembro é cerca de 22% acima da média, janeiro é o pior mês, e o padrão se repete nos três anos |
| Tamanho da loja | Dispersão (tamanho em m²) | Feito | Correlação de 0,81: é o fator que mais explica as vendas |
| Temperatura × vendas | Dispersão com tendência | Feito | Não encontramos relação neste período (−0,11 dentro de cada loja) |
| Indicadores econômicos × vendas | Dispersão com tendência | Feito | Não encontramos relação neste período: combustível, CPI e desemprego ficam com correlação perto de zero |
| MarkDowns × vendas | Exploratória | Feito | Só cerca de 30% das loja-semanas têm o dado, e só a partir de nov/2011. MD1 e MD5 têm correlação de 0,55 e 0,60, mas dentro de cada loja isso some. Só o MD3 (+0,41) se mantém, porque acompanha o fim do ano |
| Previsão de vendas | Série mensal com previsão do Tableau | Feito | A previsão repete o padrão: cerca de US$ 58 mi por semana em dezembro de 2012 e queda em janeiro. Repetir o mesmo mês do ano anterior erra 2,3% em média |

## Fonte de dados

O `.twbx` leva o extract dentro e abre em qualquer computador com Tableau Public ou Desktop. O `.twb` procura o extract em `tableau/Data/Extracts/walmart_sales_analitico.hyper`, pelo caminho relativo, então abre direto de um clone do repositório.

## Limitações

- Os MarkDown1 a MarkDown5 estão quase todos vazios antes de novembro de 2011. Os valores foram mantidos sem imputação.
- 1.285 linhas têm venda semanal negativa, provavelmente devoluções.
- O feriado `IsHoliday` cai na semana de **sexta** anterior. Por isso, a semana do Natal marcada como feriado (31/12) é pós-Natal, e o pico de verdade está em 24/12, numa semana que não aparece como feriado.
- A base vai de fevereiro de 2010 a outubro de 2012: 2010 não tem janeiro e 2012 não tem novembro nem dezembro. As comparações usam média por semana, nunca total do ano.
- Correlação não é causalidade. O tamanho da loja confunde quase todas as outras relações.
