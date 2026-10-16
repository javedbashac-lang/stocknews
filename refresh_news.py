import json
import re
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import feedparser
import requests

IST = ZoneInfo("Asia/Kolkata")
OUT = Path(__file__).with_name("news.json")

# Google News RSS query for major global drivers of Indian equities.
QUERY = (
    '("Federal Reserve" OR "US inflation" OR "US Treasury yields" OR "Wall Street" '
    'OR "crude oil" OR OPEC OR "China economy" OR tariffs OR "US dollar" '
    'OR "global markets" OR "geopolitical tensions" OR "European Central Bank" '
    'OR "US jobs data" OR "bond yields") (markets OR economy OR stocks OR oil)'
)

# Transparent, simple keyword rules. This is a prioritisation aid, not an AI forecast.
WEIGHTS = {
    "fed": 5, "federal reserve": 5, "interest rate": 4, "inflation": 4,
    "crude oil": 5, "oil price": 5, "opec": 4, "treasury yield": 4,
    "bond yield": 4, "tariff": 4, "trade war": 4, "china": 3,
    "wall street": 4, "s&p 500": 4, "nasdaq": 3, "dollar": 3,
    "rupee": 4, "geopolitical": 3, "war": 2, "recession": 4,
    "jobs data": 3, "fii": 4, "foreign investor": 3, "supply disruption": 4,
}
NEGATIVE = [
    "surge in oil", "oil jumps", "rate hike", "higher inflation", "sell-off",
    "selloff", "market falls", "escalation", "recession", "tariffs rise",
    "sanctions", "war", "weak demand", "yields jump", "stocks tumble",
]
POSITIVE = [
    "rate cut", "inflation cools", "oil falls", "oil drops", "ceasefire",
    "trade deal", "stocks rally", "markets rise", "stimulus", "growth accelerates",
    "yields fall", "strong earnings",
]

def clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()

def score_item(title, description):
    text = f"{title} {description}".lower()
    return sum(weight for term, weight in WEIGHTS.items() if term in text)

def estimate_impact(title, description):
    text = f"{title} {description}".lower()
    neg = sum(1 for term in NEGATIVE if term in text)
    pos = sum(1 for term in POSITIVE if term in text)
    if pos > neg:
        return "Positive"
    if neg > pos:
        return "Negative"
    return "Mixed"

def affected_areas(title, description):
    text = f"{title} {description}".lower()
    areas = []
    if any(k in text for k in ["crude", "oil", "opec", "shipping", "middle east"]):
        areas += ["Crude-sensitive sectors", "Inflation", "Rupee"]
    if any(k in text for k in ["federal reserve", "fed", "treasury yield", "bond yield", "dollar", "currency"]):
        areas += ["Rupee", "FII flows", "Banks"]
    if any(k in text for k in ["china", "tariff", "trade war", "global trade", "manufacturing"]):
        areas += ["Exporters", "Metals", "Global risk sentiment"]
    if any(k in text for k in ["nasdaq", "technology", "tech stocks", "semiconductor", "artificial intelligence"]):
        areas += ["IT", "Technology"]
    if any(k in text for k in ["wall street", "s&p 500", "stocks", "equities", "market rally", "market falls"]):
        areas += ["Nifty 50", "Sensex"]
    if not areas:
        areas = ["Nifty 50", "Sensex", "FII flows"]
    return list(dict.fromkeys(areas))[:5]

def why_it_matters(title, description, impact):
    text = f"{title} {description}".lower()
    if any(k in text for k in ["crude", "oil", "opec"]):
        return "Oil-price changes can affect India's import bill, inflation expectations, the rupee and margins in fuel-sensitive sectors."
    if any(k in text for k in ["federal reserve", "fed", "treasury yield", "bond yield", "dollar"]):
        return "US rates and the dollar can change global borrowing costs and foreign-investor flows into emerging markets, including India."
    if any(k in text for k in ["china", "tariff", "trade war", "trade deal"]):
        return "Trade and China-related developments can affect global demand, supply chains, metals and sentiment toward export-oriented Indian companies."
    if any(k in text for k in ["wall street", "s&p 500", "nasdaq", "stocks", "equities"]):
        return "A broad move in overseas equities can influence Indian market sentiment at the next open, though local factors can override it."
    if any(k in text for k in ["inflation", "jobs data", "employment", "recession", "growth"]):
        return "Economic data can shift expectations for interest rates and global demand, which may affect valuations, the rupee and FII flows."
    return "This development may change global risk appetite or economic expectations, influencing Indian equities through sentiment and foreign-investor flows."

def fetch():
    url = "https://news.google.com/rss/search?q=" + quote(QUERY) + "&hl=en-IN&gl=IN&ceid=IN:en"
    response = requests.get(url, timeout=25, headers={"User-Agent": "GlobalMarketBriefing/1.0"})
    response.raise_for_status()
    feed = feedparser.parse(response.content)

    candidates = []
    seen = set()
    for entry in feed.entries:
        title = clean(entry.get("title"))
        link = entry.get("link", "")
        if not title or not link or title.lower() in seen:
            continue
        seen.add(title.lower())
        description = clean(re.sub(r"<[^>]+>", " ", entry.get("summary", "")))
        try:
            published_dt = parsedate_to_datetime(entry.published).astimezone(IST)
            published = published_dt.strftime("%d %b %Y, %I:%M %p IST")
            timestamp = published_dt.timestamp()
        except (AttributeError, TypeError, ValueError):
            published = "Publication time unavailable"
            timestamp = 0
        source = clean(entry.get("source", {}).get("title", "Google News"))
        score = score_item(title, description)
        candidates.append({
            "title": title,
            "url": link,
            "source": source or "Google News",
            "published": published,
            "_timestamp": timestamp,
            "_score": score,
            "impact": estimate_impact(title, description),
            "affected_areas": affected_areas(title, description),
            "why_it_matters": why_it_matters(title, description, ""),
        })

    # Prioritise market relevance, then newer stories. Keep only the 10 best-ranked stories.
    candidates.sort(key=lambda x: (x["_score"], x["_timestamp"]), reverse=True)
    final_items = []
    used_titles = set()
    for item in candidates:
        key = re.sub(r"[^a-z0-9]", "", item["title"].lower())
        if key in used_titles:
            continue
        used_titles.add(key)
        item.pop("_timestamp", None)
        item.pop("_score", None)
        final_items.append(item)
        if len(final_items) == 10:
            break

    payload = {
        "updated_at": datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST"),
        "items": final_items,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(final_items)} stories to {OUT}")
    if not final_items:
        raise RuntimeError("No stories were returned by the RSS feed.")

if __name__ == "__main__":
    fetch()
