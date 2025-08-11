import streamlit as st
import pandas as pd
import re
import io
import unicodedata
from typing import Dict, List, Tuple
import base64

# Simple SLK to Excel converter app

TRANSLATIONS = {
    "Nederlands": {
        "title": "Routemeister converter tool",
        "subtitle": "Meditec Export Reha Bonn  > Routemeister import",
        "upload": "Upload SLK Bestand",
        "select_file": "Selecteer een SLK bestand om te converteren",
        "mapping": "⚙️ Kolom Mapping Configuratie (optioneel)",
        "mapping_desc": "Configureer hoe de SLK kolommen moeten worden omgezet:",
        "preview": "📊 Data Preview",
        "input_data": "📁 Input Data (SLK)",
        "found_columns": "📊 Gevonden Kolommen",
        "output_data": "🔄 Output Data (Excel)",
        "success": "✅ Conversie voltooid!",
        "download": "📥 Download Excel bestand",
        "warning_special": "⚠️ {n} cel(len) bevatten speciale of niet-toegestane tekens. Deze zijn lichtrood gemarkeerd. Pas het SLK-bestand aan en probeer opnieuw te converteren.",
        "no_data": "❌ Geen data gevonden in het SLK bestand",
        "processing": "SLK bestand wordt geparsed...",
        "converting": "Data wordt geconverteerd...",
        "select_language": "Taal / Sprache / Language"
    },
    "Deutsch": {
        "title": "Routemeister Konverter-Tool",
        "subtitle": "Meditec Export Reha Bonn  > Routemeister Import",
        "upload": "SLK Datei hochladen",
        "select_file": "Wählen Sie eine SLK-Datei zum Konvertieren aus",
        "mapping": "⚙️ Spaltenzuordnung (optional)",
        "mapping_desc": "Konfigurieren Sie, wie die SLK-Spalten zugeordnet werden:",
        "preview": "📊 Datenvorschau",
        "input_data": "📁 Eingabedaten (SLK)",
        "found_columns": "📊 Gefundene Spalten",
        "output_data": "🔄 Ausgabedaten (Excel)",
        "success": "✅ Konvertierung abgeschlossen!",
        "download": "📥 Excel-Datei herunterladen",
        "warning_special": "⚠️ {n} Zelle(n) enthalten spezielle oder nicht erlaubte Zeichen. Diese sind hellrot markiert. Bitte passen Sie die SLK-Datei an und versuchen Sie es erneut.",
        "no_data": "❌ Keine Daten in der SLK-Datei gefunden",
        "processing": "SLK-Datei wird geparst...",
        "converting": "Daten werden konvertiert...",
        "select_language": "Taal / Sprache / Language"
    },
    "English": {
        "title": "Routemeister converter tool",
        "subtitle": "Meditec Export Reha Bonn  > Routemeister import",
        "upload": "Upload SLK file",
        "select_file": "Select an SLK file to convert",
        "mapping": "⚙️ Column Mapping (optional)",
        "mapping_desc": "Configure how the SLK columns should be mapped:",
        "preview": "📊 Data Preview",
        "input_data": "📁 Input Data (SLK)",
        "found_columns": "📊 Found Columns",
        "output_data": "🔄 Output Data (Excel)",
        "success": "✅ Conversion completed!",
        "download": "📥 Download Excel file",
        "warning_special": "⚠️ {n} cell(s) contain special or disallowed characters. These are highlighted in light red. Please adjust the SLK file and try again.",
        "no_data": "❌ No data found in the SLK file",
        "processing": "Parsing SLK file...",
        "converting": "Converting data...",
        "select_language": "Taal / Sprache / Language"
    }
}

def clean_value(val):
    if pd.isna(val):
        return val
    
    # Converteer naar string
    text = str(val)
    
    # Vervang escape sequences + de volgende letter door de juiste umlaut
    # Deze worden nu al in de parser afgehandeld, maar als backup hier ook
    escape_replacements = {
        '\x1bNHa': 'ä',  # \x1bNH + a = ä
        '\x1bNHo': 'ö',  # \x1bNH + o = ö 
        '\x1bNHu': 'ü',  # \x1bNH + u = ü 
        '\x1bNHr': 'ür', # \x1bNH + r = ür (voor "für")
        '\x1bNOo': 'ö',  # \x1bNO + o = ö
        '\x1bNUu': 'ü',  # \x1bNU + u = ü
        '\x1bNSs': 'ss', # \x1bNS + s = ss (ß wordt ss)
        '\x1bN{e': 'ße', # \x1bN{ + e = ße (ß escape sequence)
        # Probeer ook andere varianten
        '\x1bNUb': 'üb', # \x1bNU + b = üb 
        '\x1bNUc': 'üc', # \x1bNU + c = üc 
    }
    
    # Pas escape sequence replacements toe
    for escape_seq, replacement in escape_replacements.items():
        if escape_seq in text:
            text = text.replace(escape_seq, replacement)
    
    # Verwijder overgebleven escape sequences
    text = re.sub(r'\x1b[A-Z]{2,}[a-z{]?', '', text)
    
    # Extra conversie: ß naar ss als het nog in de tekst staat
    text = text.replace('ß', 'ss')
    
    # Verwijder controle karakters maar behoud printbare karakters
    cleaned = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')
    
    # Verwijder alleen de echt problematische karakters voor Excel
    problematic_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', 
                        '\x0b', '\x0c', '\x0e', '\x0f', '\x10', '\x11', '\x12', '\x13', '\x14', 
                        '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a', '\x1b', '\x1c', '\x1d', 
                        '\x1e', '\x1f']
    
    for char in problematic_chars:
        cleaned = cleaned.replace(char, '')
    
    return cleaned

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    return df.applymap(clean_value)

def extract_rit_datum(file_content: str) -> str:
    # Zoek naar Y2;X1
    last_row = None
    last_col = None
    for line in file_content.split('\n'):
        line = line.strip()
        pos_match = re.search(r'Y(\d+);X(\d+)', line)
        if pos_match:
            last_row = int(pos_match.group(1))
            last_col = int(pos_match.group(2))
            continue
        if line.startswith('C;K') and last_row == 2 and last_col == 1:
            match = re.search(r'C;K"([^"]*)"', line)
            if match:
                datum = match.group(1)
                # Vervang punten door streepjes in datum
                return datum.replace('.', '-')
    return ''

def parse_slk_patients(file_content: str) -> pd.DataFrame:
    # Robuuste parser: onthoud altijd laatst gevonden Y/X, koppel elke C;K aan die coördinaat
    patients = []
    current_patient = {}
    last_row = None
    last_col = None
    for line in file_content.split('\n'):
        line = line.strip()
        pos_match = re.search(r'Y(\d+);X(\d+)', line)
        if pos_match:
            last_row = int(pos_match.group(1))
            last_col = int(pos_match.group(2))
            continue
        if line.startswith('C;K') and last_row is not None and last_col is not None:
            if last_row >= 4 and 2 <= last_col <= 14:
                # Accepteer zowel C;K"waarde" als C;Kwaarde (voor postcodes etc.)
                match = re.search(r'C;K"([^"]*)"', line)
                if not match:
                    # Probeer zonder quotes (voor numerieke waarden)
                    match = re.search(r'C;K([0-9]+)$', line)
                if match:
                    value = match.group(1) if match.group(1) is not None else match.group(2)
                    
                    # Vervang escape sequences + de volgende letter door de juiste umlaut
                    # De escape sequence vervangt de volgende letter
                    escape_replacements = {
                        '\x1bNHa': 'ä',  # \x1bNH + a = ä
                        '\x1bNHo': 'ö',  # \x1bNH + o = ö 
                        '\x1bNHu': 'ü',  # \x1bNH + u = ü 
                        '\x1bNHr': 'ür', # \x1bNH + r = ür (voor "für")
                        '\x1bNOo': 'ö',  # \x1bNO + o = ö
                        '\x1bNUu': 'ü',  # \x1bNU + u = ü
                        '\x1bNSs': 'ss', # \x1bNS + s = ss (ß wordt ss)
                        '\x1bN{e': 'ße', # \x1bN{ + e = ße (ß escape sequence)
                        # Probeer ook andere varianten
                        '\x1bNUb': 'üb', # \x1bNU + b = üb 
                        '\x1bNUc': 'üc', # \x1bNU + c = üc 
                    }
                    
                    # Probeer alle mogelijke combinaties
                    for escape_seq, replacement in escape_replacements.items():
                        if escape_seq in value:
                            value = value.replace(escape_seq, replacement)
                    
                    # Verwijder overgebleven escape sequences
                    value = re.sub(r'\x1b[A-Z]{2,}[a-z]?', '', value)
                    
                    # Extra conversie: ß naar ss als het nog in de tekst staat
                    value = value.replace('ß', 'ss')
                    
                    column_mapping = {
                        2: 'erster_termin',
                        3: 'letzter_termin',
                        4: 'name',
                        5: 'vorname',
                        6: 'titel',
                        7: 'telefon',
                        8: 'strasse',
                        9: 'plz',
                        10: 'ort',
                        11: 'adresszusatz',
                        12: 'bemerkung',
                        13: 'bht',
                        14: 'fallnummer'
                    }
                    col_name = column_mapping[last_col]
                    if last_col == 2:
                        # Start nieuwe patient bij X2
                        if current_patient:
                            patients.append(current_patient)
                        current_patient = {}
                    current_patient[col_name] = value
    if current_patient:
        patients.append(current_patient)
    df = pd.DataFrame(patients)
    # Zorg dat alle relevante kolommen altijd aanwezig zijn en in de juiste volgorde staan
    all_cols = ['erster_termin', 'letzter_termin', 'name', 'vorname', 'titel', 'telefon', 'strasse', 'plz', 'ort', 'adresszusatz', 'bemerkung', 'bht', 'fallnummer']
    for col in all_cols:
        if col not in df.columns:
            df[col] = ''
    df = df[all_cols]
    return df

def convert_to_custom_format(df: pd.DataFrame, rit_datum: str) -> pd.DataFrame:
    # Helper: split phone numbers
    def split_phones(telefon):
        if pd.isna(telefon):
            return '', ''
        parts = re.split(r'[ ,;/]+', str(telefon).strip())
        hoofd = parts[0] if len(parts) > 0 else ''
        tweede = parts[1] if len(parts) > 1 else ''
        return hoofd, tweede
    
    # Helper: format time by removing colons
    def format_time(tijd):
        if pd.isna(tijd) or tijd == '':
            return ''
        # Verwijder dubbele punten uit tijd (15:15 -> 1515)
        return str(tijd).replace(':', '')

    columns = [
        'patient ID', 'leeg1', 'Name', 'vorname', 'leeg2', 'leeg3', 'strasse+nr', 'leeg4',
        'ort', 'PLZ', 'landcode', '1telefon', '2telefon', 'leeg5', 'leeg6',
        'datum von farht', 'leeg7', 'erster_termin', 'letze_termin'
    ]
    output = []
    for _, row in df.iterrows():
        hoofd, tweede = split_phones(row.get('telefon', ''))
        landcode = 'D'
        output.append([
            row.get('fallnummer', ''), # 1 patient ID
            '',                       # 2 leeg
            row.get('name', ''),      # 3 Name (achternaam)
            row.get('vorname', ''),   # 4 vorname
            '',                       # 5 leeg
            '',                       # 6 leeg
            row.get('strasse', ''),   # 7 strasse+nr
            '',                       # 8 leeg
            row.get('ort', ''),       # 9 ort (plaatsnaam)
            row.get('plz', ''),       # 10 PLZ (postcode)
            landcode,                 # 11 landcode
            hoofd,                    # 12 1telefon
            tweede,                   # 13 2telefon
            '',                       # 14 leeg
            '',                       # 15 leeg
            rit_datum,                # 16 datum der farht
            '',                       # 17 leeg
            format_time(row.get('erster_termin', '')), # 18 erster_termin
            format_time(row.get('letzter_termin', '')) # 19 letzter_termin
        ])
    df_out = pd.DataFrame(output, columns=columns)
    # Splits de kolom '1telefon' op komma's in meerdere kolommen
    if '1telefon' in df_out.columns:
        tel_split = df_out['1telefon'].str.split(',', expand=True)
        for i in range(tel_split.shape[1]):
            df_out[f'1telefon_{i+1}'] = tel_split[i].str.strip()
        df_out = df_out.drop(columns=['1telefon'])
    # Zet de kolommen in de gewenste volgorde, waarbij 1telefon_1 op positie 12 komt
    gewenste_volgorde = [
        'patient ID', 'leeg1', 'Name', 'vorname', 'leeg2', 'leeg3', 'strasse+nr', 'leeg4',
        'ort', 'PLZ', 'landcode', '1telefon_1', '2telefon', 'leeg5', 'leeg6',
        'datum von farht', 'leeg7', 'erster_termin', 'letze_termin'
    ]
    # Voeg extra telefoonkolommen toe achteraan als ze bestaan
    extra_telcols = [col for col in df_out.columns if col.startswith('1telefon_') and col != '1telefon_1']
    for col in extra_telcols:
        if col not in gewenste_volgorde:
            gewenste_volgorde.append(col)
    # Alleen kolommen die daadwerkelijk bestaan in df_out
    bestaande_volgorde = [col for col in gewenste_volgorde if col in df_out.columns]
    df_out = df_out[bestaande_volgorde]
    return df_out

def get_download_link(df: pd.DataFrame, filename: str, text: str):
    """Generate a download link for the DataFrame."""
    from openpyxl import Workbook
    
    buffer = io.BytesIO()
    
    # Maak direct een Excel workbook zonder pandas tussenkomst
    wb = Workbook()
    ws = wb.active
    ws.title = 'Data'
    
    # Schrijf alleen de data waarden, geen headers
    data_only = df.values.tolist()
    for row_idx, row_data in enumerate(data_only, 1):  # Start bij rij 1 (niet 0)
        for col_idx, value in enumerate(row_data, 1):   # Start bij kolom 1 (niet 0)
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Sla op naar buffer
    wb.save(buffer)
    buffer.seek(0)
    
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{text}</a>'
    return href

def has_special_chars(val):
    """Check of een waarde speciale/ongewenste tekens bevat (niet-printbaar of niet-ASCII)."""
    if pd.isna(val):
        return False
    s = str(val)
    # Niet-printbare/control chars of niet-ASCII
    return any(ord(c) < 32 or ord(c) > 126 for c in s)

def highlight_special_chars(df):
    """Geeft een Styler terug die cellen met speciale tekens lichtrood maakt."""
    def style_func(val):
        if has_special_chars(val):
            return 'background-color: #ffcccc'  # lichtrood
        return ''
    return df.style.applymap(style_func)

def main():
    taal = st.selectbox(TRANSLATIONS["Deutsch"]["select_language"], ["Deutsch", "Nederlands", "English"], index=0)
    t = TRANSLATIONS[taal]
    st.set_page_config(
        page_title=t["title"],
        page_icon="📊",
        layout="wide"
    )

    # Logo bovenaan
    st.image("Routemeister_Logo_White_BG_Larger.png", width=220)
    st.markdown(f"""
    # {t['title']}
    **{t['subtitle']}**
    """)
    st.markdown("---")
    
    # File upload
    st.header(t["upload"])
    uploaded_file = st.file_uploader(
        t["select_file"],
        type=['slk', 'txt'],
        help=t["select_file"]
    )
    
    # Column mapping configuration
    with st.expander(t["mapping"], expanded=False):
        st.markdown(t["mapping_desc"])
        # Default column mapping
        default_mapping = {
            'Patient_ID': 'fallnummer',
            'Name': 'name', 
            'Vorname': 'vorname',
            'Titel': 'titel',
            'Telefon': 'telefon',
            'Strasse': 'strasse',
            'PLZ': 'plz',
            'Ort': 'ort',
            'Adresszusatz': 'adresszusatz',
            'Bemerkung': 'bemerkung',
            'BHT': 'bht',
            'Erster_Termin': 'erster_termin',
            'Letzter_Termin': 'letzter_termin'
        }
        # Available SLK columns
        slk_columns = ['name', 'vorname', 'titel', 'telefon', 'strasse', 'plz', 'ort', 
                       'adresszusatz', 'bemerkung', 'bht', 'fallnummer', 'erster_termin', 'letzter_termin']
        # Create mapping interface
        column_mapping = {}
        for routemeister_col, default_slk_col in default_mapping.items():
            selected_col = st.selectbox(
                f"Map '{routemeister_col}' naar:",
                [''] + slk_columns,
                index=slk_columns.index(default_slk_col) + 1 if default_slk_col in slk_columns else 0
            )
            if selected_col:
                column_mapping[routemeister_col] = selected_col
    
    # Main content area
    st.header(t["preview"])
    
    if uploaded_file is not None:
        # Read file content
        # Probeer verschillende encodings voor Duitse karakters
        raw_content = uploaded_file.read()
        encodings_to_try = ['utf-8', 'cp1252', 'iso-8859-1', 'windows-1252']
        
        file_content = None
        for encoding in encodings_to_try:
            try:
                file_content = raw_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if file_content is None:
            file_content = raw_content.decode('utf-8', errors='ignore')
        
        # Parse SLK file
        with st.spinner(t["processing"]):
            df = parse_slk_patients(file_content)
        
        if not df.empty:
            st.success(t["success"])
            
            # Check op speciale tekens
            special_mask = df.applymap(has_special_chars)
            n_special = special_mask.values.sum()
            if n_special > 0:
                st.warning(t["warning_special"].format(n=n_special))
                st.dataframe(highlight_special_chars(df), use_container_width=True)
            else:
                st.dataframe(df.head(10), use_container_width=True)
            
            # Show column info
            with st.expander(t["found_columns"], expanded=False):
                for col in df.columns:
                    st.write(f"• {col}: {df[col].notna().sum()} waarden")
            
            # Convert to Routemeister format
            if column_mapping:
                st.subheader(t["output_data"])
                with st.spinner(t["converting"]):
                    # Extract RIT datum
                    rit_datum = extract_rit_datum(file_content)
                    if not rit_datum:
                        routemeister_df = convert_to_custom_format(df, '') # Pass empty string for rit_datum
                    else:
                        routemeister_df = convert_to_custom_format(df, rit_datum)
                    
                    # Clean data to remove illegal characters
                    routemeister_df = clean_dataframe(routemeister_df)
                
                if not routemeister_df.empty:
                    st.success(t["success"])
                    st.dataframe(routemeister_df.head(10).reset_index(drop=True), use_container_width=True, hide_index=True)
                    
                    # Download button
                    st.subheader(t["download"])
                    download_filename = f"converted_no_headers_{uploaded_file.name.replace('.slk', '.xlsx')}"
                    download_link = get_download_link(routemeister_df, download_filename, t["download"])
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                    # Show conversion summary
                    st.subheader("📈 Conversie Samenvatting")
                    st.write(f"• Input records: {len(df)}")
                    st.write(f"• Output records: {len(routemeister_df)}")
                    st.write(f"• Gemapte kolommen: {len(column_mapping)}")
                else:
                    st.error("❌ Conversie mislukt")
            else:
                st.info("⚙️ Configureer kolom mapping hierboven om output te zien")
        else:
            st.error(t["no_data"])
    else:
        st.info("👆 Upload een SLK bestand om te beginnen")
    
    # Footer
    st.markdown("---")
    st.markdown("**Gemaakt voor Meditec data conversie** | 📧 Voor vragen, neem contact op")

if __name__ == "__main__":
    main() 