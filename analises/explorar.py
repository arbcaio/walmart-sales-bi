# /// script
# dependencies = ["pandas", "numpy", "scipy"]
# ///
"""Números de apoio para os gráficos do dashboard.

Rodar da raiz do repositório:  uv run analises/explorar.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

CSV = Path(__file__).resolve().parent.parent / "dados" / "walmart_sales_analitico_br.csv"
df = pd.read_csv(CSV, sep=";", decimal=",", parse_dates=["Date"])
df["IsHoliday"] = df["IsHoliday"].astype(str).eq("True")
mi = 1e6


def titulo(t):
    print(f"\n=== {t}")


titulo("Base")
print(f"{len(df):,} linhas | {df.Store.nunique()} lojas | {df.Dept.nunique()} departamentos | "
      f"{df.Date.min():%d/%m/%Y} a {df.Date.max():%d/%m/%Y} ({df.Date.nunique()} semanas)")
print(f"Vendas totais: US$ {df.Weekly_Sales.sum()/1e9:.2f} bi | linhas com venda negativa: {(df.Weekly_Sales<0).sum():,}")

# Uma linha por loja-semana para variáveis que não dependem do departamento
sem = (df.groupby(["Store", "Date"])
         .agg(vendas=("Weekly_Sales", "sum"), feriado=("IsHoliday", "first"),
              temp=("Temperature", "first"), comb=("Fuel_Price", "first"),
              cpi=("CPI", "first"), desemp=("Unemployment", "first"),
              tipo=("Type", "first"), tamanho=("Size", "first"),
              **{f"md{i}": (f"MarkDown{i}", "first") for i in range(1, 6)})
         .reset_index())

titulo("Vendas por tipo de loja")
t = sem.groupby("tipo").agg(lojas=("Store", "nunique"), total=("vendas", "sum"),
                            media_semana_loja=("vendas", "mean"))
t["participacao_%"] = 100 * t.total / t.total.sum()
t["total"] /= mi
t["media_semana_loja"] /= 1e3
print(t.round(1).to_string())

titulo("Ranking das lojas (total, US$ mi)")
r = sem.groupby(["Store", "tipo", "tamanho"]).vendas.sum().div(mi).sort_values(ascending=False).round(1)
print("Top 5:\n" + r.head().to_string())
print("Bottom 5:\n" + r.tail().to_string())
print(f"Maior/menor: {r.iloc[0]/r.iloc[-1]:.1f}x")

titulo("Departamentos (participação no faturamento)")
d = df.groupby("Dept").Weekly_Sales.sum().sort_values(ascending=False)
p = 100 * d / d.sum()
print(p.head(10).round(1).to_string())
print(f"Top 10 deptos = {p.head(10).sum():.1f}% do total; top 20 = {p.head(20).sum():.1f}%")

titulo("Semanas com e sem feriado (média por loja-semana, US$ mil)")
print(sem.groupby("feriado").vendas.mean().div(1e3).round(1).to_string())
total_semana = sem.groupby("Date").agg(vendas=("vendas", "sum"), feriado=("feriado", "first"))
print("Semanas de feriado (total da rede, US$ mi):")
print(total_semana[total_semana.feriado].vendas.div(mi).round(1).to_string())
print("Top 8 semanas da série:")
print(total_semana.vendas.div(mi).sort_values(ascending=False).head(8).round(1).to_string())

titulo("Sazonalidade mensal (média semanal da rede, US$ mi) — mapa de calor ano × mês")
total_semana["ano"] = total_semana.index.year
total_semana["mes"] = total_semana.index.month
print(total_semana.pivot_table(index="ano", columns="mes", values="vendas", aggfunc="mean").div(mi).round(1).to_string())

titulo("Correlações com as vendas por loja-semana (Pearson | Spearman)")
for c in ["tamanho", "temp", "comb", "cpi", "desemp"]:
    print(f"{c:>8}: {sem.vendas.corr(sem[c]):+.2f} | {sem.vendas.corr(sem[c], method='spearman'):+.2f}")
print("Mesmas variáveis, mas dentro de cada loja (tira o efeito do tamanho):")
z = sem.copy()
z["v"] = z.groupby("Store").vendas.transform(lambda s: (s - s.mean()) / s.std())
for c in ["temp", "comb", "cpi", "desemp"]:
    z["x"] = z.groupby("Store")[c].transform(lambda s: (s - s.mean()) / s.std())
    print(f"{c:>8}: {z.v.corr(z.x):+.2f}")

titulo("MarkDowns (promoções)")
print("% de loja-semanas com valor preenchido:")
print((100 * sem[[f"md{i}" for i in range(1, 6)]].notna().mean()).round(1).to_string())
desde = sem[sem.Date >= "2011-11-11"]
print("A partir de 11/11/2011 — correlação com vendas (Spearman):")
for i in range(1, 6):
    print(f"  MarkDown{i}: {desde.vendas.corr(desde[f'md{i}'], method='spearman'):+.2f}")
