# 游戏卷轴修改后 - WebSocket 冒烟测试逻辑（高性能并发版）
import json
import asyncio
import websockets
import allure
import os
from datetime import datetime
from common.request_sign import GAME_CONFIG

LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)

def write_log(account, msg_type, content):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_file = os.path.join(LOG_DIR, f"game_ws_{datetime.now().strftime('%Y%m%d')}.log")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time_str}] [{account}] [{msg_type}] {content}\n")
    except Exception:
        pass

# WSS 统一校验：有 code 就必须 = 0，否则抛出异常 + 打印
def check_ws_code(data, account):
    if "code" in data:
        code = data["code"]
        if code != 0:
            msg = f"WSS业务异常 code={code}"
            print(f"❌ [{account}] {msg}")
            write_log(account, "ERROR", f"{msg} | 响应={data}")
            allure.attach(f"{msg}\n{json.dumps(data, ensure_ascii=False, indent=2)}", 
                          name=f"[{account}] WS异常", attachment_type=allure.attachment_type.TEXT)
            raise Exception(msg)

async def play_game(token, ws_url, account="test_account"):
    max_conn_retries = 2
    conn_retry_delay = 1

    for conn_retry in range(max_conn_retries):
        try:
            websocket = await asyncio.wait_for(
                websockets.connect(
                    ws_url,
                    ping_interval=None,
                    close_timeout=10,
                    max_size=None
                ),
                timeout=10
            )

            async with websocket:
                print(f"✅ [{account}] WebSocket 连接成功")
                allure.attach("WS连接成功", name=f"[{account}] WS状态", attachment_type=allure.attachment_type.TEXT)

                # 1 认证
                msg1 = {
                    "req_id": 1,
                    "msg_name": "MsgGameAuthReq",
                    "data": {"token": token, "account": "", "dev_info": ""}
                }
                await websocket.send(json.dumps(msg1))
                resp1 = await asyncio.wait_for(websocket.recv(), timeout=3)
                write_log(account, "AUTH", resp1)
                try:
                    data1 = json.loads(resp1)
                    check_ws_code(data1, account)
                except Exception as e:
                    print(f"❌ [{account}] 认证失败: {e}")
                    allure.attach(f"认证失败: {e}\n{resp1}", name=f"[{account}] 认证异常", attachment_type=allure.attachment_type.TEXT)
                    raise

                # 2 进入游戏
                msg2 = {
                    "req_id": 2,
                    "msg_name": "MsgGameEnterReq",
                    "data": {}
                }
                await websocket.send(json.dumps(msg2))
                resp2 = await asyncio.wait_for(websocket.recv(), timeout=3)
                write_log(account, "ENTER", resp2)
                try:
                    data2 = json.loads(resp2)
                    check_ws_code(data2, account)
                except Exception as e:
                    print(f"❌ [{account}] 进入游戏失败: {e}")
                    allure.attach(f"进入游戏失败: {e}\n{resp2}", name=f"[{account}] 进入游戏异常", attachment_type=allure.attachment_type.TEXT)
                    raise

                # 旋转
                total_spin = GAME_CONFIG["total_spin_count"]
                success_spin = 0
                fail_spin = 0
                win_total = 0.0

                print(f"🎯 [{account}] 开始 {total_spin} 次旋转")

                for spin_idx in range(1, total_spin + 1):
                    try:
                        msg3 = {
                            "req_id": 3,
                            "msg_name": "MsgGameSpinReq",
                            "data": {
                                "currency": GAME_CONFIG["currency"],
                                "bet_size": GAME_CONFIG["bet_size"],
                                "bet_multiple": GAME_CONFIG["bet_multiple"]
                            }
                        }
                        await websocket.send(json.dumps(msg3))
                        msg = await asyncio.wait_for(websocket.recv(), timeout=0.7)
                        write_log(account, f"SPIN_{spin_idx}", msg)

                        # ===================== 关键修复：code≠0 必捕获 =====================
                        data = json.loads(msg)
                        check_ws_code(data, account)  # 这里不会被吞掉

                        win = data.get("data", {}).get("win_gold", 0)
                        if win > 0:
                            win_total += float(win)

                        success_spin += 1
                        if spin_idx % 10 == 0:
                            print(f"✅ [{account}] 已完成 {spin_idx}/{total_spin} 次")

                    except Exception as e:
                        fail_spin += 1
                        err = f"第{spin_idx}次旋转失败：{str(e)}"
                        print(f"❌ [{account}] {err}")
                        allure.attach(err, name=f"[{account}] {err}", attachment_type=allure.attachment_type.TEXT)
                        continue

                # 统计
                stat = f"""
账号：{account}
总旋转：{total_spin}
成功：{success_spin}
失败：{fail_spin}
总赢金币：{win_total:.2f}
"""
                print(stat)
                write_log(account, "STAT", stat)
                allure.attach(stat, name=f"【{account}】最终统计", attachment_type=allure.attachment_type.TEXT)
                return True

        except Exception as e:
            err_msg = f"[{account}] 连接/流程失败：{str(e)}"
            print(f"❌ {err_msg}")
            write_log(account, "ERROR", err_msg)
            allure.attach(err_msg, name=f"[{account}] WS连接/初始化失败", attachment_type=allure.attachment_type.TEXT)
            await asyncio.sleep(conn_retry_delay)

    final_err = f"[{account}] 流程最终失败"
    print(f"❌ [{final_err}")
    allure.attach(final_err, name=f"[{account}] 最终失败", attachment_type=allure.attachment_type.TEXT)
    return False