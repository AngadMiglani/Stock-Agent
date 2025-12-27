import feedparser
from urllib.parse import quote_plus

def fetch_news(query: str, max_items: int = 10):
    
    q = quote_plus(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"

    feed = feedparser.parse(url)
    print("RSS entries found:", len(feed.entries))

    items = []

    for entry in feed.entries[:max_items]:
        items.append({
            "title" : getattr(entry, "title", ""),
            "link" : getattr(entry, "link", ""),
            "published" : getattr(entry, "published", ""),
        })

        print (len(items))
    return items