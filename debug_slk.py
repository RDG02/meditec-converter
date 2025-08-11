#!/usr/bin/env python3
import re

def debug_slk_parsing(file_path):
    """Debug SLK parsing om te zien wat er precies wordt gelezen"""
    
    # Probeer verschillende encodings
    encodings_to_try = ['utf-8', 'cp1252', 'iso-8859-1', 'windows-1252']
    
    file_content = None
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                file_content = file.read()
                print(f"✓ Bestand gelezen met encoding: {encoding}")
                break
        except UnicodeDecodeError:
            continue
    
    if file_content is None:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            file_content = file.read()
            print("⚠ Bestand gelezen met UTF-8 en errors='ignore'")
    
    last_row = None
    last_col = None
    patient_count = 0
    
    print("\n=== DEBUG: SLK Parsing ===")
    
    for line_num, line in enumerate(file_content.split('\n'), 1):
        line = line.strip()
        
        # Check voor positie
        pos_match = re.search(r'Y(\d+);X(\d+)', line)
        if pos_match:
            last_row = int(pos_match.group(1))
            last_col = int(pos_match.group(2))
            continue
            
        # Check voor data
        if line.startswith('C;K') and last_row is not None and last_col is not None:
            if last_row >= 4 and 2 <= last_col <= 14:
                # Debug: print de originele regel
                print(f"Regel {line_num}: {repr(line)} (Y{last_row};X{last_col})")
                
                # Probeer met quotes
                match = re.search(r'C;K"([^"]*)"', line)
                if match:
                    value = match.group(1)
                    print(f"  → Met quotes: '{value}' (len={len(value)})")
                    # Check voor speciale karakters
                    for i, char in enumerate(value):
                        if ord(char) > 127 or ord(char) < 32:
                            print(f"    Speciaal karakter op pos {i}: '{char}' (ord={ord(char)})")
                else:
                    # Probeer zonder quotes
                    match = re.search(r'C;K([0-9]+)$', line)
                    if match:
                        value = match.group(1)
                        print(f"  → Zonder quotes: '{value}'")
                    else:
                        print(f"  → GEEN MATCH!")
                
                # Check voor nieuwe patiënt
                if last_col == 2:
                    patient_count += 1
                    print(f"  → Nieuwe patiënt #{patient_count}")
                
                print()

if __name__ == "__main__":
    debug_slk_parsing("reha bonn.slk")
