#!/usr/bin/env python3
"""
获取美国 M2 货币供应量数据（月度）
Version: 1.0

数据来源: FRED API (Federal Reserve Economic Data)
系列代码: M2SL (M2 Money Supply, Seasonally Adjusted)
"""

import requests
import json
from datetime import datetime

FRED_API_KEY = "5829f98ab0ac4f79358f2f85d98e5e89"

def fetch_fred_m2():
    """从 FRED API 获取美国 M2 数据"""
    
    series_id = "M2SL"
    base_url = f"https://api.stlouisfed.org/fred/series/observations"
    
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'limit': 13,  # 最近13个月
        'sort_order': 'desc'
    }
    
    print(f"正在从 FRED API 获取 M2 数据...")
    
    try:
        resp = requests.get(base_url, params=params, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            
            if 'observations' in data:
                observations = data['observations']
                
                # 解析数据
                values = []
                for obs in observations:
                    if obs['value'] != '.':
                        values.append({
                            'date': obs['date'],
                            'value': float(obs['value'])
                        })
                
                if len(values) >= 2:
                    # 计算年增长率
                    latest = values[0]
                    year_ago = values[12] if len(values) >= 13 else values[-1]
                    yoy_change = None
                    
                    if len(values) >= 13 and year_ago['value']:
                        yoy_change = round(((latest['value'] - year_ago['value']) / year_ago['value']) * 100, 2)
                    
                    return {
                        "symbol": "US_M2",
                        "name": "美国M2货币供应量（月度）",
                        "series_id": series_id,
                        "unit": "Billions of Dollars",
                        "latest": {
                            "date": latest['date'],
                            "value": latest['value']
                        },
                        "yoy_change_percent": yoy_change,
                        "source": "FRED (Federal Reserve Economic Data)",
                        "timestamp": datetime.now().isoformat(),
                        "historical_data": values[:13]
                    }
        else:
            print(f"请求失败: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"请求异常: {e}")
    
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("美国 M2 货币供应量数据 (FRED API)")
    print("=" * 60)
    data = fetch_fred_m2()
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
