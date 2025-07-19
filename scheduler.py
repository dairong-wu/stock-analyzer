# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from data_fetcher import fetch_and_store_all_data

def start_scheduler():
    """啟動排程器，設定每日固定時間更新資料"""
    scheduler = BackgroundScheduler()
    # 設定在每天的凌晨 2:00 執行更新任務
    scheduler.add_job(fetch_and_store_all_data, 'cron', hour=2, minute=0)
    scheduler.start()
    print("Scheduler started. Data will be updated daily at 2:00 AM.")