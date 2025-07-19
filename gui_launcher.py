import tkinter as tk
from tkinter import messagebox, ttk
import os
import sys
import webbrowser
import threading
import time
import json
from data_fetcher import fetch_and_store_all_data
from app import app as flask_app


# 取得執行檔案的目錄
if getattr(sys, 'frozen', False):
    # 如果是打包後的 exe
    application_path = os.path.dirname(sys.executable)
else:
    # 如果是開發環境
    application_path = os.path.dirname(os.path.abspath(__file__))

# 設定路徑
CONFIG_FILE = os.path.join(application_path, 'config.json')
DB_FILE = os.path.join(application_path, 'stock_data.db')
TEMPLATE_PATH = os.path.join(application_path, 'templates')

# 檢查模板路徑是否存在
if not os.path.exists(TEMPLATE_PATH):
    print(f"Warning: Template path not found at {TEMPLATE_PATH}")
    # 嘗試其他可能的路徑
    possible_paths = [
        os.path.join(os.path.dirname(application_path), 'templates'),
        os.path.join(application_path, '_internal', 'templates'),
        'templates'
    ]
    for path in possible_paths:
        if os.path.exists(path):
            TEMPLATE_PATH = path
            print(f"Found templates at: {TEMPLATE_PATH}")
            break

# 全域變數，用於儲存 TICKERS
TICKERS = {}

def load_config():
    """載入設定檔"""
    global TICKERS
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                TICKERS = config.get('TICKERS', {})
        except Exception as e:
            print(f"載入設定檔失敗: {e}")
            # 使用預設值
            TICKERS = {
                'NVIDIA': 'NVDA',
                '台積電': '2330.TW',
                '聯電': '2303.TW',
                '鴻海': '2317.TW',
            }
    else:
        # 使用預設值
        TICKERS = {
            'NVIDIA': 'NVDA',
            '台積電': '2330.TW',
            '聯電': '2303.TW',
            '鴻海': '2317.TW',
        }
        save_config()

def save_config():
    """儲存設定檔"""
    try:
        config = {
            'TICKERS': TICKERS,
            'DB_FILE': DB_FILE
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"儲存設定檔失敗: {e}")
        return False

# 修改 config.py 模組的變數
import config
config.TICKERS = TICKERS
config.DB_FILE = DB_FILE

# 修改 database.py 使用正確的路徑
import database
database.DB_FILE = DB_FILE

class StockAnalysisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("股票分析工具\n此工具僅供學術研究與技術展示，不構成任何投資建議")
        self.root.geometry("400x400")
        
        # 設定 GUI 圖標
        icon_path = os.path.join(application_path, "icon1.ico")
        if not os.path.exists(icon_path):
            # 嘗試其他可能的路徑
            possible_icon_paths = [
                os.path.join(os.path.dirname(application_path), 'icon1.ico'),
                os.path.join(application_path, '_internal', 'icon1.ico'),
                'icon1.ico'
            ]
            for path in possible_icon_paths:
                if os.path.exists(path):
                    icon_path = path
                    break
        
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except tk.TclError as e:
                print(f"無法載入圖標: {e}")
        
        # 設定 Flask 模板路徑
        flask_app.template_folder = TEMPLATE_PATH
        
        # 標題
        tk.Label(root, text="股票分析工具\n此工具僅供學術研究與技術展示，不構成任何投資建議", font=("Arial", 12, "bold")).pack(pady=10)
        
        # 顯示當前股票清單
        self.ticker_label = tk.Label(root, text="當前股票清單：\n" + self.format_tickers(), wraplength=350)
        self.ticker_label.pack(pady=10)
        
        # 三個按鈕
        tk.Button(root, text="股票清單編輯", command=self.edit_tickers, width=20).pack(pady=10)
        tk.Button(root, text="抓取奇摩股市數據", command=self.fetch_data, width=20).pack(pady=10)
        tk.Button(root, text="開啟 HTML 網頁", command=self.open_webpage, width=20).pack(pady=10)
        
        # 狀態標籤
        self.status_label = tk.Label(root, text="準備就緒", wraplength=350)
        self.status_label.pack(pady=20)
        
        # 啟動 Flask 伺服器在背景線程
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
        
        # 等待伺服器啟動
        time.sleep(2)
    
    def format_tickers(self):
        """格式化 TICKERS 字典以顯示"""
        return "\n".join([f"{name}: {ticker}" for name, ticker in TICKERS.items()]) if TICKERS else "無股票清單"
    
    def edit_tickers(self):
        """開啟股票清單編輯視窗"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title("編輯股票清單")
        edit_window.geometry("500x400")
        
        tk.Label(edit_window, text="輸入股票代號和名稱（格式：代號,名稱; 每行一組）").pack(pady=10)
        
        # 文字輸入框
        text_area = tk.Text(edit_window, height=10, width=50)
        text_area.pack(pady=10)
        
        # 預填當前 TICKERS
        current_tickers = "\n".join([f"{ticker},{name}" for name, ticker in TICKERS.items()])
        text_area.insert(tk.END, current_tickers)
        
        def save_tickers():
            """保存編輯的股票清單"""
            global TICKERS
            input_text = text_area.get("1.0", tk.END).strip()
            new_tickers = {}
            try:
                for line in input_text.split("\n"):
                    if line.strip():
                        ticker, name = line.split(",")
                        ticker = ticker.strip().upper()
                        name = name.strip()
                        if ticker and name:
                            new_tickers[name] = ticker
                if not new_tickers:
                    messagebox.showerror("錯誤", "請至少輸入一組有效股票代號和名稱")
                    return
                
                TICKERS = new_tickers
                # 更新 config 模組的變數
                config.TICKERS = TICKERS
                
                if save_config():
                    self.ticker_label.config(text="當前股票清單：\n" + self.format_tickers())
                    messagebox.showinfo("成功", "股票清單已更新")
                    edit_window.destroy()
            except Exception as e:
                messagebox.showerror("錯誤", f"解析股票清單失敗：{str(e)}")
        
        tk.Button(edit_window, text="保存清單", command=save_tickers).pack(pady=10)
    
    def fetch_data(self):
        """執行資料抓取"""
        def run_fetch():
            self.status_label.config(text="正在抓取資料...")
            self.root.update()
            
            try:
                # 確保使用最新的 TICKERS
                config.TICKERS = TICKERS
                fetch_and_store_all_data()
                self.status_label.config(text="資料抓取成功")
                messagebox.showinfo("成功", "資料抓取完成")
            except Exception as e:
                messagebox.showerror("錯誤", f"資料抓取失敗：{str(e)}")
                self.status_label.config(text="資料抓取失敗")
        
        # 在新線程中執行，避免阻塞 GUI
        threading.Thread(target=run_fetch, daemon=True).start()
    
    def open_webpage(self):
        """開啟瀏覽器顯示網頁"""
        self.status_label.config(text="開啟網頁...")
        self.root.update()
        
        try:
            webbrowser.open("http://localhost:5000")
            self.status_label.config(text="網頁已開啟，請查看")
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟網頁失敗：{str(e)}")
            self.status_label.config(text="開啟失敗")
    
    def run_server(self):
        """在背景線程中運行 Flask 伺服器"""
        try:
            flask_app.run(port=5000, debug=False, use_reloader=False, threaded=True)
        except Exception as e:
            print(f"Flask 伺服器錯誤: {e}")

def main():
    # 載入設定
    load_config()
    from database import init_db
    init_db()
    root = tk.Tk()
    app = StockAnalysisGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()