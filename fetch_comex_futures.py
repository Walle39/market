#!/usr/bin/env python3
"""
获取COMEX金/银期货数据 (使用新浪财经)
Version: 2.2
"""

import requests
import json
from datetime import datetime


def fetch_single(code):
    """获取单个品种数据"""
    url = 'https://hq.sinajs.cn'
    params = {'list': code}
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn/'}
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.encoding = 'gbk'
        return resp.text
    except Exception:
        return None


def fetch_from_sina():
    """获取COMEX金/银期货 (新浪财经)"""
    result = {}
    
    # 获取COMEX黄金
    gc_data = fetch_single('hf_GC')
    if gc_data and 'hq_str_hf_GC' in gc_data:
        parts = gc_data.split('"')[1].split(',') if '"' in gc_data else gc_data.split(',')
        if len(parts) > 6:
            result['GC'] = {
                "symbol": "GC",
                "name": "COMEX黄金期货",
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
    
    # 获取COMEX白银
    si_data = fetch_single('hf_SI')
    if si_data and 'hq_str_hf_SI' in si_data:
        parts = si_data.split('"')[1].split(',') if '"' in si_data else si_data.split(',')
        if len(parts) > 6:
            result['SI'] = {
                "symbol": "SI",
                "name": "COMEX白银期货",
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
    
    return result if result else None


if __name__ == "__main__":
    print("=" * 50)
    print("COMEX金/银期货数据 (新浪财经)")
    print("=" * 50)

    data = fetch_from_sina()
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("无法获取数据")
