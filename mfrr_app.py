import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Cache data with optimized loading
@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    try:
        mfrr_df = pd.read_excel("MFRR CM.xlsx", sheet_name="Sheet1", 
                              usecols=['Period', 'mFRR Upp Pris (EUR/MW)', 'mFRR Ned Pris (EUR/MW)'])
        mfrr_df['Period'] = pd.to_datetime(mfrr_df['Period'])
        
        fcr_df = pd.read_excel("FCR Dashboard.xlsx", sheet_name="data 2021-2023",
                              usecols=['Datum', 'FCR-N Pris (EUR/MW)', 'FCR-D upp Pris (EUR/MW)', 
                                      'FCR-D ned Pris (EUR/MW)'])
        fcr_df['Datum'] = pd.to_datetime(fcr_df['Datum'])
        
        return mfrr_df, fcr_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Load only needed columns
mfrr_df, fcr_df = load_data()

# Title with loading indicator
with st.spinner('Preparing dashboard...'):
    st.title('Energy Market Dashboard')

    # Get date range
    min_date = min(mfrr_df['Period'].min(), fcr_df['Datum'].min())
    max_date = max(mfrr_df['Period'].max(), fcr_df['Datum'].max())

    # Date selection with default 30-day window
    default_end = max_date
    default_start = max(min_date, default_end - pd.Timedelta(days=30))
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=default_start, 
                                 min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("End date", value=default_end,
                               min_value=min_date, max_value=max_date)

    # Convert to datetime once
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.min.time())

    # Filter data efficiently
    def filter_dates(df, date_col):
        mask = (df[date_col] >= start_dt) & (df[date_col] <= end_dt)
        return df.loc[mask].copy()

    mfrr_filt = filter_dates(mfrr_df, 'Period')
    fcr_filt = filter_dates(fcr_df, 'Datum')

    # FCR Price Visualization
    st.header('FCR Prices')
    
    # Create FCR plot with direct data access (no melt)
    fig_fcr = go.Figure()
    
    # Stack FCR-D up and down
    fig_fcr.add_trace(go.Scatter(
        x=fcr_filt['Datum'],
        y=fcr_filt['FCR-D upp Pris (EUR/MW)'],
        name='FCR-D Up',
        stackgroup='one',
        mode='lines',
        line=dict(width=0.5, color='blue')
    ))
    
    fig_fcr.add_trace(go.Scatter(
        x=fcr_filt['Datum'],
        y=fcr_filt['FCR-D ned Pris (EUR/MW)'],
        name='FCR-D Down',
        stackgroup='one',
        mode='lines',
        line=dict(width=0.5, color='lightblue')
    ))
    
    # Add FCR-N line
    fig_fcr.add_trace(go.Scatter(
        x=fcr_filt['Datum'],
        y=fcr_filt['FCR-N Pris (EUR/MW)'],
        name='FCR-N',
        mode='lines',
        line=dict(color='red', width=2)
    ))
    
    fig_fcr.update_layout(
        yaxis_title='Price (EUR/MW)',
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_fcr, use_container_width=True, use_browser=True)

    # mFRR Price Visualization
    st.header('mFRR Prices')
    
    # Create mFRR plot with direct data access
    fig_mfrr = go.Figure()
    
    fig_mfrr.add_trace(go.Scatter(
        x=mfrr_filt['Period'],
        y=mfrr_filt['mFRR Upp Pris (EUR/MW)'],
        name='mFRR Up',
        mode='lines',
        line=dict(color='green', width=1.5)
    ))
    
    fig_mfrr.add_trace(go.Scatter(
        x=mfrr_filt['Period'],
        y=mfrr_filt['mFRR Ned Pris (EUR/MW)'],
        name='mFRR Down',
        mode='lines',
        line=dict(color='orange', width=1.5)
    ))
    
    fig_mfrr.update_layout(
        yaxis_title='Price (EUR/MW)',
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_mfrr, use_container_width=True, use_browser=True)

    # Price Analysis Section
    st.header('Price Analysis')
    
    # Prepare combined data more efficiently
    fcr_prices = fcr_filt[['Datum', 'FCR-N Pris (EUR/MW)', 
                          'FCR-D upp Pris (EUR/MW)', 'FCR-D ned Pris (EUR/MW)']]
    mfrr_prices = mfrr_filt[['Period', 'mFRR Upp Pris (EUR/MW)', 
                            'mFRR Ned Pris (EUR/MW)']]
    
    # Create top prices table without full melt
    top_n = st.slider('Number of top prices to show', 5, 50, 10)
    
    # Find top prices for each product
    top_dfs = []
    for col, product in [
        ('FCR-N Pris (EUR/MW)', 'FCR-N'),
        ('FCR-D upp Pris (EUR/MW)', 'FCR-D Up'), 
        ('FCR-D ned Pris (EUR/MW)', 'FCR-D Down'),
        ('mFRR Upp Pris (EUR/MW)', 'mFRR Up'),
        ('mFRR Ned Pris (EUR/MW)', 'mFRR Down')
    ]:
        if col in fcr_prices.columns:
            temp_df = fcr_prices[['Datum', col]].copy()
            date_col = 'Datum'
        else:
            temp_df = mfrr_prices[['Period', col]].copy()
            date_col = 'Period'
        
        temp_df.columns = ['Date', 'Price']
        temp_df['Market'] = product
        top_dfs.append(temp_df.nlargest(top_n, 'Price'))
    
    top_prices = pd.concat(top_dfs).nlargest(top_n, 'Price')
    
    st.subheader(f'Top {top_n} Price Points')
    st.dataframe(
        top_prices.style.format({
            'Price': '{:.2f} EUR/MW',
            'Date': lambda x: x.strftime('%Y-%m-%d %H:%M')
        }),
        height=min((top_n + 1) * 35 + 3, 500)
    )
    
    # Price Distribution (simplified)
    st.subheader('Price Distribution')
    dist_fig = go.Figure()
    
    for col, product, color in [
        ('FCR-N Pris (EUR/MW)', 'FCR-N', 'red'),
        ('FCR-D upp Pris (EUR/MW)', 'FCR-D Up', 'blue'),
        ('FCR-D ned Pris (EUR/MW)', 'FCR-D Down', 'lightblue'),
        ('mFRR Upp Pris (EUR/MW)', 'mFRR Up', 'green'),
        ('mFRR Ned Pris (EUR/MW)', 'mFRR Down', 'orange')
    ]:
        if col in fcr_prices.columns:
            dist_fig.add_trace(go.Box(
                y=fcr_prices[col],
                name=product,
                marker_color=color,
                boxpoints=False
            ))
        elif col in mfrr_prices.columns:
            dist_fig.add_trace(go.Box(
                y=mfrr_prices[col],
                name=product,
                marker_color=color,
                boxpoints=False
            ))
    
    dist_fig.update_layout(
        yaxis_title='Price (EUR/MW)',
        height=500,
        showlegend=True
    )
    
    st.plotly_chart(dist_fig, use_container_width=True, use_browser=True)