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

# إذا كان الملف فاضي أو غير موجود: نحاول نبدأ من هذا التاريخ، لكن فعلياً
# السكربت سيبدأ من "أول يوم فيه بيانات فعلية" من المصدر.
START_FALLBACK = "2000-01-01"


# =========================
# Helpers
# =========================
def _safe_to_datetime(s):
    return pd.to_datetime(s, errors="coerce")


def _load_existing_daily(path: str) -> pd.DataFrame:
    """Load existing Daily sheet if available, else return empty schema."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K", "IsTradingDay"])

    try:
        xls = pd.ExcelFile(path)
    except Exception:
        # لو الملف تالف/غير مقروء
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K", "IsTradingDay"])

    if SHEET_DAILY not in xls.sheet_names:
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K", "IsTradingDay"])

    df = pd.read_excel(path, sheet_name=SHEET_DAILY)
    if "Date" not in df.columns:
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K", "IsTradingDay"])

    df["Date"] = _safe_to_datetime(df["Date"])
    df = df.dropna(subset=["Date"]).sort_values("Date").drop_duplicates(subset=["Date"]).reset_index(drop=True)

    # Ensure IsTradingDay exists
    if "IsTradingDay" not in df.columns:
        df["IsTradingDay"] = 1

    # Keep only expected cols if extra columns exist
    keep = ["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K", "IsTradingDay"]
    keep = [c for c in keep if c in df.columns]
    df = df[keep]

    return df


def _download_gold_close(start_date: str, end_date_exclusive: str) -> pd.Series:
    """
    Download Close prices for SYMBOL from Yahoo.
    end_date_exclusive is exclusive in yfinance.
    """
    raw = yf.download(SYMBOL, start=start_date, end=end_date_exclusive, progress=False, auto_adjust=False)
    if raw is None or raw.empty:
        return pd.Series(dtype="float64")

    # Handle MultiIndex
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
    Build calendar-daily prices between start_date and end_date (inclusive),
    BUT starts from the first valid data point returned by the source
    (so no empty rows at the beginning).
    Adds IsTradingDay flag: 1 if source had a close for that day, else 0 (ffill).
    """
    # yfinance end is exclusive, so we add +1 day
    end_plus = (pd.to_datetime(end_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    close = _download_gold_close(start_date, end_plus)

    if close.empty:
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K", "IsTradingDay"])

    # ✅ Start from first valid data date (avoid leading empties)
    first_valid_ts = close.first_valid_index()
    if first_valid_ts is None:
        return pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K", "IsTradingDay"])

    effective_start = max(pd.to_datetime(start_date), first_valid_ts).strftime("%Y-%m-%d")

    full = pd.date_range(start=effective_start, end=end_date, freq="D")

    close_on_full = close.reindex(full)                 # NaN on non-trading days
    is_trading = close_on_full.notna().astype(int)      # 1 if real, 0 if filled
    close_filled = close_on_full.ffill()                # fill weekends/holidays

    df = pd.DataFrame({
        "Date": full,
        "USD_Ounce": close_filled.values,
        "IsTradingDay": is_trading.values
    })

    # Convert USD/ounce to SAR/gram for 24K then scale for other karats
    df["SAR_24K"] = (df["USD_Ounce"] / OZT_TO_GRAM) * SAR_PEG
    df["SAR_22K"] = df["SAR_24K"] * (22 / 24)
    df["SAR_21K"] = df["SAR_24K"] * (21 / 24)
    df["SAR_18K"] = df["SAR_24K"] * (18 / 24)

    df[["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]] = df[
        ["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]
    ].round(2)

    return df[["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K", "IsTradingDay"]]


def _clean_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Data preparation/cleaning:
    - parse Date
    - numeric prices
    - drop rows where all prices are NaN
    - drop future dates
    - drop duplicates
    - sort
    """
    df = df.copy()

    # Date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # Prices numeric
    price_cols = ["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]
    for c in price_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # IsTradingDay default if missing
    if "IsTradingDay" not in df.columns:
        df["IsTradingDay"] = 1
    df["IsTradingDay"] = pd.to_numeric(df["IsTradingDay"], errors="coerce").fillna(1).astype(int)

    # Drop rows where all prices are missing
    df = df.dropna(subset=price_cols, how="all")

    # Remove future dates (Actions runs UTC)
    today = datetime.utcnow().date()
    df = df[df["Date"].dt.date <= today]

    # Sort & de-duplicate
    df = df.sort_values("Date").drop_duplicates(subset=["Date"]).reset_index(drop=True)

    # Ensure first row has data (no leading empties)
    df = df.dropna(subset=price_cols, how="all").reset_index(drop=True)

    return df


# =========================
# Main
# =========================
def main():
    today = datetime.utcnow().date()
    today_str = today.strftime("%Y-%m-%d")

    existing = _load_existing_daily(FILE_PATH)
    existing = _clean_daily(existing) if not existing.empty else existing

    # Determine start date for new data
    if existing.empty:
        start = START_FALLBACK
    else:
        last_date = existing["Date"].max().date()
        start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

    # Nothing to add?
    if pd.to_datetime(start).date() > today:
        print("No new dates to add. Exit.")
        return

    new_daily = _build_daily_prices(start, today_str)

    # If source returned nothing, do not modify files
    if new_daily.empty:
        print("No new data fetched. Exit.")
        return

    # Combine old + new
    combined = pd.concat([existing, new_daily], ignore_index=True)

    # Clean/prep
    combined = _clean_daily(combined)

    # Recompute monthly/yearly from cleaned daily
    monthly = combined.set_index("Date")[["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]].resample("ME").mean().round(2).reset_index()
    yearly = combined.set_index("Date")[["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]].resample("YE").mean().round(2).reset_index()

    # Save Excel
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with pd.ExcelWriter(FILE_PATH, engine="openpyxl") as writer:
        combined.to_excel(writer, sheet_name=SHEET_DAILY, index=False)
        monthly.to_excel(writer, sheet_name=SHEET_MONTHLY, index=False)
        yearly.to_excel(writer, sheet_name=SHEET_YEARLY, index=False)

    # Report
    first_date = combined["Date"].min().date()
    last_date = combined["Date"].max().date()
    added_rows = len(new_daily["Date"].unique())

    print(f"✅ Updated: {FILE_PATH}")
    print(f"   Range: {first_date} -> {last_date}")
    print(f"   Added new calendar rows: {added_rows}")
    print(f"   Total rows (daily calendar): {len(combined)}")


if __name__ == "__main__":
    main()
