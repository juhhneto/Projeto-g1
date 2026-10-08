"""
Projeto G1 - Mobilidade Urbana no Brasil
Disciplina: Linguagens de Programação - Análise e Visualização de Dados com Python
Aluna: Juliana Neto Sá | Professor: Alexandre Neves Louzada
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from sqlalchemy import create_engine, text

import utils as U

st.set_page_config(page_title="Mobilidade Urbana no Brasil", page_icon="🚌", layout="wide")
sns.set_theme(style="whitegrid")


@st.cache_data(show_spinner="Carregando dados...")
def carregar(arquivo=None):
    return U.ler_csv(arquivo) if arquivo is not None else U.carregar_base()


@st.cache_data(ttl=3600, show_spinner=False)
def estados_ibge():
    return U.ibge_estados()


def mostrar(fig):
    st.pyplot(fig)
    plt.close(fig)


def classificar_r(r):
    a = abs(r)
    forca = "praticamente nula" if a < 0.1 else "fraca" if a < 0.3 else "moderada" if a < 0.6 else "forte"
    return f"{forca} ({'positiva' if r > 0 else 'negativa'})"


def br(x, d=1):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ================================================================ cabeçalho
st.title("🚌 Mobilidade Urbana no Brasil")
st.caption("**Aluna:** Juliana Neto Sá  |  **Professor:** Alexandre Neves Louzada  |  "
           "**Disciplina:** Linguagens de Programação — Análise e Visualização de Dados com Python (G1)")
st.markdown("""
### Descrição do problema
O deslocamento diário nas cidades brasileiras envolve tempo perdido, custo da tarifa, lotação e emissões de CO₂.
Este dashboard analisa uma base **simulada** com **37 cidades, 20 UFs e 6 meios de transporte (2015–2024)** para
responder: *quais meios, regiões e períodos apresentam piores indicadores de mobilidade e como as variáveis se relacionam?*
""")

# ================================================================ dados + filtros
st.sidebar.header("⚙️ Dados e filtros")
up = st.sidebar.file_uploader("Enviar outro CSV (mesmo formato)", type="csv")
try:
    bruto = carregar(up)
except Exception as e:
    st.error(f"Não foi possível carregar os dados: {e}")
    st.stop()
bruto.columns = [c.replace("\ufeff", "").strip() for c in bruto.columns]
faltando = U.validar(bruto)
if faltando:
    st.error(f"O CSV não tem as colunas esperadas: {', '.join(faltando)}")
    st.stop()
df = U.preparar(bruto)

regioes = st.sidebar.multiselect("Região", sorted(df["regiao"].unique()), default=sorted(df["regiao"].unique()))
ufs_op = sorted(df[df["regiao"].isin(regioes)]["uf"].unique())
ufs = st.sidebar.multiselect("UF", ufs_op, default=ufs_op)
meios = st.sidebar.multiselect("Meio de transporte", sorted(df["meio_transporte"].unique()),
                               default=sorted(df["meio_transporte"].unique()))
niveis = st.sidebar.multiselect("Nível de congestionamento", U.ORDEM, default=U.ORDEM)
a0, a1 = int(df["ano"].min()), int(df["ano"].max())
anos = st.sidebar.slider("Ano", a0, a1, (a0, a1))
metrica = st.sidebar.selectbox("Métrica principal", list(U.NUMS), format_func=U.NUMS.get, index=1)

f = df[df["regiao"].isin(regioes) & df["uf"].isin(ufs) & df["meio_transporte"].isin(meios)
       & df["nivel_congestionamento"].isin(niveis) & df["ano"].between(*anos)]
if f.empty:
    st.warning("Nenhum registro com os filtros atuais. Ajuste a barra lateral.")
    st.stop()
rot = U.NUMS[metrica]

# ================================================================ KPIs
st.subheader("📊 KPIs")
k = st.columns(6)
k[0].metric("Registros", br(len(f), 0))
k[1].metric("Passageiros (milhões)", br(f["passageiros"].sum() / 1e6, 1))
k[2].metric("Tempo médio (min)", br(f["tempo_medio_deslocamento"].mean()))
k[3].metric("Velocidade média (km/h)", br(f["velocidade_media"].mean()))
k[4].metric("Tarifa média (R$)", br(f["tarifa_media"].mean(), 2))
k[5].metric("% Alto/Crítico", f"{f['congestionado'].mean() * 100:.1f}%")

abas = st.tabs(["📋 Tabelas", "⚖️ Comparativos", "🕒 Temporal", "🚦 Congestionamento",
                "🔗 Correlação", "🗄️ API e Banco", "✅ Conclusão"])

# ---------------------------------------------------------------- tabelas
with abas[0]:
    st.markdown("**Dados filtrados (200 primeiras linhas)**")
    st.dataframe(f.head(200), use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Estatísticas descritivas**")
        st.dataframe(f[list(U.NUMS)].rename(columns=U.NUMS).describe().T.round(2), use_container_width=True)
    with c2:
        st.markdown("**Resumo por meio de transporte**")
        res = f.groupby("meio_transporte").agg(registros=("ano", "size"),
                                               passageiros_milhoes=("passageiros", lambda s: s.sum() / 1e6),
                                               tempo_medio=("tempo_medio_deslocamento", "mean"),
                                               velocidade=("velocidade_media", "mean"),
                                               tarifa=("tarifa_media", "mean")).round(2)
        st.dataframe(res, use_container_width=True)
    st.download_button("⬇️ Baixar dados filtrados (CSV)", f.to_csv(index=False).encode("utf-8"),
                       "mobilidade_filtrado.csv", "text/csv")

# ---------------------------------------------------------------- comparativos
with abas[1]:
    dim = st.selectbox("Comparar por", ["meio_transporte", "regiao", "uf", "cidade"],
                       format_func=lambda x: x.replace("_", " ").title())
    g = f.groupby(dim)[metrica].mean().sort_values(ascending=False)
    gp = g.head(15)
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        sns.barplot(x=gp.values, y=gp.index.astype(str), ax=ax, color="#2a9d8f")
        ax.set_title(f"Média de {rot} por {dim.replace('_', ' ')}")
        ax.set_xlabel(rot); ax.set_ylabel("")
        mostrar(fig)
    with c2:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        ordem = list(gp.index[:10])
        sns.boxplot(data=f[f[dim].isin(ordem)], y=dim, x=metrica, order=ordem, ax=ax, color="#8ecae6")
        ax.set_title(f"Distribuição de {rot}")
        ax.set_xlabel(rot); ax.set_ylabel("")
        mostrar(fig)
    dif = (g.iloc[0] / g.iloc[-1] - 1) * 100 if g.iloc[-1] else np.nan
    st.info(f"**Interpretação:** a maior média de {rot} está em **{g.index[0]}** ({br(g.iloc[0], 2)}) e a menor em "
            f"**{g.index[-1]}** ({br(g.iloc[-1], 2)}), diferença de {br(dif)}%. "
            + ("Como a diferença é pequena e as caixas se sobrepõem, não há evidência de que o grupo seja "
               "realmente diferente (efeito esperado em dados simulados)." if abs(dif) < 10 else
               "A diferença é relevante e merece investigação."))

# ---------------------------------------------------------------- temporal
with abas[2]:
    agrup = st.radio("Separar por", ["Total", "meio_transporte", "regiao"], horizontal=True,
                     format_func=lambda x: x if x == "Total" else x.replace("_", " ").title())
    f2 = f.assign(periodo=f["data"].dt.to_period("M").dt.to_timestamp())
    fig, ax = plt.subplots(figsize=(11, 4))
    if agrup == "Total":
        s = f2.groupby("periodo")[metrica].mean()
        ax.plot(s.index, s.values, color="#e76f51", alpha=.5, label="Média mensal")
        ax.plot(s.index, s.rolling(12, min_periods=3).mean(), color="#264653", lw=2.5, label="Média móvel 12m")
        ax.legend()
    else:
        s = f2.groupby(["periodo", agrup])[metrica].mean().unstack().rolling(12, min_periods=3).mean()
        s.plot(ax=ax)
        ax.legend(title=f"{agrup.replace('_', ' ')} (média móvel 12m)", ncol=3, fontsize=8)
    ax.set_title(f"Evolução mensal — {rot}"); ax.set_xlabel(""); ax.set_ylabel(rot)
    mostrar(fig)
    c1, c2 = st.columns(2)
    with c1:
        anual = f.groupby("ano")[metrica].mean()
        fig, ax = plt.subplots(figsize=(6, 3.8))
        sns.barplot(x=anual.index, y=anual.values, ax=ax, color="#2a9d8f")
        ax.set_title(f"Média anual — {rot}"); ax.set_xlabel("")
        lo, hi = anual.min(), anual.max()
        ax.set_ylim(lo - (hi - lo) * .5, hi + (hi - lo) * .2)
        mostrar(fig)
    with c2:
        pv = f.pivot_table(index="ano", columns="mes", values=metrica, aggfunc="mean")
        fig, ax = plt.subplots(figsize=(6, 3.8))
        sns.heatmap(pv, cmap="YlOrRd", ax=ax, cbar_kws={"label": rot})
        ax.set_title("Sazonalidade (ano x mês)")
        mostrar(fig)
    pico, vale = anual.idxmax(), anual.idxmin()
    var = (anual.iloc[-1] / anual.iloc[0] - 1) * 100 if len(anual) > 1 else 0
    st.info(f"**Interpretação:** o ano com maior média de {rot} foi **{pico}** ({br(anual.max(), 2)}) e o menor "
            f"**{vale}** ({br(anual.min(), 2)}). Do primeiro ao último ano filtrado a variação foi de "
            f"{br(var)}%. O heatmap permite procurar meses recorrentemente mais altos (sazonalidade).")

# ---------------------------------------------------------------- congestionamento
with abas[3]:
    base = st.selectbox("Analisar por", ["meio_transporte", "regiao"],
                        format_func=lambda x: x.replace("_", " ").title(), key="cong")
    ct = pd.crosstab(f[base], f["nivel_congestionamento"], normalize="index")[
        [n for n in U.ORDEM if n in f["nivel_congestionamento"].unique()]] * 100
    fig, ax = plt.subplots(figsize=(10, 4))
    ct.plot(kind="barh", stacked=True, ax=ax, color=["#90be6d", "#f9c74f", "#f8961e", "#d62828"][:ct.shape[1]])
    ax.set_xlabel("% dos registros"); ax.set_ylabel(""); ax.set_title("Níveis de congestionamento (100%)")
    ax.legend(title="Nível", bbox_to_anchor=(1.01, 1), loc="upper left")
    mostrar(fig)
    pc = f.groupby(base)["congestionado"].mean().sort_values(ascending=False) * 100
    st.info(f"**Interpretação:** **{pc.index[0]}** tem a maior proporção de registros em nível Alto/Crítico "
            f"({br(pc.iloc[0])}%), e **{pc.index[-1]}** a menor ({br(pc.iloc[-1])}%). Os níveis estão bem "
            f"distribuídos entre os grupos, sem um meio claramente 'imune' ao congestionamento.")

# ---------------------------------------------------------------- correlação
with abas[4]:
    cols = list(U.NUMS) + ["indice_congestionamento", "emissao_por_mil_passageiros"]
    corr = f[cols].corr()
    fig, ax = plt.subplots(figsize=(9, 6.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, vmin=-1, vmax=1, ax=ax)
    ax.set_title("Matriz de correlação (Pearson)")
    mostrar(fig)
    c1, c2 = st.columns(2)
    x = c1.selectbox("Eixo X", list(U.NUMS), format_func=U.NUMS.get, index=3)
    y = c2.selectbox("Eixo Y", list(U.NUMS), format_func=U.NUMS.get, index=1)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.regplot(data=f.sample(min(1500, len(f)), random_state=1), x=x, y=y, ax=ax,
                scatter_kws={"alpha": .35, "s": 14}, line_kws={"color": "#d62828"})
    ax.set_xlabel(U.NUMS[x]); ax.set_ylabel(U.NUMS[y])
    mostrar(fig)
    r = f[x].corr(f[y])
    st.info(f"**Interpretação:** entre *{U.NUMS[x]}* e *{U.NUMS[y]}* a correlação é **{r:.2f}**, "
            f"{classificar_r(r)}. Correlação não implica causalidade; em bases simuladas com valores "
            f"gerados de forma independente, é comum que todas fiquem próximas de zero.")

# ---------------------------------------------------------------- API e banco
with abas[5]:
    st.markdown("### 🌐 Consumo de API — IBGE (localidades)")
    if st.button("Consultar API do IBGE"):
        try:
            est = estados_ibge()
            rank = (f.groupby("uf").agg(registros=("ano", "size"),
                                        passageiros_milhoes=("passageiros", lambda s: s.sum() / 1e6),
                                        tempo_medio=(  "tempo_medio_deslocamento", "mean")).round(2)
                    .reset_index().merge(est, on="uf", how="left"))
            st.success(f"{len(est)} estados recebidos da API e integrados à base por UF.")
            st.dataframe(rank.sort_values("passageiros_milhoes", ascending=False), use_container_width=True)
        except Exception as e:
            st.warning(f"API do IBGE indisponível no momento: {e}")
    st.markdown("### 🗄️ Banco de dados (SQLAlchemy + SQLite)")
    st.caption("Modelo relacional: dimensão `localidades` (cidade, UF, região) → fato `mobilidade` (por `localidade_id`).")
    eng = create_engine(f"sqlite:///{U.DB_PATH}")
    if st.button("💾 Gravar base tratada no SQLite"):
        U.DB_PATH.parent.mkdir(exist_ok=True)
        nl, nf = U.salvar_banco(df, eng)
        st.success(f"Gravadas {nl} localidades e {nf} registros em database/mobilidade.db")
    nome = st.selectbox("Consulta SQL", list(U.CONSULTAS))
    st.code(U.CONSULTAS[nome].strip(), language="sql")
    if st.button("▶️ Executar consulta"):
        try:
            st.dataframe(pd.read_sql(text(U.CONSULTAS[nome]), eng), use_container_width=True)
        except Exception:
            st.warning("Banco ainda não criado. Clique em 'Gravar base tratada no SQLite' primeiro.")

# ---------------------------------------------------------------- conclusão
with abas[6]:
    st.markdown("### Conclusão executiva")
    mt = f.groupby("meio_transporte")["tempo_medio_deslocamento"].mean().sort_values()
    rg = f.groupby("regiao")["tempo_medio_deslocamento"].mean().sort_values()
    pr = f.groupby("meio_transporte")["passageiros"].sum().sort_values(ascending=False)
    cm = f[cols].corr().where(~np.eye(len(cols), dtype=bool)).abs().stack().sort_values(ascending=False)
    (v1, v2), rmax = cm.index[0], cm.iloc[0]
    st.markdown(f"""
- **Escala:** {br(len(f), 0)} registros, {br(f['passageiros'].sum() / 1e6)} milhões de passageiros, tempo médio de deslocamento de **{br(f['tempo_medio_deslocamento'].mean())} min**.
- **Meios de transporte:** menor tempo médio em **{mt.index[0]}** ({br(mt.iloc[0])} min) e maior em **{mt.index[-1]}** ({br(mt.iloc[-1])} min); mais passageiros em **{pr.index[0]}**.
- **Regiões:** deslocamento mais demorado no **{rg.index[-1]}** ({br(rg.iloc[-1])} min) e mais rápido no **{rg.index[0]}** ({br(rg.iloc[0])} min).
- **Congestionamento:** **{f['congestionado'].mean() * 100:.1f}%** dos registros estão em nível Alto ou Crítico.
- **Relações:** a maior correlação entre variáveis é de **{rmax:.2f}** (*{v1}* × *{v2}*), ou seja, {classificar_r(rmax)}.
- **Recomendação:** as diferenças entre grupos são pequenas; antes de decisões de política pública seria necessário validar com dados reais e investigar fatores não presentes na base (renda, infraestrutura, população).
- **Limitação:** os dados são simulados, portanto os resultados têm finalidade didática.
""")
