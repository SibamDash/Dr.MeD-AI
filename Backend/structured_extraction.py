import re

def extract_lab_values(text):
    pattern = r"([A-Za-z\s\(\)]+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)-(\d+\.?\d*)"
    
    results = []
    
    matches = re.findall(pattern, text)
    
    for match in matches:
        test_name = match[0].strip()
        value = float(match[1])
        low = float(match[2])
        high = float(match[3])
        
        if value < low:
            status = "Low"
        elif value > high:
            status = "High"
        else:
            status = "Normal"
        
        results.append({
            "test": test_name,
            "value": value,
            "range": f"{low}-{high}",
            "status": status
        })
    
    return results