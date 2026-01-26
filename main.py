import pandas as pd
import yfinance as yf
from datetime import datetime


def generate_saudi_gold_price_report(
    file_name: str = 'Saudi_Gold_Prices_2000_2026.xlsx'
):
    symbol = "GC=F"
    start_date = "2000-01-01"
    end_date = datetime.now().strftime('%Y-%m-%d')

    sar_peg = 3.75
    ounce_to_gram = 31.1034768

    print(f"Fetching Gold data from {start_date} to {end_date}...")

    # 1. Download data
    gold_data = yf.download(symbol, start=start_date, end=end_date)
    df = gold_data[['Close']].copy()
    df.columns = ['USD_Ounce']

    # 2. Fill missing days
    full_range = pd.date_range(start=start_date, end=end_date, freq='D')
    df = df.reindex(full_range).interpolate(method='linear')
    df.index.name = 'Date'
    df.reset_index(inplace=True)

    # 3. Base 24K price (SAR / gram)
    df['SAR_24K'] = (df['USD_Ounce'] / ounce_to_gram) * sar_peg

    # 4. Saudi karats
    df['SAR_22K'] = df['SAR_24K'] * (22 / 24)
    df['SAR_21K'] = df['SAR_24K'] * (21 / 24)
    df['SAR_18K'] = df['SAR_24K'] * (18 / 24)

    # 5. Round prices
    df[['SAR_24K', 'SAR_22K', 'SAR_21K', 'SAR_18K']] = \
        df[['SAR_24K', 'SAR_22K', 'SAR_21K', 'SAR_18K']].round(2)

    # 6. Final table
    daily = df[['Date', 'SAR_24K', 'SAR_22K', 'SAR_21K', 'SAR_18K']]

    # 7. Monthly & Yearly averages
    monthly = daily.set_index('Date').resample('ME').mean().round(2).reset_index()
    yearly = daily.set_index('Date').resample('YE').mean().round(2).reset_index()

    # 8. Save Excel
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        daily.to_excel(writer, sheet_name='Daily_Prices', index=False)
        monthly.to_excel(writer, sheet_name='Monthly_Averages', index=False)
        yearly.to_excel(writer, sheet_name='Yearly_Averages', index=False)

    print(f"Report Created Successfully: {file_name}")


# Run
generate_saudi_gold_price_report()
