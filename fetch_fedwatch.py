#!/usr/bin/env python3
"""
获取 FedWatch 概率数据
Version: 5.1

数据来源: AkShare (美国国债收益率)
英为财情等网站受Cloudflare保护，无法直接访问
使用国债收益率作为市场对美联储政策预期的代理指标
"""

import requests
import json
from datetime import datetime
import akshare as ak

def fetch_us_bond_yields():
    """获取美国国债收益率"""
    try:
        df = ak.bond_zh_us_rate()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return {
                "date": str(latest.get('日期', '')),
                "2_year": float(latest.get('美国国债收益率2年', 0)),
                "5_year": float(latest.get('美国国债收益率5年', 0)),
                "10_year": float(latest.get('美国国债收益率10年', 0)),
                "30_year": float(latest.get('美国国债收益率30年', 0)),
                "spread_10_2": float(latest.get('美国国债收益率10年-2年', 0)),
                "source": "AkShare"
            }
    except Exception as e:
        print(f"获取国债收益率失败: {e}")
    return None

def fetch_fed_rate():
    """获取 FedWatch 相关数据 - 使用替代指标"""
    print("正在获取 FedWatch 相关数据...")
    
    # 获取国债收益率
    bond_yields = fetch_us_bond_yields()
    
    # 构建结果
    result = {
        "symbol": "FEDWATCH",
        "name": "FedWatch相关数据",
        "note": "英为财情等网站受Cloudflare保护无法访问，以下数据可作为替代参考",
        "data_source": "AkShare (美国国债收益率)",
        "limitation": "FedWatch降息概率需要商业API(CME等)支持，以下为替代指标",
        "timestamp": datetime.now().isoformat()
    }
    
    if bond_yields:
        result["us_bond_yields"] = bond_yields
        result["yield_analysis"] = {
            "description": "国债收益率反映市场对美联储政策预期",
            "2y_10y_spread": f"{bond_yields['spread_10_2']}%",
            "interpretation": "正利差表示正常曲线，负利差可能预示经济衰退",
            "rate_expectation": "2年期收益率变化反映市场对短期利率预期"
        }
        
        # 添加一些补充说明
        result["alternative_data_notes"] = [
            "1. 2年期国债收益率可间接反映市场对美联储政策预期",
            "2. 10年期与2年期利差是重要的经济预测指标",
            "3. 官方FedWatch数据需通过CME付费API获取",
            "4. 英为财情页面受Cloudflare保护无法自动访问"
        ]
    else:
        result["error"] = "无法获取替代数据"
    
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("FedWatch 相关数据 (AkShare 国债收益率)")
    print("=" * 60)
    data = fetch_fed_rate()
    print(json.dumps(data, indent=2, ensure_ascii=False))
