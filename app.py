import streamlit as st
import pandas as pd

st.set_page_config(page_title="PRE E-mobilita Kalkulačka", layout="wide")

# CSS pro barvy PRE (modrá a šedá)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #00529b; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Indikativní kalkulačka nákladů e-mobility v SVJ/BD")

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
        "schema": "schema_pripajnice.png"
    },
    "Model 3.3 - Malá realizace (10 míst)": {
        "desc": "Realizace - 10 míst, 100 % penetrace, kabelové vedení (obsahuje nové HDV, navýšení kapacity na 250A).",
        "svj_base": 790000,
        "zakaznik_celkem": 330000,
        "wallbox": 23800,
        "mist": 10,
        "schema": "schema_kabel.png"
    }
}

# Sidebar
with st.sidebar:
    st.header("⚙️ Nastavení")
    selected_model_name = st.selectbox("Vyberte vzorový model:", list(models.keys()))
    podil_svj = st.slider("Podíl SVJ na nákladech zákaznické části (%)", 0, 100, 0)
    show_dph = st.checkbox("Zobrazit ceny s DPH (12 %)", value=False)

model = models[selected_model_name]
coeff = 1.12 if show_dph else 1.0
label_dph = "s DPH" if show_dph else "bez DPH"

# Výpočty
naklady_svj_extra = model["zakaznik_celkem"] * (podil_svj / 100)
celkem_svj = (model["svj_base"] + naklady_svj_extra) * coeff

naklady_uzivatel_extra = (model["zakaznik_celkem"] * (1 - podil_svj / 100)) / model["mist"]
celkem_uzivatel = (naklady_uzivatel_extra + model["wallbox"]) * coeff

# Hlavní panel
st.info(f"**Popis vybraného řešení:** {model['desc']}")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"📊 Odhadované náklady ({label_dph})")
    st.metric("Celková investice SVJ (fond oprav)", f"{celkem_svj:,.0f} Kč".replace(",", " "))
    st.write(f"*(Z toho základní páteř: {model['svj_base']*coeff:,.0f} Kč)*".replace(",", " "))
    
    st.write("---")
    st.metric("Náklad na 1 majitele stání", f"{celkem_uzivatel:,.0f} Kč".replace(",", " "))
    st.write(f"*(Z toho wallbox: {model['wallbox']*coeff:,.0f} Kč)*".replace(",", " "))

with col2:
    st.subheader("🖼️ Schéma zapojení")
    try:
        st.image(model["schema"], caption=f"Schéma pro {selected_model_name}")
    except:
        st.warning(f"Obrázek {model['schema']} nebyl v úložišti nalezen.")

# Export
st.divider()
if st.button("Generate Report Data"):
    export_df = pd.DataFrame([{
        "Model": selected_model_name,
        "DPH": "12%",
        "Zobrazeno s DPH": show_dph,
        "Investice SVJ": f"{celkem_svj:.0f} Kč",
        "Investice Uzivatel": f"{celkem_uzivatel:.0f} Kč"
    }])
    st.dataframe(export_df)
    st.download_button("📥 Stáhnout CSV", export_df.to_csv(index=False).encode('utf-8'), "kalkulace.csv", "text/csv")
