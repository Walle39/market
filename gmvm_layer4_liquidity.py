#!/usr/bin/env python3
"""
GMVM v6.1 Layer 4: 动态流动性系数 (K_liquidity)
计算流动性因子并输出系数

因子:
- VIX 恐慌指数
- 信用利差 (Baa-10Y)

K_liquidity 范围: 0.3 ~ 1.2
"""

import sys
sys.path.insert(0, '/workspace')

import json
from datetime import datetime

from fetch_vix import fetch_vix
from fetch_credit_spread import fetch_credit_spread

def get_k_liquidity(vix_value, credit_spread):
    """
    根据VIX和信用利差确定K_liquidity

    VIX范围        | 信用利差   | K_liquidity | 市场状态
    ---------------|-----------|-------------|----------
    < 15           | < 2%      | 1.2         | 极度宽松
    15-25          | < 3%      | 1.0         | 正常环境
    15-25          | ≥ 3%      | 0.9         | 信用隐忧
    25-35          | < 3%      | 0.8         | 恐慌初现
    ≥ 25           | ≥ 3%      | 0.7         | 双重紧张
    ≥ 35           | 任意      | 0.5         | 流动性危机
    """
    # VIX >= 35
    if vix_value >= 35:
        return 0.5, "流动性危机 (VIX ≥ 35)"

    # VIX >= 25 (且 < 35)
    if vix_value >= 25:
        if credit_spread is not None and credit_spread >= 3:
            return 0.7, "双重紧张 (VIX 25-35, 信用利差 ≥ 3%)"
        else:
            return 0.8, "恐慌初现 (VIX 25-35, 信用利差 < 3%)"

    # VIX 15-25
    if vix_value >= 15:
        if credit_spread is not None and credit_spread >= 3:
            return 0.9, "信用隐忧 (VIX 15-25, 信用利差 ≥ 3%)"
        else:
            return 1.0, "正常环境 (VIX 15-25, 信用利差 < 3%)"

    # VIX < 15
    if credit_spread is not None and credit_spread < 2:
        return 1.2, "极度宽松 (VIX < 15, 信用利差 < 2%)"
    else:
        return 1.0, "相对宽松 (VIX < 15)"

def calculate_k_liquidity():
    """计算动态流动性系数 K_liquidity"""
    print("=" * 60)
    print("GMVM v6.1 Layer 4: 动态流动性系数 (K_liquidity)")
    print("=" * 60)

    result = {
        "layer": "K_liquidity",
        "timestamp": datetime.now().isoformat(),
        "factors": {},
        "k_liquidity": None,
        "market_status": None
    }

    # 1. 获取VIX
    vix_value = None
    try:
        vix_data = fetch_vix()
        if vix_data:
            # 尝试从ETF获取VIX估值
            if 'primary_etf' in vix_data and vix_data['primary_etf']:
                etf = vix_data['primary_etf']
                vix_value = etf.get('price')
                result['factors']['vix'] = {
                    'value': vix_value,
                    'source': 'TwelveData ETF (VXX)',
                    'note': 'VIX指数无法直接获取，使用VXX ETF作为代理'
                }
            elif 'price' in vix_data:
                vix_value = vix_data['price']
                result['factors']['vix'] = {
                    'value': vix_value,
                    'source': vix_data.get('source', 'Unknown')
                }
            else:
                result['factors']['vix'] = {'error': '无法获取VIX数据'}
        else:
            result['factors']['vix'] = {'error': '无数据'}
    except Exception as e:
        print(f"VIX数据获取失败: {e}")
        result['factors']['vix'] = {'error': str(e)}

    # 2. 获取信用利差
    credit_spread = None
    try:
        spread_data = fetch_credit_spread()
        if spread_data and 'credit_spread' in spread_data:
            credit_spread = spread_data['credit_spread']['value']
            result['factors']['credit_spread'] = {
                'value': credit_spread,
                'baa_yield': spread_data.get('baa_yield', {}).get('yield'),
                'treasury_10y': spread_data.get('us_bond_10y', {}).get('yield'),
                'source': 'FRED + AkShare'
            }
        else:
            result['factors']['credit_spread'] = {'error': '无法获取信用利差数据'}
    except Exception as e:
        print(f"信用利差数据获取失败: {e}")
        result['factors']['credit_spread'] = {'error': str(e)}

    # 计算K_liquidity
    k_liquidity, status = get_k_liquidity(vix_value, credit_spread)
    result['k_liquidity'] = round(k_liquidity, 4)
    result['market_status'] = status

    # 解读
    if k_liquidity >= 1.1:
        result['interpretation'] = "流动性极度宽松 - 利好黄金"
    elif k_liquidity >= 0.9:
        result['interpretation'] = "流动性正常 - 中性环境"
    elif k_liquidity >= 0.7:
        result['interpretation'] = "流动性紧张 - 谨慎黄金"
    else:
        result['interpretation'] = "流动性危机 - 极端谨慎"

    return result

def main():
    result = calculate_k_liquidity()
    print("\n" + "=" * 60)
    print("动态流动性系数结果 (K_liquidity)")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    main()
