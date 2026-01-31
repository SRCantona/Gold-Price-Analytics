import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone

OZT_TO_GRAM = 31.1034768

DATA_DAILY = "data/Daily_SAR_Gram.csv"
DATA_MONTHLY = "data/Monthly_Avg.csv"
DATA_YEARLY = "data/Yearly_Avg.csv"

FX_SYMBOLS = ["USDSAR=X", "SAR=X"]  # fallback

def read_daily():
    df = pd.read_csv(DATA_DAILY)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    return df

def fetch_gold_stooq():
    url = "https://stooq.com/q/d/l/?s=xauusd&i=d"
    g = pd.read_csv(url)
    g["Date"] = pd.to_datetime(g["Date"])
    g = g.set_index("Date").sort_index()
    return g["Close"]  # USD per ounce

def fetch_fx_close(start, end):
    # يحاول أكثر من رمز لأن Yahoo أحيانًا يغيّر
    for sym in FX_SYMBOLS:
        fx = yf.download(sym, start=start, end=end, progress=False, auto_adjust=False)
        if fx is None or fx.empty:
            continue

        if isinstance(fx.columns, pd.MultiIndex):
            s = fx["Close"]
            s = s.iloc[:, 0] if isinstance(s, pd.DataFrame) else s
        else:
            s = fx["Close"] if "Close" in fx.columns else fx.iloc[:, 0]

        s.index = pd.to_datetime(s.index)
        s = s.dropna()
        if not s.empty:
            return s, sym

    return pd.Series(dtype="float64"), None

def compute_prices(usd_ounce, usdsar):
    sar_24 = (usd_ounce * usdsar) / OZT_TO_GRAM
    return {
        "SAR_24K_G": round(sar_24, 2),
        "SAR_22K_G": round(sar_24 * (22/24), 2),
        "SAR_21K_G": round(sar_24 * (21/24), 2),
        "SAR_18K_G": round(sar_24 * (18/24), 2),
    }

def main():
    daily = read_daily()
    if daily.empty:
        raise RuntimeError("Daily CSV is empty or Date invalid.")

    # ✅ نعتمد على تاريخ اليوم الحقيقي (UTC) بدل آخر صف
    today = datetime.now(timezone.utc).date()

    # إذا عندك صف لنفس تاريخ اليوم—لا تسوي شيء
    if (daily["Date"].dt.date == today).any():
        print(f"{today} already exists. Exit.")
        return

    # نافذة بحث: آخر 15 يوم (عشان عطلات/ويكند)
    start = (today - timedelta(days=20)).strftime("%Y-%m-%d")
    end = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    gold = fetch_gold_stooq()
    if gold.empty:
        raise RuntimeError("No gold data from Stooq.")

    # اختر آخر يوم تداول <= today
    gold_upto = gold.loc[:pd.to_datetime(today)]
    if gold_upto.empty:
        print("No gold trading data up to today. Exit.")
        return
    trade_date = gold_upto.index.max().date()
    usd_ounce = float(gold_upto.loc[pd.to_datetime(trade_date)])

    fx_series, fx_sym = fetch_fx_close(start, end)
    if fx_series.empty:
        # fallback: peg (إذا تبي توقف بدل peg قلّي)
        usdsar = 3.75
        fx_sym = "PEG_3.75"
    else:
        fx_upto = fx_series.loc[:pd.to_datetime(trade_date)]
        usdsar = float(fx_upto.iloc[-1]) if not fx_upto.empty else float(fx_series.iloc[-1])

    prices = compute_prices(usd_ounce, usdsar)

    # ✅ نضيف صف بتاريخ "today" حتى لو trade_date كان أمس (عطلة)
    new_row = {"Date": pd.to_datetime(today), **prices}
    daily2 = pd.concat([daily, pd.DataFrame([new_row])], ignore_index=True)
    daily2 = daily2.sort_values("Date").reset_index(drop=True)

    daily2.to_csv(DATA_DAILY, index=False)

    monthly = daily2.set_index("Date").resample("ME").mean().round(2).reset_index()
    yearly  = daily2.set_index("Date").resample("YE").mean().round(2).reset_index()

    monthly.to_csv(DATA_MONTHLY, index=False)
    yearly.to_csv(DATA_YEARLY, index=False)

    print(f"✅ Added row for {today} (gold trade date {trade_date}) | 24K={prices['SAR_24K_G']} SAR/g | FX={usdsar} ({fx_sym})")

if __name__ == "__main__":
    main()
