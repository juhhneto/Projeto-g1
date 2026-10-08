"""
Projeto G1 - Mobilidade Urbana no Brasil
Disciplina: Linguagens de Programação - Análise e Visualização de Dados com Python
Aluna: Juliana Neto Sá | Professor: Alexandre Neves Louzada

Funções de apoio: carga, limpeza, engenharia de atributos, API do IBGE e banco SQLite.
"""
from pathlib import Path

import pandas as pd
import requests

URL = ("https://raw.githubusercontent.com/AlexandreLouzada/Dados-Simulados-G2/main/"
       "datasets_g2_30_temas/simulacao_mobilidade_urbana_brasil.csv")
BASE = Path(__file__).parent
CSV_LOCAL = BASE / "dados" / "simulacao_mobilidade_urbana_brasil.csv"
DB_PATH = BASE / "database" / "mobilidade.db"
IBGE_API = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"

NUMS = {
    "passageiros": "Passageiros",
    "tempo_medio_deslocamento": "Tempo médio de deslocamento (min)",
    "lotacao_media": "Lotação média (%)",
    "velocidade_media": "Velocidade média (km/h)",
    "emissao_co2": "Emissão de CO₂",
    "tarifa_media": "Tarifa média (R$)",
}
CATS = ["regiao", "uf", "cidade", "meio_transporte", "nivel_congestionamento"]
ORDEM = ["Baixo", "Médio", "Alto", "Crítico"]
COLUNAS = ["ano", "mes", "data"] + CATS + list(NUMS)


def ler_csv(origem) -> pd.DataFrame:
    """Lê CSV (caminho, URL ou arquivo). utf-8-sig remove o BOM do início do arquivo."""
    return pd.read_csv(origem, encoding="utf-8-sig")


def carregar_base() -> pd.DataFrame:
    """Usa o CSV local; se não existir, baixa do GitHub e salva em dados/."""
    if CSV_LOCAL.exists():
        return ler_csv(CSV_LOCAL)
    df = ler_csv(URL)
    CSV_LOCAL.parent.mkdir(exist_ok=True)
    df.to_csv(CSV_LOCAL, index=False, encoding="utf-8")
    return df


def validar(df: pd.DataFrame) -> list:
    """Retorna as colunas obrigatórias que estão faltando."""
    return [c for c in COLUNAS if c not in df.columns]


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Limpeza e engenharia de atributos."""
    df = df.copy()
    df.columns = [c.replace("\ufeff", "").strip() for c in df.columns]
    df = df.drop_duplicates()
    for c in CATS:
        df[c] = df[c].astype(str).str.strip()
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    for c in NUMS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df[c] = df[c].fillna(df[c].median())
    df["nivel_congestionamento"] = pd.Categorical(df["nivel_congestionamento"],
                                                  categories=ORDEM, ordered=True)
    # atributos criados
    df["indice_congestionamento"] = df["nivel_congestionamento"].cat.codes + 1   # 1=Baixo ... 4=Crítico
    df["congestionado"] = df["indice_congestionamento"] >= 3                     # Alto ou Crítico
    df["emissao_por_mil_passageiros"] = df["emissao_co2"] / df["passageiros"] * 1000
    df["trimestre"] = df["data"].dt.quarter
    return df


def ibge_estados() -> pd.DataFrame:
    """Consome a API de localidades do IBGE: sigla, nome do estado e região."""
    r = requests.get(IBGE_API, timeout=15)
    r.raise_for_status()
    return pd.DataFrame([{"uf": e["sigla"], "estado": e["nome"], "regiao_ibge": e["regiao"]["nome"]}
                         for e in r.json()]).sort_values("uf")


def salvar_banco(df: pd.DataFrame, engine) -> tuple:
    """Modelo relacional: dimensão `localidades` + fato `mobilidade` (chave localidade_id)."""
    loc = df[["cidade", "uf", "regiao"]].drop_duplicates().reset_index(drop=True)
    loc["localidade_id"] = loc.index + 1
    fato = df.merge(loc, on=["cidade", "uf", "regiao"]).drop(columns=["cidade", "uf", "regiao"])
    fato["nivel_congestionamento"] = fato["nivel_congestionamento"].astype(str)
    fato["data"] = fato["data"].dt.strftime("%Y-%m-%d")
    loc.to_sql("localidades", engine, if_exists="replace", index=False)
    fato.to_sql("mobilidade", engine, if_exists="replace", index=False)
    return len(loc), len(fato)


CONSULTAS = {
    "Tempo médio e passageiros por região": """
        SELECT l.regiao, COUNT(*) AS registros,
               ROUND(AVG(m.tempo_medio_deslocamento), 1) AS tempo_medio_min,
               ROUND(SUM(m.passageiros) / 1000000.0, 1) AS passageiros_milhoes
        FROM mobilidade m JOIN localidades l ON l.localidade_id = m.localidade_id
        GROUP BY l.regiao ORDER BY tempo_medio_min DESC""",
    "Top 10 cidades por passageiros": """
        SELECT l.cidade, l.uf, ROUND(SUM(m.passageiros) / 1000000.0, 1) AS passageiros_milhoes
        FROM mobilidade m JOIN localidades l ON l.localidade_id = m.localidade_id
        GROUP BY l.cidade, l.uf ORDER BY passageiros_milhoes DESC LIMIT 10""",
    "Registros críticos por meio de transporte": """
        SELECT m.meio_transporte, COUNT(*) AS registros_criticos
        FROM mobilidade m WHERE m.nivel_congestionamento = 'Crítico'
        GROUP BY m.meio_transporte ORDER BY registros_criticos DESC""",
}
