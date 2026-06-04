#!/usr/bin/env python3
"""
获取信用利差数据 (Credit Spread) - Baa-10Y
Version: 1.1

信用利差 = BAA企业债收益率 - 10年期美国国债收益率

数据来源:
- 10年期美国国债收益率: AkShare
- BAA企业债收益率: Yahoo Finance / 新浪财经 LQD ETF作为代理指标
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
                "10_year": float(latest.get('美国国债收益率10年', 0)),
                "source": "AkShare"
            }
    except Exception as e:
        print(f"获取国债收益率失败: {e}")
    return None

def fetch_baa_yield_proxy():
    """从新浪财经获取LQD ETF作为BAA代理指标"""
    try:
        url = "https://hq.sinajs.cn/list=gb_lqd"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn/'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'gbk'
        data_str = resp.text.split('"')[1]
        parts = data_str.split(',')
        if len(parts) > 5:
            return {
                "symbol": "LQD",
                "name": parts[0],
                "price": float(parts[1]),
                "change": float(parts[2]),
                "change_percent": float(parts[4]),
                "date": parts[3].split(' ')[0],
                "source": "新浪财经 (LQD ETF作为BAA代理)"
            }
    except Exception as e:
        print(f"获取LQD ETF数据失败: {e}")
    return None

def fetch_credit_spread():
    """计算信用利差 Baa-10Y"""
    print("正在获取信用利差数据 (Baa-10Y)...")
    
    # 获取国债收益率
    bond_yields = fetch_us_bond_yields()
    
    # 获取BAA企业债收益率代理
    baa_proxy = fetch_baa_yield_proxy()
    
    # 构建结果
    result = {
        "symbol": "BAA_10Y_SPREAD",
        "name": "信用利差 Baa-10Y",
        "description": "信用利差 = BAA企业债收益率 - 10年期美国国债收益率",
        "data_source": "AkShare + 新浪财经",
        "timestamp": datetime.now().isoformat()
    }
    
    if bond_yields and baa_proxy:
        result["us_bond_10y"] = {
            "yield": bond_yields["10_year"],
            "date": bond_yields["date"],
            "source": bond_yields["source"]
        }
        
        result["baa_proxy"] = {
            "symbol": baa_proxy["symbol"],
            "name": baa_proxy["name"],
            "price": baa_proxy["price"],
            "change": baa_proxy["change"],
            "change_percent": baa_proxy["change_percent"],
            "date": baa_proxy["date"],
            "source": baa_proxy["source"]
        }
        
        result["analysis"] = {
            "description": "信用利差反映市场对企业信用风险的评估",
            "interpretation": "利差扩大通常表示风险偏好下降，利差收窄表示风险偏好上升",
            "note": "使用LQD ETF作为BAA企业债收益率的代理指标，实际BAA收益率建议通过FRED API获取"
        }
        
        result["limitations"] = [
            "1. 使用LQD ETF价格作为企业债市场状况的代理指标",
            "2. 如需精确的BAA收益率，建议使用FRED API (series_id: BAA)",
            "3. FRED API需要注册获取免费API Key",
            "4. 实际信用利差计算需要企业债收益率与国债收益率的差值"
        ]
    else:
        if not bond_yields:
            result["error"] = "无法获取国债收益率数据"
        if not baa_proxy:
            result["error"] = result.get("error", "") + "无法获取企业债代理数据"
    
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("信用利差数据 (Credit Spread) - Baa-10Y")
    print("=" * 60)
    data = fetch_credit_spread()
    print(json.dumps(data, indent=2, ensure_ascii=False))