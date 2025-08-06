import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Cache data with optimized loading
@st.cache_data(ttl=3600)
def load_data():
    try:
        mfrr_df = pd.read_excel("MFRR CM.xlsx", sheet_name="Sheet1")
        mfrr_df['Period'] = pd.to_datetime(mfrr_df['Period'])
        
        fcr_df = pd.read_excel("FCR Dashboard.xlsx", sheet_name="data 2021-2023")
        fcr_df['Datum'] = pd.to_datetime(fcr_df['Datum'])
        
        return mfrr_df, fcr_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

mfrr_df, fcr_df = load_data()

# Title
st.title('Energy Market Dashboard')

# Get date range
min_date = min(mfrr_df['Period'].min(), fcr_df['Datum'].min())
max_date = max(mfrr_df['Period'].max(), fcr_df['Datum'].max())

# Date selection
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
with col2:
    end_date = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)

# Convert to datetime
start_date = datetime.combine(start_date, datetime.min.time())
end_date = datetime.combine(end_date, datetime.min.time())

# Filter data
date_filter = lambda df, col: df[(df[col] >= start_date) & (df[col] <= end_date)]
mfrr_df_filtered = date_filter(mfrr_df, 'Period')
fcr_df_filtered = date_filter(fcr_df, 'Datum')

# FCR Price Visualization
st.header('FCR Prices')

# Prepare FCR data
fcr_price_df = fcr_df_filtered.melt(
    id_vars=['Datum'],
    value_vars=['FCR-N Pris (EUR/MW)', 'FCR-D upp Pris (EUR/MW)', 'FCR-D ned Pris (EUR/MW)'],
    var_name='Product',
    value_name='Price'
)
fcr_price_df['Product'] = fcr_price_df['Product'].str.replace(' Pris \(EUR/MW\)', '', regex=True)

# Create combined FCR plot
fig_fcr = go.Figure()

# Add stacked areas for FCR-D
for product in ['FCR-D upp', 'FCR-D ned']:
    product_df = fcr_price_df[fcr_price_df['Product'] == product]
    fig_fcr.add_trace(go.Scatter(
        x=product_df['Datum'],
        y=product_df['Price'],
        stackgroup='fcr_d',
        name=product,
        mode='lines',
        line=dict(width=0.5),
        hoverinfo='x+y+name'
    ))

# Add line for FCR-N
fcr_n_df = fcr_price_df[fcr_price_df['Product'] == 'FCR-N']
fig_fcr.add_trace(go.Scatter(
    x=fcr_n_df['Datum'],
    y=fcr_n_df['Price'],
    name='FCR-N',
    mode='lines',
    line=dict(color='red', width=2),
    hoverinfo='x+y+name'
))

fig_fcr.update_layout(
    title='FCR Prices (EUR/MW)',
    yaxis_title='Price (EUR/MW)',
    hovermode='x unified',
    showlegend=True
)

st.plotly_chart(fig_fcr, use_container_width=True)

# mFRR Price Visualization
st.header('mFRR Prices')

# Prepare mFRR data
mfrr_price_df = mfrr_df_filtered.melt(
    id_vars=['Period'],
    value_vars=['mFRR Upp Pris (EUR/MW)', 'mFRR Ned Pris (EUR/MW)'],
    var_name='Product',
    value_name='Price'
)
mfrr_price_df['Product'] = mfrr_price_df['Product'].str.replace('mFRR ', '').str.replace(' Pris \(EUR/MW\)', '', regex=True)

# Create combined mFRR plot
fig_mfrr = go.Figure()

for product in ['Upp', 'Ned']:
    product_df = mfrr_price_df[mfrr_price_df['Product'] == product]
    fig_mfrr.add_trace(go.Scatter(
        x=product_df['Period'],
        y=product_df['Price'],
        name=f'mFRR {product}',
        mode='lines',
        hoverinfo='x+y+name'
    ))

fig_mfrr.update_layout(
    title='mFRR Prices (EUR/MW)',
    yaxis_title='Price (EUR/MW)',
    hovermode='x unified'
)

st.plotly_chart(fig_mfrr, use_container_width=True)

# Price Analysis Section
st.header('Price Analysis')

# Combine all price data
all_prices = pd.concat([
    fcr_price_df.rename(columns={'Datum': 'Date', 'Product': 'Market'}),
    mfrr_price_df.rename(columns={'Period': 'Date', 'Product': 'Market'}).assign(Market=lambda x: 'mFRR ' + x['Market'])
])

# Top Price Points
st.subheader('Top Price Points')
top_n = st.slider('Number of top prices to show', 5, 50, 10)
top_prices = all_prices.nlargest(top_n, 'Price')[['Date', 'Market', 'Price']]
st.dataframe(
    top_prices.style.format({
        'Price': '{:.2f} EUR/MW',
        'Date': lambda x: x.strftime('%Y-%m-%d %H:%M')
    }),
    height=min((top_n + 1) * 35 + 3, 500)
)

# Price Distribution
st.subheader('Price Distribution')
fig_dist = px.box(
    all_prices,
    x='Market',
    y='Price',
    color='Market',
    points="all",
    hover_data=['Date'],
    labels={'Price': 'Price (EUR/MW)', 'Market': 'Product'},
    height=500
)
st.plotly_chart(fig_dist, use_container_width=True)