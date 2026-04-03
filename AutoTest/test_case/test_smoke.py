import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/..")

import asyncio
import json
from urllib.parse import parse_qs
from common.request_sign import player_login, ACCOUNT_LIST, env, GAME_ID, CURRENT_ENV
from common.ws_smoke import play_smoke
import allure

def clean_smoke_report():
    if os.path.exists("./reports"):
        for f in os.listdir("./reports"):
            try:
                os.remove(os.path.join("./reports", f))
            except:
                pass

@allure.feature("游戏接口冒烟测试")
def test_smoke_full():
    clean_smoke_report()
    print("="*60)
    print("🔥 冒烟测试（正常+异常+边界）")
    print(f"环境：{CURRENT_ENV}  game_id：{GAME_ID}")
    print("="*60)

    account = ACCOUNT_LIST[0]
    print(f"\n🧪 测试账号：{account}")

    # ==========================
    # HTTP 登录：正常 + 异常 + 边界
    # ==========================
    # 正常
    resp = player_login(account)
    res = resp.json()
    code = res.get("resp_msg", {}).get("code", -1)
    print(f"\n[正常] HTTP code：{code}")
    assert code == 100, f"HTTP正常场景失败 code={code}"

    # 异常：无效账号
    resp_err = player_login("invalid_account_999")
    res_err = resp_err.json()
    code_err = res_err.get("resp_msg", {}).get("code", -1)
    print(f"[异常] HTTP code：{code_err}")
    assert code_err != 100

    # 边界：空账号
    resp_null = player_login("")
    res_null = resp_null.json()
    code_null = res_null.get("resp_msg", {}).get("code", -1)
    print(f"[边界] HTTP code：{code_null}")
    assert code_null != 100

    # 获取token
    url_str = res["resp_data"]["url"]
    token = parse_qs(url_str.split("?")[1])["token"][0]
    ws_url = env["url"].rstrip("/") + f"/{GAME_ID}"

    # WS 冒烟
    ok = asyncio.run(play_smoke(token, ws_url, account))
    assert ok, "冒烟测试不通过"

    print("\n🎉 所有接口冒烟测试：PASS")