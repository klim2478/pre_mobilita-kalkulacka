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
    "Model 3.1 - Realizace na stávající přívod (21 míst)": {
        "popis": "Realizace na stávající přívod, kabelové vedení: 21 míst, 50 % penetrace (bez úpravy HDV).",
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
        "hdv_navyseni": 580000,
        "zakaznik_celkem": 3500000,
        "wallbox_ks": 23800,
        "mist": 100,
        "schema": "schema_pripajnice.png"
    },
    "Model 3.3 - Malá realizace (10 míst)": {
        "popis": "Realizace 10 míst, 100 % penetrace, kabelové vedení (obsahuje nové HDV a navýšení kapacity).",
        "pater_svj": 290000,
        "hdv_navyseni": 500000,
        "zakaznik_celkem": 330000,
        "wallbox_ks": 23800,
        "mist": 10,
        "schema": "schema_kabel.png"
    }
}

# --- SIDEBAR VSTUPY ---
st.sidebar.header("📝 Údaje pro nabídku")
projekt_nazev = st.sidebar.text_input("Název projektu / SVJ:", "SVJ ")
sel_name = st.sidebar.selectbox("Varianta realizace:", list(models.keys()))
podil_svj = st.sidebar.slider("Podíl SVJ na rozvodech v garážích (%)", 0, 100, 0)
dph_check = st.sidebar.checkbox("Zobrazit ceny s DPH (12 %)", value=False)

m = models[sel_name]
coeff = 1.12 if dph_check else 1.0
tax_label = "VČETNĚ DPH 12 %" if dph_check else "BEZ DPH"

# Výpočty
naklady_svj_pater = (m["pater_svj"] + m["hdv_navyseni"]) * coeff
extra_z_garazi = (m["zakaznik_celkem"] * (podil_svj / 100)) * coeff
celkem_svj_investice = naklady_svj_pater + extra_z_garazi

naklad_uzivatel_rozvody = ((m["zakaznik_celkem"] * (1 - podil_svj / 100)) / m["mist"]) * coeff
celkem_uzivatel = (naklad_uzivatel_rozvody + (m["wallbox_ks"] * coeff))

# --- ZOBRAZENÍ V APP ---
st.title(f"Indikativní kalkulace: {projekt_nazev}")
st.subheader(f"Ceny jsou uvedeny: {tax_label}")

col1, col2 = st.columns(2)
with col1:
    st.metric("Celková investice SVJ", f"{celkem_svj_investice:,.0f} Kč".replace(",", " "))
with col2:
    st.metric("Náklad na 1 uživatele (vč. WB)", f"{celkem_uzivatel:,.0f} Kč".replace(",", " "))

if podil_svj > 0:
    st.success(f"💡 SVJ přispívá na zákaznické rozvody v garážích podílem {podil_svj} %.")

st.divider()

# Tabulka pro náhled
table_data = [
    {
        "Položka": "Páteřní rozvody a HDV",
        "Celkem objekt": f"{(m['pater_svj'] + m['hdv_navyseni']) * coeff:,.0f} Kč".replace(",", " "),
        "Hradí SVJ": f"{(m['pater_svj'] + m['hdv_navyseni']) * coeff:,.0f} Kč".replace(",", " "),
        "Hradí 1 Uživatel": "0 Kč"
    },
    {
        "Položka": f"Zákaznické rozvody (příspěvek SVJ {podil_svj} %)",
        "Celkem objekt": f"{m['zakaznik_celkem'] * coeff:,.0f} Kč".replace(",", " "),
        "Hradí SVJ": f"{extra_z_garazi:,.0f} Kč".replace(",", " "),
        "Hradí 1 Uživatel": f"{naklad_uzivatel_rozvody:,.0f} Kč".replace(",", " ")
    },
    {
        "Položka": "Wallbox vč. instalace",
        "Celkem objekt": f"{(m['wallbox_ks'] * m['mist']) * coeff:,.0f} Kč".replace(",", " "),
        "Hradí SVJ": "0 Kč",
        "Hradí 1 Uživatel": f"{m['wallbox_ks'] * coeff:,.0f} Kč".replace(",", " ")
    }
]
st.table(pd.DataFrame(table_data))

# --- GENERÁTOR WORDU ---
def create_word():
    doc = Document()
    
    title = doc.add_heading('Indikativní kalkulačka nákladů emobility v SVJ/BD dle vzorové instalace', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph()
    p.add_run(f'Projekt: {projekt_nazev}').bold = True
    p.add_run(f'\nModel: {sel_name}')
    p.add_run(f'\nCenová hladina: {tax_label}').bold = True

    if podil_svj > 0:
        p_info = doc.add_paragraph()
        p_info.add_run(f'Upozornění: Tato kalkulace počítá s příspěvkem SVJ/BD na zákaznické rozvody ve výši {podil_svj} %.').italic = True

    doc.add_heading('Rozdělení nákladů', level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Light Shading Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text = 'Položka'
    hdr[1].text = 'Celkem objekt'
    hdr[2].text = 'Hradí SVJ'
    hdr[3].text = 'Hradí 1 Uživatel'

    for row_item in table_data:
        cells = table.add_row().cells
        cells[0].text = row_item["Položka"]
        cells[1].text = row_item["Celkem objekt"]
        cells[2].text = row_item["Hradí SVJ"]
        cells[3].text = row_item["Hradí 1 Uživatel"]

    doc.add_heading('Proč zvolit PRE POINT RESIDENT?', level=1)
    doc.add_paragraph('Bezpečnost: Centrální vypínání Total Stop a certifikované komponenty.', style='List Bullet')
    doc.add_paragraph('Správa: Automatické rozúčtování spotřeby přímo mezi PRE a koncového uživatele.', style='List Bullet')
    doc.add_paragraph('Dynamika: Systém řízení výkonu brání přetížení domovního jističe.', style='List Bullet')

    if os.path.exists(m["schema"]):
        doc.add_heading('Schéma zapojení', level=1)
        doc.add_picture(m["schema"], width=Inches(5.0))

    target = io.BytesIO()
    doc.save(target)
    return target.getvalue()

st.divider()
if st.button("📄 Vygenerovat Indikativní nabídku"):
    doc_bytes = create_word()
    st.download_button(label="📥 Stáhnout Word (.docx)", data=doc_bytes, file_name=f"Nabidka_{projekt_nazev}.docx")
