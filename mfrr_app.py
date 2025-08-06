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
    format="YYYY-MM-%d"
)

# Product selection for price visualization
st.sidebar.header('Price Display Options')
price_products = {
    'FCR-N': True,
    'FCR-D Up': True,
    'FCR-D Down': True,
    'mFRR Up': True,
    'mFRR Down': True
}

for product in price_products:
    price_products[product] = st.sidebar.checkbox(
        f"Show {product}",
        value=True,
        key=f"price_{product}"
    )

# Price range filter
min_price, max_price = st.sidebar.slider(
    'Filter Price Range (EUR/MW)',
    min_value=0,
    max_value=500,  # Adjust based on your data range
    value=(0, 500),
    step=5
)

# Data processing
def prepare_fcr_data(df):
    # Price data
    price_mapping = {
        'FCR-N Pris (EUR/MW)': 'FCR-N',
        'FCR-D upp Pris (EUR/MW)': 'FCR-D Up',
        'FCR-D ned Pris (EUR/MW)': 'FCR-D Down'
    }
    
    price_df = pd.DataFrame()
    for col, product in price_mapping.items():
        if col in df.columns:
            temp_df = df[['Datum', col]].copy()
            temp_df.columns = ['Datum', 'Price']
            temp_df['Product'] = product
            price_df = pd.concat([price_df, temp_df])
    
    # Volume data
    volume_mapping = {
        'SE1 FCRN': 'FCR-N',
        'SE2 FCRN': 'FCR-N',
        'SE3 FCRN': 'FCR-N',
        'SE4 FCRN': 'FCR-N',
        'DK2 FCRN': 'FCR-N',
        'SE1 FCRD upp': 'FCR-D Up',
        'SE2 FCRD upp': 'FCR-D Up',
        'SE3 FCRD upp': 'FCR-D Up',
        'SE4 FCRD upp': 'FCR-D Up',
        'DK2 FCRD upp': 'FCR-D Up',
        'SE1 FCRD ned': 'FCR-D Down',
        'SE2 FCRD ned': 'FCR-D Down',
        'SE3 FCRD ned': 'FCR-D Down',
        'SE4 FCRD ned': 'FCR-D Down',
        'DK2 FCRD ned': 'FCR-D Down'
    }
    
    volume_df = pd.DataFrame()
    for col, product in volume_mapping.items():
        if col in df.columns:
            temp_df = df[['Datum', col]].copy()
            temp_df.columns = ['Datum', 'Volume']
            temp_df['Product'] = product
            temp_df['Region'] = col.split()[0]
            volume_df = pd.concat([volume_df, temp_df])
    
    return price_df, volume_df

fcr_price_df, fcr_volume_df = prepare_fcr_data(fcr_df)

# Filter by date and price range
fcr_price_df = fcr_price_df[
    (fcr_price_df['Datum'] >= date_range[0]) & 
    (fcr_price_df['Datum'] <= date_range[1]) &
    (fcr_price_df['Price'] >= min_price) &
    (fcr_price_df['Price'] <= max_price)
]

fcr_volume_df = fcr_volume_df[
    (fcr_volume_df['Datum'] >= date_range[0]) & 
    (fcr_volume_df['Datum'] <= date_range[1])
]

# Combined Price Visualization
st.header('Combined Price Visualization')

# Filter products based on selection
selected_price_products = [k for k, v in price_products.items() if v]
filtered_price_df = fcr_price_df[fcr_price_df['Product'].isin(selected_price_products)]

fig_price = px.line(
    filtered_price_df,
    x='Datum',
    y='Price',
    color='Product',
    title='Market Prices (EUR/MW)',
    labels={'Price': 'Price (EUR/MW)', 'Datum': 'Date'},
    hover_data={'Price': ':.2f', 'Datum': '|%Y-%m-%d %H:%M'},
)

# Add mFRR data if selected and available
if not mfrr_df.empty:
    mfrr_price_mapping = {
        'mFRR Upp Pris (EUR/MW)': 'mFRR Up',
        'mFRR Ned Pris (EUR/MW)': 'mFRR Down'
    }
    
    for col, product in mfrr_price_mapping.items():
        if price_products[product] and col in mfrr_df.columns:
            temp_df = mfrr_df[['Period', col]].copy()
            temp_df.columns = ['Datum', 'Price']
            temp_df['Product'] = product
            temp_df = temp_df[
                (temp_df['Datum'] >= date_range[0]) & 
                (temp_df['Datum'] <= date_range[1]) &
                (temp_df['Price'] >= min_price) &
                (temp_df['Price'] <= max_price)
            ]
            
            fig_price.add_scatter(
                x=temp_df['Datum'],
                y=temp_df['Price'],
                name=product,
                line=dict(dash='dot' if 'Down' in product else 'solid'),
                hovertemplate="<br>".join([
                    "Product: %{customdata[0]}",
                    "Date: %{x|%Y-%m-%d %H:%M}",
                    "Price: %{y:.2f} EUR/MW"
                ])
            )

fig_price.update_layout(
    hovermode='x unified',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)
st.plotly_chart(fig_price, use_container_width=True)

# Volume Visualization
st.header('Volume Visualization')

product_selection = st.selectbox(
    'Select Product for Volume View',
    options=['FCR-N', 'FCR-D Up', 'FCR-D Down', 'mFRR Up', 'mFRR Down'],
    index=0
)

if 'FCR' in product_selection:
    filtered_volumes = fcr_volume_df[fcr_volume_df['Product'] == product_selection]
    
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
    mfrr_vol_col = f'mFRR {"Upp" if "Up" in product_selection else "Ned"} Volym (MW)'
    if mfrr_vol_col in mfrr_df.columns:
        filtered_mfrr = mfrr_df[['Period', 'Elområde', mfrr_vol_col]].copy()
        filtered_mfrr.columns = ['Datum', 'Elområde', 'Volume']
        filtered_mfrr = filtered_mfrr[
            (filtered_mfrr['Datum'] >= date_range[0]) & 
            (filtered_mfrr['Datum'] <= date_range[1])
        ]
        
        fig_vol = px.area(
            filtered_mfrr,
            x='Datum',
            y='Volume',
            color='Elområde',
            title=f'{product_selection} Volumes (MW)',
            labels={'Volume': 'Volume (MW)', 'Datum': 'Date'},
            hover_data={'Volume': ':.2f', 'Datum': '|%Y-%m-%d %H:%M'},
        )

st.plotly_chart(fig_vol, use_container_width=True)

# Enhanced Top Price Points
st.header('Price Analysis')

col1, col2 = st.columns(2)
with col1:
    top_n = st.slider('Number of top prices to show', 5, 50, 10)
with col2:
    product_filter = st.multiselect(
        'Filter by product',
        options=['FCR-N', 'FCR-D Up', 'FCR-D Down', 'mFRR Up', 'mFRR Down'],
        default=['FCR-N', 'FCR-D Up', 'FCR-D Down', 'mFRR Up', 'mFRR Down']
    )

# Combine all price data
all_prices = pd.concat([
    fcr_price_df.rename(columns={'Datum': 'Date', 'Product': 'Market'}),
    mfrr_df[['Period', 'mFRR Upp Pris (EUR/MW)']].rename(columns={'Period': 'Date', 'mFRR Upp Pris (EUR/MW)': 'Price'}).assign(Market='mFRR Up'),
    mfrr_df[['Period', 'mFRR Ned Pris (EUR/MW)']].rename(columns={'Period': 'Date', 'mFRR Ned Pris (EUR/MW)': 'Price'}).assign(Market='mFRR Down')
])

# Apply product filter
if product_filter:
    all_prices = all_prices[all_prices['Market'].isin(product_filter)]

top_prices = all_prices.nlargest(top_n, 'Price')[['Date', 'Market', 'Price']]

# Add price distribution
col1, col2 = st.columns(2)
with col1:
    st.subheader(f'Top {top_n} Price Points')
    st.dataframe(
        top_prices.style.format({
            'Price': '{:.2f} EUR/MW',
            'Date': lambda x: x.strftime('%Y-%m-%d %H:%M')
        }),
        height=min((top_n + 1) * 35 + 3, 500)
    )

with col2:
    st.subheader('Price Distribution')
    fig_dist = px.box(
        all_prices,
        x='Market',
        y='Price',
        color='Market',
        points="all",
        hover_data=['Date'],
        labels={'Price': 'Price (EUR/MW)', 'Market': 'Product'}
    )
    st.plotly_chart(fig_dist, use_container_width=True)