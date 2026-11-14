"""Monta o 'Walmart Sales BI.twb' (e o .twbx) a partir do arquivo original do Victor.

Entrada:  tableau/original-victor.twb  (as 3 planilhas dele, intactas)
Saída:    tableau/Walmart Sales BI.twb   abre direto, usa Data/Extracts/*.hyper ao lado
          tableau/Walmart Sales BI.twbx  o mesmo, empacotado num arquivo só para mandar

O que o script acrescenta:
  - campos calculados (média semanal, feriado, vendas vs. média da loja, m², °C...)
  - 9 planilhas novas (ranking, departamentos, feriados, sazonalidade, 4 dispersões, previsão)
  - 4 filtros compartilhados (loja, tipo, departamento, ano) em todas as planilhas,
    inclusive nas 3 do Victor: é a única mudança feita nelas
  - 3 dashboards com esses filtros

    python3 tableau/gerar_workbook.py
"""
import re
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

PASTA = Path(__file__).parent
ORIGINAL = PASTA / "original-victor.twb"
TWB = PASTA / "Walmart Sales BI.twb"
TWBX = PASTA / "Walmart Sales BI.twbx"
HYPER = "Data/Extracts/walmart_sales_analitico.hyper"   # relativo ao .twb
DS = "federated.04q3kzx1gxqzh213ayewc0sa8rwq"
DS_CAPTION = "walmart_sales_analitico"

# ---------------------------------------------------------------- campos calculados
C = "Calculation_19112026000000"
CALC_MEDIA, CALC_FERIADO, CALC_MEDIA_LOJA, CALC_VS_LOJA = C + "01", C + "02", C + "03", C + "04"
CALC_M2, CALC_TIPO, CALC_TEMP_C, CALC_ACUM = C + "05", C + "06", C + "07", C + "08"
CALC_MEDIA_MI, CALC_SEMANA = C + "09", C + "10"

# nome: (legenda, tipo de dado, papel, tipo, fórmula, formato padrão)
CALCS = {
    CALC_MEDIA: ("Vendas médias por semana", "real", "measure", "quantitative",
                 "SUM([Weekly_Sales]) / COUNTD([Date])", None),
    CALC_FERIADO: ("Feriado", "string", "dimension", "nominal",
                   'IF [IsHoliday] AND MONTH([Date]) = 2 THEN "Super Bowl"\n'
                   'ELSEIF [IsHoliday] AND MONTH([Date]) = 9 THEN "Labor Day"\n'
                   'ELSEIF [IsHoliday] AND MONTH([Date]) = 11 THEN "Thanksgiving"\n'
                   'ELSEIF [IsHoliday] AND MONTH([Date]) = 12 THEN "Natal (semana de 31/12)"\n'
                   'ELSEIF MONTH([Date]) = 12 AND DAY([Date]) >= 18 AND DAY([Date]) <= 24 '
                   'THEN "Semana antes do Natal (não marcada)"\n'
                   'ELSE "Semana comum" END', None),
    CALC_MEDIA_LOJA: ("Média semanal da loja", "real", "measure", "quantitative",
                      "{ FIXED [Store] : SUM([Weekly_Sales]) / COUNTD([Date]) }", None),
    CALC_VS_LOJA: ("Vendas vs. média da loja", "real", "measure", "quantitative",
                   f"SUM([Weekly_Sales]) / AVG([{CALC_MEDIA_LOJA}]) - 1", "p0%"),
    # a base não documenta a unidade de Size; pés² é o que bate com o porte de um Walmart
    CALC_M2: ("Tamanho da loja (m²)", "real", "measure", "quantitative",
              "[Size] * 0.092903", None),
    CALC_TIPO: ("Tipo de loja", "string", "dimension", "nominal", "[Type]", None),
    CALC_TEMP_C: ("Temperatura (°C)", "real", "measure", "quantitative",
                  "([Temperature] - 32) * 5 / 9", None),
    CALC_ACUM: ("% acumulado das vendas", "real", "measure", "quantitative",
                "RUNNING_SUM(SUM([Weekly_Sales])) / TOTAL(SUM([Weekly_Sales]))", "p0%"),
}
CALCS.update({
    CALC_MEDIA_MI: ("Vendas médias por semana (US$ milhões)", "real", "measure", "quantitative",
                    "SUM([Weekly_Sales]) / COUNTD([Date]) / 1000000", "n#,##0.0"),
    # total da rede em cada semana; a média disso no mês é a série mensal usada na previsão
    CALC_SEMANA: ("Vendas semanais da rede", "real", "measure", "quantitative",
                  "{ FIXED [Date] : SUM([Weekly_Sales]) }", None),
})
DEPENDE = {CALC_VS_LOJA: [CALC_MEDIA_LOJA]}

# ---------------------------------------------------------------- colunas da base
COLS = {
    "Weekly_Sales": ("Weekly Sales", "real", "measure", "quantitative"),
    "Store": ("Loja (ID)", "integer", "dimension", "ordinal"),
    "Dept": ("Departamento (ID)", "integer", "dimension", "ordinal"),
    "Year": ("Ano", "integer", "dimension", "quantitative"),
    "Month": ("Mês", "integer", "dimension", "quantitative"),
    "Type": (None, "string", "dimension", "nominal"),
    "Date": (None, "date", "dimension", "ordinal"),
    "IsHoliday": ("Is Holiday", "boolean", "dimension", "nominal"),
    "Size": (None, "integer", "measure", "quantitative"),
    "Temperature": (None, "real", "measure", "quantitative"),
    "Fuel_Price": ("Fuel Price", "real", "measure", "quantitative"),
    "CPI": (None, "real", "measure", "quantitative"),
    "Unemployment": (None, "real", "measure", "quantitative"),
    **{f"MarkDown{i}": (None, "real", "measure", "quantitative") for i in range(1, 6)},
}

DERIV = {"sum": "Sum", "avg": "Avg", "min": "Min", "none": "None", "usr": "User",
         "yr": "Year", "mn": "Month", "tmn": "Month-Trunc"}
TIPO = {"qk": "quantitative", "nk": "nominal", "ok": "ordinal"}

VENDAS = "sum:Weekly_Sales:qk"
MEDIA = f"usr:{CALC_MEDIA_MI}:qk"
VS_LOJA = f"usr:{CALC_VS_LOJA}:qk"
ACUM = f"usr:{CALC_ACUM}:qk"
LOJA, DEPTO, DATA = "none:Store:ok", "none:Dept:ok", "none:Date:qk"
TIPO_LOJA = f"none:{CALC_TIPO}:nk"
ANO = "none:Year:ok"

# filtros compartilhados: o mesmo grupo em todas as planilhas faz o filtro valer para todas.
# São filtros de contexto para o FIXED da média da loja respeitar a seleção.
FILTROS = [(LOJA, 1), (TIPO_LOJA, 2), (DEPTO, 3), (ANO, 4)]


def ref(inst):
    return f"[{DS}].[{inst}]"


def novo_id():
    return f"{{{str(uuid.uuid4()).upper()}}}"


def column_xml(name, indent):
    if name in CALCS:
        cap, dt, role, typ, formula, fmt = CALCS[name]
        f = f"default-format='{fmt}' " if fmt else ""
        return (f"{indent}<column caption={quoteattr(cap)} datatype='{dt}' {f}name='[{name}]' "
                f"role='{role}' type='{typ}'>\n{indent}  <calculation class='tableau' "
                f"formula={quoteattr(formula)} />\n{indent}</column>\n")
    cap, dt, role, typ = COLS[name]
    c = f"caption={quoteattr(cap)} " if cap else ""
    return f"{indent}<column {c}datatype='{dt}' name='[{name}]' role='{role}' type='{typ}' />\n"


def campos_de(insts):
    """Campos que precisam ser declarados na planilha para essas instâncias."""
    campos = list(dict.fromkeys(i.split(":")[1] for i in insts))
    for c in list(campos):
        for d in DEPENDE.get(c, []):
            if d not in campos:
                campos.append(d)
    for c in list(campos):
        if c in CALCS:
            campos += [x for x in re.findall(r"\[([A-Za-z_0-9]+)\]", CALCS[c][4])
                       if x in COLS and x not in campos]
    return list(dict.fromkeys(campos))


def instancia_xml(i, indent, table_calc=None):
    d, f, t = i.split(":")
    base = (f"{indent}<column-instance column='[{f}]' derivation='{DERIV[d]}' "
            f"name='[{i}]' pivot='key' type='{TIPO[t]}'")
    if table_calc:   # cálculo de tabela: acumula ao longo desse campo, na ordem da planilha
        return (f"{base}>\n{indent}  <table-calc ordering-field='{ref(table_calc)}' "
                f"ordering-type='Field' />\n{indent}</column-instance>\n")
    return base + " />\n"


def filtros_xml():
    f = ""
    for inst, grupo in FILTROS:
        f += (f"          <filter class='categorical' column='{ref(inst)}' context='true' "
              f"filter-group='{grupo}'>\n            <groupfilter function='level-members' "
              f"level='[{inst}]' user:ui-enumeration='all' user:ui-marker='enumerate' />\n"
              f"          </filter>\n")
    return f


def slices_xml():
    return ("          <slices>\n" + "".join(f"            <column>{ref(i)}</column>\n" for i, _ in FILTROS)
            + "          </slices>\n")


def titulo_xml(texto):
    if not texto:
        return ""
    return ("      <layout-options>\n        <title>\n          <formatted-text>\n"
            f"            <run>{escape(texto)}</run>\n          </formatted-text>\n"
            "        </title>\n      </layout-options>\n")


def worksheet(name, rows, cols, mark, color=None, text=None, lod=(), sort=None, titulo=None,
              eixos=None, larguras=None, tendencia=False, opacidade=None, table_calcs=None,
              previsao=None):
    """rows/cols: listas de instâncias ('sum:Weekly_Sales:qk'); várias = lado a lado.
    eixos: {instância: (scope, título, (mín, máx) ou None)}; larguras: {instância: px}."""
    usadas = list(dict.fromkeys(rows + cols + [x for x in (color, text) if x] + list(lod)
                                + [i for i, _ in FILTROS]))
    deps = "".join(column_xml(c, "            ") for c in campos_de(usadas))
    deps += "".join(instancia_xml(i, "            ", (table_calcs or {}).get(i)) for i in usadas)
    if previsao:   # o Tableau troca a medida por uma versão "real + previsto"
        d, f, _ = previsao.split(":")
        fval = f"fVal:{previsao}"
        deps += (f"            <column-instance column='[{f}]' derivation='{DERIV[d]}' "
                 f"forecast-column-base='[{previsao}]' forecast-column-type='forecast-value' "
                 f"name='[{fval}]' pivot='key' type='quantitative' />\n"
                 "            <column-instance column='[Forecast Indicator]' derivation='None' "
                 "forecast-column-base='[Forecast Indicator]' forecast-column-type='forecast-indicator' "
                 "name='[none:Forecast Indicator:nk]' pivot='key' type='nominal' />\n")
        rows = [fval]
        color = "none:Forecast Indicator:nk"
        eixos = {(fval if k == previsao else k): v for k, v in (eixos or {}).items()}

    sorts = ""
    if sort:
        dim, medida, shelf = sort
        sorts = (f"          <shelf-sorts>\n            <shelf-sort-v2 dimension-to-sort='{ref(dim)}' "
                 f"direction='DESC' is-on-innermost-dimension='true' "
                 f"measure-to-sort-by='{ref(medida)}' shelf='{shelf}' />\n          </shelf-sorts>\n")

    estilo = ""
    if eixos:
        estilo += "          <style-rule element='axis'>\n"
        for inst, (scope, tit, faixa) in eixos.items():
            estilo += (f"            <format attr='title' class='0' field='{ref(inst)}' "
                       f"scope='{scope}' value={quoteattr(tit)} />\n")
            if faixa:
                estilo += (f"            <encoding attr='space' class='0' field='{ref(inst)}' "
                           f"field-type='quantitative' max='{faixa[1]}' min='{faixa[0]}' "
                           f"range-type='fixed' scope='{scope}' type='space' />\n")
        estilo += "          </style-rule>\n"
    if larguras:
        estilo += "          <style-rule element='header'>\n"
        for inst, px in larguras.items():
            estilo += f"            <format attr='width' field='{ref(inst)}' value='{px}' />\n"
        estilo += "          </style-rule>\n"
    estilo = f"        <style>\n{estilo}        </style>\n" if estilo else "        <style />\n"

    enc = ""
    if color or text or lod:
        enc = "            <encodings>\n"
        if color:
            enc += f"              <color column='{ref(color)}' />\n"
        if text:
            enc += f"              <text column='{ref(text)}' />\n"
        for l in lod:
            enc += f"              <lod column='{ref(l)}' />\n"
        enc += "            </encodings>\n"
    if tendencia:
        enc += ("            <trendline enable-confidence-bands='false' enable-instant-analytics='false' "
                "enabled='true' exclude-color='true' exclude-intercept='false' fit='linear' />\n")
    marca = ""
    if text:
        marca += ("                <format attr='mark-labels-show' value='true' />\n"
                  "                <format attr='mark-labels-cull' value='true' />\n")
    if opacidade:
        marca += f"                <format attr='mark-transparency' value='{opacidade}' />\n"
    if marca:
        marca = ("            <style>\n              <style-rule element='mark'>\n" + marca
                 + "              </style-rule>\n            </style>\n")

    def shelf(xs):
        if not xs:
            return None
        s = " + ".join(ref(x) for x in xs)
        return f"({s})" if len(xs) > 1 else s

    r, c = shelf(rows), shelf(cols)
    prev = ""
    if previsao:
        prev = ("        <forecast-specification auto-forecast-agg='true' band-confidence-level='95.000000' "
                "enabled='true' fill-type='fill-zero' ignore-last='0' model-type='custom' "
                "range-type='auto' season-type='ets-additive' show-prediction-bands='true' "
                "trend-type='ets-additive' />\n")
    return (f"    <worksheet name={quoteattr(name)}>\n{titulo_xml(titulo)}      <table>\n        <view>\n"
            f"          <datasources>\n            <datasource caption='{DS_CAPTION}' name='{DS}' />\n"
            f"          </datasources>\n          <datasource-dependencies datasource='{DS}'>\n{deps}"
            f"          </datasource-dependencies>\n{filtros_xml()}{sorts}{slices_xml()}"
            f"          <aggregation value='true' />\n"
            f"        </view>\n{estilo}        <panes>\n"
            f"          <pane selection-relaxation-option='selection-relaxation-allow'>\n"
            f"            <view>\n              <breakdown value='auto' />\n            </view>\n"
            f"            <mark class='{mark}' />\n{enc}{marca}          </pane>\n        </panes>\n"
            + (f"        <rows>{r}</rows>\n" if r else "        <rows />\n")
            + (f"        <cols>{c}</cols>\n" if c else "        <cols />\n")
            + prev + f"      </table>\n      <simple-id uuid='{novo_id()}' />\n    </worksheet>\n")


def window(name, fit=False):
    zoom = "      <viewpoint>\n        <zoom type='entire-view' />\n      </viewpoint>\n" if fit else ""
    return (f"    <window class='worksheet' name={quoteattr(name)}>\n      <cards>\n"
            "        <edge name='left'>\n          <strip size='160'>\n            <card type='pages' />\n"
            "            <card type='filters' />\n            <card type='marks' />\n          </strip>\n"
            "        </edge>\n        <edge name='top'>\n          <strip size='2147483647'>\n"
            "            <card type='columns' />\n          </strip>\n          <strip size='2147483647'>\n"
            "            <card type='rows' />\n          </strip>\n          <strip size='2147483647'>\n"
            "            <card type='title' />\n          </strip>\n        </edge>\n      </cards>\n"
            + zoom + f"      <simple-id uuid='{novo_id()}' />\n    </window>\n")


# ---------------------------------------------------------------- planilhas novas
US = "Vendas no período (US$)"
VS_T = "Vendas vs. média da própria loja"
PLANILHAS = {
    "Ranking das Lojas": dict(
        rows=[LOJA], cols=[VENDAS], mark="Bar", color=TIPO_LOJA, sort=(LOJA, VENDAS, "rows"),
        titulo="Ranking das Lojas (o número é o ID da loja)",
        eixos={VENDAS: ("cols", US, None)}, larguras={LOJA: 70}, fit=True),
    "Vendas por Departamento": dict(
        rows=[DEPTO], cols=[VENDAS, ACUM], mark="Bar", sort=(DEPTO, VENDAS, "rows"),
        table_calcs={ACUM: DEPTO}, larguras={DEPTO: 110},
        titulo="Vendas por Departamento e % acumulado (Pareto)",
        eixos={VENDAS: ("cols", US, None), ACUM: ("cols", "% acumulado das vendas", None)}),
    "Vendas em Semanas de Feriado": dict(
        rows=[f"none:{CALC_FERIADO}:nk"], cols=[MEDIA], mark="Bar", text=MEDIA,
        sort=(f"none:{CALC_FERIADO}:nk", MEDIA, "rows"), larguras={f"none:{CALC_FERIADO}:nk": 260},
        titulo="Vendas em Semanas de Feriado (média da rede por semana)",
        eixos={MEDIA: ("cols", "Vendas médias da rede por semana (US$ milhões)", None)}),
    "Sazonalidade Mensal": dict(
        rows=[ANO], cols=["none:Month:ok"], mark="Square", color=MEDIA, text=MEDIA, fit=True,
        titulo="Sazonalidade Mensal: média por semana em US$ milhões (base: fev/2010 a out/2012)"),
    "Vendas por Tamanho da Loja": dict(
        rows=[VENDAS], cols=[f"min:{CALC_M2}:qk"], mark="Circle", color=TIPO_LOJA, lod=[LOJA],
        tendencia=True, fit=True,
        titulo="Vendas por Tamanho da Loja (correlação 0,81 sem filtros)",
        eixos={VENDAS: ("rows", US, None),
               f"min:{CALC_M2}:qk": ("cols", "Tamanho da loja (m²)", None)}),
    "Temperatura x Vendas": dict(
        rows=[VS_LOJA], cols=[f"avg:{CALC_TEMP_C}:qk"], mark="Circle", color=TIPO_LOJA,
        lod=[LOJA, DATA], tendencia=True, opacidade=70, fit=True,
        titulo="Temperatura x Vendas (correlação −0,11 sem filtros)",
        eixos={VS_LOJA: ("rows", VS_T, None),
               f"avg:{CALC_TEMP_C}:qk": ("cols", "Temperatura média da semana (°C)", None)}),
    "Indicadores Econômicos x Vendas": dict(
        rows=[VS_LOJA], cols=["avg:Fuel_Price:qk", "avg:CPI:qk", "avg:Unemployment:qk"],
        mark="Circle", color=TIPO_LOJA, lod=[LOJA, DATA], tendencia=True, opacidade=70, fit=True,
        titulo="Indicadores Econômicos x Vendas (correlações perto de zero neste período)",
        eixos={VS_LOJA: ("rows", VS_T, None),
               "avg:Fuel_Price:qk": ("cols", "Preço do combustível (US$/galão)", (2.4, 4.6)),
               "avg:CPI:qk": ("cols", "CPI (índice de preços)", (120, 232)),
               "avg:Unemployment:qk": ("cols", "Desemprego (%)", (3.5, 14.5))}),
    "MarkDowns x Vendas": dict(
        rows=[VS_LOJA], cols=[f"avg:MarkDown{i}:qk" for i in range(1, 6)],
        mark="Circle", color=TIPO_LOJA, lod=[LOJA, DATA], tendencia=True, opacidade=70, fit=True,
        titulo="Promoções (MarkDowns) x Vendas (dados só a partir de nov/2011)",
        eixos={VS_LOJA: ("rows", VS_T, None),
               **{f"avg:MarkDown{i}:qk": ("cols", f"MarkDown{i} (US$)", None) for i in range(1, 6)}}),
    "Previsão de Vendas": dict(
        rows=[f"avg:{CALC_SEMANA}:qk"], cols=["tmn:Date:qk"], mark="Automatic",
        previsao=f"avg:{CALC_SEMANA}:qk", fit=True,
        titulo="Previsão de Vendas: média semanal da rede em cada mês, com previsão (faixa de 95%)",
        eixos={f"avg:{CALC_SEMANA}:qk": ("rows", "Média de vendas semanais da rede (US$)", None),
               "tmn:Date:qk": ("cols", "Mês", None)}),
}

# ---------------------------------------------------------------- dashboards
# (planilha, x, y, largura, altura) numa grade de 100000 x 100000, abaixo do título e dos filtros
TOPO = 13000
DASHBOARDS = {
    "Visão Geral das Vendas": [
        ("KPI - Vendas Totais", 0, TOPO, 28000, 10000),
        ("Vendas por Tipo de Loja", 0, TOPO + 10000, 28000, 23000),
        ("Evolução Semanal das Vendas", 28000, TOPO, 72000, 33000),
        ("Ranking das Lojas", 0, TOPO + 33000, 50000, 54000),
        ("Vendas por Departamento", 50000, TOPO + 33000, 50000, 54000),
    ],
    "Sazonalidade e Feriados": [
        ("Vendas em Semanas de Feriado", 0, TOPO, 50000, 38000),
        ("Sazonalidade Mensal", 50000, TOPO, 50000, 38000),
        ("Previsão de Vendas", 0, TOPO + 38000, 100000, 49000),
    ],
    "Fatores Associados às Vendas": [
        ("Vendas por Tamanho da Loja", 0, TOPO, 40000, 43000),
        ("Temperatura x Vendas", 40000, TOPO, 60000, 43000),
        ("Indicadores Econômicos x Vendas", 0, TOPO + 43000, 50000, 44000),
        ("MarkDowns x Vendas", 50000, TOPO + 43000, 50000, 44000),
    ],
}
SEM_AJUSTE = {"Vendas por Departamento", "Ranking das Lojas"}   # muitas barras: melhor rolar do que espremer


def dashboard(nome, itens):
    campos = campos_de([i for i, _ in FILTROS])
    deps = "".join(column_xml(c, "        ") for c in campos)
    deps += "".join(instancia_xml(i, "        ") for i, _ in FILTROS)
    z, n = "", 3
    z += "          <zone h='6000' id='3' type-v2='title' w='100000' x='0' y='0' />\n"
    for k, (inst, _) in enumerate(FILTROS):
        n += 1
        z += (f"          <zone h='7000' id='{n}' mode='checkdropdown' name={quoteattr(itens[0][0])} "
              f"param='{ref(inst)}' type-v2='filter' w='25000' x='{k * 25000}' y='6000' />\n")
    for planilha, x, y, w, h in itens:
        n += 1
        z += f"          <zone h='{h}' id='{n}' name={quoteattr(planilha)} w='{w}' x='{x}' y='{y}' />\n"
    return (f"    <dashboard name={quoteattr(nome)}>\n      <style />\n"
            f"      <datasources>\n        <datasource caption='{DS_CAPTION}' name='{DS}' />\n"
            f"      </datasources>\n      <datasource-dependencies datasource='{DS}'>\n{deps}"
            "      </datasource-dependencies>\n      <zones>\n"
            "        <zone h='100000' id='2' type-v2='layout-basic' w='100000' x='0' y='0'>\n"
            f"{z}        </zone>\n      </zones>\n"
            f"      <simple-id uuid='{novo_id()}' />\n    </dashboard>\n")


def window_dashboard(nome, itens):
    v = ""
    for planilha, *_ in itens:
        zoom = "" if planilha in SEM_AJUSTE else "          <zoom type='entire-view' />\n"
        v += f"        <viewpoint name={quoteattr(planilha)}>\n{zoom}        </viewpoint>\n"
    return (f"    <window class='dashboard' name={quoteattr(nome)}>\n      <viewpoints>\n{v}"
            f"      </viewpoints>\n      <active id='-1' />\n"
            f"      <simple-id uuid='{novo_id()}' />\n    </window>\n")


def filtrar_planilhas_existentes(xml):
    """Põe os 4 filtros compartilhados nas planilhas do Victor, sem mudar mais nada nelas."""
    campos = campos_de([i for i, _ in FILTROS])

    def ajusta(m):
        bloco = m.group(0)
        novos = "".join(column_xml(c, "            ") for c in campos if f"name='[{c}]'" not in bloco)
        novos += "".join(instancia_xml(i, "            ") for i, _ in FILTROS if f"name='[{i}]'" not in bloco)
        bloco = bloco.replace("          </datasource-dependencies>\n",
                              novos + "          </datasource-dependencies>\n" + filtros_xml(), 1)
        return bloco.replace("          <aggregation ", slices_xml() + "          <aggregation ", 1)

    return re.sub(r"    <worksheet name=.*?</worksheet>\n", ajusta, xml, flags=re.S)


def main():
    xml = ORIGINAL.read_bytes().decode("utf-8").replace("\r\n", "\n")

    # extract ao lado do .twb, em caminho relativo: abre em qualquer computador
    xml, n = re.subn(r"dbname='[^']*\.hyper'", f"dbname='{HYPER}'", xml)
    assert n == 1, "não achei o extract no arquivo original"

    # Store, Dept, Year e Month ganham nome em português (nenhuma planilha do Victor usa esses campos)
    for campo in ("Store", "Dept"):
        xml = xml.replace(f"<column aggregation='Sum' datatype='integer' name='[{campo}]' ",
                          f"<column aggregation='Sum' caption={quoteattr(COLS[campo][0])} "
                          f"datatype='integer' name='[{campo}]' ", 1)
    for campo in ("Year", "Month"):
        xml = xml.replace(f"<column datatype='integer' name='[{campo}]' ",
                          f"<column caption={quoteattr(COLS[campo][0])} datatype='integer' name='[{campo}]' ", 1)

    # campos calculados no nível da fonte de dados, antes do <extract>
    novos = "".join(column_xml(c, "      ") for c in CALCS)
    xml = xml.replace("      <extract ", novos + "      <extract ", 1)

    xml = filtrar_planilhas_existentes(xml)

    ws, wins = "", ""
    for nome, kw in PLANILHAS.items():
        kw = dict(kw)
        fit = kw.pop("fit", False)
        ws += worksheet(nome, **kw)
        wins += window(nome, fit)
    xml = xml.replace("  </worksheets>", ws + "  </worksheets>", 1)

    dash = "  <dashboards>\n" + "".join(dashboard(n, i) for n, i in DASHBOARDS.items()) + "  </dashboards>\n"
    xml = xml.replace("  <windows ", dash + "  <windows ", 1)
    wins += "".join(window_dashboard(n, i) for n, i in DASHBOARDS.items())
    xml = xml.replace("  </windows>", wins + "  </windows>", 1)

    dados = xml.replace("\n", "\r\n").encode("utf-8")   # o original vem do Windows
    TWB.write_bytes(dados)
    with zipfile.ZipFile(TWBX, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(TWB.name, dados)
        z.write(PASTA / HYPER, HYPER)
    print(f"{xml.count('<worksheet ')} planilhas, {xml.count('<dashboard ')} dashboards "
          f"-> {TWB.name} e {TWBX.name}")


if __name__ == "__main__":
    main()
