#!/usr/bin/env python3
"""
获取 VIX 恐慌指数数据
Version: 5.1

数据来源:
1. 新浪财经 gb_vix 等接口 (尝试失败，返回空数据)
2. TwelveData API (使用 ETF 作为替代)
"""

import requests
import json
from datetime import datetime

API_KEY = "1a0c6578fc804d48b672bb7346d528a7"
BASE_URL = "https://api.twelvedata.com"

def fetch_from_sina():
    """尝试从新浪财经获取 VIX (返回空数据)"""
    codes = ['gb_vix', 'hf_VIX', 'hf_vix', 'VIX', 'gb_vixnq', 'gb_vixcboe', 's_vix', 'us_VIX']
    
    for code in codes:
        url = f"https://hq.sinajs.cn/list={code}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://finance.sina.com.cn/'
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = 'gbk'
            if f'"' in resp.text and resp.text.split('"')[1].strip():
                data_str = resp.text.split('"')[1]
                parts = data_str.split(',')
                if len(parts) > 1 and parts[1]:
                    return {
                        "symbol": "VIX",
                        "name": "VIX恐慌指数",
                        "price": float(parts[1]) if parts[1] else None,
                        "source": f"新浪财经 {code}"
                    }
        except Exception:
            continue
    return None

def fetch_twelvedata_quote(symbol):
    """从 TwelveData 获取实时报价"""
    url = f"{BASE_URL}/quote"
    params = {
        'symbol': symbol,
        'apikey': API_KEY
    }
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        if 'status' in data and data['status'] == 'error':
            return None
        
        return data
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def fetch_vix():
    """获取 VIX 恐慌指数 - 优先尝试新浪，失败则用 ETF 替代"""
    print("正在从新浪财经获取 VIX...")
    # 先尝试新浪财经
    sina_data = fetch_from_sina()
    if sina_data:
        return sina_data
    
    print("新浪财经获取失败，尝试 TwelveData ETF...")
    # VIX ETF 替代品
    vix_etfs = [
        ('VXX', 'iPath Series B S&P 500 VIX Short-Term Futures ETN'),
        ('VIXY', 'ProShares VIX Short-Term Futures ETF'),
        ('UVXY', 'ProShares Ultra VIX Short-Term Futures ETF'),
        ('VIXM', 'ProShares VIX Mid-Term Futures ETF')
    ]
    
    results = {}
    
    for symbol, name in vix_etfs:
        data = fetch_twelvedata_quote(symbol)
        if data and 'close' in data:
            results[symbol] = {
                "symbol": symbol,
                "name": name,
                "price": float(data.get('close', 0)),
                "open": float(data.get('open', 0)) if data.get('open') else None,
                "high": float(data.get('high', 0)) if data.get('high') else None,
                "low": float(data.get('low', 0)) if data.get('low') else None,
                "change": float(data.get('change', 0)) if data.get('change') else None,
                "change_percent": data.get('percent_change'),
                "volume": data.get('volume'),
                "datetime": data.get('datetime'),
                "source": "TwelveData API",
                "timestamp": datetime.now().isoformat()
            }
    
    if results:
        return {
            "symbol": "VIX",
            "name": "VIX恐慌指数",
            "note": "新浪财经 VIX 接口返回空数据，以下 ETF 可作为替代参考",
            "primary_etf": results.get('VXX', results.get('VIXY')),
            "alternative_etfs": results,
            "explanation": {
                "VXX": "VIX短期期货ETN，与VIX指数相关性较高",
                "VIXY": "ProShares VIX短期期货ETF",
                "UVXY": "1.5x杠杆VIX短期期货ETF",
                "VIXM": "VIX中期期货ETF"
            },
            "source": "TwelveData API",
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "symbol": "VIX",
        "name": "VIX恐慌指数",
        "error": "无法获取数据",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("=" * 50)
    print("VIX 恐慌指数数据")
    print("=" * 50)
    data = fetch_vix()
    print(json.dumps(data, indent=2, ensure_ascii=False))
