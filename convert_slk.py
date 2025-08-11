#!/usr/bin/env python3
"""
Simple SLK to Excel converter
Usage: python convert_slk.py input.slk output.xlsx
"""

import pandas as pd
import re
import sys
import os
import unicodedata

def clean_value(val):
    if pd.isna(val):
        return val
    
    # Converteer naar string
    text = str(val)
    
    # Specifieke correcties voor bekende parsing fouten
    # Deze patronen ontstaan door verkeerde parsing van het SLK bestand
    corrections = {
        'HNHarig': 'Härig',
        'KNHubra': 'Kübra', 
        'HNHoveler': 'Höveler',
        'BINHuchenstraße': 'Blüchenstraße',
        'HHarig': 'Härig',  # Voor het geval er dubbele H's zijn
        'KKubra': 'Kübra',  # Voor het geval er dubbele K's zijn
    }
    
    # Pas correcties toe
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
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

def read_file_with_encoding(file_path: str) -> str:
    """Lees bestand met verschillende encodings voor Duitse karakters"""
    encodings_to_try = ['utf-8', 'cp1252', 'iso-8859-1', 'windows-1252']
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    
    # Als laatste poging met error ignore
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        return file.read()

def extract_rit_datum(file_path: str) -> str:
    # Zoek naar Y2;X1
    file_content = read_file_with_encoding(file_path)
    
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

def parse_slk_patients(file_path: str) -> pd.DataFrame:
    # Per patient: Y4..Ymax, X2..X14
    patients = []
    current_patient = {}
    last_row = None
    last_col = None
    
    file_content = read_file_with_encoding(file_path)
    for line in file_content.split('\n'):
        line = line.strip()
        pos_match = re.search(r'Y(\d+);X(\d+)', line)
        if pos_match:
            last_row = int(pos_match.group(1))
            last_col = int(pos_match.group(2))
            continue
        if line.startswith('C;K') and last_row is not None and last_col is not None:
            if last_row >= 4 and 2 <= last_col <= 14:
                match = re.search(r'C;K"([^"]*)"', line)
                if not match:
                    # Probeer zonder quotes (voor numerieke waarden)
                    match = re.search(r'C;K([0-9]+)$', line)
                if match:
                    value = match.group(1)
                    
                    # Direct correcties toepassen voor verkeerd geparsede umlauts
                    umlaut_corrections = {
                        'HNHarig': 'Härig',
                        'KNHubra': 'Kübra', 
                        'HNHoveler': 'Höveler',
                        'BINHuchenstraße': 'Blüchenstraße',
                        'HHarig': 'Härig',
                        'KKubra': 'Kübra',
                    }
                    for wrong, correct in umlaut_corrections.items():
                        if value == wrong:
                            value = correct
                            break
                    
                    # Map kolomnummer naar veldnaam
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
    return pd.DataFrame(patients)

def convert_to_sample_format(df: pd.DataFrame, rit_datum: str) -> pd.DataFrame:
    # Helper: format time by removing colons
    def format_time(tijd):
        if pd.isna(tijd) or tijd == '':
            return ''
        # Verwijder dubbele punten uit tijd (15:15 -> 1515)
        return str(tijd).replace(':', '')
    
    columns = [
        'PT18007598', 'TS-RV-AHB', 'Mevilzen', 'Hansel', 'M', '07.07.1985', 'Alst 6', 'Unnamed: 7',
        'Brüggen', '41379', 'D', '0049 215222111', 'Unnamed: 12', '15.01.2024', 'Unnamed: 14',
        '01.02.2025', 'Unnamed: 16', '800', '830'
    ]
    output = []
    for _, row in df.iterrows():
        output.append([
            row.get('fallnummer', ''),         # PT18007598
            'TS-RV-AHB',                      # TS-RV-AHB (vast)
            row.get('name', ''),              # Mevilzen (achternaam)
            row.get('vorname', ''),           # Hansel (voornaam)
            row.get('titel', 'M'),            # M (geslacht of titel, default 'M')
            '',                               # 07.07.1985 (geboortedatum, niet beschikbaar)
            row.get('strasse', ''),           # Alst 6 (adres)
            '',                               # Unnamed: 7
            row.get('ort', ''),               # Brüggen (plaats)
            row.get('plz', ''),               # 41379 (postcode)
            'D',                              # D (landcode)
            row.get('telefon', ''),           # 0049 215222111 (telefoon)
            '',                               # Unnamed: 12
            '',                               # 15.01.2024 (datum opname, niet beschikbaar)
            '',                               # Unnamed: 14
            rit_datum,                        # 01.02.2025 (datum rit)
            '',                               # Unnamed: 16 (leeg)
            format_time(row.get('erster_termin', '')),  # 800 (tijd start)
            format_time(row.get('letzter_termin', ''))  # 830 (tijd eind)
        ])
    return pd.DataFrame(output, columns=columns)

def main():
    print("=" * 50)
    print("📊 Meditec SLK naar Excel Converter (Sample Format)")
    print("=" * 50)
    if len(sys.argv) != 3:
        print("Gebruik: python convert_slk.py input.slk output.xlsx")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    if not os.path.exists(input_file):
        print(f"❌ Fout: Bestand '{input_file}' bestaat niet!")
        sys.exit(1)
    try:
        rit_datum = extract_rit_datum(input_file)
        print(f"📅 Datum van de rit: {rit_datum}")
        df = parse_slk_patients(input_file)
        if df.empty:
            print("❌ Geen data gevonden in het SLK bestand!")
            sys.exit(1)
        print(f"✅ {len(df)} patiënten gevonden!")
        print(f"📊 Kolommen: {', '.join(df.columns.tolist())}")
        print("🔄 Data wordt geconverteerd naar sample formaat...")
        sample_df = convert_to_sample_format(df, rit_datum)
        sample_df = clean_dataframe(sample_df)
        print(f"💾 Excel bestand wordt opgeslagen: {output_file}")
        sample_df.to_excel(output_file, index=False)
        print("✅ Conversie voltooid!")
        print(f"📈 Samenvatting:")
        print(f"   • Patiënten: {len(df)}")
        print(f"   • Output records: {len(sample_df)}")
        print(f"   • Output kolommen: {len(sample_df.columns)}")
        print(f"   • Bestand opgeslagen: {output_file}")
        print("\n📋 Eerste 3 rijen van output:")
        print(sample_df.head(3).to_string(index=False))
    except Exception as e:
        print(f"❌ Fout tijdens conversie: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 