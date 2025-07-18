#!/usr/bin/env python3
"""
Trading System Test and Simulation
Tests the arbitrage trading system with simulated data
"""

import asyncio
import random
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
from unittest.mock import AsyncMock, Mock
import json

from arbitrage_trading_system import (
    TradingSystem, TradingConfig, ArbitrageOpportunity,
    KrakenAPI, MarketDataManager, OpportunityScanner,
    RiskManager, TradeExecutor
)

# Configure test logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockKrakenAPI:
    """Mock Kraken API for testing"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = None
        self.trade_count = 0
        
    async def __aenter__(self):
        self.session = Mock()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def get_ticker(self, pairs: List[str]) -> Dict:
        """Generate mock ticker data"""
        ticker_data = {}
        
        base_prices = {
            'XBTUSD': 43000,
            'ETHUSD': 2500,
            'ADAUSD': 0.5,
            'DOTUSD': 7.0,
            'SOLUSD': 65,
            'LINKUSD': 15,
            'LTCUSD': 75,
            'XRPUSD': 0.6,
            'AVAXUSD': 38,
            'MATICUSD': 0.8
        }
        
        for pair in pairs:
            if pair in base_prices:
                base_price = base_prices[pair]
                # Add some randomness
                price_variation = random.uniform(-0.02, 0.02)  # ±2%
                current_price = base_price * (1 + price_variation)
                
                # Create realistic bid-ask spread
                spread_pct = random.uniform(0.001, 0.005)  # 0.1% to 0.5%
                spread = current_price * spread_pct
                
                bid = current_price - spread / 2
                ask = current_price + spread / 2
                
                # Generate volume
                volume = random.uniform(100, 10000)
                
                ticker_data[pair] = {
                    'c': [str(current_price), '1'],  # Last trade price
                    'v': [str(volume/2), str(volume)],  # Volume (today, 24h)
                    'b': [str(bid), '1'],  # Best bid
                    'a': [str(ask), '1'],  # Best ask
                    'h': [str(current_price * 1.01), str(current_price * 1.02)],  # High
                    'l': [str(current_price * 0.99), str(current_price * 0.98)]   # Low
                }
        
        return ticker_data
    
    async def get_order_book(self, pair: str, count: int = 10) -> Dict:
        """Generate mock order book"""
        base_price = 43000 if 'XBT' in pair else 2500
        
        bids = []
        asks = []
        
        for i in range(count):
            bid_price = base_price * (1 - (i + 1) * 0.0001)
            ask_price = base_price * (1 + (i + 1) * 0.0001)
            volume = random.uniform(0.1, 5.0)
            
            bids.append([str(bid_price), str(volume), str(int(datetime.now().timestamp()))])
            asks.append([str(ask_price), str(volume), str(int(datetime.now().timestamp()))])
        
        return {
            pair: {
                'bids': bids,
                'asks': asks
            }
        }
    
    async def get_account_balance(self) -> Dict:
        """Return mock account balance"""
        return {
            'ZUSD': '10000.0000',  # $10,000 USD
            'XXBT': '0.1000',      # 0.1 BTC
            'XETH': '2.0000'       # 2 ETH
        }
    
    async def place_order(self, pair: str, type_: str, ordertype: str, 
                         volume: str, price: str = None) -> Dict:
        """Mock order placement"""
        self.trade_count += 1
        
        # Simulate occasional order failures
        if random.random() < 0.05:  # 5% failure rate
            return {'error': ['Order placement failed']}
        
        return {
            'txid': [f'TEST-{self.trade_count:06d}'],
            'descr': {
                'order': f'{type_} {volume} {pair} @ {price or "market"}'
            }
        }

class TestTradingSystem:
    """Test harness for the trading system"""
    
    def __init__(self):
        self.config = TradingConfig(
            kraken_api_key="TEST_API_KEY",
            kraken_api_secret="TEST_API_SECRET",
            min_profit_threshold=Decimal('0.2'),  # Lower threshold for testing
            min_confidence_score=0.5,  # Lower confidence for testing
            max_position_size=Decimal('100'),
            min_liquidity=Decimal('50'),
            max_daily_trades=20,
            scan_interval=2.0,  # Slower for testing
            max_idle_minutes=2,  # Shorter for testing
            trading_pairs=['XBTUSD', 'ETHUSD', 'ADAUSD']  # Fewer pairs for testing
        )
        
    async def test_market_data_collection(self):
        """Test market data collection and analysis"""
        logger.info("Testing market data collection...")
        
        mock_api = MockKrakenAPI("test", "test")
        await mock_api.__aenter__()
        
        market_manager = MarketDataManager(mock_api)
        
        # Test data collection
        for i in range(5):
            data = await market_manager.update_market_data(self.config.trading_pairs)
            logger.info(f"Iteration {i+1}: Collected data for {len(data)} pairs")
            
            # Test momentum calculation
            for pair in data:
                momentum = market_manager.calculate_momentum(pair)
                logger.info(f"{pair} momentum: {momentum:.2f}%")
            
            await asyncio.sleep(1)
        
        await mock_api.__aexit__(None, None, None)
        logger.info("Market data collection test completed")
    
    async def test_opportunity_scanning(self):
        """Test opportunity scanning and confidence scoring"""
        logger.info("Testing opportunity scanning...")
        
        mock_api = MockKrakenAPI("test", "test")
        await mock_api.__aenter__()
        
        market_manager = MarketDataManager(mock_api)
        scanner = OpportunityScanner(market_manager, self.config)
        
        # Collect some market data
        market_data = await market_manager.update_market_data(self.config.trading_pairs)
        
        # Artificially create profitable spreads for testing
        for pair, data in market_data.items():
            # Increase spread to create arbitrage opportunity
            original_ask = data['ask']
            data['ask'] = original_ask * Decimal('1.01')  # 1% higher ask
            data['spread'] = data['ask'] - data['bid']
        
        # Scan for opportunities
        opportunities = await scanner.scan_for_opportunities(market_data)
        
        logger.info(f"Found {len(opportunities)} opportunities:")
        for opp in opportunities:
            logger.info(f"  {opp.pair}: {opp.profit_pct:.3f}% profit, "
                       f"confidence: {opp.confidence_score:.3f}")
        
        await mock_api.__aexit__(None, None, None)
        logger.info("Opportunity scanning test completed")
    
    async def test_risk_management(self):
        """Test risk management and position sizing"""
        logger.info("Testing risk management...")
        
        risk_manager = RiskManager(self.config)
        
        # Create test opportunity
        opportunity = ArbitrageOpportunity(
            pair="XBTUSD",
            buy_exchange="Kraken",
            sell_exchange="Kraken",
            buy_price=Decimal('43000'),
            sell_price=Decimal('43150'),
            profit_pct=Decimal('0.35'),
            confidence_score=0.8,
            volume_available=Decimal('1000'),
            timestamp=datetime.now()
        )
        
        # Test trade approval
        can_trade, reason = risk_manager.can_trade(opportunity)
        logger.info(f"Can trade: {can_trade}, Reason: {reason}")
        
        # Test position sizing
        balance = Decimal('10000')
        position_size = risk_manager.calculate_position_size(opportunity, balance)
        logger.info(f"Calculated position size: ${position_size}")
        
        # Simulate multiple trades to test daily limits
        for i in range(5):
            risk_manager.daily_trades += 1
            risk_manager.daily_pnl += Decimal('10')
            logger.info(f"Trade {i+1}: Daily trades: {risk_manager.daily_trades}, "
                       f"Daily P&L: ${risk_manager.daily_pnl}")
        
        logger.info("Risk management test completed")
    
    async def test_trade_execution(self):
        """Test trade execution logic"""
        logger.info("Testing trade execution...")
        
        mock_api = MockKrakenAPI("test", "test")
        await mock_api.__aenter__()
        
        risk_manager = RiskManager(self.config)
        executor = TradeExecutor(mock_api, risk_manager)
        
        # Create test opportunity
        opportunity = ArbitrageOpportunity(
            pair="XBTUSD",
            buy_exchange="Kraken",
            sell_exchange="Kraken",
            buy_price=Decimal('43000'),
            sell_price=Decimal('43150'),
            profit_pct=Decimal('0.35'),
            confidence_score=0.8,
            volume_available=Decimal('1000'),
            timestamp=datetime.now()
        )
        
        # Execute trade
        result = await executor.execute_arbitrage(opportunity)
        
        logger.info(f"Trade execution result:")
        logger.info(f"  Success: {result['success']}")
        if result['success']:
            logger.info(f"  Buy Order ID: {result.get('buy_order_id')}")
            logger.info(f"  Sell Order ID: {result.get('sell_order_id')}")
            logger.info(f"  Position Size: ${result.get('position_size')}")
            logger.info(f"  Estimated Profit: ${result.get('estimated_profit')}")
        else:
            logger.info(f"  Reason: {result['reason']}")
        
        await mock_api.__aexit__(None, None, None)
        logger.info("Trade execution test completed")
    
    async def test_full_system_simulation(self):
        """Test the complete trading system in simulation mode"""
        logger.info("Starting full system simulation...")
        
        # Create trading system with mock API
        trading_system = TradingSystem(self.config)
        
        # Replace the Kraken API with mock
        trading_system.kraken = MockKrakenAPI(
            self.config.kraken_api_key, 
            self.config.kraken_api_secret
        )
        await trading_system.kraken.__aenter__()
        
        # Initialize other components
        trading_system.market_data_manager = MarketDataManager(trading_system.kraken)
        trading_system.opportunity_scanner = OpportunityScanner(
            trading_system.market_data_manager, self.config
        )
        trading_system.risk_manager = RiskManager(self.config)
        trading_system.trade_executor = TradeExecutor(
            trading_system.kraken, trading_system.risk_manager
        )
        
        trading_system.system_status = "active"
        
        # Run simulation for a short time
        logger.info("Running trading simulation for 30 seconds...")
        start_time = datetime.now()
        
        try:
            while (datetime.now() - start_time).total_seconds() < 30:
                trade_executed, reasons = await trading_system.trading_cycle()
                
                if trade_executed:
                    logger.info(f"✅ Trade executed! Total trades: {trading_system.trade_count}")
                else:
                    logger.info(f"❌ No trade: {reasons}")
                
                await asyncio.sleep(self.config.scan_interval)
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            await trading_system.kraken.__aexit__(None, None, None)
        
        logger.info(f"Simulation completed. Total trades: {trading_system.trade_count}")
        logger.info(f"Total P&L: ${trading_system.total_pnl}")
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("="*60)
        logger.info("ARBITRAGE TRADING SYSTEM TESTS")
        logger.info("="*60)
        
        tests = [
            self.test_market_data_collection,
            self.test_opportunity_scanning,
            self.test_risk_management,
            self.test_trade_execution,
            self.test_full_system_simulation
        ]
        
        for test in tests:
            try:
                await test()
                logger.info(f"✅ {test.__name__} PASSED")
            except Exception as e:
                logger.error(f"❌ {test.__name__} FAILED: {e}")
            
            logger.info("-" * 40)
        
        logger.info("All tests completed!")

async def main():
    """Main test runner"""
    test_system = TestTradingSystem()
    await test_system.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())