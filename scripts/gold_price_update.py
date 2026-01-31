import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone

OZT_TO_GRAM = 31.1034768

DATA_DAILY = "data/Daily_SAR_Gram.csv"
DATA_MONTHLY = "data/Monthly_Avg.csv"
DATA_YEARLY = "data/Yearly_Avg.csv"

def read_daily():
    df = pd.read_csv(DATA_DAILY, parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df

def fetch_gold_close(date_from: str, date_to: str) -> pd.Series:
    """
    Gold from Stooq CSV (xauusd) — نجيب مدى صغير ونفلتر.
    ملاحظة: Stooq يعطي Open/High/Low/Close/Volume، نأخذ Close.
    """
    url = "https://stooq.com/q/d/l/?s=xauusd&i=d"
    g = pd.read_csv(url)
    g["Date"] = pd.to_datetime(g["Date"])
    g = g.set_index("Date").sort_index()
    close = g["Close"]
    return close.loc[pd.to_datetime(date_from): pd.to_datetime(date_to)]

def fetch_fx_close(date_from: str, date_to: str) -> pd.Series:
    fx = yf.download("USDSAR=X", start=date_from, end=date_to, progress=False, auto_adjust=False)
    if fx.empty:
        return pd.Series(dtype="float64")
    # حماية من MultiIndex
    if isinstance(fx.columns, pd.MultiIndex):
        if "Close" in fx.columns.get_level_values(0):
            s = fx["Close"]
            s = s.iloc[:, 0] if isinstance(s, pd.DataFrame) else s
        else:
            s = fx.iloc[:, 0]
    else:
        s = fx["Close"] if "Close" in fx.columns else fx.iloc[:, 0]
    s.index = pd.to_datetime(s.index)
    return s.loc[pd.to_datetime(date_from): pd.to_datetime(date_to)]

def compute_row(usd_ounce: float, usdsar: float):
    sar_24k = (usd_ounce * usdsar) / OZT_TO_GRAM
    sar_22k = sar_24k * (22/24)
    sar_21k = sar_24k * (21/24)
    sar_18k = sar_24k * (18/24)
    return round(sar_24k, 2), round(sar_22k, 2), round(sar_21k, 2), round(sar_18k, 2)

def main():
    daily = read_daily()
    last_date = daily["Date"].max().date()

    # نطلب “اليوم التالي” بعد آخر تاريخ موجود
    target_date = last_date + timedelta(days=1)

    # اليوم عند Actions يكون UTC؛ ما يهم، نجيب نافذة صغيرة ونختار أقرب يوم متاح
    # نجيب 10 أيام كاحتياط (عطلة/ويكند)
    date_from = (target_date - timedelta(days=3)).strftime("%Y-%m-%d")
    date_to = (target_date + timedelta(days=10)).strftime("%Y-%m-%d")

    gold = fetch_gold_close(date_from, date_to)
    fx = fetch_fx_close(date_from, date_to)

    if gold.empty:
        raise RuntimeError("No gold data returned from Stooq for the requested window.")

    # نختار أول يوم >= target_date موجود فعليًا في gold
    gold_dates = [d.date() for d in gold.index]
    candidates = [d for d in gold_dates if d >= target_date]
    if not candidates:
        # لو ما فيه بيانات بعد target_date، نوقف بدون تعديل (أفضل من إضافة خطأ)
        print("No newer gold data yet. Exiting without changes.")
        return

    use_date = min(candidates)

    # نفس الفكرة للصرف: نستخدم نفس التاريخ لو موجود، وإلا نأخذ آخر قيمة قبل/عند التاريخ
    fx_series = fx.copy()
    if fx_series.empty:
        # fallback: peg (لو ودّك تمنعه احذف هالجزء وخله يوقف)
        usdsar = 3.75
    else:
        fx_series = fx_series.sort_index()
        # خذ آخر قيمة <= use_date
        fx_up_to = fx_series.loc[:pd.to_datetime(use_date)]
        if fx_up_to.empty:
            usdsar = float(fx_series.iloc[0])
        else:
            usdsar = float(fx_up_to.iloc[-1])

    usd_ounce = float(gold.loc[pd.to_datetime(use_date)])
    sar_24k, sar_22k, sar_21k, sar_18k = compute_row(usd_ounce, usdsar)

    # لو الصف موجود أصلاً لا نضيف
    if (daily["Date"].dt.date == use_date).any():
        print(f"{use_date} already exists. Exiting.")
        return

    new_row = pd.DataFrame([{
        "Date": pd.to_datetime(use_date),
        "SAR_24K_G": sar_24k,
        "SAR_22K_G": sar_22k,
        "SAR_21K_G": sar_21k,
        "SAR_18K_G": sar_18k,
    }])

    daily2 = pd.concat([daily, new_row], ignore_index=True).sort_values("Date").reset_index(drop=True)
    daily2.to_csv(DATA_DAILY, index=False)

    monthly = daily2.set_index("Date").resample("ME").mean().round(2).reset_index()
    yearly  = daily2.set_index("Date").resample("YE").mean().round(2).reset_index()
    monthly.to_csv(DATA_MONTHLY, index=False)
    yearly.to_csv(DATA_YEARLY, index=False)

    print(f"Added row for {use_date}: 24K={sar_24k} SAR/g (FX={usdsar})")

if __name__ == "__main__":
    main()
