import requests, pandas as pd
def fetch_price_history(symbol: str, days: int = 30):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
    params = dict(vs_currency="usd", days=days)
    r = requests.get(url, params=params, timeout=15).json()
    prices = pd.DataFrame(r["prices"], columns=["ts", "price"])
    prices["ts"] = pd.to_datetime(prices["ts"], unit="ms")
    volumes = pd.DataFrame(r["total_volumes"], columns=["ts", "volume"])
    volumes["ts"] = pd.to_datetime(volumes["ts"], unit="ms")
    return prices, volumes
