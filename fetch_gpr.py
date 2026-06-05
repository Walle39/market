#!/usr/bin/env python3
"""
获取 GPR 地缘政治风险指数月度数据
Version: 2.0

数据来源: https://www.matteoiacoviello.com/gpr.htm
下载链接: https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls

GPR指数由Dario Caldara和Matteo Iacoviello构建，基于报纸报道中地缘政治紧张事件的统计
"""

import urllib.request
import ssl
import os
import json
from datetime import datetime

GPR_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"
OUTPUT_FILE = "gpr_monthly_data.xls"

def download_gpr_data():
    """下载GPR月度数据Excel文件"""
    try:
        # 创建SSL上下文，跳过证书验证
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            GPR_URL,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.matteoiacoviello.com/gpr.htm'
            }
        )

        with urllib.request.urlopen(req, timeout=60, context=ssl_context) as resp:
            data = resp.read()

            with open(OUTPUT_FILE, 'wb') as f:
                f.write(data)

            return True

    except Exception as e:
        print(f"下载失败: {e}")
        return False


def get_latest_gpr():
    """获取最新的GPR数据"""
    try:
        import xlrd

        if not os.path.exists(OUTPUT_FILE):
            if not download_gpr_data():
                return None

        workbook = xlrd.open_workbook(OUTPUT_FILE)
        sheet = workbook.sheet_by_index(0)

        # 获取最后一行数据
        last_row = sheet.nrows - 1
        excel_date = sheet.cell_value(last_row, 0)
        gpr_value = sheet.cell_value(last_row, 1)
        gprt_value = sheet.cell_value(last_row, 2)
        gpra_value = sheet.cell_value(last_row, 3)

        # Excel日期转换
        year, month, day, hour, minute, second = xlrd.xldate_as_tuple(excel_date, workbook.datemode)
        date_str = f"{year}-{month:02d}-{day:02d}"

        result = {
            "symbol": "GPR",
            "name": "地缘政治风险指数",
            "date": date_str,
            "gpr": round(gpr_value, 2),
            "gprt": round(gprt_value, 2),
            "gpra": round(gpra_value, 2),
            "data_source": "https://www.matteoiacoviello.com/gpr.htm",
            "update_note": "每月初更新（最后更新: May 1, 2026）",
            "timestamp": datetime.now().isoformat()
        }

        return result

    except ImportError:
        print("需要安装 xlrd 库")
        return None
    except Exception as e:
        print(f"获取GPR数据失败: {e}")
        return None


def fetch_gpr():
    """主函数：获取并返回GPR数据"""
    print("正在获取GPR地缘政治风险指数...")
    
    # 检查文件是否存在，不存在则下载
    if not os.path.exists(OUTPUT_FILE):
        download_gpr_data()
    
    result = get_latest_gpr()
    
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("GPR 地缘政治风险指数月度数据")
    print("=" * 60)
    fetch_gpr()
    print("=" * 60)
    print("数据说明:")
    print("- GPR: 地缘政治风险指数")
    print("- GPRT: 地缘政治威胁指数 (Categories 1-5)")
    print("- GPRA: 地缘政治行动指数 (Categories 6-8)")
    print("- 还有各国特定的GPR指数")
    print("=" * 60)