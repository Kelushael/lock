#!/bin/bash

# High-Frequency Arbitrage Trading System Setup Script

echo "=========================================="
echo "ARBITRAGE TRADING SYSTEM SETUP"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
    print_status "Python version $python_version is compatible"
else
    print_error "Python 3.8+ required. Current version: $python_version"
    exit 1
fi

# Check if pip is available
print_status "Checking pip availability..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 not found. Please install pip first."
    exit 1
fi

# Install requirements
print_status "Installing Python dependencies..."
if pip3 install -r requirements.txt; then
    print_status "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Create environment file template
print_status "Creating environment configuration..."
cat > .env << 'EOF'
# Kraken API Configuration
# Get these from your Kraken Pro account settings
KRAKEN_API_KEY=your_kraken_api_key_here
KRAKEN_API_SECRET=your_kraken_api_secret_here

# Trading Configuration
MIN_PROFIT_THRESHOLD=0.3
MIN_CONFIDENCE_SCORE=0.7
MAX_POSITION_SIZE=500
SCAN_INTERVAL=1.0
MAX_IDLE_MINUTES=10
EOF

print_status "Environment template created (.env file)"

# Set executable permissions
print_status "Setting executable permissions..."
chmod +x run_trading_system.py
chmod +x test_trading_system.py
chmod +x arbitrage_trading_system.py

# Create logs directory
print_status "Creating logs directory..."
mkdir -p logs

# Run initial test
print_status "Running system tests..."
if python3 test_trading_system.py; then
    print_status "All tests passed! System is ready."
else
    print_warning "Some tests failed. Check the output above."
fi

echo ""
echo "=========================================="
echo "SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Kraken API credentials"
echo "2. Review config.py for trading parameters"
echo "3. Run tests: python3 test_trading_system.py"
echo "4. Start trading: python3 run_trading_system.py"
echo ""
print_warning "IMPORTANT: Never trade with money you cannot afford to lose!"
print_warning "Test thoroughly in simulation mode before live trading."
echo ""