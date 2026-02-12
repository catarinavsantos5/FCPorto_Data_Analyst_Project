#1. Imports
import pandas as pd
import numpy as np
import requests
import datetime


#2. Funão para criação de KPIs
#Calcula KPIs a partir de uma série temporal anual ordenada
def compute_kpis(df):

    df = df.copy()

    # Ordenar por país e ano
    df = df.sort_values(["country", "year"]).reset_index(drop=True)

    # Cálculo por país
    def compute_country_kpis(group):
        group = group.sort_values("year").copy()

        #PIB total em usd
        group["gdp_total_usd"] = group["population"] * group["gdp_per_capita_usd"]

        # Variação absoluta anual da população: this_year - prev_year
        group["pop_abs_change"] = group["population"].diff()
        # Variação percentual anual da população: (this_year - prev_year) / prev_year * 100
        group["pop_pct_change"] = group["population"].pct_change() * 100

        #Variação absoluta anual do PIB per capita: this_year - prev_year
        group["gdp_pc_abs_change_usd"] = group["gdp_per_capita_usd"].diff()
        #Variação percentual anual do PIB per capita: (this_year - prev_year) / prev_year * 100
        group["gdp_pc_pct_change"] = group["gdp_per_capita_usd"].pct_change() * 100

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
        group["pop_cagr_25y"] = cagr_percent(group["population"], years_window=25)
        group["gdp_pc_cagr_25y"] = cagr_percent(group["gdp_per_capita_usd"], years_window=25)

        # Inflação
        #Média móvel 5 anos da inflação
        group["inflation_ma_5y"] = group["inflation_pct"].rolling(5, min_periods=1).mean()

        #Inflação acumulada em 5 anos: (1+i1​)(1+i2​)…(1+i5​)−1, i sem estar em %
        group["inflation_cum_5y"] = (
            (1 + group["inflation_pct"] / 100)
            .rolling(5, min_periods=1)
            .apply(lambda x: x.prod() - 1, raw=False)
            * 100
        )

        return group

    # Aplicar por país
    df = df.groupby("country", group_keys=False).apply(compute_country_kpis)

    #Limpeza de valores infinitos
    df = df.replace([np.inf, -np.inf], pd.NA)
    return df

#3. Função para armazenar taxa de conversão USD-EUR, para os últimos N anos com info disponível
def build_rates_df(last_n_years):

    current_year = datetime.datetime.now().year
    collected_years = []
    collected_rows = []

    year = current_year

    # Obter N anos com dados
    while year >= 1960 and len(collected_years) < last_n_years:
        start = f"{year}-01-01"
        end = f"{year}-12-31"

        url = f"https://api.frankfurter.app/{start}..{end}"

        try:
            r = requests.get(url, params={"from": "USD", "to": "EUR"}, timeout=30)
            r.raise_for_status()
            payload = r.json()
            rates = payload.get("rates", {})

            if rates:
                year_has_data = False

                for date_str, v in rates.items():
                    rate = v.get("EUR")
                    if rate is None:
                        continue

                    collected_rows.append({
                        "date": pd.to_datetime(date_str),
                        "rate": float(rate)
                    })
                    year_has_data = True

                if year_has_data:
                    collected_years.append(year)

        except Exception:
            None

        year -= 1

    if not collected_rows:
        print("[ERROR] Nenhuma taxa encontrada.")
        return None

    df_daily = pd.DataFrame(collected_rows).sort_values("date").reset_index(drop=True)
    df_daily["year"] = df_daily["date"].dt.year

    df_avg = df_daily.groupby("year", as_index=False)["rate"].mean() \
        .rename(columns={"rate": "rate_usd_to_eur_avg"}) \
        .sort_values("year")

    return df_avg