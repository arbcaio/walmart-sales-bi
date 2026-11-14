# Insights dos gráficos

Na mesma ordem do documento de insights do grupo, para colar lá. Os números vêm de `analises/explorar.py` e batem com as planilhas do Tableau.

## Ranking das lojas
- O número de cada loja é o **ID** dela na base, não a posição no ranking. O gráfico ordena as 45 lojas por vendas.
- A loja 20 (US$ 301 mi) vende **8,1 vezes** mais que a loja 33 (US$ 37 mi).
- O top 5 (lojas 20, 4, 14, 13 e 2) é todo de lojas **tipo A** com cerca de 19 mil m².
- Anomalia: as lojas 33 e 36 são classificadas como tipo A, mas têm cerca de 3,7 mil m² e estão entre as que menos vendem. O "tipo" não é só uma faixa de tamanho.

## Vendas por departamento
- O número é o **ID** do departamento. São 81 departamentos, com IDs que vão até 99.
- O faturamento é concentrado: **10 dos 81 departamentos fazem 46%** das vendas, e 20 fazem 68%.
- Os maiores são os departamentos 92 (7,2%), 95 (6,7%) e 38 (5,8%).
- O gráfico é um Pareto: à esquerda as vendas de cada departamento, à direita o percentual acumulado.
- A base não diz o que cada departamento vende (são só números), e isso é uma limitação para a interpretação.

## Vendas em semanas de feriado
Média de vendas da rede inteira por semana:

| Semana | US$ mi/semana |
|---|---|
| Semana antes do Natal (não marcada como feriado) | **79,0** |
| Thanksgiving | 66,2 |
| Super Bowl | 48,6 |
| Labor Day | 46,9 |
| Semana comum | 46,4 |
| "Natal" marcado como feriado (semana de 31/12) | **43,2** |

- No geral, as semanas de feriado vendem 8% acima das outras, mas **quem puxa isso é só o Thanksgiving** (Black Friday).
- Super Bowl e Labor Day ficam praticamente na média.
- Nenhum dado foi criado: as categorias são só um agrupamento das semanas reais pela data. "Semana antes do Natal" são as semanas de 24/12/2010 e 23/12/2011, que a base não marca como feriado. O que é nosso é o rótulo, as vendas são as da base.
- Cada categoria de feriado tem só 2 ou 3 semanas na base, então a média é uma indicação, não uma estimativa precisa.
- A flag `IsHoliday` do Natal cai na semana **depois** do Natal, que vende abaixo de uma semana comum. A semana campeã do ano, que é a anterior ao Natal, nem aparece como feriado. Ou seja, a variável de feriado da base não captura o maior efeito sazonal.

## Sazonalidade mensal
- Dezembro tem média de cerca de **US$ 57,7 mi por semana**, 22% acima da média geral (47,1), e novembro vem em seguida.
- **Janeiro é o pior mês** (41 a 42 mi), a ressaca pós-festas.
- O padrão **se repete nos três anos** e o resto do ano é bem estável (44 a 48 mi). O crescimento ano a ano é pequeno (cerca de 2% entre 2011 e 2012, comparando fevereiro a outubro).
- **Anos incompletos:** a base vai de fevereiro de 2010 a outubro de 2012, então 2010 não tem janeiro e 2012 não tem novembro nem dezembro. Por isso comparamos sempre a **média por semana**, nunca o total do ano, e as células sem dado ficam em branco no mapa de calor. O total de 2012 é menor só porque faltam os dois meses mais fortes.

## Vendas por tamanho da loja
- O tamanho é o fator que mais se relaciona com as vendas: **correlação de 0,81**.
- O tamanho está em **m²**, convertido de pés² (× 0,0929). A base não documenta a unidade do campo `Size`; pés² é a suposição que bate com o porte de um Walmart nos EUA.
- No gráfico as três faixas aparecem bem separadas: C pequenas, B médias e A grandes.
- Por isso as outras variáveis precisam ser comparadas **dentro de cada loja**, senão o tamanho domina tudo. É o que o campo "Vendas vs. média da loja" faz.

## Temperatura × vendas
- Não encontramos relação neste período: a correlação é de **−0,11** dentro de cada loja, e a linha de tendência é quase horizontal.
- Os picos de venda (pontos acima de +40%) aparecem entre −5 e 10 °C, que é a temperatura do fim do ano. Isso é efeito do calendário, não do clima.

## Indicadores econômicos × vendas
- **Não encontramos relação neste período** entre as vendas e combustível, CPI ou desemprego: as correlações ficam entre −0,06 e +0,06, tanto no total quanto dentro de cada loja.
- Isso não prova que a economia não afeta as vendas. Em 33 meses os indicadores macro mudam devagar demais para explicar a variação de uma semana para outra; uma série mais longa poderia mostrar outra coisa.

## Indicadores promocionais (MarkDowns) × vendas
- Só cerca de 30% das loja-semanas têm valor, e só a partir de **novembro de 2011**.
- No total, MD1 e MD5 parecem fortes (0,55 e 0,60), mas **é efeito do tamanho**: lojas grandes fazem mais promoção e vendem mais. Dentro de cada loja, isso cai para perto de zero.
- O único que se mantém é o **MarkDown3 (+0,41)**, que se concentra no Thanksgiving e no Natal. Ele acompanha a sazonalidade, então não dá para dizer que causa as vendas.

## Previsão de vendas
- Feita com a previsão nativa do Tableau (suavização exponencial com tendência e sazonalidade), sobre a **média semanal da rede em cada mês**, 14 meses à frente, com faixa de 95%.
- A previsão repete o padrão: cerca de **US$ 58 mi por semana em dezembro de 2012**, queda para cerca de 43 mi em janeiro de 2013 e novo pico perto de 59 mi em dezembro de 2013.
- Por que mensal: na série semanal o modelo do Tableau não achou a sazonalidade de 52 semanas e a previsão saiu reta, sem o pico do Natal. Na série mensal ele pega.
- Conferência simples fora do Tableau: prever cada mês de fevereiro a outubro de 2012 repetindo o mesmo mês de 2011 erra em média **2,3%** (no máximo 4,1%). A série é muito regular, e por isso a previsão é confiável no curto prazo.
- Limite: são menos de três ciclos anuais. A previsão supõe que nada muda (mesmas lojas, mesmo calendário).

## Dashboards
Os três dashboards têm os mesmos quatro filtros no topo (loja, tipo de loja, departamento e ano), que valem para todos os gráficos ao mesmo tempo.
1. **Visão Geral das Vendas:** KPI, vendas por tipo de loja, evolução semanal, ranking das lojas e Pareto dos departamentos.
2. **Sazonalidade e Feriados:** semanas de feriado, mapa de calor ano × mês e previsão.
3. **Fatores Associados às Vendas:** tamanho da loja, temperatura, indicadores econômicos e MarkDowns.

As correlações escritas nos títulos foram calculadas com a base inteira. Elas não mudam quando se mexe nos filtros.

## Insights que combinam gráficos
- **O calendário manda mais que tudo:** a sazonalidade, os feriados e a temperatura contam a mesma história. O pico é a semana antes do Natal e o Thanksgiving, e o resto do ano é estável.
- **O tamanho da loja explica a escala, o calendário explica a variação.** Clima, economia e promoção quase não mexem nas vendas quando se olha dentro de cada loja.
