import urllib.request
import os
import re
from pathlib import Path

# Load cookies from .env
env_file = Path("/Users/alex_mac/Sites/alexandrefroissart.github.io/.env")
cookies = ""
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith("ROOTME_COOKIES="):
                cookies = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

url = "https://www.root-me.org/fr/Challenges/Programmation/CAPTCHA-me-if-you-can"

print(f"DEBUG: Testing access to {url}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Cookie': cookies
}

req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        html = response.read().decode("utf-8")
        print(f"DEBUG: Status {response.status}")
        
        m_title = re.search(r'<title>(.*?)</title>', html)
        if m_title: print(f"Title: {m_title.group(1)}")
        
        # New regex for validations based on previous successful scrape (often near "Validations")
        # Trying a few patterns
        m_val = re.search(r'(\d+(?:[\s\.]\d+)*)\s*Validations', html)
        if m_val: 
            print(f"Validations: {m_val.group(1)}")
        else:
            # Fallback dump
            idx = html.find("Validations")
            if idx != -1: print(f"Snippet: {html[idx:idx+300]}")
        
        m_score = re.search(r'(\d+)&nbsp;Points', html)
        if m_score: print(f"Score: {m_score.group(1)}")

except Exception as e:
    print(f"❌ ERROR: {e}")
