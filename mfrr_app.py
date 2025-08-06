import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Load your data
@st.cache_data  # This decorator caches the data to avoid reloading on every interaction
def load_data():
    # Adjust the path if your file is in a different location
    df = pd.read_excel('MFRR CM.xlsx', sheet_name='Sheet1')
    
    # Convert 'Period' to datetime if it's not already
    df['Period'] = pd.to_datetime(df['Period'])
    
    # Convert 'Publiceringstidpunkt' to datetime if needed
    if 'Publiceringstidpunkt' in df.columns:
        df['Publiceringstidpunkt'] = pd.to_datetime(df['Publiceringstidpunkt'])
    
    return df

df = load_data()

# Title
st.title('mFRR Market Data Visualization')

# Sidebar controls
st.sidebar.header('Filter Options')

# Elområde selection
selected_elomrade = st.sidebar.multiselect(
    'Select Elområde',
    options=df['Elområde'].unique(),
    default=['SN1']  # Default selection
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

# Apply Elområde filter
if selected_elomrade:
    filtered_df = filtered_df[filtered_df['Elområde'].isin(selected_elomrade)]

# Apply date range filter
filtered_df = filtered_df[
    (filtered_df['Period'] >= date_range[0]) & 
    (filtered_df['Period'] <= date_range[1])
]

# Apply aggregation if selected
if aggregation == 'Daily Average' and not filtered_df.empty:
    # Create a date column without time for grouping
    filtered_df['Date'] = filtered_df['Period'].dt.date
    
    # Group by Date and Elområde, calculate mean
    aggregated_df = filtered_df.groupby(['Date', 'Elområde']).agg({
        'mFRR Upp Pris (EUR/MW)': 'mean',
        'mFRR Upp Volym (MW)': 'mean',
        'mFRR Ned Pris (EUR/MW)': 'mean',
        'mFRR Ned Volym (MW)': 'mean'
    }).reset_index()
    
    # Convert back to datetime for plotting
    aggregated_df['Period'] = pd.to_datetime(aggregated_df['Date'])
    filtered_df = aggregated_df

# Display filtered data
st.write(f"Displaying {len(filtered_df)} records")
st.dataframe(filtered_df.head())

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
    
    # Format x-axis based on time range
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
else:
    st.warning("No data available for the selected filters.")