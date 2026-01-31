#1. Imports
import pandas as pd
import numpy as np

#2. Funão para criação de KPIs
#Calcula KPIs a partir de uma série temporal anual ordenada
def compute_kpis(df):
    #Ordenação cronológica dos dados
    df = df.copy().sort_values("year").reset_index(drop=True)

    #Variação absoluta anual da população: this_year - prev_year
    df["pop_abs_change"] = df["population"].diff()
    #Variação percentual anual da população: (this_year - prev_year) / prev_year * 100
    df["pop_pct_change"] = df["population"].pct_change() * 100
    #Variação absoluta anual do PIB per capita: this_year - prev_year
    df["gdp_pc_abs_change_usd"] = df["gdp_per_capita_usd"].diff()
    #Variação percentual anual do PIB per capita: (this_year - prev_year) / prev_year * 100
    df["gdp_pc_pct_change"] = df["gdp_per_capita_usd"].pct_change() * 100

    #Crescimento médio dos últimos N anos
    #Calcula a taxa de crescimento anual composta (CAGR) para uma janela temporal definida
    def cagr_percent(series, years_window):
        s = series.dropna()
        if len(s) < 2:
            return None
        last = float(s.iloc[-1])
        if len(s) >= years_window:
            first = float(s.iloc[-years_window])
            n_periods = years_window - 1
        else:
            first = float(s.iloc[0])
            n_periods = len(s) - 1
        if first == 0 or n_periods <= 0:
            return None
        try:
            cagr = (last / first) ** (1.0 / n_periods) - 1.0 #n_periods será sempre número de anos - 1
            return cagr * 100.0
        except Exception:
            return None

    #Crescimento médio dos últimos 25 anos (= 24 períodos)
    gdp_cagr = cagr_percent(df["gdp_per_capita_usd"], years_window=25)
    pop_cagr = cagr_percent(df["population"], years_window=25)
    df["pop_cagr_25y"] = pop_cagr
    df["gdp_pc_cagr_25y"] = gdp_cagr

    #Média móvel 5 anos da inflação
    df["inflation_ma_5y"] = df["inflation_pct"].rolling(window=5, min_periods=1).mean()
    #Inflação acumulada em 5 anos: (1+i1​)(1+i2​)…(1+i5​)−1, i sem estar em %
    df["inflation_cum_5y"] = (
        (1 + df["inflation_pct"] / 100)
        .rolling(window=5, min_periods=1)
        .apply(lambda x: x.prod() - 1, raw=False)
        * 100
    )

    #Limpeza de valores infinitos
    df = df.replace([np.inf, -np.inf], pd.NA)
    return df