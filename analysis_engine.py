# analysis_engine.py
import pandas as pd
import pandas_ta as ta

# analysis_engine.py (部分修改)
def analyze_kline(df):
    """分析 K 線圖，尋找簡單的模式，返回最近 5 個信號"""
    signals = {}
    if len(df) < 60:  # 確保至少 60 天數據以支持技術分析
        signals['Error'] = '數據不足，無法分析K線型態'
        return signals
    if len(df) < 2:
        return signals

    # 計算技術指標以輔助分析
    df.ta.sma(length=20, append=True)
    df.ta.sma(length=60, append=True)
    df.ta.macd(append=True)
    df.ta.stoch(append=True)

    # 遍歷數據尋找K線模式
    for i in range(1, len(df)):
        last = df.iloc[i]
        prev = df.iloc[i-1]

        # 看漲吞噬 (Bullish Engulfing)
        if (prev['Close'] < prev['Open'] and 
            last['Close'] > last['Open'] and 
            last['Close'] > prev['Open'] and 
            last['Open'] < prev['Close']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '看漲吞噬 (Bullish Engulfing)',
                'recommendation': '買進訊號'
            }

        # 看跌吞噬 (Bearish Engulfing)
        if (prev['Close'] > prev['Open'] and 
            last['Close'] < last['Open'] and 
            last['Close'] < prev['Open'] and 
            last['Open'] > prev['Close']):
            signals[df.index[i]] = {
                'type': 'K-Line',
                'signal': '看跌吞噬 (Bearish Engulfing)',
                'recommendation': '賣出訊號'
            }

        # 價格突破前高
        if i > 1 and last['Close'] > df['High'].iloc[i-2:i].max() and last['Volume'] > df['Volume'].iloc[i-1]:
            signals[df.index[i]] = {
                'type': 'Breakout',
                'signal': '價格突破前高',
                'recommendation': '買進訊號'
            }

    # 只保留最近 5 個信號
    if signals:
        sorted_signals = dict(sorted(signals.items(), key=lambda x: x[0], reverse=True))
        signals = dict(list(sorted_signals.items())[:5])

    print(f"Generated kline signals (recent 5): {signals}")
    return signals

def analyze_fundamentals(info, financials_df, last_price):
    analysis = {}
    
    if info is None or not isinstance(info, (dict, pd.Series)):
        analysis['Error'] = '無法獲取公司基本資訊'
        return analysis

    # P/E 比率分析
    pe = info.get('TrailingPE')
    if pe and pd.notna(pe) and pe > 0:
        analysis['P/E Ratio'] = f"{pe:.2f}"
        if pe > 40:
            analysis['P/E Valuation'] = '估值偏高'
        elif pe < 15:
            analysis['P/E Valuation'] = '估值可能偏低'
        else:
            analysis['P/E Valuation'] = '估值在合理範圍'
    else:
        forward_pe = info.get('forwardPE')
        if forward_pe and pd.notna(forward_pe) and forward_pe > 0:
            analysis['P/E Ratio'] = f"N/A (Trailing), Forward: {forward_pe:.2f}"
            if forward_pe > 40:
                analysis['P/E Valuation'] = '未來估值偏高'
            elif forward_pe < 15:
                analysis['P/E Valuation'] = '未來估值可能偏低'
            else:
                analysis['P/E Valuation'] = '未來估值在合理範圍'
        else:
            analysis['P/E Ratio'] = 'N/A (可能虧損)'
            analysis['P/E Valuation'] = '無法評估 (負盈餘或數據缺失)'
    
    # 每股盈餘 (EPS)
    eps = info.get('TrailingEps')
    analysis['EPS (Trailing)'] = f"${eps:.2f}" if pd.notna(eps) and eps else 'N/A'

    # 市場資本額
    market_cap = info.get('MarketCap')
    # EPS 估值評價
    if eps is not None and not pd.isna(eps):
        analysis["EPS (Trailing)"] = f"${eps:.2f}"
        if eps < 1:
            analysis["EPS Valuation"] = "盈餘極低（可能為初期高成長股或虧損）"
        elif eps < 3:
            analysis["EPS Valuation"] = "盈餘偏低"
        elif eps < 10:
            analysis["EPS Valuation"] = "盈餘穩健"
        else:
            analysis["EPS Valuation"] = "高盈餘公司"
    else:
        analysis["EPS (Trailing)"] = "N/A"
        analysis["EPS Valuation"] = "無法評估（資料缺失）"
    
    # Market Cap 評價
    if market_cap is not None and not pd.isna(market_cap):
        if market_cap >= 1e12:
            analysis["Market Cap"] = f"${market_cap / 1e9:.2f} B"
        elif market_cap >= 1e9:
            analysis["Market Cap"] = f"${market_cap / 1e9:.2f} B"
        elif market_cap >= 1e6:
            analysis["Market Cap"] = f"${market_cap / 1e6:.2f} M"
        else:
            analysis["Market Cap"] = f"${market_cap:.0f}"
    
        if market_cap < 2e9:
            analysis["Market Cap Valuation"] = "小型公司（高風險高報酬）"
        elif market_cap < 10e9:
            analysis["Market Cap Valuation"] = "中型公司（成長潛力）"
        elif market_cap < 200e9:
            analysis["Market Cap Valuation"] = "大型公司（穩健型）"
        else:
            analysis["Market Cap Valuation"] = "超大型公司（全球級龍頭）"
    else:
        analysis["Market Cap"] = "N/A"
        analysis["Market Cap Valuation"] = "無法評估（資料缺失）"

    analysis['Market Cap'] = f"${market_cap / 1e9:.2f} B" if market_cap and pd.notna(market_cap) else 'N/A'

    # ... (rest of the function remains the same)
    return analysis

def generate_comprehensive_conclusion(kline_df, fundamental_analysis):
    """產生綜合結論"""
    buy_score = 0
    sell_score = 0
    reasons = []

    # 計算技術指標
    kline_df.ta.sma(length=20, append=True)
    kline_df.ta.sma(length=60, append=True)
    kline_df.ta.macd(append=True)
    kline_df.ta.stoch(append=True)
    
    last = kline_df.iloc[-1]

    # 技術指標評分
    # 移動平均線 (MA)
    if 'SMA_20' in kline_df.columns and 'SMA_60' in kline_df.columns:
        if last['SMA_20'] > last['SMA_60']:
            buy_score += 2
            reasons.append("中期趨勢向上 (SMA20 > SMA60)")
        else:
            sell_score += 2
            reasons.append("中期趨勢向下 (SMA20 < SMA60)")
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
            reasons.append("MACD 指標看漲 (快線>慢線)")
        else:
            sell_score += 1.5
            reasons.append("MACD 指標看跌 (快線<慢線)")

    # KD (Stochastic)
    if 'STOCHk_14_3_3' in kline_df.columns:
        if last['STOCHk_14_3_3'] < 20:
            buy_score += 2
            reasons.append("KD 指標進入超賣區 (<20)")
        elif last['STOCHk_14_3_3'] > 80:
            sell_score += 2
            reasons.append("KD 指標進入超買區 (>80)")

    # K 線型態分析
    kline_signals = analyze_kline(kline_df)
    for signal in kline_signals.values():
        if "買進" in signal['recommendation']:
            buy_score += 1
            reasons.append(f"K線訊號: {signal['signal']}")
        elif "賣出" in signal['recommendation']:
            sell_score += 1
            reasons.append(f"K線訊號: {signal['signal']}")

    # 基本面評分
    if 'P/E Valuation' in fundamental_analysis:
        if fundamental_analysis['P/E Valuation'] == '估值可能偏低':
            buy_score += 1
            reasons.append("基本面：本益比估值偏低")
        elif fundamental_analysis['P/E Valuation'] == '估值偏高':
            sell_score += 1
            reasons.append("基本面：本益比估值偏高")
    if 'Growth Outlook' in fundamental_analysis:
        if fundamental_analysis['Growth Outlook'] == '高速成長':
            buy_score += 2
            reasons.append("基本面：營收高速成長")
        elif fundamental_analysis['Growth Outlook'] == '營收衰退':
            sell_score += 2
            reasons.append("基本面：營收衰退")
    if 'Profit Margin' in fundamental_analysis and float(fundamental_analysis['Profit Margin'].replace('%', '')) > 15:
        buy_score += 1
        reasons.append("基本面：利潤率高 (>15%)")
    if 'Debt to EBITDA' in fundamental_analysis and float(fundamental_analysis['Debt to EBITDA'].replace('N/A', '999')) < 3:
        buy_score += 1
        reasons.append("基本面：負債比率健康 (<3)")

    # 最終結論
    if buy_score > sell_score and buy_score >= 7:
        conclusion_text = "好的買入點"
        conclusion_class = "conclusion-buy"
    elif sell_score > buy_score and sell_score >= 4:
        conclusion_text = "好的賣出點"
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