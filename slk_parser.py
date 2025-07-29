import pandas as pd
import re
from typing import Dict, List, Tuple

def parse_slk_file(file_path: str) -> pd.DataFrame:
    """
    Parse SLK file and extract data into a structured format.
    """
    data = []
    current_row = {}
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
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
    df = df[available_columns]
    
    return df

def convert_to_routemeister_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the parsed data to the Routemeister format.
    Based on the sample Excel file, we need to create specific columns.
    """
    # Create a new DataFrame with the Routemeister format
    routemeister_df = pd.DataFrame()
    
    # Map the SLK data to Routemeister columns
    # Based on the sample, we need columns like: PT18007598, TS-RV-AHB, Mevilzen, Hansel, etc.
    
    # For now, let's create a basic mapping
    # You may need to adjust this based on your specific requirements
    
    routemeister_df['Patient_ID'] = df.get('fallnummer', '')
    routemeister_df['Name'] = df.get('name', '')
    routemeister_df['Vorname'] = df.get('vorname', '')
    routemeister_df['Telefon'] = df.get('telefon', '')
    routemeister_df['Strasse'] = df.get('strasse', '')
    routemeister_df['PLZ'] = df.get('plz', '')
    routemeister_df['Ort'] = df.get('ort', '')
    routemeister_df['Erster_Termin'] = df.get('erster_termin', '')
    routemeister_df['Letzter_Termin'] = df.get('letzter_termin', '')
    routemeister_df['Bemerkung'] = df.get('bemerkung', '')
    
    return routemeister_df

def main():
    # Parse the SLK file
    print("Parsing SLK file...")
    df = parse_slk_file('reha bonn.slk')
    
    print(f"Found {len(df)} records")
    print("Columns:", df.columns.tolist())
    print("\nFirst few rows:")
    print(df.head())
    
    # Convert to Routemeister format
    print("\nConverting to Routemeister format...")
    routemeister_df = convert_to_routemeister_format(df)
    
    print("\nRoutemeister format:")
    print(routemeister_df.head())
    
    # Save to Excel
    output_file = 'converted_routemeister.xlsx'
    routemeister_df.to_excel(output_file, index=False)
    print(f"\nSaved to {output_file}")

if __name__ == "__main__":
    main() 