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

# Sidebar controls
st.sidebar.header('Filter Options')

# Date range selection
min_date = min(mfrr_df['Period'].min(), fcr_df['Datum'].min()).to_pydatetime()
max_date = max(mfrr_df['Period'].max(), fcr_df['Datum'].max()).to_pydatetime()

date_range = st.sidebar.slider(
    'Select Date Range',
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

# Data processing
def prepare_fcr_data(df):
    # Price data
    price_cols = [col for col in df.columns if 'Pris' in col]
    price_df = df.melt(
        id_vars=['Datum'],
        value_vars=price_cols,
        var_name='Product',
        value_name='Price'
    )
    
    # Volume data
    volume_cols = [col for col in df.columns if 'Pris' not in col and col != 'Datum' and 'Total' not in col]
    volume_df = df.melt(
        id_vars=['Datum'],
        value_vars=volume_cols,
        var_name='Product_Region',
        value_name='Volume'
    )
    
    # Clean product names
    price_df['Product'] = price_df['Product'].str.replace(' Pris \(EUR/MW\)', '', regex=True)
    volume_df['Product'] = volume_df['Product_Region'].str.extract(r'(FCR[-\w]+)')[0]
    volume_df['Region'] = volume_df['Product_Region'].str.extract(r'(SE[1-4]|DK2)')[0]
    
    return price_df, volume_df

fcr_price_df, fcr_volume_df = prepare_fcr_data(fcr_df)

# Filter by date
fcr_price_df = fcr_price_df[(fcr_price_df['Datum'] >= date_range[0]) & 
                          (fcr_price_df['Datum'] <= date_range[1])]
fcr_volume_df = fcr_volume_df[(fcr_volume_df['Datum'] >= date_range[0]) & 
                            (fcr_volume_df['Datum'] <= date_range[1])]

# Combined Price Visualization
st.header('Combined Price Visualization')

fig_price = px.line(
    fcr_price_df,
    x='Datum',
    y='Price',
    color='Product',
    title='FCR Prices (EUR/MW)',
    labels={'Price': 'Price (EUR/MW)', 'Datum': 'Date'},
    hover_data={'Price': ':.2f', 'Datum': '|%Y-%m-%d %H:%M'},
)

# Add MFRR data if available
if not mfrr_df.empty:
    mfrr_price_df = mfrr_df.melt(
        id_vars=['Period'],
        value_vars=['mFRR Upp Pris (EUR/MW)', 'mFRR Ned Pris (EUR/MW)'],
        var_name='Product',
        value_name='Price'
    )
    mfrr_price_df['Product'] = mfrr_price_df['Product'].str.replace('mFRR ', '').str.replace(' Pris (EUR/MW)', '')
    
    for product in mfrr_price_df['Product'].unique():
        product_df = mfrr_price_df[mfrr_price_df['Product'] == product]
        fig_price.add_scatter(
            x=product_df['Period'],
            y=product_df['Price'],
            name=f'mFRR {product}',
            line=dict(dash='dot' if 'Ned' in product else 'solid'),
            hovertemplate="<br>".join([
                "Product: mFRR %{customdata[0]}",
                "Date: %{x|%Y-%m-%d %H:%M}",
                "Price: %{y:.2f} EUR/MW"
            ])
        )

fig_price.update_layout(hovermode='x unified')
st.plotly_chart(fig_price, use_container_width=True)

# Volume Visualization
st.header('Volume Visualization')

product_selection = st.selectbox(
    'Select Product',
    options=['FCR-N', 'FCR-D upp', 'FCR-D ned', 'mFRR Upp', 'mFRR Ned'],
    index=0
)

if 'FCR' in product_selection:
    product_filter = product_selection.replace('FCR-', 'FCR')
    filtered_volumes = fcr_volume_df[fcr_volume_df['Product'] == product_filter]
    
    fig_vol = px.area(
        filtered_volumes,
        x='Datum',
        y='Volume',
        color='Region',
        title=f'{product_selection} Volumes (MW)',
        labels={'Volume': 'Volume (MW)', 'Datum': 'Date'},
        hover_data={'Volume': ':.2f', 'Datum': '|%Y-%m-%d %H:%M'},
    )
else:
    # mFRR volumes
    filtered_mfrr = mfrr_df.melt(
        id_vars=['Period', 'Elområde'],
        value_vars=['mFRR Upp Volym (MW)', 'mFRR Ned Volym (MW)'],
        var_name='Product',
        value_name='Volume'
    )
    filtered_mfrr = filtered_mfrr[filtered_mfrr['Product'].str.contains(product_selection)]
    
    fig_vol = px.area(
        filtered_mfrr,
        x='Period',
        y='Volume',
        color='Elområde',
        title=f'{product_selection} Volumes (MW)',
        labels={'Volume': 'Volume (MW)', 'Period': 'Date'},
        hover_data={'Volume': ':.2f', 'Period': '|%Y-%m-%d %H:%M'},
    )

st.plotly_chart(fig_vol, use_container_width=True)

# Top Price Points
st.header('Top Price Points')

top_n = st.slider('Number of top prices to show', 5, 20, 10)

# Combine all price data
all_prices = pd.concat([
    fcr_price_df.rename(columns={'Datum': 'Date', 'Product': 'Market'}),
    mfrr_price_df.rename(columns={'Period': 'Date', 'Product': 'Market'}).assign(Market=lambda x: 'mFRR ' + x['Market'])
])

top_prices = all_prices.nlargest(top_n, 'Price')[['Date', 'Market', 'Price']]
st.dataframe(
    top_prices.style.format({
        'Price': '{:.2f} EUR/MW',
        'Date': lambda x: x.strftime('%Y-%m-%d %H:%M')
    }),
    height=(top_n + 1) * 35 + 3
)