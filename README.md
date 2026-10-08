# Mobilidade Urbana no Brasil — Análise e Visualização de Dados com Python

**Disciplina:** Linguagens de Programação — Análise e Visualização de Dados com Python (Avaliação G1)  
**Aluna:** Juliana Neto Sá  
**Professor:** Alexandre Neves Louzada  

## Problema
Analisar uma base simulada de mobilidade urbana no Brasil para identificar padrões, comparar grupos e relacionar variáveis, gerando KPIs e visualizações que apoiem decisões sobre transporte.

## Base de dados
`simulacao_mobilidade_urbana_brasil.csv` — repositório [AlexandreLouzada/Dados-Simulados-G2](https://github.com/AlexandreLouzada/Dados-Simulados-G2/tree/main/datasets_g2_30_temas). Dados simulados, uso didático.

4.440 registros mensais (2015–2024), 5 regiões, 20 UFs, 37 cidades e 6 meios de transporte (Ônibus, BRT, Metrô, Trem, VLT, Bicicleta).
Colunas: `ano, mes, data, regiao, uf, cidade, meio_transporte, passageiros, tempo_medio_deslocamento, lotacao_media, velocidade_media, emissao_co2, tarifa_media, nivel_congestionamento`.

## Tecnologias
Python · Pandas · NumPy · Matplotlib · Seaborn · Streamlit · SQLAlchemy + SQLite · Requests (API IBGE) · GitHub

## Funcionalidades
- **Intermediárias:** filtros múltiplos, KPIs dinâmicos, dashboard em seções (abas), visualizações comparativas, análise temporal, upload de arquivos
- **Avançadas:** consumo de API (IBGE), persistência em SQLite com SQLAlchemy, modelagem relacional (`localidades` + `mobilidade`), séries temporais (média móvel e sazonalidade), correlação estatística (Pandas/NumPy)

## Estrutura
```
projeto-g1/
├── app.py            # dashboard Streamlit
├── utils.py          # carga, limpeza, API IBGE e banco SQLite
├── requirements.txt
├── README.md
├── index.html        # página do projeto (GitHub Pages)
├── dados/            # CSV (baixado automaticamente na 1ª execução)
├── database/         # mobilidade.db (SQLite)
├── notebooks/        # analise_mobilidade.ipynb
└── imagens/          # prints do dashboard
```

## Como executar
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Links
- Repositório: https://github.com/SEU-USUARIO/projeto-g1
- Página (GitHub Pages): https://SEU-USUARIO.github.io/projeto-g1/
- Dashboard (Streamlit): https://SEU-APP.streamlit.app
