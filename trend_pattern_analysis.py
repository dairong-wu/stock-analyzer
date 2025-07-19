import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from scipy.stats import linregress

def find_local_extrema(df, order=5):
    """
    尋找局部極值點（高點和低點）
    order: 用於判斷極值的窗口大小
    """
    highs = argrelextrema(df['High'].values, np.greater, order=order)[0]
    lows = argrelextrema(df['Low'].values, np.less, order=order)[0]
    return highs, lows

def detect_head_and_shoulders(df, min_pattern_bars=20):
    """
    偵測頭肩頂和頭肩底型態
    返回: (pattern_type, score, description)
    """
    if len(df) < min_pattern_bars:
        return None, 0, "資料長度不足以判斷頭肩型態"
    
    highs, lows = find_local_extrema(df, order=3)
    
    # 頭肩頂檢測 - 只檢查最近的型態
    if len(highs) >= 3:
        # 從最近的高點開始往前檢查
        for i in range(len(highs) - 2, -1, -1):
            if highs[i+2] < len(df) - 10:  # 確保型態不是太久以前的
                left_shoulder = df.iloc[highs[i]]['High']
                head = df.iloc[highs[i+1]]['High']
                right_shoulder = df.iloc[highs[i+2]]['High']
                
                # 頭肩頂條件：頭部最高，兩肩高度相近
                if (head > left_shoulder and head > right_shoulder and
                    abs(left_shoulder - right_shoulder) / head < 0.05):
                    # 檢查時間是否在近期
                    pattern_date = df.index[highs[i+1]]
                    days_ago = (df.index[-1] - pattern_date).days if hasattr(df.index, 'date') else len(df) - highs[i+1]
                    date_str = pattern_date.strftime('%Y-%m-%d') if hasattr(pattern_date, 'strftime') else str(pattern_date)
                    return "頭肩頂", -1, f"在 {date_str} 形成頭肩頂，預示下跌"
    
    # 頭肩底檢測
    if len(lows) >= 3:
        # 從最近的低點開始往前檢查
        for i in range(len(lows) - 2, -1, -1):
            if lows[i+2] < len(df) - 10:  # 確保型態不是太久以前的
                left_shoulder = df.iloc[lows[i]]['Low']
                head = df.iloc[lows[i+1]]['Low']
                right_shoulder = df.iloc[lows[i+2]]['Low']
                
                # 頭肩底條件：頭部最低，兩肩低度相近
                if (head < left_shoulder and head < right_shoulder and
                    abs(left_shoulder - right_shoulder) / abs(head) < 0.05):
                    pattern_date = df.index[lows[i+1]]
                    days_ago = (df.index[-1] - pattern_date).days if hasattr(df.index, 'date') else len(df) - lows[i+1]
                    date_str = pattern_date.strftime('%Y-%m-%d') if hasattr(pattern_date, 'strftime') else str(pattern_date)
                    return "頭肩底", 1, f"在 {date_str} 形成頭肩底，預示上漲"
    
    return None, 0, None

def detect_double_top_bottom(df, min_pattern_bars=15, tolerance=0.02):
    """
    偵測雙重頂和雙重底
    tolerance: 兩個峰/谷的價格容忍度
    """
    if len(df) < min_pattern_bars:
        return None, 0, "資料長度不足以判斷雙重頂底"
    
    highs, lows = find_local_extrema(df, order=3)
    
    # 雙重頂檢測 - 只檢查最近的高點
    if len(highs) >= 2:
        # 確保是最近的型態
        if highs[-1] > len(df) - 30:  # 最近30根K線內
            recent_highs = highs[-2:]
            peak1 = df.iloc[recent_highs[0]]['High']
            peak2 = df.iloc[recent_highs[1]]['High']
            
            if abs(peak1 - peak2) / max(peak1, peak2) < tolerance:
                # 檢查中間是否有明顯回檔
                valley_between = df.iloc[recent_highs[0]:recent_highs[1]]['Low'].min()
                if (peak1 - valley_between) / peak1 > 0.05:
                    date_str = df.index[recent_highs[-1]].strftime('%Y-%m-%d') if hasattr(df.index[0], 'strftime') else str(df.index[recent_highs[-1]])
                    return "雙重頂", -1, f"在 {date_str} 形成雙重頂，兩個高點在 {peak1:.2f} 附近"
    
    # 雙重底檢測
    if len(lows) >= 2:
        # 確保是最近的型態
        if lows[-1] > len(df) - 30:  # 最近30根K線內
            recent_lows = lows[-2:]
            valley1 = df.iloc[recent_lows[0]]['Low']
            valley2 = df.iloc[recent_lows[1]]['Low']
            
            if abs(valley1 - valley2) / min(valley1, valley2) < tolerance:
                # 檢查中間是否有明顯反彈
                peak_between = df.iloc[recent_lows[0]:recent_lows[1]]['High'].max()
                if (peak_between - valley1) / valley1 > 0.05:
                    date_str = df.index[recent_lows[-1]].strftime('%Y-%m-%d') if hasattr(df.index[0], 'strftime') else str(df.index[recent_lows[-1]])
                    return "雙重底", 1, f"在 {date_str} 形成雙重底，兩個低點在 {valley1:.2f} 附近"
    
    return None, 0, None

def detect_triangle_patterns(df, min_pattern_bars=20):
    """
    偵測三角形型態（上升三角形、下降三角形）
    """
    if len(df) < min_pattern_bars:
        return None, 0, "資料長度不足以判斷三角形型態"
    
    recent_df = df.tail(min_pattern_bars)
    highs, lows = find_local_extrema(recent_df, order=2)
    
    if len(highs) < 2 or len(lows) < 2:
        return None, 0, None
    
    # 計算高點和低點的趨勢線斜率
    high_points = recent_df.iloc[highs]['High'].values
    low_points = recent_df.iloc[lows]['Low'].values
    
    # 使用線性回歸計算斜率
    if len(highs) >= 2:
        high_slope = linregress(range(len(high_points)), high_points).slope
    else:
        high_slope = 0
        
    if len(lows) >= 2:
        low_slope = linregress(range(len(low_points)), low_points).slope
    else:
        low_slope = 0
    
    # 上升三角形：低點上升，高點水平
    if low_slope > 0 and abs(high_slope) < 0.001:
        date_str = recent_df.index[-1].strftime('%Y-%m-%d') if hasattr(recent_df.index[-1], 'strftime') else str(recent_df.index[-1])
        return "上升三角形", 1, f"在 {date_str} 形成上升三角形，支撐線上升，壓力線水平"
    
    # 下降三角形：高點下降，低點水平
    if high_slope < 0 and abs(low_slope) < 0.001:
        date_str = recent_df.index[-1].strftime('%Y-%m-%d') if hasattr(recent_df.index[-1], 'strftime') else str(recent_df.index[-1])
        return "下降三角形", -1, f"在 {date_str} 形成下降三角形，壓力線下降，支撐線水平"
    
    return None, 0, None

def detect_flag_patterns(df, min_pattern_bars=10):
    """
    偵測旗型（Flag）型態
    """
    if len(df) < min_pattern_bars + 10:
        return None, 0, "資料長度不足以判斷旗型"
    
    # 取最近的資料
    recent_df = df.tail(min_pattern_bars + 10)
    
    # 分析前期趨勢（旗桿）
    pole_df = recent_df.iloc[:-min_pattern_bars]
    flag_df = recent_df.iloc[-min_pattern_bars:]
    
    pole_return = (pole_df.iloc[-1]['Close'] - pole_df.iloc[0]['Close']) / pole_df.iloc[0]['Close']
    
    # 計算旗型部分的斜率
    flag_slope = linregress(range(len(flag_df)), flag_df['Close'].values).slope
    flag_volatility = flag_df['Close'].std() / flag_df['Close'].mean()
    
    # 多頭旗型：前期大漲後小幅回檔
    if pole_return > 0.1 and flag_slope < 0 and flag_volatility < 0.05:
        date_str = flag_df.index[-1].strftime('%Y-%m-%d') if hasattr(flag_df.index[-1], 'strftime') else str(flag_df.index[-1])
        return "多頭旗型", 1, f"在 {date_str} 上升趨勢中的旗型整理，預期續漲"
    
    # 空頭旗型：前期大跌後小幅反彈
    if pole_return < -0.1 and flag_slope > 0 and flag_volatility < 0.05:
        date_str = flag_df.index[-1].strftime('%Y-%m-%d') if hasattr(flag_df.index[-1], 'strftime') else str(flag_df.index[-1])
        return "空頭旗型", -1, f"在 {date_str} 下降趨勢中的旗型整理，預期續跌"
    
    return None, 0, None

def detect_wedge_patterns(df, min_pattern_bars=20):
    """
    偵測楔形型態
    """
    if len(df) < min_pattern_bars:
        return None, 0, "資料長度不足以判斷楔形"
    
    recent_df = df.tail(min_pattern_bars)
    highs, lows = find_local_extrema(recent_df, order=3)
    
    if len(highs) < 2 or len(lows) < 2:
        return None, 0, None
    
    # 計算趨勢線
    high_slope = linregress(highs, recent_df.iloc[highs]['High'].values).slope
    low_slope = linregress(lows, recent_df.iloc[lows]['Low'].values).slope
    
    # 上升楔形：兩條線都上升，但逐漸收斂
    if high_slope > 0 and low_slope > 0 and low_slope > high_slope:
        date_str = recent_df.index[-1].strftime('%Y-%m-%d') if hasattr(recent_df.index[-1], 'strftime') else str(recent_df.index[-1])
        return "上升楔形", -1, f"在 {date_str} 形成上升楔形，雖然上升但動能減弱，可能反轉"
    
    # 下降楔形：兩條線都下降，但逐漸收斂
    if high_slope < 0 and low_slope < 0 and high_slope > low_slope:
        date_str = recent_df.index[-1].strftime('%Y-%m-%d') if hasattr(recent_df.index[-1], 'strftime') else str(recent_df.index[-1])
        return "下降楔形", 1, f"在 {date_str} 形成下降楔形，賣壓減弱，可能反轉向上"
    
    return None, 0, None

def detect_rounded_patterns(df, min_pattern_bars=30):
    """
    偵測圓弧頂和圓弧底
    """
    if len(df) < min_pattern_bars:
        return None, 0, "資料長度不足以判斷圓弧型態"
    
    recent_df = df.tail(min_pattern_bars)
    prices = recent_df['Close'].values
    
    # 計算價格的二階導數來判斷曲率
    first_diff = np.diff(prices)
    second_diff = np.diff(first_diff)
    
    # 平滑處理
    smooth_second_diff = pd.Series(second_diff).rolling(5).mean().values
    
    # 圓弧頂：先凸後凹
    if np.nanmean(smooth_second_diff[:len(smooth_second_diff)//2]) < -0.01 and \
       np.nanmean(smooth_second_diff[len(smooth_second_diff)//2:]) > 0.01:
        date_str = recent_df.index[-1].strftime('%Y-%m-%d') if hasattr(recent_df.index[-1], 'strftime') else str(recent_df.index[-1])
        return "圓弧頂", -1, f"在 {date_str} 形成圓弧頂，買盤逐漸衰竭"
    
    # 圓弧底：先凹後凸
    if np.nanmean(smooth_second_diff[:len(smooth_second_diff)//2]) > 0.01 and \
       np.nanmean(smooth_second_diff[len(smooth_second_diff)//2:]) < -0.01:
        date_str = recent_df.index[-1].strftime('%Y-%m-%d') if hasattr(recent_df.index[-1], 'strftime') else str(recent_df.index[-1])
        return "圓弧底", 1, f"在 {date_str} 形成圓弧底，賣壓逐漸消化"
    
    return None, 0, None

def analyze_trend_patterns(df, lookback_days=200):
    """
    主函數：分析所有趨勢型態
    參數:
    - df: K線數據
    - lookback_days: 分析最近多少天的數據（預設200天）
    返回: {pattern_name: (score, description), ...}
    """
    patterns = {}
    
    # 只使用最近的數據進行分析
    if len(df) > lookback_days:
        df = df.tail(lookback_days)
    
    if len(df) < 20:
        return {"錯誤": (0, "資料長度不足（需要至少20根K線）")}
    
    # 檢測各種型態
    pattern_functions = [
        detect_head_and_shoulders,
        detect_double_top_bottom,
        detect_triangle_patterns,
        detect_flag_patterns,
        detect_wedge_patterns,
        detect_rounded_patterns
    ]
    
    for func in pattern_functions:
        try:
            pattern_name, score, description = func(df)
            if pattern_name and description:
                patterns[pattern_name] = (score, description)
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
            continue
    
    # 檢測 MACD 和 KD 交叉
    if 'MACD_12_26_9' in df.columns and 'MACDs_12_26_9' in df.columns:
        macd_cross = detect_macd_cross(df)
        if macd_cross[0]:
            patterns[macd_cross[0]] = (macd_cross[1], macd_cross[2])
    
    if 'STOCHk_14_3_3' in df.columns and 'STOCHd_14_3_3' in df.columns:
        kd_cross = detect_kd_cross(df)
        if kd_cross[0]:
            patterns[kd_cross[0]] = (kd_cross[1], kd_cross[2])
    
    # 檢測均線排列
    if 'SMA_20' in df.columns and 'SMA_60' in df.columns:
        ma_arrangement = detect_ma_arrangement(df)
        if ma_arrangement[0]:
            patterns[ma_arrangement[0]] = (ma_arrangement[1], ma_arrangement[2])
    
    return patterns if patterns else {"無型態": (0, "目前未偵測到明確的趨勢型態")}

def detect_macd_cross(df):
    """偵測 MACD 金叉和死叉"""
    if len(df) < 2:
        return None, 0, None
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 金叉：MACD 從下往上穿越信號線
    if (prev['MACD_12_26_9'] <= prev['MACDs_12_26_9'] and 
        last['MACD_12_26_9'] > last['MACDs_12_26_9']):
        return "MACD金叉", 1, "MACD向上穿越信號線，動能轉強"
    
    # 死叉：MACD 從上往下穿越信號線
    if (prev['MACD_12_26_9'] >= prev['MACDs_12_26_9'] and 
        last['MACD_12_26_9'] < last['MACDs_12_26_9']):
        return "MACD死叉", -1, "MACD向下穿越信號線，動能轉弱"
    
    return None, 0, None

def detect_kd_cross(df):
    """偵測 KD 黃金交叉和死亡交叉"""
    if len(df) < 2:
        return None, 0, None
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 黃金交叉：K值從下往上穿越D值，且在低檔區
    if (prev['STOCHk_14_3_3'] <= prev['STOCHd_14_3_3'] and 
        last['STOCHk_14_3_3'] > last['STOCHd_14_3_3'] and
        last['STOCHk_14_3_3'] < 50):
        return "KD黃金交叉", 1, "K值向上穿越D值於低檔區，買進訊號"
    
    # 死亡交叉：K值從上往下穿越D值，且在高檔區
    if (prev['STOCHk_14_3_3'] >= prev['STOCHd_14_3_3'] and 
        last['STOCHk_14_3_3'] < last['STOCHd_14_3_3'] and
        last['STOCHk_14_3_3'] > 50):
        return "KD死亡交叉", -1, "K值向下穿越D值於高檔區，賣出訊號"
    
    return None, 0, None

def detect_ma_arrangement(df):
    """偵測均線多頭或空頭排列"""
    if len(df) < 1:
        return None, 0, None
    
    last = df.iloc[-1]
    
    # 檢查是否有有效的均線值
    if pd.isna(last['SMA_20']) or pd.isna(last['SMA_60']):
        return None, 0, None
    
    # 多頭排列：價格 > 20MA > 60MA
    if last['Close'] > last['SMA_20'] > last['SMA_60']:
        return "均線多頭排列", 1, "價格 > 20MA > 60MA，趨勢向上"
    
    # 空頭排列：價格 < 20MA < 60MA
    if last['Close'] < last['SMA_20'] < last['SMA_60']:
        return "均線空頭排列", -1, "價格 < 20MA < 60MA，趨勢向下"
    
    return None, 0, None