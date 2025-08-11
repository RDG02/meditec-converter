#!/usr/bin/env python3
import re

def test_slk_parsing():
    with open('reha bonn.slk', 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    last_row = None
    last_col = None
    
    print("=== TEST SLK PARSING ===")
    
    for line_num, line in enumerate(file_content.split('\n'), 1):
        line = line.strip()
        
        # Check voor positie
        pos_match = re.search(r'Y(\d+);X(\d+)', line)
        if pos_match:
            last_row = int(pos_match.group(1))
            last_col = int(pos_match.group(2))
            continue
            
        # Check voor data - alleen voor namen (kolom 4 en 5)
        if line.startswith('C;K') and last_row is not None and last_col is not None:
            if last_row >= 4 and last_col in [4, 5]:  # name, vorname
                print(f"Regel {line_num}: {repr(line)} (Y{last_row};X{last_col})")
                
                # Probeer met quotes
                match = re.search(r'C;K"([^"]*)"', line)
                if match:
                    value = match.group(1)
                    print(f"  → Gevonden waarde: '{value}'")
                    if 'arig' in value or 'ubra' in value:
                        print(f"  → PROBLEMATISCH: {repr(value)}")
                        for i, char in enumerate(value):
                            print(f"    Char {i}: '{char}' (ord={ord(char)})")
                else:
                    print(f"  → GEEN MATCH")
                print()

if __name__ == "__main__":
    test_slk_parsing()
