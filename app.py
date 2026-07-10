import streamlit as st
import plotly.graph_objects as go
import requests

def brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Simulador de Metas", page_icon="🎯", layout="wide")

st.markdown("""
<style>
h1 {
    font-family: Georgia, serif !important;
    color: #7c1c12 !important;
    font-weight: bold !important;
}
h2, h3, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
    font-family: Georgia, serif !important;
    color: #7c1c12 !important;
    font-weight: normal !important;
}
[data-testid="stImage"] img {
    margin-top: 25px;
}
[data-testid="stMetric"] {
    background-color: #f3ead8;
    border: 1px solid #d94d26;
    border-radius: 10px;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)

SENHA_INTERNA = "ava2026"  # troca pela senha que quiser

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col_esq, col_centro, col_dir = st.columns([2, 1, 2])
    with col_centro:
        st.image("logo.svg", width=180)
    st.markdown("<h1 style='text-align: center;'>Simulador de Metas Financeiras</h1>", unsafe_allow_html=True)

    col_e, col_c, col_d = st.columns([1, 2, 1])
    with col_c:
        senha = st.text_input("Senha de acesso", type="password")
        if st.button("Entrar", use_container_width=True):
            if senha == SENHA_INTERNA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

@st.cache_data(ttl=86400)
def buscar_cdi():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.4389/dados/ultimos/1?formato=json"
        resposta = requests.get(url, timeout=5)
        return float(resposta.json()[0]["valor"])
    except:
        return 14.65

CDI_HOJE = buscar_cdi()  # apenas informativo — NÃO é usado na projeção

cores = {"Conservador": "#C4A882", "Moderado": "#d94d26", "Otimista": "#7c1c12"}

def simular(valor_inicial, aporte_mensal, taxa_anual, meses, aumento_anual=0.0):
    taxa_mensal = (1 + taxa_anual) ** (1/12) - 1
    saldos = [valor_inicial]
    saldo = valor_inicial
    aporte = aporte_mensal
    for m in range(meses):
        if m > 0 and m % 12 == 0:
            aporte = aporte * (1 + aumento_anual)
        saldo = saldo * (1 + taxa_mensal) + aporte
        saldos.append(saldo)
    return saldos

def total_aportado(valor_inicial, aporte_mensal, meses, aumento_anual=0.0):
    total = valor_inicial
    aporte = aporte_mensal
    for m in range(meses):
        if m > 0 and m % 12 == 0:
            aporte = aporte * (1 + aumento_anual)
        total += aporte
    return total

def mes_que_atinge(saldos, valor_meta):
    for i, saldo in enumerate(saldos):
        if saldo >= valor_meta:
            return i
    return None

def aporte_necessario(valor_meta, valor_inicial, taxa_anual, meses, aumento_anual=0.0):
    taxa_mensal = (1 + taxa_anual) ** (1/12) - 1
    fator = (1 + taxa_mensal) ** meses
    valor_por_real = 0.0
    aporte_relativo = 1.0
    for m in range(meses):
        if m > 0 and m % 12 == 0:
            aporte_relativo = aporte_relativo * (1 + aumento_anual)
        valor_por_real += aporte_relativo * (1 + taxa_mensal) ** (meses - m - 1)
    falta = valor_meta - valor_inicial * fator
    if falta <= 0:
        return 0.0
    return falta / valor_por_real

# ---------- CABEÇALHO ----------
col_logo, col_titulo = st.columns([1, 5], vertical_alignment="center")
with col_logo:
    st.image("logo.svg", width=170)
with col_titulo:
    st.title("Simulador de Metas Financeiras")
    st.caption(f"CDI hoje: {CDI_HOJE:.2f}% a.a. (só referência — não é usado na projeção)")

st.markdown("<hr style='border: none; border-top: 2px solid #7c1c12; margin-top: 0;'>", unsafe_allow_html=True)

# ---------- PREMISSAS (índices juntos no topo) ----------
# CDI e inflação de longo prazo ficam aqui em cima, valendo para todas as metas.
col_cdi, col_inf, col_tog = st.columns([1, 1, 1.4], vertical_alignment="bottom")
with col_cdi:
    cdi_projecao = st.number_input(
        "CDI de projeção (% a.a.)",
        min_value=0.0, value=10.0, step=0.5,
        help="Para o longo prazo usa-se uma média histórica (~10%), não o CDI de hoje, "
             "que sobe e desce demais. Troque aqui se quiser testar outro valor."
    )
with col_inf:
    inflacao_input = st.number_input(
        "Inflação anual (% a.a.)",
        min_value=0.0, value=5.0, step=0.5,
        help="Usada quando 'Descontar inflação' estiver ligado, para mostrar os "
             "valores no poder de compra de hoje."
    )
with col_tog:
    considerar_inflacao = st.toggle("Descontar inflação (valores de hoje)", value=False)

CDI = cdi_projecao
inflacao_anual = inflacao_input / 100
cenarios = {
    "Conservador": (CDI * 0.85) / 100,
    "Moderado": (CDI * 1.0) / 100,
    "Otimista": (CDI * 1.2) / 100,
}

# ---------- FUNÇÃO DA META ----------
def salvar_nome(id_meta):
    st.session_state.nomes_metas[id_meta] = st.session_state[f"nome_{id_meta}"]

def render_meta(id_meta):
    st.subheader("Dados da meta")

    col1, col2 = st.columns(2)

    with col1:
        nome_meta = st.text_input("Nome da meta", placeholder="Ex: Aposentadoria, Apartamento...",
                                  key=f"nome_{id_meta}", on_change=salvar_nome, args=(id_meta,))
        nome_meta = st.session_state.nomes_metas.get(id_meta, "")
        valor_meta = st.number_input("Valor da meta (R$)", min_value=0.0, value=500000.0, step=10000.0, key=f"valor_{id_meta}")
        prazo_anos = st.slider("Prazo (anos)", min_value=1, max_value=40, value=10, key=f"prazo_{id_meta}")

    with col2:
        valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, value=50000.0, step=5000.0, key=f"inicial_{id_meta}")
        aporte_mensal = st.number_input("Aporte mensal (R$)", min_value=0.0, value=2000.0, step=500.0, key=f"aporte_{id_meta}")
        aumento_aporte = st.number_input("Aumento anual do aporte (%)", min_value=0.0, value=0.0, step=1.0, key=f"aumento_{id_meta}") / 100

    meses = prazo_anos * 12

    resultados = {}
    for nome, taxa in cenarios.items():
        resultados[nome] = simular(valor_inicial, aporte_mensal, taxa, meses, aumento_aporte)

    if considerar_inflacao:
        inflacao_mensal = (1 + inflacao_anual) ** (1/12) - 1
        for nome in resultados:
            resultados[nome] = [
                saldo / (1 + inflacao_mensal) ** i
                for i, saldo in enumerate(resultados[nome])
            ]

    aportado = total_aportado(valor_inicial, aporte_mensal, meses, aumento_aporte)

    # ---------- GRÁFICO DE PROJEÇÃO ----------
    st.subheader("Projeção")

    fig = go.Figure()

    for nome, saldos in resultados.items():
        fig.add_trace(go.Scatter(
            x=list(range(meses + 1)),
            y=saldos,
            mode="lines",
            name=nome,
            line=dict(color=cores[nome], width=3),
        ))

    fig.add_hline(y=valor_meta, line_dash="dash", line_color="#ef4444",
                  annotation_text=f"Meta: {brl(valor_meta)}")

    fig.update_layout(
        margin=dict(t=30, b=20),
        xaxis_title="Meses",
        yaxis_title="Saldo (R$ de hoje)" if considerar_inflacao else "Saldo (R$)",
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickformat=",.0f",
        separators=",.",
    )

    st.plotly_chart(fig, use_container_width=True, key=f"fig_projecao_{id_meta}")

    # ---------- RESULTADO ----------
    mes = mes_que_atinge(resultados["Moderado"], valor_meta)

    if mes is not None:
        anos, meses_resto = divmod(mes, 12)
        meta_label = f'"{nome_meta}"' if nome_meta else "sua meta"
        st.success(f"No cenário moderado, você atinge {meta_label} em **{anos} anos e {meses_resto} meses**.")
    else:
        meta_label = f'"{nome_meta}"' if nome_meta else "a meta"
        st.warning(f"No cenário moderado, {meta_label} não é atingida no prazo. Veja abaixo o aporte necessário.")

    st.subheader("Quanto investir por mês para atingir a meta")

    col_a, col_b, col_c = st.columns(3)
    colunas = [col_a, col_b, col_c]

    for coluna, (nome, taxa) in zip(colunas, cenarios.items()):
        aporte = aporte_necessario(valor_meta, valor_inicial, taxa, meses, aumento_aporte)
        with coluna:
            st.metric(f"{nome} ({taxa:.1%} a.a.)", f"{brl(aporte)}/mês")

    # ---------- GRÁFICO DE COMPOSIÇÃO ----------
    st.subheader("De onde vem o resultado")

    fig2 = go.Figure()
    nomes_cenarios = list(cenarios.keys())
    rendimentos = [max(resultados[n][-1] - aportado, 0) for n in nomes_cenarios]

    fig2.add_trace(go.Bar(name="Aportes", x=nomes_cenarios, y=[aportado] * 3, marker_color="#C4A882"))
    fig2.add_trace(go.Bar(name="Rendimento", x=nomes_cenarios, y=rendimentos, marker_color="#7c1c12"))

    fig2.update_layout(
        barmode="stack",
        margin=dict(t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickformat=",.0f",
        separators=",.",
    )

    st.plotly_chart(fig2, use_container_width=True, key=f"fig_composicao_{id_meta}")

    # ---------- DOWNLOAD ----------
    resumo = f"""SIMULAÇÃO DE META - AVA INVEST

Meta: {nome_meta or "-"}
Valor da meta: {brl(valor_meta)}
Valor inicial: {brl(valor_inicial)}
Aporte mensal: {brl(aporte_mensal)}
Prazo: {prazo_anos} anos

RESULTADO POR CENÁRIO:
"""
    for nome, taxa in cenarios.items():
        final = resultados[nome][-1]
        aporte_nec = aporte_necessario(valor_meta, valor_inicial, taxa, meses, aumento_aporte)
        resumo += f"\n{nome} ({taxa:.1%} a.a.): saldo final {brl(final)} | aporte necessário {brl(aporte_nec)}/mês"

    resumo += "\n\nSimulação meramente ilustrativa. Não constitui recomendação de investimento."

    st.download_button("📄 Baixar resumo", resumo, file_name="simulacao_meta.txt", key=f"download_{id_meta}")
    if len(st.session_state.metas) > 1:
        if st.button("🗑️ Apagar esta meta", key=f"apagar_{id_meta}"):
            st.session_state.metas.remove(id_meta)
            st.rerun()

# mantém os valores de todas as metas vivos entre trocas
prefixos = ("nome_", "valor_", "prazo_", "inicial_", "aporte_", "inflacao_", "taxa_inflacao_", "aumento_")
for k in list(st.session_state.keys()):
    if k.startswith(prefixos):
        st.session_state[k] = st.session_state[k]

# ---------- ABAS ----------
if "metas" not in st.session_state:
    st.session_state.metas = [1]
    st.session_state.proximo_id = 2

col_btn, _ = st.columns([1, 4])
with col_btn:
    if st.button("➕ Nova meta"):
        st.session_state.metas.append(st.session_state.proximo_id)
        st.session_state.proximo_id += 1
        st.rerun()

if "nomes_metas" not in st.session_state:
    st.session_state.nomes_metas = {}

opcoes = {}
for id_meta in st.session_state.metas:
    nome = st.session_state.nomes_metas.get(id_meta, "")
    opcoes[id_meta] = nome if nome else f"Meta {id_meta}"

meta_selecionada = st.radio(
    "Selecione a meta:",
    options=list(opcoes.keys()),
    format_func=lambda id_meta: opcoes[id_meta],
    horizontal=True,
    key="meta_ativa",
)

render_meta(meta_selecionada)

# ---------- VISÃO GERAL ----------
if len(st.session_state.metas) > 1:
    st.markdown("<hr style='border: none; border-top: 2px solid #7c1c12;'>", unsafe_allow_html=True)
    st.subheader("Visão geral das metas")

    aporte_total = 0.0
    linhas = []
    for id_meta in st.session_state.metas:
        nome = st.session_state.nomes_metas.get(id_meta, "") or f"Meta {id_meta}"
        valor = st.session_state.get(f"valor_{id_meta}", 0.0)
        prazo = st.session_state.get(f"prazo_{id_meta}", 0)
        aporte = st.session_state.get(f"aporte_{id_meta}", 0.0)
        aporte_total += aporte
        linhas.append((nome, valor, prazo, aporte))

    colunas_metas = st.columns(len(linhas))
    for coluna, (nome, valor, prazo, aporte) in zip(colunas_metas, linhas):
        with coluna:
            st.metric(nome, brl(valor), f"{prazo} anos | {brl(aporte)}/mês", delta_color="off")

    st.metric("Aporte mensal total (todas as metas)", f"{brl(aporte_total)}/mês")

st.divider()
st.caption("⚠️ Simulação meramente ilustrativa com base em cenários hipotéticos de rentabilidade. "
           "Não constitui recomendação de investimento. Rentabilidade passada não garante resultados futuros.")