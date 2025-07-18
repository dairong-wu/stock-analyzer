# database.py
import sqlite3
import pandas as pd
from config import DB_FILE

def get_db_connection():
    """建立資料庫連線"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    """初始化資料庫和資料表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for table_name in ['kline_daily', 'financials', 'info']:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

    cursor.execute('''
    CREATE TABLE kline_daily (
        Ticker TEXT,
        Date TEXT,
        Open REAL,
        High REAL,
        Low REAL,
        Close REAL,
        Volume INTEGER,
        PRIMARY KEY (Ticker, Date)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE financials (
        Ticker TEXT,
        ReportDate TEXT,
        Metric TEXT,
        Value REAL,
        PRIMARY KEY (Ticker, ReportDate, Metric)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE info (
        Ticker TEXT PRIMARY KEY,
        Name TEXT,
        Industry TEXT,
        MarketCap REAL,
        TrailingPE REAL,
        ForwardPE REAL,
        TrailingEps REAL  -- 添加 TrailingEps 欄位
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized.")

def save_data(df, table_name, ticker):
    """將 DataFrame 存入指定資料表"""
    conn = get_db_connection()
    if not df.empty:
        conn.execute(f"DELETE FROM {table_name} WHERE Ticker = ?", (ticker,))
        df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()

def get_kline(ticker, period='daily'):
    """從資料庫讀取K線資料"""
    conn = get_db_connection()
    table_name = f"kline_{period}"
    df = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE Ticker = ? ORDER BY Date ASC", conn, params=(ticker,))
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    return df

"""def get_info(ticker):
    #從資料庫讀取公司基本資訊
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM info WHERE Ticker = ?", conn, params=(ticker,))
    return df.iloc[0] if not df.empty else None
"""    

def get_info(ticker):
    conn = sqlite3.connect('stock_data.db')
    query = "SELECT * FROM info WHERE Ticker = ?"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df.iloc[0] if not df.empty else None

def get_financials(ticker):
    """從資料庫讀取財報"""
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM financials WHERE Ticker = ?", conn, params=(ticker,))
    return df if not df.empty else pd.DataFrame()