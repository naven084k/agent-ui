from urllib.parse import quote_plus

import httpx

from ..config import get_settings


WMO_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}

TOOL_SPECS: list[dict] = [
    # ── Weather ──────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "weather_current",
            "description": "Get current weather conditions for a city or location.",
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
            "description": "Get a multi-day weather forecast for a city or location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City or location name"},
                    "days": {"type": "integer", "description": "Number of forecast days (1–7)", "default": 3},
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "air_quality",
            "description": "Get current air quality index and pollutant levels for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City or location name"},
                },
                "required": ["location"],
            },
        },
    },
    # ── Finance ──────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "stock_price",
            "description": "Get the current stock price and basic info for a ticker symbol (e.g. AAPL, TSLA, GOOGL).",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL"},
                },
                "required": ["symbol"],
            },
        },
    },
    # ── Search ───────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Search the web using Google. Use for current events, news, or any question that benefits from up-to-date web results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results to return (1–10)", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wikipedia_search",
            "description": "Search Wikipedia and return a summary of the best matching article. Good for factual questions about people, places, events, and concepts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Topic or question to look up"},
                },
                "required": ["query"],
            },
        },
    },
    # ── Knowledge ────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "dictionary_lookup",
            "description": "Look up the definition, pronunciation, and examples for an English word.",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {"type": "string", "description": "Word to define"},
                },
                "required": ["word"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "country_info",
            "description": "Get information about a country: capital, population, area, currency, languages, and region.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Country name"},
                },
                "required": ["country"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "currency_convert",
            "description": "Convert an amount from one currency to another using live exchange rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount to convert"},
                    "from_currency": {"type": "string", "description": "Source currency code, e.g. USD"},
                    "to_currency": {"type": "string", "description": "Target currency code, e.g. EUR"},
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
]


def _http() -> httpx.Client:
    return httpx.Client(timeout=15, follow_redirects=True)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _geocode(location: str) -> tuple[float, float, str]:
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote_plus(location)}&count=1&language=en&format=json"
    with _http() as client:
        data = client.get(url).raise_for_status().json()
    results = data.get("results") or []
    if not results:
        raise ValueError(f"Location not found: {location}")
    r = results[0]
    name = f"{r['name']}, {r.get('country', '')}".strip(", ")
    return r["latitude"], r["longitude"], name


# ── Weather ───────────────────────────────────────────────────────────────────

def _weather_current(location: str) -> str:
    lat, lon, name = _geocode(location)
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code"
        f"&timezone=auto"
    )
    with _http() as client:
        data = client.get(url).raise_for_status().json()
    c = data.get("current", {})
    code = c.get("weather_code", -1)
    lines = [
        f"Location: {name}",
        f"Condition: {WMO_CODES.get(code, 'Unknown')}",
        f"Temperature: {c.get('temperature_2m', '?')} °C",
        f"Feels like: {c.get('apparent_temperature', '?')} °C",
        f"Humidity: {c.get('relative_humidity_2m', '?')}%",
        f"Wind: {c.get('wind_speed_10m', '?')} km/h",
    ]
    print("[tool.weather_current]", {"location": name}, flush=True)
    return "\n".join(lines)


def _weather_forecast(location: str, days: int = 3) -> str:
    lat, lon, name = _geocode(location)
    days = max(1, min(days, 7))
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
        f"&forecast_days={days}&timezone=auto"
    )
    with _http() as client:
        data = client.get(url).raise_for_status().json()
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    lines = [f"Forecast for: {name}"]
    for i, date in enumerate(dates):
        code = (daily.get("weather_code") or [])[i] if i < len(daily.get("weather_code") or []) else -1
        tmax = (daily.get("temperature_2m_max") or [])[i] if i < len(daily.get("temperature_2m_max") or []) else "?"
        tmin = (daily.get("temperature_2m_min") or [])[i] if i < len(daily.get("temperature_2m_min") or []) else "?"
        rain = (daily.get("precipitation_probability_max") or [])[i] if i < len(daily.get("precipitation_probability_max") or []) else "?"
        lines.append(f"{date}: {WMO_CODES.get(code, 'Unknown')}, {tmax}°C / {tmin}°C, rain {rain}%")
    print("[tool.weather_forecast]", {"location": name, "days": days}, flush=True)
    return "\n".join(lines)


def _air_quality(location: str) -> str:
    lat, lon, name = _geocode(location)
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        f"&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone,european_aqi"
        f"&timezone=auto"
    )
    with _http() as client:
        data = client.get(url).raise_for_status().json()
    c = data.get("current", {})
    aqi = c.get("european_aqi", "?")
    if isinstance(aqi, (int, float)):
        if aqi <= 20:
            category = "Good"
        elif aqi <= 40:
            category = "Fair"
        elif aqi <= 60:
            category = "Moderate"
        elif aqi <= 80:
            category = "Poor"
        elif aqi <= 100:
            category = "Very Poor"
        else:
            category = "Extremely Poor"
    else:
        category = "Unknown"
    lines = [
        f"Air Quality for: {name}",
        f"European AQI: {aqi} ({category})",
        f"PM2.5: {c.get('pm2_5', '?')} μg/m³",
        f"PM10: {c.get('pm10', '?')} μg/m³",
        f"Ozone: {c.get('ozone', '?')} μg/m³",
        f"NO₂: {c.get('nitrogen_dioxide', '?')} μg/m³",
        f"CO: {c.get('carbon_monoxide', '?')} μg/m³",
    ]
    print("[tool.air_quality]", {"location": name}, flush=True)
    return "\n".join(lines)


# ── Finance ───────────────────────────────────────────────────────────────────

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _yahoo_quote(sym: str) -> dict | None:
    """Fetch quote meta from Yahoo Finance using session-based crumb auth."""
    with httpx.Client(timeout=15, follow_redirects=True) as client:
        # Establish cookies
        client.get("https://finance.yahoo.com/", headers=_BROWSER_HEADERS)
        # Retrieve crumb
        crumb_resp = client.get(
            "https://query1.finance.yahoo.com/v1/test/getcrumb",
            headers=_BROWSER_HEADERS,
        )
        if crumb_resp.status_code != 200 or not crumb_resp.text.strip():
            return None
        crumb = crumb_resp.text.strip()
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{quote_plus(sym)}"
            f"?interval=1d&range=1d&crumb={quote_plus(crumb)}"
        )
        resp = client.get(url, headers=_BROWSER_HEADERS)
    if resp.status_code != 200:
        return None
    data = resp.json()
    results = (data.get("chart") or {}).get("result") or []
    return results[0].get("meta") if results else None


def _stooq_quote(sym: str) -> dict | None:
    """Fallback: last close from stooq.com (end-of-day, no auth needed)."""
    url = f"https://stooq.com/q/d/l/?s={sym.lower()}.us&i=d"
    with _http() as client:
        resp = client.get(url, headers=_BROWSER_HEADERS)
    if resp.status_code != 200:
        return None
    lines = [ln for ln in resp.text.strip().splitlines() if ln]
    if len(lines) < 2:
        return None
    parts = lines[-1].split(",")
    prev = lines[-2].split(",") if len(lines) >= 3 else None
    if len(parts) < 5:
        return None
    date, open_p, high, low, close = parts[:5]
    volume = parts[5] if len(parts) > 5 else "?"
    return {
        "source": "stooq",
        "date": date,
        "regularMarketPrice": float(close),
        "chartPreviousClose": float(prev[4]) if prev and len(prev) >= 5 else None,
        "open": float(open_p),
        "high": float(high),
        "low": float(low),
        "volume": volume,
        "currency": "USD",
    }


def _stock_price(symbol: str) -> str:
    sym = symbol.upper().strip()
    meta = _yahoo_quote(sym)
    source = "Yahoo Finance"
    if not meta:
        meta = _stooq_quote(sym)
        source = "Stooq (end-of-day)"
    if not meta:
        return f"Could not fetch price for **{sym}**. Check the ticker symbol and try again."

    price = meta.get("regularMarketPrice", "?")
    prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
    currency = meta.get("currency", "USD")
    name = meta.get("longName") or meta.get("shortName") or sym
    exchange = meta.get("exchangeName", "")
    market_state = meta.get("marketState", "")

    change_str = ""
    if isinstance(price, (int, float)) and isinstance(prev_close, (int, float)) and prev_close:
        change = price - prev_close
        pct = (change / prev_close) * 100
        sign = "+" if change >= 0 else ""
        change_str = f"  {sign}{change:.2f} ({sign}{pct:.2f}%)"

    lines = [
        f"**{name}** ({sym})",
        f"Price: {price} {currency}{change_str}",
    ]
    if prev_close:
        lines.append(f"Previous Close: {prev_close} {currency}")
    if exchange:
        lines.append(f"Exchange: {exchange}" + (f"  [{market_state}]" if market_state else ""))
    if meta.get("source") == "stooq" and meta.get("date"):
        lines.append(f"Date: {meta['date']}  (via {source})")
    else:
        lines.append(f"Source: {source}")

    print("[tool.stock_price]", {"symbol": sym, "price": price, "source": source}, flush=True)
    return "\n".join(lines)


# ── Search ────────────────────────────────────────────────────────────────────

def _google_search(query: str, num_results: int = 5) -> str:
    key = get_settings().serpapi_key
    if not key:
        raise ValueError("SERPAPI_KEY is not configured")
    num_results = max(1, min(num_results, 10))
    url = (
        f"https://serpapi.com/search.json"
        f"?engine=google&q={quote_plus(query)}&num={num_results}&api_key={key}"
    )
    with _http() as client:
        data = client.get(url).raise_for_status().json()
    results = data.get("organic_results", [])
    if not results:
        return "No results found."
    lines = []
    for r in results[:num_results]:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        link = r.get("link", "")
        lines.append(f"**{title}**\n{snippet}\n{link}")
    print("[tool.google_search]", {"query": query, "results": len(results)}, flush=True)
    return "\n\n".join(lines)


def _wikipedia_search(query: str) -> str:
    search_url = (
        f"https://en.wikipedia.org/w/api.php"
        f"?action=query&list=search&srsearch={quote_plus(query)}&format=json&srlimit=1"
    )
    with _http() as client:
        search_data = client.get(search_url).raise_for_status().json()
    results = search_data.get("query", {}).get("search", [])
    if not results:
        return f"No Wikipedia article found for: {query}"
    title = results[0]["title"]
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(title)}"
    with _http() as client:
        summary = client.get(summary_url).raise_for_status().json()
    extract = summary.get("extract", "No summary available.")
    page_url = summary.get("content_urls", {}).get("desktop", {}).get("page", "")
    lines = [f"**{title}**", "", extract]
    if page_url:
        lines += ["", f"Source: {page_url}"]
    print("[tool.wikipedia_search]", {"query": query, "title": title}, flush=True)
    return "\n".join(lines)


# ── Knowledge ─────────────────────────────────────────────────────────────────

def _dictionary_lookup(word: str) -> str:
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote_plus(word.lower())}"
    with _http() as client:
        resp = client.get(url)
    if resp.status_code == 404:
        return f"No definition found for: {word}"
    data = resp.raise_for_status().json()
    entry = data[0] if data else {}
    phonetic = entry.get("phonetic", "")
    lines = [f"**{word}**" + (f"  {phonetic}" if phonetic else "")]
    for meaning in entry.get("meanings", [])[:3]:
        part = meaning.get("partOfSpeech", "")
        defs = meaning.get("definitions", [])
        if defs:
            lines.append(f"\n*{part}*: {defs[0].get('definition', '')}")
            example = defs[0].get("example", "")
            if example:
                lines.append(f'  Example: "{example}"')
    print("[tool.dictionary_lookup]", {"word": word}, flush=True)
    return "\n".join(lines)


def _country_info(country: str) -> str:
    url = (
        f"https://restcountries.com/v3.1/name/{quote_plus(country)}"
        f"?fullText=false&fields=name,capital,population,currencies,languages,region,subregion,area"
    )
    with _http() as client:
        resp = client.get(url)
    if resp.status_code == 404:
        return f"Country not found: {country}"
    data = resp.raise_for_status().json()
    c = data[0]
    name = c.get("name", {}).get("common", country)
    capital = ", ".join(c.get("capital", [])) or "N/A"
    population = f"{c.get('population', 0):,}"
    region = c.get("region", "")
    subregion = c.get("subregion", "")
    area = f"{c.get('area', 0):,.0f} km²"
    currencies = ", ".join(
        f"{v.get('name', k)} ({v.get('symbol', '')})"
        for k, v in (c.get("currencies") or {}).items()
    )
    languages = ", ".join((c.get("languages") or {}).values())
    lines = [
        f"**{name}**",
        f"Region: {region}" + (f", {subregion}" if subregion else ""),
        f"Capital: {capital}",
        f"Population: {population}",
        f"Area: {area}",
        f"Currencies: {currencies or 'N/A'}",
        f"Languages: {languages or 'N/A'}",
    ]
    print("[tool.country_info]", {"country": name}, flush=True)
    return "\n".join(lines)


def _currency_convert(amount: float, from_currency: str, to_currency: str) -> str:
    from_c = from_currency.upper()
    to_c = to_currency.upper()
    url = f"https://api.frankfurter.app/latest?amount={amount}&from={from_c}&to={to_c}"
    with _http() as client:
        resp = client.get(url)
    if resp.status_code == 404:
        return f"Unsupported currency pair: {from_c} → {to_c}"
    data = resp.raise_for_status().json()
    rates = data.get("rates", {})
    if to_c not in rates:
        return f"Could not convert {from_c} to {to_c}."
    result = rates[to_c]
    date = data.get("date", "")
    print("[tool.currency_convert]", {"from": from_c, "to": to_c, "amount": amount}, flush=True)
    return f"{amount:,} {from_c} = {result:,} {to_c}" + (f"  (rate as of {date})" if date else "")


# ── Dispatcher ────────────────────────────────────────────────────────────────

def execute_tool(name: str, arguments: dict) -> str:
    match name:
        case "weather_current":
            return _weather_current(arguments["location"])
        case "weather_forecast":
            return _weather_forecast(arguments["location"], int(arguments.get("days", 3)))
        case "air_quality":
            return _air_quality(arguments["location"])
        case "stock_price":
            return _stock_price(arguments["symbol"])
        case "google_search":
            return _google_search(arguments["query"], int(arguments.get("num_results", 5)))
        case "wikipedia_search":
            return _wikipedia_search(arguments["query"])
        case "dictionary_lookup":
            return _dictionary_lookup(arguments["word"])
        case "country_info":
            return _country_info(arguments["country"])
        case "currency_convert":
            return _currency_convert(
                float(arguments["amount"]),
                arguments["from_currency"],
                arguments["to_currency"],
            )
        case _:
            raise ValueError(f"Unknown tool: {name}")
