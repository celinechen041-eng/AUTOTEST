import hashlib
import time
import random
import string
import requests
import json

# ===================== 读取环境配置 =====================
def load_env():
    with open("config/env.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ===================== 读取游戏配置 =====================
def load_game_config():
    with open("config/game_config.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ===================== 读取玩家账号（第二行开始） =====================
def load_user_list():
    with open("config/user.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines[1:]

# ===================== 环境切换 =====================
CURRENT_ENV = "intranet"
env_data = load_env()
env = env_data[CURRENT_ENV]

# 游戏配置
GAME_CONFIG = load_game_config()

# 配置
ACCESS_KEY_ID = env["access_key_id"]
ACCESS_KEY_SECRET = env["access_key_secret"]
LOGIN_URL = env["login_url"]
GAME_ID = GAME_CONFIG["game_id"]

# 固定参数
LANGUAGE = "EN_US"
RETURN_URL = ""
PLAY_MODE = ""
ACCOUNT_LIST = load_user_list()

# ===================== 签名 =====================
def get_sign_headers():
    nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    timestamp = str(int(time.time()))
    sign_str = ACCESS_KEY_SECRET + nonce + timestamp
    sign = hashlib.sha1(sign_str.encode('utf-8')).hexdigest().lower()

    return {
        "AccessKeyId": ACCESS_KEY_ID,
        "AccessKeySecret": ACCESS_KEY_SECRET,
        "Nonce": nonce,
        "Timestamp": timestamp,
        "Sign": sign,
        "Content-Type": "application/json"
    }

# ===================== 登录 =====================
def player_login(account_id):
    headers = get_sign_headers()
    body = {
        "account_id": account_id,
        "game_id": GAME_ID,
        "language": LANGUAGE,
        "return_url": RETURN_URL,
        "play_mode": PLAY_MODE
    }
    return requests.post(LOGIN_URL, json=body, headers=headers, timeout=10)