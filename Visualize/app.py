import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# --- Page and Data Setup ---
st.set_page_config(layout="wide")
st.title("Financial Analysis Dashboard")
DATA_DIR = 'Visualize/data'

# --- Reusable Text Parsing Function ---
def format_prompt_content(prompt_text):
    """Parses the raw prompt text to extract and format news and press releases."""
    try:
        prompt_text = str(prompt_text)
        news_html, press_html = "No news available.", "No press releases available."
        news_section_match = re.search(r"\[RECENT NEWS\](.*?)\[LATEST PRESS RELEASE\]", prompt_text, re.DOTALL)
        press_section_match = re.search(r"\[LATEST PRESS RELEASE\](.*?)\[ANALYSIS TASKS?\]", prompt_text, re.DOTALL)
        
        # Process News
        if news_section_match:
            news_items = re.split(r'\[Headline\]:', news_section_match.group(1).strip())
            formatted_news = []
            for item in news_items:
                if not item.strip(): continue
                match = re.search(r"(.*?)\n\[Summary\]:(.*)", item, re.DOTALL)
                if match: formatted_news.append(f"<b>{match.group(1).strip()}:</b> {match.group(2).strip()}")
            if formatted_news: news_html = "<br><br>".join(formatted_news)
        
        # Process Press Releases
        if press_section_match:
            press_content = press_section_match.group(1)
            press_matches = re.findall(r"\[Headline\]: (.*?)\n\[Description\]: (.*?)(?=\n\[Headline\]:|\Z)", press_content, re.DOTALL)
            if press_matches:
                formatted_press = [f"<b>{title.strip()}:</b> {desc.strip()}" for title, desc in press_matches]
                press_html = '<br><br>'.join(formatted_press)
        
        return news_html, press_html
    except Exception:
        return "Error parsing content.", "Error parsing content."

# --- Main App Logic ---
try:
    # --- Data Loading and Filtering ---
    stock_files = ["AAPL_data.csv", "AMZN_data.csv", "CRM_data.csv", "MSFT_data.csv", "NFLX_data.csv"]
    
    # CORRECTED DATA LOADING: Assign the ticker symbol as each file is read.
    df_all = pd.concat([
        pd.read_csv(f"{DATA_DIR}/{file}").assign(ticker=file.split('_')[0]) 
        for file in stock_files
    ])
    
    df_all['Date'] = pd.to_datetime(df_all['Date'])

    st.sidebar.title("Filters")
    ticker_option = st.sidebar.selectbox("Select Ticker", df_all['ticker'].unique())
    min_date, max_date = df_all['Date'].min().date(), df_all['Date'].max().date()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(date_range) != 2: st.stop()
    
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_filtered = df_all[(df_all['ticker'] == ticker_option) & (df_all['Date'] >= start_date) & (df_all['Date'] <= end_date)].copy()

    if df_filtered.empty:
        st.warning("No data available for the selected ticker and date range.")
        st.stop()
        
    # --- Top Section: Chart and Details Pane ---
    col1, col2 = st.columns([2, 1.2])

    # --- Right Column (col2): Controls and Sentiment Scores ---
    with col2:
        st.subheader("🗓️ Select a Date")
        
        available_dates = sorted(df_filtered['Date'].dt.date.unique())
        selected_date_from_slider = st.select_slider(
            'Slide to choose a date to inspect:',
            options=available_dates,
            format_func=lambda date: pd.to_datetime(date).strftime('%b %d, %Y')
        )
        
        selected_date = pd.to_datetime(selected_date_from_slider)
        
        st.markdown("---")
        
        st.subheader("📊 Details for Selected Date")
        
        row_data = df_filtered[df_filtered['Date'] == selected_date].iloc[0]
        
        st.markdown(f"**Date:** {selected_date.strftime('%B %d, %Y')}")
        st.metric(label=f"Adjusted Close Price", value=f"${row_data['Adj Close Price']:.2f}")

        st.markdown("**Sentiment Analysis Scores**")
        s_col1, s_col2 = st.columns(2)
        s_col1.metric("Sentiment", f"{row_data['Sentiment']:.0f}")
        s_col2.metric("Trend Direction", f"{row_data['Trend Direction']:.0f}")
        s_col1.metric("Price Impact", f"{row_data['Price Impact Potential']:.0f}")
        s_col2.metric("Earnings Impact", f"{row_data['Earnings Impact']:.0f}")
        s_col1.metric("Investor Confidence", f"{row_data['Investor Confidence']:.0f}")
        s_col2.metric("Risk Profile", f"{row_data['Risk Profile Change']:.0f}")
        s_col1.metric("News Relevance", f"{row_data['News Relevance']:.0f}")

    # --- Left Column (col1): Price Chart ---
    with col1:
        st.subheader(f"Price Chart for {ticker_option}")
        fig_price = px.line(df_filtered, x='Date', y='Adj Close Price')
        fig_price.update_traces(line_color='#636EFA', hovertemplate='Date: %{x|%b %d, %Y}<br>Price: %{y:$.2f}')
        
        price_on_date = row_data['Adj Close Price']
        fig_price.add_vline(x=selected_date, line_width=1.5, line_dash="dash", line_color="#EF553B")
        fig_price.add_trace(go.Scatter(
            x=[selected_date], y=[price_on_date],
            mode='markers',
            marker=dict(color='#EF553B', size=10, symbol='circle'),
            name='Selected',
            showlegend=False,
        ))
        fig_price.update_layout(hovermode='x unified', height=550)
        st.plotly_chart(fig_price, use_container_width=True)

    # --- Bottom Section: News and Press Release Details ---
    st.markdown("---")
    st.header(f"News & Press Releases for {selected_date.strftime('%B %d, %Y')}")
    
    full_news, full_press = format_prompt_content(row_data['Prompt'])
    
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        with st.expander("**News Summary**", expanded=True):
            st.markdown(f'<div style="height:400px;overflow-y:scroll;padding:10px;">{full_news}</div>', unsafe_allow_html=True)
    
    with exp_col2:
        with st.expander("**Press Releases**", expanded=True):
            st.markdown(f'<div style="height:400px;overflow-y:scroll;padding:10px;">{full_press}</div>', unsafe_allow_html=True)

except (FileNotFoundError, IndexError, KeyError) as e:
    st.error(f"Data could not be loaded or processed. Please check your file paths, CSV column names, and filter selections. Error: {e}")