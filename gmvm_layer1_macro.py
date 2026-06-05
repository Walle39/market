#!/usr/bin/env python3
"""
GMVM v6.1 Layer 1: 宏观驱动信号层 (S_macro)
计算宏观因子编码并输出综合信号

因子权重:
- 央行购金代理: 30%
- M2高频预估: 25%
- 债务/GDP: 15%
- Fed量化预期差: 15%
- 10Y TIPS实际利率: 10%
- 美元指数 DXY: 5%
"""

import sys
import os
sys.path.insert(0, '/workspace')

import json
from datetime import datetime
import requests

# 导入现有脚本
from fetch_central_bank_gold_quarterly import fetch_central_bank_gold_quarterly
from fetch_usa_m2 import fetch_fred_m2
from fetch_us_debt_gdp import fetch_us_debt_gdp
from fetch_us_bond_tips import fetch_bond_data
from fetch_dxy_index import fetch_dxy_index
from fetch_gold_technical import fetch_gold_current_price

# 手动输入的Fed预期编码 (-1=鹰派加息, 0=中性, 1=鸽派降息)
# 可以通过环境变量或配置文件设置
MANUAL_FED_EXPECTATION = None  # None表示自动获取，-1/0/1表示手动设置

def get_fed_expectation_input():
    """
    获取Fed预期编码
    优先级:
    1. 环境变量 MANUAL_FED_EXPECTATION
    2. 手动输入 (标准输入)
    3. TIPS实际利率作为备用
    """
    # 1. 检查环境变量
    if MANUAL_FED_EXPECTATION is not None:
        return MANUAL_FED_EXPECTATION, "环境变量设置"

    # 2. 提示手动输入
    print("\n" + "=" * 50)
    print("Fed预期编码选择 (跳过请按回车使用TIPS备用)")
    print("=" * 50)
    print("  -1 = 鹰派 (加息预期)")
    print("   0 = 中性 (预期不变)")
    print("  +1 = 鸽派 (降息预期)")
    print("=" * 50)

    try:
        user_input = input("请输入Fed预期编码 (-1/0/1): ").strip()
        if user_input in ['-1', '0', '1']:
            return int(user_input), "手动输入"
    except EOFError:
        pass  # 非交互环境，跳过

    # 3. 返回None表示使用TIPS备用
    return None, "将使用TIPS备用"

def encode_fed_expectation_tips(tips_value):
    """
    使用TIPS实际利率作为Fed预期代理
    +1: 未来6个月隐含累计降息 >50bp (TIPS < -0.5%)
    0: 预期变动介于 -50bp ~ +50bp (TIPS -0.5% ~ 1.5%)
    -1: 隐含加息或鹰派重定价 (TIPS > 1.5%)
    """
    if tips_value is None:
        return None, "TIPS数据不可用"

    if tips_value < -0.5:
        return 1, f"Fed鸽派预期 (TIPS: {tips_value:.2f}% < -0.5%)"
    elif tips_value > 1.5:
        return -1, f"Fed鹰派预期 (TIPS: {tips_value:.2f}% > 1.5%)"
    else:
        return 0, f"Fed中性预期 (TIPS: {tips_value:.2f}% in -0.5%~1.5%)"

def encode_central_bank_gold(total_4q):
    """
    央行购金代理编码
    +1: 近12个月滚动购金 > 900吨
    0: 600~900吨
    -1: <600吨
    """
    if total_4q > 900:
        return 1, "购金强劲 (>900吨)"
    elif total_4q >= 600:
        return 0, "购金正常 (600-900吨)"
    else:
        return -1, "购金疲弱 (<600吨)"

def encode_m2_yoy(yoy_change_pct):
    """
    M2高频预估编码
    +1: 同比 > 6%
    0: 同比 0%~6%
    -1: 同比 < 0%
    """
    if yoy_change_pct is None:
        return 0, "数据不可用"
    if yoy_change_pct > 6:
        return 1, f"M2增长强劲 ({yoy_change_pct:.1f}% > 6%)"
    elif yoy_change_pct >= 0:
        return 0, f"M2增长正常 ({yoy_change_pct:.1f}% in 0-6%)"
    else:
        return -1, f"M2收缩 ({yoy_change_pct:.1f}% < 0%)"

def encode_debt_gdp(debt_to_gdp_pct):
    """
    债务/GDP编码
    +1: >120%
    0: 100%~120%
    -1: <100%
    """
    if debt_to_gdp_pct > 120:
        return 1, f"债务极高 ({debt_to_gdp_pct:.1f}% > 120%)"
    elif debt_to_gdp_pct >= 100:
        return 0, f"债务偏高 ({debt_to_gdp_pct:.1f}% in 100-120%)"
    else:
        return -1, f"债务可控 ({debt_to_gdp_pct:.1f}% < 100%)"

def encode_fed_expectation_manual(fed_code):
    """
    根据手动输入的Fed预期编码返回结果
    +1: 鸽派 (降息预期)
    0: 中性 (预期不变)
    -1: 鹰派 (加息预期)
    """
    if fed_code == 1:
        return 1, "Fed鸽派预期 (降息)"
    elif fed_code == -1:
        return -1, "Fed鹰派预期 (加息)"
    else:
        return 0, "Fed中性预期 (不变)"

def encode_tips(tips_value):
    """
    10Y TIPS实际利率编码
    +1: < -0.5%
    0: -0.5% ~ +1.5%
    -1: > 1.5%
    """
    if tips_value is None:
        return 0, "数据不可用"
    if tips_value < -0.5:
        return 1, f"负实际利率 ({tips_value:.2f}% < -0.5%)"
    elif tips_value > 1.5:
        return -1, f"高实际利率 ({tips_value:.2f}% > 1.5%)"
    else:
        return 0, f"正常实际利率 ({tips_value:.2f}% in -0.5%~1.5%)"

def encode_dxy(dxy_value):
    """
    美元指数DXY编码
    +1: <95 (美元弱势)
    0: 95~105
    -1: >105 (美元强势)
    """
    if dxy_value is None:
        return 0, "数据不可用"
    if dxy_value < 95:
        return 1, f"美元弱势 (DXY: {dxy_value:.2f} < 95)"
    elif dxy_value > 105:
        return -1, f"美元强势 (DXY: {dxy_value:.2f} > 105)"
    else:
        return 0, f"美元中性 (DXY: {dxy_value:.2f} in 95-105)"

def calculate_s_macro():
    """计算宏观驱动信号层 S_macro"""
    print("=" * 60)
    print("GMVM v6.1 Layer 1: 宏观驱动信号层 (S_macro)")
    print("=" * 60)

    result = {
        "layer": "S_macro",
        "timestamp": datetime.now().isoformat(),
        "factors": {},
        "weights": {
            "central_bank_gold": 0.30,
            "m2": 0.25,
            "debt_gdp": 0.15,
            "fed_expectation": 0.15,
            "tips": 0.10,
            "dxy": 0.05
        },
        "encoding": {},
        "s_macro": None,
        "signal": None
    }

    # 1. 央行购金代理 (30%)
    try:
        cb_gold_data = fetch_central_bank_gold_quarterly()
        if cb_gold_data and 'total_4_quarters' in cb_gold_data:
            total_4q = cb_gold_data['total_4_quarters']
            enc, desc = encode_central_bank_gold(total_4q)
            result['factors']['central_bank_gold'] = {
                'total_4q': total_4q,
                'encoding': enc,
                'description': desc
            }
            result['encoding']['central_bank_gold'] = enc
        else:
            result['factors']['central_bank_gold'] = {'error': '数据不可用'}
            result['encoding']['central_bank_gold'] = 0
    except Exception as e:
        print(f"央行购金数据获取失败: {e}")
        result['factors']['central_bank_gold'] = {'error': str(e)}
        result['encoding']['central_bank_gold'] = 0

    # 2. M2高频预估 (25%)
    try:
        m2_data = fetch_fred_m2()
        if m2_data and 'yoy_change_percent' in m2_data:
            yoy = m2_data['yoy_change_percent']
            enc, desc = encode_m2_yoy(yoy)
            result['factors']['m2'] = {
                'yoy_change': yoy,
                'encoding': enc,
                'description': desc
            }
            result['encoding']['m2'] = enc
        else:
            result['factors']['m2'] = {'error': '数据不可用'}
            result['encoding']['m2'] = 0
    except Exception as e:
        print(f"M2数据获取失败: {e}")
        result['factors']['m2'] = {'error': str(e)}
        result['encoding']['m2'] = 0

    # 3. 债务/GDP (15%)
    try:
        debt_gdp_data = fetch_us_debt_gdp()
        if debt_gdp_data and 'debt_to_gdp_ratio' in debt_gdp_data:
            ratio = debt_gdp_data['debt_to_gdp_ratio']['value']
            enc, desc = encode_debt_gdp(ratio)
            result['factors']['debt_gdp'] = {
                'ratio': ratio,
                'encoding': enc,
                'description': desc
            }
            result['encoding']['debt_gdp'] = enc
        else:
            result['factors']['debt_gdp'] = {'error': '数据不可用'}
            result['encoding']['debt_gdp'] = 0
    except Exception as e:
        print(f"债务/GDP数据获取失败: {e}")
        result['factors']['debt_gdp'] = {'error': str(e)}
        result['encoding']['debt_gdp'] = 0

    # 4. Fed量化预期差 (15%)
    # 尝试verifiedinvesting.com获取，与TIPS比较，不一致时提示手动输入
    try:
        # 获取TIPS值
        bond_data = fetch_bond_data()
        tips_value = None
        if bond_data and 'data' in bond_data:
            if 'tips_10y' in bond_data['data']:
                tips_value = bond_data['data']['tips_10y']['latest']['value']

        # 获取Fed预期（手动输入或TIPS备用）
        fed_code, input_source = get_fed_expectation_input()

        if fed_code is not None:
            # 使用手动输入或环境变量
            enc, desc = encode_fed_expectation_manual(fed_code)
            result['factors']['fed_expectation'] = {
                'source': input_source,
                'manual_code': fed_code,
                'encoding': enc,
                'description': desc
            }
            result['encoding']['fed_expectation'] = enc
        else:
            # 使用TIPS备用
            enc, desc = encode_fed_expectation_tips(tips_value)
            result['factors']['fed_expectation'] = {
                'source': 'TIPS备用',
                'tips_value': tips_value,
                'encoding': enc,
                'description': desc
            }
            result['encoding']['fed_expectation'] = enc
    except Exception as e:
        print(f"Fed预期数据获取失败: {e}")
        result['factors']['fed_expectation'] = {'error': str(e)}
        result['encoding']['fed_expectation'] = 0

    # 5. 10Y TIPS实际利率 (10%)
    try:
        if 'tips_value' not in result['factors']['fed_expectation']:
            tips_value = None
        else:
            tips_value = result['factors']['fed_expectation']['tips_value']

        if tips_value is None:
            bond_data = fetch_bond_data()
            if bond_data and 'data' in bond_data:
                if 'tips_10y' in bond_data['data']:
                    tips_value = bond_data['data']['tips_10y']['latest']['value']

        enc, desc = encode_tips(tips_value)
        result['factors']['tips'] = {
            'tips_value': tips_value,
            'encoding': enc,
            'description': desc
        }
        result['encoding']['tips'] = enc
    except Exception as e:
        print(f"TIPS数据获取失败: {e}")
        result['factors']['tips'] = {'error': str(e)}
        result['encoding']['tips'] = 0

    # 6. 美元指数 DXY (5%)
    try:
        dxy_data = fetch_dxy_index()
        if dxy_data and 'price' in dxy_data:
            dxy_value = dxy_data['price']
            enc, desc = encode_dxy(dxy_value)
            result['factors']['dxy'] = {
                'dxy_value': dxy_value,
                'encoding': enc,
                'description': desc
            }
            result['encoding']['dxy'] = enc
        else:
            result['factors']['dxy'] = {'error': '数据不可用'}
            result['encoding']['dxy'] = 0
    except Exception as e:
        print(f"DXY数据获取失败: {e}")
        result['factors']['dxy'] = {'error': str(e)}
        result['encoding']['dxy'] = 0

    # 计算加权编码和
    weights = result['weights']
    encoding = result['encoding']

    weighted_sum = (
        encoding.get('central_bank_gold', 0) * weights['central_bank_gold'] +
        encoding.get('m2', 0) * weights['m2'] +
        encoding.get('debt_gdp', 0) * weights['debt_gdp'] +
        encoding.get('fed_expectation', 0) * weights['fed_expectation'] +
        encoding.get('tips', 0) * weights['tips'] +
        encoding.get('dxy', 0) * weights['dxy']
    )

    result['s_macro'] = round(weighted_sum, 4)

    # 信号解读
    if result['s_macro'] >= 0.5:
        result['signal'] = "强力看多宏观环境"
    elif result['s_macro'] >= 0.2:
        result['signal'] = "偏多宏观环境"
    elif result['s_macro'] >= -0.2:
        result['signal'] = "中性宏观环境"
    elif result['s_macro'] >= -0.5:
        result['signal'] = "偏空宏观环境"
    else:
        result['signal'] = "强力看空宏观环境"

    return result

def main():
    result = calculate_s_macro()
    print("\n" + "=" * 60)
    print("宏观驱动信号层结果 (S_macro)")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    main()