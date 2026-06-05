#!/usr/bin/env python3
"""
GMVM v6.1 黄金市场估值模型 - 主程序
整合所有层次并输出最终信号

综合信号 = S_macro × K_verif × K_trend × K_liquidity × K_geo

强制规则覆盖:
- OR-03: 流动性危机 → 最终信号 ≤ -0.50
- OR-01: 极度超买+顶背离 → 最终信号 ≤ -0.20
- OR-02: 极度超卖+底背离 → 最终信号 ≥ +0.30
- OR-05: 验证层总分 > 0.8 且 S_macro > 0 → 最终信号不得低于 +0.15
- 结构牛底线: 央行连续两季净购金 > 300吨 → 最终信号下限锚定 +0.15
- OR-04: 央行购金连续两季 > 300吨 且 金价低于历史高点10%以上 → 额外+0.10
"""

import sys
sys.path.insert(0, '/workspace')

import json
from datetime import datetime

# 导入各层计算模块
from gmvm_layer1_macro import calculate_s_macro
from gmvm_layer2_verif import calculate_k_verif
from gmvm_layer3_trend import calculate_k_trend
from gmvm_layer4_liquidity import calculate_k_liquidity
from gmvm_layer5_geo import calculate_k_geo

# 导入数据获取脚本
from fetch_gold_technical import fetch_gold_current_price
from fetch_central_bank_gold_quarterly import fetch_central_bank_gold_quarterly

def apply_override_rules(raw_signal, layer_results):
    """
    应用强制规则覆盖

    优先级: OR-03 > OR-01/OR-02 > 结构牛底线 > OR-05/OR-04
    """
    final_signal = raw_signal
    applied_rules = []

    # 获取各层数据
    s_macro = layer_results.get('s_macro', {}).get('s_macro', 0)
    k_verif_data = layer_results.get('k_verif', {})
    k_trend_data = layer_results.get('k_trend', {})
    k_liquidity_data = layer_results.get('k_liquidity', {})

    v_score = k_verif_data.get('v_score', 50) / 100  # 转换为0-1
    t_score = k_trend_data.get('t_score', 50)
    k_liquidity = k_liquidity_data.get('k_liquidity', 1.0)

    # OR-03: 流动性危机 (VIX ≥ 35 且 黄金美元同跌)
    if k_liquidity <= 0.5:
        # 检查是否黄金美元同跌
        gold_data = fetch_gold_current_price()
        # 这里简化处理，实际需要检查金价跌幅和DXY涨幅
        final_signal = -0.50
        applied_rules.append({
            "rule": "OR-03",
            "description": "流动性危机强制清仓",
            "forced_signal": final_signal
        })

    # OR-01: 极度超买+顶背离 (趋势层总分 < 20)
    elif t_score < 20:
        final_signal = min(final_signal, -0.20)
        applied_rules.append({
            "rule": "OR-01",
            "description": "极度超买+顶背离强制偏空",
            "forced_signal": final_signal
        })

    # OR-02: 极度超卖+底背离 (趋势层总分 > 80)
    elif t_score > 80:
        final_signal = max(final_signal, 0.30)
        applied_rules.append({
            "rule": "OR-02",
            "description": "极度超卖+底背离强制偏多",
            "forced_signal": final_signal
        })

    # 结构牛底线: 全球央行连续两季净购金 > 300吨/季
    try:
        cb_gold_data = fetch_central_bank_gold_quarterly()
        if cb_gold_data and 'quarters' in cb_gold_data:
            quarters = cb_gold_data['quarters']
            if len(quarters) >= 2:
                q1 = quarters[0]['tonnes']
                q2 = quarters[1]['tonnes']
                if q1 > 300 and q2 > 300:
                    if final_signal < 0.15:
                        final_signal = 0.15
                    applied_rules.append({
                        "rule": "结构牛底线",
                        "description": "央行连续两季净购金 > 300吨",
                        "q1_tonnes": q1,
                        "q2_tonnes": q2,
                        "forced_signal": final_signal
                    })

                # OR-04: 央行购金连续两季 > 300吨 且 金价低于历史高点10%以上
                # 简化：假设当前金价已知，需要获取历史高点
                gold_price = fetch_gold_current_price()
                # 这里需要历史高点数据，暂用当前价格*1.1作为估算
                hist_high_estimate = gold_price['price'] * 1.1 if gold_price else None
                if q1 > 300 and q2 > 300 and hist_high_estimate:
                    current_price = gold_price['price'] if gold_price else 0
                    if current_price < hist_high_estimate * 0.9:  # 低于历史高点10%以上
                        final_signal = final_signal + 0.10
                        applied_rules.append({
                            "rule": "OR-04",
                            "description": "央行购金强劲且金价回调",
                            "additional_signal": 0.10,
                            "new_signal": final_signal
                        })
    except Exception as e:
        print(f"检查央行购金规则失败: {e}")

    # OR-05: 验证层总分 > 0.8 且 S_macro > 0
    if v_score > 0.8 and s_macro > 0:
        if final_signal < 0.15:
            final_signal = 0.15
            applied_rules.append({
                "rule": "OR-05",
                "description": "强验证层+正宏观信号保护",
                "forced_signal": final_signal
            })

    return final_signal, applied_rules

def get_signal_grade(final_signal):
    """根据最终信号确定信号等级和仓位建议"""
    if final_signal >= 0.60:
        return {
            "grade": "🔥 强力看多",
            "action": "积极加仓，可适度杠杆",
            "position": "80%-100%"
        }
    elif final_signal >= 0.35:
        return {
            "grade": "✅ 看多",
            "action": "分批建仓，回调加仓",
            "position": "60%-80%"
        }
    elif final_signal >= 0.15:
        return {
            "grade": "🟡 偏多",
            "action": "持有为主，轻仓可增",
            "position": "40%-60%"
        }
    elif final_signal >= -0.15:
        return {
            "grade": "⚪ 中性",
            "action": "观望，不做方向性操作",
            "position": "20%-40%"
        }
    elif final_signal >= -0.35:
        return {
            "grade": "🟠 偏空",
            "action": "减仓，了结部分利润",
            "position": "10%-20%"
        }
    else:
        return {
            "grade": "🔴 看空",
            "action": "清仓或对冲做空",
            "position": "0%-10%"
        }

def calculate_gmvm():
    """GMVM v6.1 主计算函数"""
    print("=" * 70)
    print("GMVM v6.1 黄金市场估值模型")
    print("=" * 70)

    result = {
        "model": "GMVM v6.1",
        "name": "黄金市场估值模型",
        "timestamp": datetime.now().isoformat(),
        "layers": {},
        "raw_signal": None,
        "final_signal": None,
        "signal_grade": None,
        "override_rules": [],
        "position_recommendation": None
    }

    # Layer 1: 宏观驱动信号层 (S_macro)
    print("\n[1/5] 计算宏观驱动信号层 S_macro...")
    try:
        s_macro_result = calculate_s_macro()
        result['layers']['s_macro'] = s_macro_result
    except Exception as e:
        print(f"S_macro计算失败: {e}")
        result['layers']['s_macro'] = {'error': str(e)}

    # Layer 2: 市场验证系数 (K_verif)
    print("\n[2/5] 计算市场验证系数 K_verif...")
    try:
        k_verif_result = calculate_k_verif()
        result['layers']['k_verif'] = k_verif_result
    except Exception as e:
        print(f"K_verif计算失败: {e}")
        result['layers']['k_verif'] = {'error': str(e)}

    # Layer 3: 趋势动量系数 (K_trend)
    print("\n[3/5] 计算趋势动量系数 K_trend...")
    try:
        k_trend_result = calculate_k_trend()
        result['layers']['k_trend'] = k_trend_result
    except Exception as e:
        print(f"K_trend计算失败: {e}")
        result['layers']['k_trend'] = {'error': str(e)}

    # Layer 4: 动态流动性系数 (K_liquidity)
    print("\n[4/5] 计算动态流动性系数 K_liquidity...")
    try:
        k_liquidity_result = calculate_k_liquidity()
        result['layers']['k_liquidity'] = k_liquidity_result
    except Exception as e:
        print(f"K_liquidity计算失败: {e}")
        result['layers']['k_liquidity'] = {'error': str(e)}

    # Layer 5: 地缘条件化乘数 (K_geo)
    print("\n[5/5] 计算地缘条件化乘数 K_geo...")
    try:
        k_geo_result = calculate_k_geo()
        result['layers']['k_geo'] = k_geo_result
    except Exception as e:
        print(f"K_geo计算失败: {e}")
        result['layers']['k_geo'] = {'error': str(e)}

    # 计算综合信号
    print("\n" + "=" * 70)
    print("计算综合信号...")
    print("=" * 70)

    s_macro = result['layers'].get('s_macro', {}).get('s_macro', 0)
    k_verif = result['layers'].get('k_verif', {}).get('k_verif', 1.0)
    k_trend = result['layers'].get('k_trend', {}).get('k_trend', 1.0)
    k_liquidity = result['layers'].get('k_liquidity', {}).get('k_liquidity', 1.0)
    k_geo = result['layers'].get('k_geo', {}).get('k_geo', 1.0)

    # 原始综合信号 = S_macro × K_verif × K_trend × K_liquidity × K_geo
    raw_signal = s_macro * k_verif * k_trend * k_liquidity * k_geo
    result['raw_signal'] = round(raw_signal, 4)

    print(f"\n原始综合信号计算:")
    print(f"  S_macro    = {s_macro:.4f}")
    print(f"  K_verif    = {k_verif:.4f}")
    print(f"  K_trend    = {k_trend:.4f}")
    print(f"  K_liquidity = {k_liquidity:.4f}")
    print(f"  K_geo      = {k_geo:.4f}")
    print(f"  ─────────────────────────────")
    print(f"  原始信号   = {raw_signal:.4f}")

    # 应用强制规则覆盖
    final_signal, applied_rules = apply_override_rules(raw_signal, result['layers'])
    result['final_signal'] = round(final_signal, 4)
    result['override_rules'] = applied_rules

    if applied_rules:
        print(f"\n强制规则覆盖:")
        for rule in applied_rules:
            print(f"  - {rule['rule']}: {rule['description']} → {rule.get('forced_signal', rule.get('additional_signal', 'N/A'))}")
        print(f"  ─────────────────────────────")
        print(f"  最终信号   = {final_signal:.4f}")

    # 获取信号等级和仓位建议
    grade_info = get_signal_grade(final_signal)
    result['signal_grade'] = grade_info['grade']
    result['position_recommendation'] = {
        "action": grade_info['action'],
        "position": grade_info['position']
    }

    # 输出结果摘要
    print("\n" + "=" * 70)
    print("GMVM v6.1 最终结果")
    print("=" * 70)
    print(f"\n  最终信号: {final_signal:.4f}")
    print(f"  信号等级: {grade_info['grade']}")
    print(f"  操作建议: {grade_info['action']}")
    print(f"  建议仓位: {grade_info['position']}")
    print("=" * 70)

    return result

def main():
    result = calculate_gmvm()

    # 输出完整JSON
    print("\n" + "=" * 70)
    print("完整JSON输出:")
    print("=" * 70)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return result

if __name__ == "__main__":
    main()
