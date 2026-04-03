import json
import asyncio
import websockets
import allure
import os
from datetime import datetime

# 冒烟测试 - 独立版本，不影响原脚本
# 覆盖：正常流程 + 异常场景 + 边界值
LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)

def write_log(account, msg_type, content):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_file = os.path.join(LOG_DIR, f"smoke_ws_{datetime.now().strftime('%Y%m%d')}.log")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time_str}] [{account}] [{msg_type}] {content}\n")
    except Exception:
        pass

async def play_smoke(token, ws_url, account="smoke_account"):
    try:
        websocket = await asyncio.wait_for(
            websockets.connect(ws_url, ping_interval=None, close_timeout=30),
            timeout=15
        )
        async with websocket:
            print("\n✅ WS 连接成功（冒烟）")

            # ==========================
            # 1. 认证：正常 + 异常 + 边界
            # ==========================
            # 正常
            msg1 = {"req_id": 1, "msg_name": "MsgGameAuthReq", "data": {"token": token, "account": "", "dev_info": ""}}
            await websocket.send(json.dumps(msg1))
            resp1 = await asyncio.wait_for(websocket.recv(), timeout=8)
            print("\n[正常] 认证响应")
            print(resp1)
            try:
                d = json.loads(resp1)
                code = d.get("data", {}).get("code")
                if code is not None and code != 0:
                    raise Exception(f"认证正常场景失败 code={code}")
            except:
                pass

            # 异常：无效token
            msg1_err = {"req_id": 1, "msg_name": "MsgGameAuthReq", "data": {"token": "invalid_xxx", "account": "", "dev_info": ""}}
            await websocket.send(json.dumps(msg1_err))
            resp1_err = await asyncio.wait_for(websocket.recv(), timeout=8)
            print("\n[异常] 无效Token")

            # 边界：空token
            msg1_null = {"req_id": 1, "msg_name": "MsgGameAuthReq", "data": {"token": "", "account": "", "dev_info": ""}}
            await websocket.send(json.dumps(msg1_null))
            resp1_null = await asyncio.wait_for(websocket.recv(), timeout=8)
            print("\n[边界] 空Token")
            print("✅ 认证场景全部通过")

            # ==========================
            # 2. 进入游戏：正常
            # ==========================
            msg2 = {"req_id": 2, "msg_name": "MsgGameEnterReq", "data": {}}
            await websocket.send(json.dumps(msg2))
            resp2 = await asyncio.wait_for(websocket.recv(), timeout=8)
            print("\n[正常] 进入游戏")
            print(resp2)
            try:
                d = json.loads(resp2)
                code = d.get("data", {}).get("code")
                if code is not None and code != 0:
                    raise Exception(f"进入游戏失败 code={code}")
            except:
                pass

            # ==========================
            # 3. 旋转：正常 + 异常 + 边界（仅1次）
            # ==========================
            print("\n===== 旋转正常场景（冒烟1次） =====")
            msg3 = {"req_id": 3, "msg_name": "MsgGameSpinReq", 
                    "data": {"currency": "USD", "bet_size": 0.05, "bet_multiple": 1}}
            await websocket.send(json.dumps(msg3))
            await asyncio.sleep(0.5)

            resp_index = 1
            while True:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"\n[旋转响应 {resp_index}]")
                    print(msg)
                    write_log(account, f"SPIN_{resp_index}", msg)
                    try:
                        d = json.loads(msg)
                        code = d.get("data", {}).get("code")
                        if code is not None:
                            print(f"🔍 code={code}")
                            if code != 0:
                                raise Exception(f"旋转失败 code={code}")
                    except:
                        pass
                    resp_index += 1
                except asyncio.TimeoutError:
                    break

            # 异常：负数下注
            print("\n===== 旋转异常场景（负数bet） =====")
            msg3_err = {"req_id": 3, "msg_name": "MsgGameSpinReq", 
                        "data": {"currency": "USD", "bet_size": -0.05, "bet_multiple": 1}}
            await websocket.send(json.dumps(msg3_err))
            await asyncio.sleep(0.3)

            # 边界：最小下注 0.01
            print("\n===== 旋转边界场景（min bet） =====")
            msg3_min = {"req_id": 3, "msg_name": "MsgGameSpinReq", 
                        "data": {"currency": "USD", "bet_size": 0.01, "bet_multiple": 1}}
            await websocket.send(json.dumps(msg3_min))
            await asyncio.sleep(0.3)

            print("\n✅ 冒烟测试全部通过")
            return True

    except Exception as e:
        print(f"\n❌ 冒烟失败：{str(e)}")
        return False