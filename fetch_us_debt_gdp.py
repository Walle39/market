#!/usr/bin/env python3
"""
获取美国国债总量、GDP总量及国债占GDP百分比
Version: 2.0

数据来源:
- FRED API (联邦储备经济数据) - 主数据源
  - 国债总量: GFDEBTN (联邦政府债务总规模)
  - GDP总量: GDP (国内生产总值)
- TwelveData API - 辅助参考
  - TLT (20+年期美国国债ETF)

国债/GDP比率是衡量国家财政健康的重要指标
"""

import urllib.request
import json
from datetime import datetime

FRED_API_KEY = "5829f98ab0ac4f79358f2f85d98e5e89"
TWELVEDATA_API_KEY = "1a0c6578fc804d48b672bb7346d528a7"

def fetch_fred_data(series_id):
    """从FRED API获取数据"""
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&limit=1&sort_order=desc"
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            if 'observations' in data and len(data['observations']) > 0:
                obs = data['observations'][-1]
                return {
                    "date": obs.get('date', ''),
                    "value": float(obs.get('value', 0)),
                    "series_id": series_id
                }
    except Exception as e:
        print(f"获取{series_id}数据失败: {e}")
    return None

def fetch_tlt_data():
    """从TwelveData API获取TLT国债ETF数据"""
    try:
        url = f"https://api.twelvedata.com/quote?symbol=TLT&apikey={TWELVEDATA_API_KEY}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            if 'status' not in data or data['status'] != 'error':
                return {
                    "symbol": "TLT",
                    "name": data.get('name', 'iShares 20+ Year Treasury Bond ETF'),
                    "price": float(data.get('close', 0)),
                    "change": float(data.get('change', 0)),
                    "percent_change": float(data.get('percent_change', 0)),
                    "high": float(data.get('high', 0)),
                    "low": float(data.get('low', 0)),
                    "volume": int(data.get('volume', 0)),
                    "datetime": data.get('datetime', ''),
                    "previous_close": float(data.get('previous_close', 0)),
                    "fifty_two_week_high": float(data.get('fifty_two_week', {}).get('high', 0)),
                    "fifty_two_week_low": float(data.get('fifty_two_week', {}).get('low', 0))
                }
    except Exception as e:
        print(f"获取TLT数据失败: {e}")
    return None


def fetch_us_debt_gdp():
    """获取美国国债总量、GDP总量并计算比率"""
    print("正在获取美国国债和GDP数据...")

    # 从FRED获取国债总量 (单位: 百万美元)
    debt_data = fetch_fred_data("GFDEBTN")

    # 从FRED获取GDP总量 (单位: 十亿美元)
    gdp_data = fetch_fred_data("GDP")

    # 从TwelveData获取TLT国债ETF作为辅助参考
    tlt_data = fetch_tlt_data()

    # 构建结果
    result = {
        "symbol": "US_DEBT_GDP_RATIO",
        "name": "美国国债占GDP百分比",
        "timestamp": datetime.now().isoformat()
    }

    if debt_data and gdp_data:
        # 国债单位: 百万美元
        debt_millions = debt_data["value"]
        # GDP单位: 十亿美元，需要转换为百万美元
        gdp_millions = gdp_data["value"] * 1000

        # 计算国债占GDP百分比
        debt_to_gdp = (debt_millions / gdp_millions) * 100

        result["national_debt"] = {
            "value": debt_millions,
            "unit": "百万美元",
            "date": debt_data["date"],
            "series_id": debt_data["series_id"],
            "display": f"${debt_millions/1000:.2f} 万亿美元" if debt_millions > 1000000 else f"${debt_millions:.2f} 百万美元"
        }

        result["gdp"] = {
            "value": gdp_data["value"],
            "unit": "十亿美元",
            "date": gdp_data["date"],
            "series_id": gdp_data["series_id"],
            "display": f"${gdp_data['value']:.2f} 万亿美元" if gdp_data['value'] > 1000 else f"${gdp_data['value']:.2f} 十亿美元"
        }

        result["debt_to_gdp_ratio"] = {
            "value": round(debt_to_gdp, 2),
            "unit": "%",
            "calculation": f"国债({debt_millions:,.0f}百万) / GDP({gdp_millions:,.0f}百万) × 100"
        }

        result["analysis"] = {
            "description": "国债占GDP比率是衡量国家财政可持续性的关键指标",
            "interpretation": "比率越高表示国家债务负担越重",
            "reference": {
                "低于60%": "相对安全的水平",
                "60%-90%": "需要注意",
                "90%-120%": "较高风险",
                "超过120%": "极高风险，可能引发债务危机"
            }
        }

        result["data_source"] = "FRED API"
        result["source_url"] = "https://fred.stlouisfed.org/"

        # 添加TLT国债ETF数据作为辅助参考
        if tlt_data:
            result["tlt_etf_reference"] = {
                "symbol": tlt_data["symbol"],
                "name": tlt_data["name"],
                "price": tlt_data["price"],
                "change": tlt_data["change"],
                "percent_change": tlt_data["percent_change"],
                "volume": tlt_data["volume"],
                "datetime": tlt_data["datetime"],
                "52w_high": tlt_data["fifty_two_week_high"],
                "52w_low": tlt_data["fifty_two_week_low"],
                "note": "TLT是20+年期美国国债ETF，价格走势反映市场对长期国债的预期"
            }
    else:
        if not debt_data:
            result["error"] = "无法获取国债数据"
        if not gdp_data:
            result["error"] = result.get("error", "") + "无法获取GDP数据"

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("美国国债与GDP数据")
    print("=" * 60)
    data = fetch_us_debt_gdp()
    print(json.dumps(data, indent=2, ensure_ascii=False))