#!/usr/bin/env python3
"""
综合测试所有fetch_*和gmvm_*脚本
"""
import sys
import os
import json
from datetime import datetime

# 添加工作目录到Python路径
sys.path.insert(0, '/workspace')

def test_scripts():
    results = {
        "fetch_scripts": {},
        "gmvm_layers": {},
        "timestamp": datetime.now().isoformat()
    }
    
    print("=" * 80)
    print("开始测试所有fetch_*数据获取脚本")
    print("=" * 80)
    
    # 测试fetch_scripts
    fetch_test_cases = [
        # (脚本名, 函数名, 描述)
        ("fetch_central_bank_gold", "fetch_gold_demand_data", "央行购金数据"),
        ("fetch_central_bank_gold_quarterly", "fetch_central_bank_gold_quarterly", "央行购金季度数据"),
        ("fetch_gold_technical", "fetch_gold_current_price", "黄金价格"),
        ("fetch_gold_holdings", "fetch_gold_holdings", "ETF持仓数据"),
        ("fetch_gpr", "fetch_gpr", "GPR地缘风险"),
        ("fetch_us_debt_gdp", "fetch_us_debt_gdp", "美国国债/GDP"),
        ("fetch_gold_silver_spot", "fetch_from_sina", "金银价格"),
        ("fetch_dxy_index", "fetch_dxy_index", "美元指数"),
        ("fetch_aisc", "fetch_aisc_data", "AISC成本"),
        ("fetch_credit_spread", "fetch_credit_spread", "信用利差"),
        ("fetch_us_bond_tips", "fetch_bond_data", "美债TIPS"),
        ("fetch_usa_m2", "fetch_fred_m2", "美国M2"),
        ("fetch_usa_cpi", "fetch_usa_cpi", "美国CPI"),
        ("fetch_vix", "fetch_vix", "VIX恐慌指数"),
        ("fetch_crude_oil", "fetch_from_sina", "原油价格"),
    ]
    
    for module_name, func_name, desc in fetch_test_cases:
        print(f"\n{'=' * 80}")
        print(f"测试: {desc} ({module_name}.py)")
        print(f"{'=' * 80}")
        
        try:
            # 动态导入模块和函数
            module = __import__(module_name)
            func = getattr(module, func_name)
            
            # 调用函数
            result = func()
            
            # 验证结果
            if result:
                print(f"✅ 成功！返回结果: {type(result)}")
                # 打印部分结果用于验证
                if isinstance(result, dict):
                    preview = dict(list(result.items())[:5])
                    print(f"   预览: {json.dumps(preview, ensure_ascii=False, indent=2)[:500]}")
                
                results["fetch_scripts"][module_name] = {"status": "success", "result_type": str(type(result))}
            else:
                print(f"⚠️ 无返回值")
                results["fetch_scripts"][module_name] = {"status": "warning", "message": "no result"}
                
        except Exception as e:
            print(f"❌ 失败: {e}")
            import traceback
            print(f"   错误详情: {traceback.format_exc()[:1000]}")
            results["fetch_scripts"][module_name] = {"status": "error", "error": str(e)}
    
    # 现在测试gmvm层
    print("\n" + "=" * 80)
    print("开始测试gmvm层脚本")
    print("=" * 80)
    
    gmvm_test_cases = [
        ("gmvm_layer1_macro", "calculate_s_macro", "宏观驱动信号"),
        ("gmvm_layer2_verif", "calculate_k_verif", "市场验证系数"),
        ("gmvm_layer3_trend", "calculate_k_trend", "趋势动量系数"),
        ("gmvm_layer4_liquidity", "calculate_k_liquidity", "动态流动性系数"),
        ("gmvm_layer5_geo", "calculate_k_geo", "地缘条件化乘数"),
    ]
    
    for module_name, func_name, desc in gmvm_test_cases:
        print(f"\n{'=' * 80}")
        print(f"测试: {desc} ({module_name}.py)")
        print(f"{'=' * 80}")
        
        try:
            module = __import__(module_name)
            func = getattr(module, func_name)
            result = func()
            
            if result:
                print(f"✅ 成功！")
                results["gmvm_layers"][module_name] = {"status": "success"}
            else:
                print(f"⚠️ 无返回值")
                results["gmvm_layers"][module_name] = {"status": "warning"}
                
        except Exception as e:
            print(f"❌ 失败: {e}")
            import traceback
            print(f"   错误详情: {traceback.format_exc()[:1000]}")
            results["gmvm_layers"][module_name] = {"status": "error", "error": str(e)}
    
    return results

if __name__ == "__main__":
    results = test_scripts()
    
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"\nfetch脚本测试统计:")
    for name, res in results["fetch_scripts"].items():
        print(f"  {name:30s}: {res['status']}")
    
    print(f"\ngmvm层测试统计:")
    for name, res in results["gmvm_layers"].items():
        print(f"  {name:30s}: {res['status']}")
