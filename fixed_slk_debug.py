#!/usr/bin/env python3
import re

def debug_parser_step_by_step():
    """Stap-voor-stap debug van de SLK parser"""
    
    with open('reha bonn.slk', 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    print("=== STAP-VOOR-STAP PARSER DEBUG ===")
    
    last_row = None
    last_col = None
    patient_count = 0
    
    for line_num, line in enumerate(file_content.split('\n'), 1):
        original_line = line
        line = line.strip()
        
        # Skip lege regels
        if not line:
            continue
            
        # Check voor positie
        pos_match = re.search(r'Y(\d+);X(\d+)', line)
        if pos_match:
            last_row = int(pos_match.group(1))
            last_col = int(pos_match.group(2))
            if last_row >= 4 and 2 <= last_col <= 14:
                print(f"Regel {line_num}: Nieuwe positie Y{last_row};X{last_col}")
            continue
            
        # Check voor data
        if line.startswith('C;K'):
            print(f"Regel {line_num}: Data regel: {repr(line)}")
            print(f"  Huidige positie: Y{last_row};X{last_col}")
            
            if last_row is not None and last_col is not None:
                if last_row >= 4 and 2 <= last_col <= 14:
                    print(f"  ✓ Binnen data bereik")
                    
                    # Probeer regex
                    match = re.search(r'C;K"([^"]*)"', line)
                    if match:
                        value = match.group(1)
                        print(f"  ✓ Waarde gevonden: '{value}'")
                        
                        # Check voor nieuwe patiënt
                        if last_col == 2:
                            patient_count += 1
                            print(f"  → Nieuwe patiënt #{patient_count}")
                        
                        # Toon kolom mapping
                        column_names = {
                            2: 'erster_termin', 3: 'letzter_termin', 4: 'name', 5: 'vorname',
                            6: 'titel', 7: 'telefon', 8: 'strasse', 9: 'plz', 10: 'ort',
                            11: 'adresszusatz', 12: 'bemerkung', 13: 'bht', 14: 'fallnummer'
                        }
                        col_name = column_names.get(last_col, f'col_{last_col}')
                        print(f"  → Kolom: {col_name}")
                        
                        # Highlight interessante waarden
                        if 'arig' in value.lower() or 'ubra' in value.lower():
                            print(f"  🔍 INTERESSANT: {repr(value)}")
                            for i, char in enumerate(value):
                                print(f"    Pos {i}: '{char}' (ord={ord(char)})")
                        
                    else:
                        print(f"  ✗ Geen match met regex")
                        # Probeer zonder quotes
                        match2 = re.search(r'C;K([0-9]+)$', line)
                        if match2:
                            value = match2.group(1)
                            print(f"  ✓ Numerieke waarde: '{value}'")
                else:
                    print(f"  - Buiten data bereik")
            else:
                print(f"  - Geen positie bekend")
            print()

if __name__ == "__main__":
    debug_parser_step_by_step()
