import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Load data functions
@st.cache_data
def load_mfrr_data():
    try:
        df = pd.read_excel("MFRR CM.xlsx", sheet_name="Sheet1")
        df['Period'] = pd.to_datetime(df['Period'])
        return df
    except Exception as e:
        st.error(f"Error loading MFRR data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_fcr_data():
    try:
        df = pd.read_excel("FCR Dashboard.xlsx", sheet_name="data 2021-2023")
        df['Datum'] = pd.to_datetime(df['Datum'])
        return df
    except Exception as e:
        st.error(f"Error loading FCR data: {e}")
        return pd.DataFrame()

# Load all data
mfrr_df = load_mfrr_data()
fcr_df = load_fcr_data()

# Title
st.title('Energy Market Dashboard')

# Date range selection
date_col1, date_col2 = st.columns(2)
with date_col1:
    start_date = st.date_input(
        "Start date",
        value=min(mfrr_df['Period'].min(), fcr_df['Datum'].min()),
        min_value=min(mfrr_df['Period'].min(), fcr_df['Datum'].min()),
        max_value=max(mfrr_df['Period'].max(), fcr_df['Datum'].max())
    )
with date_col2:
    end_date = st.date_input(
        "End date",
        value=max(mfrr_df['Period'].max(), fcr_df['Datum'].max()),
        min_value=min(mfrr_df['Period'].min(), fcr_df['Datum'].min()),
        max_value=max(mfrr_df['Period'].max(), fcr_df['Datum'].max())
    )

# Convert to datetime
start_date = datetime.combine(start_date, datetime.min.time())
end_date = datetime.combine(end_date, datetime.min.time())

# FCR Price Visualization
st.header('FCR Prices')
fcr_price_cols = ['FCR-N Pris (EUR/MW)', 'FCR-D upp Pris (EUR/MW)', 'FCR-D ned Pris (EUR/MW)']
fcr_price_df = fcr_df[['Datum'] + fcr_price_cols].copy()
fcr_price_df = fcr_price_df.melt(
    id_vars=['Datum'], 
    value_vars=fcr_price_cols,
    var_name='Product',
    value_name='Price'
)
fcr_price_df['Product'] = fcr_price_df['Product'].str.replace(' Pris \(EUR/MW\)', '', regex=True)
fcr_price_df = fcr_price_df[(fcr_price_df['Datum'] >= start_date) & (fcr_price_df['Datum'] <= end_date)]

fig_fcr = px.area(
    fcr_price_df,
    x='Datum',
    y='Price',
    color='Product',
    title='FCR Prices (EUR/MW)',
    labels={'Price': 'Price (EUR/MW)', 'Datum': 'Date'},
    hover_data={'Price': ':.2f', 'Datum': '|%Y-%m-%d %H:%M'},
    facet_col='Product',
    facet_col_wrap=1,
    height=800
)
fig_fcr.update_yaxes(matches=None)
st.plotly_chart(fig_fcr, use_container_width=True)

# mFRR Price Visualization
st.header('mFRR Prices')
mfrr_price_cols = ['mFRR Upp Pris (EUR/MW)', 'mFRR Ned Pris (EUR/MW)']
mfrr_price_df = mfrr_df[['Period'] + mfrr_price_cols].copy()
mfrr_price_df = mfrr_price_df.melt(
    id_vars=['Period'], 
    value_vars=mfrr_price_cols,
    var_name='Product',
    value_name='Price'
)
mfrr_price_df['Product'] = mfrr_price_df['Product'].str.replace('mFRR ', '').str.replace(' Pris \(EUR/MW\)', '', regex=True)
mfrr_price_df = mfrr_price_df[(mfrr_price_df['Period'] >= start_date) & (mfrr_price_df['Period'] <= end_date)]

fig_mfrr = px.line(
    mfrr_price_df,
    x='Period',
    y='Price',
    color='Product',
    title='mFRR Prices (EUR/MW)',
    labels={'Price': 'Price (EUR/MW)', 'Period': 'Date'},
    hover_data={'Price': ':.2f', 'Period': '|%Y-%m-%d %H:%M'},
    facet_col='Product',
    facet_col_wrap=1,
    height=600
)
fig_mfrr.update_yaxes(matches=None)
st.plotly_chart(fig_mfrr, use_container_width=True)

# Price Analysis Section
st.header('Price Analysis')

# Combine all price data
all_prices = pd.concat([
    fcr_price_df.rename(columns={'Datum': 'Date', 'Product': 'Market'}),
    mfrr_price_df.rename(columns={'Period': 'Date', 'Product': 'Market'}).assign(Market=lambda x: 'mFRR ' + x['Market'])
])

# Top Price Points Table
st.subheader(f'Top Price Points')
top_n = st.slider('Number of top prices to show', 5, 50, 10, key='top_n_slider')
top_prices = all_prices.nlargest(top_n, 'Price')[['Date', 'Market', 'Price']]
st.dataframe(
    top_prices.style.format({
        'Price': '{:.2f} EUR/MW',
        'Date': lambda x: x.strftime('%Y-%m-%d %H:%M')
    }),
    height=min((top_n + 1) * 35 + 3, 500)
)

# Price Distribution Plot
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