#!/usr/bin/env python3
"""
获取信用利差数据 (Credit Spread) - Baa-10Y
Version: 2.0

信用利差 = BAA企业债收益率 - 10年期美国国债收益率

数据来源:
- 10年期美国国债收益率: AkShare
- BAA企业债收益率: FRED API (series_id: BAA)
"""

import requests
import json
from datetime import datetime
import akshare as ak

FRED_API_KEY = "5829f98ab0ac4f79358f2f85d98e5e89"

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

def fetch_baa_yield():
    """从FRED API获取BAA企业债收益率"""
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=BAA&api_key={FRED_API_KEY}&file_type=json&limit=1&sort_order=desc"
        resp = requests.get(url, timeout=30)
        data = resp.json()
        if 'observations' in data and len(data['observations']) > 0:
            obs = data['observations'][-1]
            if obs.get('value') and obs['value'] != '.':
                return {
                    "date": obs.get('date', ''),
                    "yield": float(obs.get('value', 0)),
                    "source": "FRED",
                    "series_id": "BAA"
                }
    except Exception as e:
        print(f"获取BAA收益率失败: {e}")
    return None

def fetch_credit_spread():
    """计算信用利差 Baa-10Y"""
    print("正在获取信用利差数据 (Baa-10Y)...")
    
    # 获取国债收益率
    bond_yields = fetch_us_bond_yields()
    
    # 获取BAA企业债收益率
    baa_data = fetch_baa_yield()
    
    # 构建结果
    result = {
        "symbol": "BAA_10Y_SPREAD",
        "name": "信用利差 Baa-10Y",
        "description": "信用利差 = BAA企业债收益率 - 10年期美国国债收益率",
        "data_source": "AkShare + FRED API",
        "timestamp": datetime.now().isoformat()
    }
    
    if bond_yields and baa_data:
        # 计算信用利差
        credit_spread = baa_data["yield"] - bond_yields["10_year"]
        
        result["us_bond_10y"] = {
            "yield": bond_yields["10_year"],
            "date": bond_yields["date"],
            "source": bond_yields["source"]
        }
        
        result["baa_yield"] = {
            "yield": baa_data["yield"],
            "date": baa_data["date"],
            "source": baa_data["source"],
            "series_id": baa_data["series_id"]
        }
        
        result["credit_spread"] = {
            "value": round(credit_spread, 2),
            "unit": "%",
            "calculation": f"BAA({baa_data['yield']}%) - 10Y({bond_yields['10_year']}%) = {round(credit_spread, 2)}%"
        }
        
        result["analysis"] = {
            "description": "信用利差反映市场对企业信用风险的评估",
            "interpretation": "利差扩大通常表示风险偏好下降，利差收窄表示风险偏好上升"
        }
    else:
        if not bond_yields:
            result["error"] = "无法获取国债收益率数据"
        if not baa_data:
            result["error"] = result.get("error", "") + "无法获取BAA收益率数据"
    
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("信用利差数据 (Credit Spread) - Baa-10Y")
    print("=" * 60)
    data = fetch_credit_spread()
    print(json.dumps(data, indent=2, ensure_ascii=False))