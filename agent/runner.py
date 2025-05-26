import os, base64, io, datetime
import openai, pandas as pd, matplotlib.pyplot as plt
from jinja2 import Template
from tools.price import fetch_price_history
from tools.onchain import fetch_onchain_stats
from tools.news import search_news

openai.api_key = os.getenv("OPENAI_API_KEY")

def plot_chart(df: pd.DataFrame, ylabel: str):
    plt.figure(figsize=(6,3))
    plt.plot(df["ts"], df[df.columns[1]])
    plt.ylabel(ylabel); plt.xlabel("Date")
    buf = io.BytesIO(); plt.tight_layout(); plt.savefig(buf, format="png"); plt.close()
    return base64.b64encode(buf.getvalue()).decode()

def analyze_token(symbol: str, contract_addr: str):
    prices, volumes = fetch_price_history(symbol)
    onchain = fetch_onchain_stats(contract_addr)
    news = search_news(symbol)

    stats_line = (f"当前价 {prices.iloc[-1,1]:.4f} USD，30日涨跌 "
                  f"{(prices.iloc[-1,1]-prices.iloc[0,1])/prices.iloc[0,1]*100:.2f}%")
    onchain_line = (f"持币地址 {onchain['holders']}，近7日交易 {onchain['recent_tx']} 笔")

    prompt = Template(open('prompts/analysis_prompt.txt',encoding='utf-8').read()).render(
        market_line=stats_line, onchain_line=onchain_line, news_count=len(news)
    )
    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0.3, max_tokens=1024
    )
    body_html = completion.choices[0].message.content

    price_img = plot_chart(prices, "Price (USD)")
    volume_img = plot_chart(volumes, "Volume")
    body_html += (f"<h3>价格走势</h3><img src='data:image/png;base64,{price_img}'/>"
                  f"<h3>交易量</h3><img src='data:image/png;base64,{volume_img}'/>")

    template = Template(open('templates/report_template.html',encoding='utf-8').read())
    final_html = template.render(symbol=symbol.upper(), body=body_html,
                                 now=datetime.datetime.utcnow().isoformat())

    out_path = f"{symbol}_report.html"
    with open(out_path,"w",encoding="utf-8") as f:
        f.write(final_html)
    print("Report saved:", out_path)

if __name__ == "__main__":
    analyze_token("usd-coin", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
