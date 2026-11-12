"""Acrescenta as planilhas que faltam ao 'Walmart Sales BI.twb'.

Segue o mesmo padrão das planilhas do Victor (mesma fonte de dados) e só insere
o que ainda não existe, então pode rodar de novo sem duplicar nada.

    python3 tableau/gerar_planilhas.py
"""
import re
import uuid
from pathlib import Path
from xml.sax.saxutils import quoteattr

TWB = Path(__file__).with_name("Walmart Sales BI.twb")
DS = "federated.04q3kzx1gxqzh213ayewc0sa8rwq"

# ---------------------------------------------------------------- campos calculados
CALC_MEDIA = "Calculation_1911202600000001"        # média semanal (total ÷ nº de semanas)
CALC_FERIADO = "Calculation_1911202600000002"      # nome do feriado
CALC_MEDIA_LOJA = "Calculation_1911202600000003"   # média semanal de cada loja (LOD)
CALC_VS_LOJA = "Calculation_1911202600000004"      # semana vs. média da própria loja

CALCS = {
    CALC_MEDIA: ("Vendas médias por semana", "real", "measure", "quantitative",
                 "SUM([Weekly_Sales]) / COUNTD([Date])"),
    CALC_FERIADO: ("Feriado", "string", "dimension", "nominal",
                   'IF [IsHoliday] AND MONTH([Date]) = 2 THEN "Super Bowl"\n'
                   'ELSEIF [IsHoliday] AND MONTH([Date]) = 9 THEN "Labor Day"\n'
                   'ELSEIF [IsHoliday] AND MONTH([Date]) = 11 THEN "Thanksgiving"\n'
                   'ELSEIF [IsHoliday] AND MONTH([Date]) = 12 THEN "Natal (semana de 31/12)"\n'
                   'ELSEIF MONTH([Date]) = 12 AND DAY([Date]) >= 18 AND DAY([Date]) <= 24 '
                   'THEN "Semana antes do Natal (não marcada)"\n'
                   'ELSE "Semana comum" END'),
    CALC_MEDIA_LOJA: ("Média semanal da loja", "real", "measure", "quantitative",
                      "{ FIXED [Store] : SUM([Weekly_Sales]) / COUNTD([Date]) }"),
    CALC_VS_LOJA: ("Vendas vs. média da loja", "real", "measure", "quantitative",
                   f"SUM([Weekly_Sales]) / AVG([{CALC_MEDIA_LOJA}]) - 1"),
}

# ---------------------------------------------------------------- colunas usadas
COLS = {
    "Weekly_Sales": ("Weekly Sales", "real", "measure", "quantitative"),
    "Store": (None, "integer", "dimension", "ordinal"),
    "Dept": (None, "integer", "dimension", "ordinal"),
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
         "yr": "Year", "mn": "Month"}
TIPO = {"qk": "quantitative", "nk": "nominal", "ok": "ordinal"}


def ref(inst):
    return f"[{DS}].[{inst}]"


def column_xml(name, indent):
    if name in CALCS:
        cap, dt, role, typ, formula = CALCS[name]
        return (f"{indent}<column caption={quoteattr(cap)} datatype='{dt}' name='[{name}]' "
                f"role='{role}' type='{typ}'>\n{indent}  <calculation class='tableau' "
                f"formula={quoteattr(formula)} />\n{indent}</column>\n")
    cap, dt, role, typ = COLS[name]
    c = f"caption={quoteattr(cap)} " if cap else ""
    return f"{indent}<column {c}datatype='{dt}' name='[{name}]' role='{role}' type='{typ}' />\n"


def worksheet(name, rows, cols, mark, color=None, text=None, lod=(), sort=None):
    """rows/cols: listas de instâncias ('sum:Weekly_Sales:qk'); várias = lado a lado."""
    usadas = list(dict.fromkeys(rows + cols + [x for x in (color, text) if x] + list(lod)))
    campos = list(dict.fromkeys(i.split(":")[1] for i in usadas))
    # um campo calculado que usa outro precisa do outro declarado também
    if CALC_VS_LOJA in campos:
        campos.append(CALC_MEDIA_LOJA)
    for c in list(campos):
        if c in CALCS:
            campos += [x for x in re.findall(r"\[([A-Za-z_0-9]+)\]", CALCS[c][4])
                       if x in COLS and x not in campos]
    deps = "".join(column_xml(c, "            ") for c in dict.fromkeys(campos))
    for i in usadas:
        d, f, t = i.split(":")
        deps += (f"            <column-instance column='[{f}]' derivation='{DERIV[d]}' "
                 f"name='[{i}]' pivot='key' type='{TIPO[t]}' />\n")
    sorts = ""
    if sort:
        dim, medida, shelf = sort
        sorts = (f"          <shelf-sorts>\n            <shelf-sort-v2 dimension-to-sort='{ref(dim)}' "
                 f"direction='DESC' is-on-innermost-dimension='true' "
                 f"measure-to-sort-by='{ref(medida)}' shelf='{shelf}' />\n          </shelf-sorts>\n")
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
    style = ""
    if text:
        style = ("            <style>\n              <style-rule element='mark'>\n"
                 "                <format attr='mark-labels-show' value='true' />\n"
                 "                <format attr='mark-labels-cull' value='true' />\n"
                 "              </style-rule>\n            </style>\n")

    def shelf(xs):
        if not xs:
            return None
        s = " + ".join(ref(x) for x in xs)
        return f"({s})" if len(xs) > 1 else s

    r, c = shelf(rows), shelf(cols)
    return (f"    <worksheet name={quoteattr(name)}>\n      <table>\n        <view>\n"
            f"          <datasources>\n            <datasource caption='walmart_sales_analitico' name='{DS}' />\n"
            f"          </datasources>\n          <datasource-dependencies datasource='{DS}'>\n{deps}"
            f"          </datasource-dependencies>\n{sorts}          <aggregation value='true' />\n"
            f"        </view>\n        <style />\n        <panes>\n"
            f"          <pane selection-relaxation-option='selection-relaxation-allow'>\n"
            f"            <view>\n              <breakdown value='auto' />\n            </view>\n"
            f"            <mark class='{mark}' />\n{enc}{style}          </pane>\n        </panes>\n"
            + (f"        <rows>{r}</rows>\n" if r else "        <rows />\n")
            + (f"        <cols>{c}</cols>\n" if c else "        <cols />\n")
            + f"      </table>\n      <simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' />\n    </worksheet>\n")


def window(name):
    return (f"    <window class='worksheet' name={quoteattr(name)}>\n      <cards>\n"
            "        <edge name='left'>\n          <strip size='160'>\n            <card type='pages' />\n"
            "            <card type='filters' />\n            <card type='marks' />\n          </strip>\n"
            "        </edge>\n        <edge name='top'>\n          <strip size='2147483647'>\n"
            "            <card type='columns' />\n          </strip>\n          <strip size='2147483647'>\n"
            "            <card type='rows' />\n          </strip>\n          <strip size='2147483647'>\n"
            "            <card type='title' />\n          </strip>\n        </edge>\n      </cards>\n"
            f"      <simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' />\n    </window>\n")


VENDAS = "sum:Weekly_Sales:qk"
MEDIA = f"usr:{CALC_MEDIA}:qk"
VS_LOJA = f"usr:{CALC_VS_LOJA}:qk"
LOJA, TIPO_LOJA, DATA = "none:Store:ok", "none:Type:nk", "none:Date:qk"

PLANILHAS = {
    "Ranking das Lojas": dict(
        rows=[LOJA], cols=[VENDAS], mark="Bar", color=TIPO_LOJA,
        sort=(LOJA, VENDAS, "rows")),
    "Vendas por Departamento": dict(
        rows=["none:Dept:ok"], cols=[VENDAS], mark="Bar",
        sort=("none:Dept:ok", VENDAS, "rows")),
    "Vendas em Semanas de Feriado": dict(
        rows=[f"none:{CALC_FERIADO}:nk"], cols=[MEDIA], mark="Bar", text=MEDIA,
        sort=(f"none:{CALC_FERIADO}:nk", MEDIA, "rows")),
    "Sazonalidade Mensal": dict(
        rows=["yr:Date:ok"], cols=["mn:Date:ok"], mark="Square", color=MEDIA, text=MEDIA),
    "Vendas por Tamanho da Loja": dict(
        rows=[VENDAS], cols=["min:Size:qk"], mark="Circle", color=TIPO_LOJA, lod=[LOJA]),
    "Temperatura x Vendas": dict(
        rows=[VS_LOJA], cols=["avg:Temperature:qk"], mark="Circle", color=TIPO_LOJA,
        lod=[LOJA, DATA]),
    "Indicadores Econômicos x Vendas": dict(
        rows=[VS_LOJA], cols=["avg:Fuel_Price:qk", "avg:CPI:qk", "avg:Unemployment:qk"],
        mark="Circle", color=TIPO_LOJA, lod=[LOJA, DATA]),
    "MarkDowns x Vendas": dict(
        rows=[VS_LOJA], cols=[f"avg:MarkDown{i}:qk" for i in range(1, 6)],
        mark="Circle", color=TIPO_LOJA, lod=[LOJA, DATA]),
}


def main():
    raw = TWB.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    xml = raw.replace("\r\n", "\n")

    # campos calculados no nível da fonte de dados, antes do <extract>
    novos = "".join(column_xml(c, "      ") for c in CALCS if f"name='[{c}]'" not in xml)
    xml = xml.replace("      <extract ", novos + "      <extract ", 1)

    ws, wins = "", ""
    for nome, kw in PLANILHAS.items():
        if f"<worksheet name={quoteattr(nome)}>" in xml:
            continue
        ws += worksheet(nome, **kw)
        wins += window(nome)
    xml = xml.replace("  </worksheets>", ws + "  </worksheets>", 1)
    xml = xml.replace("  </windows>", wins + "  </windows>", 1)
    if crlf:  # o arquivo vem do Windows; mantém as quebras de linha dele
        xml = xml.replace("\n", "\r\n")
    TWB.write_bytes(xml.encode("utf-8"))
    print(f"{len(CALCS)} campos calculados, {xml.count('<worksheet ')} planilhas no arquivo")


if __name__ == "__main__":
    main()
