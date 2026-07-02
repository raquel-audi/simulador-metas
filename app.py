import streamlit as st
import plotly.graph_objects as go

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
col_logo, col_titulo = st.columns([1, 5], vertical_alignment="center")
with col_logo:
    st.image("logo.svg", width=170)
with col_titulo:
    st.title("Simulador de Metas Financeiras")
st.subheader("Dados da meta")

st.markdown("<hr style='border: none; border-top: 2px solid #7c1c12; margin-top: 0;'>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    nome_meta = st.text_input("Nome da meta", placeholder="Ex: Aposentadoria, Apartamento...")
    valor_meta = st.number_input("Valor da meta (R$)", min_value=0.0, value=500000.0, step=10000.0)
    prazo_anos = st.slider("Prazo (anos)", min_value=1, max_value=40, value=10)

with col2:
    valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, value=50000.0, step=5000.0)
    aporte_mensal = st.number_input("Aporte mensal (R$)", min_value=0.0, value=2000.0, step=500.0)

def simular(valor_inicial, aporte_mensal, taxa_anual, meses):
    taxa_mensal = (1 + taxa_anual) ** (1/12) - 1
    saldos = [valor_inicial]
    saldo = valor_inicial
    for _ in range(meses):
        saldo = saldo * (1 + taxa_mensal) + aporte_mensal
        saldos.append(saldo)
    return saldos

cenarios = {
    "Conservador": 0.06,
    "Moderado": 0.09,
    "Otimista": 0.12,
}

meses = prazo_anos * 12

resultados = {}
for nome, taxa in cenarios.items():
    resultados[nome] = simular(valor_inicial, aporte_mensal, taxa, meses)

st.subheader("Projeção")

cores = {"Conservador": "#C4A882", "Moderado": "#d94d26", "Otimista": "#7c1c12"}

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
    yaxis_title="Saldo (R$)",
    hovermode="x unified",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Quanto investir por mês para atingir a meta")

def mes_que_atinge(saldos, valor_meta):
    for i, saldo in enumerate(saldos):
        if saldo >= valor_meta:
            return i
    return None

mes = mes_que_atinge(resultados["Moderado"], valor_meta)

if mes is not None:
    anos, meses_resto = divmod(mes, 12)
    meta_label = f'"{nome_meta}"' if nome_meta else "sua meta"
    st.success(f"No cenário moderado, você atinge {meta_label} em **{anos} anos e {meses_resto} meses**.")
else:
    meta_label = f'"{nome_meta}"' if nome_meta else "a meta"
    st.warning(f"No cenário moderado, {meta_label} não é atingida no prazo. Veja abaixo o aporte necessário.")

def aporte_necessario(valor_meta, valor_inicial, taxa_anual, meses):
    taxa_mensal = (1 + taxa_anual) ** (1/12) - 1
    fator = (1 + taxa_mensal) ** meses
    falta = valor_meta - valor_inicial * fator
    if falta <= 0:
        return 0.0
    return falta * taxa_mensal / (fator - 1)

col_a, col_b, col_c = st.columns(3)
colunas = [col_a, col_b, col_c]

for coluna, (nome, taxa) in zip(colunas, cenarios.items()):
    aporte = aporte_necessario(valor_meta, valor_inicial, taxa, meses)
    with coluna:
        st.metric(f"{nome} ({taxa:.0%} a.a.)", f"{brl(aporte)}/mês")

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
    aporte_nec = aporte_necessario(valor_meta, valor_inicial, taxa, meses)
    resumo += f"\n{nome} ({taxa:.0%} a.a.): saldo final {brl(final)} | aporte necessário {brl(aporte_nec)}/mês"

resumo += "\n\nSimulação meramente ilustrativa. Não constitui recomendação de investimento."

st.download_button("📄 Baixar resumo", resumo, file_name="simulacao_meta.txt")

st.divider()
st.caption("⚠️ Simulação meramente ilustrativa com base em cenários hipotéticos de rentabilidade. "
           "Não constitui recomendação de investimento. Rentabilidade passada não garante resultados futuros.")