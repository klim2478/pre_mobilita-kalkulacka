import streamlit as st
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import os

st.set_page_config(page_title="PRE Nabídkový generátor", layout="wide")

# --- DATA A LOGIKA ---
models = {
    "Model 3.1 - Klasická realizace (21 míst)": {
        "popis": "Realizace na stávající přívod: 21 míst, 50 % penetrace (bez úpravy HDV).",
        "pater_svj": 450000,
        "hdv_navyseni": 0,
        "zakaznik_celkem": 1197000,
        "wallbox_ks": 23800,
        "mist": 21,
        "schema": "schema_kabel.png"
    },
    "Model 3.2 - Přípojnicové řešení (100 míst)": {
        "popis": "Realizace 100 míst, 100 % penetrace – přípojnicové vedení (obsahuje nové HDV a navýšení kapacity).",
        "pater_svj": 1250000,
        "hdv_navyseni": 580000, # 400k HDV + 180k jistič
        "zakaznik_celkem": 3500000,
        "wallbox_ks": 23800,
        "mist": 100,
        "schema": "schema_pripajnice.png"
    },
    "Model 3.3 - Malá realizace (10 míst)": {
        "popis": "Realizace 10 míst, 100 % penetrace, kabelové vedení (obsahuje nové HDV a navýšení kapacity).",
        "pater_svj": 290000,
        "hdv_navyseni": 500000, # 300k HDV + 200k jistič
        "zakaznik_celkem": 330000,
        "wallbox_ks": 23800,
        "mist": 10,
        "schema": "schema_kabel.png"
    }
}

# --- SIDEBAR VSTUPY ---
st.sidebar.header("📝 Údaje pro nabídku")
projekt_nazev = st.sidebar.text_input("Název projektu / SVJ:", "SVJ Trojská")
sel_name = st.sidebar.selectbox("Varianta realizace:", list(models.keys()))
podil_svj = st.sidebar.slider("Podíl SVJ na rozvodech v garážích (%)", 0, 100, 0)
dph_check = st.sidebar.checkbox("Ceny s DPH 12 %")

m = models[sel_name]
coeff = 1.12 if dph_check else 1.0
tax_label = "s DPH" if dph_check else "bez DPH"

# Výpočty dle vzoru z obrázku
naklady_svj_pater = (m["pater_svj"] + m["hdv_navyseni"]) * coeff
extra_z_garazi = (m["zakaznik_celkem"] * (podil_svj / 100)) * coeff
celkem_svj_investice = naklady_svj_pater + extra_z_garazi

naklad_uzivatel_rozvody = ((m["zakaznik_celkem"] * (1 - podil_svj / 100)) / m["mist"]) * coeff
celkem_uzivatel = (naklad_uzivatel_rozvody + (m["wallbox_ks"] * coeff))

# --- ZOBRAZENÍ V APP ---
st.title(f"Indikativní kalkulace: {projekt_nazev}")
st.subheader(f"Varianta: {sel_name}")

col1, col2 = st.columns(2)
with col1:
    st.metric("Celková investice SVJ", f"{celkem_svj_investice:,.0f} Kč".replace(",", " "))
    st.write(f"Včetně přípravy páteře a HDV ({tax_label})")

with col2:
    st.metric("Náklad na 1 uživatele", f"{celkem_uzivatel:,.0f} Kč".replace(",", " "))
    st.write(f"Včetně wallboxu a instalace ({tax_label})")

# --- GENERÁTOR WORDU ---
def create_word():
    doc = Document()
    
    # Hlavička
    title = doc.add_heading('Indikativní nabídka vybudování dobíjecí infrastruktury', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph()
    p.add_run(f'Projekt: {projekt_nazev}').bold = True
    p.add_run(f'\nModel: {sel_name}\nPopis: {m["popis"]}')

    # Tabulka nákladů (dle tvého vzoru)
    doc.add_heading('Ekonomické rozdělení nákladů', level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Light Shading Accent 1'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Položka'
    hdr_cells[1].text = f'Celkem ({tax_label})'
    hdr_cells[2].text = 'Hradí SVJ'
    hdr_cells[3].text = 'Hradí Uživatel'

    # Data řádky
    row1 = table.add_row().cells
    row1[0].text = 'Páteřní rozvody a HDV'
    row1[1].text = f'{(m["pater_svj"] + m["hdv_navyseni"])*coeff:,.0f} Kč'
    row1[2].text = f'{(m["pater_svj"] + m["hdv_navyseni"])*coeff:,.0f} Kč'
    row1[3].text = '0 Kč'

    row2 = table.add_row().cells
    row2[0].text = 'Zákaznické rozvody (garáže)'
    row2[1].text = f'{m["zakaznik_celkem"]*coeff:,.0f} Kč'
    row2[2].text = f'{extra_z_garazi:,.0f} Kč'
    row2[3].text = f'{(m["zakaznik_celkem"]*coeff - extra_z_garazi):,.0f} Kč'

    # Argumentace (Metodika)
    doc.add_heading('Proč zvolit toto řešení (Metodika PRE)', level=1)
    doc.add_paragraph('1. Bezpečnost: Centrální vypínání Total Stop pro hasiče.', style='List Bullet')
    doc.add_paragraph('2. Inteligentní řízení: Systém PRE Power Control hlídá soudobost a jističe.', style='List Bullet')
    doc.add_paragraph('3. Bez starostí: PRE zajišťuje revize, servis a individuální fakturaci.', style='List Bullet')

    # Schéma
    if os.path.exists(m["schema"]):
        doc.add_heading('Schéma zapojení', level=1)
        doc.add_picture(m["schema"], width=Inches(5.5))

    target = io.BytesIO()
    doc.save(target)
    return target.getvalue()

st.divider()
if st.button("📄 Vygenerovat Indikativní nabídku ve Wordu"):
    doc_bytes = create_word()
    st.download_button(
        label="📥 Stáhnout hotový dokument (.docx)",
        data=doc_bytes,
        file_name=f"Nabidka_{projekt_nazev.replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
