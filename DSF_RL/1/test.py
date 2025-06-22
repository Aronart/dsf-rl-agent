#!/usr/bin/env python
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
    from urllib2 import urlopen
import certifi
import json
""" def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
    return json.loads(data)

url = ("https://financialmodelingprep.com/api/v3/stock_news?tickers=AAPL&from=2021-01-01&to=2021-12-31&apikey=hoyW31n5KNbaLiVR3djw74SRaH6rntsT")
print(get_jsonparsed_data(url))
url = ("https://financialmodelingprep.com/stable/news/stock?symbols=AAPL&from=2021-01-01&to=2021-01-01&apikey=hoyW31n5KNbaLiVR3djw74SRaH6rntsT")
print(get_jsonparsed_data(url)) """

import requests
# url = "https://financialmodelingprep.com/stable/news/press-releases?symbols=AAPL&apikey=hoyW31n5KNbaLiVR3djw74SRaH6rntsT&from=2021-12-30&to=2021-12-31"
""" url = "https://financialmodelingprep.com/api/v3/press-releases/AAPL?apikey=hoyW31n5KNbaLiVR3djw74SRaH6rntsT&page=100"
url = "https://financialmodelingprep.com/stable/profile/?symbol=AAPL&apikey=hoyW31n5KNbaLiVR3djw74SRaH6rntsT"
response = requests.get(url)
response.raise_for_status()
batch = response.json()
print(batch) """

url = "https://financialmodelingprep.com/stable/profile/?symbol=AAPL&apikey=hoyW31n5KNbaLiVR3djw74SRaH6rntsT"

response = requests.get(url)
response.raise_for_status()
profile = response.json()[0]
print({'name': profile.get('companyName'), 'exchange': profile.get('exchange'), 'marketCapitalization': profile.get('marketCap'), 'employeeTotal': profile.get('fullTimeEmployees'), 'industry': profile.get('industry'), 'symbol': profile.get('symbol')})