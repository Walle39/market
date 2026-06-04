#!/usr/bin/env python3
"""
获取黄金开采平均AISC成本 (All-In Sustaining Cost)
Version: 1.0

数据来源: World Gold Council - fsapi.gold.org API
AISC = 全维持成本，反映维持金矿运营的完整成本

API端点: https://fsapi.gold.org/api/productioncosts/v11/charts/aisc
"""

import requests
import json
from datetime import datetime

def fetch_aisc_data():
    """从WGC API获取AISC成本数据"""
    try:
        url = "https://fsapi.gold.org/api/productioncosts/v11/charts/aisc?break-cache=25-04-25"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.gold.org/goldhub/data/aisc-gold'
        }
        resp = requests.get(url, headers=headers, timeout=30)
        data = resp.json()
        
        if 'chartData' in data:
            chart_data = data['chartData']
            categories = chart_data.get('categories', [])
            values = chart_data.get('data', [])
            as_of_date = chart_data.get('asOfDate', '')
            
            if categories and values and len(categories) == len(values):
                # 获取最新季度数据
                latest_quarter = categories[-1]
                latest_aisc = values[-1]
                
                # 获取过去4个季度的平均值
                last_4_quarters_values = values[-4:] if len(values) >= 4 else values
                avg_4q = sum(last_4_quarters_values) / len(last_4_quarters_values)
                
                return {
                    "symbol": "AISC",
                    "name": "黄金开采全维持成本 (All-In Sustaining Cost)",
                    "latest": {
                        "quarter": latest_quarter,
                        "aisc": round(latest_aisc, 2),
                        "unit": "USD/oz"
                    },
                    "average_4q": {
                        "value": round(avg_4q, 2),
                        "unit": "USD/oz",
                        "quarters": categories[-4:] if len(categories) >= 4 else categories
                    },
                    "as_of_date": as_of_date,
                    "source": "World Gold Council",
                    "data_source": "fsapi.gold.org",
                    "timestamp": datetime.now().isoformat(),
                    "history": {
                        "quarters": categories,
                        "values": [round(v, 2) for v in values]
                    }
                }
    except Exception as e:
        print(f"获取AISC数据失败: {e}")
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("黄金开采AISC成本数据 (World Gold Council)")
    print("=" * 60)
    data = fetch_aisc_data()
    if data:
        # 只显示关键信息，不显示完整历史
        output = {
            "symbol": data["symbol"],
            "name": data["name"],
            "latest": data["latest"],
            "average_4q": data["average_4q"],
            "as_of_date": data["as_of_date"],
            "source": data["source"]
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("获取数据失败")