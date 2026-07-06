import requests
from bs4 import BeautifulSoup
import json
import sys

def scrape_google_token(url):
    """Scrape token from Netlify page (updated for current format)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # New primary method: direct JSON in <pre> or body
        text = soup.get_text(strip=True)
        
        # Try to find JSON object
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start != -1 and end > start:
            json_str = text[start:end]
            try:
                data = json.loads(json_str)
                print("✅ Token scraped successfully", file=sys.stderr)
                return data
            except json.JSONDecodeError:
                pass
        
        # Fallback: try full response text
        try:
            data = json.loads(response.text.strip())
            print("✅ Token scraped from raw response", file=sys.stderr)
            return data
        except:
            pass
            
    except Exception as e:
        print(f"Scraping error: {e}", file=sys.stderr)
    
    print("❌ Could not find token data", file=sys.stderr)
    return None


def create_success_file_in_drive(access_token):
    """Create empty logged_success.txt in Google Drive"""
    url = "https://www.googleapis.com/drive/v3/files"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    metadata = {
        "name": "logged_success.txt",
        "mimeType": "text/plain",
        "description": "GitHub Workflow auth test - " + "2026-07-06"
    }
    
    try:
        response = requests.post(url, headers=headers, json=metadata, timeout=10)
        
        if response.status_code == 200:
            file_id = response.json().get('id')
            print(f"✅ SUCCESS: logged_success.txt created (ID: {file_id})")
            return True
        else:
            print(f"❌ Drive API error {response.status_code}", file=sys.stderr)
            print(response.text[:500], file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"Drive request failed: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    url = "https://sprightly-jalebi-93b4cc.netlify.app/"
    
    data = scrape_google_token(url)
    if not data or 'access_token' not in data:
        print("❌ No access token found in data", file=sys.stderr)
        sys.exit(1)
    
    access_token = data['access_token']
    create_success_file_in_drive(access_token)
