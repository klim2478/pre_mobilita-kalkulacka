import streamlit as st
import pandas as pd

st.set_page_config(page_title="PRE Kalkulačka", layout="wide")

st.title("⚡ Indikativní kalkulačka nákladů e-mobility")

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
        "desc": "Realizace 100 míst, 100 % penetrace – přípojnicové vedení.",
        "svj_base": 1830000,
        "zakaznik_celkem": 3500000,
        "wallbox": 23800,
        "mist": 100,
        "schema": "schema_pripajnice.png"
    },
    "Model 3.3 - Malá realizace (10 míst)": {
        "desc": "Realizace 10 míst, 100 % penetrace, kabelové vedení.",
        "svj_base": 790000,
        "zakaznik_celkem": 330000,
        "wallbox": 23800,
        "mist": 10,
        "schema": "schema_kabel.png"
    }
}

with st.sidebar:
    st.header("Nastavení")
    sel_name = st.selectbox("Model:", list(models.keys()))
    podil = st.slider("Podíl SVJ na rozvodech (%)", 0, 100, 0)
    dph = st.checkbox("Zobrazit s DPH (12 %)")

m = models[sel_name]
c = 1.12 if dph else 1.0

# Výpočty
investice_svj = (m["svj_base"] + (m["zakaznik_celkem"] * podil / 100)) * c
investice_osoba = ((m["zakaznik_celkem"] * (1 - podil / 100) / m["mist"]) + m["wallbox"]) * c

st.info(m["desc"])

col1, col2 = st.columns(2)
with col1:
    st.metric("Náklad SVJ", f"{investice_svj:,.0f} Kč".replace(",", " "))
    st.metric("Náklad na 1 stání", f"{investice_osoba:,.0f} Kč".replace(",", " "))

with col2:
    # Ošetření chyby s obrázkem - tohle zabrání pádu aplikace
    import os
    if os.path.exists(m["schema"]):
        st.image(m["schema"], caption="Schéma zapojení")
    else:
        st.warning(f"⚠️ Nahrajte soubor {m['schema']} do GitHubu pro zobrazení schématu.")

if st.button("Exportovat data"):
    df = pd.DataFrame([{"Model": sel_name, "SVJ": investice_svj, "Uživatel": investice_osoba}])
    st.download_button("Stáhnout CSV", df.to_csv(index=False).encode('utf-8'), "vypocet.csv")
