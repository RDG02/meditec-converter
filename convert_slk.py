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
    return ''.join(c for c in str(val) if unicodedata.category(c)[0] != 'C')

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    return df.applymap(clean_value)

def extract_rit_datum(file_path: str) -> str:
    # Zoek naar Y2;X1
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        last_row = None
        last_col = None
        for line in file:
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

def parse_slk_patients(file_path: str) -> pd.DataFrame:
    # Per patient: Y4..Ymax, X2..X14
    patients = []
    current_patient = {}
    last_row = None
    last_col = None
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            line = line.strip()
            pos_match = re.search(r'Y(\d+);X(\d+)', line)
            if pos_match:
                last_row = int(pos_match.group(1))
                last_col = int(pos_match.group(2))
                continue
            if line.startswith('C;K') and last_row is not None and last_col is not None:
                if last_row >= 4 and 2 <= last_col <= 14:
                    match = re.search(r'C;K"([^"]*)"', line)
                    if match:
                        value = match.group(1)
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
    columns = [
        'PT18007598', 'TS-RV-AHB', 'Mevilzen', 'Hansel', 'M', '07.07.1985', 'Alst 6', 'Unnamed: 7',
        'Brüggen', '41379', 'D', '0049 215222111', 'Unnamed: 12', '15.01.2024', 'Unnamed: 14',
        '01.02.2025', 'KG1R', '800', '830'
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
            '',                               # KG1R (behandelcode, niet beschikbaar)
            '',                               # 800 (tijd start, niet beschikbaar)
            ''                                # 830 (tijd eind, niet beschikbaar)
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