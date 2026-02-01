import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

FILE_PATH = "data/Saudi_Gold_Prices.xlsx"
SYMBOL = "GC=F"

SAR_PEG = 3.75
OZT_TO_GRAM = 31.1034768

SHEET_DAILY = "Daily_Prices"
SHEET_MONTHLY = "Monthly_Averages"
SHEET_YEARLY = "Yearly_Averages"

START_FALLBACK = "2000-01-01"


def _safe_to_datetime(s):
    return pd.to_datetime(s, errors="coerce")


def _load_existing_daily(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"])

    xls = pd.ExcelFile(path)
    if SHEET_DAILY not in xls.sheet_names:
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"])

    df = pd.read_excel(path, sheet_name=SHEET_DAILY)
    df["Date"] = _safe_to_datetime(df["Date"])
    df = df.dropna(subset=["Date"]).sort_values("Date").drop_duplicates(subset=["Date"])
    return df.reset_index(drop=True)


def _download_gold_close(start_date: str, end_date: str) -> pd.Series:
    """
    end_date هنا يكون exclusive عملياً (yfinance)، فنمرر end_date+1 يوم عادة.
    """
    raw = yf.download(SYMBOL, start=start_date, end=end_date, progress=False, auto_adjust=False)

    if raw is None or raw.empty:
        return pd.Series(dtype="float64")

    # حماية من MultiIndex
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
        close = close.iloc[:, 0] if isinstance(close, pd.DataFrame) else close
    else:
        close = raw["Close"] if "Close" in raw.columns else raw.iloc[:, 0]

    close.index = pd.to_datetime(close.index)
    close = close.dropna().sort_index()
    return close


def _build_daily_prices(start_date: str, end_date: str) -> pd.DataFrame:
    """
    يبني أسعار يومية من start_date إلى end_date (شاملة end_date) باستخدام ffill.
    """
    # نجيب نافذة فيها end+1 عشان yfinance
    end_plus = (pd.to_datetime(end_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    close = _download_gold_close(start_date, end_plus)
    if close.empty:
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"])

    full = pd.date_range(start=start_date, end=end_date, freq="D")
    close = close.reindex(full).ffill()  # تعبئة أيام الويكند بآخر إغلاق
    df = pd.DataFrame({"Date": full, "USD_Ounce": close.values})

    # 24K SAR/gram
    df["SAR_24K"] = (df["USD_Ounce"] / OZT_TO_GRAM) * SAR_PEG
    df["SAR_22K"] = df["SAR_24K"] * (22 / 24)
    df["SAR_21K"] = df["SAR_24K"] * (21 / 24)
    df["SAR_18K"] = df["SAR_24K"] * (18 / 24)

    df[["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]] = df[
        ["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]
    ].round(2)

    return df[["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]]


def main():
    today = datetime.utcnow().date()  # Actions runs UTC
    today_str = today.strftime("%Y-%m-%d")

    existing = _load_existing_daily(FILE_PATH)

    if existing.empty:
        start = START_FALLBACK
    else:
        last_date = existing["Date"].max().date()
        # لو الملف فيه تواريخ مستقبلية بالغلط، نقصّها لليوم
        if last_date > today:
            existing = existing[existing["Date"].dt.date <= today].copy()
            if existing.empty:
                start = START_FALLBACK
            else:
                last_date = existing["Date"].max().date()
                start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

    # إذا ما فيه شيء جديد نضيفه
    if pd.to_datetime(start).date() > today:
        print("No new dates to add. Exit.")
        return

    new_daily = _build_daily_prices(start, today_str)

    if new_daily.empty:
        print("No new data fetched. Exit.")
        return

    # دمج بدون تكرار
    combined = pd.concat([existing, new_daily], ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"])
    combined = combined.dropna(subset=["Date"]).sort_values("Date").drop_duplicates(subset=["Date"]).reset_index(drop=True)

    # Monthly/Yearly
    monthly = combined.set_index("Date").resample("ME").mean().round(2).reset_index()
    yearly = combined.set_index("Date").resample("YE").mean().round(2).reset_index()

    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with pd.ExcelWriter(FILE_PATH, engine="openpyxl") as writer:
        combined.to_excel(writer, sheet_name=SHEET_DAILY, index=False)
        monthly.to_excel(writer, sheet_name=SHEET_MONTHLY, index=False)
        yearly.to_excel(writer, sheet_name=SHEET_YEARLY, index=False)

    print(f"Updated: {FILE_PATH} | Added rows: {len(new_daily)} | Total rows: {len(combined)}")


if __name__ == "__main__":
    main()
