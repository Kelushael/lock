#!/usr/bin/env python3
"""
High-Frequency Arbitrage Trading System
Real-time market scanning, evaluation, and automated execution
"""

import asyncio
import time
import logging
import json
import hashlib
import hmac
import base64
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_DOWN
import aiohttp
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Represents a potential arbitrage opportunity"""
    pair: str
    buy_exchange: str
    sell_exchange: str
    buy_price: Decimal
    sell_price: Decimal
    profit_pct: Decimal
    confidence_score: float
    volume_available: Decimal
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'pair': self.pair,
            'buy_exchange': self.buy_exchange,
            'sell_exchange': self.sell_exchange,
            'buy_price': str(self.buy_price),
            'sell_price': str(self.sell_price),
            'profit_pct': str(self.profit_pct),
            'confidence_score': self.confidence_score,
            'volume_available': str(self.volume_available),
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class TradingConfig:
    """Trading system configuration"""
    # API credentials
    kraken_api_key: str
    kraken_api_secret: str
    
    # Trading parameters
    min_profit_threshold: Decimal = Decimal('0.5')  # 0.5% minimum profit
    min_confidence_score: float = 0.75  # Minimum confidence score
    max_position_size: Decimal = Decimal('1000')  # Max USD per trade
    min_liquidity: Decimal = Decimal('500')  # Minimum liquidity required
    
    # Risk management
    max_daily_trades: int = 100
    max_daily_loss: Decimal = Decimal('500')
    stop_loss_pct: Decimal = Decimal('2.0')
    
    # System parameters
    scan_interval: float = 0.5  # Seconds between scans
    max_idle_minutes: int = 10  # Max minutes without trades
    trading_pairs: List[str] = None
    
    def __post_init__(self):
        if self.trading_pairs is None:
            self.trading_pairs = [
                'XBTUSD', 'ETHUSD', 'ADAUSD', 'DOTUSD', 'SOLUSD',
                'LINKUSD', 'LTCUSD', 'XRPUSD', 'AVAXUSD', 'MATICUSD'
            ]

class KrakenAPI:
    """Kraken API client for trading operations"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.kraken.com"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_kraken_signature(self, urlpath: str, data: Dict, secret: str) -> str:
        """Generate Kraken API signature"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        return base64.b64encode(mac.digest()).decode()
    
    async def public_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a public API request"""
        url = f"{self.base_url}/0/public/{endpoint}"
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                if data.get('error'):
                    logger.error(f"Kraken API error: {data['error']}")
                    return {}
                return data.get('result', {})
        except Exception as e:
            logger.error(f"Public request failed: {e}")
            return {}
    
    async def private_request(self, endpoint: str, data: Dict = None) -> Dict:
        """Make a private API request"""
        if data is None:
            data = {}
        
        data['nonce'] = str(int(1000 * time.time()))
        urlpath = f"/0/private/{endpoint}"
        
        headers = {
            'API-Key': self.api_key,
            'API-Sign': self._get_kraken_signature(urlpath, data, self.api_secret)
        }
        
        url = f"{self.base_url}{urlpath}"
        try:
            async with self.session.post(url, headers=headers, data=data) as response:
                result = await response.json()
                if result.get('error'):
                    logger.error(f"Kraken private API error: {result['error']}")
                    return {}
                return result.get('result', {})
        except Exception as e:
            logger.error(f"Private request failed: {e}")
            return {}
    
    async def get_ticker(self, pairs: List[str]) -> Dict:
        """Get ticker information for trading pairs"""
        pair_str = ','.join(pairs)
        return await self.public_request('Ticker', {'pair': pair_str})
    
    async def get_order_book(self, pair: str, count: int = 10) -> Dict:
        """Get order book for a specific pair"""
        return await self.public_request('Depth', {'pair': pair, 'count': count})
    
    async def get_account_balance(self) -> Dict:
        """Get account balance"""
        return await self.private_request('Balance')
    
    async def place_order(self, pair: str, type_: str, ordertype: str, 
                         volume: str, price: str = None) -> Dict:
        """Place a trading order"""
        data = {
            'pair': pair,
            'type': type_,  # buy or sell
            'ordertype': ordertype,  # market, limit, etc.
            'volume': volume
        }
        
        if price:
            data['price'] = price
            
        return await self.private_request('AddOrder', data)

class MarketDataManager:
    """Manages real-time market data collection and analysis"""
    
    def __init__(self, kraken_api: KrakenAPI):
        self.kraken = kraken_api
        self.price_history = {}
        self.volume_history = {}
        self.last_update = {}
        
    async def update_market_data(self, pairs: List[str]) -> Dict:
        """Update market data for given pairs"""
        ticker_data = await self.kraken.get_ticker(pairs)
        current_time = datetime.now()
        
        market_data = {}
        for pair in pairs:
            if pair in ticker_data:
                data = ticker_data[pair]
                price = Decimal(data['c'][0])  # Last trade price
                volume = Decimal(data['v'][1])  # 24h volume
                bid = Decimal(data['b'][0])  # Best bid
                ask = Decimal(data['a'][0])  # Best ask
                
                # Store historical data
                if pair not in self.price_history:
                    self.price_history[pair] = []
                    self.volume_history[pair] = []
                
                self.price_history[pair].append((current_time, price))
                self.volume_history[pair].append((current_time, volume))
                
                # Keep only last 100 data points
                self.price_history[pair] = self.price_history[pair][-100:]
                self.volume_history[pair] = self.volume_history[pair][-100:]
                
                market_data[pair] = {
                    'price': price,
                    'bid': bid,
                    'ask': ask,
                    'volume': volume,
                    'spread': ask - bid,
                    'timestamp': current_time
                }
                
        return market_data
    
    def calculate_momentum(self, pair: str, minutes: int = 5) -> float:
        """Calculate price momentum over specified timeframe"""
        if pair not in self.price_history or len(self.price_history[pair]) < 2:
            return 0.0
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_prices = [
            (t, p) for t, p in self.price_history[pair] 
            if t >= cutoff_time
        ]
        
        if len(recent_prices) < 2:
            return 0.0
        
        start_price = recent_prices[0][1]
        end_price = recent_prices[-1][1]
        
        return float((end_price - start_price) / start_price * 100)
    
    def calculate_volatility(self, pair: str, minutes: int = 15) -> float:
        """Calculate price volatility"""
        if pair not in self.price_history or len(self.price_history[pair]) < 5:
            return 0.0
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_prices = [
            float(p) for t, p in self.price_history[pair] 
            if t >= cutoff_time
        ]
        
        if len(recent_prices) < 5:
            return 0.0
        
        return float(np.std(recent_prices))

class OpportunityScanner:
    """Scans for arbitrage opportunities across different timeframes and conditions"""
    
    def __init__(self, market_data_manager: MarketDataManager, config: TradingConfig):
        self.market_data = market_data_manager
        self.config = config
        
    def calculate_confidence_score(self, pair: str, profit_pct: Decimal, 
                                 volume: Decimal) -> float:
        """Calculate confidence score for an opportunity"""
        score = 0.0
        
        # Base score from profit percentage
        score += min(float(profit_pct) * 10, 40)  # Max 40 points from profit
        
        # Volume score
        volume_score = min(float(volume) / 1000 * 20, 20)  # Max 20 points
        score += volume_score
        
        # Momentum score
        momentum = self.market_data.calculate_momentum(pair)
        momentum_score = min(abs(momentum) * 2, 20)  # Max 20 points
        score += momentum_score
        
        # Volatility penalty
        volatility = self.market_data.calculate_volatility(pair)
        volatility_penalty = min(volatility * 2, 15)  # Max 15 point penalty
        score -= volatility_penalty
        
        # Historical success rate (placeholder - would need trade history)
        score += 5  # Base historical score
        
        return max(0, min(score / 100, 1.0))  # Normalize to 0-1
    
    async def scan_for_opportunities(self, market_data: Dict) -> List[ArbitrageOpportunity]:
        """Scan market data for arbitrage opportunities"""
        opportunities = []
        
        for pair, data in market_data.items():
            # For this example, we'll look for spread-based opportunities
            # In a real system, you'd compare across multiple exchanges
            
            bid = data['bid']
            ask = data['ask']
            spread = data['spread']
            volume = data['volume']
            
            # Calculate potential profit from spread
            profit_pct = (spread / ask) * 100
            
            if profit_pct >= self.config.min_profit_threshold:
                confidence = self.calculate_confidence_score(pair, profit_pct, volume)
                
                if confidence >= self.config.min_confidence_score:
                    opportunity = ArbitrageOpportunity(
                        pair=pair,
                        buy_exchange="Kraken",
                        sell_exchange="Kraken",  # Same exchange spread arbitrage
                        buy_price=bid,
                        sell_price=ask,
                        profit_pct=profit_pct,
                        confidence_score=confidence,
                        volume_available=min(volume, self.config.max_position_size),
                        timestamp=datetime.now()
                    )
                    opportunities.append(opportunity)
        
        return sorted(opportunities, key=lambda x: x.confidence_score, reverse=True)

class RiskManager:
    """Manages trading risks and position sizing"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.daily_trades = 0
        self.daily_pnl = Decimal('0')
        self.last_reset = datetime.now().date()
        
    def reset_daily_counters(self):
        """Reset daily counters if new day"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_trades = 0
            self.daily_pnl = Decimal('0')
            self.last_reset = today
    
    def can_trade(self, opportunity: ArbitrageOpportunity) -> Tuple[bool, str]:
        """Check if we can execute this trade"""
        self.reset_daily_counters()
        
        # Check daily trade limit
        if self.daily_trades >= self.config.max_daily_trades:
            return False, "Daily trade limit reached"
        
        # Check daily loss limit
        if self.daily_pnl <= -self.config.max_daily_loss:
            return False, "Daily loss limit reached"
        
        # Check minimum liquidity
        if opportunity.volume_available < self.config.min_liquidity:
            return False, f"Insufficient liquidity: {opportunity.volume_available}"
        
        # Check confidence threshold
        if opportunity.confidence_score < self.config.min_confidence_score:
            return False, f"Low confidence score: {opportunity.confidence_score}"
        
        return True, "Trade approved"
    
    def calculate_position_size(self, opportunity: ArbitrageOpportunity, 
                              available_balance: Decimal) -> Decimal:
        """Calculate optimal position size"""
        # Base position size on available balance and max position size
        max_size = min(
            available_balance * Decimal('0.1'),  # Max 10% of balance per trade
            self.config.max_position_size,
            opportunity.volume_available
        )
        
        # Adjust based on confidence score
        confidence_multiplier = Decimal(str(opportunity.confidence_score))
        position_size = max_size * confidence_multiplier
        
        return position_size.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)

class TradeExecutor:
    """Executes trades and manages order flow"""
    
    def __init__(self, kraken_api: KrakenAPI, risk_manager: RiskManager):
        self.kraken = kraken_api
        self.risk_manager = risk_manager
        
    async def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> Dict:
        """Execute an arbitrage trade"""
        # Check if we can trade
        can_trade, reason = self.risk_manager.can_trade(opportunity)
        if not can_trade:
            return {
                'success': False,
                'reason': reason,
                'opportunity': opportunity.to_dict()
            }
        
        # Get account balance
        balance = await self.kraken.get_account_balance()
        if not balance:
            return {
                'success': False,
                'reason': "Failed to get account balance",
                'opportunity': opportunity.to_dict()
            }
        
        # Calculate position size
        usd_balance = Decimal(balance.get('ZUSD', '0'))
        position_size = self.risk_manager.calculate_position_size(
            opportunity, usd_balance
        )
        
        if position_size <= 0:
            return {
                'success': False,
                'reason': "Calculated position size is zero",
                'opportunity': opportunity.to_dict()
            }
        
        # Execute the trade (simplified for spread arbitrage)
        try:
            # Place buy order at bid
            buy_order = await self.kraken.place_order(
                pair=opportunity.pair,
                type_='buy',
                ordertype='limit',
                volume=str(position_size / opportunity.buy_price),
                price=str(opportunity.buy_price)
            )
            
            if not buy_order or 'txid' not in buy_order:
                return {
                    'success': False,
                    'reason': "Failed to place buy order",
                    'opportunity': opportunity.to_dict()
                }
            
            # Place sell order at ask
            sell_order = await self.kraken.place_order(
                pair=opportunity.pair,
                type_='sell',
                ordertype='limit',
                volume=str(position_size / opportunity.sell_price),
                price=str(opportunity.sell_price)
            )
            
            if not sell_order or 'txid' not in sell_order:
                return {
                    'success': False,
                    'reason': "Failed to place sell order",
                    'opportunity': opportunity.to_dict(),
                    'buy_order_id': buy_order.get('txid')
                }
            
            # Update risk manager
            self.risk_manager.daily_trades += 1
            estimated_profit = position_size * opportunity.profit_pct / 100
            self.risk_manager.daily_pnl += estimated_profit
            
            return {
                'success': True,
                'buy_order_id': buy_order['txid'],
                'sell_order_id': sell_order['txid'],
                'position_size': str(position_size),
                'estimated_profit': str(estimated_profit),
                'opportunity': opportunity.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return {
                'success': False,
                'reason': f"Execution error: {str(e)}",
                'opportunity': opportunity.to_dict()
            }

class TradingSystem:
    """Main trading system orchestrator"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.kraken = None
        self.market_data_manager = None
        self.opportunity_scanner = None
        self.risk_manager = None
        self.trade_executor = None
        
        self.last_trade_time = datetime.now()
        self.system_status = "initializing"
        self.trade_count = 0
        self.total_pnl = Decimal('0')
        
    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing trading system...")
        
        self.kraken = KrakenAPI(self.config.kraken_api_key, self.config.kraken_api_secret)
        await self.kraken.__aenter__()
        
        self.market_data_manager = MarketDataManager(self.kraken)
        self.opportunity_scanner = OpportunityScanner(self.market_data_manager, self.config)
        self.risk_manager = RiskManager(self.config)
        self.trade_executor = TradeExecutor(self.kraken, self.risk_manager)
        
        self.system_status = "active"
        logger.info("Trading system initialized successfully")
    
    async def shutdown(self):
        """Shutdown system gracefully"""
        logger.info("Shutting down trading system...")
        self.system_status = "shutting_down"
        
        if self.kraken:
            await self.kraken.__aexit__(None, None, None)
        
        logger.info("Trading system shutdown complete")
    
    def check_idle_timeout(self) -> bool:
        """Check if system has been idle too long"""
        idle_time = datetime.now() - self.last_trade_time
        return idle_time.total_seconds() > (self.config.max_idle_minutes * 60)
    
    def log_system_status(self, opportunities: List[ArbitrageOpportunity], 
                         reasons: List[str]):
        """Log current system status and performance"""
        logger.info(f"System Status: {self.system_status}")
        logger.info(f"Trades executed: {self.trade_count}")
        logger.info(f"Total P&L: {self.total_pnl}")
        logger.info(f"Opportunities found: {len(opportunities)}")
        logger.info(f"Daily trades: {self.risk_manager.daily_trades}")
        logger.info(f"Daily P&L: {self.risk_manager.daily_pnl}")
        
        if reasons:
            logger.info(f"No-trade reasons: {reasons}")
    
    async def trading_cycle(self) -> Tuple[bool, List[str]]:
        """Execute one complete trading cycle"""
        reasons = []
        
        try:
            # Update market data
            market_data = await self.market_data_manager.update_market_data(
                self.config.trading_pairs
            )
            
            if not market_data:
                reasons.append("Failed to retrieve market data")
                return False, reasons
            
            # Scan for opportunities
            opportunities = await self.opportunity_scanner.scan_for_opportunities(market_data)
            
            if not opportunities:
                reasons.append("No profitable opportunities found")
                return False, reasons
            
            # Execute the best opportunity
            best_opportunity = opportunities[0]
            
            result = await self.trade_executor.execute_arbitrage(best_opportunity)
            
            if result['success']:
                self.trade_count += 1
                self.last_trade_time = datetime.now()
                estimated_profit = Decimal(result['estimated_profit'])
                self.total_pnl += estimated_profit
                
                logger.info(f"Trade executed successfully!")
                logger.info(f"Pair: {best_opportunity.pair}")
                logger.info(f"Profit: {estimated_profit}")
                logger.info(f"Confidence: {best_opportunity.confidence_score}")
                
                return True, []
            else:
                reasons.append(result['reason'])
                return False, reasons
                
        except Exception as e:
            logger.error(f"Trading cycle error: {e}")
            reasons.append(f"System error: {str(e)}")
            return False, reasons
    
    async def run_continuous_trading(self):
        """Main continuous trading loop"""
        logger.info("Starting continuous trading loop...")
        
        while self.system_status == "active":
            cycle_start = time.time()
            
            # Execute trading cycle
            trade_executed, reasons = await self.trading_cycle()
            
            # Check for system interrupt conditions
            if self.check_idle_timeout() and not trade_executed:
                logger.warning(f"SYSTEM INTERRUPT: No trades for {self.config.max_idle_minutes} minutes")
                logger.warning(f"Last no-trade reasons: {reasons}")
                self.system_status = "interrupted"
                break
            
            # Log status periodically
            if self.trade_count % 10 == 0 or not trade_executed:
                opportunities = await self.opportunity_scanner.scan_for_opportunities(
                    await self.market_data_manager.update_market_data(self.config.trading_pairs)
                ) if trade_executed else []
                self.log_system_status(opportunities, reasons)
            
            # Maintain scan interval
            cycle_time = time.time() - cycle_start
            if cycle_time < self.config.scan_interval:
                await asyncio.sleep(self.config.scan_interval - cycle_time)
        
        logger.info("Continuous trading loop ended")

async def main():
    """Main entry point"""
    # Configuration
    config = TradingConfig(
        kraken_api_key="YOUR_API_KEY_HERE",  # Replace with actual API key
        kraken_api_secret="YOUR_API_SECRET_HERE",  # Replace with actual API secret
        min_profit_threshold=Decimal('0.3'),  # 0.3% minimum profit
        min_confidence_score=0.7,
        max_position_size=Decimal('500'),
        scan_interval=1.0,  # 1 second between scans
        max_idle_minutes=10
    )
    
    # Initialize and run trading system
    trading_system = TradingSystem(config)
    
    try:
        await trading_system.initialize()
        await trading_system.run_continuous_trading()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        await trading_system.shutdown()

if __name__ == "__main__":
    asyncio.run(main())