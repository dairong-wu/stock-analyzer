# app.py
from flask import Flask, render_template, jsonify
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from analysis_engine import analyze_kline, analyze_fundamentals, generate_comprehensive_conclusion
from config import TICKERS
from database import get_kline, get_info, get_financials
from scheduler import start_scheduler
import pandas_ta as ta

# 將 Plotly 預設主題設為白色系
pio.templates.default = "plotly_white"

app = Flask(__name__)

@app.route('/')
def index():
    """主頁，顯示所有股票的儀表板"""
    summary_data = []
    for name, ticker in TICKERS.items():
        info = get_info(ticker)
        kline_df = get_kline(ticker)
        last_price = kline_df.iloc[-1]['Close'] if not kline_df.empty else 0
        
        # 先取得PE
        pe_value = "N/A"
        if info is not None and pd.notna(info.get('TrailingPE', None)):
            pe_value = f"{info['TrailingPE']:.2f}" if not isinstance(info, pd.DataFrame) else f"{info.iloc[0]['TrailingPE']:.2f}"
        
        # 呼叫分析函數，前提是有完整資料才做
        conclusion_class = None
        if info is not None and not kline_df.empty:
            # 如果info是DataFrame先轉Series
            if isinstance(info, pd.DataFrame) and not info.empty:
                info_series = info.iloc[0]
            else:
                info_series = info
            
            fundamental_analysis = analyze_fundamentals(info_series, pd.DataFrame(), last_price)
            conclusion = generate_comprehensive_conclusion(kline_df, fundamental_analysis)
            conclusion_class = conclusion.get("class", None)
        
        summary_data.append({
            'name': name,
            'ticker': ticker,
            'price': f"${last_price:.2f}",
            'pe': pe_value,
            'conclusion_class': conclusion_class
        })
    return render_template('index.html', summary=summary_data)

@app.route('/stock/<ticker>')
def stock_detail(ticker):
    info = get_info(ticker)
    kline_df = get_kline(ticker)
    financials_df = get_financials(ticker)
    print(f"info raw: {info}")  # 調試原始 info
    print(f"info type: {type(info)}")  # 調試 info 類型
    
    if info is not None and isinstance(info, pd.DataFrame) and not info.empty:
        info = info.iloc[0]  # 將 DataFrame 轉為 Series
        print(f"info after conversion: {info.to_dict()}")  # 調試轉換後的 info
    elif info is None:
        print(f"Info for {ticker} is None")
        return f"<h1>無法獲取 {ticker} 的基本資訊，請確認資料庫是否已更新。</h1>"
    
    print(f"financials_df head: {financials_df.head() if not financials_df.empty else 'Empty'}")
    
    if kline_df.empty:
        return f"<h1>無法獲取 {ticker} 的K線資料，請確認資料庫是否已更新。</h1>"

    company_name = info['Name'] if info is not None and 'Name' in info else ticker

    # 計算技術指標
    try:
        kline_df = kline_df.copy()
        kline_df.ta.sma(length=20, append=True)
        kline_df.ta.sma(length=60, append=True)
        kline_df.ta.macd(append=True)
        kline_df.ta.stoch(append=True)
        print(f"After indicators, columns: {kline_df.columns}")
    except Exception as e:
        print(f"Indicator error: {e}")
        return f"<h1>技術指標計算失敗: {e}</h1>"

    last_price = kline_df.iloc[-1]['Close'] if not kline_df.empty else None
    fundamental_analysis = analyze_fundamentals(info, financials_df, last_price)
    conclusion = generate_comprehensive_conclusion(kline_df, fundamental_analysis)
    kline_signals = analyze_kline(kline_df)
    print(f"kline_signals: {kline_signals}")
    print(f"fundamental_analysis: {fundamental_analysis}")  # 調試基本面分析結果

    # 產生 K 線圖 (保持不變)
    kline_df = kline_df.dropna(subset=['Open', 'High', 'Low', 'Close'])
    if kline_df.empty:
        return f"<h1>無效K線數據，請檢查數據庫。</h1>"
    
    candlestick_data = {
        "x": kline_df.index.astype(str).tolist(),
        "open": kline_df['Open'].tolist(),
        "high": kline_df['High'].tolist(),
        "low": kline_df['Low'].tolist(),
        "close": kline_df['Close'].tolist(),
        "type": "candlestick",
        "name": "K-Line"
    }
    sma20_data = {"x": kline_df.index.astype(str).tolist(), "y": kline_df['SMA_20'].tolist(), "type": "scatter", "mode": "lines", "name": "20日均線", "line": {"color": "orange", "width": 1}} if 'SMA_20' in kline_df.columns and not kline_df['SMA_20'].isna().all() else None
    sma60_data = {"x": kline_df.index.astype(str).tolist(), "y": kline_df['SMA_60'].tolist(), "type": "scatter", "mode": "lines", "name": "60日均線", "line": {"color": "purple", "width": 1}} if 'SMA_60' in kline_df.columns and not kline_df['SMA_60'].isna().all() else None
    macd_data = {"x": kline_df.index.astype(str).tolist(), "y": kline_df['MACD_12_26_9'].tolist(), "type": "scatter", "mode": "lines", "name": "MACD", "line": {"color": "blue", "width": 1}} if 'MACD_12_26_9' in kline_df.columns and not kline_df['MACD_12_26_9'].isna().all() else None
    signal_data = {"x": kline_df.index.astype(str).tolist(), "y": kline_df['MACDs_12_26_9'].tolist(), "type": "scatter", "mode": "lines", "name": "Signal", "line": {"color": "red", "width": 1}} if 'MACDs_12_26_9' in kline_df.columns and not kline_df['MACDs_12_26_9'].isna().all() else None
    kd_k_data = {"x": kline_df.index.astype(str).tolist(), "y": kline_df['STOCHk_14_3_3'].tolist(), "type": "scatter", "mode": "lines", "name": "KD %K", "line": {"color": "green", "width": 1}, "yaxis": "y2"} if 'STOCHk_14_3_3' in kline_df.columns and not kline_df['STOCHk_14_3_3'].isna().all() else None
    kd_d_data = {"x": kline_df.index.astype(str).tolist(), "y": kline_df['STOCHd_14_3_3'].tolist(), "type": "scatter", "mode": "lines", "name": "KD %D", "line": {"color": "purple", "width": 1}, "yaxis": "y2"} if 'STOCHd_14_3_3' in kline_df.columns and not kline_df['STOCHd_14_3_3'].isna().all() else None

    data = [candlestick_data]
    if sma20_data: data.append(sma20_data)
    if sma60_data: data.append(sma60_data)
    if macd_data and signal_data: data.extend([macd_data, signal_data])
    if kd_k_data and kd_d_data: data.extend([kd_k_data, kd_d_data])

    layout = {
        "title": f"{company_name} ({ticker}) K線圖與分析",
        "yaxis_title": "股價 (USD)",
        "xaxis_rangeslider_visible": True,
        "height": 800,
        "yaxis2": {
            "title": "MACD / KD",
            "overlaying": "y",
            "side": "right",
            "range": [0, 100]
        }
    }

    fig = go.Figure(data=data, layout=layout)
    graph_json = fig.to_json()

    print(f"graph_json type: {type(graph_json)}, content length: {len(graph_json)}, sample: {graph_json[:500]}...")
    
    print(f"info keys: {info.keys()}")
    print(f"TrailingPE: {info.get('TrailingPE')} (type: {type(info.get('TrailingPE'))})")
    print(f"TrailingEps: {info.get('TrailingEps')}")
    print(f"MarketCap: {info.get('MarketCap')}")

    return render_template(
        'stock_detail.html',
        company_name=company_name,
        ticker=ticker,
        graph_json=graph_json,
        kline_analysis=list(kline_signals.values()) if isinstance(kline_signals, dict) else [],
        fundamental_analysis=fundamental_analysis if isinstance(fundamental_analysis, dict) else {'Error': '數據無效'},
        conclusion=conclusion
    )

if __name__ == '__main__':
    print("=" * 50)
    print("股票分析軟體啟動中...")
    print("訪問網址: http://localhost:5000")
    print("=" * 50)
    start_scheduler()
    app.run(debug=True, port=5000)