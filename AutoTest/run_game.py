# 游戏卷轴修改后冒烟测试（一键执行 + Allure 报告）
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("    🧪 游戏卷轴修改后冒烟测试")
print("="*60)

# 执行测试并生成报告
os.system("pytest test_case/test_game_flow.py -v --alluredir=./reports --clean-alluredir")
os.system("allure serve ./reports")