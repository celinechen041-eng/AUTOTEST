# 游戏卷轴修改后冒烟测试（高性能并发 + Allure账号同级 + 仅保留原始响应）
import asyncio
import json
from urllib.parse import parse_qs
import sys
import os
import pytest
import allure
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.request_sign import player_login, ACCOUNT_LIST, env, GAME_ID, CURRENT_ENV
from common.ws_game import play_game

def clean_old_report():
    if os.path.exists("./reports"):
        for f in os.listdir("./reports"):
            try:
                os.remove(os.path.join("./reports", f))
            except:
                pass

# 独立运行：每个账号自带独立allure上下文，不嵌套、不交叉、并发安全
def run_account_sync(account, index):
    with allure.step(f"账号：{account}"):
        try:
            print(f"\n==== 账号 {index}/{len(ACCOUNT_LIST)}: {account} ====")
            
            # 登录
            resp = player_login(account)
            res_data = resp.json() if resp.content else {}

            # ===================== 只附加【原始响应】到当前账号 =====================
            allure.attach(
                f"HTTP状态码：{resp.status_code}\n{json.dumps(res_data, ensure_ascii=False, indent=2)}",
                name=f"登录原始响应",
                attachment_type=allure.attachment_type.TEXT
            )

            # 校验HTTP状态
            assert resp.status_code == 200, f"HTTP请求失败：{resp.status_code}"

            # 业务code校验
            if "code" in res_data:
                code = res_data["code"]
                if code != 100:
                    msg = res_data.get("resp_msg", {}).get("message", "登录失败")
                    print(f"❌ [{account}] 登录失败：{msg}")
                    return False

            # 获取token
            url_str = res_data["resp_data"]["url"]
            query_params = parse_qs(url_str.split("?")[1])
            token = query_params["token"][0]

            # WS游戏
            ws_url = env["url"].rstrip("/") + f"/{GAME_ID}"
            ok = asyncio.run(play_game(token, ws_url, account))
            return ok

        except Exception as e:
            print(f"❌ [{account}] 异常：{str(e)}")
            return False

def test_batch_game_flow():
    clean_old_report()
    print("=" * 70)
    print(f"🧪 游戏卷轴冒烟测试 | 环境：{CURRENT_ENV} | 游戏ID：{GAME_ID}")
    print(f"👥 账号数：{len(ACCOUNT_LIST)} ｜ 多线程并发（高性能）")
    print("=" * 70)

    # 多线程 + 独立Allure上下文 = 绝对不嵌套 + 性能拉满
    with ThreadPoolExecutor(max_workers=len(ACCOUNT_LIST)) as executor:
        tasks = [executor.submit(run_account_sync, account, i+1) for i, account in enumerate(ACCOUNT_LIST)]
        results = [t.result() for t in tasks]

    success = sum(results)
    fail = len(results) - success

    print("\n" + "="*70)
    print(f"📊 测试完成：成功 {success} 个｜失败 {fail} 个")
    print("="*70)
    assert fail == 0, "存在失败账号"