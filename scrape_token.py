import requests
from bs4 import BeautifulSoup
import json
import re
import sys

def scrape_google_token(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Primary method: Find script with token
        for script in soup.find_all('script'):
            if script.string and 'ya29' in script.string and 'token' in script.string:
                json_match = re.search(r'const data = (\{.*?\});', script.string, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(1))
                    print(json.dumps(data, indent=2))
                    return data
        
        # Fallback: pre tag
        pre = soup.find('pre')
        if pre and pre.text.strip():
            data = json.loads(pre.text.strip())
            print(json.dumps(data, indent=2))
            return data
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    
    print("❌ Could not extract token data", file=sys.stderr)
    return None

if __name__ == "__main__":
    url = "https://sprightly-jalebi-93b4cc.netlify.app/"
    scrape_google_token(url)
