# Insights dos gráficos

Na mesma ordem do documento de insights do grupo, para colar lá. Os números vêm de `analises/explorar.py` e batem com as planilhas do Tableau.

## Ranking das lojas
- A loja 20 (US$ 301 mi) vende **8,1 vezes** mais que a loja 33 (US$ 37 mi).
- O top 5 (lojas 20, 4, 14, 13 e 2) é todo de lojas **tipo A** com mais de 200 mil pés².
- Anomalia: as lojas 33 e 36 são classificadas como tipo A, mas têm cerca de 40 mil pés² e estão entre as que menos vendem. O "tipo" não é só uma faixa de tamanho.

## Vendas por departamento
- O faturamento é concentrado: **10 dos 81 departamentos fazem 46%** das vendas, e 20 fazem 68%.
- Os maiores são os departamentos 92 (7,2%), 95 (6,7%) e 38 (5,8%).
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
- A flag `IsHoliday` do Natal cai na semana **depois** do Natal, que vende abaixo de uma semana comum. A semana campeã do ano, que é a anterior ao Natal, nem aparece como feriado. Ou seja, a variável de feriado da base não captura o maior efeito sazonal.

## Sazonalidade mensal
- Dezembro tem média de cerca de **US$ 57,7 mi por semana**, 22% acima da média geral (47,1), e novembro vem em seguida.
- **Janeiro é o pior mês** (41 a 42 mi), a ressaca pós-festas.
- O padrão **se repete nos três anos** e o resto do ano é bem estável (44 a 48 mi). O crescimento ano a ano é pequeno.

## Vendas por tamanho da loja
- O tamanho é o fator que mais se relaciona com as vendas: **correlação de 0,81**.
- No gráfico as três faixas aparecem bem separadas: C pequenas, B médias e A grandes.
- Por isso as outras variáveis precisam ser comparadas **dentro de cada loja**, senão o tamanho domina tudo. É o que o campo "Vendas vs. média da loja" faz.

## Temperatura × vendas
- A relação é quase nula, com correlação de **−0,11** dentro de cada loja.
- Os picos de venda (pontos acima de 0,4) aparecem entre 30 e 50 °F, que é a temperatura do fim do ano. Isso é efeito do calendário, não do clima.

## Indicadores econômicos × vendas
- Combustível, CPI e desemprego têm **correlação perto de zero** com as vendas, tanto no total quanto dentro de cada loja (entre −0,06 e +0,06).
- No período analisado, as vendas semanais não acompanham os indicadores macro, que mudam devagar demais para explicar a variação de uma semana para outra.

## Indicadores promocionais (MarkDowns) × vendas
- Só cerca de 30% das loja-semanas têm valor, e só a partir de **novembro de 2011**.
- No total, MD1 e MD5 parecem fortes (0,55 e 0,60), mas **é efeito do tamanho**: lojas grandes fazem mais promoção e vendem mais. Dentro de cada loja, isso cai para perto de zero.
- O único que se mantém é o **MarkDown3 (+0,41)**, que se concentra no Thanksgiving e no Natal. Ele acompanha a sazonalidade, então não dá para dizer que causa as vendas.

## Previsão de vendas
- Ainda não foi feita. A sazonalidade anual é forte e estável, então a previsão nativa do Tableau (Analysis > Forecast na planilha "Evolução Semanal das Vendas") deve funcionar bem.

## Insights que combinam gráficos
- **O calendário manda mais que tudo:** a sazonalidade, os feriados e a temperatura contam a mesma história. O pico é a semana antes do Natal e o Thanksgiving, e o resto do ano é estável.
- **O tamanho da loja explica a escala, o calendário explica a variação.** Clima, economia e promoção quase não mexem nas vendas quando se olha dentro de cada loja.
