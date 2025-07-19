import pandas as pd
import pandas_ta as ta
from trend_pattern_analysis import analyze_trend_patterns
from valuation_analysis import perform_fundamental_valuation

def analyze_kline(df, lookback_bars=15):
    """
    Analyze K-line patterns and return recent signals with scores
    
    參數:
    - df: 完整的K線數據
    - lookback_bars: 只分析最近幾根K線（預設15根）
    """
    signals = {}
    if len(df) < 60:  # Ensure enough data for analysis
        signals['Error'] = '資料不足，無法進行 K 線型態分析'
        return signals
    if len(df) < 2:
        return signals

    # Calculate technical indicators
    df = df.copy()
    df.ta.sma(length=20, append=True)
    df.ta.sma(length=60, append=True)
    df.ta.macd(append=True)
    df.ta.stoch(append=True)

    # 只分析最近的 K 線
    start_index = max(3, len(df) - lookback_bars)
    
    # 輔助函數：格式化日期
    def format_date(date_index):
        if hasattr(date_index, 'strftime'):
            return date_index.strftime('%Y-%m-%d')
        else:
            return str(date_index)
    
    # Analyze candlestick patterns
    for i in range(start_index, len(df)):  # 只分析最近的K線
        last = df.iloc[i]
        prev = df.iloc[i-1]
        prev2 = df.iloc[i-2]
        prev3 = df.iloc[i-3]

        # Bullish Patterns (+1 score)
        # 1. Bullish Engulfing
        if (prev['Close'] < prev['Open'] and 
            last['Close'] > last['Open'] and 
            last['Close'] > prev['Open'] and 
            last['Open'] < prev['Close']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '看漲吞噬',
                'recommendation': '買進訊號',
                'score': 1,
                'date': format_date(df.index[i])
            }

        # 2. Piercing Line
        if (prev['Close'] < prev['Open'] and 
            last['Close'] > last['Open'] and 
            last['Open'] < prev['Close'] and 
            last['Close'] > (prev['Open'] + prev['Close']) / 2 and 
            last['Close'] < prev['Open']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '刺透線',
                'recommendation': '買進訊號',
                'score': 1,
                'date': format_date(df.index[i])
            }

        # 3. Morning Star (3-candle pattern)
        if (prev2['Close'] < prev2['Open'] and 
            abs(prev['Close'] - prev['Open']) < abs(prev2['Close'] - prev2['Open']) * 0.5 and 
            last['Close'] > last['Open'] and 
            last['Close'] > prev2['Open']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '早晨之星',
                'recommendation': '買進訊號',
                'score': 1,
                'date': format_date(df.index[i])
            }

        # 4. Three White Soldiers (3-candle pattern)
        if (prev2['Close'] > prev2['Open'] and 
            prev['Close'] > prev['Open'] and 
            last['Close'] > last['Open'] and 
            prev2['Close'] > prev2['Open'] * 1.01 and 
            prev['Close'] > prev['Open'] * 1.01 and 
            last['Close'] > last['Open'] * 1.01):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '紅三兵',
                'recommendation': '買進訊號',
                'score': 1,
                'date': format_date(df.index[i])
            }

        # 5. Rising Three Methods (simplified, 5-candle pattern)
        if i >= 5 and i >= start_index + 2 and \
           df.iloc[i-4]['Close'] > df.iloc[i-4]['Open'] and \
           df.iloc[i-3]['Close'] < df.iloc[i-3]['Open'] and \
           df.iloc[i-2]['Close'] < df.iloc[i-2]['Open'] and \
           df.iloc[i-1]['Close'] < df.iloc[i-1]['Open'] and \
           last['Close'] > last['Open'] and last['Close'] > df.iloc[i-4]['Close']:
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '上升三法',
                'recommendation': '買進訊號',
                'score': 1,
                'date': format_date(df.index[i])
            }

        # 6. Three Inside Up
        if (prev2['Close'] < prev2['Open'] and 
            prev['Close'] > prev['Open'] and 
            prev['Open'] > prev2['Close'] and 
            prev['Close'] < prev2['Open'] and 
            last['Close'] > last['Open'] and 
            last['Close'] > prev2['Open']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '三內升勢',
                'recommendation': '買進訊號',
                'score': 1,
                'date': format_date(df.index[i])
            }

        # 7. Bullish Harami
        if (prev['Close'] < prev['Open'] and 
            last['Close'] > last['Open'] and 
            last['Open'] > prev['Close'] and 
            last['Close'] < prev['Open']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '夾陽線',
                'recommendation': '買進訊號',
                'score': 1,
                'date': format_date(df.index[i])
            }

        # 8. Three White Gaps
        if i >= 3 and prev2['Close'] > prev2['Open'] and \
           prev['Close'] > prev['Open'] and prev['Open'] > prev2['Close'] and \
           last['Close'] > last['Open'] and last['Open'] > prev['Close']:
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '三空白',
                'recommendation': '買進訊號',
                'score': 1,
                'date': format_date(df.index[i])
            }

        # Bearish Patterns (-1 score)
        # 1. Bearish Engulfing
        if (prev['Close'] > prev['Open'] and 
            last['Close'] < last['Open'] and 
            last['Close'] < prev['Open'] and 
            last['Open'] > prev['Close']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '看跌吞噬',
                'recommendation': '賣出訊號',
                'score': -1,
                'date': format_date(df.index[i])
            }

        # 2. Dark Cloud Cover
        if (prev['Close'] > prev['Open'] and 
            last['Close'] < last['Open'] and 
            last['Open'] > prev['Close'] and 
            last['Close'] < (prev['Open'] + prev['Close']) / 2 and 
            last['Close'] > prev['Open']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '烏雲蓋頂',
                'recommendation': '賣出訊號',
                'score': -1,
                'date': format_date(df.index[i])
            }

        # 3. Evening Star (3-candle pattern)
        if (prev2['Close'] > prev2['Open'] and 
            abs(prev['Close'] - prev['Open']) < abs(prev2['Close'] - prev2['Open']) * 0.5 and 
            last['Close'] < last['Open'] and 
            last['Close'] < prev2['Open']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '黃昏之星',
                'recommendation': '賣出訊號',
                'score': -1,
                'date': format_date(df.index[i])
            }

        # 4. Three Black Crows (3-candle pattern)
        if (prev2['Close'] < prev2['Open'] and 
            prev['Close'] < prev['Open'] and 
            last['Close'] < last['Open'] and 
            prev2['Close'] < prev2['Open'] * 0.99 and 
            prev['Close'] < prev['Open'] * 0.99 and 
            last['Close'] < last['Open'] * 0.99):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '黑三鴉',
                'recommendation': '賣出訊號',
                'score': -1,
                'date': format_date(df.index[i])
            }

        # 5. Falling Three Methods (simplified, 5-candle pattern)
        if i >= 5 and i >= start_index + 2 and \
           df.iloc[i-4]['Close'] < df.iloc[i-4]['Open'] and \
           df.iloc[i-3]['Close'] > df.iloc[i-3]['Open'] and \
           df.iloc[i-2]['Close'] > df.iloc[i-2]['Open'] and \
           df.iloc[i-1]['Close'] > df.iloc[i-1]['Open'] and \
           last['Close'] < last['Open'] and last['Close'] < df.iloc[i-4]['Close']:
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '下降三法',
                'recommendation': '賣出訊號',
                'score': -1,
                'date': format_date(df.index[i])
            }

        # 6. Three Inside Down
        if (prev2['Close'] > prev2['Open'] and 
            prev['Close'] < prev['Open'] and 
            prev['Open'] < prev2['Close'] and 
            prev['Close'] > prev2['Open'] and 
            last['Close'] < last['Open'] and 
            last['Close'] < prev2['Open']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '三內下降勢',
                'recommendation': '賣出訊號',
                'score': -1,
                'date': format_date(df.index[i])
            }

        # 7. Bearish Harami
        if (prev['Close'] > prev['Open'] and 
            last['Close'] < last['Open'] and 
            last['Open'] < prev['Close'] and 
            last['Close'] > prev['Open']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '夾陰線',
                'recommendation': '賣出訊號',
                'score': -1,
                'date': format_date(df.index[i])
            }

        # 8. Three Black Gaps
        if i >= 3 and prev2['Close'] < prev2['Open'] and \
           prev['Close'] < prev['Open'] and prev['Open'] < prev2['Close'] and \
           last['Close'] < last['Open'] and last['Open'] < prev['Close']:
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '三空黑',
                'recommendation': '賣出訊號',
                'score': -1,
                'date': format_date(df.index[i])
            }

        # Price Breakout
        if i > 1 and last['Close'] > df['High'].iloc[i-2:i].max() and last['Volume'] > df['Volume'].iloc[i-1]:
            signals[df.index[i]] = {
                'type': 'Breakout',
                'signal': '價格突破前高',
                'recommendation': '買進訊號',
                'score': 1,
                'date': format_date(df.index[i])
            }

    # Keep only the most recent 5 signals
    if signals:
        sorted_signals = dict(sorted(signals.items(), key=lambda x: x[0], reverse=True))
        signals = dict(list(sorted_signals.items())[:5])

    print(f"Generated kline signals (recent 5 from last {lookback_bars} bars): {signals}")
    return signals

def analyze_fundamentals(info, financials_df, last_price):
    analysis = {}
    
    if info is None or not isinstance(info, (dict, pd.Series)):
        analysis['Error'] = '無法獲取公司基本面資訊'
        return analysis

    # P/E Ratio Analysis
    pe = info.get('TrailingPE')
    if pe and pd.notna(pe) and pe > 0:
        analysis['本益比'] = f"{pe:.2f}"
        if pe > 40:
            analysis['本益比評估'] = '估值偏高'
        elif pe < 15:
            analysis['本益比評估'] = '估值可能偏低'
        else:
            analysis['本益比評估'] = '估值合理'
    else:
        forward_pe = info.get('ForwardPE')
        if forward_pe and pd.notna(forward_pe) and forward_pe > 0:
            analysis['本益比'] = f"本益比無資料，遠期本益比: {forward_pe:.2f}"
            if forward_pe > 40:
                analysis['本益比評估'] = '遠期估值偏高'
            elif forward_pe < 15:
                analysis['本益比評估'] = '遠期估值可能偏低'
            else:
                analysis['本益比評估'] = '遠期估值合理'
        else:
            analysis['本益比'] = '無資料（可能虧損）'
            analysis['本益比評估'] = '無法評估（負盈餘或資料缺失）'
    
    # EPS Analysis
    eps = info.get('TrailingEps')
    if eps is not None and not pd.isna(eps):
        analysis["每股盈餘 (過去12個月)"] = f"${eps:.2f}"
        if eps < 1:
            analysis["每股盈餘評估"] = "盈餘極低（可能為初期高成長股或虧損）"
        elif eps < 3:
            analysis["每股盈餘評估"] = "盈餘偏低"
        elif eps < 10:
            analysis["每股盈餘評估"] = "盈餘穩健"
        else:
            analysis["每股盈餘評估"] = "高盈餘公司"
    else:
        analysis["每股盈餘 (過去12個月)"] = "無資料"
        analysis["每股盈餘評估"] = "無法評估（資料缺失）"
    
    # Market Cap Analysis
    market_cap = info.get('MarketCap')
    if market_cap is not None and not pd.isna(market_cap):
        if market_cap >= 1e12:
            analysis["市值"] = f"${market_cap / 1e8:.2f} 億"
        elif market_cap >= 1e9:
            analysis["市值"] = f"${market_cap / 1e8:.2f} 億"
        elif market_cap >= 1e6:
            analysis["市值"] = f"${market_cap / 1e6:.2f} 百萬"
        else:
            analysis["市值"] = f"${market_cap:.0f}"
        
        if market_cap < 2e9:
            analysis["市值評估"] = "小型公司（高風險高報酬）"
        elif market_cap < 10e9:
            analysis["市值評估"] = "中型公司（成長潛力）"
        elif market_cap < 200e9:
            analysis["市值評估"] = "大型公司（穩健型）"
        else:
            analysis["市值評估"] = "超大型公司（全球級龍頭）"
    else:
        analysis["市值"] = "無資料"
        analysis["市值評估"] = "無法評估（資料缺失）"

    return analysis

def analyze_fundamentals_with_valuation(info, financials_df, last_price):
    """
    分析基本面並加入估值分析
    這個函數會取代原本的 analyze_fundamentals
    """
    # 先執行原本的基本面分析
    analysis = analyze_fundamentals(info, financials_df, last_price)
    
    # 加入估值分析
    valuation_results = perform_fundamental_valuation(info, financials_df, last_price)
    
    # 將估值結果整合到分析中
    analysis['估值分析'] = '請查看詳細估值報告'
    
    # 將估值結果存入單獨的 key，方便在網頁中顯示
    analysis['_valuation_details'] = valuation_results
    
    return analysis

def generate_comprehensive_conclusion_with_patterns(kline_df, fundamental_analysis):
    """
    生成包含趨勢型態分析的綜合結論
    這個函數會取代原本的 generate_comprehensive_conclusion
    """
    buy_score = 0
    sell_score = 0
    reasons = []

    # 計算技術指標
    kline_df = kline_df.copy()
    kline_df.ta.sma(length=20, append=True)
    kline_df.ta.sma(length=60, append=True)
    kline_df.ta.macd(append=True)
    kline_df.ta.stoch(append=True)
    
    last = kline_df.iloc[-1]

    # 原本的技術指標評分邏輯
    # Moving Averages (MA)
    if 'SMA_20' in kline_df.columns and 'SMA_60' in kline_df.columns:
        if last['SMA_20'] > last['SMA_60']:
            buy_score += 2
            reasons.append("中期趨勢向上 (20日均線 > 60日均線)")
        else:
            sell_score += 2
            reasons.append("中期趨勢向下 (20日均線 < 60日均線)")
        if last['Close'] > last['SMA_20']:
            buy_score += 1
            reasons.append("股價位於短期均線之上")
        else:
            sell_score += 1
            reasons.append("股價位於短期均線之下")

    # MACD
    if 'MACD_12_26_9' in kline_df.columns and 'MACDs_12_26_9' in kline_df.columns:
        if last['MACD_12_26_9'] > last['MACDs_12_26_9']:
            buy_score += 1.5
            reasons.append("MACD 指標看漲 (快線 > 慢線)")
        else:
            sell_score += 1.5
            reasons.append("MACD 指標看跌 (快線 < 慢線)")

    # KD (Stochastic)
    if 'STOCHk_14_3_3' in kline_df.columns:
        if last['STOCHk_14_3_3'] < 20:
            buy_score += 2
            reasons.append("KD 指標進入超賣區 (<20)")
        elif last['STOCHk_14_3_3'] > 80:
            sell_score += 2
            reasons.append("KD 指標進入超買區 (>80)")

    # K-line Pattern Scoring (原本的)
    kline_signals = analyze_kline(kline_df)
    for signal in kline_signals.values():
        if 'score' in signal:
            if signal['score'] > 0:
                buy_score += signal['score']
                reasons.append(f"K 線訊號: {signal['signal']}")
            elif signal['score'] < 0:
                sell_score += abs(signal['score'])
                reasons.append(f"K 線訊號: {signal['signal']}")

    # 新增：趨勢型態分析評分
    trend_patterns = analyze_trend_patterns(kline_df, lookback_days=200)
    for pattern_name, (score, description) in trend_patterns.items():
        if score > 0:
            buy_score += abs(score)
            reasons.append(f"趨勢型態: {pattern_name} - {description}")
        elif score < 0:
            sell_score += abs(score)
            reasons.append(f"趨勢型態: {pattern_name} - {description}")

    # Fundamental Scoring (原本的)
    if '本益比評估' in fundamental_analysis:
        if fundamental_analysis['本益比評估'] == '估值可能偏低':
            buy_score += 1
            reasons.append("基本面：本益比估值偏低")
        elif fundamental_analysis['本益比評估'] == '估值偏高':
            sell_score += 1
            reasons.append("基本面：本益比估值偏高")
    
    # 新增：從估值分析中提取評分
    if '_valuation_details' in fundamental_analysis:
        valuation = fundamental_analysis['_valuation_details']
        valuation_conclusions = []
        
        for method, result in valuation.get('估值方法', {}).items():
            if result.get('評估結論') == '低估':
                buy_score += 1.5
                valuation_conclusions.append(f"{method}顯示低估")
            elif result.get('評估結論') == '高估':
                sell_score += 1.5
                valuation_conclusions.append(f"{method}顯示高估")
        
        if valuation_conclusions:
            reasons.extend(valuation_conclusions)

    # 原本的其他基本面評分邏輯保持不變
    if 'Growth Outlook' in fundamental_analysis:
        if fundamental_analysis['Growth Outlook'] == 'High Growth':
            buy_score += 2
            reasons.append("基本面：營收高速成長")
        elif fundamental_analysis['Growth Outlook'] == 'Revenue Decline':
            sell_score += 2
            reasons.append("基本面：營收衰退")
    if 'Profit Margin' in fundamental_analysis and float(fundamental_analysis.get('Profit Margin', '0%').replace('%', '')) > 15:
        buy_score += 1
        reasons.append("基本面：利潤率高 (>15%)")
    if 'Debt to EBITDA' in fundamental_analysis and float(fundamental_analysis.get('Debt to EBITDA', '999').replace('N/A', '999')) < 3:
        buy_score += 1
        reasons.append("基本面：負債比率健康 (<3)")

    # Final Conclusion (調整分數門檻)
    if buy_score > sell_score and buy_score >= 8:  # 提高門檻
        conclusion_text = "良好買入機會"
        conclusion_class = "conclusion-buy"
    elif sell_score > buy_score and sell_score >= 5:  # 提高門檻
        conclusion_text = "良好賣出機會"
        conclusion_class = "conclusion-sell"
    else:
        conclusion_text = "暫時觀望"
        conclusion_class = "conclusion-hold"

    return {
        "text": conclusion_text,
        "buy_score": round(buy_score, 1),
        "sell_score": round(sell_score, 1),
        "reasons": reasons,
        "class": conclusion_class,
        "trend_patterns": trend_patterns  # 新增：提供詳細的趨勢型態
    }

def generate_comprehensive_conclusion(kline_df, fundamental_analysis):
    """Generate comprehensive conclusion with K-line pattern scores"""
    buy_score = 0
    sell_score = 0
    reasons = []

    # Calculate technical indicators
    kline_df = kline_df.copy()
    kline_df.ta.sma(length=20, append=True)
    kline_df.ta.sma(length=60, append=True)
    kline_df.ta.macd(append=True)
    kline_df.ta.stoch(append=True)
    
    last = kline_df.iloc[-1]

    # Technical Indicator Scoring
    # Moving Averages (MA)
    if 'SMA_20' in kline_df.columns and 'SMA_60' in kline_df.columns:
        if last['SMA_20'] > last['SMA_60']:
            buy_score += 2
            reasons.append("中期趨勢向上 (20日均線 > 60日均線)")
        else:
            sell_score += 2
            reasons.append("中期趨勢向下 (20日均線 < 60日均線)")
        if last['Close'] > last['SMA_20']:
            buy_score += 1
            reasons.append("股價位於短期均線之上")
        else:
            sell_score += 1
            reasons.append("股價位於短期均線之下")

    # MACD
    if 'MACD_12_26_9' in kline_df.columns and 'MACDs_12_26_9' in kline_df.columns:
        if last['MACD_12_26_9'] > last['MACDs_12_26_9']:
            buy_score += 1.5
            reasons.append("MACD 指標看漲 (快線 > 慢線)")
        else:
            sell_score += 1.5
            reasons.append("MACD 指標看跌 (快線 < 慢線)")

    # KD (Stochastic)
    if 'STOCHk_14_3_3' in kline_df.columns:
        if last['STOCHk_14_3_3'] < 20:
            buy_score += 2
            reasons.append("KD 指標進入超賣區 (<20)")
        elif last['STOCHk_14_3_3'] > 80:
            sell_score += 2
            reasons.append("KD 指標進入超買區 (>80)")

    # K-line Pattern Scoring
    kline_signals = analyze_kline(kline_df)
    for signal in kline_signals.values():
        if 'score' in signal:
            if signal['score'] > 0:
                buy_score += signal['score']
                reasons.append(f"K 線訊號: {signal['signal']}")
            elif signal['score'] < 0:
                sell_score += abs(signal['score'])
                reasons.append(f"K 線訊號: {signal['signal']}")

    # Fundamental Scoring
    if '本益比評估' in fundamental_analysis:
        if fundamental_analysis['本益比評估'] == '估值可能偏低':
            buy_score += 1
            reasons.append("基本面：本益比估值偏低")
        elif fundamental_analysis['本益比評估'] == '估值偏高':
            sell_score += 1
            reasons.append("基本面：本益比估值偏高")
    if 'Growth Outlook' in fundamental_analysis:
        if fundamental_analysis['Growth Outlook'] == 'High Growth':
            buy_score += 2
            reasons.append("基本面：營收高速成長")
        elif fundamental_analysis['Growth Outlook'] == 'Revenue Decline':
            sell_score += 2
            reasons.append("基本面：營收衰退")
    if 'Profit Margin' in fundamental_analysis and float(fundamental_analysis['Profit Margin'].replace('%', '')) > 15:
        buy_score += 1
        reasons.append("基本面：利潤率高 (>15%)")
    if 'Debt to EBITDA' in fundamental_analysis and float(fundamental_analysis['Debt to EBITDA'].replace('N/A', '999')) < 3:
        buy_score += 1
        reasons.append("基本面：負債比率健康 (<3)")

    # Final Conclusion
    if buy_score > sell_score and buy_score >= 7:
        conclusion_text = "良好買入機會"
        conclusion_class = "conclusion-buy"
    elif sell_score > buy_score and sell_score >= 4:
        conclusion_text = "良好賣出機會"
        conclusion_class = "conclusion-sell"
    else:
        conclusion_text = "暫時觀望"
        conclusion_class = "conclusion-hold"

    return {
        "text": conclusion_text,
        "buy_score": round(buy_score, 1),
        "sell_score": round(sell_score, 1),
        "reasons": reasons,
        "class": conclusion_class
    }