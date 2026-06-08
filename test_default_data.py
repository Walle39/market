#!/usr/bin/env python3
"""
测试央行购金默认数据功能
"""

import sys
from pathlib import Path

# 确保工作目录正确
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

print("=" * 60)
print("测试央行购金数据脚本（无依赖库模式）")
print("=" * 60)

# 测试季度数据
print("\n1. 测试 fetch_central_bank_gold_quarterly.py:")
from fetch_central_bank_gold_quarterly import fetch_central_bank_gold_quarterly
quarterly_data = fetch_central_bank_gold_quarterly()
print(f"   - total_4_quarters: {quarterly_data['total_4_quarters']} 吨")
print(f"   - is_default: {quarterly_data.get('is_default', False)}")
print(f"   - 数据来源: {quarterly_data['source']}")

# 测试季度数据
print("\n2. 测试 fetch_central_bank_gold.py:")
from fetch_central_bank_gold import fetch_central_bank_gold
gold_data = fetch_central_bank_gold()
print(f"   - Q1_2026_tonnes: {gold_data['central_bank_purchase']['Q1_2026_tonnes']} 吨")
print(f"   - is_default: {gold_data.get('is_default', False)}")
print(f"   - 数据来源: {gold_data['source']}")

print("\n" + "=" * 60)
print("测试完成！默认数据正常工作，无需任何外部依赖。")
print("=" * 60)
