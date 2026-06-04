#!/usr/bin/env python3
"""
获取美国债券/利率数据
Version: 1.0

数据来源:
1. AkShare bond_zh_us_rate - 美国国债收益率
2. FRED API DFII10 - 10年期TIPS实际利率
"""

import akshare as ak
import requests
import json
from datetime import datetime

FRED_API_KEY = "5829f98ab0ac4f79358f2f85d98e5e89"

def fetch_us_treasury_yields():
    """获取美国国债收益率"""
    print("正在获取美国国债收益率...")
    
    try:
        df = ak.bond_zh_us_rate()
        
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return {
                "symbol": "US_TREASURY_YIELDS",
                "name": "美国国债收益率",
                "date": str(latest.get('日期', '')),
                "2_year": float(latest.get('美国国债收益率2年', 0)),
                "5_year": float(latest.get('美国国债收益率5年', 0)),
                "10_year": float(latest.get('美国国债收益率10年', 0)),
                "30_year": float(latest.get('美国国债收益率30年', 0)),
                "spread_10_2": float(latest.get('美国国债收益率10年-2年', 0)),
                "source": "AkShare bond_zh_us_rate",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"获取国债收益率失败: {e}")
    return None

def fetch_fred_tips():
    """从 FRED API 获取 10年期 TIPS 实际利率"""
    print("正在从 FRED API 获取 TIPS 数据...")
    
    series_id = "DFII10"
    url = f"https://api.stlouisfed.org/fred/series/observations"
    
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'limit': 10,
        'sort_order': 'desc'
    }
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            
            if 'observations' in data:
                values = []
                for obs in data['observations']:
                    if obs['value'] != '.':
                        values.append({
                            'date': obs['date'],
                            'value': float(obs['value'])
                        })
                
                if values:
                    latest = values[0]
                    return {
                        "symbol": "US_TIPS_10Y",
                        "name": "美国10年期TIPS实际利率",
                        "series_id": series_id,
                        "latest": latest,
                        "historical": values[:5],
                        "source": "FRED API",
                        "timestamp": datetime.now().isoformat()
                    }
    except Exception as e:
        print(f"获取 TIPS 失败: {e}")
    
    return None

def fetch_bond_data():
    """获取完整债券数据"""
    print("正在获取债券数据...")
    
    treasury = fetch_us_treasury_yields()
    tips = fetch_fred_tips()
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "data": {}
    }
    
    if treasury:
        result['data']['treasury_yields'] = treasury
    
    if tips:
        result['data']['tips_10y'] = tips
    
    return result

if __name__ == "__main__":
    print("=" * 60)
    print("美国债券/利率数据")
    print("=" * 60)
    data = fetch_bond_data()
    print(json.dumps(data, indent=2, ensure_ascii=False))
