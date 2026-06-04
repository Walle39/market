#!/usr/bin/env python3
"""
获取 DXY 美元指数数据
Version: 7.0

数据来源优先级:
1. 新浪财经 DINIW 接口 (优先)
2. ExchangeRate-API (备用)
"""

import requests
import json
from datetime import datetime

def fetch_from_sina():
    """从新浪财经获取美元指数 DINIW"""
    url = "https://hq.sinajs.cn/list=DINIW"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://finance.sina.com.cn/'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'gbk'
        
        if 'hq_str_DINIW' in resp.text:
            data_str = resp.text.split('"')[1]
            parts = data_str.split(',')
            
            if len(parts) >= 11:
                price = float(parts[1]) if parts[1] else None
                pre_close = float(parts[3]) if parts[3] else None
                
                # 计算涨幅和涨跌额
                change = None
                change_percent = None
                if price is not None and pre_close is not None and pre_close != 0:
                    change = price - pre_close
                    change_percent = (change / pre_close) * 100
                
                return {
                    "symbol": "DXY",
                    "name": parts[9] if len(parts) > 9 else "美元指数",
                    "price": price,
                    "open": float(parts[2]) if parts[2] else None,
                    "pre_close": pre_close,
                    "bid": float(parts[5]) if parts[5] else None,
                    "ask": float(parts[8]) if parts[8] else None,
                    "high": float(parts[6]) if parts[6] else None,
                    "low": float(parts[7]) if parts[7] else None,
                    "change": round(change, 4) if change is not None else None,
                    "change_percent": round(change_percent, 2) if change_percent is not None else None,
                    "time": parts[0] if len(parts) > 0 else None,
                    "date": parts[10] if len(parts) > 10 else None,
                    "source": "新浪财经 DINIW",
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        print(f"新浪财经获取失败: {e}")
    return None

def fetch_dxy_index():
    """获取美元指数 - 优先使用新浪财经"""
    print("正在从新浪财经获取美元指数...")
    
    # 优先使用新浪财经
    data = fetch_from_sina()
    if data:
        return data
    
    # 新浪财经失败，可以添加备用方案
    return {
        "symbol": "DXY",
        "name": "美元指数",
        "error": "无法获取美元指数数据",
        "note": "新浪财经 DINIW 接口访问失败",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("=" * 50)
    print("DXY 美元指数数据 (新浪财经)")
    print("=" * 50)
    data = fetch_dxy_index()
    print(json.dumps(data, indent=2, ensure_ascii=False))
