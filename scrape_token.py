import requests
from bs4 import BeautifulSoup
import json
import re
import sys

def scrape_google_token(url):
    """Scrape the Google access token from Netlify page"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract token data
        for script in soup.find_all('script'):
            if script.string and 'ya29' in script.string:
                match = re.search(r'const data = (\{.*?\});', script.string, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
        
        # Fallback
        pre = soup.find('pre')
        if pre:
            return json.loads(pre.text.strip())
            
    except Exception as e:
        print(f"Scraping failed: {e}", file=sys.stderr)
    
    return None


def create_success_file_in_drive(access_token):
    """Create empty logged_success.txt in Google Drive root"""
    url = "https://www.googleapis.com/drive/v3/files"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    metadata = {
        "name": "logged_success.txt",
        "mimeType": "text/plain",
        "description": "Authentication test file - created via GitHub Workflow"
    }
    
    try:
        response = requests.post(url, headers=headers, json=metadata, timeout=10)
        
        if response.status_code == 200:
            file_id = response.json().get('id')
            print(f"✅ SUCCESS: logged_success.txt created (ID: {file_id})")
            return True
        else:
            print(f"❌ Failed to create file. Status: {response.status_code}", file=sys.stderr)
            print(response.text, file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"Error creating file: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    url = "https://sprightly-jalebi-93b4cc.netlify.app/"
    
    data = scrape_google_token(url)
    if not data or 'access_token' not in data:
        print("❌ No access token found", file=sys.stderr)
        sys.exit(1)
    
    access_token = data['access_token']
    create_success_file_in_drive(access_token)
