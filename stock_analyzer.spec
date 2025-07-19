# -*- mode: python ; coding: utf-8 -*-

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
