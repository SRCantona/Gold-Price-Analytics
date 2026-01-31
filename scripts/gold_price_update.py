import os
import pandas as pd
from datetime import datetime, timedelta
from openpyxl import load_workbook

# =========================
# CONFIG (GitHub)
# =========================
EXCEL_PATH = "data/gold_prices.xlsx"
OUNCE_CSV_PATH = "data/ounce_usd.csv"  # لازم يكون موجود بالريبو

BOOTSTRAP_START_DATE = "2026-01-23"

SAR_PEG = 3.75
OUNCE_TO_GRAM = 31.1034768
KARAT_COLS = ["SAR_24K", "SAR_22K", "SAR_21K", "SAR_18K"]


# =========================
# EXCEL HELPERS
# =========================
def load_daily_any_sheet(path: str) -> pd.DataFrame:
    """Load Daily sheet if exists; else empty with standard columns."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=["Date"] + KARAT_COLS)

    wb = load_workbook(path)
    sheets = wb.sheetnames
    sheet = "Daily_Data" if "Daily_Data" in sheets else sheets[0]

    df = pd.read_excel(path, sheet_name=sheet)

    if "Date" not in df.columns:
        return pd.DataFrame(columns=["Date"] + KARAT_COLS)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    for c in KARAT_COLS:
        if c not in df.columns:
            df[c] = pd.NA

    return df[["Date"] + KARAT_COLS].copy()


def get_start_date(daily: pd.DataFrame) -> str:
    """Empty -> bootstrap date, else last_date+1."""
    if daily is None or len(daily) == 0:
        return BOOTSTRAP_START_DATE
    last_date = daily["Date"].max()
    return (last_date + timedelta(days=1)).strftime("%Y-%m-%d")


def write_yearly_note(excel_path: str):
    """Add YTD note on Yearly_Averages."""
    wb = load_workbook(excel_path)
    if "Yearly_Averages" not in wb.sheetnames:
        wb.save(excel_path)
        return

    ws = wb["Yearly_Averages"]
    existing = ws["A1"].value
    if existing and "Year-to-date" in str(existing):
        wb.save(excel_path)
        return

    ws.insert_rows(1)
    ws["A1"] = (
        "NOTE: Yearly_Averages = Year-to-date (YTD) average based on available days so far in the year "
        "(not a full completed year)."
    )
    max_col = ws.max_column
    if max_col >= 2:
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_col)

    wb.save(excel_path)


# =========================
# DATA SOURCE (Ounce USD CSV)
# =========================
def load_ounce_usd_csv(path: str) -> pd.DataFrame:
    """
    Expected CSV columns:
      Date, USD_Ounce
    Example:
      2026-01-23, 4990
      2026-01-24, 4989
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing CSV source file: {path}")

    df = pd.read_csv(path)
    if "Date" not in df.columns or "USD_Ounce" not in df.columns:
        raise ValueError("CSV must contain columns: Date, USD_Ounce")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["USD_Ounce"] = pd.to_numeric(df["USD_Ounce"], errors="coerce")
    df = df.dropna(subset=["Date", "USD_Ounce"]).sort_values("Date")
    return df


def compute_sar_karats_from_ounce(df_ounce: pd.DataFrame) -> pd.DataFrame:
    out = df_ounce.copy()
    out["SAR_24K"] = (out["USD_Ounce"] / OUNCE_TO_GRAM) * SAR_PEG
    out["SAR_22K"] = out["SAR_24K"] * (22 / 24)
    out["SAR_21K"] = out["SAR_24K"] * (21 / 24)
    out["SAR_18K"] = out["SAR_24K"] * (18 / 24)
    out[KARAT_COLS] = out[KARAT_COLS].round(2)
    return out[["Date"] + KARAT_COLS].copy()


# =========================
# MAIN
# =========================
def update_excel_sar_prices():
    daily = load_daily_any_sheet(EXCEL_PATH)
    start_date = get_start_date(daily)
    start_dt = pd.to_datetime(start_date)

    print(f"Updating from {start_date} to {datetime.now().strftime('%Y-%m-%d')}")

    # Load ounce prices
    ounce_df = load_ounce_usd_csv(OUNCE_CSV_PATH)

    # Filter to only new dates
    new_ounce = ounce_df[ounce_df["Date"] >= start_dt].copy()
    if new_ounce.empty:
        print("No new rows to add.")
        return

    new_rows = compute_sar_karats_from_ounce(new_ounce)

    # Merge
    daily = pd.concat([daily, new_rows], ignore_index=True, sort=False)
    daily = daily.drop_duplicates(subset=["Date"], keep="last")

    # ✅ FIX: Ensure Date is datetime for resampling
    daily["Date"] = pd.to_datetime(daily["Date"], errors="coerce")
    daily = daily.dropna(subset=["Date"]).sort_values("Date")

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

    os.makedirs(os.path.dirname(EXCEL_PATH) or ".", exist_ok=True)
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
        daily.to_excel(writer, sheet_name="Daily_Data", index=False)
        monthly.to_excel(writer, sheet_name="Monthly_Averages", index=False)
        yearly.to_excel(writer, sheet_name="Yearly_Averages", index=False)

    write_yearly_note(EXCEL_PATH)
    print("Excel updated successfully ✅")


if __name__ == "__main__":
    update_excel_sar_prices()
