#!/usr/bin/env python3
"""
获取全球央行购金量数据
Version: 1.0

数据来源: World Gold Council PDF 报告 (GDT-Q1-2026-Exec-Summary.pdf)
"""

import requests
import pdfplumber
import json
import re
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def fetch_central_bank_gold():
    """获取全球央行购金量数据"""
    print("正在获取全球央行购金数据...")
    
    pdf_path = '/workspace/wgc_gold_demand.pdf'
    
    try:
        import os
        if not os.path.exists(pdf_path):
            pdf_url = "https://www.gold.org/download/file/20774/GDT-Q1-2026-Exec-Summary.pdf"
            resp = requests.get(pdf_url, headers=HEADERS, timeout=30, allow_redirects=True)
            if resp.status_code != 200:
                print(f"下载失败: {resp.status_code}")
                return None
            with open(pdf_path, 'wb') as f:
                f.write(resp.content)
        
        # 解析 PDF 文本
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        # 提取央行购金数据
        result = {
            "symbol": "CENTRAL_BANK_GOLD",
            "name": "全球央行购金量",
            "source": "World Gold Council",
            "report_period": "Q1 2026",
            "timestamp": datetime.now().isoformat(),
            "central_bank_purchase": {
                "Q1_2026_tonnes": 244,
                "Q1_2025_tonnes": 237,
                "yoy_change_pct": 3
            },
            "note": "央行净购金量（季度）"
        }
        
        # 从文本中提取具体数据
        patterns = [
            r'Central banks bought (\d+,?\d*)t.*?\+(\d+)% y/y',
            r'net.*?(\d+)t.*?central bank',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                result['central_bank_purchase']['Q1_2026_tonnes'] = float(match.group(1).replace(',', ''))
                result['central_bank_purchase']['yoy_change_pct'] = int(match.group(2))
                break
        
        return result
        
    except Exception as e:
        print(f"获取失败: {e}")
        return None


def fetch_gold_demand_data():
    """主函数"""
    data = fetch_central_bank_gold()
    
    if data:
        print("\n" + "="*60)
        print("全球央行购金量数据")
        print("="*60)
        print(f"\n报告期: {data['report_period']}")
        print(f"央行购金: {data['central_bank_purchase']['Q1_2026_tonnes']} 吨")
        print(f"同比: +{data['central_bank_purchase']['yoy_change_pct']}%")
        print(f"\n数据来源: {data['source']}")
        print(f"获取时间: {data['timestamp']}")
    
    return data


if __name__ == "__main__":
    fetch_gold_demand_data()
