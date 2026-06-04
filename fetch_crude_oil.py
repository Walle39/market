#!/usr/bin/env python3
"""
获取原油价格数据 (使用新浪财经)
Version: 3.0
"""

import requests
import json
from datetime import datetime


def fetch_from_sina():
    """获取原油价格 (新浪财经)"""
    url = 'https://hq.sinajs.cn'
    params = {'list': 'hf_OIL'}
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn/'}
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.encoding = 'gbk'
        
        if 'hq_str_hf_OIL' in resp.text:
            parts = resp.text.split('"')[1].split(',') if '"' in resp.text else resp.text.split(',')
            if len(parts) > 6:
                result = {
                    "symbol": "OIL",
                    "name": "布伦特原油",
                    "price": float(parts[0]),
                    "buy": float(parts[1]) if parts[1] else None,
                    "sell": float(parts[2]) if parts[2] else None,
                    "pre_close": float(parts[3]),
                    "high": float(parts[4]),
                    "low": float(parts[5]),
                    "time": parts[6],
                    "open": float(parts[7]) if len(parts) > 7 and parts[7] else None,
                    "date": parts[12] if len(parts) > 12 else None,
                    "timestamp": datetime.now().isoformat()
                }
                return result
        return None
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("=" * 50)
    print("原油价格数据 (新浪财经)")
    print("=" * 50)

    data = fetch_from_sina()
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("无法获取数据")
