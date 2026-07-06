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
        
        # Extract from <pre> tag
        pre = soup.find('pre')
        if pre:
            content = pre.get_text().strip()
            # Clean common issues
            content = re.sub(r'^\s*//.*$', '', content, flags=re.MULTILINE)  # remove comments
            content = re.sub(r',\s*}', '}', content)  # trailing commas
            content = re.sub(r',\s*]', ']', content)
            
            try:
                data = json.loads(content)
                print("✅ Successfully extracted from <pre> tag", file=sys.stderr)
                return data
            except json.JSONDecodeError:
                # Try regex extraction as fallback
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        print("✅ Extracted using regex cleanup", file=sys.stderr)
                        return data
                    except:
                        pass
        
        # Fallback: look for JSON in script
        script_content = None
        for script in soup.find_all('script'):
            if script.string and 'access_token' in script.string:
                script_content = script.string
                break
        
        if script_content:
            json_match = re.search(r'(\{[\s\S]*?\})', script_content)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    print("✅ Extracted from script tag", file=sys.stderr)
                    return data
                except:
                    pass
        
        print("❌ Failed to parse JSON", file=sys.stderr)
        return None
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def create_success_file_in_drive(access_token):
    url = "https://www.googleapis.com/drive/v3/files"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    metadata = {
        "name": "logged_success.txt",
        "mimeType": "text/plain",
        "description": "GitHub Workflow success test"
    }
    
    try:
        resp = requests.post(url, headers=headers, json=metadata, timeout=12)
        if resp.status_code == 200:
            file_id = resp.json().get('id')
            print(f"✅ SUCCESS: logged_success.txt created successfully (ID: {file_id})")
            return True
        else:
            print(f"❌ Drive API Error {resp.status_code}", file=sys.stderr)
            print(resp.text[:300], file=sys.stderr)
            return False
    except Exception as e:
        print(f"Drive request failed: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    url = "https://sprightly-jalebi-93b4cc.netlify.app/"
    data = scrape_google_token(url)
    
    if not data or 'access_token' not in data:
        print("❌ No access_token found in data", file=sys.stderr)
        sys.exit(1)
    
    print("🔑 Access token found, attempting Drive login...", file=sys.stderr)
    create_success_file_in_drive(data['access_token'])
