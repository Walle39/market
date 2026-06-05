#!/usr/bin/env python3
"""
黄金现货技术分析脚本
计算RSI、MACD背离、均线斜率、布林带等指标并综合评分

数据来源: 新浪财经当前价格 + 上海黄金交易所历史数据
"""

import requests
import json
from datetime import datetime
import numpy as np

def fetch_gold_current_price():
    """获取黄金当前价格"""
    try:
        url = "https://hq.sinajs.cn/list=hf_XAU"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://finance.sina.com.cn/'
        }

        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'gbk'
        data_str = resp.text.split('"')[1]
        parts = data_str.split(',')

        if len(parts) < 5:
            return None

        return {
            'price': float(parts[0]),
            'pre_close': float(parts[3]),
            'high': float(parts[4]),
            'low': float(parts[5]),
            'date': parts[12] if len(parts) > 12 else datetime.now().strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"获取当前价格失败: {e}")
        return None


def fetch_gold_history_akshare():
    """使用AkShare获取黄金历史数据（上海金）"""
    try:
        import akshare as ak

        # 获取上海金历史数据
        df = ak.spot_golden_benchmark_sge()

        if df is not None and len(df) > 30:
            # 提取价格列（可能有多个）
            price_cols = [c for c in df.columns if '价' in c or 'price' in c.lower()]
            if price_cols:
                price_col = price_cols[0]
                prices = df[price_col].tolist()
                dates = df['日期'].tolist() if '日期' in df.columns else [None] * len(prices)
                return {
                    'prices': prices,
                    'dates': dates,
                    'source': 'AkShare spot_golden_benchmark_sge (上海金)'
                }
    except Exception as e:
        print(f"AkShare获取失败: {e}")

    return None


def fetch_gold_history_sina():
    """从新浪获取模拟历史数据（备用方案）"""
    try:
        url = "https://hq.sinajs.cn/list=hf_XAU"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://finance.sina.com.cn/'
        }

        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'gbk'
        data_str = resp.text.split('"')[1]
        parts = data_str.split(',')

        if len(parts) < 5:
            return None

        current_price = float(parts[0])

        # 使用随机游走模拟60天历史数据
        np.random.seed(42)
        prices = [current_price]
        for _ in range(59):
            change = np.random.normal(-0.5, current_price * 0.008)
            prices.insert(0, prices[0] + change)

        return {
            'prices': prices,
            'dates': [datetime.now().strftime('%Y-%m-%d')] * len(prices),
            'source': 'Sina (模拟数据)'
        }
    except Exception as e:
        print(f"新浪获取失败: {e}")
        return None


def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    if len(prices) < period + 1:
        return 50.0

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gains = np.mean(gains[-period:])
    avg_losses = np.mean(losses[-period:])

    if avg_losses == 0:
        return 100.0

    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi), 2)


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD指标及其背离"""
    if len(prices) < slow + signal:
        return None, None, None, 50, "数据不足"

    # 计算EMA
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    macd_line = ema_fast - ema_slow

    # 计算MACD序列用于背离检测
    macd_series = []
    for i in range(len(prices)):
        if i < slow:
            macd_series.append(0)
        else:
            ema_f = calculate_ema(prices[:i+1], fast)
            ema_s = calculate_ema(prices[:i+1], slow)
            macd_series.append(float(ema_f) - float(ema_s))

    # 计算信号线EMA
    signal_line = calculate_ema(macd_series[-signal:], signal) if len(macd_series) >= signal else 0

    # 检测背离
    divergence_score, divergence_signal = detect_macd_divergence(prices, macd_series)

    return round(float(macd_line), 2), round(float(signal_line), 2), round(float(ema_fast), 2), divergence_score, divergence_signal


def calculate_ema(prices, period):
    """计算指数移动平均"""
    if len(prices) < period:
        return float(np.mean(prices)) if prices else 0

    prices_array = np.array(prices[-period:])
    multiplier = 2 / (period + 1)
    ema = [float(prices_array[0])]
    for price in prices_array[1:]:
        ema.append((float(price) - ema[-1]) * multiplier + ema[-1])
    return ema[-1]


def detect_macd_divergence(prices, macd_series):
    """检测MACD背离 - 使用最近30天数据"""
    if len(prices) < 34 or len(macd_series) < 34:
        return 50, "数据不足"

    # 取最近30个数据点
    recent_prices = list(prices[-34:-1])
    recent_macd = list(macd_series[-34:-1])

    # 寻找价格的高点和低点
    price_low_idx = np.argmin(recent_prices)
    price_high_idx = np.argmax(recent_prices)
    macd_low_idx = np.argmin(recent_macd)
    macd_high_idx = np.argmax(recent_macd)

    # 底背离：价格在近期新低，但MACD低点高于之前低点
    if price_low_idx > 20 and price_low_idx < 30:
        # 检查MACD是否没有创新低
        prev_macd_low = np.min(recent_macd[:price_low_idx])
        if recent_macd[macd_low_idx] > prev_macd_low * 0.9:  # 放宽条件
            return 100, "底背离 - 可能上涨信号"

    # 顶背离：价格在近期新高，但MACD高点低于之前高点
    if price_high_idx > 20 and price_high_idx < 30:
        # 检查MACD是否没有创新高
        prev_macd_high = np.max(recent_macd[:price_high_idx])
        if recent_macd[macd_high_idx] < prev_macd_high * 1.1:  # 放宽条件
            return 0, "顶背离 - 可能下跌信号"

    return 50, "无背离"


def calculate_ma_slope(prices, period=20):
    """计算均线斜率（度和百分比变化）"""
    if len(prices) < period + 5:
        return 0, 0, 0, "数据不足"

    # 计算20日均线
    ma_values = []
    for i in range(period - 1, len(prices)):
        ma = np.mean(prices[i - period + 1:i + 1])
        ma_values.append(float(ma))

    if len(ma_values) < 5:
        return 0, 0, 0, "数据不足"

    # 计算斜率（线性回归）
    x = np.arange(len(ma_values))
    slope, _ = np.polyfit(x, ma_values, 1)

    # 转换为角度（度）
    angle = np.degrees(np.arctan(slope))

    # 计算百分比变化（基于最近N天）
    n_days = 5
    if len(ma_values) > n_days:
        ma_start = ma_values[-n_days - 1]
        ma_end = ma_values[-1]
        pct_change = (ma_end - ma_start) / abs(ma_start) * 100 if ma_start != 0 else 0
    else:
        pct_change = 0

    return round(float(slope), 4), round(float(angle), 2), round(pct_change, 2), "正常"


def evaluate_ma_slope_signal(slope, angle, pct_change):
    """评估均线斜率信号"""
    # 基于百分比变化评分
    # 正百分比上涨：高分
    # 负百分比下跌：低分
    
    if pct_change >= 2:
        return 100, f"强势上涨趋势 ({pct_change:.2f}%)"
    elif pct_change >= 1:
        return 80, f"温和上涨趋势 ({pct_change:.2f}%)"
    elif pct_change >= 0.5:
        return 65, f"小幅上涨趋势 ({pct_change:.2f}%)"
    elif pct_change > -0.5:
        return 50, f"中性震荡趋势 ({pct_change:.2f}%)"
    elif pct_change > -1:
        return 35, f"小幅下跌趋势 ({pct_change:.2f}%)"
    elif pct_change > -2:
        return 20, f"温和下跌趋势 ({pct_change:.2f}%)"
    else:
        return 0, f"强势下跌趋势 ({pct_change:.2f}%)"


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """计算布林带"""
    if len(prices) < period * 2:
        return None, "数据不足"

    # 计算最近20日布林带
    recent_prices = [float(p) for p in prices[-period:]]
    prev_prices = [float(p) for p in prices[-period*2:-period]]

    ma = np.mean(recent_prices)
    std = np.std(recent_prices)
    prev_ma = np.mean(prev_prices)
    prev_std = np.std(prev_prices)

    upper_band = ma + std_dev * std
    lower_band = ma - std_dev * std
    prev_upper = prev_ma + std_dev * prev_std
    prev_lower = prev_ma - std_dev * prev_std

    # 带宽
    bandwidth = (upper_band - lower_band) / ma * 100
    prev_bandwidth = (prev_upper - prev_lower) / prev_ma * 100

    # 带宽是否扩大
    bandwidth_expanding = bool(bandwidth > prev_bandwidth)

    current_price = float(prices[-1])

    return {
        'upper': round(float(upper_band), 2),
        'middle': round(float(ma), 2),
        'lower': round(float(lower_band), 2),
        'bandwidth': round(float(bandwidth), 2),
        'current': round(float(current_price), 2),
        'bandwidth_expanding': bandwidth_expanding,
        'prev_bandwidth': round(float(prev_bandwidth), 2)
    }, None


def evaluate_bollinger_signals(bollinger_data):
    """评估布林带信号"""
    if not bollinger_data:
        return 50, "数据不足"

    current = bollinger_data['current']
    upper = bollinger_data['upper']
    lower = bollinger_data['lower']
    bandwidth_expanding = bollinger_data['bandwidth_expanding']

    # 触下轨且带宽扩大
    if current <= lower * 1.01 and bandwidth_expanding:  # 允许1%误差
        return 100, "触下轨且带宽扩大 - 超卖信号(100分)"

    # 触上轨且带宽扩大
    if current >= upper * 0.99 and bandwidth_expanding:  # 允许1%误差
        return 0, "触上轨且带宽扩大 - 超买信号(0分)"

    # 其他情况
    return 50, "布林带无明显信号(50分)"


def calculate_gold_technical_analysis():
    """综合技术分析主函数"""
    print("正在获取黄金现货数据...")

    # 获取当前价格
    current_data = fetch_gold_current_price()
    if not current_data:
        return {
            "symbol": "GOLD_TECH",
            "name": "黄金现货技术分析",
            "error": "获取当前价格失败",
            "timestamp": datetime.now().isoformat()
        }

    current_price = current_data['price']

    # 尝试获取真实历史数据，否则使用模拟数据
    history_data = fetch_gold_history_akshare()
    if not history_data:
        print("AkShare获取失败，使用模拟历史数据")
        history_data = fetch_gold_history_sina()

    prices = history_data['prices']
    data_source = history_data['source']

    # 确保有足够的数据
    if len(prices) < 60:
        return {
            "symbol": "GOLD_TECH",
            "name": "黄金现货技术分析",
            "error": "历史数据不足",
            "timestamp": datetime.now().isoformat()
        }

    # 1. 计算RSI
    rsi = calculate_rsi(prices, 14)

    # 2. 计算MACD及背离
    macd, signal, ema, macd_score, macd_signal = calculate_macd(prices)

    # 3. 计算均线斜率
    slope, slope_angle, slope_pct_change, slope_status = calculate_ma_slope(prices, 20)
    ma_slope_score, ma_slope_signal = evaluate_ma_slope_signal(slope, slope_angle, slope_pct_change)

    # 4. 计算布林带
    bollinger, bollinger_status = calculate_bollinger_bands(prices, 20, 2)
    if bollinger:
        bollinger_score, bollinger_signal = evaluate_bollinger_signals(bollinger)
    else:
        bollinger_score, bollinger_signal = 50, "数据不足"

    # 计算综合评分
    # RSI: 30-70为正常区间，<30超卖(高分)，>70超买(低分)
    if rsi < 30:
        rsi_score = 100 - rsi  # 超卖，越低越高
    elif rsi > 70:
        rsi_score = 100 - rsi  # 超买，越高越低
    else:
        rsi_score = 50  # 正常区间

    # 综合评分 = RSI(25%) + MACD背离(25%) + 均线斜率(25%) + 布林带(25%)
    total_score = rsi_score * 0.25 + macd_score * 0.25 + ma_slope_score * 0.25 + bollinger_score * 0.25

    result = {
        "symbol": "GOLD_TECH",
        "name": "黄金现货技术分析",
        "current_price": current_price,
        "date": current_data['date'],
        "timestamp": datetime.now().isoformat(),

        "indicators": {
            "rsi_14": {
                "value": rsi,
                "score": rsi_score,
                "interpretation": "RSI<30超卖(高分)，RSI>70超买(低分)"
            },
            "macd_12_26_9": {
                "macd": macd,
                "signal_line": signal,
                "ema_12": ema,
                "divergence_score": macd_score,
                "signal": macd_signal
            },
            "ma_slope_20": {
                "slope": slope,
                "angle_degrees": slope_angle,
                "pct_change_5d": slope_pct_change,
                "score": ma_slope_score,
                "interpretation": ma_slope_signal
            },
            "bollinger_20_2": {
                "upper": bollinger['upper'] if bollinger else None,
                "middle": bollinger['middle'] if bollinger else None,
                "lower": bollinger['lower'] if bollinger else None,
                "bandwidth": bollinger['bandwidth'] if bollinger else None,
                "bandwidth_expanding": bollinger['bandwidth_expanding'] if bollinger else None,
                "score": bollinger_score,
                "signal": bollinger_signal
            }
        },

        "综合评分": {
            "score": round(total_score, 1),
            "max_score": 100,
            "RSI贡献": round(rsi_score * 0.25, 1),
            "MACD贡献": round(macd_score * 0.25, 1),
            "均线斜率贡献": round(ma_slope_score * 0.25, 1),
            "布林带贡献": round(bollinger_score * 0.25, 1),
            "verdict": "强势买入" if total_score >= 70 else ("弱势卖出" if total_score <= 30 else "中性观望")
        },

        "data_source": data_source,
        "note": "综合评分权重: RSI(25%) + MACD背离(25%) + 均线斜率(25%) + 布林带(25%)"
    }

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("黄金现货技术分析")
    print("=" * 60)
    result = calculate_gold_technical_analysis()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60)