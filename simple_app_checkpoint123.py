import streamlit as st
import pandas as pd
import re
import io
import unicodedata
from typing import Dict, List, Tuple
import base64

# Simple SLK to Excel converter app

def clean_value(val):
    if pd.isna(val):
        return val
    return ''.join(c for c in str(val) if unicodedata.category(c)[0] != 'C')

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
                return match.group(1)
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
                # Accepteer zowel C;K"waarde" als C;Kwaarde
                match = re.search(r'C;K"([^"]*)"|C;K([^\"]+)$', line)
                if match:
                    value = match.group(1) if match.group(1) is not None else match.group(2)
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

    columns = [
        'patient ID', 'leeg1', 'Name', 'vorname', 'leeg2', 'leeg3', 'adres+huisnummer', 'leeg4',
        'ort', 'PLZ', 'landcode', 'telefoonnummer', '2e telefoonnummer', 'leeg5', 'leeg6',
        'datum van de rit', 'eerst behandeling', 'laatste behandeling'
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
            row.get('strasse', ''),   # 7 adres+huisnummer
            '',                       # 8 leeg
            row.get('ort', ''),       # 9 ort (plaatsnaam)
            row.get('plz', ''),       # 10 PLZ (postcode)
            landcode,                 # 11 landcode
            hoofd,                    # 12 telefoonnummer
            tweede,                   # 13 2e telefoonnummer
            '',                       # 14 leeg
            '',                       # 15 leeg
            rit_datum,                # 16 datum van de rit
            row.get('erster_termin', ''), # 17 eerst behandeling
            row.get('letzter_termin', '') # 18 laatste behandeling
        ])
    return pd.DataFrame(output, columns=columns)

def get_download_link(df: pd.DataFrame, filename: str, text: str):
    """Generate a download link for the DataFrame."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{text}</a>'
    return href

def main():
    st.set_page_config(
        page_title="Routemeister converter tool",
        page_icon="📊",
        layout="wide"
    )

    # Logo bovenaan
    st.image("Routemeister_Logo_White_BG_Larger.png", width=220)
    st.markdown("""
    # Routemeister converter tool:
    **Meditec Export Reha Bonn  > Routemeister import**
    """)
    st.markdown("---")
    
    # File upload
    st.header("📁 Upload SLK Bestand")
    uploaded_file = st.file_uploader(
        "Selecteer een SLK bestand om te converteren",
        type=['slk', 'txt'],
        help="Selecteer een SLK bestand om te converteren"
    )
    
    # Column mapping configuration
    with st.expander("⚙️ Kolom Mapping Configuratie (optioneel)", expanded=False):
        st.markdown("Configureer hoe de SLK kolommen moeten worden omgezet:")
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
    st.header("📊 Data Preview")
    
    if uploaded_file is not None:
        # Read file content
        file_content = uploaded_file.read().decode('utf-8', errors='ignore')
        
        # Parse SLK file
        with st.spinner("SLK bestand wordt geparsed..."):
            df = parse_slk_patients(file_content)
        
        if not df.empty:
            st.success(f"✅ {len(df)} records gevonden!")
            
            # Show input data
            st.subheader("📁 Input Data (SLK)")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Show column info
            with st.expander("📊 Gevonden Kolommen", expanded=False):
                for col in df.columns:
                    st.write(f"• {col}: {df[col].notna().sum()} waarden")
            
            # Convert to Routemeister format
            if column_mapping:
                st.subheader("🔄 Output Data (Excel)")
                with st.spinner("Data wordt geconverteerd..."):
                    # Extract RIT datum
                    rit_datum = extract_rit_datum(file_content)
                    if not rit_datum:
                        st.warning("Waarschuwing: Geen RIT datum gevonden in het SLK bestand. De output zal geen datum bevatten.")
                        routemeister_df = convert_to_custom_format(df, '') # Pass empty string for rit_datum
                    else:
                        routemeister_df = convert_to_custom_format(df, rit_datum)
                
                if not routemeister_df.empty:
                    st.success("✅ Conversie voltooid!")
                    st.dataframe(routemeister_df.head(10), use_container_width=True)
                    
                    # Download button
                    st.subheader("💾 Download")
                    download_filename = f"converted_{uploaded_file.name.replace('.slk', '.xlsx')}"
                    download_link = get_download_link(routemeister_df, download_filename, "📥 Download Excel bestand")
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
            st.error("❌ Geen data gevonden in het SLK bestand")
    else:
        st.info("👆 Upload een SLK bestand om te beginnen")
    
    # Footer
    st.markdown("---")
    st.markdown("**Gemaakt voor Meditec data conversie** | 📧 Voor vragen, neem contact op")

if __name__ == "__main__":
    main() 