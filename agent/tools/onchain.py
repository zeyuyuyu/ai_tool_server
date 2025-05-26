import requests, os
ETHERSCAN_KEY = os.getenv("ETHERSCAN_KEY","")
def fetch_onchain_stats(token_address: str):
    url = "https://api.etherscan.io/api"
    holders = requests.get(url, params=dict(
        module="token", action="tokenholdercount",
        contractaddress=token_address, apikey=ETHERSCAN_KEY), timeout=15).json()
    tx = requests.get(url, params=dict(
        module="account", action="txlist",
        address=token_address, startblock=0, endblock=99999999,
        page=1, offset=100, sort="desc", apikey=ETHERSCAN_KEY), timeout=15).json()
    return {
        "holders": int(holders.get("result",0)),
        "recent_tx": len(tx.get("result",[]))
    }
