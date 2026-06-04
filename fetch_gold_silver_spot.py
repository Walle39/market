#!/usr/bin/env python3
"""
获取伦敦金/银现货数据 (使用新浪财经)
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
    """获取伦敦金/银现货 (新浪财经)"""
    result = {}
    
    # 获取伦敦金
    xau_data = fetch_single('hf_XAU')
    if xau_data and 'hq_str_hf_XAU' in xau_data:
        parts = xau_data.split('"')[1].split(',') if '"' in xau_data else xau_data.split(',')
        if len(parts) > 6:
            price = float(parts[0])
            pre_close = float(parts[3])
            change = price - pre_close
            change_percent = (change / pre_close) * 100
            
            result['XAU'] = {
                "symbol": "XAU",
                "name": "伦敦金现货",
                "price": price,
                "buy": float(parts[1]) if parts[1] else None,
                "sell": float(parts[2]) if parts[2] else None,
                "pre_close": pre_close,
                "high": float(parts[4]),
                "low": float(parts[5]),
                "time": parts[6],
                "open": float(parts[7]) if len(parts) > 7 and parts[7] else None,
                "date": parts[12] if len(parts) > 12 else None,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "timestamp": datetime.now().isoformat()
            }
    
    # 获取伦敦银
    xag_data = fetch_single('hf_XAG')
    if xag_data and 'hq_str_hf_XAG' in xag_data:
        parts = xag_data.split('"')[1].split(',') if '"' in xag_data else xag_data.split(',')
        if len(parts) > 6:
            price = float(parts[0])
            pre_close = float(parts[3])
            change = price - pre_close
            change_percent = (change / pre_close) * 100
            
            result['XAG'] = {
                "symbol": "XAG",
                "name": "伦敦银现货",
                "price": price,
                "buy": float(parts[1]) if parts[1] else None,
                "sell": float(parts[2]) if parts[2] else None,
                "pre_close": pre_close,
                "high": float(parts[4]),
                "low": float(parts[5]),
                "time": parts[6],
                "open": float(parts[7]) if len(parts) > 7 and parts[7] else None,
                "date": parts[12] if len(parts) > 12 else None,
                "change": round(change, 4),
                "change_percent": round(change_percent, 2),
                "timestamp": datetime.now().isoformat()
            }
    
    # 计算金银价格比 (Gold-Silver Ratio)
    if 'XAU' in result and 'XAG' in result:
        xau_price = result['XAU']['price']
        xag_price = result['XAG']['price']
        if xag_price > 0:
            gold_silver_ratio = xau_price / xag_price
            result['gold_silver_ratio'] = {
                "value": round(gold_silver_ratio, 2),
                "calculation": f"XAU({xau_price}) / XAG({xag_price})",
                "interpretation": "金银价格比表示一盎司黄金可以购买多少盎司白银",
                "note": "通常认为高于80表示黄金相对昂贵，低于60表示白银相对昂贵"
            }
    
    return result if result else None


if __name__ == "__main__":
    print("=" * 50)
    print("伦敦金/银现货数据 (新浪财经)")
    print("=" * 50)

    data = fetch_from_sina()
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("无法获取数据")
