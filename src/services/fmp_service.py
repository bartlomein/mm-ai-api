"""
Financial Modeling Prep (FMP) API Service
Fetches and normalizes market data for LLM consumption
"""

import os
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

class FMPService:
    def __init__(self):
        self.api_key = os.getenv("FMP_API_KEY")
        self.base_url = "https://financialmodelingprep.com/api/v3"
        
        if not self.api_key:
            print("[FMPService] WARNING: FMP_API_KEY not found in environment variables")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make HTTP request to FMP API"""
        if not self.api_key:
            print("[FMPService] ERROR: FMP_API_KEY not configured")
            return None
        
        url = f"{self.base_url}/{endpoint}"
        
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"[FMPService] Error {response.status_code}: {response.text}")
                    return None
        except Exception as e:
            print(f"[FMPService] Request error: {str(e)}")
            return None
    
    async def get_market_indices(self) -> Dict[str, Any]:
        """Get major market indices (SPY, QQQ, DIA)"""
        indices = ["SPY", "QQQ", "DIA", "IWM", "VTI"]
        data = await self._make_request("quote/" + ",".join(indices))
        
        if not data:
            return {}
        
        normalized = {
            "indices": [],
            "summary": ""
        }
        
        for index in data:
            normalized["indices"].append({
                "symbol": index.get("symbol"),
                "name": index.get("name"),
                "price": index.get("price"),
                "change": index.get("change"),
                "changePercent": index.get("changesPercentage"),
                "dayLow": index.get("dayLow"),
                "dayHigh": index.get("dayHigh"),
                "volume": index.get("volume")
            })
        
        # Create summary text for LLM
        summary_parts = []
        for idx in normalized["indices"]:
            if idx["symbol"] and idx["price"]:
                direction = "up" if idx["change"] > 0 else "down"
                summary_parts.append(
                    f"{idx['symbol']} is trading at ${idx['price']:.2f}, "
                    f"{direction} {abs(idx['changePercent']):.2f}%"
                )
        
        normalized["summary"] = " | ".join(summary_parts)
        return normalized
    
    async def get_premarket_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get premarket data with calculated percent changes using both APIs"""
        if symbols is None:
            symbols = ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"]
        
        normalized = {
            "premarket": [],
            "summary": ""
        }
        
        # Step 1: Get previous close prices from regular quotes API
        print("[FMPService] Fetching previous close prices...")
        previous_closes = {}
        regular_quotes = await self.get_regular_quotes(symbols)
        for quote in regular_quotes.get("quotes", []):
            symbol = quote.get("symbol")
            prev_close = quote.get("previousClose")
            if symbol and prev_close:
                previous_closes[symbol] = prev_close
        
        # Step 2: Get premarket bid/ask data from v4 API
        print("[FMPService] Fetching premarket bid/ask data...")
        for symbol in symbols:
            v4_url = f"https://financialmodelingprep.com/api/v4/pre-post-market/{symbol}"
            params = {'apikey': self.api_key} if self.api_key else {}
            
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(v4_url, params=params)
                    
                    if response.status_code == 200:
                        stock_data = response.json()
                        
                        if stock_data.get("error"):
                            print(f"[FMPService] API error for {symbol}: {stock_data.get('error')}")
                            continue
                            
                        if stock_data and "bid" in stock_data and "ask" in stock_data:
                            bid = stock_data.get("bid", 0)
                            ask = stock_data.get("ask", 0)
                            mid_price = (bid + ask) / 2 if bid and ask else None
                            
                            # Calculate change and percent change if we have previous close
                            prev_close = previous_closes.get(symbol)
                            change = None
                            change_percent = None
                            
                            if mid_price and prev_close:
                                change = mid_price - prev_close
                                change_percent = (change / prev_close) * 100
                            
                            normalized["premarket"].append({
                                "symbol": symbol,
                                "preMarketPrice": mid_price,
                                "preMarketChange": change,
                                "preMarketChangePercent": change_percent,
                                "lastClose": prev_close,
                                "bid": bid,
                                "ask": ask
                            })
                    else:
                        print(f"[FMPService] Error fetching {symbol}: {response.status_code}")
                        
            except Exception as e:
                print(f"[FMPService] Request error for {symbol}: {str(e)}")
                continue
        
        # Create summary text with percent changes
        summary_parts = []
        for stock in normalized["premarket"]:
            if stock["symbol"] and stock.get("preMarketPrice"):
                symbol = stock["symbol"]
                price = stock["preMarketPrice"]
                change = stock.get("preMarketChange")
                change_pct = stock.get("preMarketChangePercent")
                
                if change is not None and change_pct is not None:
                    direction = "+" if change >= 0 else ""
                    summary_parts.append(
                        f"{symbol}: ${price:.2f} ({direction}{change:.2f}, {direction}{change_pct:.2f}%)"
                    )
                else:
                    # Fallback to bid/ask if no previous close available
                    bid = stock.get("bid")
                    ask = stock.get("ask")
                    if bid and ask:
                        summary_parts.append(
                            f"{symbol}: ${price:.2f} (bid: ${bid:.2f}, ask: ${ask:.2f})"
                        )
        
        normalized["summary"] = " | ".join(summary_parts) if summary_parts else "No premarket data available"
        return normalized
    
    async def get_regular_quotes(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get regular market quotes with previous close data"""
        if symbols is None:
            symbols = ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"]
        
        # Use the batch quote endpoint
        data = await self._make_request("quote/" + ",".join(symbols))
        
        if not data:
            return {}
        
        normalized = {
            "quotes": [],
            "summary": ""
        }
        
        for stock in data:
            if stock:
                normalized["quotes"].append({
                    "symbol": stock.get("symbol"),
                    "price": stock.get("price"),
                    "previousClose": stock.get("previousClose"),
                    "change": stock.get("change"), 
                    "changesPercentage": stock.get("changesPercentage"),
                    "dayLow": stock.get("dayLow"),
                    "dayHigh": stock.get("dayHigh"),
                    "volume": stock.get("volume")
                })
        
        # Create summary text
        summary_parts = []
        for stock in normalized["quotes"]:
            if stock["symbol"] and stock.get("price"):
                change = stock.get("change", 0) or 0
                change_pct = stock.get("changesPercentage", 0) or 0
                direction = "+" if change >= 0 else ""
                summary_parts.append(
                    f"{stock['symbol']}: ${stock['price']:.2f} "
                    f"({direction}{change:.2f}, {direction}{change_pct:.2f}%)"
                )
        
        normalized["summary"] = " | ".join(summary_parts) if summary_parts else "No quote data available"
        return normalized
    
    async def get_crypto_overview(self) -> Dict[str, Any]:
        """Get overview of major cryptocurrencies"""
        cryptos = ["BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "ADAUSD", "XRPUSD"]
        data = await self._make_request("quote/" + ",".join(cryptos))
        
        if not data:
            return {}
        
        normalized = {
            "cryptos": [],
            "summary": "",
            "market_sentiment": ""
        }
        
        total_market_cap = 0
        positive_count = 0
        
        for crypto in data:
            change_percent = crypto.get("changesPercentage", 0)
            normalized["cryptos"].append({
                "symbol": crypto.get("symbol"),
                "name": crypto.get("name"),
                "price": crypto.get("price"),
                "change": crypto.get("change"),
                "changePercent": change_percent,
                "volume": crypto.get("volume"),
                "marketCap": crypto.get("marketCap")
            })
            
            if crypto.get("marketCap"):
                total_market_cap += crypto["marketCap"]
            if change_percent > 0:
                positive_count += 1
        
        # Determine market sentiment
        if positive_count > len(data) * 0.6:
            normalized["market_sentiment"] = "bullish"
        elif positive_count < len(data) * 0.4:
            normalized["market_sentiment"] = "bearish"
        else:
            normalized["market_sentiment"] = "mixed"
        
        # Create summary
        btc = next((c for c in normalized["cryptos"] if "BTC" in c["symbol"]), None)
        eth = next((c for c in normalized["cryptos"] if "ETH" in c["symbol"]), None)
        
        summary_parts = []
        if btc:
            summary_parts.append(f"Bitcoin at ${btc['price']:,.0f} ({btc['changePercent']:.1f}%)")
        if eth:
            summary_parts.append(f"Ethereum at ${eth['price']:,.0f} ({eth['changePercent']:.1f}%)")
        
        normalized["summary"] = f"Crypto market is {normalized['market_sentiment']}. " + " | ".join(summary_parts)
        return normalized
    
    async def get_market_movers(self) -> Dict[str, Any]:
        """Get biggest gainers, losers, and most active stocks"""
        gainers = await self._make_request("stock_market/gainers")
        losers = await self._make_request("stock_market/losers")
        actives = await self._make_request("stock_market/actives")
        
        normalized = {
            "gainers": [],
            "losers": [],
            "most_active": [],
            "summary": ""
        }
        
        # Process gainers
        if gainers:
            for stock in gainers[:5]:  # Top 5
                normalized["gainers"].append({
                    "symbol": stock.get("symbol"),
                    "name": stock.get("name"),
                    "price": stock.get("price"),
                    "changePercent": stock.get("changesPercentage")
                })
        
        # Process losers
        if losers:
            for stock in losers[:5]:  # Top 5
                normalized["losers"].append({
                    "symbol": stock.get("symbol"),
                    "name": stock.get("name"),
                    "price": stock.get("price"),
                    "changePercent": stock.get("changesPercentage")
                })
        
        # Process most active
        if actives:
            for stock in actives[:5]:  # Top 5
                normalized["most_active"].append({
                    "symbol": stock.get("symbol"),
                    "name": stock.get("name"),
                    "price": stock.get("price"),
                    "volume": stock.get("volume")
                })
        
        # Create summary
        summary_parts = []
        if normalized["gainers"]:
            top_gainer = normalized["gainers"][0]
            summary_parts.append(f"Top gainer: {top_gainer['symbol']} up {top_gainer['changePercent']:.1f}%")
        
        if normalized["losers"]:
            top_loser = normalized["losers"][0]
            summary_parts.append(f"Top loser: {top_loser['symbol']} down {abs(top_loser['changePercent']):.1f}%")
        
        if normalized["most_active"]:
            most_active = normalized["most_active"][0]
            summary_parts.append(f"Most active: {most_active['symbol']}")
        
        normalized["summary"] = " | ".join(summary_parts)
        return normalized
    
    async def get_sector_performance(self) -> Dict[str, Any]:
        """Get sector performance data"""
        data = await self._make_request("sectors-performance")
        
        if not data:
            return {}
        
        normalized = {
            "sectors": [],
            "summary": "",
            "strongest_sector": "",
            "weakest_sector": ""
        }
        
        for sector in data:
            normalized["sectors"].append({
                "sector": sector.get("sector"),
                "changePercent": sector.get("changesPercentage", "").replace("%", "") if sector.get("changesPercentage") else 0
            })
        
        # Sort by performance
        sorted_sectors = sorted(normalized["sectors"], key=lambda x: float(x["changePercent"]) if x["changePercent"] else 0, reverse=True)
        
        if sorted_sectors:
            normalized["strongest_sector"] = sorted_sectors[0]["sector"]
            normalized["weakest_sector"] = sorted_sectors[-1]["sector"]
            
            # Create summary
            strong = sorted_sectors[0]
            weak = sorted_sectors[-1]
            normalized["summary"] = (
                f"{strong['sector']} leads sectors up {strong['changePercent']}%, "
                f"while {weak['sector']} lags at {weak['changePercent']}%"
            )
        
        return normalized
    
    async def get_intraday_performance(self, symbol: str, interval: str = "5min") -> Dict[str, Any]:
        """Get intraday price action for a symbol"""
        data = await self._make_request(f"historical-chart/{interval}/{symbol}")
        
        if not data:
            return {}
        
        # Get last 8 hours of data (96 5-minute candles)
        recent_data = data[:96] if len(data) > 96 else data
        
        if not recent_data:
            return {}
        
        normalized = {
            "symbol": symbol,
            "interval": interval,
            "data_points": len(recent_data),
            "high": max([d.get("high", 0) for d in recent_data]),
            "low": min([d.get("low", float('inf')) for d in recent_data]),
            "current": recent_data[0].get("close") if recent_data else 0,
            "open_8h_ago": recent_data[-1].get("open") if recent_data else 0,
            "volume_total": sum([d.get("volume", 0) for d in recent_data]),
            "summary": ""
        }
        
        # Calculate 8-hour change
        if normalized["open_8h_ago"] and normalized["current"]:
            change = normalized["current"] - normalized["open_8h_ago"]
            change_percent = (change / normalized["open_8h_ago"]) * 100
            
            direction = "up" if change > 0 else "down"
            normalized["summary"] = (
                f"{symbol} is {direction} {abs(change_percent):.2f}% over the past 8 hours, "
                f"trading at ${normalized['current']:.2f} with range ${normalized['low']:.2f}-${normalized['high']:.2f}"
            )
        
        return normalized
    
    async def get_economic_calendar(self, from_date: str = None, to_date: str = None, country: str = None) -> Dict[str, Any]:
        """Get upcoming economic events
        
        Args:
            from_date: Start date in YYYY-MM-DD format (defaults to today)
            to_date: End date in YYYY-MM-DD format (defaults to tomorrow)
            country: Filter by country code (e.g., 'US', 'EU', 'GB')
        """
        if from_date is None:
            from_date = datetime.now().strftime("%Y-%m-%d")
        if to_date is None:
            to_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        params = {
            "from": from_date,
            "to": to_date
        }
        
        data = await self._make_request("economic_calendar", params)
        
        if not data:
            return {}
        
        normalized = {
            "events": [],
            "high_impact": [],
            "summary": ""
        }
        
        # Filter by country if specified
        if country:
            data = [event for event in data if event.get("country") == country]
        
        # Process all events (remove the 10 event limit for weekly view)
        for event in data:
            event_data = {
                "date": event.get("date"),
                "event": event.get("event"),
                "country": event.get("country"),
                "impact": event.get("impact"),
                "actual": event.get("actual"),
                "estimate": event.get("estimate"),
                "previous": event.get("previous")
            }
            
            normalized["events"].append(event_data)
            
            if event.get("impact") == "High":
                normalized["high_impact"].append(event_data)
        
        # Create summary
        if normalized["high_impact"]:
            high_impact_names = [e["event"] for e in normalized["high_impact"][:3]]
            normalized["summary"] = f"Key events today: {', '.join(high_impact_names)}"
        else:
            normalized["summary"] = f"{len(normalized['events'])} economic events scheduled"
        
        return normalized
    
    async def generate_market_briefing(self, focus_areas: List[str] = None) -> str:
        """Generate a comprehensive market briefing for LLM consumption"""
        if focus_areas is None:
            focus_areas = ["indices", "crypto", "movers", "sectors"]
        
        briefing_parts = []
        
        # Add timestamp
        briefing_parts.append(f"Market Update - {datetime.now().strftime('%Y-%m-%d %H:%M')} ET\n")
        
        # Fetch and add market indices
        if "indices" in focus_areas:
            indices = await self.get_market_indices()
            if indices.get("summary"):
                briefing_parts.append(f"INDICES: {indices['summary']}")
        
        # Fetch and add crypto overview
        if "crypto" in focus_areas:
            crypto = await self.get_crypto_overview()
            if crypto.get("summary"):
                briefing_parts.append(f"CRYPTO: {crypto['summary']}")
        
        # Fetch and add market movers
        if "movers" in focus_areas:
            movers = await self.get_market_movers()
            if movers.get("summary"):
                briefing_parts.append(f"MOVERS: {movers['summary']}")
        
        # Fetch and add sector performance
        if "sectors" in focus_areas:
            sectors = await self.get_sector_performance()
            if sectors.get("summary"):
                briefing_parts.append(f"SECTORS: {sectors['summary']}")
        
        # Fetch and add economic calendar
        if "calendar" in focus_areas:
            calendar = await self.get_economic_calendar()
            if calendar.get("summary"):
                briefing_parts.append(f"EVENTS: {calendar['summary']}")
        
        return "\n\n".join(briefing_parts)
    
    async def get_past_8_hours_summary(self, symbols: List[str] = None) -> str:
        """Generate summary of past 8 hours for specific symbols"""
        if symbols is None:
            symbols = ["SPY", "QQQ", "BTC-USD"]
        
        summaries = []
        
        for symbol in symbols:
            # FMP uses different notation for crypto
            fmp_symbol = symbol.replace("-USD", "USD") if "-USD" in symbol else symbol
            intraday = await self.get_intraday_performance(fmp_symbol)
            
            if intraday.get("summary"):
                summaries.append(intraday["summary"])
        
        return " | ".join(summaries) if summaries else "No 8-hour data available"