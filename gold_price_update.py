import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os

EXCEL_PATH = "data/gold_prices.xlsx"

def generate_saudi_gold_price_report():

    symbol = "GC=F"
    sar_peg = 3.75
    ounce_to_gram = 31.1034768

    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError("Excel file not found")

    # -------------------------------
    # 1. Load existing data
    # -------------------------------
    daily = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Daily_Prices",
        parse_dates=["Date"]
    )

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
    if gold_data.empty:
        print("No new market data.")
        return

    df = gold_data[['Close']].copy()
    df.columns = ['USD_Ounce']
    df.reset_index(inplace=True)

    # -------------------------------
    # 3. Calculate all karats
    # -------------------------------
    df['SAR_24K'] = (df['USD_Ounce'] / ounce_to_gram) * sar_peg
    df['SAR_22K'] = df['SAR_24K'] * (22 / 24)
    df['SAR_21K'] = df['SAR_24K'] * (21 / 24)
    df['SAR_18K'] = df['SAR_24K'] * (18 / 24)

    karat_cols = ['SAR_24K', 'SAR_22K', 'SAR_21K', 'SAR_18K']
    df[karat_cols] = df[karat_cols].round(2)

    new_daily = df[['Date'] + karat_cols]

    # -------------------------------
    # 4. Merge with existing
    # -------------------------------
    for col in karat_cols:
        if col not in daily.columns:
            daily[col] = None

    daily = pd.concat([daily, new_daily], ignore_index=True)
    daily = daily.drop_duplicates(subset=['Date']).sort_values('Date')

    # -------------------------------
    # 5. Recalculate Monthly & Yearly
    # -------------------------------
    monthly = (
        daily.set_index('Date')
        .resample('ME')
        .mean()
        .round(2)
        .reset_index()
    )

    yearly = (
        daily.set_index('Date')
        .resample('YE')
        .mean()
        .round(2)
        .reset_index()
    )

    # -------------------------------
    # 6. Save Excel
    # -------------------------------
    with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl', mode='w') as writer:
        daily.to_excel(writer, sheet_name='Daily_Prices', index=False)
        monthly.to_excel(writer, sheet_name='Monthly_Averages', index=False)
        yearly.to_excel(writer, sheet_name='Yearly_Averages', index=False)

    print("Excel updated successfully with all karats!")


# Run
generate_saudi_gold_price_report()
