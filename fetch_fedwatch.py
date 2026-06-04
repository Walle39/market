#!/usr/bin/env python3
"""
获取信用利差数据 (Credit Spread)
Version: 1.0

信用利差 = BAA企业债收益率 - 10年期美国国债收益率

数据来源:
- 10年期美国国债收益率: AkShare
- 企业债收益率: 使用LQD ETF收益率作为代理指标
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
                "2_year": float(latest.get('美国国债收益率2年', 0)),
                "5_year": float(latest.get('美国国债收益率5年', 0)),
                "10_year": float(latest.get('美国国债收益率10年', 0)),
                "30_year": float(latest.get('美国国债收益率30年', 0)),
                "source": "AkShare"
            }
    except Exception as e:
        print(f"获取国债收益率失败: {e}")
    return None

def fetch_corporate_bond_yield():
    """获取企业债收益率代理数据"""
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
                "time": parts[3],
                "change_percent": float(parts[4]),
                "volume": float(parts[10]),
                "source": "新浪财经"
            }
    except Exception as e:
        print(f"获取企业债ETF数据失败: {e}")
    
    return None

def fetch_credit_spread():
    """计算信用利差"""
    print("正在获取信用利差数据...")
    
    # 获取国债收益率
    bond_yields = fetch_us_bond_yields()
    
    # 获取企业债收益率代理
    corporate_bond = fetch_corporate_bond_yield()
    
    # 构建结果
    result = {
        "symbol": "CREDIT_SPREAD",
        "name": "信用利差",
        "description": "信用利差 = BAA企业债收益率 - 10年期美国国债收益率",
        "data_source": "AkShare + 新浪财经",
        "timestamp": datetime.now().isoformat()
    }
    
    if bond_yields and corporate_bond:
        # 使用LQD ETF收益率作为企业债收益率代理
        # 注意：实际BAA收益率需要FRED等数据源，这里使用ETF价格作为参考
        result["us_bond_10y"] = {
            "yield": bond_yields["10_year"],
            "date": bond_yields["date"],
            "source": bond_yields["source"]
        }
        
        result["corporate_bond_proxy"] = corporate_bond
        
        result["analysis"] = {
            "description": "信用利差反映市场对企业信用风险的评估",
            "interpretation": "利差扩大通常表示风险偏好下降，利差收窄表示风险偏好上升",
            "note": "由于AkShare未提供BAA企业债收益率，使用LQD ETF作为代理指标"
        }
        
        result["limitations"] = [
            "1. AkShare暂未提供直接的BAA企业债收益率数据",
            "2. 使用LQD ETF价格作为企业债市场状况的代理指标",
            "3. 如需精确的BAA收益率，建议使用FRED API (series_id: BAA)",
            "4. 实际信用利差计算需要企业债收益率与国债收益率的差值"
        ]
    else:
        if not bond_yields:
            result["error"] = "无法获取国债收益率数据"
        if not corporate_bond:
            result["error"] = result.get("error", "") + "无法获取企业债数据"
    
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("信用利差数据 (Credit Spread)")
    print("=" * 60)
    data = fetch_credit_spread()
    print(json.dumps(data, indent=2, ensure_ascii=False))
