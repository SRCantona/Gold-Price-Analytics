# 🇸🇦 GoldGauge — Saudi Gold Price Pipeline & Dashboard (2000 → 2025 + Jan 2026)

> A polished data pipeline + Power BI dashboard that fetches live gold futures, converts to SAR/gram for common karats, and visualizes historical trends and insights. Beautiful, repeatable, and ready for automation. ✨

---

![Dashboard Preview](assets/dashboard_preview.png)  
*(Place your Power BI screenshot at `assets/dashboard_preview.png` in the repo — I used the style from your example README.)*

---

## 🚀 Quick Summary
GoldGauge automatically:
- fetches historical gold futures (Yahoo Finance: `GC=F`),  
- converts USD/oz → SAR/gram (peg: **1 USD = 3.75 SAR**),  
- computes prices for **24K, 22K, 21K, 18K**,  
- writes **Daily / Monthly / Yearly** sheets to Excel,  
- and powers a Power BI dashboard (`gold price.pbix`) for interactive analysis and presentation.

Includes a Jan 2026 update point (you mentioned "junn from 2026" — if you meant **Jan 2026**, this is covered; if you meant monthly 2026 data, the script supports daily granularity and can be extended).

---

## 🔭 Features (Why this repo is cool)
- ✅ **Automated data pipeline** (online → Excel → Power BI)  
- ✅ **Karats breakdown**: 24K / 22K / 21K / 18K prices in SAR/gram  
- ✅ **Daily, monthly, yearly** aggregated sheets ready for visualization  
- ✅ **Power BI dashboard** with KPIs, year-over-year leaps, currency toggle (SAR / USD), and beautiful visuals  
- ✅ **Easily schedulable** for automated updates (cron, Task Scheduler, or GitHub Actions)

---

## 📁 Repo Structure (suggested)
```
GoldGauge/
├─ .github/
│  └─ workflows/update-data.yml         # optional: GitHub Actions schedule
├─ assets/
│  └─ dashboard_preview.png             # dashboard screenshot
├─ data/
│  └─ Saudi_Gold_Prices_2000_2026.xlsx  # generated data (gitignored)
├─ src/
│  └─ generate_saudi_gold_price_report.py
├─ dashboard/
│  └─ gold price.pbix
├─ requirements.txt
├─ README.md
└─ .gitignore
```

---

## 🧠 How It Works (architecture)
1. **Fetch** — `yfinance` downloads `GC=F` (gold futures close price) daily.  
2. **Interpolate** — missing days are linearly interpolated to produce continuous daily values.  
3. **Convert** — `USD/Ounce → SAR/gram` with:
   ```
   SAR_24K = (USD_Ounce / 31.1034768) * 3.75
   ```
   Other karats are proportional to 24K:
   ```
   SAR_22K = SAR_24K * 22/24
   SAR_21K = SAR_24K * 21/24
   SAR_18K = SAR_24K * 18/24
   ```
4. **Aggregate** — produce daily, monthly (month-end mean), yearly (year-end mean).  
5. **Export** — write to `Saudi_Gold_Prices_2000_2026.xlsx` with sheets `Daily_Prices`, `Monthly_Averages`, `Yearly_Averages`.  
6. **Visualize** — open `gold price.pbix` in Power BI pointing at the Excel file and refresh.

---

## 🧩 Files included
- `src/generate_saudi_gold_price_report.py` — main script (you provided this).  
- `dashboard/gold price.pbix` — Power BI report.  
- `GOLD .xlsx` or `data/Saudi_Gold_Prices_2000_2026.xlsx` — raw/generated dataset.  
- `assets/dashboard_preview.png` — screenshot used in README.

---

## ▶️ How to run (local)
1. Clone repo.
2. Create virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate      # Windows
   ```
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   python src/generate_saudi_gold_price_report.py
   ```
5. Open `data/Saudi_Gold_Prices_2000_2026.xlsx` (or `GOLD .xlsx`) in Power BI and refresh the report.

---

## 📃 Example `requirements.txt`
```
pandas>=1.5
yfinance>=0.2
openpyxl>=3.0
numpy>=1.22
```

---

## 🛠 Optional Automation

### Cron (Linux) — daily at 02:00:
```cron
0 2 * * * /path/to/.venv/bin/python /path/to/GoldGauge/src/generate_saudi_gold_price_report.py >> /path/to/GoldGauge/logs/update.log 2>&1
```

### GitHub Actions — scheduled run (example)
Create `.github/workflows/update-data.yml`:
```yaml
name: scheduled-data-update
on:
  schedule:
    - cron: '0 2 * * *'  # daily at 02:00 UTC
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run generator
        run: python src/generate_saudi_gold_price_report.py
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: Saudi_Gold_Prices
          path: data/Saudi_Gold_Prices_2000_2026.xlsx
```
> Note: If you want to automatically push the Excel to the repo you’ll need to configure a PAT and push via action (careful with credentials & repo size).

---

## 📈 Power BI tips
- Use `Year` and `Month` columns from `Yearly_Averages` and `Monthly_Averages` to build slicers.  
- Create KPI cards for 18K & 21K current values and use DAX for % change (YoY).  
- Use conditional formatting and a dark theme for the gold aesthetic (like your screenshot).  
- Add a toggle parameter for currency (SAR / USD) and compute conversion in Power Query or DAX.

---

## ✨ Nice-to-have / Future Ideas
- Add **forecasting** (Prophet / ARIMA / ML) for 2026+ projections.  
- Add **monthly breakdown** in the dashboard and a small multiples chart for karats.  
- Add **tax calculations** and an interactive tax-rate slider in Power BI.  
- Expose a tiny Flask API to serve latest prices for other apps.  
- Add unit tests for the conversion logic.

---

## 🧾 License & Attribution
This repo is for analytics, educational, and demonstration purposes. Use responsibly. Add your preferred open-source license (MIT, Apache-2.0, etc.) if you plan to publish.

---

## 👤 Author
**You** — add your name and optionally a GitHub / LinkedIn link here.

---

## ✅ Want me to also:
- generate `requirements.txt` and `.gitignore`? ✅  
- create the GitHub Actions YAML and commit-ready README file (full repo)? ✅  
- rewrite README in Arabic or adapt it for a portfolio/LinkedIn blurb? ✅

Tell me which of the above you want me to output next and I’ll paste the files ready-to-commit (README.md, requirements.txt, .github/workflows/update-data.yml, .gitignore).
