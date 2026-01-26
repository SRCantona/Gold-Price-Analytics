# 🇸🇦 GoldGauge — Saudi Gold Price Pipeline & Dashboard (2000 → 2025 + Jan 2026)

> A polished data pipeline + Power BI dashboard that fetches live gold futures, converts to SAR/gram for common karats, and visualizes historical trends and insights. Beautiful, repeatable, and ready for automation. ✨


<img width="1555" height="870" alt="37d0f4c2-1760-40fd-ab84-6b61e5c7fc92" src="https://github.com/user-attachments/assets/757bf779-062a-4b4b-b7c8-174b5663d898" />



## 🚀 Quick Summary
GoldGauge automatically:
- fetches historical gold futures (Yahoo Finance: `GC=F`),  
- converts USD/oz → SAR/gram (peg: **1 USD = 3.75 SAR**),  
- computes prices for **24K, 22K, 21K, 18K**,  
- writes **Daily / Monthly / Yearly** sheets to Excel,  
- and powers a Power BI dashboard for interactive analysis and presentation.

---

## 🔭 Features (Why this repo is cool)
- ✅ **Automated data pipeline** (online → Excel → Power BI)  
- ✅ **Karats breakdown**: 24K / 22K / 21K / 18K prices in SAR/gram  
- ✅ **Daily, monthly, yearly** aggregated sheets ready for visualization  
- ✅ **Power BI dashboard** with KPIs, year-over-year leaps, currency toggle (SAR / USD), and beautiful visuals  
- ✅ **Easily schedulable** for automated updates (cron, Task Scheduler, or GitHub Actions)

---
🟡 Why Gold? (The story behind the numbers)

Gold isn’t just jewelry — it’s one of the most important assets in the world economy.

It is widely seen as:

🛡️ A safe haven during uncertainty
📉 A hedge against inflation
💱 A global price reference affected by USD strength, interest rates, and geopolitical events
🧠 A market where history matters: long-term trends + sudden spikes tell a real story

In Saudi Arabia, gold is also a daily-life commodity — people buy and sell it as:

🎁 gifts 
💰savings 
📈investment 
🏦long-term value storage 

🧪 Gold Purity (Karats) — What do 18K and 21K mean?

Gold purity is measured in karats, where:

- 24K = pure gold (100%)
- 22K = 91.67% gold
- 21K = 87.5% gold
- 18K = 75% gold

That’s why the price changes based on purity:
"Lower karat = less pure gold = cheaper per gram"

---

🧠 Stage 1 — Online Gold Market Data (the source)
Gold in financial markets is usually priced in:
📌 USD per troy ounce
📌 Updated daily (sometimes intraday)

A popular global reference is Gold Futures, symbol:

📌 GC=F (Yahoo Finance)

This project starts by pulling the historical daily Close price.

Why “Close”?
Because it’s stable and consistent for time-series reporting.

---

🐍 Stage 2 — Python ETL (the engine)

Python is the “factory” in this project.

It handles:

✅ Fetching
✅ Cleaning
✅ Converting
✅ Aggregating
✅ Exporting

🔥 What Python does here (in a smart way)

Instead of manually collecting prices, Python turns the project into a repeatable system:

● Every run = updated dataset

● No copy/paste

● No manual edits

● No broken data structure

🧩 Step-by-step ETL logic
1) Fetch data

Python downloads gold futures history from 2000 until today.

2) Fix missing dates

Markets close on weekends/holidays → time series has gaps.
To make analysis smoother, we create a full daily timeline and fill gaps using interpolation.

This makes the dataset more dashboard-friendly and consistent.

3) Convert USD/oz → SAR/gram

Gold market data is in USD per ounce, but Saudi retail is SAR per gram.

So we apply 2 conversions:

1 ounce = 31.1034768 grams
1 USD = 3.75 SAR (peg)

---

🗄️ Stage 3 — Online Database (where data becomes “real”)

A serious analytics project doesn’t rely only on files.

So the next step is storing the pipeline output in an online database.

Why use an online DB?

Because it makes the project:
● scalable 📈

● auditable 🧾

● queryable ⚡

● shareable 👥

● automation-ready 🤖

Two layers of storage (professional setup)
🧱 Raw layer (unchanged source)

This keeps the original fetched price history.

Purpose:
● debugging

● trust

● reprocessing anytime

🧼 Clean layer (analytics-ready)

This contains the processed results:
● SAR/gram

● karats

● clean date series

● validated values

---

🧹 Stage 4 — Data Cleaning & Preparation (making it dashboard-ready)

This stage is where “data science discipline” shows up.

Gold price data needs cleaning because:

● missing market days happen

● sudden spikes can occur

● duplicates can exist

● time formatting can break joins

Key cleaning rules

✅ Handle missing dates
✅ Remove duplicates
✅ Ensure price > 0
✅ Detect extreme jumps
✅ Standardize rounding and types

Why this matters

Because dashboards are only as good as the dataset behind them.

A clean dataset means:

1- stable visuals
2- correct measures
3- trusted KPIs
4- accurate growth insights

---

📗 Stage 5 — Excel as the Data Warehouse Output

Even though databases are powerful, Excel is still the most common business format.

So we export the final dataset into a structured workbook.

The Excel file becomes a “gold warehouse”

It contains clean tables that Power BI can load instantly.

Recommended sheets:
● Daily_Prices 

● Monthly_Averages

● Yearly_Averages

This gives flexibility:

● daily chart analysis

● monthly smoothing

● yearly trend storytelling

---

📊 Stage 6 — Power BI Modeling (where insights are born)

Power BI is where the project becomes visual intelligence.

Once the Excel tables are loaded, we build:

● relationships

● measures

● calculated metrics

● time intelligence

Power BI transforms the dataset into:

✅ KPIs
✅ trend charts
✅ year-to-year growth
✅ price comparisons
✅ taxed vs non-taxed scenarios

---

● Final Result / Experience: This project delivers a complete Saudi gold price intelligence experience — turning raw global market data into clear, trusted, and interactive insights. 🟡✨

● Instead of relying on manual updates, the entire process becomes automated and repeatable, meaning the dashboard can always reflect the latest market movement with minimal effort.

● The project converts complex financial pricing (USD/ounce) into real Saudi retail meaning (SAR/gram), making it easier to understand gold value locally for different karats like 18K and 21K.

● By generating daily, monthly, and yearly views, it allows both short-term tracking and long-term historical analysis, giving a full story of how gold evolved from 2000 to 2025 (plus Jan 2026).

● The final Power BI dashboard becomes more than a visualization — it becomes a decision tool that highlights trends, growth, comparisons, and price changes over time in a professional way. 📊

● This project demonstrates real-world skills across the full data lifecycle: data collection, cleaning, transformation, storage logic, reporting structure, and business intelligence modeling. 🚀
● It creates a strong foundation that can easily be expanded into forecasting, real-time refresh, alerts, or even a public gold price API in the future.


● Conclusion: GoldGauge is a full end-to-end analytics solution that bridges global financial markets with Saudi gold pricing, delivering clean data, meaningful insights, and a powerful dashboard — all built with automation, accuracy, and scalability in mind. 


































