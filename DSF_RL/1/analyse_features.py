import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Data Loading and Preparation ---

# Define the stocks and features to be plotted (using lowercase and underscores)
tickers = ["AAPL", "NFLX", "MSFT", "CRM", "AMZN"]
features = [
    "news_relevance",
    "sentiment",
    "price_impact_potential",
    "trend_direction",
    "earnings_impact",
    "investor_confidence",
    "risk_profile_change"
]

# Define the possible values for each feature for consistent axis formatting
# Keys must match the 'features' list
feature_ranges = {
    "news_relevance": [0, 1, 2],
    "sentiment": [-1, 0, 1],
    "price_impact_potential": [-3, -2, -1, 0, 1, 2, 3],
    "trend_direction": [-1, 0, 1],
    "earnings_impact": [-2, -1, 0, 1, 2],
    "investor_confidence": [-3, -2, -1, 0, 1, 2, 3],
    "risk_profile_change": [-2, -1, 0, 1, 2]
}

# Store dataframes for each stock
data_frames = {}

# Loop through the tickers to load data
for ticker in tickers:
    # Use the specific file path provided by the user
    file_path = f'DSF_RL/1/data_gpt/{ticker}_2020-07-01_2025-05-31/{ticker}_2020-07-01_2025-05-31_gpt.csv'
    try:
        df = pd.read_csv(file_path)
        
        # Standardize column names to match the 'features' list
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
        
        data_frames[ticker] = df
        print(f"Successfully loaded and processed data for {ticker}")

    except FileNotFoundError:
        print(f"Warning: Data file not found for {ticker} at {file_path}. Plots for this stock will be empty.")
        data_frames[ticker] = pd.DataFrame()


# --- Plotting ---

# Create a 5x7 grid of subplots. Note `constrained_layout` is removed.
# The figsize is adjusted for a better fit on most screens.
fig, axes = plt.subplots(nrows=5, ncols=7, figsize=(22, 14))
fig.suptitle('Distribution of AI-Generated Stock Features', fontsize=24, weight='bold')

# Set common properties for colors
colors = plt.cm.viridis(np.linspace(0, 1, 5))

# Iterate over each stock (row) and each feature (column) to create the plots
for i, ticker in enumerate(tickers):
    for j, feature in enumerate(features):
        ax = axes[i, j]
        if ticker in data_frames:
            df = data_frames[ticker]

            if not df.empty and feature in df.columns:
                data = df[feature].value_counts().sort_index()

                bars = ax.bar(data.index, data.values, color=colors[i], alpha=0.8)

                # Add labels to the bars with a slightly smaller font
                ax.bar_label(bars, fontsize=8, padding=3)

                ax.set_xticks(feature_ranges[feature])
                ax.tick_params(axis='x', rotation=45, labelsize=9)
            else:
                ax.text(0.5, 0.5, 'Data not found', ha='center', va='center', fontsize=12, color='red')
                ax.set_xticks([])
                ax.set_yticks([])
        else:
            ax.text(0.5, 0.5, 'File not loaded', ha='center', va='center', fontsize=12, color='red')
            ax.set_xticks([])
            ax.set_yticks([])

        # Set titles for the columns (feature names) on the top row
        if i == 0:
            formatted_feature_name = feature.replace('_', ' ').title()
            ax.set_title(formatted_feature_name, fontsize=13, weight='bold')

        # Set y-labels for the rows (stock tickers) on the first column
        if j == 0:
            ax.set_ylabel(ticker, fontsize=16, weight='bold')

# *** FIX: Use fig.tight_layout() to automatically adjust subplot params ***
# The `rect` parameter reserves space: [left, bottom, right, top]
# Setting top to 0.96 reserves space for the suptitle.
fig.tight_layout(rect=[0, 0, 1, 0.96])

# Display the plot
plt.show()
