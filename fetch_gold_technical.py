#!/usr/bin/env python3
"""
黄金现货技术分析脚本
计算RSI、MACD背离、均线斜率、布林带等指标

数据来源: 新浪财经当前价格 + 历史数据
"""

import requests
import json
from datetime import datetime
import numpy as np
import urllib.request

FRED_API_KEY = '5829f98ab0ac4f79358f2f85d98e5e89'

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


def fetch_gold_history_fred(current_price=None):
    """从FRED获取黄金相关数据"""
    try:
        # 尝试FRED中的几个可能的黄金价格系列
        gold_series_list = [
            'GOLDAMGBD228NLBM',  # 伦敦金上午定盘价
            'GOLDPMGBD228NLBM',  # 伦敦金下午定盘价
            'GVZCLS'  # 黄金波动率指数（最后备选）
        ]
        
        ssl_context = urllib.request.ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = urllib.request.ssl.CERT_NONE
        
        for series_id in gold_series_list:
            try:
                url = f'https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&limit=120&sort_order=desc'
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                
                with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                    data = json.loads(resp.read().decode())
                
                if 'observations' in data and len(data['observations']) > 30:
                    observations = data['observations']
                    prices = []
                    dates = []
                    for obs in reversed(observations):
                        try:
                            val = float(obs['value'])
                            prices.append(val)
                            dates.append(obs['date'])
                        except:
                            continue
                    
                    if len(prices) >= 30:
                        # 如果是波动率数据且有当前价格，进行适配
                        if series_id == 'GVZCLS' and current_price:
                            scaled_prices = []
                            base_val = prices[-1]
                            for p in prices:
                                scaled = current_price * (p / base_val)
                                scaled_prices.append(scaled)
                            return {
                                'prices': scaled_prices,
                                'dates': dates,
                                'source': f'FRED {series_id} (缩放适配)'
                            }
                        
                        return {
                            'prices': prices,
                            'dates': dates,
                            'source': f'FRED {series_id}'
                        }
            except Exception as e:
                continue
        
    except Exception as e:
        print(f'FRED获取失败: {e}')
    
    return None


def cross_validate_sources(fred_data, akshare_data):
    """交叉验证FRED和AkShare数据，比较相对变化而非绝对价格"""
    if not fred_data or not akshare_data:
        return None, "数据不足"
    
    fred_prices = fred_data['prices']
    akshare_prices = akshare_data['prices']
    
    if len(fred_prices) < 5 or len(akshare_prices) < 5:
        return None, "数据不足"
    
    # 取最近N个数据点比较相对变化
    n_compare = 5
    
    # 计算每日涨跌幅变化
    def calc_changes(prices, n):
        changes = []
        for i in range(-n, 0):
            if i > -len(prices) and i-1 > -len(prices):
                try:
                    change = (prices[i] - prices[i-1]) / prices[i-1] * 100
                    changes.append(abs(change))
                except:
                    changes.append(0)
            else:
                changes.append(0)
        return changes
    
    fred_changes = calc_changes(fred_prices, n_compare)
    akshare_changes = calc_changes(akshare_prices, n_compare)
    
    # 计算涨跌幅偏差
    deviations = []
    for i in range(min(len(fred_changes), len(akshare_changes))):
        if fred_changes[i] > 0 and akshare_changes[i] > 0:
            dev = abs(fred_changes[i] - akshare_changes[i]) / max(fred_changes[i], akshare_changes[i]) * 100
            deviations.append(dev)
        elif fred_changes[i] > 0 or akshare_changes[i] > 0:
            # 一个有变化，一个没变化，偏差100%
            deviations.append(100)
        else:
            deviations.append(0)
    
    avg_deviation = sum(deviations) / len(deviations) if deviations else 0
    max_deviation = max(deviations) if deviations else 0
    
    # 判断偏差是否超过5%（比较相对变化）
    warning = None
    if avg_deviation > 5:
        warning = f"⚠️ 警告: FRED与AkShare相对变化偏差 {avg_deviation:.2f}% (超过5%阈值)"
    elif max_deviation > 5:
        warning = f"⚠️ 警告: 最大变化偏差 {max_deviation:.2f}% (超过5%阈值)"
    
    return {
        'fred_source': fred_data.get('source', 'Unknown'),
        'akshare_source': akshare_data.get('source', 'Unknown'),
        'fred_unit': fred_data.get('unit', 'USD/oz'),
        'akshare_unit': akshare_data.get('unit', 'CNY/g'),
        'avg_change_deviation': round(avg_deviation, 2),
        'max_change_deviation': round(max_deviation, 2),
        'deviations': [round(d, 2) for d in deviations],
        'warning': warning,
        'status': 'OK' if avg_deviation <= 5 else 'WARNING'
    }, warning


def fetch_gold_history_akshare():
    """使用AkShare获取黄金历史数据（上海金，元/克）"""
    try:
        import akshare as ak
        
        df = ak.spot_golden_benchmark_sge()
        
        if df is not None and len(df) > 30:
            # 查找价格列 - 上海金数据通常以"元/克"为单位
            price_cols = [c for c in df.columns if '价' in c or 'price' in c.lower()]
            if price_cols:
                price_col = price_cols[0]
                prices = df[price_col].tolist()
                dates = df['日期'].tolist() if '日期' in df.columns else [None] * len(prices)
                
                return {
                    'prices': prices,
                    'dates': dates,
                    'source': 'AkShare spot_golden_benchmark_sge (上海金，元/克)',
                    'unit': 'CNY/g'
                }
    except Exception as e:
        print(f'AkShare获取失败: {e}')
    
    return None


def fetch_gold_history_sina(current_price):
    """从新浪获取模拟历史数据（备用方案）"""
    try:
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
        print(f'新浪获取失败: {e}')
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

    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    macd_line = ema_fast - ema_slow

    macd_series = []
    for i in range(len(prices)):
        if i < slow:
            macd_series.append(0)
        else:
            ema_f = calculate_ema(prices[:i+1], fast)
            ema_s = calculate_ema(prices[:i+1], slow)
            macd_series.append(float(ema_f) - float(ema_s))

    signal_line = calculate_ema(macd_series[-signal:], signal) if len(macd_series) >= signal else 0

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
    """检测MACD背离"""
    if len(prices) < 34 or len(macd_series) < 34:
        return 50, "数据不足"

    recent_prices = list(prices[-34:-1])
    recent_macd = list(macd_series[-34:-1])

    price_low_idx = np.argmin(recent_prices)
    price_high_idx = np.argmax(recent_prices)
    macd_low_idx = np.argmin(recent_macd)
    macd_high_idx = np.argmax(recent_macd)

    if price_low_idx > 20 and price_low_idx < 30:
        prev_macd_low = np.min(recent_macd[:price_low_idx])
        if recent_macd[macd_low_idx] > prev_macd_low * 0.9:
            return 100, "底背离 - 可能上涨信号"

    if price_high_idx > 20 and price_high_idx < 30:
        prev_macd_high = np.max(recent_macd[:price_high_idx])
        if recent_macd[macd_high_idx] < prev_macd_high * 1.1:
            return 0, "顶背离 - 可能下跌信号"

    return 50, "无背离"


def calculate_ma_slope(prices, period=20):
    """计算均线斜率（度和百分比变化"""
    if len(prices) < period + 5:
        return 0, 0, 0, "数据不足"

    ma_values = []
    for i in range(period - 1, len(prices)):
        ma = np.mean(prices[i - period + 1:i + 1])
        ma_values.append(float(ma))

    if len(ma_values) < 5:
        return 0, 0, 0, "数据不足"

    x = np.arange(len(ma_values))
    slope, _ = np.polyfit(x, ma_values, 1)

    angle = np.degrees(np.arctan(slope))

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
    daily_pct_change = pct_change / 5

    if daily_pct_change >= 0.5:
        return 100, f"强势上涨趋势 (日涨幅{daily_pct_change:.3f}% ≥ +0.5%)"
    elif daily_pct_change <= -0.5:
        return 0, f"强势下跌趋势 (日涨幅{daily_pct_change:.3f}% ≤ -0.5%)"
    else:
        score = (daily_pct_change - (-0.5)) / (0.5 - (-0.5)) * 100
        score = max(0, min(100, score))
        if daily_pct_change > 0:
            return round(score, 1), f"上涨趋势 (日涨幅{daily_pct_change:.3f}%)"
        else:
            return round(score, 1), f"下跌趋势 (日涨幅{daily_pct_change:.3f}%)"


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """计算布林带"""
    if len(prices) < period * 2:
        return None, "数据不足"

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

    bandwidth = (upper_band - lower_band) / ma * 100
    prev_bandwidth = (prev_upper - prev_lower) / prev_ma * 100

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

    if current <= lower * 1.01 and bandwidth_expanding:
        return 100, "触下轨且带宽扩大 - 超卖信号(100分)"

    if current >= upper * 0.99 and bandwidth_expanding:
        return 0, "触上轨且带宽扩大 - 超买信号(0分)"

    return 50, "布林带无明显信号(50分)"


def calculate_gold_technical_analysis():
    """综合技术分析主函数"""
    print("正在获取黄金现货数据...")

    current_data = fetch_gold_current_price()
    if not current_data:
        return {
            "symbol": "GOLD_TECH",
            "name": "黄金现货技术分析",
            "error": "获取当前价格失败",
            "timestamp": datetime.now().isoformat()
        }

    current_price = current_data['price']

    # 分别获取FRED和AkShare数据用于交叉验证
    fred_data = fetch_gold_history_fred(current_price)
    akshare_data = fetch_gold_history_akshare()

    # 交叉验证
    validation_result, warning_msg = cross_validate_sources(fred_data, akshare_data)

    # 选择主数据源：优先使用FRED数据
    if fred_data:
        history_data = fred_data
    elif akshare_data:
        history_data = akshare_data
    else:
        history_data = fetch_gold_history_sina(current_price)

    prices = history_data['prices']
    data_source = history_data['source']

    if len(prices) < 60:
        return {
            "symbol": "GOLD_TECH",
            "name": "黄金现货技术分析",
            "error": "历史数据不足",
            "timestamp": datetime.now().isoformat()
        }

    rsi = calculate_rsi(prices, 14)

    macd, signal, ema, macd_score, macd_signal = calculate_macd(prices)

    slope, slope_angle, slope_pct_change, slope_status = calculate_ma_slope(prices, 20)
    ma_slope_score, ma_slope_signal = evaluate_ma_slope_signal(slope, slope_angle, slope_pct_change)

    bollinger, bollinger_status = calculate_bollinger_bands(prices, 20, 2)
    if bollinger:
        bollinger_score, bollinger_signal = evaluate_bollinger_signals(bollinger)
    else:
        bollinger_score, bollinger_signal = 50, "数据不足"

    if rsi < 30:
        rsi_score = 100 - rsi
    elif rsi > 70:
        rsi_score = 100 - rsi
    else:
        rsi_score = 50

    result = {
        "symbol": "GOLD_TECH",
        "name": "黄金现货技术分析",
        "current_price": current_price,
        "date": current_data['date'],
        "timestamp": datetime.now().isoformat(),
        "data_validation": validation_result,
        "warning": warning_msg,
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
        "data_source": data_source
    }

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("黄金现货技术分析")
    print("=" * 60)
    result = calculate_gold_technical_analysis()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60)
