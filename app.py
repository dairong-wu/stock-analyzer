from flask import Flask, render_template, request, jsonify, render_template_string
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from analysis_engine import analyze_kline, analyze_fundamentals, generate_comprehensive_conclusion
from database import get_kline, get_info, get_financials
import pandas_ta as ta
import os
import sys
from analysis_engine import analyze_fundamentals_with_valuation, generate_comprehensive_conclusion_with_patterns
from trend_pattern_analysis import analyze_trend_patterns
from valuation_analysis import perform_fundamental_valuation

# 取得執行檔案的目錄
if getattr(sys, 'frozen', False):
    # 如果是打包後的 exe
    application_path = os.path.dirname(sys.executable)
else:
    # 如果是開發環境
    application_path = os.path.dirname(os.path.abspath(__file__))

# 將 Plotly 預設主題設為白色系
pio.templates.default = "plotly_white"

# 設定模板路徑，嘗試多個可能的位置
template_path = None
possible_template_paths = [
    os.path.join(application_path, 'templates'),
    os.path.join(application_path, '_internal', 'templates'),
    os.path.join(os.path.dirname(application_path), 'templates'),
    'templates'
]

for path in possible_template_paths:
    if os.path.exists(path):
        template_path = path
        print(f"Found templates at: {template_path}")
        break

# 嘗試導入內嵌模板
USE_EMBEDDED_TEMPLATES = False
if template_path is None:
    try:
        from embedded_templates import INDEX_TEMPLATE, STOCK_DETAIL_TEMPLATE
        USE_EMBEDDED_TEMPLATES = True
        print("Using embedded templates")
    except ImportError:
        print("ERROR: Cannot find templates folder or embedded templates!")
        template_path = os.path.join(application_path, "templates")  # 使用預設路徑

app = Flask(__name__, template_folder=template_path if template_path else None)

# 加入錯誤處理
@app.errorhandler(500)
def internal_error(error):
    return f"""
    <h1>Internal Server Error</h1>
    <p>錯誤詳情：{str(error)}</p>
    <p>模板路徑：{template_path}</p>
    <p>模板路徑存在：{os.path.exists(template_path)}</p>
    <p>應用程式路徑：{application_path}</p>
    <p>當前工作目錄：{os.getcwd()}</p>
    """, 500

@app.route('/')
def index():
    """主頁，顯示所有股票的儀表板"""
    # 動態載入 TICKERS
    from config import TICKERS
    
    summary_data = []
    for name, ticker in TICKERS.items():
        try:
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
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            summary_data.append({
                'name': name,
                'ticker': ticker,
                'price': "N/A",
                'pe': "N/A",
                'conclusion_class': None
            })
    
    # 使用內嵌模板或檔案模板
    if USE_EMBEDDED_TEMPLATES:
        return render_template_string(INDEX_TEMPLATE, summary=summary_data)
    else:
        return render_template('index.html', summary=summary_data)

@app.route('/stock/<ticker>')
def stock_detail(ticker):
    try:
        info = get_info(ticker)
        kline_df = get_kline(ticker)
        financials_df = get_financials(ticker)
        
        if info is not None and isinstance(info, pd.DataFrame) and not info.empty:
            info = info.iloc[0]
        elif info is None:
            return f"<h1>無法獲取 {ticker} 的基本資訊，請確認資料庫是否已更新。</h1>"
        
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
        except Exception as e:
            print(f"Indicator error: {e}")
            return f"<h1>技術指標計算失敗: {e}</h1>"

        last_price = kline_df.iloc[-1]['Close'] if not kline_df.empty else None
        
        # 使用新的分析函數
        fundamental_analysis = analyze_fundamentals_with_valuation(info, financials_df, last_price)
        conclusion = generate_comprehensive_conclusion_with_patterns(kline_df, fundamental_analysis)
        kline_signals = analyze_kline(kline_df)
        
        # 新增：趨勢型態分析
        trend_patterns = conclusion.get('trend_patterns', {})
        
        # 新增：估值分析詳情
        valuation_details = fundamental_analysis.pop('_valuation_details', None)

        # 根據天數參數動態生成 K 線圖
        days = int(request.args.get('days', 60))
        if days not in [20, 60, 120]:
            days = 20
        kline_df_display = kline_df.tail(days)

        # 產生 K 線與均線圖
        kline_df_display = kline_df_display.dropna(subset=['Open', 'High', 'Low', 'Close'])
        if kline_df_display.empty:
            return f"<h1>無效K線數據，請檢查數據庫。</h1>"
        
        candlestick_data = {
            "x": kline_df_display.index.astype(str).tolist(),
            "open": kline_df_display['Open'].tolist(),
            "high": kline_df_display['High'].tolist(),
            "low": kline_df_display['Low'].tolist(),
            "close": kline_df_display['Close'].tolist(),
            "type": "candlestick",
            "name": "K-Line"
        }
        sma20_data = {"x": kline_df_display.index.astype(str).tolist(), "y": kline_df_display['SMA_20'].tolist(), "type": "scatter", "mode": "lines", "name": "20日均線", "line": {"color": "orange", "width": 1}} if 'SMA_20' in kline_df_display.columns and not kline_df_display['SMA_20'].isna().all() else None
        sma60_data = {"x": kline_df_display.index.astype(str).tolist(), "y": kline_df_display['SMA_60'].tolist(), "type": "scatter", "mode": "lines", "name": "60日均線", "line": {"color": "purple", "width": 1}} if 'SMA_60' in kline_df_display.columns and not kline_df_display['SMA_60'].isna().all() else None

        kline_data = [candlestick_data]
        if sma20_data: kline_data.append(sma20_data)
        if sma60_data: kline_data.append(sma60_data)
        kline_layout = {
            "title": f"{company_name} ({ticker}) K線圖與均線",
            "yaxis_title": "股價 (USD)",
            "xaxis_rangeslider_visible": True,
            "height": 400
        }
        kline_fig = go.Figure(data=kline_data, layout=kline_layout)
        kline_json = kline_fig.to_json()

        # 產生 MACD 與 KD 圖
        macd_data = {"x": kline_df_display.index.astype(str).tolist(), "y": kline_df_display['MACD_12_26_9'].tolist(), "type": "scatter", "mode": "lines", "name": "MACD", "line": {"color": "blue", "width": 1}, "yaxis": "y1"} if 'MACD_12_26_9' in kline_df_display.columns and not kline_df_display['MACD_12_26_9'].isna().all() else None
        signal_data = {"x": kline_df_display.index.astype(str).tolist(), "y": kline_df_display['MACDs_12_26_9'].tolist(), "type": "scatter", "mode": "lines", "name": "Signal", "line": {"color": "red", "width": 1}, "yaxis": "y1"} if 'MACDs_12_26_9' in kline_df_display.columns and not kline_df_display['MACDs_12_26_9'].isna().all() else None
        kd_k_data = {"x": kline_df_display.index.astype(str).tolist(), "y": kline_df_display['STOCHk_14_3_3'].tolist(), "type": "scatter", "mode": "lines", "name": "KD %K", "line": {"color": "green", "width": 1}, "yaxis": "y2"} if 'STOCHk_14_3_3' in kline_df_display.columns and not kline_df_display['STOCHk_14_3_3'].isna().all() else None
        kd_d_data = {"x": kline_df_display.index.astype(str).tolist(), "y": kline_df_display['STOCHd_14_3_3'].tolist(), "type": "scatter", "mode": "lines", "name": "KD %D", "line": {"color": "purple", "width": 1}, "yaxis": "y2"} if 'STOCHd_14_3_3' in kline_df_display.columns and not kline_df_display['STOCHd_14_3_3'].isna().all() else None

        macd_kd_data = []
        if macd_data and signal_data: macd_kd_data.extend([macd_data, signal_data])
        if kd_k_data and kd_d_data: macd_kd_data.extend([kd_k_data, kd_d_data])
        macd_kd_layout = {
            "title": f"{company_name} ({ticker}) MACD 與 KD",
            "yaxis": {"title": "MACD", "side": "left", "range": [-5, 5]},
            "yaxis2": {"title": "KD", "overlaying": "y", "side": "right", "range": [0, 100]},
            "xaxis": {"matches": "x"},
            "height": 300
        }
        macd_kd_fig = go.Figure(data=macd_kd_data, layout=macd_kd_layout)
        macd_kd_json = macd_kd_fig.to_json()

        # 使用內嵌模板或檔案模板
        if USE_EMBEDDED_TEMPLATES:
            return render_template_string(
                STOCK_DETAIL_TEMPLATE,
                company_name=company_name,
                ticker=ticker,
                kline_json=kline_json,
                macd_kd_json=macd_kd_json,
                kline_analysis=list(kline_signals.values()) if isinstance(kline_signals, dict) else [],
                trend_patterns=trend_patterns,  # 新增
                fundamental_analysis=fundamental_analysis if isinstance(fundamental_analysis, dict) else {'Error': '數據無效'},
                valuation_details=valuation_details,  # 新增
                conclusion=conclusion,
                selected_days=days
            )
        else:
            return render_template(
                'stock_detail.html',
                company_name=company_name,
                ticker=ticker,
                kline_json=kline_json,
                macd_kd_json=macd_kd_json,
                kline_analysis=list(kline_signals.values()) if isinstance(kline_signals, dict) else [],
                trend_patterns=trend_patterns,  # 新增
                fundamental_analysis=fundamental_analysis if isinstance(fundamental_analysis, dict) else {'Error': '數據無效'},
                valuation_details=valuation_details,  # 新增
                conclusion=conclusion,
                selected_days=days
            )
    except Exception as e:
        print(f"Error in stock_detail: {e}")
        return f"<h1>處理 {ticker} 時發生錯誤: {str(e)}</h1>"

if __name__ == "__main__":
    app.run(debug=True, port=5000)