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

def get_k_geo(gpr_3month_avg, oil_price, cpi_yoy, fed_code):
    """
    根据GPR、油价、CPI、Fed预期确定K_geo
    """
    if gpr_3month_avg is None:
        raise RuntimeError("GPR数据不可用")

    # GPR <= 100: 无显著地缘影响
    if gpr_3month_avg <= 100:
        return 1.00, "无显著地缘影响"

    # GPR > 120:
    if gpr_3month_avg > 120:
        # > $120: 结构性供给冲击（滞胀型）
        if oil_price > 120:
            return 1.20, "结构性供给冲击（滞胀型）"
        # $100~$120:
        elif 100 <= oil_price <= 120:
            # Fed预期: 鹰派 → 0.95
            if fed_code == -1:
                return 0.95, "利率压制型（油价较高但Fed鹰派）"
            # 其他 → 1.10
            else:
                return 1.10, "情绪利多，无利率压制"
        # < $100:
        else:
            return 1.10, "高GPR但油价较低"

    # 100 < GPR <= 120:
    # Fed预期: 鹰派 → 0.98
    if fed_code == -1:
        return 0.98, "轻度利率压制"
    # 其他 → 1.05
    else:
        return 1.05, "日常避险溢价"

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

    # 1. 获取GPR指数
    gpr_data = fetch_gpr()
    if not gpr_data or 'gpr' not in gpr_data:
        raise RuntimeError("无法获取GPR数据")
    gpr_value = gpr_data['gpr']
    result['factors']['gpr'] = {
        'value': gpr_value,
        'source': 'Matteo Iacoviello'
    }

    # 2. 获取布伦特原油价格
    oil_data = fetch_from_sina()
    oil_price = None
    if oil_data and 'price' in oil_data:
        oil_price = oil_data['price']
        result['factors']['oil'] = {
            'price': oil_price,
            'source': '新浪财经'
        }
    if oil_price is None:
        raise RuntimeError("无法获取原油价格数据")

    # 3. 获取CPI同比
    cpi_data = fetch_usa_cpi()
    cpi_yoy = None
    if cpi_data and 'latest' in cpi_data:
        cpi_yoy = cpi_data['latest']
        result['factors']['cpi'] = {
            'yoy': cpi_yoy,
            'source': 'FRED/BLS'
        }

    # 4. 获取Fed预期（使用TIPS作为代理）
    bond_data = fetch_bond_data()
    fed_code = 0
    if bond_data and 'data' in bond_data:
        if 'tips_10y' in bond_data['data']:
            tips_val = bond_data['data']['tips_10y']['latest']['value']
            if tips_val < -0.5:
                fed_code = 1
            elif tips_val > 1.5:
                fed_code = -1
            else:
                fed_code = 0
            result['factors']['fed_expectation'] = {
                'code': fed_code,
                'tips_value': tips_val,
                'source': 'TIPS代理'
            }

    # 计算K_geo
    k_geo, paradigm = get_k_geo(
        gpr_3month_avg=gpr_value,
        oil_price=oil_price,
        cpi_yoy=cpi_yoy,
        fed_code=fed_code
    )

    result['k_geo'] = round(k_geo, 4)
    result['paradigm'] = paradigm

    # 解读
    if k_geo >= 1.15:
        result['interpretation'] = "地缘极强利多黄金"
    elif k_geo >= 1.05:
        result['interpretation'] = "地缘轻微利多"
    elif k_geo >= 0.95:
        result['interpretation'] = "地缘中性或轻微压制"
    else:
        result['interpretation'] = "地缘利空黄金"

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
