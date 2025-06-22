import os
import requests
import math
import time
import json
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from datetime import time as dt_time
from collections import defaultdict
from dotenv import load_dotenv
from tqdm import tqdm

# --- Environment Setup ---
load_dotenv()
FMP_API_KEY = os.environ.get("FMP_API_KEY")
# Using the base URL as you provided, endpoint paths will be specified in each function.
FMP_BASE_URL = "https://financialmodelingprep.com"

# --- Helper Functions ---

def bin_mapping(ret):
    """Maps stock returns to a categorical bin label (e.g., 'U3', 'D5+')."""
    up_down = 'U' if ret >= 0 else 'D'
    integer = math.ceil(abs(100 * ret))
    return up_down + (str(integer) if integer <= 5 else '5+')

def get_returns(stock_symbol, start_date, end_date):
    """
    Downloads historical stock data from Yahoo Finance and calculates daily returns.
    The end_date is now treated as inclusive.
    """
    # CORRECTED: Add one day to the end_date to make yfinance's range inclusive.
    end_date_inclusive = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    stock_data = yf.download(stock_symbol, start=start_date, end=end_date_inclusive, auto_adjust=False)
    
    if isinstance(stock_data.columns, pd.MultiIndex):
        stock_data.columns = [col[0] for col in stock_data.columns]
    returns = stock_data['Adj Close'].pct_change()
    data = pd.DataFrame({
        'Date': stock_data.index.strftime('%Y-%m-%d').tolist(),
        'Adj Close Price': stock_data['Adj Close'].values.flatten(),
        'Returns': returns.values.flatten()
    }).dropna()
    data['Bin Label'] = data['Returns'].apply(bin_mapping)
    return data

def fetch_paginated_news_data(endpoint_url, start_date, end_date):
    """
    A specific function to fetch NEWS data from a paginated FMP endpoint by breaking the
    request into yearly chunks to avoid the 100-page API limit.
    """
    all_items = []
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    current_start_dt = start_dt
    while current_start_dt <= end_dt:
        chunk_end_dt = datetime(current_start_dt.year, 12, 31)
        if chunk_end_dt > end_dt:
            chunk_end_dt = end_dt

        start_chunk_str = current_start_dt.strftime('%Y-%m-%d')
        end_chunk_str = chunk_end_dt.strftime('%Y-%m-%d')
        
        print(f"Fetching FMP NEWS data from {start_chunk_str} to {end_chunk_str}...")

        page = 0
        MAX_PAGES = 100
        while page < MAX_PAGES:
            # Construct URL with chunk dates, pagination, and max limit.
            url = f"{endpoint_url}&from={start_chunk_str}&to={end_chunk_str}&page={page}&limit=250"
            if page == MAX_PAGES -1: # Corrected page check logic
                print(f"Approaching Max Pages for {url}")
            # time.sleep(0.25)  # Rate limiting
            
            try:
                response = requests.get(url)
                response.raise_for_status()
                batch = response.json()
                # print(batch)
                if not batch:
                    break
                all_items.extend(batch)
                page += 1
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data on page {page} for chunk {start_chunk_str}-{end_chunk_str}: {e}")
                break
        
        current_start_dt = datetime(current_start_dt.year + 1, 1, 1)
        
    return all_items

def get_news(symbol, data, start_date, end_date):
    """Fetches all stock news using the yearly chunking strategy."""
    print("--- Starting News Fetch from FMP ---")
    endpoint_url = f"{FMP_BASE_URL}/stable/news/stock?symbols={symbol}&apikey={FMP_API_KEY}"
    all_news_items = fetch_paginated_news_data(endpoint_url, start_date, end_date)

    news_by_calendar_day = defaultdict(list)
    for n in all_news_items:
        try:
            news_date = datetime.strptime(n['publishedDate'], '%Y-%m-%d %H:%M:%S')
            news_by_calendar_day[news_date.date()].append({
                "datetime": news_date, "headline": n.get('title', 'No Title'),
                "summary": n.get('text', 'No Summary'), "source": n.get('publisher', 'Unknown Source'),
            })
        except (ValueError, TypeError, KeyError):
            continue
            
    news_list = []
    valid_sources = [
        "Zacks Investment Research", "Zacks", "InvestorPlace", "Seeking Alpha", 
        "Yahoo Finance", "Yahoo Finance video", "CNBC", "TipRanks", "MarketWatch", 
        "The Fly", "Benzinga", "TalkMarkets", "Reuters", "Business Insider", 
        "The Motley Fool", "Fool.com", "GlobeNewswire", "Business Wire", "PR Newswire",
        "Associated Press", "Bloomberg", "Investopedia"
    ]
    market_close_time, market_open_time = dt_time(16, 0), dt_time(9, 30)

    for i in range(len(data)):
        current_date = datetime.strptime(data.iloc[i]['Date'], '%Y-%m-%d').date()
        next_trading_date = datetime.strptime(data.iloc[i + 1]['Date'], '%Y-%m-%d').date() if i + 1 < len(data) else current_date + timedelta(days=1)
        
        relevant_news = []
        for news in news_by_calendar_day.get(current_date, []):
            if news['datetime'].time() >= market_close_time: relevant_news.append(news)
        
        day_after_current = current_date + timedelta(days=1)
        while day_after_current < next_trading_date:
            relevant_news.extend(news_by_calendar_day.get(day_after_current, []))
            day_after_current += timedelta(days=1)

        for news in news_by_calendar_day.get(next_trading_date, []):
            if news['datetime'].time() <= market_open_time: relevant_news.append(news)

        filtered_news = [{"date": n['datetime'].strftime('%Y%m%d%H%M%S'), "headline": n['headline'], "summary": n['summary'], "source": n['source']} for n in relevant_news if n['source'] in valid_sources]
        filtered_news.sort(key=lambda x: x['date'])
        news_list.append(json.dumps(filtered_news))

    data['News'] = news_list
    return data

def get_press_releases(symbol, data, start_date, end_date):
    """
    Fetches press releases by paginating until the release date is outside the
    desired start_date, as this endpoint does not accept date parameters.
    """
    print("--- Starting Press Release Fetch from FMP ---")
    endpoint_url = f"{FMP_BASE_URL}/api/v3/press-releases/{symbol}?apikey={FMP_API_KEY}"
    all_releases = []
    start_date_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date_dt = datetime.strptime(end_date, '%Y-%m-%d').date() # Create end_date object

    page = 0
    MAX_PAGES = 100 # Safety break to avoid infinite loops
    while page < MAX_PAGES:
        # Construct URL with pagination. No date parameters are used.
        url = f"{endpoint_url}&page={page}"
        print(f"Fetching press releases from page: {page}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            batch = response.json()
            # print(batch)
            # This correctly handles the case where a page is empty.
            if not batch:
                print("No more press releases found, stopping.")
                break
            
            # Check the date of the last item in the batch to see if we should stop
            last_item_date_str = batch[-1].get('date', '').split(' ')[0]
            last_item_date = datetime.strptime(last_item_date_str, '%Y-%m-%d').date()

            all_releases.extend(batch)

            if last_item_date < start_date_dt:
                print(f"Last fetched press release ({last_item_date}) is older than start date ({start_date_dt}). Stopping pagination.")
                break

            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data on page {page}: {e}")
            break

    releases_by_date = defaultdict(list)
    for pr in all_releases:
        try:
            pr_date_obj = datetime.strptime(pr['date'], '%Y-%m-%d %H:%M:%S')
            # BUG FIX: Added check to ensure the date is also not AFTER the end_date.
            if start_date_dt <= pr_date_obj.date() <= end_date_dt:
                 releases_by_date[pr_date_obj.date().strftime('%Y-%m-%d')].append({
                    "date": pr_date_obj.strftime('%Y-%m-%d %H:%M:%S'), 
                    "headline": pr.get('title', 'No Title'),
                    "description": pr.get('text', 'No Description')
                })
        except (ValueError, TypeError, KeyError):
            continue
            
    press_releases_list = [json.dumps(sorted(releases_by_date.get(date_str, []), key=lambda x: x['date'])) for date_str in data['Date']]
    data['PressReleases'] = press_releases_list
    return data

def get_company_profile(symbol):
    """Fetches company profile data from the FMP API."""
    print(f"Fetching company profile for {symbol}...")
    url = f"{FMP_BASE_URL}/stable/profile/?symbol={symbol}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        profile = response.json()[0]
        try:
            employees_int = int(profile.get('fullTimeEmployees', 0))
        except (ValueError, TypeError):
            # If the value is None or not a valid number, default to 0
            employees_int = 0
        return {'name': profile.get('companyName'), 'exchange': profile.get('exchange'), 'marketCapitalization': profile.get('marketCap'), 'employeeTotal': employees_int, 'industry': profile.get('industry'), 'symbol': profile.get('symbol')}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching company profile for {symbol}: {e}")
        return {}

def prepare_data_for_symbol(symbol, data_dir, start_date, end_date):
    """Main function to orchestrate the data downloading and preparation process."""
    data = get_returns(symbol, start_date, end_date)
    print("Returns data prepared.")
    
    if not data.empty:
        data = get_news(symbol, data, start_date, end_date)
        print("News data prepared.")
        data = get_press_releases(symbol, data, start_date, end_date)
        print("Press releases data prepared.")
    else:
        print("No returns data found; skipping news and press release fetch.")
        data['News'] = '[]'
        data['PressReleases'] = '[]'

    filename = f"{symbol}_{start_date}_{end_date}.csv"
    filepath = os.path.join(data_dir, filename)
    data.to_csv(filepath, index=False)
    print(f"Data for {symbol} saved to {filepath}")
    
    return data
