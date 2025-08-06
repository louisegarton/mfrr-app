import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Load your data
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("MFRR CM.xlsx", sheet_name="Sheet1")
        df['Period'] = pd.to_datetime(df['Period'])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

# Title
st.title('mFRR Market Data Visualization')

# Sidebar controls
st.sidebar.header('Filter Options')

# Elområde selection
selected_elomrade = st.sidebar.multiselect(
    'Select Elområde',
    options=df['Elområde'].unique(),
    default=['SN1'] if 'SN1' in df['Elområde'].unique() else []
)

# Aggregation option
aggregation = st.sidebar.radio(
    'Time Aggregation',
    options=['Hourly', 'Daily Average'],
    index=0
)

# Date range slider
if not df.empty:
    min_date = df['Period'].min().to_pydatetime()
    max_date = df['Period'].max().to_pydatetime()
    
    date_range = st.sidebar.slider(
        'Select Date Range',
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )

# Filter data based on selections
filtered_df = df.copy()

# Apply filters
if selected_elomrade:
    filtered_df = filtered_df[filtered_df['Elområde'].isin(selected_elomrade)]
    
filtered_df = filtered_df[
    (filtered_df['Period'] >= date_range[0]) & 
    (filtered_df['Period'] <= date_range[1])
]

# Apply aggregation if selected
if aggregation == 'Daily Average' and not filtered_df.empty:
    filtered_df['Date'] = filtered_df['Period'].dt.date
    aggregated_df = filtered_df.groupby(['Date', 'Elområde']).agg({
        'mFRR Upp Pris (EUR/MW)': 'mean',
        'mFRR Upp Volym (MW)': 'mean',
        'mFRR Ned Pris (EUR/MW)': 'mean',
        'mFRR Ned Volym (MW)': 'mean'
    }).reset_index()
    aggregated_df['Period'] = pd.to_datetime(aggregated_df['Date'])
    filtered_df = aggregated_df

# Plotting
if not filtered_df.empty:
    st.header('Price Visualization')
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot each selected Elområde
    for elomrade in selected_elomrade:
        subset = filtered_df[filtered_df['Elområde'] == elomrade]
        ax.plot(subset['Period'], subset['mFRR Upp Pris (EUR/MW)'], 
                label=f'{elomrade} - Up Price')
        ax.plot(subset['Period'], subset['mFRR Ned Pris (EUR/MW)'], 
                linestyle='--', label=f'{elomrade} - Down Price')
    
    # Formatting
    ax.set_xlabel('Period')
    ax.set_ylabel('Price (EUR/MW)')
    ax.set_title('mFRR Up and Down Prices')
    ax.legend()
    
    if aggregation == 'Daily Average':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    
    # Volume visualization
    st.header('Volume Visualization')
    
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    
    for elomrade in selected_elomrade:
        subset = filtered_df[filtered_df['Elområde'] == elomrade]
        ax2.plot(subset['Period'], subset['mFRR Upp Volym (MW)'], 
                label=f'{elomrade} - Up Volume')
        ax2.plot(subset['Period'], subset['mFRR Ned Volym (MW)'], 
                linestyle='--', label=f'{elomrade} - Down Volume')
    
    ax2.set_xlabel('Period')
    ax2.set_ylabel('Volume (MW)')
    ax2.set_title('mFRR Up and Down Volumes')
    ax2.legend()
    
    if aggregation == 'Daily Average':
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    else:
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig2)

    # Show top 5 highest price points
    st.header('Top 5 Highest Price Points')
    
    # Combine up and down prices for analysis
    top_prices = filtered_df.melt(
        id_vars=['Period', 'Elområde'],
        value_vars=['mFRR Upp Pris (EUR/MW)', 'mFRR Ned Pris (EUR/MW)'],
        var_name='Price Type',
        value_name='Price'
    )
    
    # Get top 5 highest prices
    top_5 = top_prices.nlargest(5, 'Price')
    
    # Format for display
    display_df = top_5[[
        'Period', 'Elområde', 'Price Type', 'Price'
    ]].copy()
    display_df['Price Type'] = display_df['Price Type'].str.replace(
        'mFRR ', '').str.replace(' Pris (EUR/MW)', '')
    
    st.dataframe(display_df.style.format({
        'Price': '{:.2f} EUR/MW'
    }))
    
else:
    st.warning("No data available for the selected filters.")