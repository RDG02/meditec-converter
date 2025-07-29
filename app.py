import streamlit as st
import pandas as pd
import re
import io
from typing import Dict, List, Tuple
import base64

def parse_slk_file(file_content: str) -> pd.DataFrame:
    """
    Parse SLK file content and extract data into a structured format.
    """
    data = []
    current_row = {}
    
    lines = file_content.split('\n')
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and header lines
        if not line or line.startswith('ID;') or line.startswith('B;') or line.startswith('F;') or line.startswith('P;'):
            continue
            
        # Parse cell data (format: C;K"value")
        if line.startswith('C;K'):
            # Extract the value between quotes
            match = re.search(r'C;K"([^"]*)"', line)
            if match:
                value = match.group(1)
                
                # Find the position (X and Y coordinates)
                pos_match = re.search(r'Y(\d+);X(\d+)', line)
                if pos_match:
                    row = int(pos_match.group(1))
                    col = int(pos_match.group(2))
                    
                    # Map column numbers to meaningful names based on the SLK structure
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
                    
                    if col in column_mapping:
                        col_name = column_mapping[col]
                        
                        # Start new row if we encounter a new row number
                        if row not in current_row:
                            if current_row:  # Save previous row if exists
                                data.append(current_row)
                            current_row = {'row': row}
                        
                        current_row[col_name] = value
    
    # Add the last row
    if current_row:
        data.append(current_row)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Remove the 'row' column and reorder columns
    if 'row' in df.columns:
        df = df.drop('row', axis=1)
    
    # Reorder columns to match the expected output format
    expected_columns = ['name', 'vorname', 'titel', 'telefon', 'strasse', 'plz', 'ort', 
                       'adresszusatz', 'bemerkung', 'bht', 'fallnummer', 'erster_termin', 'letzter_termin']
    
    # Only include columns that exist in the data
    available_columns = [col for col in expected_columns if col in df.columns]
    if available_columns:
        df = df[available_columns]
    
    return df

def convert_to_routemeister_format(df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Convert the parsed data to the Routemeister format using custom column mapping.
    """
    routemeister_df = pd.DataFrame()
    
    # Apply the custom column mapping
    for routemeister_col, slk_col in column_mapping.items():
        if slk_col in df.columns:
            routemeister_df[routemeister_col] = df[slk_col]
        else:
            routemeister_df[routemeister_col] = ''
    
    return routemeister_df

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
        page_title="Meditec SLK naar Excel Converter",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Meditec SLK naar Excel Converter")
    st.markdown("---")
    
    # Sidebar for configuration
    st.sidebar.header("⚙️ Configuratie")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload SLK bestand",
        type=['slk', 'txt'],
        help="Selecteer een SLK bestand om te converteren"
    )
    
    # Column mapping configuration
    st.sidebar.subheader("📋 Kolom Mapping")
    st.sidebar.markdown("Configureer hoe de SLK kolommen moeten worden omgezet:")
    
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
        selected_col = st.sidebar.selectbox(
            f"Map '{routemeister_col}' naar:",
            [''] + slk_columns,
            index=slk_columns.index(default_slk_col) + 1 if default_slk_col in slk_columns else 0
        )
        if selected_col:
            column_mapping[routemeister_col] = selected_col
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📁 Input Data")
        
        if uploaded_file is not None:
            # Read file content
            file_content = uploaded_file.read().decode('utf-8', errors='ignore')
            
            # Parse SLK file
            with st.spinner("SLK bestand wordt geparsed..."):
                df = parse_slk_file(file_content)
            
            if not df.empty:
                st.success(f"✅ {len(df)} records gevonden!")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Show column info
                st.subheader("📊 Gevonden Kolommen")
                for col in df.columns:
                    st.write(f"• {col}: {df[col].notna().sum()} waarden")
            else:
                st.error("❌ Geen data gevonden in het SLK bestand")
        else:
            st.info("👆 Upload een SLK bestand om te beginnen")
    
    with col2:
        st.subheader("🔄 Output Data")
        
        if uploaded_file is not None and not df.empty and column_mapping:
            # Convert to Routemeister format
            with st.spinner("Data wordt geconverteerd..."):
                routemeister_df = convert_to_routemeister_format(df, column_mapping)
            
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
            if uploaded_file is None:
                st.info("👆 Upload een bestand om output te zien")
            elif not column_mapping:
                st.info("⚙️ Configureer kolom mapping in de sidebar")
    
    # Footer
    st.markdown("---")
    st.markdown("**Gemaakt voor Meditec data conversie** | 📧 Voor vragen, neem contact op")

if __name__ == "__main__":
    main() 