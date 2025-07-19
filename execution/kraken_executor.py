import krakenex
from pykrakenapi import KrakenAPI
import time
import numpy as np

class QuantumKrakenExecutor:
    """Quantum-enhanced Kraken trade execution engine"""
    
    def __init__(self, vault):
        self.vault = vault
        self.api = krakenex.API(key=vault.kraken_key, secret=vault.kraken_secret)
        self.kraken = KrakenAPI(self.api)
        self.portfolio_value = vault.initial_portfolio
        self.trade_history = []
        
    def validate_abundance(self, swap_decision):
        """Quantum abundance validation before execution"""
        if swap_decision['decision'] != 'SWAP':
            return False
            
        swap_details = swap_decision.get('swap_details', {})
        
        # Validate swap parameters
        if not all(key in swap_details for key in ['from_asset', 'to_asset', 'amount']):
            return False
            
        # Check minimum profit threshold
        expected_profit = swap_details.get('expected_profit', 0)
        if expected_profit < self.vault.min_profit:
            return False
            
        # Check position size limits
        amount = swap_details.get('amount', 0)
        if amount > self.portfolio_value * self.vault.max_position:
            return False
            
        # Confidence threshold check
        if swap_decision.get('confidence', 0) < self.vault.confidence_threshold:
            return False
            
        return True
    
    def execute_swap(self, swap_decision):
        """Executes validated swap with quantum precision"""
        if not self.validate_abundance(swap_decision):
            return {
                'success': False,
                'reason': 'Failed abundance validation',
                'timestamp': time.time()
            }
        
        swap_details = swap_decision['swap_details']
        
        try:
            # Get current balances
            balance = self.kraken.get_account_balance()
            
            # Construct trading pair
            from_asset = swap_details['from_asset']
            to_asset = swap_details['to_asset']
            pair = f"{from_asset}{to_asset}"
            
            # Check if pair exists, try reverse if not
            try:
                ticker = self.kraken.get_ticker_information(pair)
            except:
                pair = f"{to_asset}{from_asset}"
                ticker = self.kraken.get_ticker_information(pair)
                # Adjust order type for reverse pair
                order_type = 'sell'
            else:
                order_type = 'buy'
            
            # Calculate order volume
            volume = self._calculate_order_volume(swap_details, balance, ticker)
            
            # Execute market order
            order_result = self.kraken.add_standard_order(
                pair=pair,
                type=order_type,
                ordertype='market',
                volume=volume,
                validate=False  # Execute immediately
            )
            
            # Record successful trade
            trade_record = {
                'success': True,
                'pair': pair,
                'type': order_type,
                'volume': volume,
                'order_id': order_result.get('txid', [''])[0],
                'timestamp': time.time(),
                'decision': swap_decision
            }
            
            self.trade_history.append(trade_record)
            
            # Update portfolio value estimate
            self._update_portfolio_estimate(trade_record)
            
            return trade_record
            
        except Exception as e:
            error_record = {
                'success': False,
                'reason': str(e),
                'timestamp': time.time(),
                'decision': swap_decision
            }
            self.trade_history.append(error_record)
            return error_record
    
    def _calculate_order_volume(self, swap_details, balance, ticker):
        """Calculates optimal order volume"""
        amount = swap_details.get('amount', 0)
        
        # Get current price from ticker
        current_price = float(ticker.iloc[0]['c'])
        
        # Calculate volume based on amount and current price
        volume = amount / current_price
        
        # Apply minimum order size constraints
        min_volume = 0.001  # Kraken minimum
        volume = max(min_volume, volume)
        
        # Round to appropriate decimal places
        volume = round(volume, 8)
        
        return volume
    
    def _update_portfolio_estimate(self, trade_record):
        """Updates estimated portfolio value"""
        if trade_record['success']:
            # Simple estimation - in practice, would query actual balances
            expected_profit = trade_record['decision']['swap_details'].get('expected_profit', 0)
            self.portfolio_value *= (1 + expected_profit)
    
    def get_portfolio_status(self):
        """Returns current portfolio status"""
        try:
            balance = self.kraken.get_account_balance()
            return {
                'balances': balance.to_dict(),
                'estimated_value': self.portfolio_value,
                'trade_count': len(self.trade_history),
                'success_rate': self._calculate_success_rate()
            }
        except Exception as e:
            return {
                'error': str(e),
                'estimated_value': self.portfolio_value,
                'trade_count': len(self.trade_history)
            }
    
    def _calculate_success_rate(self):
        """Calculates trade success rate"""
        if not self.trade_history:
            return 0.0
            
        successful_trades = sum(1 for trade in self.trade_history if trade.get('success', False))
        return successful_trades / len(self.trade_history)
    
    def get_recent_trades(self, limit=10):
        """Returns recent trade history"""
        return self.trade_history[-limit:] if self.trade_history else []