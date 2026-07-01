# Fraud Detection Dashboard

A professional banking fraud detection dashboard built with Python and Streamlit, 
simulating real-time transaction monitoring work done by risk analysts at 
investment banks.

## Project Overview
Built an end-to-end fraud detection system on 5,000 synthetic banking transactions 
with rule-based detection, risk scoring, and interactive analytics.

## Key Features
- 5 rule-based fraud detection rules (large amounts, blacklisted countries, 
  odd hours, rapid transactions, unusual spending vs customer average)
- Risk scoring system (0-115) with 4 risk bands (Low/Medium/High/Critical)
- Executive summary dashboard with 6 interactive charts
- Sidebar filters (date, country, transaction type, customer, severity)
- Searchable suspicious transactions table with fraud reasons
- Customer risk profiling with individual risk trend charts
- Downloadable fraud investigation report (CSV)

## Results
- 126 fraud alerts detected out of 5,000 transactions (2.52%)
- Fraud concentrated in blacklisted countries (Iran, North Korea, Syria)
- Peak fraud activity: 1-5 AM window
- Top fraud merchant categories: Electronics, Grocery

## Tech Stack
Python | Streamlit | Pandas | NumPy | Plotly

## Files
- `app.py` — main Streamlit dashboard
- `generate_data.py` — synthetic transaction data generator
- `synthetic_transactions.csv` — generated dataset

## How to Run
pip install streamlit pandas numpy plotly
python -m streamlit run app.py
