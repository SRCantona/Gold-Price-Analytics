import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from openpyxl import load_workbook

EXCEL_PATH = "data/gold_prices.xlsx"
URL = "https://saudigoldprice.com/"

KARAT_COLS = ["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]
BOOTSTRAP_START_DATE = "2026-01-23"


# -------------------------
# Load existing daily data
# -------------------------
def load_daily(path):
    if not os.path.exists(path):
        return pd.DataFrame(columns=["Date"] + KARAT_COLS)

    wb = load_workbook(path)
    sheet = "Daily_Data" if "Daily_Data" in wb.sheetnames else wb.sheetnames[0]
    df = pd.read_excel(path, sheet_name=sheet)

    if "Date" not in df.columns:
        return pd.DataFrame(columns=["Date"] + KARAT_COLS)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    for c in KARAT_COLS:
        if c not in df.columns:
            df[c] = pd.NA

    return df[["Date"] + KARAT_COLS]


# -------------------------
# Fetch today prices (SAR)
# -------------------------
def fetch_today_prices():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ar,en;q=0.9",
    }
    r = requests.get(URL, headers=headers, timeout=30)
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    def find_price(karat):
        m = re.search(
            rf"عيار\s*{karat}[^0-9]{{0,40}}([0-9]+\.[0-9]+)",
            text
        )
        return float(m.group(1)) if m else None

    prices = {
        "SAR_24K": find_price(24),
        "SAR_22K": find_price(22),
        "SAR_21K": find_price(21),
        "SAR_18K": find_price(18),
    }

    if any(v is None for v in prices.values()):
        raise RuntimeError("Failed to fetch gold prices from website")

    return prices


# -------------------------
# Main update logic
# -------------------------
def update_excel_sar_prices():
    daily = load_daily(EXCEL_PATH)

    today = pd.to_datetime(datetime.now().date())

    if not daily.empty and today <= daily["Date"].max():
        print("Today's data already exists.")
        return

    prices = fetch_today_prices()

    new_row = {"Date": today, **prices}
    daily = pd.concat([daily, pd.DataFrame([new_row])], ignore_index=True)

    daily["Date"] = pd.to_datetime(daily["Date"])
    daily = daily.sort_values("Date")

    daily_idx = daily.set_index("Date")

    monthly = (
        daily_idx[KARAT_COLS]
        .resample("ME")
        .mean()
        .round(2)
        .reset_index()
    )

    yearly = (
        daily_idx[KARAT_COLS]
        .resample("YE")
        .mean()
        .round(2)
        .reset_index()
    )

    os.makedirs("data", exist_ok=True)
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
        daily.to_excel(writer, sheet_name="Daily_Data", index=False)
        monthly.to_excel(writer, sheet_name="Monthly_Averages", index=False)
        yearly.to_excel(writer, sheet_name="Yearly_Averages", index=False)

    print("Gold prices updated successfully")


if __name__ == "__main__":
    update_excel_sar_prices()
