#!/usr/bin/env python3
"""
使用 AkShare macro_cons_gold() 获取黄金持仓数据
"""

import akshare as ak
import json
from datetime import datetime

def fetch_gold_holdings():
    """获取黄金持仓数据"""
    print("正在从 AkShare 获取黄金持仓数据...")
    
    try:
        df = ak.macro_cons_gold()
        
        # 获取最近的数据
        df_clean = df.dropna(subset=['总库存'])
        
        if len(df_clean) > 0:
            latest = df_clean.iloc[-1]
            
            result = {
                "symbol": "GOLD_HOLDINGS",
                "name": "黄金ETF持仓",
                "source": "AkShare macro_cons_gold",
                "unit": "百万美元 / 吨",
                "latest": {
                    "date": str(latest['日期']),
                    "total_inventory": float(latest['总库存']),
                    "change": float(latest['增持/减持']),
                    "total_value": float(latest['总价值'])
                },
                "timestamp": datetime.now().isoformat(),
                "historical_data": []
            }
            
            # 添加最近20条数据
            for i in range(1, min(21, len(df_clean)+1)):
                row = df_clean.iloc[-i]
                result['historical_data'].append({
                    "date": str(row['日期']),
                    "total_inventory": float(row['总库存']),
                    "change": float(row['增持/减持']),
                    "total_value": float(row['总价值'])
                })
            
            return result
        else:
            return {
                "symbol": "GOLD_HOLDINGS",
                "name": "黄金ETF持仓",
                "error": "无有效数据",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "symbol": "GOLD_HOLDINGS",
            "name": "黄金ETF持仓",
            "error": f"获取失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    print("=" * 60)
    print("黄金 ETF 持仓数据 (AkShare)")
    print("=" * 60)
    data = fetch_gold_holdings()
    print(json.dumps(data, indent=2, ensure_ascii=False))
