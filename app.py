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
        "rozsiritelnost": "Nízká – omezeno kapacitou stávajícího jističe a místem v kabelových trasách.",
        "pater_svj": 450000,
        "hdv_navyseni": 0,
        "zakaznik_celkem": 1197000,
        "wallbox_ks": 23800,
        "mist": 21,
        "schema": "schema_kabel.png"
    },
    "Model 3.2 - Přípojnicové řešení (100 míst)": {
        "popis": "Realizace 100 míst, 100 % penetrace – přípojnicové vedení (obsahuje nové HDV a navýšení kapacity).",
        "rozsiritelnost": "Vysoká – páteřní systém umožňuje snadné připojení jakéhokoliv stání v budoucnu bez nutnosti dalších stavebních úprav.",
        "pater_svj": 1250000,
        "hdv_navyseni": 580000,
        "zakaznik_celkem": 3500000,
        "wallbox_ks": 23800,
        "mist": 100,
        "schema": "schema_pripajnice.png"
    },
    "Model 3.3 - Malá realizace (10 míst)": {
        "popis": "Realizace 10 míst, 100 % penetrace, kabelové vedení (obsahuje nové HDV a navýšení kapacity).",
        "rozsiritelnost": "Střední – díky novému HDV je kapacita dostatečná, ale kabelové trasy mohou být při dalším rozšiřování komplikované.",
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
tax_label = "Včetně DPH 12 %" if dph_check else "Bez DPH"

# Výpočty
naklady_svj_pater = (m["pater_svj"] + m["hdv_navyseni"]) * coeff
extra_z_garazi = (m["zakaznik_celkem"] * (podil_svj / 100)) * coeff
celkem_svj_investice = naklady_svj_pater + extra_z_garazi

naklad_uzivatel_rozvody = ((m["zakaznik_celkem"] * (1 - podil_svj / 100)) / m["mist"]) * coeff
celkem_uzivatel = (naklad_uzivatel_rozvody + (m["wallbox_ks"] * coeff))

# --- ZOBRAZENÍ V APP ---
st.title(f"Indikativní kalkulace: {projekt_nazev}")
st.subheader(f"Cenová hladina: {tax_label}")

col1, col2 = st.columns(2)
with col1:
    st.metric("Celková investice SVJ", f"{celkem_svj_investice:,.0f} Kč".replace(",", " "))
    st.info(f"**Rozšiřitelnost:** {m['rozsiritelnost']}")
with col2:
    st.metric("Náklad na 1 uživatele (vč. WB)", f"{celkem_uzivatel:,.0f} Kč".replace(",", " "))
    st.warning("Doporučeno: Modul COMFORT (bez starostí pro SVJ)")

st.divider()

# Tabulka pro náhled
table_data = [
    {
        "Položka": "Páteřní rozvody a nové HDV",
        "Hradí SVJ": f"{(m['pater_svj'] + m['hdv_navyseni']) * coeff:,.0f} Kč".replace(",", " "),
        "Hradí 1 Uživatel": "0 Kč"
    },
    {
        "Položka": f"Zákaznické rozvody (příspěvek SVJ {podil_svj} %)",
        "Hradí SVJ": f"{extra_z_garazi:,.0f} Kč".replace(",", " "),
        "Hradí 1 Uživatel": f"{naklad_uzivatel_rozvody:,.0f} Kč".replace(",", " ")
    },
    {
        "Položka": "Wallbox vč. instalace",
        "Hradí SVJ": "0 Kč",
        "Hradí 1 Uživatel": f"{m['wallbox_ks'] * coeff:,.0f} Kč".replace(",", " ")
    }
]
st.table(pd.DataFrame(table_data))

# --- GENERÁTOR WORDU ---
def create_word():
    doc = Document()
    
    # 1. Titulka
    title = doc.add_heading('Indikativní nákladovost emobility v SVJ/BD dle vzorové instalace', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph()
    p.add_run(f'Projekt: {projekt_nazev}').bold = True
    p.add_run(f'\nZvolený model: {sel_name}')
    p.add_run(f'\nCenová hladina: {tax_label}').bold = True

    # 2. Argumentace - Proč Modul COMFORT?
    doc.add_heading('Klíčové výhody řešení v Modulu COMFORT', level=1)
    
    # Rozúčtování
    para = doc.add_paragraph()
    para.add_run('Bezstarostné rozúčtování: ').bold = True
    para.add_run('Při individuálním řešení padá povinnost rozúčtování elektřiny na SVJ, což je administrativně i právně náročné. V modulu COMFORT PRE fakturuje spotřebu přímo koncovému uživateli. SVJ nemá s vyúčtováním žádnou práci.')

    # Řízení výkonu
    para = doc.add_paragraph()
    para.add_run('Ochrana proti přetížení: ').bold = True
    para.add_run('Systém dynamického řízení výkonu (DLM) neustále monitoruje spotřebu celého objektu (výtahy, osvětlení, byty) a dobíjení aut v reálném čase reguluje tak, aby nikdy nedošlo k překročení kapacity hlavního jističe.')

    # Rozšiřitelnost (str 13/14)
    doc.add_heading('Technická koncepce a rozšířitelnost', level=1)
    doc.add_paragraph(f'Technický popis: {m["popis"]}')
    doc.add_paragraph(f'Možnost budoucího rozšíření: {m["rozsiritelnost"]}')

    # 3. Tabulka nákladů
    doc.add_heading('Ekonomické rozdělení nákladů', level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Light Shading Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text = 'Položka'
    hdr[1].text = 'Hradí SVJ (Fond oprav)'
    hdr[2].text = 'Hradí 1 Uživatel'

    for row_item in table_data:
        cells = table.add_row().cells
        cells[0].text = row_item["Položka"]
        cells[1].text = row_item["Hradí SVJ"]
        cells[2].text = row_item["Hradí 1 Uživatel"]

    # 4. Schéma
    if os.path.exists(m["schema"]):
        doc.add_heading('Schéma zapojení (vzorové)', level=1)
        doc.add_picture(m["schema"], width=Inches(5.0))

    target = io.BytesIO()
    doc.save(target)
    return target.getvalue()

st.divider()
if st.button("📄 Vygenerovat Profesionální nabídku (.docx)"):
    doc_bytes = create_word()
    st.download_button(label="📥 Stáhnout Nabídku", data=doc_bytes, file_name=f"Nabidka_PRE_{projekt_nazev}.docx")
