import streamlit as st
import pandas as pd
import plotly.express as px
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

# Plotting with Plotly
if not filtered_df.empty:
    st.header('Price Visualization')
    
    # Create a melted dataframe for Plotly
    price_df = filtered_df.melt(
        id_vars=['Period', 'Elområde'],
        value_vars=['mFRR Upp Pris (EUR/MW)', 'mFRR Ned Pris (EUR/MW)'],
        var_name='Price Type',
        value_name='Price'
    )
    
    # Clean up price type names
    price_df['Price Type'] = price_df['Price Type'].str.replace('mFRR ', '').str.replace(' Pris (EUR/MW)', '')
    
    # Create interactive plot
    fig = px.line(
        price_df,
        x='Period',
        y='Price',
        color='Elområde',
        line_dash='Price Type',
        title='mFRR Up and Down Prices',
        labels={'Price': 'Price (EUR/MW)', 'Period': 'Date'},
        hover_data={'Price': ':.2f', 'Period': '|%Y-%m-%d %H:%M'},
    )
    
    # Improve hover template
    fig.update_traces(
        hovertemplate="<br>".join([
            "Elområde: %{customdata[0]}",
            "Date: %{x|%Y-%m-%d %H:%M}",
            "Price: %{y:.2f} EUR/MW",
            "Type: %{customdata[1]}"
        ])
    )
    
    # Show the plot
    st.plotly_chart(fig, use_container_width=True)
    
    # Volume visualization
    st.header('Volume Visualization')
    
    # Create a melted dataframe for volumes
    volume_df = filtered_df.melt(
        id_vars=['Period', 'Elområde'],
        value_vars=['mFRR Upp Volym (MW)', 'mFRR Ned Volym (MW)'],
        var_name='Volume Type',
        value_name='Volume'
    )
    
    # Clean up volume type names
    volume_df['Volume Type'] = volume_df['Volume Type'].str.replace('mFRR ', '').str.replace(' Volym (MW)', '')
    
    # Create interactive plot
    fig2 = px.line(
        volume_df,
        x='Period',
        y='Volume',
        color='Elområde',
        line_dash='Volume Type',
        title='mFRR Up and Down Volumes',
        labels={'Volume': 'Volume (MW)', 'Period': 'Date'},
        hover_data={'Volume': ':.2f', 'Period': '|%Y-%m-%d %H:%M'},
    )
    
    # Improve hover template
    fig2.update_traces(
        hovertemplate="<br>".join([
            "Elområde: %{customdata[0]}",
            "Date: %{x|%Y-%m-%d %H:%M}",
            "Volume: %{y:.2f} MW",
            "Type: %{customdata[1]}"
        ])
    )
    
    # Show the plot
    st.plotly_chart(fig2, use_container_width=True)

    # Show top 5 highest price points
    st.header('Top 5 Highest Price Points')
    
    # Get top 5 highest prices
    top_5 = price_df.nlargest(5, 'Price')
    
    # Format for display
    display_df = top_5[[
        'Period', 'Elområde', 'Price Type', 'Price'
    ]].copy()
    
    st.dataframe(display_df.style.format({
        'Price': '{:.2f} EUR/MW',
        'Period': lambda x: x.strftime('%Y-%m-%d %H:%M')
    }))
    
else:
    st.warning("No data available for the selected filters.")