#1. Imports
import requests
import pandas as pd
import numpy as np
import time
import datetime
from pathlib import Path
from src.utils import compute_kpis, build_rates_df
from functools import reduce
# Melhorias para performance/robustez
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

#2. Configuração geral
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)

BASE = "https://api.worldbank.org/v2"
INDICATORS = {
    "population": "SP.POP.TOTL",
    "gdp_per_capita_usd": "NY.GDP.PCAP.CD",
    "inflation_pct": "FP.CPI.TOTL.ZG"
}

# Lista de países a processar/considerar
COUNTRIES = ["PRT", "ESP", "FRA", "ITA", "DEU", "BEL", "NLD", "DNK", "SWE", "NOR", "FIN", "AUT", "GBR", "IRL", "GRC", "CHE", "LUX", "ISL"]

# Sessão global com retries (reuso de conexões + backoff)
def make_session(total_retries=3, backoff_factor=0.3, status_forcelist=(429, 500, 502, 503, 504)):
    #Cria uma requests.Session com retry/backoff para maior robustez e reuso de conexões

    s = requests.Session()
    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(['GET', 'POST'])
    )
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

SESSION = make_session()

#3. Funções de extração dos dados
#Extrai todos os dados disponíveis para um indicador e país, tratando a paginação da API do World Bank
def fetch_indicator(country_iso3, indicator_code, per_page=1000, timeout=10, pause=0.05):

    #per_page aumentado para reduzir número de requests
    #timeout definido para evitar bloqueios indefinidos
    #pausa entre páginas

    url = f"{BASE}/country/{country_iso3}/indicator/{indicator_code}"
    params = {"format": "json", "per_page": per_page, "page": 1}

    try:
        r = SESSION.get(url, params=params, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Request inicial falhou para {indicator_code} {country_iso3}: {e}")
        return []

    payload = r.json()
    if not isinstance(payload, list) or len(payload) < 2:
        print(f"[WARN] Payload inesperado para {indicator_code} {country_iso3}")
        return []
    meta, data = payload[0], payload[1]
    total_pages = int(meta.get("pages", 1))
    results = list(data)

    if total_pages > 1:
        print(f"  -> {indicator_code} {country_iso3}: {total_pages} pages (per_page={per_page})")

    for page in range(2, total_pages + 1):
        params["page"] = page
        try:
            r = SESSION.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            page_payload = r.json()
            if isinstance(page_payload, list) and len(page_payload) >= 2 and isinstance(page_payload[1], list):
                results.extend(page_payload[1])
            else:
                print(f"[WARN] Página {page} com formato inesperado para {indicator_code} {country_iso3}")
                break
        except Exception as e:
            print(f"[ERROR] Falha na página {page} para {indicator_code} {country_iso3}: {e}")
            break
        time.sleep(pause)
    return results

# Converte a lista JSON devolvida pela API num df pandas mantendo apenas os campos relevantes
def to_dataframe(raw_list, indicator_name):
    rows = []
    for item in raw_list:
        try:
            year = int(item.get("date"))
        except Exception:
            continue
        rows.append({
            "country": item.get("country", {}).get("value"),
            "countryiso3code": item.get("countryiso3code"),
            "year": year,
            indicator_name: item.get("value")
        })
    #Criação de df com a informação bruta extraída
    df = pd.DataFrame(rows)
    df = df.sort_values("year").reset_index(drop=True)
    return df


#4. Função principal de processamento (agora devolve df, sem aplicar KPIs)
#Extrai todos os indicadores definidos para um país, faz o merge e aplica tratamentos
def build_country_dataframe(country_iso3):
    frames = []
    #Extração e criação de df por indicador
    for key, code in INDICATORS.items():
        raw = fetch_indicator(country_iso3, code)
        df = to_dataframe(raw, key)
        frames.append(df)

    if not frames:
        print(f"No data for {country_iso3}")
        return None

    #Merge dos indicadores por país e ano (outer)
    merged = reduce(
        lambda left, right: pd.merge(left, right, on=["country", "countryiso3code", "year"], how="outer"),
        frames
    )

    #Conversão de tipos para numérico
    merged["population"] = pd.to_numeric(merged.get("population"), errors="coerce")
    merged["gdp_per_capita_usd"] = pd.to_numeric(merged.get("gdp_per_capita_usd"), errors="coerce")
    merged["inflation_pct"] = pd.to_numeric(merged.get("inflation_pct"), errors="coerce")

    #Remoção de linhas onde TODOS os indicadores são nulos (mantém anos com pelo menos 1 indicador)
    merged = merged.dropna(subset=["population", "gdp_per_capita_usd", "inflation_pct"], how="all")

    #Ordenação cronológica
    merged = merged.sort_values("year").reset_index(drop=True)

    #Diagnóstico simples de cobertura temporal por indicador
    for col in ["population", "gdp_per_capita_usd", "inflation_pct"]:
        if col in merged.columns:
            yrs = merged.loc[merged[col].notna(), "year"].astype(int).tolist()
            if yrs:
                print(f"{country_iso3} - {col}: {min(yrs)} até {max(yrs)} ({len(yrs)} obs)")
            else:
                print(f"{country_iso3} - {col}: NO DATA")

    # Retornar dataframe (sem calcular KPIs aqui; será feito no DataFrame concatenado)
    return merged


#5. Ponto de entrada do script: processa todos os países e escreve um único CSV
def main():

    all_dfs = []

    max_workers = min(4, len(COUNTRIES))
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(build_country_dataframe, c): c for c in COUNTRIES}
        for fut in as_completed(futures):
            c = futures[fut]
            try:
                df_country = fut.result()
            except Exception as e:
                print(f"[ERROR] {c} falhou: {e}")
                df_country = None
            if df_country is not None and not df_country.empty:
                all_dfs.append(df_country)
            else:
                print(f"  -> no data for {c} or empty, skipping")

    if not all_dfs:
        print("No data collected for any country.")
        return

    # Concatenar todos os países num único DataFrame
    final_df = pd.concat(all_dfs, ignore_index=True, sort=False)

    # Garantir ordenação por país e ano antes de calcular KPIs
    final_df = final_df.sort_values(["country", "year"]).reset_index(drop=True)

    # Aplicar KPIs (compute_kpis já faz groupby("country") internamente)
    final_df = compute_kpis(final_df)

    n_years = datetime.datetime.now().year - min(final_df['year']) + 1
    rates_df = build_rates_df(last_n_years = n_years)

    # Merge com a rate USD/EUR por ano usando o ano mais próximo se ano exato não existir
    if rates_df is None or rates_df.empty:
        print("[WARN] rates_df vazio; nenhuma taxa será adicionada ao final_df.")
        final_df["rate_usd_to_eur_avg"] = pd.NA
    else:
        # garantir tipos de dados
        rates_df = rates_df.drop_duplicates(subset=["year"]).copy()
        rates_df["year"] = rates_df["year"].astype(int)
        rates_df = rates_df.sort_values("year").reset_index(drop=True)

        rates_map = dict(zip(rates_df["year"].tolist(), rates_df["rate_usd_to_eur_avg"].tolist()))

        # Array de anos disponíveis para pesquisa do ano mais próximo
        available_years = np.array(sorted(rates_map.keys()), dtype=int)
        available_rates = np.array([rates_map[y] for y in available_years], dtype=float)

        # Função para obter a rate (exata ou mais próxima)
        def get_nearest_rate(year):
            try:
                y = int(year)
            except Exception:
                return np.nan
            if y in rates_map: # valor exato
                return float(rates_map[y])
            if available_years.size == 0: 
                return np.nan
            idx = (np.abs(available_years - y)).argmin()  # ano mais proximo
            return float(available_rates[idx])

        final_df["rate_usd_to_eur_avg"] = final_df["year"].apply(get_nearest_rate)

        final_df["gdp_per_capita_eur"] = final_df["gdp_per_capita_usd"] * final_df["rate_usd_to_eur_avg"]
        final_df["gdp_total_eur"] = final_df["gdp_total_usd"] * final_df["rate_usd_to_eur_avg"]
        final_df["gdp_pc_abs_change_eur"] = final_df["gdp_pc_abs_change_usd"] * final_df["rate_usd_to_eur_avg"]

    # Escrever um único ficheiro com todos os países
    out_path = DATA_DIR / "all_countries.csv"
    final_df.to_csv(out_path, index=False)
    print(f"Saved {out_path} ({len(final_df)} rows total)")


if __name__ == "__main__":
    main()