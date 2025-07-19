import pandas as pd
import numpy as np

def calculate_pe_valuation(eps, industry_pe=None, default_pe=15):
    """
    使用 P/E 法計算合理價值
    
    參數:
    - eps: 每股盈餘
    - industry_pe: 同業平均本益比（若無則使用預設值）
    - default_pe: 預設合理本益比
    
    返回: (合理價值, 使用的PE值, 計算說明)
    """
    if eps is None or pd.isna(eps) or eps <= 0:
        return None, None, "無法使用P/E法：EPS為負值或無資料"
    
    pe_used = industry_pe if industry_pe else default_pe
    fair_value = eps * pe_used
    
    explanation = f"使用 P/E 法：EPS ${eps:.2f} × PE {pe_used} = ${fair_value:.2f}"
    
    return fair_value, pe_used, explanation

def calculate_ddm_valuation(dividend, growth_rate=0.03, required_return=0.08):
    """
    使用股利折現模型（DDM）計算合理價值
    
    參數:
    - dividend: 年度股利
    - growth_rate: 股利成長率
    - required_return: 要求報酬率
    
    返回: (合理價值, 使用參數, 計算說明)
    """
    if dividend is None or pd.isna(dividend) or dividend <= 0:
        return None, None, "無法使用DDM：無股利發放或資料不足"
    
    if required_return <= growth_rate:
        return None, None, "無法使用DDM：成長率高於或等於要求報酬率"
    
    # Gordon Growth Model: V = D1 / (r - g)
    # D1 = D0 * (1 + g)
    next_dividend = dividend * (1 + growth_rate)
    fair_value = next_dividend / (required_return - growth_rate)
    
    explanation = f"使用 DDM：股利 ${dividend:.2f} × (1+{growth_rate:.1%}) / ({required_return:.1%} - {growth_rate:.1%}) = ${fair_value:.2f}"
    
    return fair_value, {"dividend": dividend, "g": growth_rate, "r": required_return}, explanation

def calculate_dcf_valuation(fcf, growth_rate=0.05, terminal_growth=0.02, 
                          required_return=0.10, years=5):
    """
    使用簡化的現金流折現模型（DCF）計算合理價值
    
    參數:
    - fcf: 自由現金流（每股）
    - growth_rate: 預測期成長率
    - terminal_growth: 終值成長率
    - required_return: 折現率
    - years: 預測年數
    
    返回: (合理價值, 使用參數, 計算說明)
    """
    if fcf is None or pd.isna(fcf) or fcf <= 0:
        return None, None, "無法使用DCF：自由現金流為負值或無資料"
    
    # 計算預測期現金流現值
    pv_cf = 0
    for year in range(1, years + 1):
        cf = fcf * (1 + growth_rate) ** year
        pv_cf += cf / (1 + required_return) ** year
    
    # 計算終值
    terminal_cf = fcf * (1 + growth_rate) ** years * (1 + terminal_growth)
    terminal_value = terminal_cf / (required_return - terminal_growth)
    pv_terminal = terminal_value / (1 + required_return) ** years
    
    fair_value = pv_cf + pv_terminal
    
    explanation = f"使用 DCF：FCF ${fcf:.2f}，{years}年成長率{growth_rate:.1%}，終值成長率{terminal_growth:.1%}，折現率{required_return:.1%} = ${fair_value:.2f}"
    
    return fair_value, {
        "fcf": fcf, 
        "growth_rate": growth_rate, 
        "terminal_growth": terminal_growth,
        "discount_rate": required_return
    }, explanation

def get_valuation_conclusion(current_price, fair_value, margin=0.15):
    """
    根據現價和合理價值判斷估值狀態
    
    參數:
    - current_price: 當前股價
    - fair_value: 計算的合理價值
    - margin: 安全邊際（預設15%）
    
    返回: (結論, 差異百分比)
    """
    if fair_value is None or current_price is None:
        return "無法評估", None
    
    diff_pct = (current_price - fair_value) / fair_value
    
    if current_price < fair_value * (1 - margin):
        return "低估", diff_pct
    elif current_price > fair_value * (1 + margin):
        return "高估", diff_pct
    else:
        return "合理", diff_pct

def perform_fundamental_valuation(info, financials_df, current_price):
    """
    執行完整的基本面估值分析
    
    參數:
    - info: 公司基本資訊
    - financials_df: 財務報表資料
    - current_price: 當前股價
    
    返回: 估值分析結果字典
    """
    valuation_results = {
        "當前股價": f"${current_price:.2f}",
        "估值方法": {}
    }
    
    # 1. P/E 估值法
    eps = info.get('TrailingEps')
    if eps and not pd.isna(eps):
        # 可以根據行業設定不同的合理PE值
        industry = info.get('Industry', '')
        industry_pe_map = {
            'Technology': 20,
            'Semiconductors': 18,
            'Software': 25,
            'Financial': 12,
            'Utilities': 15,
            'Consumer': 18
        }
        
        # 根據行業找合理PE，找不到就用預設值
        industry_pe = None
        for key, value in industry_pe_map.items():
            if key.lower() in industry.lower():
                industry_pe = value
                break
        
        pe_value, pe_used, pe_explanation = calculate_pe_valuation(eps, industry_pe)
        
        if pe_value:
            conclusion, diff_pct = get_valuation_conclusion(current_price, pe_value)
            valuation_results["估值方法"]["P/E估值法"] = {
                "合理價值": f"${pe_value:.2f}",
                "評估結論": conclusion,
                "價差": f"{diff_pct:.1%}" if diff_pct else "N/A",
                "計算說明": pe_explanation,
                "使用資料": {
                    "EPS": f"${eps:.2f}",
                    "合理PE": pe_used
                }
            }
    else:
        valuation_results["估值方法"]["P/E估值法"] = {
            "合理價值": "無法計算",
            "評估結論": "無法評估",
            "計算說明": "缺少EPS資料或EPS為負值"
        }
    
    # 2. DDM 股利折現模型
    # 嘗試從財務報表中獲取股利資訊
    dividend = None
    if not financials_df.empty:
        dividend_data = financials_df[financials_df['Metric'] == 'Dividends Per Share']
        if not dividend_data.empty:
            dividend = dividend_data.iloc[0]['Value']
    
    # 如果財報沒有，嘗試從info獲取
    if dividend is None or pd.isna(dividend):
        dividend = info.get('dividendRate', info.get('trailingAnnualDividendRate'))
    
    if dividend and not pd.isna(dividend) and dividend > 0:
        # 計算股利成長率（簡化：使用固定值或根據歷史計算）
        growth_rate = 0.03  # 預設3%成長
        
        ddm_value, ddm_params, ddm_explanation = calculate_ddm_valuation(
            dividend, growth_rate=growth_rate, required_return=0.08
        )
        
        if ddm_value:
            conclusion, diff_pct = get_valuation_conclusion(current_price, ddm_value)
            valuation_results["估值方法"]["DDM股利折現"] = {
                "合理價值": f"${ddm_value:.2f}",
                "評估結論": conclusion,
                "價差": f"{diff_pct:.1%}" if diff_pct else "N/A",
                "計算說明": ddm_explanation,
                "使用資料": {
                    "年度股利": f"${dividend:.2f}",
                    "成長率": f"{ddm_params['g']:.1%}",
                    "要求報酬率": f"{ddm_params['r']:.1%}"
                }
            }
    else:
        valuation_results["估值方法"]["DDM股利折現"] = {
            "合理價值": "無法計算",
            "評估結論": "無法評估", 
            "計算說明": "該公司不發放股利或股利資料不足"
        }
    
    # 3. DCF 現金流折現模型
    # 嘗試計算簡化的自由現金流
    fcf_per_share = None
    
    if not financials_df.empty:
        # 嘗試從財報獲取營運現金流和資本支出
        operating_cf = financials_df[financials_df['Metric'] == 'Operating Cash Flow']
        capex = financials_df[financials_df['Metric'] == 'Capital Expenditure']
        
        if not operating_cf.empty and not capex.empty:
            ocf = operating_cf.iloc[0]['Value']
            cap = abs(capex.iloc[0]['Value'])  # 資本支出通常是負值
            fcf = ocf - cap
            
            # 計算每股FCF
            shares = info.get('sharesOutstanding', info.get('impliedSharesOutstanding'))
            if shares and shares > 0:
                fcf_per_share = fcf / shares
    
    # 如果無法從財報計算，使用簡化方法
    if fcf_per_share is None and eps and not pd.isna(eps) and eps > 0:
        # 假設FCF約為EPS的80%（簡化假設）
        fcf_per_share = eps * 0.8
    
    if fcf_per_share and fcf_per_share > 0:
        # 根據公司成長性調整參數
        revenue_growth = info.get('revenueGrowth', 0.05)
        growth_rate = min(max(revenue_growth, 0.02), 0.15)  # 限制在2%-15%
        
        dcf_value, dcf_params, dcf_explanation = calculate_dcf_valuation(
            fcf_per_share, 
            growth_rate=growth_rate,
            terminal_growth=0.02,
            required_return=0.10
        )
        
        if dcf_value:
            conclusion, diff_pct = get_valuation_conclusion(current_price, dcf_value)
            valuation_results["估值方法"]["DCF現金流折現"] = {
                "合理價值": f"${dcf_value:.2f}",
                "評估結論": conclusion,
                "價差": f"{diff_pct:.1%}" if diff_pct else "N/A",
                "計算說明": dcf_explanation,
                "使用資料": {
                    "每股FCF": f"${fcf_per_share:.2f}",
                    "成長率": f"{dcf_params['growth_rate']:.1%}",
                    "終值成長率": f"{dcf_params['terminal_growth']:.1%}",
                    "折現率": f"{dcf_params['discount_rate']:.1%}"
                }
            }
    else:
        valuation_results["估值方法"]["DCF現金流折現"] = {
            "合理價值": "無法計算",
            "評估結論": "無法評估",
            "計算說明": "自由現金流為負值或資料不足"
        }
    
    # 綜合評估
    conclusions = []
    for method, result in valuation_results["估值方法"].items():
        if result.get("評估結論") and result["評估結論"] != "無法評估":
            conclusions.append(result["評估結論"])
    
    if conclusions:
        # 計算綜合結論
        conclusion_weights = {"低估": -1, "合理": 0, "高估": 1}
        weighted_sum = sum(conclusion_weights.get(c, 0) for c in conclusions)
        
        if weighted_sum <= -len(conclusions) * 0.5:
            overall_conclusion = "綜合評估：低估（建議買進）"
        elif weighted_sum >= len(conclusions) * 0.5:
            overall_conclusion = "綜合評估：高估（建議賣出）"
        else:
            overall_conclusion = "綜合評估：合理（建議持有）"
        
        valuation_results["綜合結論"] = overall_conclusion
    else:
        valuation_results["綜合結論"] = "資料不足，無法進行綜合評估"
    
    return valuation_results