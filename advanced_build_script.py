import os
import shutil
import subprocess
import sys

def clean_build():
    """清理舊的打包檔案"""
    print("清理舊檔案...")
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # 刪除 .spec 檔案
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            os.remove(file)

def ensure_templates():
    """確保模板檔案存在"""
    print("檢查模板檔案...")
    if not os.path.exists('templates'):
        print("錯誤：找不到 templates 資料夾！")
        return False
    
    template_files = []
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                template_files.append(os.path.join(root, file))
    
    if not template_files:
        print("錯誤：templates 資料夾中沒有 HTML 檔案！")
        return False
    
    print(f"找到 {len(template_files)} 個模板檔案")
    return True

def create_spec_file():
    """創建 PyInstaller spec 檔案"""
    print("創建 spec 檔案...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 收集所有模板檔案
import os
template_files = []
for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            src = os.path.join(root, file)
            dst = root
            template_files.append((src, dst))

# 收集所有 Python 檔案
python_files = []
for file in os.listdir('.'):
    if file.endswith('.py') and file != 'gui_launcher.py':
        python_files.append((file, '.'))

a = Analysis(
    ['gui_launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('icon1.ico', '.'),
        ('embedded_templates.py', '.'),
    ] + template_files + python_files,
    hiddenimports=[
        'yfinance',
        'pandas',
        'pandas_ta',
        'pandas_ta.core',
        'pandas_ta.utils',
        'pandas_ta.momentum',
        'pandas_ta.overlap',
        'pandas_ta.trend',
        'pandas_ta.volatility',
        'pandas_ta.volume',
        'pandas_ta.statistics',
        'plotly',
        'plotly.graph_objects',
        'plotly.io',
        'flask',
        'sqlite3',
        'numpy',
        'scipy',
        'scipy.special',
        'scipy.stats',
        'werkzeug',
        'werkzeug.serving',
        'jinja2',
        'markupsafe',
        'itsdangerous',
        'click',
        'config',
        'database',
        'analysis_engine',
        'data_fetcher',
        'app',
        'embedded_templates',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='stock_analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon1.ico',
)
'''
    
    with open('stock_analyzer.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("spec 檔案創建完成")

def build_exe():
    """執行打包"""
    print("開始打包...")
    try:
        subprocess.run([sys.executable, '-m', 'PyInstaller', 'stock_analyzer.spec'], check=True)
        print("打包成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"打包失敗：{e}")
        return False

def post_build():
    """打包後處理"""
    print("執行打包後處理...")
    
    dist_path = os.path.join('dist')
    if not os.path.exists(dist_path):
        print("錯誤：dist 資料夾不存在！")
        return
    
    # 複製模板資料夾到 dist（作為備份）
    templates_src = 'templates'
    templates_dst = os.path.join(dist_path, 'templates')
    if os.path.exists(templates_src) and not os.path.exists(templates_dst):
        shutil.copytree(templates_src, templates_dst)
        print("已複製 templates 資料夾到 dist")
    
    # 複製 icon1.ico
    icon_src = 'icon1.ico'
    icon_dst = os.path.join(dist_path, 'icon1.ico')
    if os.path.exists(icon_src) and not os.path.exists(icon_dst):
        shutil.copy(icon_src, icon_dst)
        print("已複製 icon1.ico 到 dist")
    
    # 複製 embedded_templates.py（如果存在）
    embedded_src = 'embedded_templates.py'
    embedded_dst = os.path.join(dist_path, 'embedded_templates.py')
    if os.path.exists(embedded_src) and not os.path.exists(embedded_dst):
        shutil.copy(embedded_src, embedded_dst)
        print("已複製 embedded_templates.py 到 dist")

def main():
    print("=== 股票分析器進階打包腳本 ===\n")
    
    # 步驟 1：清理
    clean_build()
    
    # 步驟 2：檢查模板
    if not ensure_templates():
        print("\n打包失敗：請確保 templates 資料夾存在且包含 HTML 檔案")
        return
    
    # 步驟 3：檢查 icon
    if not os.path.exists('icon1.ico'):
        print("警告：找不到 icon1.ico，將使用預設圖標")
    
    # 步驟 4：創建 spec 檔案
    create_spec_file()
    
    # 步驟 5：執行打包
    if build_exe():
        # 步驟 6：後處理
        post_build()
        print("\n=== 打包完成！===")
        print("執行檔位於: dist\\stock_analyzer.exe")
    else:
        print("\n打包失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main()
    input("\n按 Enter 鍵結束...")