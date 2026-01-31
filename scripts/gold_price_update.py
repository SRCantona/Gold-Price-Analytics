import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
from openpyxl import load_workbook

EXCEL_PATH = "data/gold_prices.xlsx"

def load_daily(EXCEL_PATH: str) -> pd.DataFrame:
    """Load daily data from Excel even if sheet names differ."""
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Excel file not found: {EXCEL_PATH}")

    wb = load_workbook(EXCEL_PATH)
    sheets = wb.sheetnames

    # Prefer standard sheet name, otherwise fallback to first sheet
    sheet_to_use = "Daily_Data" if "Daily_Data" in sheets else sheets[0]

    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_to_use)

    # Normalize expected schema
    if "Date" not in df.columns:
        # If the existing file doesn't have Date, start fresh
        df = pd.DataFrame(columns=["Date", "SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"])
    else:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

    return df

def generate_saudi_gold_price_report():
    symbol = "GC=F"
    sar_peg = 3.75
    ounce_to_gram = 31.1034768

    # -------------------------------
    # 1. Load existing data (safe)
    # -------------------------------
    daily = load_daily(EXCEL_PATH)

    if len(daily) == 0:
        # If empty, start from earliest date you want
        start_date = "2000-01-01"
    else:
        last_date = daily["Date"].max()
        start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

    end_date = datetime.now().strftime("%Y-%m-%d")

    print(f"Updating from {start_date} to {end_date}")

    if start_date > end_date:
        print("No new data needed.")
        return

    # -------------------------------
    # 2. Download new data
    # -------------------------------
    gold_data = yf.download(symbol, start=start_date, end=end_date)

    if gold_data is None or gold_data.empty or "Close" not in gold_data.columns:
        print("No new market data (or failed to fetch).")
        return

    df = gold_data[["Close"]].copy()
    df.columns = ["USD_Ounce"]
    df.reset_index(inplace=True)  # Date column will be here (usually named 'Date' by yfinance)

    # Sometimes yfinance returns index named 'Date' but column might be 'Date' or something else
    if "Date" not in df.columns:
        # If it came as 'index'
        if "index" in df.columns:
            df.rename(columns={"index": "Date"}, inplace=True)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # -------------------------------
    # 3. Calculate all karats
    # -------------------------------
    df["SAR_24K"] = (df["USD_Ounce"] / ounce_to_gram) * sar_peg
    df["SAR_22K"] = df["SAR_24K"] * (22 / 24)
    df["SAR_21K"] = df["SAR_24K"] * (21 / 24)
    df["SAR_18K"] = df["SAR_24K"] * (18 / 24)

    karat_cols = ["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]
    df[karat_cols] = df[karat_cols].round(2)

    new_daily = df[["Date"] + karat_cols]

    # -------------------------------
    # 4. Merge with existing
    # -------------------------------
    for col in karat_cols:
        if col not in daily.columns:
            daily[col] = pd.NA

    daily = pd.concat([daily, new_daily], ignore_index=True)
    daily = daily.drop_duplicates(subset=["Date"], keep="last").sort_values("Date")

    # -------------------------------
    # 5. Recalculate Monthly & Yearly
    # -------------------------------
    monthly = (
        daily.set_index("Date")[karat_cols]
        .resample("ME")
        .mean()
        .round(2)
        .reset_index()
    )

    yearly = (
        daily.set_index("Date")[karat_cols]
        .resample("YE")
        .mean()
        .round(2)
        .reset_index()
    )

    # -------------------------------
    # 6. Save Excel with standard sheet names
    # -------------------------------
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
        daily[["Date"] + karat_cols].to_excel(writer, sheet_name="Daily_Data", index=False)
        monthly.to_excel(writer, sheet_name="Monthly_Averages", index=False)
        yearly.to_excel(writer, sheet_name="Yearly_Averages", index=False)

    print("Excel updated successfully with all karats!")

# Run
generate_saudi_gold_price_report()
