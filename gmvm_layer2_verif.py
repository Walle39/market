#!/usr/bin/env python3
"""
GMVM v6.1 Layer 2: 市场验证系数 (K_verif)
计算市场验证因子并输出系数

因子权重:
- ETF持仓变化（近4周）: 40%
- 金银比: 35%
- 金价/AISC比率: 25%

K_verif = V / 100 + 0.5  范围: 0.5 ~ 1.5
"""

import sys
sys.path.insert(0, '/workspace')

import json
from datetime import datetime

from fetch_gold_holdings import fetch_gold_holdings
from fetch_gold_silver_spot import fetch_from_sina
from fetch_aisc import fetch_aisc_data
from fetch_gold_technical import fetch_gold_current_price

def score_etf_holding(change_4w_pct):
    """
    ETF持仓变化评分 (0-100)
    累计变化率 ≥ +2% → 100分
    累计变化率 ≤ -2% → 0分
    线性插值
    """
    if change_4w_pct is None:
        raise RuntimeError("ETF数据不可用")

    if change_4w_pct >= 2:
        return 100, f"ETF大幅增仓 ({change_4w_pct:.2f}% ≥ +2%)"
    elif change_4w_pct <= -2:
        return 0, f"ETF大幅减仓 ({change_4w_pct:.2f}% ≤ -2%)"
    else:
        # 线性插值: -2% → 0分, +2% → 100分
        score = (change_4w_pct + 2) / 4 * 100
        score = max(0, min(100, score))
        return round(score, 1), f"ETF温和变动 ({change_4w_pct:.2f}%)"

def score_gold_silver_ratio(ratio):
    """
    金银比评分 (0-100)
    比值 ≤ 60 → 100分 (白银相对便宜，黄金估值中性偏空)
    比值 ≥ 100 → 0分 (黄金相对昂贵，白银估值中性偏多)
    线性插值
    """
    if ratio is None:
        raise RuntimeError("金银比数据不可用")

    if ratio <= 60:
        return 100, f"金银比极低 ({ratio:.2f} ≤ 60) - 白银相对便宜"
    elif ratio >= 100:
        return 0, f"金银比极高 ({ratio:.2f} ≥ 100) - 黄金相对昂贵"
    else:
        # 线性插值: 100 → 0分, 60 → 100分
        score = (100 - ratio) / (100 - 60) * 100
        score = max(0, min(100, score))
        return round(score, 1), f"金银比正常 ({ratio:.2f})"

def score_gold_aisc_ratio(gold_price, aisc):
    """
    金价/AISC比率评分 (0-100)
    比率 ≤ 1.5 → 100分 (金价接近成本，估值极低)
    比率 ≥ 2.5 → 0分 (金价远离成本，估值极高)
    线性插值
    """
    if gold_price is None:
        raise RuntimeError("金价数据不可用")
    if aisc is None:
        raise RuntimeError("AISC数据不可用")

    ratio = gold_price / aisc

    if ratio <= 1.5:
        return 100, f"金价/成本比极低 ({ratio:.2f} ≤ 1.5) - 估值极低"
    elif ratio >= 2.5:
        return 0, f"金价/成本比极高 ({ratio:.2f} ≥ 2.5) - 估值极高"
    else:
        # 线性插值: 2.5 → 0分, 1.5 → 100分
        score = (2.5 - ratio) / (2.5 - 1.5) * 100
        score = max(0, min(100, score))
        return round(score, 1), f"金价/成本比正常 ({ratio:.2f})"

def calculate_k_verif():
    """计算市场验证系数 K_verif"""
    print("=" * 60)
    print("GMVM v6.1 Layer 2: 市场验证系数 (K_verif)")
    print("=" * 60)

    result = {
        "layer": "K_verif",
        "timestamp": datetime.now().isoformat(),
        "factors": {},
        "weights": {
            "etf_holding": 0.40,
            "gold_silver_ratio": 0.35,
            "gold_aisc_ratio": 0.25
        },
        "scores": {},
        "v_score": None,  # 总分 (0-100)
        "k_verif": None,  # 最终系数 (0.5-1.5)
        "interpretation": None
    }

    # 1. ETF持仓变化 (40%)
    etf_data = fetch_gold_holdings()
    if not etf_data or 'latest' not in etf_data or 'change_4w_percent' not in etf_data['latest']:
        raise RuntimeError("无法获取ETF持仓数据")
    change_4w = etf_data['latest']['change_4w_percent']
    score, desc = score_etf_holding(change_4w)
    result['factors']['etf_holding'] = {
        'change_4w_percent': change_4w,
        'score': score,
        'description': desc
    }
    result['scores']['etf_holding'] = score

    # 2. 金银比 (35%)
    gs_data = fetch_from_sina()
    if not gs_data or 'gold_silver_ratio' not in gs_data:
        raise RuntimeError("无法获取金银比数据")
    ratio = gs_data['gold_silver_ratio']['value']
    score, desc = score_gold_silver_ratio(ratio)
    result['factors']['gold_silver_ratio'] = {
        'ratio': ratio,
        'score': score,
        'description': desc
    }
    result['scores']['gold_silver_ratio'] = score

    # 3. 金价/AISC比率 (25%)
    # 获取黄金当前价格
    gold_data = fetch_gold_current_price()
    if not gold_data:
        raise RuntimeError("无法获取金价数据")
    gold_price = gold_data['price']

    # 获取AISC成本
    aisc_data = fetch_aisc_data()
    if not aisc_data or 'average_4q' not in aisc_data:
        raise RuntimeError("无法获取AISC数据")
    aisc = aisc_data['average_4q']['value']

    score, desc = score_gold_aisc_ratio(gold_price, aisc)
    result['factors']['gold_aisc_ratio'] = {
        'gold_price': gold_price,
        'aisc': aisc,
        'ratio': gold_price / aisc,
        'score': score,
        'description': desc
    }
    result['scores']['gold_aisc_ratio'] = score

    # 计算加权总分 V
    weights = result['weights']
    scores = result['scores']

    v_score = (
        scores['etf_holding'] * weights['etf_holding'] +
        scores['gold_silver_ratio'] * weights['gold_silver_ratio'] +
        scores['gold_aisc_ratio'] * weights['gold_aisc_ratio']
    )

    result['v_score'] = round(v_score, 2)

    # 计算 K_verif = V / 100 + 0.5
    k_verif = v_score / 100 + 0.5
    result['k_verif'] = round(k_verif, 4)

    # 解读
    if k_verif >= 1.3:
        result['interpretation'] = "市场验证极强 - 极度看多信号"
    elif k_verif >= 1.1:
        result['interpretation'] = "市场验证偏强 - 温和看多信号"
    elif k_verif >= 0.9:
        result['interpretation'] = "市场验证中性"
    elif k_verif >= 0.7:
        result['interpretation'] = "市场验证偏弱 - 温和看空信号"
    else:
        result['interpretation'] = "市场验证极弱 - 极度看空信号"

    return result

def main():
    result = calculate_k_verif()
    print("\n" + "=" * 60)
    print("市场验证系数结果 (K_verif)")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    main()
