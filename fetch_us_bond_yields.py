#!/usr/bin/env python3
"""
使用 AkShare bond_zh_us_rate 获取美国国债收益率
"""

import akshare as ak
import json
from datetime import datetime

def fetch_us_bond_yields():
    """获取美国国债收益率"""
    try:
        df = ak.bond_zh_us_rate()
        if df is not None and not df.empty:
            # 获取最新一行
            latest = df.iloc[-1]
            return {
                "symbol": "US_BOND_YIELDS",
                "name": "美国国债收益率",
                "date": str(latest.get('日期', '')),
                "yields": {
                    "2_year": latest.get('美国国债收益率2年'),
                    "5_year": latest.get('美国国债收益率5年'),
                    "10_year": latest.get('美国国债收益率10年'),
                    "30_year": latest.get('美国国债收益率30年'),
                },
                "spread_10_2": latest.get('美国国债收益率10年-2年'),
                "source": "AkShare/bond_zh_us_rate",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {"error": str(e)}
    return {"error": "No data"}

if __name__ == "__main__":
    print("=" * 50)
    print("美国国债收益率数据")
    print("=" * 50)
    data = fetch_us_bond_yields()
    print(json.dumps(data, indent=2, ensure_ascii=False))