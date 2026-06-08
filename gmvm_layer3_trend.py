#!/usr/bin/env python3
"""
GMVM v6.1 Layer 3: 趋势动量系数 (K_trend)
计算趋势动量因子并输出系数

因子权重:
- RSI (14日): 30%
- MACD背离 (12,26,9): 25%
- 均线斜率 (20日): 25%
- 布林带 (20,2): 20%

K_trend = 1 + (T - 0.5) × 0.4  范围: 0.6 ~ 1.4
"""

import sys
sys.path.insert(0, '/workspace')

import json
from datetime import datetime

from fetch_gold_technical import calculate_gold_technical_analysis

def score_rsi(rsi_value):
    """
    RSI评分 (0-100)
    RSI ≤ 30 → 100分 (超卖)
    RSI 30~70 线性递减 (每1点减2.5分)
    RSI ≥ 70 → 0分 (超买)
    """
    if rsi_value is None:
        raise RuntimeError("RSI数据不可用")

    if rsi_value <= 30:
        return 100, f"RSI超卖 ({rsi_value:.2f} ≤ 30)"
    elif rsi_value >= 70:
        return 0, f"RSI超买 ({rsi_value:.2f} ≥ 70)"
    else:
        # 30~70: 线性递减
        # 30 → 100分, 70 → 0分
        score = (70 - rsi_value) / (70 - 30) * 100
        return round(score, 1), f"RSI中性 ({rsi_value:.2f})"

def score_macd_divergence(divergence_score):
    """
    MACD背离评分 (0-100)
    底背离 → 100分
    顶背离 → 0分
    无背离 → 50分
    """
    if divergence_score is None:
        raise RuntimeError("MACD数据不可用")

    if divergence_score >= 80:
        return 100, "MACD底背离 - 可能上涨信号"
    elif divergence_score <= 20:
        return 0, "MACD顶背离 - 可能下跌信号"
    else:
        return divergence_score, f"MACD无背离 ({divergence_score:.0f})"

def score_ma_slope(daily_pct_change):
    """
    均线斜率评分 (0-100)
    日涨幅 ≥ +0.5% → 100分
    日涨幅 ≤ -0.5% → 0分
    线性插值
    """
    if daily_pct_change is None:
        raise RuntimeError("均线数据不可用")

    if daily_pct_change >= 0.5:
        return 100, f"强势上涨趋势 (日涨幅{daily_pct_change:.3f}% ≥ +0.5%)"
    elif daily_pct_change <= -0.5:
        return 0, f"强势下跌趋势 (日涨幅{daily_pct_change:.3f}% ≤ -0.5%)"
    else:
        # 线性插值: -0.5% → 0分, +0.5% → 100分
        score = (daily_pct_change + 0.5) / (0.5 - (-0.5)) * 100
        score = max(0, min(100, score))
        return round(score, 1), f"温和趋势 (日涨幅{daily_pct_change:.3f}%)"

def score_bollinger(bollinger_score):
    """
    布林带评分 (0-100)
    触下轨且带宽扩大 → 100分
    触上轨且带宽扩大 → 0分
    其他 → 50分
    """
    if bollinger_score is None:
        raise RuntimeError("布林带数据不可用")

    if bollinger_score >= 80:
        return 100, "触下轨且带宽扩大 - 超卖信号"
    elif bollinger_score <= 20:
        return 0, "触上轨且带宽扩大 - 超买信号"
    else:
        return bollinger_score, "布林带无明显信号"

def calculate_k_trend():
    """计算趋势动量系数 K_trend"""
    print("=" * 60)
    print("GMVM v6.1 Layer 3: 趋势动量系数 (K_trend)")
    print("=" * 60)

    result = {
        "layer": "K_trend",
        "timestamp": datetime.now().isoformat(),
        "factors": {},
        "weights": {
            "rsi": 0.30,
            "macd_divergence": 0.25,
            "ma_slope": 0.25,
            "bollinger": 0.20
        },
        "scores": {},
        "t_score": None,  # 总分 (0-100)
        "k_trend": None,  # 最终系数 (0.6-1.4)
        "interpretation": None
    }

    # 获取技术指标数据
    tech_data = calculate_gold_technical_analysis()

    if 'error' in tech_data:
        raise RuntimeError(f"技术指标获取失败: {tech_data['error']}")

    indicators = tech_data.get('indicators', {})

    # 1. RSI (30%)
    rsi_value = indicators.get('rsi_14', {}).get('value')
    score, desc = score_rsi(rsi_value)
    result['factors']['rsi'] = {
        'value': rsi_value,
        'score': score,
        'description': desc
    }
    result['scores']['rsi'] = score

    # 2. MACD背离 (25%)
    macd_score = indicators.get('macd_12_26_9', {}).get('divergence_score')
    score, desc = score_macd_divergence(macd_score)
    result['factors']['macd_divergence'] = {
        'score': macd_score,
        'description': desc
    }
    result['scores']['macd_divergence'] = score

    # 3. 均线斜率 (25%)
    ma_data = indicators.get('ma_slope_20', {})
    pct_change_5d = ma_data.get('pct_change_5d', 0)
    daily_pct_change = pct_change_5d / 5 if pct_change_5d else 0
    score, desc = score_ma_slope(daily_pct_change)
    result['factors']['ma_slope'] = {
        'pct_change_5d': pct_change_5d,
        'daily_pct_change': daily_pct_change,
        'score': score,
        'description': desc
    }
    result['scores']['ma_slope'] = score

    # 4. 布林带 (20%)
    bollinger_score = indicators.get('bollinger_20_2', {}).get('score')
    score, desc = score_bollinger(bollinger_score)
    result['factors']['bollinger'] = {
        'score': bollinger_score,
        'description': desc
    }
    result['scores']['bollinger'] = score

    # 计算加权总分 T
    weights = result['weights']
    scores = result['scores']

    t_score = (
        scores['rsi'] * weights['rsi'] +
        scores['macd_divergence'] * weights['macd_divergence'] +
        scores['ma_slope'] * weights['ma_slope'] +
        scores['bollinger'] * weights['bollinger']
    )

    result['t_score'] = round(t_score, 2)

    # 计算 K_trend = 1 + (T - 0.5) × 0.4
    k_trend = 1 + (t_score / 100 - 0.5) * 0.4
    result['k_trend'] = round(k_trend, 4)

    # 解读
    if k_trend >= 1.3:
        result['interpretation'] = "趋势动量极强 - 上涨动能强劲"
    elif k_trend >= 1.1:
        result['interpretation'] = "趋势动量偏强 - 温和上涨动能"
    elif k_trend >= 0.9:
        result['interpretation'] = "趋势动量中性"
    elif k_trend >= 0.7:
        result['interpretation'] = "趋势动量偏弱 - 温和下跌动能"
    else:
        result['interpretation'] = "趋势动量极弱 - 下跌动能强劲"

    return result

def main():
    result = calculate_k_trend()
    print("\n" + "=" * 60)
    print("趋势动量系数结果 (K_trend)")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    main()
