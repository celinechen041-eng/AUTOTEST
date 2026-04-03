# 游戏接口冒烟测试（独立脚本）
import os

print("="*60)
print("    🔥 游戏接口冒烟测试（独立脚本）")
print("="*60)

# 清理并生成报告
os.system("pytest test_case/test_smoke.py -v --alluredir=./reports --clean-alluredir")
os.system("allure serve ./reports")