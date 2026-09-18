
import codecs
import pandas as pd

def extract_breakdown():
    try:
        with codecs.open('houston_debug_breakdown_detailed.txt', 'r', 'utf-16le') as f:
            lines = f.readlines()
            
        start = -1
        for i, line in enumerate(lines):
            if "[VERIFICATION] Detailed Rows:" in line:
                start = i + 1
                break
        
        if start == -1:
            print("Could not find breakdown in log.")
            return

        print("DETAILED BREAKDOWN FROM LOG:")
        for i in range(start, start + 12):
            if i < len(lines):
                print(lines[i].strip())
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_breakdown()
