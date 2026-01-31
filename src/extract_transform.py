#1. Imports
import requests
import pandas as pd
import time
from pathlib import Path
from src.utils import compute_kpis
from functools import reduce

#2. Configuração geral
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)

BASE = "https://api.worldbank.org/v2"
INDICATORS = {
    "population": "SP.POP.TOTL",
    "gdp_per_capita_usd": "NY.GDP.PCAP.CD",
    "inflation_pct": "FP.CPI.TOTL.ZG"
}

#Lista de países ISO3 a processar/considerar
COUNTRIES = ["PRT"] 

#3. Funções de extração dos dados
#Extrai todos os dados disponíveis para um indicador e país, tratando a paginação da API do World Bank
def fetch_indicator(country_iso3, indicator_code): 
    url = f"{BASE}/country/{country_iso3}/indicator/{indicator_code}"
    params = {"format": "json", "per_page": 50}
    #Pedido HTTP à API
    r = requests.get(url, params=params) 
    r.raise_for_status()
    #Leitura do JSON
    payload = r.json()
    if not isinstance(payload, list) or len(payload) < 2:
        return []
    meta, data = payload[0], payload[1]
    total_pages = int(meta.get("pages", 1))
    results = data.copy()
    for page in range(2, total_pages + 1):
        params["page"] = page
        r = requests.get(url, params=params)
        r.raise_for_status()
        page_payload = r.json()
        results.extend(page_payload[1])
        time.sleep(0.05)
    return results

#Converte a lista JSON devolvida pela API num df pandas mantendo apenas os campos relevantes
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


#4. Função principal de processamento
#Extrai todos os indicadores definidos para um país, faz o merge, aplica tratamentos e calcula KPIs
def build_country_csv(country_iso3):
    frames = []
    #Extração e criação de df por indicador
    for key, code in INDICATORS.items(): 
        raw = fetch_indicator(country_iso3, code)
        df = to_dataframe(raw, key)
        frames.append(df)

    if not frames:
        print(f"No data for {country_iso3}")
        return

    #Merge dos indicadores por país e ano
    merged = reduce(lambda left, right: pd.merge(left, right, on=["country", "countryiso3code", "year"], how="outer"), frames)

    #Conversão de tipos para numérico
    merged["population"] = pd.to_numeric(merged.get("population"), errors="coerce")
    merged["gdp_per_capita_usd"] = pd.to_numeric(merged.get("gdp_per_capita_usd"), errors="coerce")
    merged["inflation_pct"] = pd.to_numeric(merged.get("inflation_pct"), errors="coerce")

    #Remoção de valores nulos
    merged = merged.dropna(subset=["population", "gdp_per_capita_usd", "inflation_pct"], how="all")

    #Ordenação cronológica
    merged = merged.sort_values("year").reset_index(drop=True)
    #Cálculo de KPIs
    merged = compute_kpis(merged)
    #Escrita do CSV
    out_path = DATA_DIR / f"{country_iso3}_combined.csv"
    merged.to_csv(out_path, index=False)

    #Diagnóstico simples de cobertura temporal por indicador
    for col in ["population", "gdp_per_capita_usd", "inflation_pct"]:
        if col in merged.columns:
            yrs = merged.loc[merged[col].notna(), "year"].astype(int).tolist()
            if yrs:
                print(f"{country_iso3} - {col}: {min(yrs)} até {max(yrs)} ({len(yrs)} obs)")
            else:
                print(f"{country_iso3} - {col}: NO DATA")
    print(f"Saved {out_path} ({len(merged)} rows)")


#5. Ponto de entrada do script: processa todos os países definidos em COUNTRIES
def main():
    for c in COUNTRIES:
        build_country_csv(c)

if __name__ == "__main__":
    main()