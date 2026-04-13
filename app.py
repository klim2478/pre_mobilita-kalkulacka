import streamlit as st
import pandas as pd

st.set_page_config(page_title="PRE E-mobilita Kalkulačka", layout="wide")

# CSS pro PRE barvy
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #00529b; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Indikativní kalkulačka nákladů e-mobility v SVJ/BD")
st.subheader("Všechny ceny jsou uvedeny bez DPH 12 %")

# Data modelů
models = {
    "Model 3.1 - Klasická realizace (21 míst)": {
        "desc": "Realizace na stávající přívod: 21 míst, 50 % penetrace (bez úpravy HDV).",
        "svj_base": 450000,
        "zakaznik_celkem": 1197000,
        "wallbox": 23800,
        "mist": 21,
        "schema": "schema_kabel.png"
    },
    "Model 3.2 - Přípojnicové řešení (100 míst)": {
        "desc": "Realizace 100 míst, 100 % penetrace – přípojnicové vedení (obsahuje nové HDV, navýšení kapacity na 250A).",
        "svj_base": 1830000,
        "zakaznik_celkem": 3500000,
        "wallbox": 23800,
        "mist": 100,
        "schema": "schema_busbar.png"
    },
    "Model 3.3 - Malá realizace (10 míst)": {
        "desc": "Realizace 10 míst, 100 % penetrace, kabelové vedení (obsahuje nové HDV, navýšení kapacity na 250A).",
        "svj_base": 790000,
        "zakaznik_celkem": 330000,
        "wallbox": 23800,
        "mist": 10,
        "schema": "schema_kabel.png"
    }
}

# Sidebar pro výběr
with st.sidebar:
    st.header("Nastavení parametrů")
    selected_model_name = st.selectbox("Vyberte vzorový model:", list(models.keys()))
    podil_svj = st.slider("Podíl SVJ na nákladech zákaznické části (%)", 0, 100, 0)

model = models[selected_model_name]

# Výpočty
naklady_svj_extra = model["zakaznik_celkem"] * (podil_svj / 100)
celkem_svj = model["svj_base"] + naklady_svj_extra

naklady_uzivatel_extra = (model["zakaznik_celkem"] * (1 - podil_svj / 100)) / model["mist"]
celkem_uzivatel = naklady_uzivatel_extra + model["wallbox"]

# Zobrazení výsledků
col1, col2 = st.columns(2)

with col1:
    st.info(f"**Popis:** {model['desc']}")
    st.metric("Celková investice SVJ (fond oprav)", f"{celkem_svj:,.0f} Kč".replace(",", " "))
    st.metric("Investice na 1 majitele stání", f"{celkem_uzivatel:,.0f} Kč".replace(",", " "))

with col2:
    st.write("**Schéma zapojení dle metodiky:**")
    try:
        st.image(model["schema"], use_column_width=True)
    except:
        st.warning(f"Zde se zobrazí obrázek {model['schema']} (nahrajte do Githubu).")

# Export
st.divider()
export_data = {
    "Model": [selected_model_name],
    "Podíl SVJ na rozvodech (%)": [podil_svj],
    "Celkem za SVJ (bez DPH)": [celkem_svj],
    "Celkem za Uživatele (bez DPH)": [celkem_uzivatel],
    "Počet míst": [model["mist"]]
}
df = pd.DataFrame(export_data)
csv = df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Exportovat výsledky do CSV",
    data=csv,
    file_name='kalkulace_emobilita_pre.csv',
    mime='text/csv',
)