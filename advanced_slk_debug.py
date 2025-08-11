#!/usr/bin/env python3
import re

def analyze_slk_structure():
    """Gedetailleerde analyse van het SLK bestand om het umlaut probleem te vinden"""
    
    with open('reha bonn.slk', 'rb') as f:
        raw_data = f.read()
    
    # Probeer verschillende encodings
    encodings = ['utf-8', 'cp1252', 'iso-8859-1', 'windows-1252']
    
    print("=== ENCODING ANALYSE ===")
    for encoding in encodings:
        try:
            text_data = raw_data.decode(encoding)
            print(f"✓ {encoding}: {len(text_data)} karakters")
            
            # Zoek naar Harig en omgeving
            harig_pos = text_data.find('Harig')
            if harig_pos != -1:
                context = text_data[harig_pos-20:harig_pos+20]
                print(f"  Harig context: {repr(context)}")
                
            # Zoek naar Kubra en omgeving  
            kubra_pos = text_data.find('Kubra')
            if kubra_pos != -1:
                context = text_data[kubra_pos-20:kubra_pos+20]
                print(f"  Kubra context: {repr(context)}")
                
        except UnicodeDecodeError as e:
            print(f"✗ {encoding}: {e}")
    
    print("\n=== PARSER SIMULATIE ===")
    # Simuleer onze huidige parser
    text_data = raw_data.decode('utf-8', errors='ignore')
    
    last_row = None
    last_col = None
    found_names = []
    
    for line_num, line in enumerate(text_data.split('\n'), 1):
        line = line.strip()
        
        # Positie tracking
        pos_match = re.search(r'Y(\d+);X(\d+)', line)
        if pos_match:
            last_row = int(pos_match.group(1))
            last_col = int(pos_match.group(2))
            continue
            
        # Data extractie - focus op namen (kolom 4)
        if line.startswith('C;K') and last_row is not None and last_col is not None:
            if last_row >= 4 and last_col == 4:  # name kolom
                print(f"\nRegel {line_num}: {repr(line)}")
                print(f"Positie: Y{last_row};X{last_col}")
                
                # Huidige regex
                match = re.search(r'C;K"([^"]*)"', line)
                if match:
                    value = match.group(1)
                    print(f"Geëxtraheerde waarde: '{value}'")
                    print(f"Lengte: {len(value)} karakters")
                    
                    # Karakter analyse
                    for i, char in enumerate(value):
                        if ord(char) > 127 or ord(char) < 32:
                            print(f"  Speciaal karakter op pos {i}: '{char}' (ord={ord(char)}, hex={hex(ord(char))})")
                    
                    found_names.append((line_num, value))
                else:
                    print("GEEN MATCH met huidige regex")
    
    print(f"\n=== GEVONDEN NAMEN ({len(found_names)}) ===")
    for line_num, name in found_names:
        print(f"Regel {line_num}: '{name}'")
        if any(problematic in name for problematic in ['HN', 'KN', 'BIN', 'HH', 'KK']):
            print(f"  ⚠️  PROBLEMATISCH: {repr(name)}")

if __name__ == "__main__":
    analyze_slk_structure()
