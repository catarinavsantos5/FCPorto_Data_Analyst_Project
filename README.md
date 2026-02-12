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


9. Melhorias ao Projeto
    9.1. Expansão do dataset e processamento
    Após a versão inicial focada exclusivamente em Portugal, o projeto foi expandido de forma a enriquecer e aprofundar a análise.
    As principais melhorias introduzidas foram:

        9.1.1. Inclusão de múltiplos países europeus
        Para além de Portugal, passaram a ser considerados vários países europeus (ex.: Alemanha, França, Espanha, Itália, Países Nórdicos, entre outros), permitindo análise comparativa entre economias; identificação de líderes por indicador; exploração de disparidades regionais.
        O dataset final passou a ser consolidado num único ficheiro (all_countries.csv), contendo todos os países analisados.

        9.1.2. Introdução do PIB Total
        Para complementar o PIB per capita, foi acrescentado o cálculo do PIB total, através da multiplicação da população pelo PIB per capita.
        Isto permite distinguir: dimensão absoluta da economia (PIB total); nível médio de riqueza por habitante (PIB per capita).

        9.1.3. Conversão anual de USD para EUR
        Foi integrada uma API externa para obtenção das taxas de câmbio USD → EUR, permitindo:
        - Conversão do PIB total para EUR (gdp_total_eur);
        - Conversão do PIB per capita para EUR (gdp_per_capita_eur);
        - Cálculo da variação absoluta anual do PIB per capita também em EUR (gdp_pc_abs_change_eur).
        A taxa utilizada corresponde à média anual da taxa diária USD/EUR.
        Para anos em que não exista taxa disponível, é utilizada a taxa do ano mais próximo disponível, garantindo continuidade temporal e consistência no dataset.

    9.2. Melhorias no Dashboard
    O dashboard foi também melhorado/expandido face à versão inicial.

        9.2.1. Seleção de moeda (EUR / USD) e país
        Foi introduzida a possibilidade de alternar entre valores em USD e EUR, o que permite maior flexibilidade analítica e adaptação a diferentes contextos de análise.
        Foi igualmente acrescentado um filtro do país, permitindo análises dinâmicas sobre diferentes geografias.

        9.2.2. Alteração de um dos KPIs principais (nos cards, página 1)
        Nos cartões principais foi substituído o indicador "PIB per capita (último ano)" por PIB Total (último ano). Esta alteração permite destacar a dimensão económica absoluta do país selecionado, complementando o foco relativo já presente nos gráficos abaixo.

        9.2.3. Nova página - Análise Comparativa Europeia
        Foi acrescentada uma página dedicada à análise comparativa entre países europeus, incluindo:
        - Ranking anual do país com maior população, PIB total, PIB per capita e inflação (identificação de líderes por indicador nos últimos anos);
        - Heat map geográfico do PIB per capita na Europa (visualização espacial das disparidades económicas regionais).
        Estas análises acrescentam:
        - Dimensão comparativa ao projeto;
        - Contextualização internacional;
        - Capacidade de identificar padrões estruturais (ex.: países com maior produtividade vs maior dimensão económica).

    9.3. Justificação do foco no PIB per capita no dashboard
    Embora o PIB total seja um indicador relevante da dimensão económica de um país, este tende a ser fortemente influenciado pelo tamanho populacional. Por esse motivo, o PIB per capita é frequentemente considerado uma métrica mais adequada para avaliar o nível médio de riqueza, comparar economias de diferentes dimensões.
    A predominância da análise baseada em PIB per capita permite comparações mais equilibradas e evita enviesamentos decorrentes da dimensão demográfica.
    O PIB total é utilizado como complemento, mas não como principal indicador comparativo.