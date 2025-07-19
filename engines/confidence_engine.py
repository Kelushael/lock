import numpy as np
from arch import arch_model
import time

class BayesianConfidenceEngine:
    """Quantum-Bayesian confidence scoring with volatility weighting"""
    
    def __init__(self, decay_factor=0.95):
        self.alpha = 1.0  # Prior successes
        self.beta = 1.0   # Prior failures
        self.decay_factor = decay_factor
        self.volatility_model = None
        self.trade_history = []
        self.liquidity_asymmetry = 0.0
        self.confidence_params = {
            'alpha': self.alpha,
            'beta': self.beta,
            'volatility_factor': 1.0,
            'liquidity_penalty': 0.0
        }
        
    def update_volatility(self, returns_series):
        """Updates GARCH volatility model"""
        if len(returns_series) > 10:
            try:
                self.volatility_model = arch_model(
                    returns_series, 
                    vol='Garch', 
                    p=1, 
                    q=1
                ).fit(disp='off')
                self.confidence_params['volatility_factor'] = min(
                    1.2, 
                    max(0.8, 1.0 / self.volatility_model.conditional_volatility[-1])
                )
            except:
                self.confidence_params['volatility_factor'] = 1.0
    
    def update_order_book_depth(self, bids, asks):
        """Calculates liquidity asymmetry penalty"""
        if bids and asks:
            bid_depth = sum(float(b[1]) for b in bids[:5])
            ask_depth = sum(float(a[1]) for a in asks[:5])
            total_depth = bid_depth + ask_depth
            
            if total_depth > 0:
                self.liquidity_asymmetry = abs(bid_depth - ask_depth) / total_depth
                self.confidence_params['liquidity_penalty'] = self.liquidity_asymmetry * 0.3
    
    def record_trade_result(self, success, profit=0):
        """Records trade outcome for Bayesian updating"""
        self.trade_history.append({
            'success': success,
            'profit': profit,
            'timestamp': time.time()
        })
        
        # Bayesian posterior update
        if success:
            self.alpha += 1
        else:
            self.beta += 1
            
        # Update confidence parameters
        self.confidence_params['alpha'] = self.alpha
        self.confidence_params['beta'] = self.beta
        
        # Trim history to last 100 trades
        if len(self.trade_history) > 100:
            self.trade_history = self.trade_history[-100:]
    
    def calculate_confidence(self):
        """Calculates current confidence score"""
        # Bayesian confidence with decay weighting
        n = len(self.trade_history)
        if n == 0:
            base_confidence = 0.5
        else:
            # Decay-weighted success rate
            weights = [self.decay_factor**(n-i) for i in range(n)]
            weighted_successes = sum(
                w * trade['success'] 
                for w, trade in zip(weights, self.trade_history)
            )
            weight_sum = sum(weights)
            base_confidence = weighted_successes / weight_sum if weight_sum > 0 else 0.5
        
        # Apply volatility and liquidity penalties
        vol_factor = self.confidence_params['volatility_factor']
        liq_penalty = self.confidence_params['liquidity_penalty']
        
        final_confidence = base_confidence * vol_factor * (1 - liq_penalty)
        return max(0.1, min(0.95, final_confidence))
    
    def get_kelly_fraction(self, win_prob, avg_win, avg_loss):
        """Calculates Kelly criterion position sizing"""
        if avg_loss <= 0:
            return 0.1
        
        win_loss_ratio = avg_win / abs(avg_loss)
        kelly = win_prob - ((1 - win_prob) / win_loss_ratio)
        return max(0.01, min(0.25, kelly))

# Module state for introspection
confidence_params = {
    'alpha': 1.2,
    'beta': 0.8, 
    'volatility_factor': 0.92,
    'liquidity_penalty': 0.05
}