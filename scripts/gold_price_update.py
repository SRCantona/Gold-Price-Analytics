import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# =========================
# Config
# =========================
FILE_PATH = "data/Saudi_Gold_Prices.xlsx"

SYMBOL = "GC=F"          # Gold futures (USD per troy ounce)
SAR_PEG = 3.75           # USD/SAR peg
OZT_TO_GRAM = 31.1034768

SHEET_DAILY = "Daily_Prices"
SHEET_MONTHLY = "Monthly_Averages"
SHEET_YEARLY = "Yearly_Averages"

START_FALLBACK = "2000-01-01"


# =========================
# Helpers
# =========================
def _load_existing_daily(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"])

    try:
        xls = pd.ExcelFile(path)
    except Exception:
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"])

    if SHEET_DAILY not in xls.sheet_names:
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"])

    df = pd.read_excel(path, sheet_name=SHEET_DAILY)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df.sort_values("Date").drop_duplicates(subset=["Date"]).reset_index(drop=True)
    return df


def _download_gold_close(start_date: str, end_date_exclusive: str) -> pd.Series:
    raw = yf.download(SYMBOL, start=start_date, end=end_date_exclusive,
                      progress=False, auto_adjust=False)

    if raw is None or raw.empty:
        return pd.Series(dtype="float64")

    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
        close = close.iloc[:, 0] if isinstance(close, pd.DataFrame) else close
    else:
        close = raw["Close"]

    close.index = pd.to_datetime(close.index)
    close = close.dropna().sort_index()
    return close


def _build_daily_prices(start_date: str, end_date: str) -> pd.DataFrame:
    end_plus = (pd.to_datetime(end_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    close = _download_gold_close(start_date, end_plus)

    if close.empty:
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"])

    first_valid = close.first_valid_index()
    effective_start = max(pd.to_datetime(start_date), first_valid)

    full = pd.date_range(start=effective_start, end=end_date, freq="D")

    close_daily = close.reindex(full).ffill()

    df = pd.DataFrame({
        "Date": full,
        "USD_Ounce": close_daily.values
    })

    df["SAR_24K"] = (df["USD_Ounce"] / OZT_TO_GRAM) * SAR_PEG
    df["SAR_22K"] = df["SAR_24K"] * (22 / 24)
    df["SAR_21K"] = df["SAR_24K"] * (21 / 24)
    df["SAR_18K"] = df["SAR_24K"] * (18 / 24)

    df[["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]] = \
        df[["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]].round(2)

    return df[["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]]


def _clean_daily(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    price_cols = ["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]
    for c in price_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=price_cols, how="all")

    today = datetime.utcnow().date()
    df = df[df["Date"].dt.date <= today]

    df = df.sort_values("Date").drop_duplicates(subset=["Date"]).reset_index(drop=True)
    return df


# =========================
# Main
# =========================
def main():
    today = datetime.utcnow().date()
    today_str = today.strftime("%Y-%m-%d")

    existing = _load_existing_daily(FILE_PATH)
    existing = _clean_daily(existing) if not existing.empty else existing

    if existing.empty:
        start = START_FALLBACK
    else:
        last_date = existing["Date"].max().date()
        start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

    if pd.to_datetime(start).date() > today:
        print("No new dates to add. Exit.")
        return

    new_daily = _build_daily_prices(start, today_str)
    if new_daily.empty:
        print("No new data fetched. Exit.")
        return

    combined = pd.concat([existing, new_daily], ignore_index=True)
    combined = _clean_daily(combined)

    monthly = combined.set_index("Date").resample("ME").mean().round(2).reset_index()
    yearly = combined.set_index("Date").resample("YE").mean().round(2).reset_index()

    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with pd.ExcelWriter(FILE_PATH, engine="openpyxl") as writer:
        combined.to_excel(writer, sheet_name=SHEET_DAILY, index=False)
        monthly.to_excel(writer, sheet_name=SHEET_MONTHLY, index=False)
        yearly.to_excel(writer, sheet_name=SHEET_YEARLY, index=False)

    print(f"✅ Updated successfully | Rows: {len(combined)}")


if __name__ == "__main__":
    main()
