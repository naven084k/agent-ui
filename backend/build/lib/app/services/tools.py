import subprocess
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup


TOOL_SPECS: list[dict] = [
        {
            "type": "function",
            "function": {
                "name": "read_local_file",
                "description": "Read a local text file inside the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Workspace-relative file path"}
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_python",
                "description": "Execute a short Python snippet and return stdout.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"}
                    },
                    "required": ["code"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for recent pages and return short result summaries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Maximum number of results", "default": 5},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "news_search",
                "description": "Get recent news headlines for a topic.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "News topic or keywords"},
                        "limit": {"type": "integer", "description": "Maximum number of headlines", "default": 5},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "social_updates",
                "description": "Get recent Reddit posts for a topic or subreddit.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query or subreddit name"},
                        "subreddit": {"type": "string", "description": "Optional subreddit name"},
                        "limit": {"type": "integer", "description": "Maximum number of posts", "default": 5},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "weather_lookup",
                "description": "Get current weather conditions for a location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City or location name"},
                    },
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "weather_forecast",
                "description": "Get a short weather forecast for a location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City or location name"},
                        "days": {"type": "integer", "description": "Number of forecast days", "default": 3},
                    },
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "finance_lookup",
                "description": "Get latest finance quote information for a stock, ETF, index, or forex symbol.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Ticker symbol like AAPL, MSFT, SPY, EURUSD"},
                    },
                    "required": ["symbol"],
                },
            },
        },
]


def get_tool_specs(allowed_names: Iterable[str] | None = None) -> list[dict]:
    if allowed_names is None:
        return TOOL_SPECS
    allowed = set(allowed_names)
    return [spec for spec in TOOL_SPECS if spec["function"]["name"] in allowed]


def _http_client() -> httpx.Client:
    return httpx.Client(
        timeout=15,
        headers={
            "User-Agent": "LocalAssistantWorkspace/0.1 (+https://localhost)",
        },
        follow_redirects=True,
    )


def _format_items(title: str, items: list[str]) -> str:
    body = "\n".join(f"- {item}" for item in items) if items else "- No results"
    return f"{title}\n{body}"


def _web_search(query: str, limit: int = 5) -> str:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    with _http_client() as client:
        response = client.get(url)
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results: list[str] = []
    for anchor in soup.select(".result__a")[: max(1, min(limit, 10))]:
        title = anchor.get_text(" ", strip=True)
        href = anchor.get("href", "")
        if title and href:
            results.append(f"{title} — {href}")
    print("[tool.web_search]", {"query": query, "results": len(results)}, flush=True)
    return _format_items(f"Web results for: {query}", results)


def _news_search(query: str, limit: int = 5) -> str:
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    with _http_client() as client:
        response = client.get(url)
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "xml")
    items: list[str] = []
    for item in soup.find_all("item")[: max(1, min(limit, 10))]:
        title = (item.title.text if item.title else "").strip()
        link = (item.link.text if item.link else "").strip()
        pub_date = (item.pubDate.text if item.pubDate else "").strip()
        if title:
            items.append(f"{title} ({pub_date}) — {link}")
    print("[tool.news_search]", {"query": query, "results": len(items)}, flush=True)
    return _format_items(f"News for: {query}", items)


def _social_updates(query: str, subreddit: str | None = None, limit: int = 5) -> str:
    max_results = max(1, min(limit, 10))
    if subreddit:
        url = f"https://www.reddit.com/r/{quote_plus(subreddit)}/new.json?limit={max_results}"
    else:
        url = f"https://www.reddit.com/search.json?q={quote_plus(query)}&sort=new&limit={max_results}"
    with _http_client() as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    items: list[str] = []
    for child in payload.get("data", {}).get("children", [])[:max_results]:
        data = child.get("data", {})
        title = data.get("title", "").strip()
        community = data.get("subreddit_name_prefixed", "").strip()
        permalink = data.get("permalink", "")
        score = data.get("score", 0)
        if title:
            items.append(f"{title} [{community}] score={score} — https://reddit.com{permalink}")
    print(
        "[tool.social_updates]",
        {"query": query, "subreddit": subreddit, "results": len(items)},
        flush=True,
    )
    label = f"Reddit updates for: r/{subreddit}" if subreddit else f"Reddit updates for: {query}"
    return _format_items(label, items)


def _weather_lookup(location: str) -> str:
    url = f"https://wttr.in/{quote_plus(location)}?format=j1"
    with _http_client() as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    current = (payload.get("current_condition") or [{}])[0]
    summary = [
        f"Location: {location}",
        f"Condition: {(current.get('weatherDesc') or [{}])[0].get('value', 'Unknown')}",
        f"Temperature: {current.get('temp_C', '?')} C / {current.get('temp_F', '?')} F",
        f"Feels like: {current.get('FeelsLikeC', '?')} C / {current.get('FeelsLikeF', '?')} F",
        f"Humidity: {current.get('humidity', '?')}%",
        f"Wind: {current.get('windspeedKmph', '?')} km/h",
    ]
    print("[tool.weather_lookup]", {"location": location}, flush=True)
    return "\n".join(summary)


def _weather_forecast(location: str, days: int = 3) -> str:
    url = f"https://wttr.in/{quote_plus(location)}?format=j1"
    with _http_client() as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    max_days = max(1, min(days, 5))
    lines = [f"Forecast for: {location}"]
    for day in (payload.get("weather") or [])[:max_days]:
        date = day.get("date", "")
        maxtemp = day.get("maxtempC", "?")
        mintemp = day.get("mintempC", "?")
        hourly = (day.get("hourly") or [{}])[4] if len(day.get("hourly") or []) > 4 else (day.get("hourly") or [{}])[0]
        desc = (hourly.get("weatherDesc") or [{}])[0].get("value", "Unknown")
        chance_of_rain = hourly.get("chanceofrain", "?")
        lines.append(f"{date}: {desc}, high {maxtemp} C, low {mintemp} C, rain chance {chance_of_rain}%")
    print("[tool.weather_forecast]", {"location": location, "days": max_days}, flush=True)
    return "\n".join(lines)


def _finance_lookup(symbol: str) -> str:
    cleaned = symbol.strip().lower()
    suffix = "" if "." in cleaned else ".us"
    url = f"https://stooq.com/q/l/?s={cleaned}{suffix}&f=sd2t2ohlcvn&e=csv"
    with _http_client() as client:
        response = client.get(url)
        response.raise_for_status()
    lines = [line.strip() for line in response.text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError(f"No finance data found for symbol: {symbol}")
    header = lines[0].split(",")
    values = lines[1].split(",")
    data = dict(zip(header, values, strict=False))
    if data.get("Close", "N/D") == "N/D":
        raise ValueError(f"No finance data found for symbol: {symbol}")
    print("[tool.finance_lookup]", {"symbol": symbol, "close": data.get("Close")}, flush=True)
    return "\n".join(
        [
            f"Symbol: {data.get('Symbol', symbol.upper())}",
            f"Name: {data.get('Name', '')}",
            f"Date: {data.get('Date', '')} {data.get('Time', '')}".strip(),
            f"Open: {data.get('Open', '')}",
            f"High: {data.get('High', '')}",
            f"Low: {data.get('Low', '')}",
            f"Close: {data.get('Close', '')}",
            f"Volume: {data.get('Volume', '')}",
        ]
    )


def execute_tool(name: str, arguments: dict) -> str:
    if name == "read_local_file":
        path = Path(arguments["path"]).resolve()
        workspace = Path.cwd().resolve()
        if workspace not in path.parents and path != workspace:
            raise ValueError("Path must stay inside the workspace")
        return path.read_text(encoding="utf-8", errors="ignore")[:16000]
    if name == "run_python":
        result = subprocess.run(
            ["python3", "-c", arguments["code"]],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path.cwd(),
        )
        return (result.stdout or "") + (result.stderr or "")
    if name == "web_search":
        return _web_search(arguments["query"], int(arguments.get("limit", 5)))
    if name == "news_search":
        return _news_search(arguments["query"], int(arguments.get("limit", 5)))
    if name == "social_updates":
        return _social_updates(arguments["query"], arguments.get("subreddit"), int(arguments.get("limit", 5)))
    if name == "weather_lookup":
        return _weather_lookup(arguments["location"])
    if name == "weather_forecast":
        return _weather_forecast(arguments["location"], int(arguments.get("days", 3)))
    if name == "finance_lookup":
        return _finance_lookup(arguments["symbol"])
    raise ValueError(f"Unknown tool: {name}")
