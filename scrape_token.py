import requests
from bs4 import BeautifulSoup
import json
import sys

def scrape_google_token(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print("✅ Page fetched successfully. Status:", response.status_code, file=sys.stderr)
        print("Content length:", len(response.text), file=sys.stderr)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        raw_text = response.text.strip()
        
        print("\n--- First 300 chars ---", file=sys.stderr)
        print(raw_text[:300], file=sys.stderr)
        
        print("\n--- Last 300 chars ---", file=sys.stderr)
        print(raw_text[-300:], file=sys.stderr)
        
        # Try multiple extraction methods
        data = None
        
        # Method 1: JSON in <pre> tag
        pre = soup.find('pre')
        if pre:
            print("Found <pre> tag", file=sys.stderr)
            try:
                data = json.loads(pre.text.strip())
                print("✅ Extracted from <pre> tag", file=sys.stderr)
            except:
                pass
        
        # Method 2: Find JSON object in full text
        if not data:
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            if start != -1 and end > start + 10:
                json_str = raw_text[start:end]
                try:
                    data = json.loads(json_str)
                    print("✅ Extracted JSON from page text", file=sys.stderr)
                except json.JSONDecodeError as e:
                    print("JSON parse error:", e, file=sys.stderr)
        
        # Method 3: Try full response as JSON
        if not data:
            try:
                data = json.loads(raw_text)
                print("✅ Extracted from full response", file=sys.stderr)
            except:
                pass
        
        if data:
            print("✅ Token data found!", file=sys.stderr)
            if 'access_token' in data:
                print("Access token present (starts with):", data['access_token'][:20] + "...", file=sys.stderr)
            return data
        else:
            print("❌ No valid JSON found", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"Request error: {e}", file=sys.stderr)
        return None


def create_success_file_in_drive(access_token):
    url = "https://www.googleapis.com/drive/v3/files"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    metadata = {
        "name": "logged_success.txt",
        "mimeType": "text/plain"
    }
    
    try:
        response = requests.post(url, headers=headers, json=metadata, timeout=10)
        if response.status_code == 200:
            file_id = response.json().get('id')
            print(f"✅ SUCCESS: logged_success.txt created (ID: {file_id})")
            return True
        else:
            print(f"❌ Drive API failed: {response.status_code}", file=sys.stderr)
            print(response.text[:400], file=sys.stderr)
            return False
    except Exception as e:
        print(f"Drive error: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    url = "https://sprightly-jalebi-93b4cc.netlify.app/"
    data = scrape_google_token(url)
    
    if not data or 'access_token' not in data:
        print("❌ No access token found", file=sys.stderr)
        sys.exit(1)
    
    access_token = data['access_token']
    create_success_file_in_drive(access_token)
