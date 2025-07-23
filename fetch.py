import re
import json
import requests
import os

# ========== CONFIG ==========
remote_source = "https://raw.githubusercontent.com/alex4528/m3u/refs/heads/main/jstar.m3u"
cookie_file = "fetch.json"
playlist_file = "playlist.php"

print("🔄 STEP 1: Fetching remote playlist...")
try:
    response = requests.get(remote_source)
    response.raise_for_status()
    print("✅ STEP 1: Remote playlist fetched")
except Exception as e:
    print(f"❌ STEP 1: Failed to fetch remote playlist: {e}")
    exit(1)

# ========== 1. FETCH COOKIE FROM REMOTE ==========
match = re.search(r'#EXTHTTP:\s*(\{.*\})', response.text)
if not match:
    print("❌ STEP 2: No #EXTHTTP JSON block found in remote playlist.")
    exit(1)

try:
    cookie_json = json.loads(match.group(1))
    new_cookie = cookie_json['cookie']
    print(f"✅ STEP 3: Cookie extracted: {new_cookie[:10]}...")
except Exception as e:
    print(f"❌ STEP 3: Invalid JSON or 'cookie' key missing: {e}")
    exit(1)

with open(cookie_file, "w") as f:
    json.dump({"cookie": new_cookie}, f, indent=2)
print("💾 STEP 4: Cookie saved to fetch.json")

# ========== 2. LOAD playlist.php ==========
if not os.path.exists(playlist_file):
    print("❌ STEP 5: playlist.php not found.")
    exit(1)

with open(playlist_file, "r", encoding="utf-8") as f:
    playlist_content = f.read()
print("✅ STEP 5: playlist.php loaded")

# ========== 3. REPLACE ALL #EXTHTTP: LINES WITH NEW COOKIE ==========
playlist_content = re.sub(
    r'^#EXTHTTP:.*$', 
    f'#EXTHTTP:{{"cookie":"{new_cookie}"}}', 
    playlist_content, 
    flags=re.MULTILINE
)

# ========== 4. REPLACE OLD %7Ccookie= IN URLS WITH NEW COOKIE ==========
playlist_content = re.sub(
    r'(https?://[^\s"]+?)%7Ccookie=[^"\s|]*',
    r'\1%7Ccookie=' + new_cookie,
    playlist_content,
    flags=re.IGNORECASE
)

# ========== 5. ADD %7Ccookie= TO .mpd LINKS THAT DON'T HAVE IT ==========
playlist_content = re.sub(
    r'(https?://[^\s|"]+\.mpd)(?![^|"]*%7Ccookie=)',
    r'\1%7Ccookie=' + new_cookie,
    playlist_content,
    flags=re.IGNORECASE
)

# ========== 6. SAVE UPDATED playlist.php ==========
with open(playlist_file, "w", encoding="utf-8") as f:
    f.write(playlist_content)

print("✅ STEP 6: playlist.php updated with new cookie in all applicable places.")
