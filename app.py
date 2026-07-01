import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="🏦",
    layout="wide"
)

# Premium dark green/gold theme CSS
st.markdown("""
    <style>
    .stApp { background-color: #0a1628; color: #ffffff; }
    .stMetric { 
        background-color: #132237; 
        padding: 15px; 
        border-radius: 10px;
        border-left: 4px solid #c9a84c;
    }
    h1, h2, h3 { color: #c9a84c; }
    .stDataFrame { background-color: #132237; }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🏦 Banking Fraud Detection Dashboard")
st.markdown("*Real-time transaction monitoring and fraud analysis*")
st.divider()

# File uploader
uploaded_file = st.file_uploader("Upload Transaction CSV", type=['csv'])

if uploaded_file is None:
    st.info("👆 Please upload a CSV file to begin analysis")
    st.stop()

@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df['Hour'] = df['Timestamp'].dt.hour
    df['DayOfWeek'] = df['Timestamp'].dt.day_name()
    return df

df = load_data(uploaded_file)
st.success(f"✅ Loaded {len(df):,} transactions successfully!")
st.dataframe(df.head())

st.divider()
st.subheader("🔍 Running Fraud Detection Rules")

data = df.copy()
data['risk_score'] = 0
data['fraud_reasons'] = [[] for _ in range(len(data))]

def add_flag(mask, points, reason):
    data.loc[mask, 'risk_score'] += points
    for idx in data[mask].index:
        data.at[idx, 'fraud_reasons'].append(reason)

# Rule 1: Unusually large transaction (top 2% of amounts)
amount_threshold = data['Amount'].quantile(0.98)
mask = data['Amount'] > amount_threshold
add_flag(mask, 30, f"Unusually large amount (>₹{amount_threshold:,.0f})")

# Rule 2: Transactions outside business hours (11PM - 5AM)
mask = (data['Hour'] >= 23) | (data['Hour'] <= 5)
add_flag(mask, 20, "Transaction outside business hours")

# Rule 3: Blacklisted countries
blacklisted = ['North Korea', 'Iran', 'Syria']
mask = data['Location'].isin(blacklisted)
add_flag(mask, 40, "Transaction from blacklisted country")

# Rule 4: Multiple transactions in short time (same customer, within 10 mins)
data_sorted = data.sort_values(['CustomerID', 'Timestamp'])
data_sorted['time_diff'] = data_sorted.groupby('CustomerID')['Timestamp'].diff().dt.total_seconds() / 60
rapid_mask = data_sorted['time_diff'] < 10
rapid_indices = data_sorted[rapid_mask].index
mask = data.index.isin(rapid_indices)
add_flag(mask, 25, "Multiple transactions within 10 minutes")

# Rule 5: Unusual spending vs customer's own average
customer_avg = data.groupby('CustomerID')['Amount'].transform('mean')
customer_std = data.groupby('CustomerID')['Amount'].transform('std').fillna(0)
mask = data['Amount'] > (customer_avg + 2*customer_std)
add_flag(mask, 25, "Amount significantly higher than customer's average")

st.write(f"✅ Rules applied. Risk scores range from {data['risk_score'].min()} to {data['risk_score'].max()}")
st.write(data[['TransactionID', 'CustomerID', 'Amount', 'risk_score', 'fraud_reasons']].sort_values('risk_score', ascending=False).head(10))
st.divider()

# Risk bands
def risk_band(score):
    if score >= 80:
        return 'Critical'
    elif score >= 50:
        return 'High'
    elif score >= 25:
        return 'Medium'
    else:
        return 'Low'

data['RiskBand'] = data['risk_score'].apply(risk_band)
data['IsFraud'] = data['risk_score'] >= 50  # threshold for "flagged as fraud"

# Sidebar filters
st.sidebar.header("🔎 Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    value=(data['Timestamp'].min().date(), data['Timestamp'].max().date())
)

country_filter = st.sidebar.multiselect(
    "Country",
    options=data['Location'].unique(),
    default=data['Location'].unique()
)

type_filter = st.sidebar.multiselect(
    "Transaction Type",
    options=data['TransactionType'].unique(),
    default=data['TransactionType'].unique()
)

customer_search = st.sidebar.text_input("Search Customer ID")

severity_filter = st.sidebar.multiselect(
    "Risk Severity",
    options=['Low', 'Medium', 'High', 'Critical'],
    default=['Low', 'Medium', 'High', 'Critical']
)

# Apply filters
filtered_data = data[
    (data['Timestamp'].dt.date >= date_range[0]) &
    (data['Timestamp'].dt.date <= date_range[1]) &
    (data['Location'].isin(country_filter)) &
    (data['TransactionType'].isin(type_filter)) &
    (data['RiskBand'].isin(severity_filter))
]

if customer_search:
    filtered_data = filtered_data[filtered_data['CustomerID'].str.contains(customer_search, case=False)]

st.sidebar.metric("Filtered Transactions", len(filtered_data))
# Executive Summary Cards
st.subheader("📊 Executive Summary")
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Total Transactions", f"{len(data):,}")
col2.metric("Fraud Alerts", f"{data['IsFraud'].sum():,}")
col3.metric("Fraud %", f"{(data['IsFraud'].sum()/len(data)*100):.2f}%")
col4.metric("Total Value", f"₹{data['Amount'].sum()/100000:.1f}L")
col5.metric("High-Risk Customers", f"{data[data['IsFraud']]['CustomerID'].nunique():,}")
col6.metric("Avg Transaction", f"₹{data['Amount'].mean():,.0f}")

st.divider()
st.subheader("📈 Fraud Analytics")

# Custom dark plotly theme
plot_template = dict(
    layout=dict(
        paper_bgcolor='#0a1628',
        plot_bgcolor='#132237',
        font=dict(color='#ffffff'),
        colorway=['#c9a84c', '#1a472a', '#2d6a4f', '#e63946']
    )
)

col1, col2 = st.columns(2)

# Chart 1 — Fraud trend over time
with col1:
    daily_fraud = data.groupby(data['Timestamp'].dt.date)['IsFraud'].sum().reset_index()
    daily_fraud.columns = ['Date', 'FraudCount']
    fig1 = px.line(daily_fraud, x='Date', y='FraudCount', 
                    title='Fraud Trend Over Time', markers=True)
    fig1.update_layout(**plot_template['layout'])
    fig1.update_traces(line_color='#c9a84c')
    st.plotly_chart(fig1, use_container_width=True)

# Chart 2 — Fraud by country
with col2:
    country_fraud = data[data['IsFraud']]['Location'].value_counts().reset_index()
    country_fraud.columns = ['Location', 'Count']
    fig2 = px.bar(country_fraud, x='Location', y='Count', 
                   title='Fraud by Country', color='Count',
                   color_continuous_scale=['#1a472a', '#c9a84c'])
    fig2.update_layout(**plot_template['layout'])
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

# Chart 3 — Fraud by transaction type
with col3:
    type_fraud = data[data['IsFraud']]['TransactionType'].value_counts().reset_index()
    type_fraud.columns = ['TransactionType', 'Count']
    fig3 = px.pie(type_fraud, names='TransactionType', values='Count', 
                   title='Fraud by Transaction Type',
                   color_discrete_sequence=['#c9a84c', '#1a472a', '#2d6a4f', '#e63946', '#457b9d'])
    fig3.update_layout(**plot_template['layout'])
    st.plotly_chart(fig3, use_container_width=True)

# Chart 4 — Fraud by merchant category
with col4:
    merchant_fraud = data[data['IsFraud']]['Merchant'].value_counts().reset_index()
    merchant_fraud.columns = ['Merchant', 'Count']
    fig4 = px.bar(merchant_fraud, x='Count', y='Merchant', orientation='h',
                   title='Fraud by Merchant Category', color='Count',
                   color_continuous_scale=['#1a472a', '#c9a84c'])
    fig4.update_layout(**plot_template['layout'])
    st.plotly_chart(fig4, use_container_width=True)

col5, col6 = st.columns(2)

# Chart 5 — Heatmap: Fraud by Hour and Day
with col5:
    day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    heatmap_data = data[data['IsFraud']].groupby(['DayOfWeek','Hour']).size().reset_index(name='Count')
    heatmap_pivot = heatmap_data.pivot(index='DayOfWeek', columns='Hour', values='Count')
    heatmap_pivot = heatmap_pivot.reindex(index=day_order, columns=range(24)).fillna(0)
    
    fig5 = px.imshow(heatmap_pivot, 
                      title='Fraud Heatmap: Hour vs Day',
                      labels=dict(x="Hour", y="Day", color="Fraud Count"),
                      color_continuous_scale=['#0a1628', '#1a472a', '#c9a84c'],
                      aspect='auto')
    fig5.update_layout(**plot_template['layout'])
    st.plotly_chart(fig5, use_container_width=True)

# Chart 6 — Amount distribution
with col6:
    fig6 = px.histogram(data, x='Amount', color='IsFraud', nbins=50,
                         title='Amount Distribution (Fraud vs Normal)',
                         color_discrete_map={True: '#e63946', False: '#1a472a'})
    fig6.update_layout(**plot_template['layout'])
    st.plotly_chart(fig6, use_container_width=True)

st.divider()
st.subheader("🚨 Suspicious Transactions")

suspicious = filtered_data[filtered_data['IsFraud']].sort_values('risk_score', ascending=False)

display_df = suspicious[['TransactionID', 'CustomerID', 'Amount', 'Timestamp', 
                          'Location', 'Merchant', 'TransactionType', 
                          'risk_score', 'RiskBand', 'fraud_reasons']].copy()

display_df['fraud_reasons'] = display_df['fraud_reasons'].apply(lambda x: '; '.join(x))

st.write(f"Showing {len(display_df)} suspicious transactions matching filters")
st.dataframe(display_df, use_container_width=True, height=400)

# Downloadable report
st.divider()
st.subheader("📥 Export Report")

csv = display_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Fraud Investigation Report (CSV)",
    data=csv,
    file_name=f"fraud_report_{datetime.now().strftime('%Y%m%d')}.csv",
    mime='text/csv'
)

st.divider()
st.subheader("👤 Customer Risk Profile")

selected_customer = st.selectbox(
    "Select a Customer to View Profile",
    options=sorted(data['CustomerID'].unique())
)

cust_data = data[data['CustomerID'] == selected_customer].sort_values('Timestamp')

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Transactions", len(cust_data))
col2.metric("Flagged as Fraud", cust_data['IsFraud'].sum())
col3.metric("Avg Risk Score", f"{cust_data['risk_score'].mean():.1f}")
col4.metric("Total Spend", f"₹{cust_data['Amount'].sum():,.0f}")

# Risk trend over time for this customer
fig7 = px.line(cust_data, x='Timestamp', y='risk_score', 
                title=f'Risk Score Trend — {selected_customer}', markers=True)
fig7.update_layout(**plot_template['layout'])
fig7.update_traces(line_color='#c9a84c')
fig7.add_hline(y=50, line_dash="dash", line_color="#e63946", 
                annotation_text="Fraud Threshold")
st.plotly_chart(fig7, use_container_width=True)

# Transaction history table
st.write("**Transaction History**")
hist_display = cust_data[['TransactionID', 'Amount', 'Timestamp', 'Merchant', 
                           'Location', 'risk_score', 'RiskBand']].copy()
st.dataframe(hist_display, use_container_width=True)