#!/usr/bin/env python3
"""
GMVM v6.1 Layer 5: 地缘条件化乘数 (K_geo)
计算地缘政治条件化系数

因子:
- GPR指数（连续3月）
- 布伦特原油
- CPI同比
- Fed预期差

K_geo 范围: 0.95 ~ 1.20
"""

import sys
sys.path.insert(0, '/workspace')

import json
from datetime import datetime

from fetch_gpr import fetch_gpr
from fetch_crude_oil import fetch_from_sina
from fetch_usa_cpi import fetch_usa_cpi
from fetch_us_bond_tips import fetch_bond_data

def get_k_geo(gpr_3month_avg, oil_price, cpi_yoy, fed_expectation_code):
    """
    根据GPR、油价、CPI、Fed预期确定K_geo

    GPR连续3月  | 布伦特原油 | CPI同比 | Fed预期差 | K_geo | 冲突范式
    -----------|-----------|---------|-----------|-------|----------
    > 120      | > $120    | > 4%    | 不管      | 1.20  | 结构性供给冲击
    > 120      | $100-120  | 任意    | = -1(鹰派)| 0.95  | 利率压制型
    > 120      | $100-120  | 任意    | 0或+1     | 1.10  | 情绪利多
    >100 ≤120  | < $100    | 任意    | 任意      | 1.05  | 日常避险溢价
    >100 ≤120  | ≥ $100    | 任意    | = -1      | 0.98  | 轻度利率压制
    ≤ 100      | —         | —       | —         | 1.00  | 无显著地缘影响
    """
    # GPR <= 100: 无显著地缘影响
    if gpr_3month_avg <= 100:
        return 1.00, "无显著地缘影响"

    # GPR > 120
    if gpr_3month_avg > 120:
        if oil_price > 120:
            return 1.20, "结构性供给冲击（滞胀型）"
        elif oil_price >= 100:
            if fed_expectation_code == -1:
                return 0.95, "利率压制型"
            else:
                return 1.10, "情绪利多，无利率压制"
        else:
            return 1.10, "高GPR但油价正常"

    # 100 < GPR <= 120
    if oil_price < 100:
        return 1.05, "日常避险溢价"
    else:  # oil_price >= 100
        if fed_expectation_code == -1:
            return 0.98, "轻度利率压制"
        else:
            return 1.05, "中等烈度地缘紧张"

def calculate_k_geo():
    """计算地缘条件化乘数 K_geo"""
    print("=" * 60)
    print("GMVM v6.1 Layer 5: 地缘条件化乘数 (K_geo)")
    print("=" * 60)

    result = {
        "layer": "K_geo",
        "timestamp": datetime.now().isoformat(),
        "factors": {},
        "k_geo": None,
        "paradigm": None
    }

    # 1. 获取GPR指数（连续3月平均）
    gpr_value = None
    gpr_3month_avg = None
    try:
        gpr_data = fetch_gpr()
        if gpr_data and 'gpr' in gpr_data:
            gpr_value = gpr_data['gpr']
            # 假设GPR月度数据，如果获取的是单月值，暂用该值作为3月平均的估算
            # 实际应该取连续3月均值
            gpr_3month_avg = gpr_value  # 简化处理
            result['factors']['gpr'] = {
                'latest': gpr_value,
                'gpr_3month_avg': gpr_3month_avg,
                'date': gpr_data.get('date'),
                'note': '使用最新GPR值作为3月均值估算'
            }
        else:
            result['factors']['gpr'] = {'error': '无法获取GPR数据'}
    except Exception as e:
        print(f"GPR数据获取失败: {e}")
        result['factors']['gpr'] = {'error': str(e)}

    # 2. 获取布伦特原油价格
    oil_price = None
    try:
        oil_data = fetch_from_sina()
        if oil_data and 'price' in oil_data:
            oil_price = oil_data['price']
            result['factors']['crude_oil'] = {
                'price': oil_price,
                'source': '新浪财经 hf_OIL'
            }
        else:
            result['factors']['crude_oil'] = {'error': '无法获取油价数据'}
    except Exception as e:
        print(f"油价数据获取失败: {e}")
        result['factors']['crude_oil'] = {'error': str(e)}

    # 3. 获取CPI同比
    cpi_yoy = None
    try:
        cpi_data = fetch_usa_cpi()
        if cpi_data and 'current_value' in cpi_data:
            cpi_yoy = cpi_data['current_value']
            result['factors']['cpi'] = {
                'yoy': cpi_yoy,
                'time': cpi_data.get('time'),
                'source': 'AkShare'
            }
        else:
            result['factors']['cpi'] = {'error': '无法获取CPI数据'}
    except Exception as e:
        print(f"CPI数据获取失败: {e}")
        result['factors']['cpi'] = {'error': str(e)}

    # 4. 获取Fed预期差
    fed_expectation_code = 0  # 默认中性
    try:
        bond_data = fetch_bond_data()
        tips_value = None
        if bond_data and 'data' in bond_data:
            if 'tips_10y' in bond_data['data']:
                tips_value = bond_data['data']['tips_10y']['latest']['value']

        if tips_value is not None:
            if tips_value < -0.5:
                fed_expectation_code = 1  # 鸽派
            elif tips_value > 1.5:
                fed_expectation_code = -1  # 鹰派
            else:
                fed_expectation_code = 0  # 中性

        result['factors']['fed_expectation'] = {
            'tips_value': tips_value,
            'code': fed_expectation_code,
            'description': {1: "鸽派(降息)", 0: "中性", -1: "鹰派(加息)"}.get(fed_expectation_code, "未知")
        }
    except Exception as e:
        print(f"Fed预期数据获取失败: {e}")
        result['factors']['fed_expectation'] = {'error': str(e)}

    # 计算K_geo
    k_geo, paradigm = get_k_geo(
        gpr_3month_avg,
        oil_price,
        cpi_yoy,
        fed_expectation_code
    )

    result['k_geo'] = round(k_geo, 4)
    result['paradigm'] = paradigm

    # 解读
    if k_geo >= 1.15:
        result['interpretation'] = "地缘利好黄金 - 结构性冲击"
    elif k_geo >= 1.05:
        result['interpretation'] = "地缘轻微利好"
    elif k_geo >= 0.98:
        result['interpretation'] = "地缘影响中性"
    else:
        result['interpretation'] = "地缘利空黄金 - 利率压制"

    return result

def main():
    result = calculate_k_geo()
    print("\n" + "=" * 60)
    print("地缘条件化乘数结果 (K_geo)")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    main()
