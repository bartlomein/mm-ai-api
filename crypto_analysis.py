import httpx
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio

class CryptoAnalyzer:
    """
    Crypto price analysis service that fetches data from Financial Modeling Prep API
    and provides structured analysis for BTC, ETH, and SOL with TTS-formatted output.
    """
    
    def __init__(self):
        self.api_key = "af382a3ee3dca2917ac1d80c284dec2f"  # FMP API key from request
        self.base_url = "https://financialmodelingprep.com/api/v3/historical-chart/5min"
        
        # Crypto symbols mapping
        self.symbols = {
            'BTC': 'BTCUSD',
            'ETH': 'ETHUSD', 
            'SOL': 'SOLUSD'
        }
        
        # Name mapping for TTS
        self.crypto_names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'SOL': 'Solana'
        }
    
    async def fetch_crypto_data(self, symbol: str, hours: int = 8) -> List[Dict]:
        """
        Fetch 5-minute crypto price data and aggregate into hourly periods.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTCUSD')
            hours: Number of hours of historical data to fetch
            
        Returns:
            List of hourly price data dictionaries sorted by date (oldest first)
        """
        print(f"[CryptoAnalyzer] Fetching {hours} hours of 5-minute data for {symbol}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get 5-minute data - we need roughly 12 * hours data points (12 5-min periods per hour)
                # Get extra to ensure we have enough data after filtering
                url = f"{self.base_url}/{symbol}?apikey={self.api_key}"
                
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if not data:
                        print(f"[CryptoAnalyzer] No data returned for {symbol}")
                        return []
                    
                    print(f"[CryptoAnalyzer] Fetched {len(data)} 5-minute data points for {symbol}")
                    
                    # Aggregate 5-minute data into hourly data
                    hourly_data = self._aggregate_to_hourly(data, hours)
                    
                    print(f"[CryptoAnalyzer] Aggregated to {len(hourly_data)} hourly data points for {symbol}")
                    return hourly_data
                    
                else:
                    print(f"[CryptoAnalyzer] API error for {symbol}: {response.status_code}")
                    print(f"[CryptoAnalyzer] Response: {response.text[:200]}")
                    return []
                    
            except Exception as e:
                print(f"[CryptoAnalyzer] Error fetching data for {symbol}: {str(e)}")
                return []
    
    def _aggregate_to_hourly(self, five_min_data: List[Dict], hours_needed: int) -> List[Dict]:
        """
        Aggregate 5-minute data into hourly OHLCV data.
        
        Args:
            five_min_data: List of 5-minute OHLCV data points
            hours_needed: Number of recent hours to return
            
        Returns:
            List of hourly OHLCV data points (oldest first)
        """
        from collections import defaultdict
        from datetime import datetime
        
        # Group 5-minute data by hour
        hourly_groups = defaultdict(list)
        
        for data_point in five_min_data:
            try:
                # Parse the date string (format: "2025-08-13 19:35:00")
                date_str = data_point['date']
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                
                # Create hour key (format: "2025-08-13 19")
                hour_key = dt.strftime("%Y-%m-%d %H")
                hourly_groups[hour_key].append(data_point)
                
            except (ValueError, KeyError) as e:
                print(f"[CryptoAnalyzer] Error parsing date {data_point.get('date', 'unknown')}: {e}")
                continue
        
        # Convert grouped data to hourly OHLCV
        hourly_data = []
        for hour_key in sorted(hourly_groups.keys(), reverse=True)[:hours_needed]:  # Most recent hours first
            five_min_points = hourly_groups[hour_key]
            
            if not five_min_points:
                continue
            
            # Calculate OHLCV for this hour
            opens = [float(p['open']) for p in five_min_points]
            highs = [float(p['high']) for p in five_min_points]
            lows = [float(p['low']) for p in five_min_points]
            closes = [float(p['close']) for p in five_min_points]
            volumes = [float(p.get('volume', 0)) for p in five_min_points]
            
            # For hourly data:
            # Open = first 5-min open of the hour
            # High = max of all 5-min highs
            # Low = min of all 5-min lows
            # Close = last 5-min close of the hour
            # Volume = sum of all 5-min volumes
            
            # Sort by time to get first and last
            sorted_points = sorted(five_min_points, key=lambda x: x['date'])
            
            hourly_point = {
                'date': hour_key + ":00:00",  # Add minutes and seconds for consistency
                'open': sorted_points[0]['open'],  # First open
                'high': max(highs),
                'low': min(lows),
                'close': sorted_points[-1]['close'],  # Last close
                'volume': sum(volumes)
            }
            
            hourly_data.append(hourly_point)
        
        # Sort chronologically (oldest first)
        hourly_data.reverse()
        
        return hourly_data
    
    def analyze_price_data(self, data: List[Dict], crypto_name: str) -> Dict:
        """
        Analyze crypto price data to extract key insights.
        
        Args:
            data: List of hourly price data
            crypto_name: Human-readable crypto name (e.g., 'Bitcoin')
            
        Returns:
            Dictionary with analysis results formatted for TTS
        """
        if not data or len(data) < 2:
            return self._create_fallback_analysis(crypto_name)
        
        # Get current and historical prices
        current = data[-1]  # Most recent data point
        start = data[0]     # Oldest data point in our range
        
        current_price = float(current['close'])
        start_price = float(start['close'])
        
        # Calculate price change
        price_change = current_price - start_price
        percentage_change = (price_change / start_price) * 100
        
        # Find high and low for the period
        high_price = max(float(point['high']) for point in data)
        low_price = min(float(point['low']) for point in data)
        
        # Calculate average volume
        volumes = [float(point['volume']) for point in data if point.get('volume')]
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        
        # Determine trend direction
        trend = self._calculate_trend(data)
        
        # Calculate momentum (price change in last 2 hours vs previous 6 hours)
        momentum = self._calculate_momentum(data)
        
        # Format all values for TTS
        analysis = {
            'crypto_name': crypto_name,
            'current_price': self._format_price_for_tts(current_price),
            'current_price_raw': current_price,
            'price_change': self._format_price_change_for_tts(price_change),
            'percentage_change': self._format_percentage_for_tts(percentage_change),
            'percentage_change_raw': percentage_change,
            'high_price': self._format_price_for_tts(high_price),
            'low_price': self._format_price_for_tts(low_price),
            'volume_analysis': self._format_volume_for_tts(avg_volume),
            'trend_direction': trend,
            'momentum': momentum,
            'period_hours': len(data),
            'timestamp': datetime.now().strftime('%B %d, %Y at %I:%M %p')
        }
        
        print(f"[CryptoAnalyzer] Analysis complete for {crypto_name}: {analysis['current_price']}, {analysis['percentage_change']} change")
        
        return analysis
    
    def _calculate_trend(self, data: List[Dict]) -> str:
        """
        Calculate the overall trend direction based on price movement.
        """
        if len(data) < 3:
            return "sideways"
        
        # Use simple moving average approach
        # Compare first half average vs second half average
        mid_point = len(data) // 2
        first_half_avg = sum(float(point['close']) for point in data[:mid_point]) / mid_point
        second_half_avg = sum(float(point['close']) for point in data[mid_point:]) / (len(data) - mid_point)
        
        change_threshold = 0.01  # 1% threshold for trend determination
        percentage_change = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        
        if percentage_change > change_threshold:
            return "up"
        elif percentage_change < -change_threshold:
            return "down"
        else:
            return "sideways"
    
    def _calculate_momentum(self, data: List[Dict]) -> str:
        """
        Calculate price momentum for the recent period.
        """
        if len(data) < 4:
            return "neutral"
        
        # Compare last 2 hours vs previous hours
        recent_points = data[-2:]  # Last 2 hours
        earlier_points = data[:-2]  # Previous hours
        
        recent_avg = sum(float(point['close']) for point in recent_points) / len(recent_points)
        earlier_avg = sum(float(point['close']) for point in earlier_points) / len(earlier_points)
        
        momentum_change = ((recent_avg - earlier_avg) / earlier_avg) * 100
        
        if momentum_change > 1.0:
            return "accelerating upward"
        elif momentum_change < -1.0:
            return "accelerating downward"
        elif momentum_change > 0.2:
            return "positive"
        elif momentum_change < -0.2:
            return "negative"
        else:
            return "neutral"
    
    def _format_price_for_tts(self, price: float) -> str:
        """
        Format price for text-to-speech pronunciation.
        Example: 45123.45 -> "forty-five thousand one hundred twenty-three dollars and forty-five cents"
        """
        if price >= 1000000:
            # For millions
            millions = price / 1000000
            if millions >= 10:
                return f"{millions:.0f} million dollars"
            else:
                return f"{millions:.1f} million dollars"
        elif price >= 1000:
            # For thousands
            thousands = price / 1000
            if thousands >= 10:
                return f"{thousands:.0f} thousand dollars"
            else:
                return f"{thousands:.1f} thousand dollars"
        elif price >= 100:
            # For hundreds
            return f"{price:.0f} dollars"
        elif price >= 1:
            # For single digits with cents
            return f"{price:.2f} dollars"
        else:
            # For cents
            cents = price * 100
            return f"{cents:.1f} cents"
    
    def _format_price_change_for_tts(self, change: float) -> str:
        """
        Format price change for TTS with appropriate sign.
        """
        if change > 0:
            return f"up {self._format_price_for_tts(abs(change))}"
        elif change < 0:
            return f"down {self._format_price_for_tts(abs(change))}"
        else:
            return "unchanged"
    
    def _format_percentage_for_tts(self, percentage: float) -> str:
        """
        Format percentage for TTS pronunciation.
        Example: 5.67 -> "up five point six seven percent"
        """
        if percentage > 0:
            if percentage >= 10:
                return f"up {percentage:.1f} percent"
            else:
                return f"up {percentage:.2f} percent"
        elif percentage < 0:
            abs_pct = abs(percentage)
            if abs_pct >= 10:
                return f"down {abs_pct:.1f} percent"
            else:
                return f"down {abs_pct:.2f} percent"
        else:
            return "unchanged"
    
    def _format_volume_for_tts(self, volume: float) -> str:
        """
        Format volume for TTS pronunciation.
        """
        if volume == 0:
            return "no volume data available"
        elif volume >= 1000000000:
            billions = volume / 1000000000
            return f"{billions:.1f} billion in average hourly volume"
        elif volume >= 1000000:
            millions = volume / 1000000
            return f"{millions:.1f} million in average hourly volume"
        elif volume >= 1000:
            thousands = volume / 1000
            return f"{thousands:.0f} thousand in average hourly volume"
        else:
            return f"{volume:.0f} in average hourly volume"
    
    def _create_fallback_analysis(self, crypto_name: str) -> Dict:
        """
        Create fallback analysis when data is insufficient.
        """
        return {
            'crypto_name': crypto_name,
            'current_price': "price data unavailable",
            'current_price_raw': 0,
            'price_change': "change data unavailable",
            'percentage_change': "percentage change unavailable",
            'percentage_change_raw': 0,
            'high_price': "high unavailable",
            'low_price': "low unavailable", 
            'volume_analysis': "volume data unavailable",
            'trend_direction': "unknown",
            'momentum': "unknown",
            'period_hours': 0,
            'timestamp': datetime.now().strftime('%B %d, %Y at %I:%M %p')
        }
    
    async def get_all_crypto_analysis(self, hours: int = 8) -> Dict[str, Dict]:
        """
        Get analysis for all supported cryptocurrencies.
        
        Args:
            hours: Number of hours of historical data to analyze
            
        Returns:
            Dictionary with crypto symbols as keys and analysis as values
        """
        print(f"[CryptoAnalyzer] Starting analysis for all cryptocurrencies ({hours} hours)")
        
        results = {}
        
        # Fetch data for all cryptos concurrently
        tasks = []
        for crypto_symbol, api_symbol in self.symbols.items():
            task = self.fetch_crypto_data(api_symbol, hours)
            tasks.append((crypto_symbol, task))
        
        # Execute all requests concurrently
        for crypto_symbol, task in tasks:
            try:
                data = await task
                crypto_name = self.crypto_names[crypto_symbol]
                analysis = self.analyze_price_data(data, crypto_name)
                results[crypto_symbol] = analysis
            except Exception as e:
                print(f"[CryptoAnalyzer] Error analyzing {crypto_symbol}: {str(e)}")
                results[crypto_symbol] = self._create_fallback_analysis(self.crypto_names[crypto_symbol])
        
        print(f"[CryptoAnalyzer] Completed analysis for {len(results)} cryptocurrencies")
        return results
    
    async def get_crypto_summary_for_briefing(self, hours: int = 8) -> str:
        """
        Generate a formatted crypto summary for use in market briefings.
        
        Args:
            hours: Number of hours of historical data to analyze
            
        Returns:
            TTS-formatted string suitable for audio briefing
        """
        print(f"[CryptoAnalyzer] Generating crypto summary for briefing")
        
        all_analysis = await self.get_all_crypto_analysis(hours)
        
        if not all_analysis:
            return "Cryptocurrency data is currently unavailable. Moving on to other market news."
        
        # Build summary text
        summary_parts = []
        summary_parts.append("In cryptocurrency markets,")
        
        for crypto_symbol in ['BTC', 'ETH', 'SOL']:
            if crypto_symbol in all_analysis:
                analysis = all_analysis[crypto_symbol]
                
                if analysis['current_price_raw'] > 0:  # Valid data
                    crypto_name = analysis['crypto_name']
                    current_price = analysis['current_price']
                    percentage_change = analysis['percentage_change']
                    trend = analysis['trend_direction']
                    
                    # Create natural sentence
                    summary_parts.append(
                        f"{crypto_name} is trading at {current_price}, {percentage_change} "
                        f"over the past {hours} hours with a {trend} trend."
                    )
                else:
                    # Fallback for unavailable data
                    crypto_name = analysis['crypto_name']
                    summary_parts.append(f"{crypto_name} pricing data is currently unavailable.")
        
        # Add overall market context if we have valid data
        valid_analyses = [a for a in all_analysis.values() if a['current_price_raw'] > 0]
        if len(valid_analyses) >= 2:
            positive_moves = sum(1 for a in valid_analyses if a['percentage_change_raw'] > 0)
            if positive_moves == len(valid_analyses):
                summary_parts.append("The crypto market is showing broad strength across major coins.")
            elif positive_moves == 0:
                summary_parts.append("Cryptocurrency markets are under pressure with widespread declines.")
            else:
                summary_parts.append("Cryptocurrency markets are showing mixed performance.")
        
        return " ".join(summary_parts)
    
    async def get_individual_crypto_analysis(self, crypto_symbol: str, hours: int = 8) -> Dict:
        """
        Get detailed analysis for a single cryptocurrency.
        
        Args:
            crypto_symbol: 'BTC', 'ETH', or 'SOL'
            hours: Number of hours of historical data to analyze
            
        Returns:
            Analysis dictionary for the specified crypto
        """
        if crypto_symbol not in self.symbols:
            raise ValueError(f"Unsupported crypto symbol: {crypto_symbol}. Supported: {list(self.symbols.keys())}")
        
        print(f"[CryptoAnalyzer] Getting detailed analysis for {crypto_symbol}")
        
        api_symbol = self.symbols[crypto_symbol]
        crypto_name = self.crypto_names[crypto_symbol]
        
        data = await self.fetch_crypto_data(api_symbol, hours)
        analysis = self.analyze_price_data(data, crypto_name)
        
        return analysis

# Example usage and testing functions
async def test_crypto_analyzer():
    """
    Test function to verify the crypto analyzer works correctly.
    """
    print("Testing CryptoAnalyzer...")
    
    analyzer = CryptoAnalyzer()
    
    # Test individual crypto analysis
    try:
        btc_analysis = await analyzer.get_individual_crypto_analysis('BTC', 8)
        print(f"BTC Analysis: {btc_analysis}")
    except Exception as e:
        print(f"BTC Analysis failed: {e}")
    
    # Test all crypto analysis
    try:
        all_analysis = await analyzer.get_all_crypto_analysis(8)
        print(f"All Crypto Analysis: {all_analysis}")
    except Exception as e:
        print(f"All Crypto Analysis failed: {e}")
    
    # Test briefing summary
    try:
        summary = await analyzer.get_crypto_summary_for_briefing(8)
        print(f"Briefing Summary: {summary}")
    except Exception as e:
        print(f"Briefing Summary failed: {e}")

if __name__ == "__main__":
    # Run test when script is executed directly
    asyncio.run(test_crypto_analyzer())