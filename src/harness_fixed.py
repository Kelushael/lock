# Harness: Production execution engine with timeout watchdogs and fallback logic

import time
import krakenex
from decimal import Decimal
import traceback
# --- FastAPI server imports ---
from fastapi import FastAPI, HTTPException, Response
import threading
import uvicorn

# --- FastAPI app and swap control ---
app = FastAPI()
swap_thread = None
swap_running = False

def get_env_api_keys():
    """Load API keys from .env file"""
    api_keys = []
    try:
        with open(".env") as f:
            lines = f.readlines()
        key, secret = None, None
        for line in lines:
            if line.startswith("KRAKEN_API_KEY="):
                key = line.strip().split("=", 1)[1]
            elif line.startswith("KRAKEN_API_SECRET="):
                secret = line.strip().split("=", 1)[1]
        if key and secret:
            api_keys.append((key, secret))
    except Exception as e:
        print(f"[Harness] Could not load .env: {e}")
    return api_keys

# --- Trading Configuration ---
MIN_PROFIT = Decimal('0.003')   # 0.3% (lowered for testing)
CONFIDENCE_THRESHOLD = Decimal('0.6')
CYCLE_INTERVAL = 5   # seconds
WATCHDOG_TIMEOUT = 600  # 10 minutes
FEE_RATE = Decimal('0.0026')  # 0.26% taker
MIN_TRADE_SIZE = Decimal('10')  # Minimum $10 USD

# --- Logging ---
def log_cycle(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

# --- Portfolio Functions ---
def get_spot_balances_only(k):
    """Get ONLY spot wallet balances - ignore funding wallets completely"""
    try:
        balance_response = k.query_private('Balance')
        if balance_response.get('error'):
            log_cycle(f"Balance error: {balance_response['error']}")
            return {}
        
        # Filter out ALL funding wallet assets (.F, .HOLD, etc.)
        spot_balances = {}
        for asset, amount in balance_response['result'].items():
            if not ('.' in asset):  # Only pure spot assets
                spot_balances[asset] = Decimal(amount)
        
        return spot_balances
    except Exception as e:
        log_cycle(f"Balance fetch failed: {str(e)}")
        return {}

def log_portfolio_holdings(balances):
    log_cycle("--- SPOT WALLET HOLDINGS ONLY ---")
    for asset, amount in balances.items():
        display_asset = 'USD' if asset == 'ZUSD' else asset
        if amount > 0:
            log_cycle(f"{display_asset}: {amount}")
    log_cycle("--------------------------------")

# --- Market Data ---
def fetch_order_book(k, pair):
    """Fetch order book for a single pair"""
    try:
        ob_resp = k.query_public('Depth', {'pair': pair, 'count': 10})
        if ob_resp.get('error'):
            return None
        return ob_resp['result'][pair]
    except Exception as e:
        log_cycle(f"Error fetching {pair}: {e}")
        return None

# --- Trade Simulation ---
def simulate_trade(order_book, side, usd_amount):
    """Simulate a trade and return expected output after fees"""
    if not order_book:
        return None
    
    levels = order_book['asks'] if side == 'buy' else order_book['bids']
    if not levels:
        return None
    
    remaining = usd_amount
    total_asset = Decimal('0')
    
    for level in levels:
        price = Decimal(level[0])
        volume = Decimal(level[1])
        
        if side == 'buy':
            # How much USD this level can absorb
            level_usd = price * volume
            if level_usd <= remaining:
                # Take entire level
                total_asset += volume
                remaining -= level_usd
            else:
                # Take partial level
                asset_obtained = remaining / price
                total_asset += asset_obtained
                remaining = Decimal('0')
                break
        
        if remaining <= 0:
            break
    
    if remaining > 0:
        return None  # Insufficient liquidity
    
    # Apply Kraken taker fee
    return total_asset * (Decimal('1') - FEE_RATE)

# --- Trade Execution ---
def execute_market_order(k, pair, side, amount, is_quote_currency=False):
    """Execute a market order on Kraken"""
    try:
        order = {
            'pair': pair,
            'type': side,
            'ordertype': 'market',
            'volume': str(amount)
        }
        
        # For buying with USD, use quote currency volume
        if side == 'buy' and is_quote_currency:
            order['oflags'] = 'viqc'
        
        resp = k.query_private('AddOrder', order)
        if resp.get('error'):
            return False, f"Order error: {resp['error']}"
        
        order_id = resp.get('result', {}).get('txid', [''])[0]
        return True, order_id
    except Exception as e:
        return False, f"Exception: {e}"

# --- Main Trading Logic ---
def find_best_usd_opportunity(k, usd_balance):
    """Find the best USD trading opportunity"""
    # Major USD pairs with good liquidity
    usd_pairs = [
        'XXBTZUSD',   # BTC/USD
        'XETHZUSD',   # ETH/USD  
        'SOLUSD',     # SOL/USD
        'ADAUSD',     # ADA/USD
        'DOTUSD',     # DOT/USD
        'LINKUSD',    # LINK/USD
        'AVAXUSD',    # AVAX/USD
        'MATICUSD',   # MATIC/USD
    ]
    
    best_pair = None
    best_profit = Decimal('0')
    best_data = None
    
    log_cycle(f"Scanning {len(usd_pairs)} USD pairs for opportunities...")
    
    for pair in usd_pairs:
        try:
            # Fetch order book
            order_book = fetch_order_book(k, pair)
            if not order_book:
                continue
            
            # Simulate buy with USD
            asset_received = simulate_trade(order_book, 'buy', usd_balance)
            if not asset_received:
                continue
            
            # Simulate immediate sell back to USD
            usd_received = simulate_trade(order_book, 'sell', asset_received)
            if not usd_received:
                continue
            
            # Calculate profit
            profit = (usd_received - usd_balance) / usd_balance
            
            log_cycle(f"{pair}: Buy {usd_balance} USD → {asset_received:.6f} → Sell {usd_received:.2f} USD | Profit: {profit*100:.3f}%")
            
            if profit > best_profit:
                best_profit = profit
                best_pair = pair
                best_data = {
                    'asset_amount': asset_received,
                    'final_usd': usd_received,
                    'order_book': order_book
                }
        
        except Exception as e:
            log_cycle(f"Error analyzing {pair}: {e}")
            continue
    
    return best_pair, best_profit, best_data

# --- FastAPI Endpoints ---
@app.get("/privacy", response_class=Response)
def get_privacy_policy():
    try:
        import os
        policy_path = os.path.join(os.path.dirname(__file__), "..", "PRIVACY_POLICY.md")
        with open(policy_path, "r") as f:
            return Response(f.read(), media_type="text/markdown")
    except:
        return Response("Privacy policy not found", media_type="text/plain")

@app.post("/start_swaps")
def start_swaps():
    global swap_thread, swap_running
    if swap_running:
        return {"status": "already_running"}
    
    swap_running = True
    swap_thread = threading.Thread(target=run_trading_loop, daemon=True)
    swap_thread.start()
    return {"status": "started"}

@app.get("/swap_status")
def swap_status():
    return {"running": swap_running}

@app.post("/stop_swaps")
def stop_swaps():
    global swap_running
    swap_running = False
    return {"status": "stopped"}

# --- Main Trading Loop ---
def run_trading_loop():
    """Main trading execution loop"""
    global swap_running
    
    log_cycle("🔥 MARCUS ULTRA-HF TRADING SYSTEM ACTIVATED 🔥")
    log_cycle("Initializing quantum trading modules...")
    
    # Get API credentials
    api_keys = get_env_api_keys()
    if not api_keys:
        log_cycle("❌ No API keys found in .env file")
        swap_running = False
        return
    
    key, secret = api_keys[0]
    k = krakenex.API(key=key, secret=secret)
    
    # Trading state
    last_trade_time = time.time()
    last_justifiable_reason_time = time.time()
    cycle_count = 0
    
    log_cycle("✅ System ready - Starting USD-focused trading")
    
    while swap_running:
        cycle_start = time.time()
        cycle_count += 1
        
        try:
            log_cycle(f"\n{'='*50}")
            log_cycle(f"🧠 CYCLE {cycle_count} - QUANTUM CONSCIOUSNESS ACTIVE")
            log_cycle(f"{'='*50}")
            
            # --- Phase 1: Portfolio Assessment ---
            log_cycle("📊 Fetching spot wallet balances...")
            balances = get_spot_balances_only(k)
            log_portfolio_holdings(balances)
            
            # Focus on USD balance
            usd_balance = balances.get('ZUSD', Decimal('0'))
            if usd_balance < MIN_TRADE_SIZE:
                reason = f"Insufficient USD balance: ${usd_balance} (minimum ${MIN_TRADE_SIZE})"
                log_cycle(f"⏸️  {reason}")
                last_justifiable_reason_time = time.time()
                time.sleep(CYCLE_INTERVAL)
                continue
            
            log_cycle(f"💰 Available USD: ${usd_balance}")
            
            # --- Phase 2: Opportunity Scanning ---
            log_cycle("🔍 Scanning USD markets for arbitrage opportunities...")
            best_pair, best_profit, trade_data = find_best_usd_opportunity(k, usd_balance)
            
            # --- Phase 3: Decision Making ---
            if best_pair and best_profit >= MIN_PROFIT:
                log_cycle(f"⚡ OPPORTUNITY DETECTED: {best_pair}")
                log_cycle(f"🎯 Expected profit: {best_profit*100:.3f}%")
                log_cycle(f"🚀 EXECUTING TRADE SEQUENCE...")
                
                # Execute buy order
                log_cycle(f"📈 Step 1: Buying asset with ${usd_balance} USD")
                success1, result1 = execute_market_order(k, best_pair, 'buy', usd_balance, True)
                
                if success1:
                    log_cycle(f"✅ Buy order executed: {result1}")
                    
                    # Wait briefly for settlement
                    time.sleep(3)
                    
                    # Execute sell order
                    asset_amount = trade_data['asset_amount']
                    log_cycle(f"📉 Step 2: Selling {asset_amount:.6f} asset back to USD")
                    success2, result2 = execute_market_order(k, best_pair, 'sell', asset_amount, False)
                    
                    if success2:
                        log_cycle(f"✅ Sell order executed: {result2}")
                        log_cycle(f"🔥 TRADE COMPLETED - Estimated profit: ${(trade_data['final_usd'] - usd_balance):.2f}")
                        last_trade_time = time.time()
                    else:
                        log_cycle(f"❌ Sell order failed: {result2}")
                else:
                    log_cycle(f"❌ Buy order failed: {result1}")
            
            else:
                if best_pair:
                    reason = f"Best opportunity {best_pair}: {best_profit*100:.3f}% below {MIN_PROFIT*100}% threshold"
                else:
                    reason = "No profitable opportunities found in current market conditions"
                
                log_cycle(f"⏸️  {reason}")
                last_justifiable_reason_time = time.time()
            
        except Exception as e:
            log_cycle(f"❌ CRITICAL ERROR: {e}")
            log_cycle(f"🔄 Stack trace: {traceback.format_exc()}")
        
        # --- Phase 4: Watchdog Monitoring ---
        now = time.time()
        idle_time = now - last_trade_time
        reason_time = now - last_justifiable_reason_time
        
        if idle_time >= WATCHDOG_TIMEOUT and reason_time >= WATCHDOG_TIMEOUT:
            log_cycle(f"🚨 WATCHDOG ALERT: {WATCHDOG_TIMEOUT//60} minutes without trades or valid reasons")
            log_cycle("🛑 System shutdown initiated")
            swap_running = False
            break
        
        # --- Phase 5: Cycle Timing ---
        elapsed = time.time() - cycle_start
        sleep_time = max(0, CYCLE_INTERVAL - elapsed)
        
        if sleep_time > 0:
            log_cycle(f"⏱️  Cycle completed in {elapsed:.2f}s, sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
    
    log_cycle("🔥 MARCUS TRADING SYSTEM DEACTIVATED 🔥")
    swap_running = False

if __name__ == "__main__":
    print("🔥 STARTING MARCUS QUANTUM TRADING SERVER 🔥")
    print("Server: http://0.0.0.0:8000")
    print("Endpoints:")
    print("  POST /start_swaps - Start trading")
    print("  GET  /swap_status - Check status") 
    print("  POST /stop_swaps  - Stop trading")
    uvicorn.run(app, host="0.0.0.0", port=8000)