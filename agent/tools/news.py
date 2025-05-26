import requests, os
def search_news(keyword: str, n: int = 5):
    url = "https://newsapi.org/v2/everything"
    params = dict(q=keyword, apiKey=os.getenv("NEWS_API_KEY"), language="en",
                  sortBy="publishedAt", pageSize=n)
    r = requests.get(url, params=params, timeout=15).json()
    news = []
    for art in r.get("articles", []):
        news.append({"title": art["title"], "summary": art["description"]})
    return news
