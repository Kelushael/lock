#!/usr/bin/env python3
"""
Trading System Configuration
Centralized configuration management for the arbitrage trading system
"""

import os
from decimal import Decimal
from typing import List

class Config:
    """Configuration class for trading system"""
    
    # API Configuration
    KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY', 'YOUR_API_KEY_HERE')
    KRAKEN_API_SECRET = os.getenv('KRAKEN_API_SECRET', 'YOUR_API_SECRET_HERE')
    
    # Trading Parameters
    MIN_PROFIT_THRESHOLD = Decimal('0.3')  # 0.3% minimum profit
    MIN_CONFIDENCE_SCORE = 0.7
    MAX_POSITION_SIZE = Decimal('500')  # Max USD per trade
    MIN_LIQUIDITY = Decimal('500')  # Minimum liquidity required
    
    # Risk Management
    MAX_DAILY_TRADES = 100
    MAX_DAILY_LOSS = Decimal('500')
    STOP_LOSS_PCT = Decimal('2.0')
    
    # System Parameters
    SCAN_INTERVAL = 1.0  # Seconds between scans
    MAX_IDLE_MINUTES = 10  # Max minutes without trades
    
    # Trading Pairs - High volume, liquid pairs
    TRADING_PAIRS = [
        'XBTUSD',   # Bitcoin
        'ETHUSD',   # Ethereum
        'ADAUSD',   # Cardano
        'DOTUSD',   # Polkadot
        'SOLUSD',   # Solana
        'LINKUSD',  # Chainlink
        'LTCUSD',   # Litecoin
        'XRPUSD',   # Ripple
        'AVAXUSD',  # Avalanche
        'MATICUSD', # Polygon
        'UNIUSD',   # Uniswap
        'ATOMUSD',  # Cosmos
        'ALGOUSD',  # Algorand
        'XLMUSD',   # Stellar
        'FILUSD'    # Filecoin
    ]
    
    # Advanced Configuration
    CONFIDENCE_WEIGHTS = {
        'profit_weight': 0.4,      # 40% weight on profit percentage
        'volume_weight': 0.2,      # 20% weight on volume
        'momentum_weight': 0.2,    # 20% weight on momentum
        'volatility_weight': 0.1,  # 10% penalty for volatility
        'spread_weight': 0.1       # 10% weight on spread consistency
    }
    
    # Risk Parameters
    MAX_PORTFOLIO_EXPOSURE = Decimal('0.2')  # Max 20% of balance in active trades
    POSITION_SIZE_MULTIPLIER = Decimal('0.1')  # 10% of balance per trade max
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_TO_FILE = True
    LOG_FILENAME = 'trading_system.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Performance Monitoring
    PERFORMANCE_WINDOW_MINUTES = 60  # Performance calculation window
    MIN_SUCCESS_RATE = 0.6  # Minimum 60% success rate required
    MAX_DRAWDOWN_PCT = Decimal('5.0')  # Max 5% drawdown before pause
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration parameters"""
        if cls.KRAKEN_API_KEY == 'YOUR_API_KEY_HERE':
            print("WARNING: Please set your Kraken API key")
            return False
            
        if cls.KRAKEN_API_SECRET == 'YOUR_API_SECRET_HERE':
            print("WARNING: Please set your Kraken API secret")
            return False
            
        if cls.MIN_PROFIT_THRESHOLD <= 0:
            print("ERROR: Minimum profit threshold must be positive")
            return False
            
        return True
    
    @classmethod
    def get_trading_config(cls):
        """Get TradingConfig object with current settings"""
        from arbitrage_trading_system import TradingConfig
        
        return TradingConfig(
            kraken_api_key=cls.KRAKEN_API_KEY,
            kraken_api_secret=cls.KRAKEN_API_SECRET,
            min_profit_threshold=cls.MIN_PROFIT_THRESHOLD,
            min_confidence_score=cls.MIN_CONFIDENCE_SCORE,
            max_position_size=cls.MAX_POSITION_SIZE,
            min_liquidity=cls.MIN_LIQUIDITY,
            max_daily_trades=cls.MAX_DAILY_TRADES,
            max_daily_loss=cls.MAX_DAILY_LOSS,
            stop_loss_pct=cls.STOP_LOSS_PCT,
            scan_interval=cls.SCAN_INTERVAL,
            max_idle_minutes=cls.MAX_IDLE_MINUTES,
            trading_pairs=cls.TRADING_PAIRS
        )