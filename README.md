# High-Frequency Arbitrage Trading System

A sophisticated, real-time arbitrage trading system designed for cryptocurrency markets. This system continuously scans market data, evaluates arbitrage opportunities, and executes trades automatically through the Kraken API.

## 🚀 Features

- **Real-time Market Scanning**: Continuous monitoring of multiple trading pairs
- **Intelligent Opportunity Detection**: Advanced algorithms to identify profitable arbitrage opportunities
- **Confidence Scoring**: Multi-factor confidence scoring system for trade quality assessment
- **Risk Management**: Comprehensive risk controls including daily limits, position sizing, and stop-losses
- **Automated Execution**: Direct integration with Kraken API for seamless trade execution
- **System Monitoring**: Built-in monitoring with automatic system interrupts for anomalies
- **Comprehensive Logging**: Detailed logging for analysis and debugging

## ⚠️ Important Disclaimer

**This trading system involves real financial risk. Use at your own discretion and never trade with money you cannot afford to lose. The authors are not responsible for any financial losses incurred through the use of this system.**

## 📋 Requirements

- Python 3.8+
- Kraken Pro account with API access
- Sufficient balance for trading operations
- Stable internet connection for real-time data

## 🛠️ Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd arbitrage-trading-system
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure API credentials**:
   - Set environment variables:
   ```bash
   export KRAKEN_API_KEY="your_kraken_api_key"
   export KRAKEN_API_SECRET="your_kraken_api_secret"
   ```
   - Or edit `config.py` directly (not recommended for production)

## ⚙️ Configuration

### Basic Configuration

Edit `config.py` to customize the trading parameters:

```python
# Trading Parameters
MIN_PROFIT_THRESHOLD = Decimal('0.3')  # 0.3% minimum profit
MIN_CONFIDENCE_SCORE = 0.7             # Minimum confidence score
MAX_POSITION_SIZE = Decimal('500')     # Max USD per trade
MIN_LIQUIDITY = Decimal('500')         # Minimum liquidity required

# Risk Management
MAX_DAILY_TRADES = 100                 # Maximum trades per day
MAX_DAILY_LOSS = Decimal('500')        # Maximum daily loss limit
STOP_LOSS_PCT = Decimal('2.0')         # Stop loss percentage

# System Parameters
SCAN_INTERVAL = 1.0                    # Seconds between scans
MAX_IDLE_MINUTES = 10                  # Max minutes without trades
```

### Trading Pairs

The system monitors these pairs by default:
- XBTUSD (Bitcoin)
- ETHUSD (Ethereum)
- ADAUSD (Cardano)
- DOTUSD (Polkadot)
- SOLUSD (Solana)
- And more...

You can customize the trading pairs in `config.py`.

## 🚀 Usage

### Running the Trading System

1. **Start the main trading system**:
```bash
python run_trading_system.py
```

2. **Test the system with simulation**:
```bash
python test_trading_system.py
```

### Command Line Options

The system supports graceful shutdown with Ctrl+C or system signals.

## 📊 System Architecture

### Core Components

1. **TradingSystem**: Main orchestrator that coordinates all components
2. **MarketDataManager**: Handles real-time market data collection and analysis
3. **OpportunityScanner**: Identifies and scores arbitrage opportunities
4. **RiskManager**: Manages risk controls and position sizing
5. **TradeExecutor**: Executes trades through the Kraken API
6. **KrakenAPI**: API client for Kraken exchange integration

### Data Flow

```
Market Data → Opportunity Scanning → Risk Assessment → Trade Execution
     ↓              ↓                    ↓               ↓
Price History → Confidence Score → Position Size → Order Placement
```

## 🔍 How It Works

### 1. Market Data Collection
- Fetches real-time ticker data for all configured trading pairs
- Maintains price history for momentum and volatility calculations
- Updates market data every scan interval (default: 1 second)

### 2. Opportunity Detection
- Analyzes bid-ask spreads for potential arbitrage opportunities
- Calculates profit percentages and compares against minimum thresholds
- Identifies trading opportunities that meet profitability criteria

### 3. Confidence Scoring
The system uses a multi-factor confidence scoring algorithm:
- **Profit Weight (40%)**: Higher profit percentage increases confidence
- **Volume Weight (20%)**: Higher volume increases confidence
- **Momentum Weight (20%)**: Price momentum affects confidence
- **Volatility Penalty (10%)**: High volatility decreases confidence
- **Spread Consistency (10%)**: Consistent spreads increase confidence

### 4. Risk Management
- Daily trade limits to prevent over-trading
- Daily loss limits for capital protection
- Position sizing based on account balance and confidence
- Minimum liquidity requirements
- Real-time risk assessment for each trade

### 5. Trade Execution
- Places simultaneous buy and sell orders to capture spreads
- Monitors order execution and handles failures gracefully
- Updates risk metrics after each trade
- Logs all trading activity for analysis

### 6. System Monitoring
- Automatic system interrupt if no trades for 10+ minutes without justification
- Comprehensive logging of all system activities
- Performance tracking and reporting

## 📈 Performance Monitoring

The system tracks several key metrics:

- **Trade Success Rate**: Percentage of successful trades
- **Daily P&L**: Profit and loss for the current day
- **Total P&L**: Cumulative profit and loss
- **Average Profit per Trade**: Mean profit across all trades
- **Risk-Adjusted Returns**: Returns adjusted for risk taken

## 🛡️ Risk Controls

### Built-in Safety Features

1. **Daily Limits**: Maximum trades and losses per day
2. **Position Sizing**: Automatic position sizing based on confidence and balance
3. **Minimum Thresholds**: Profit and liquidity minimums
4. **System Interrupts**: Automatic shutdown on anomalous behavior
5. **Error Handling**: Comprehensive error handling and recovery

### Risk Parameters

- Maximum 10% of balance per trade
- Maximum 20% portfolio exposure in active trades
- Automatic stop-loss at 2% adverse movement
- Daily loss limit of $500 (configurable)

## 📝 Logging

The system maintains detailed logs including:

- All market data updates
- Opportunity detection and scoring
- Risk assessment decisions
- Trade execution details
- System performance metrics
- Error conditions and recovery

Log files are automatically rotated to prevent excessive disk usage.

## 🧪 Testing

### Run the Test Suite

```bash
python test_trading_system.py
```

The test suite includes:
- Market data collection tests
- Opportunity scanning tests
- Risk management tests
- Trade execution simulation
- Full system integration tests

### Simulation Mode

The test system uses mock data to validate functionality without real trading:
- Simulated market data with realistic spreads
- Mock API responses for safe testing
- Comprehensive validation of all system components

## 📊 Expected Performance

### Typical Metrics (Simulated)

- **Profit per Trade**: 0.3% - 1.5%
- **Trades per Day**: 20-100 (depending on market conditions)
- **Success Rate**: 60-80%
- **Daily Returns**: 1-5% (highly variable)

**Note**: Actual performance will vary significantly based on market conditions, configuration, and execution timing.

## ⚠️ Risks and Limitations

### Market Risks
- Price movements during trade execution
- Liquidity changes between scan and execution
- Exchange downtime or API failures
- Network latency affecting execution timing

### Technical Risks
- API rate limiting
- System failures or crashes
- Configuration errors
- Internet connectivity issues

### Financial Risks
- Capital loss due to adverse price movements
- Transaction fees reducing profitability
- Slippage on large orders
- Exchange counterparty risk

## 🔧 Troubleshooting

### Common Issues

1. **API Authentication Errors**:
   - Verify API key and secret are correct
   - Check API permissions on Kraken account
   - Ensure API keys are properly set in environment

2. **No Opportunities Found**:
   - Check minimum profit threshold settings
   - Verify market data is being received
   - Review confidence score requirements

3. **Trade Execution Failures**:
   - Check account balance
   - Verify trading permissions
   - Review order size and market liquidity

4. **System Interrupts**:
   - Review recent market conditions
   - Check log files for error patterns
   - Verify network connectivity

### Debug Mode

Enable detailed debugging by setting `LOG_LEVEL = 'DEBUG'` in `config.py`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Review the logs for error details
3. Submit an issue with detailed information

## 🔗 Additional Resources

- [Kraken API Documentation](https://docs.kraken.com/rest/)
- [Arbitrage Trading Strategies](https://en.wikipedia.org/wiki/Arbitrage)
- [Risk Management in Trading](https://www.investopedia.com/articles/trading/09/risk-management.asp)

---

**Remember**: This system is for educational and research purposes. Always test thoroughly in simulation mode before using real capital.