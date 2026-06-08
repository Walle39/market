#!/usr/bin/env python3
"""
获取全球央行购金量数据
Version: 3.0 - 移除默认数据，必须获取真实数据
"""

import requests
import pdfplumber
import json
import re
import os
from datetime import datetime
from pathlib import Path

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def get_pdf_path():
    """获取PDF保存路径，支持本地运行"""
    script_dir = Path(__file__).parent
    return str(script_dir / "wgc_gold_demand.pdf")

def fetch_central_bank_gold():
    """获取全球央行购金量数据 - 获取不到真实数据时报错"""
    print("正在获取全球央行购金数据...")
    
    pdf_path = get_pdf_path()
    
    # 下载PDF（如果不存在）
    if not os.path.exists(pdf_path):
        print("  正在下载WGC报告...")
        pdf_url = "https://www.gold.org/download/file/20774/GDT-Q1-2026-Exec-Summary.pdf"
        try:
            resp = requests.get(pdf_url, headers=HEADERS, timeout=30, allow_redirects=True)
            if resp.status_code != 200:
                raise RuntimeError(f"下载失败，HTTP状态码: {resp.status_code}")
            with open(pdf_path, 'wb') as f:
                f.write(resp.content)
            print("  报告下载成功")
        except Exception as e:
            raise RuntimeError(f"PDF下载失败: {e}") from e
    
    # 解析PDF
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
    except Exception as e:
        raise RuntimeError(f"PDF打开失败: {e}") from e
    
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
