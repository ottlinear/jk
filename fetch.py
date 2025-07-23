import re
import json
import requests

# ========== CONFIG ==========
remote_source = "https://raw.githubusercontent.com/alex4528/m3u/refs/heads/main/jstar.m3u"
cookie_file = "fetch.json"
playlist_file = "playlist.php"

print("🔄 STEP 1: Starting fetch from remote source")

# ========== 1. FETCH COOKIE FROM REMOTE ==========
try:
    response = requests.get(remote_source)
    response.raise_for_status()
    print("✅ STEP 2: Remote playlist fetched successfully")
except Exception as e:
    print(f"❌ Remote fetch error: {e}")
    exit(1)

print("🔍 STEP 3: Looking for #EXTHTTP JSON block")

match = re.search(r'#EXTHTTP:\s*(\{.*\})', response.text)
if not match:
    print("❌ STEP 3 Failed: No #EXTHTTP JSON block found in remote playlist.")
    exit(1)

try:
    cookie_json = json.loads(match.group(1))
    new_cookie = cookie_json["cookie"]
    print(f"✅ STEP 4: Extracted new cookie: {new_cookie[:10]}...")
except (json.JSONDecodeError, KeyError):
    print("❌ STEP 4 Failed: Invalid JSON or missing 'cookie' key.")
    exit(1)

with open(cookie_file, "w") as f:
    json.dump({"cookie": new_cookie}, f, indent=2)
print("💾 STEP 5: Cookie saved to fetch.json")

# ========== 2. LOAD playlist.php ==========
print("📂 STEP 6: Reading playlist.php")
try:
    with open(playlist_file, "r", encoding="utf-8") as f:
        playlist_content = f.read()
    print("✅ STEP 6: playlist.php loaded successfully")
except FileNotFoundError:
    print("❌ STEP 6 Failed: playlist.php not found.")
    exit(1)

# ========== 3. REPLACE ALL #EXTHTTP: LINES ==========
print("✏️ STEP 7: Replacing #EXTHTTP lines")
playlist_content = re.sub(
    r'^#EXTHTTP:.*$', f'#EXTHTTP:{{"cookie":"{new_cookie}"}}', playlist_content, flags=re.MULTILINE
)

# ========== 4. REPLACE OLD %7Ccookie= IN URLS ==========
print("🔁 STEP 8: Updating existing %7Ccookie= in URLs")
playlist_content = re.sub(
    r'(https?://[^\s"]+?)%7Ccookie=[^"\s|]*',
    r'\1%7Ccookie=' + new_cookie,
    playlist_content,
    flags=re.IGNORECASE
)

# ========== 5. ADD %7Ccookie= TO .mpd LINKS ==========
print("➕ STEP 9: Appending cookie to .mpd URLs without cookie")
playlist_content = re.sub(
    r'(https?://[^\s|"]+\.mpd)(?![^|"]*%7Ccookie=)',
    r'\1%7Ccookie=' + new_cookie,
    playlist_content,
    flags=re.IGNORECASE
)

# ========== 6. SAVE playlist.php ==========
print("💾 STEP 10: Saving updated playlist.php")
with open(playlist_file, "w", encoding="utf-8") as f:
    f.write(playlist_content)

print("✅ STEP 11: playlist.php updated successfully with new cookie!")
