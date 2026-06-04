#!/usr/bin/env python3
"""
获取美国 CPI 数据（同比（月度）
Version: 1.1

数据来源: AkShare (macro_usa_cpi_yoy)
"""

import akshare as ak
import json
from datetime import datetime

def fetch_usa_cpi():
    """获取美国 CPI 同比（月度）数据"""
    print("正在从 AkShare 获取美国 CPI 数据...")
    
    try:
        df = ak.macro_usa_cpi_yoy()
        
        # 去除现值为空的行
        df_clean = df.dropna(subset=['现值'])
        
        if len(df_clean) > 0:
            latest = df_clean.iloc[-1]
            
            result = {
                "symbol": "US_CPI_YOY",
                "name": "美国CPI同比（月度）",
                "time": str(latest['时间']),
                "publish_date": str(latest['发布日期']),
                "current_value": float(latest['现值']),
                "previous_value": float(latest['前值']),
                "source": "AkShare macro_usa_cpi_yoy",
                "timestamp": datetime.now().isoformat(),
                "historical_data": []
            }
            
            # 添加最近12个月的历史数据
            for i in range(1, min(13, len(df_clean)+1)):
                row = df_clean.iloc[-i]
                result['historical_data'].append({
                    "time": str(row['时间']),
                    "publish_date": str(row['发布日期']),
                    "current_value": float(row['现值']),
                    "previous_value": float(row['前值'])
                })
            
            return result
        else:
            return {
                "symbol": "US_CPI_YOY",
                "name": "美国CPI同比（月度）",
                "error": "无有效数据",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "symbol": "US_CPI_YOY",
            "name": "美国CPI同比（月度）",
            "error": f"获取失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    print("=" * 60)
    print("美国 CPI 同比（月度）数据")
    print("=" * 60)
    data = fetch_usa_cpi()
    print(json.dumps(data, indent=2, ensure_ascii=False))
