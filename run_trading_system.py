#!/usr/bin/env python3
"""
High-Frequency Arbitrage Trading System Runner
Main entry point for the trading system
"""

import asyncio
import signal
import sys
import logging
from datetime import datetime
from config import Config
from arbitrage_trading_system import TradingSystem

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Setup logging configuration"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if Config.LOG_TO_FILE:
        file_handler = RotatingFileHandler(
            Config.LOG_FILENAME,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

class TradingSystemRunner:
    """Main runner for the trading system"""
    
    def __init__(self):
        self.trading_system = None
        self.shutdown_requested = False
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        
    async def run(self):
        """Main execution loop"""
        # Validate configuration
        if not Config.validate_config():
            logging.error("Configuration validation failed")
            return False
        
        # Get trading configuration
        config = Config.get_trading_config()
        
        # Initialize trading system
        self.trading_system = TradingSystem(config)
        
        try:
            logging.info("="*60)
            logging.info("HIGH-FREQUENCY ARBITRAGE TRADING SYSTEM")
            logging.info("="*60)
            logging.info(f"Start time: {datetime.now()}")
            logging.info(f"Min profit threshold: {config.min_profit_threshold}%")
            logging.info(f"Min confidence score: {config.min_confidence_score}")
            logging.info(f"Max position size: ${config.max_position_size}")
            logging.info(f"Scan interval: {config.scan_interval}s")
            logging.info(f"Max idle time: {config.max_idle_minutes} minutes")
            logging.info(f"Trading pairs: {len(config.trading_pairs)} pairs")
            logging.info("="*60)
            
            # Initialize the trading system
            await self.trading_system.initialize()
            
            # Start the continuous trading loop
            await self.trading_system.run_continuous_trading()
            
            return True
            
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt received, shutting down...")
            return True
        except Exception as e:
            logging.error(f"Critical system error: {e}", exc_info=True)
            return False
        finally:
            if self.trading_system:
                await self.trading_system.shutdown()
            logging.info("Trading system shutdown complete")
            logging.info(f"End time: {datetime.now()}")

async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    
    # Create and configure runner
    runner = TradingSystemRunner()
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, runner.signal_handler)
    signal.signal(signal.SIGTERM, runner.signal_handler)
    
    # Run the system
    success = await runner.run()
    
    if success:
        logging.info("Trading system completed successfully")
        sys.exit(0)
    else:
        logging.error("Trading system failed")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Failed to start trading system: {e}")
        sys.exit(1)