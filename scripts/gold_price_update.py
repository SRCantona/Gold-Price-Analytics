import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

OZT_TO_GRAM = 31.1034768

DATA_DAILY = "data/Daily_SAR_Gram.csv"
DATA_MONTHLY = "data/Monthly_Avg.csv"
DATA_YEARLY = "data/Yearly_Avg.csv"


# ---------- Helpers ----------
def read_daily():
    df = pd.read_csv(DATA_DAILY)

    # إجبار تحويل التاريخ
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # حذف أي صف تاريخُه غير صالح
    df = df.dropna(subset=["Date"])

    df = df.sort_values("Date").reset_index(drop=True)
    return df


def fetch_gold_stooq():
    url = "https://stooq.com/q/d/l/?s=xauusd&i=d"
    g = pd.read_csv(url)
    g["Date"] = pd.to_datetime(g["Date"])
    g = g.set_index("Date").sort_index()
    return g["Close"]


def fetch_usdsar(start, end):
    fx = yf.download(
        "USDSAR=X",
        start=start,
        end=end,
        progress=False,
        auto_adjust=False
    )

    if fx.empty:
        return pd.Series(dtype="float64")

    if isinstance(fx.columns, pd.MultiIndex):
        fx = fx["Close"].iloc[:, 0]
    else:
        fx = fx["Close"]

    fx.index = pd.to_datetime(fx.index)
    return fx


def compute_prices(usd_ounce, usdsar):
    sar_24 = (usd_ounce * usdsar) / OZT_TO_GRAM
    return {
        "SAR_24K_G": round(sar_24, 2),
        "SAR_22K_G": round(sar_24 * (22 / 24), 2),
        "SAR_21K_G": round(sar_24 * (21 / 24), 2),
        "SAR_18K_G": round(sar_24 * (18 / 24), 2),
    }


# ---------- Main ----------
def main():
    daily = read_daily()

    if daily.empty:
        raise RuntimeError("Daily CSV is empty or Date column invalid.")

    last_date = daily["Date"].max().date()
    target_date = last_date + timedelta(days=1)

    # نافذة بحث صغيرة تحسبًا للويكند
    start = (target_date - timedelta(days=3)).strftime("%Y-%m-%d")
    end = (target_date + timedelta(days=10)).strftime("%Y-%m-%d")

    gold = fetch_gold_stooq()
    fx = fetch_usdsar(start, end)

    if gold.empty:
        print("No gold data available. Exit.")
        return

    # اختيار أول يوم تداول >= target_date
    gold_dates = gold.index.date
    candidates = [d for d in gold_dates if d >= target_date]

    if not candidates:
        print("No new trading day yet. Exit.")
        return

    use_date = min(candidates)

    # منع التكرار
    if (daily["Date"].dt.date == use_date).any():
        print(f"{use_date} already exists. Exit.")
        return

    usd_ounce = float(gold.loc[pd.to_datetime(use_date)])

    # سعر الصرف
    fx_up_to = fx.loc[:pd.to_datetime(use_date)]
    usdsar = float(fx_up_to.iloc[-1]) if not fx_up_to.empty else 3.75

    prices = compute_prices(usd_ounce, usdsar)

    new_row = {
        "Date": pd.to_datetime(use_date),
        **prices
    }

    daily = pd.concat(
        [daily, pd.DataFrame([new_row])],
        ignore_index=True
    ).sort_values("Date")

    # حفظ اليومي
    daily.to_csv(DATA_DAILY, index=False)

    # تحديث الشهري والسنوي
    monthly = (
        daily.set_index("Date")
        .resample("ME")
        .mean()
        .round(2)
        .reset_index()
    )

    yearly = (
        daily.set_index("Date")
        .resample("YE")
        .mean()
        .round(2)
        .reset_index()
    )

    monthly.to_csv(DATA_MONTHLY, index=False)
    yearly.to_csv(DATA_YEARLY, index=False)

    print(f"✅ Added {use_date} | 24K={prices['SAR_24K_G']} SAR/g | FX={usdsar}")


if __name__ == "__main__":
    main()
