# embedded_templates.py
# 將 HTML 模板內嵌到程式碼中，避免路徑問題

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>阿融股票分析器</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        a {
            color: #4CAF50;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .conclusion-buy {
            color: #4CAF50;
            font-weight: bold;
        }
        .conclusion-sell {
            color: #f44336;
            font-weight: bold;
        }
        .conclusion-hold {
            color: #ff9800;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>阿融股票分析器 - 股票總覽</h1>
    <table>
        <thead>
            <tr>
                <th>公司名稱</th>
                <th>股票代號</th>
                <th>目前股價</th>
                <th>本益比</th>
                <th>投資建議</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            {% for stock in summary %}
            <tr>
                <td>{{ stock.name }}</td>
                <td>{{ stock.ticker }}</td>
                <td>{{ stock.price }}</td>
                <td>{{ stock.pe }}</td>
                <td class="{{ stock.conclusion_class }}">
                    {% if stock.conclusion_class == 'conclusion-buy' %}
                        良好買入機會
                    {% elif stock.conclusion_class == 'conclusion-sell' %}
                        良好賣出機會
                    {% elif stock.conclusion_class == 'conclusion-hold' %}
                        暫時觀望
                    {% else %}
                        資料不足
                    {% endif %}
                </td>
                <td><a href="/stock/{{ stock.ticker }}">查看詳情</a></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

STOCK_DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company_name }} ({{ ticker }}) - 股票分析</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1, h2 {
            color: #333;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .analysis-item {
            margin: 10px 0;
            padding: 10px;
            background-color: #f9f9f9;
            border-left: 4px solid #4CAF50;
        }
        .signal-type {
            font-weight: bold;
            color: #666;
        }
        .recommendation {
            color: #4CAF50;
            font-weight: bold;
        }
        .conclusion-buy {
            background-color: #4CAF50;
            color: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
        }
        .conclusion-sell {
            background-color: #f44336;
            color: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
        }
        .conclusion-hold {
            background-color: #ff9800;
            color: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #4CAF50;
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .day-selector {
            margin: 20px 0;
        }
        .day-selector a {
            margin: 0 10px;
            padding: 5px 15px;
            background-color: #f0f0f0;
            text-decoration: none;
            color: #333;
            border-radius: 3px;
        }
        .day-selector a.active {
            background-color: #4CAF50;
            color: white;
        }
        ul {
            list-style-type: none;
            padding-left: 0;
        }
        li {
            margin: 5px 0;
            padding: 5px;
            background-color: #f0f0f0;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <a href="/" class="back-link">← 返回股票列表</a>
    
    <h1>{{ company_name }} ({{ ticker }}) - 股票分析報告</h1>
    
    <div class="day-selector">
        <span>選擇天數：</span>
        <a href="/stock/{{ ticker }}?days=20" {% if selected_days == 20 %}class="active"{% endif %}>20天</a>
        <a href="/stock/{{ ticker }}?days=60" {% if selected_days == 60 %}class="active"{% endif %}>60天</a>
        <a href="/stock/{{ ticker }}?days=120" {% if selected_days == 120 %}class="active"{% endif %}>120天</a>
    </div>
    
    <div class="container">
        <h2>K線圖與技術指標</h2>
        <div id="klineChart"></div>
        <div id="macdKdChart"></div>
    </div>
    
    <div class="container">
        <h2>最新 K 線型態分析（最近15根K線）</h2>
        {% if kline_analysis %}
            {% for analysis in kline_analysis %}
            <div class="analysis-item">
                <span style="color: #666; font-size: 0.9em;">{{ analysis.date }}</span>
                <span class="signal-type">{{ analysis.type }}：</span>
                <span>{{ analysis.signal }}</span>
                <span class="recommendation">（{{ analysis.recommendation }}）</span>
            </div>
            {% endfor %}
        {% else %}
            <p>最近15根K線內無明顯型態訊號</p>
        {% endif %}
    </div>
    
    <div class="container">
        <h2>基本面分析</h2>
        {% for key, value in fundamental_analysis.items() %}
        <div class="analysis-item">
            <strong>{{ key }}：</strong> {{ value }}
        </div>
        {% endfor %}
    </div>
    
    <div class="container">
        <h2>綜合投資建議</h2>
        <div class="{{ conclusion.class }}">
            {{ conclusion.text }}
        </div>
        <div style="margin-top: 15px;">
            <p><strong>買入分數：</strong> {{ conclusion.buy_score }}</p>
            <p><strong>賣出分數：</strong> {{ conclusion.sell_score }}</p>
            <p><strong>評分依據：</strong></p>
            <ul>
                {% for reason in conclusion.reasons %}
                    {% if '買進' in reason or '看漲' in reason or '向上' in reason or '多頭' in reason or '黃金交叉' in reason or '金叉' in reason or '低估' in reason or '成長' in reason %}
                        <li style="color: #4CAF50; font-weight: bold;">{{ reason }}</li>
                    {% elif '賣出' in reason or '看跌' in reason or '向下' in reason or '空頭' in reason or '死亡交叉' in reason or '死叉' in reason or '高估' in reason or '衰退' in reason %}
                        <li style="color: #f44336; font-weight: bold;">{{ reason }}</li>
                    {% else %}
                        <li>{{ reason }}</li>
                    {% endif %}
                {% endfor %}
            </ul>
        </div>
    </div>
    
    <script>
        // K線圖
        var klineData = {{ kline_json|safe }};
        Plotly.newPlot('klineChart', klineData.data, klineData.layout);
        
        // MACD 與 KD 圖
        var macdKdData = {{ macd_kd_json|safe }};
        Plotly.newPlot('macdKdChart', macdKdData.data, macdKdData.layout);
    </script>
</body>
</html>
"""