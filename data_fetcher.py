# data_fetcher.py
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime
import logging
from database import init_db, save_data
from config import TICKERS

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='data_fetcher.log'
)
logger = logging.getLogger(__name__)

def fetch_and_store_all_data():
    """抓取所有公司的資料並儲存到資料庫"""
    logger.info("Starting data fetch process for all tickers...")
    conn = sqlite3.connect('stock_data.db')
    
    for name, ticker in TICKERS.items():
        logger.info(f"Fetching data for {name} ({ticker})...")
        
        try:
            stock = yf.Ticker(ticker)
            
            # 1. 獲取日 K 線資料 (近5年)
            kline_df = stock.history(period="5y", auto_adjust=True, timeout=60)
            if kline_df.empty:
                logger.warning(f"No K-line data available for {ticker}")
                continue
            
            kline_df.reset_index(inplace=True)
            kline_df = kline_df.rename(columns={
                'Date': 'Date',
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })
            kline_df['Ticker'] = ticker
            kline_df['Date'] = kline_df['Date'].dt.strftime('%Y-%m-%d')
            kline_df = kline_df[['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            kline_df = kline_df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
            
            if kline_df.empty:
                logger.warning(f"Cleaned K-line data for {ticker} is empty after dropping NaN")
                continue
            
            kline_df.to_sql('kline_daily', conn, if_exists='append', index=False, 
                           dtype={'Ticker': 'TEXT', 'Date': 'TEXT', 'Open': 'REAL', 
                                  'High': 'REAL', 'Low': 'REAL', 'Close': 'REAL', 
                                  'Volume': 'INTEGER'})
            logger.info(f"Successfully stored K-line data for {ticker} with {len(kline_df)} rows")

            # 2. 獲取公司基本資訊 with retry
            info = stock.info
            logger.debug(f"Raw info for {ticker} from yfinance: {info}")
            if not info or 'longName' not in info:
                logger.warning(f"No valid info data for {ticker}, retrying...")
                stock = yf.Ticker(ticker)
                info = stock.info
                if not info or 'longName' not in info:
                    logger.error(f"Failed to fetch valid info data for {ticker} after retry")
                    continue
            
            info_df = pd.DataFrame([{
                'Ticker': ticker,
                'Name': info.get('longName', 'N/A'),
                'Industry': info.get('industry', 'N/A'),
                'MarketCap': info.get('marketCap', None),
                'TrailingPE': info.get('trailingPE', info.get('forwardPE', None)),  # 使用 forwardPE 作為備用
                'ForwardPE': info.get('forwardPE', None),
                'TrailingEps': info.get('trailingEps', None)
            }])
            info_df.to_sql('info', conn, if_exists='append', index=False, 
                          dtype={'Ticker': 'TEXT', 'Name': 'TEXT', 'Industry': 'TEXT', 
                                 'MarketCap': 'REAL', 'TrailingPE': 'REAL', 
                                 'ForwardPE': 'REAL', 'TrailingEps': 'REAL'})
            logger.info(f"Successfully stored info data for {ticker}")

            # 3. 獲取財務報表 (年度和季報，優先使用最新數據)
            financials = stock.financials
            quarterly = stock.quarterly_financials
            
            if financials.empty and quarterly.empty:
                logger.warning(f"No financials data available for {ticker}")
                continue
            
            # 合併並轉置財務報表
            combined_financials = pd.concat([financials.T, quarterly.T], axis=0, keys=['Annual', 'Quarterly'])
            # 重塑為長格式
            combined_financials = combined_financials.reset_index()
            combined_financials = combined_financials.melt(
                id_vars=['level_0', 'level_1'],
                value_name='Value',
                var_name='Metric'
            ).drop(columns=['level_0'])  # 移除 ReportType
            combined_financials = combined_financials.rename(columns={'level_1': 'ReportDate'})
            combined_financials['Ticker'] = ticker
            # 處理 ReportDate，添加錯誤處理
            combined_financials['ReportDate'] = combined_financials['ReportDate'].apply(
                lambda x: pd.to_datetime(x, errors='coerce').strftime('%Y-%m-%d') if pd.notnull(x) else None
            )
            # 清理無效數據並去重
            combined_financials = combined_financials.dropna(subset=['ReportDate', 'Value'])
            combined_financials = combined_financials.drop_duplicates(
                subset=['Ticker', 'ReportDate', 'Metric'], keep='last'
            )
            # 選擇必要的欄位
            combined_financials = combined_financials[['Ticker', 'ReportDate', 'Metric', 'Value']]
            
            if combined_financials.empty:
                logger.warning(f"Cleaned financials data for {ticker} is empty after dropping NaN")
                continue
            
            # 調試輸出
            logger.debug(f"Combined financials columns for {ticker}: {combined_financials.columns}")
            logger.debug(f"Combined financials head for {ticker}: {combined_financials.head()}")
            # 插入資料庫，使用 replace 替代 append 以避免重複
            # --- 開始修改 ---
            
            # 寫入資料庫前，先刪除該 ticker 的舊資料，避免重複
            cursor = conn.cursor()
            cursor.execute("DELETE FROM financials WHERE Ticker = ?", (ticker,))
            conn.commit()

            # 使用 'append' 將新資料加入
            combined_financials.to_sql('financials', conn, if_exists='append', index=False, 
                                     dtype={'Ticker': 'TEXT', 'ReportDate': 'TEXT', 
                                            'Metric': 'TEXT', 'Value': 'REAL'})
            
            # --- 結束修改 ---
            logger.info(f"Successfully stored financials data for {ticker} with {len(combined_financials)} rows")

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            continue

    conn.close()
    logger.info("Data fetch process completed for all tickers.")

def main():
    """主函數，初始化資料庫並執行數據抓取"""
    try:
        init_db()  # 初始化資料庫
        fetch_and_store_all_data()
    except Exception as e:
        logger.error(f"Main process failed: {str(e)}")

if __name__ == '__main__':
    main()