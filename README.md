1. Descrição do Projeto

Este projeto tem como objetivo demonstrar competências técnicas em análise de dados através do desenvolvimento end-to-end de um pequeno projeto de dados, incluindo:
    - extração de dados a partir de uma API pública;
    - tratamento e transformação dos dados;
    - criação de indicadores e métricas relevantes;
    - disponibilização dos dados finais para análise e visualização em Power BI.

Os dados utilizados são provenientes da API do World Bank e dizem respeito a indicadores macroeconómicos e demográficos de Portugal.


2. Fonte de Dados (API)

Os dados são obtidos através da World Bank API:
Base URL: https://api.worldbank.org/v2

População total: https://api.worldbank.org/v2/country/PRT/indicator/SP.POP.TOTL
PIB per capita (USD): https://api.worldbank.org/v2/country/PRT/indicator/NY.GDP.PCAP.CD
Inflação (variação anual %): https://api.worldbank.org/v2/country/PRT/indicator/FP.CPI.TOTL.ZG

A API devolve dados em formato JSON, que são processados em Python.


3. Indicadores Utilizados

Os seguintes indicadores do World Bank foram selecionados:
    - População total:                   SP.POP.TOTL
    - PIB per capita (USD correntes):    NY.GDP.PCAP.CD
    - Taxa de inflação anual (%):        FP.CPI.TOTL.ZG

A inflação foi incluída como indicador adicional por apresentar elevada cobertura temporal e atualização recente, permitindo complementar a análise económica.


4. Tratamento de Dados

O tratamento de dados é realizado em Python e inclui:
    - Conversão de tipos para valores numéricos (pd.to_numeric);
    - Remoção de linhas vazias, mantendo apenas anos com pelo menos um indicador relevante;
    - Ordenação cronológica dos dados por ano;
    - Diagnóstico de cobertura temporal, imprimindo no terminal o primeiro e último ano disponível por indicador;

Esta abordagem garante consistência temporal e transparência quanto à qualidade dos dados utilizados.


5. Métricas e KPIs Criados

    5.1. KPIs sugeridos
        População:
        - Variação absoluta anual (pop_abs_change)
        - Variação percentual anual (pop_pct_change)
        - Crescimento médio dos últimos 25 anos (pop_cagr_25y)
    
        PIB per capita:
        - Variação absoluta anual (gdp_pc_abs_change_usd)
        - Variação percentual anual (gdp_pc_pct_change)
        - Crescimento médio dos últimos 25 anos (gdp_pc_cagr_25y)
            O crescimento médio dos últimos 25 anos é calculado através da taxa de crescimento anual composta (CAGR), utilizando os últimos 25 anos disponíveis e considerando 24 períodos de crescimento.

    5.2. KPIs adicionais
        Inflação:
        - Média móvel de 5 anos da inflação (inflation_ma_5y)
            Permite analisar a tendência de médio prazo, reduzindo a volatilidade anual.
        - Inflação acumulada em 5 anos (inflation_cum_5y)
            Mede o impacto acumulado da inflação ao longo de um período de cinco anos, utilizando crescimento composto.


6. Estrutura do Projeto
fcporto_data_analyst_project/
├─ src/
│  ├─ dashboard.pbix           [Dashboard Power BI]
│  ├─ extract_transform.py     [Extração e tratamento dos dados]
│  └─ utils.py                 [Funções de cálculo de KPIs]
├─ data/
│  └─ PRT_combined.csv         [Output final]
├─ requirements.txt            [Bibliotecas essenciais para execução do projeto]
└─ README.md                   [Documentação do projeto]

O código está devidamente comentado para facilitar a leitura e manutenção.


7. Instruções de Execução
    7.1. Requisitos
        - Python 3.8 ou superior
        - Instalar dependências: pip install -r requirements.txt

    7.2. Execução do script
        A partir da pasta raiz do projeto (fcporto_data_analyst_project): python -m src.extract_transform
        Este comando irá extrair os dados da API, aplicar os tratamentos e cálculos, gerar o ficheiro data/PRT_combined.csv, que é utilizado como fonte de dados no dashboard Power BI.


8. Utilização dos Resultados
    O ficheiro PRT_combined.csv foi importado diretamente no Power BI, permitindo:
    - criação de um dashboard interativo;
    - análise temporal dos indicadores;
    - visualização dos KPIs calculados.
