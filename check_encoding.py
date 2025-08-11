#!/usr/bin/env python3

def check_slk_encoding():
    with open('reha bonn.slk', 'rb') as f:
        data = f.read()
    
    print("Zoeken naar bytes > 127 (niet-ASCII):")
    found_special = []
    for i, b in enumerate(data):
        if b > 127:
            context = data[max(0, i-10):i+15]
            found_special.append((i, b, context))
    
    print(f"Gevonden {len(found_special)} speciale bytes:")
    for pos, byte_val, context in found_special[:10]:  # Toon eerste 10
        print(f"Positie {pos}: byte {hex(byte_val)} ({byte_val})")
        print(f"  Context: {context}")
        print()

if __name__ == "__main__":
    check_slk_encoding()
