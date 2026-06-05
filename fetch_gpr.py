#!/usr/bin/env python3
"""
获取 GPR 地缘政治风险指数月度数据
Version: 1.0

数据来源: https://www.matteoiacoviello.com/gpr.htm
下载链接: https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls

GPR指数由Dario Caldara和Matteo Iacoviello构建，基于报纸报道中地缘政治紧张事件的统计
"""

import urllib.request
import ssl
import os
from datetime import datetime

GPR_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"
OUTPUT_FILE = "gpr_monthly_data.xls"

def download_gpr_data():
    """下载GPR月度数据Excel文件"""
    print("正在下载GPR月度数据...")

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

            file_size = os.path.getsize(OUTPUT_FILE)
            print(f"下载完成！文件已保存为: {OUTPUT_FILE}")
            print(f"文件大小: {file_size / 1024:.2f} KB")
            return True

    except Exception as e:
        print(f"下载失败: {e}")
        return False


def read_gpr_data():
    """读取GPR数据（需要xlrd库）"""
    try:
        import xlrd

        if not os.path.exists(OUTPUT_FILE):
            print(f"文件 {OUTPUT_FILE} 不存在，请先运行下载功能")
            return None

        workbook = xlrd.open_workbook(OUTPUT_FILE)
        sheet = workbook.sheet_by_index(0)

        print(f"\n工作表名称: {sheet.name}")
        print(f"行数: {sheet.nrows}, 列数: {sheet.ncols}")

        # 读取表头
        headers = [sheet.cell_value(0, col) for col in range(sheet.ncols)]
        print(f"\n列名: {headers[:10]}...")  # 只显示前10列

        # 读取最后5行数据
        print("\n最新5行数据:")
        for row in range(max(1, sheet.nrows - 5), sheet.nrows):
            row_data = [sheet.cell_value(row, col) for col in range(min(10, sheet.ncols))]
            print(f"  {row_data}")

        return True

    except ImportError:
        print("提示: 需要安装 xlrd 库来读取Excel文件")
        print("运行: pip install xlrd")
        return None
    except Exception as e:
        print(f"读取失败: {e}")
        return None


def main():
    print("=" * 60)
    print("GPR 地缘政治风险指数月度数据下载器")
    print("=" * 60)
    print(f"数据来源: {GPR_URL}")
    print(f"更新时间: 每月初更新（最后更新: May 1, 2026）")
    print("=" * 60)

    # 下载数据
    success = download_gpr_data()

    if success:
        # 读取并显示数据
        read_gpr_data()

        print("\n" + "=" * 60)
        print("数据说明:")
        print("- GPR: 地缘政治风险指数")
        print("- GPRT: 地缘政治威胁指数 (Categories 1-5)")
        print("- GPRA: 地缘政治行动指数 (Categories 6-8)")
        print("- 还有各国特定的GPR指数")
        print("=" * 60)


if __name__ == "__main__":
    main()