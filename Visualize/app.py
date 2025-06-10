import streamlit as st
import pandas as pd
import plotly.express as px
import re

DATA_DIR = 'Visualize/data'

st.title("Dashboard is Live")

# Load data
st.write("Files in this folder:")
st.write("data")

# Portfolio Comparison (moved to top)
st.subheader("Portfolio Performance Comparison")
df_ppo = pd.read_pickle(DATA_DIR + "/rl_df_account_value_ppo.pkl")
df_dji = pd.read_pickle(DATA_DIR + "/rl_dji.pkl")
df_mvp = pd.read_pickle(DATA_DIR + "/rl_mean_var.pkl")

df_ppo['date'] = pd.to_datetime(df_ppo['date'])
df_dji = df_dji.rename_axis('date').reset_index()
df_mvp = df_mvp.rename_axis('date').reset_index()

fig2 = px.line()
fig2.add_scatter(x=df_ppo['date'], y=df_ppo['account_value'], mode='lines', name='PPO Portfolio')
fig2.add_scatter(x=df_dji['date'], y=df_dji['close'], mode='lines', name='DJI (Buy & Hold)')
fig2.add_scatter(x=df_mvp['date'], y=df_mvp['Mean Var'], mode='lines', name='Mean-Variance')
fig2.update_layout(title="Cumulative Portfolio Account Value", xaxis_title="Date", yaxis_title="Account Value ($)")
st.plotly_chart(fig2, use_container_width=True)

# Merge all stock-level CSVs
stock_files = ["AAPL_data.csv", "AMZN_data.csv", "CRM_data.csv", "MSFT_data.csv", "NFLX_data.csv"]
df_all = pd.concat([pd.read_csv(f"{DATA_DIR}/{file}").assign(ticker=file[:file.index('_')]) for file in stock_files])
df_all['Date'] = pd.to_datetime(df_all['Date'])

# Sidebar filters
st.sidebar.title("Filters")
ticker_option = st.sidebar.selectbox("Select Ticker", df_all['ticker'].unique())
date_range = st.sidebar.date_input("Select Date Range", [df_all['Date'].min(), df_all['Date'].max()])

# Filtered data
df_filtered = df_all[(df_all['ticker'] == ticker_option) &
                     (df_all['Date'] >= pd.to_datetime(date_range[0])) &
                     (df_all['Date'] <= pd.to_datetime(date_range[1]))]

# Process prompt

def extract_prompt_sections(prompt_text):
    try:
        news_matches = re.findall(r"\[Headline\]: (.*?)\n\[Summary\]: (.*?)(?=\n\[Headline\]:|\n\[LATEST PRESS RELEASE\]|\Z)", prompt_text, re.DOTALL)
        news = '\n'.join([f"- {title.strip()}: {summary.strip()}" for title, summary in news_matches]) if news_matches else "No news"

        press_section = re.search(r"\[LATEST PRESS RELEASE\].*?:\s*(.*?)\s*\[ANALYSIS TASKS?\]", prompt_text, re.DOTALL)
        press = press_section.group(1).strip() if press_section else "No press release"

        return news, press
    except Exception:
        return "No news", "No press release"

df_filtered[['News Summary', 'Press Release']] = df_filtered['Prompt'].apply(
    lambda x: pd.Series(extract_prompt_sections(str(x)))
)

# Line plot of Adjusted Close Price with news and press release in tooltip
fig = px.line(df_filtered, x='Date', y='Adj Close Price',
              hover_data={
                  'Sentiment': True,
                  'Trend Direction': True,
                  'Price Impact Potential': True,
                  'Earnings Impact': True,
                  'Investor Confidence': True,
                  'Risk Profile Change': True,
                  'News Summary': True,
                  'Press Release': True
              },
              title=f"Adjusted Close Price and Sentiment for {ticker_option}")
st.plotly_chart(fig, use_container_width=True)

st.caption("Powered by Data Science in Finance")