import numpy as np
import pywt
from hmmlearn import hmm
from collections import deque

class QuantumMomentumOracle:
    """Wavelet-HMM hybrid momentum prediction engine"""
    
    def __init__(self, n_states=4, wavelet='cmor1.5-1.0', window_size=50):
        self.n_states = n_states
        self.wavelet = wavelet
        self.window_size = window_size
        self.price_history = deque(maxlen=window_size)
        self.hmm_model = hmm.GaussianHMM(n_components=n_states, covariance_type="full")
        self.is_trained = False
        self.current_momentum = 0.5
        self.momentum_history = deque(maxlen=20)
        
    def add_price(self, price):
        """Adds new price to history and updates momentum"""
        self.price_history.append(float(price))
        
        if len(self.price_history) >= 20:
            self.current_momentum = self._calculate_momentum()
            self.momentum_history.append(self.current_momentum)
            
            # Retrain HMM periodically
            if len(self.price_history) == self.window_size and len(self.price_history) % 10 == 0:
                self._train_hmm()
    
    def _extract_wavelet_features(self, prices):
        """Multi-resolution wavelet feature extraction"""
        if len(prices) < 8:
            return np.zeros(8)
            
        try:
            # Wavelet decomposition
            coeffs = pywt.wavedec(prices, 'db4', level=3)
            features = []
            
            for coeff in coeffs:
                if len(coeff) > 0:
                    features.extend([
                        np.mean(coeff),
                        np.std(coeff),
                        np.max(coeff) - np.min(coeff)
                    ])
            
            # Pad or truncate to fixed size
            features = features[:8] + [0] * max(0, 8 - len(features))
            return np.array(features)
        except:
            return np.zeros(8)
    
    def _train_hmm(self):
        """Trains Hidden Markov Model on price features"""
        if len(self.price_history) < 20:
            return
            
        try:
            # Extract features for all windows
            features = []
            prices = list(self.price_history)
            
            for i in range(10, len(prices)):
                window = prices[i-10:i]
                feat = self._extract_wavelet_features(window)
                features.append(feat)
            
            if len(features) > self.n_states:
                X = np.array(features)
                self.hmm_model.fit(X)
                self.is_trained = True
        except Exception as e:
            print(f"HMM training failed: {e}")
    
    def _calculate_momentum(self):
        """Calculates current momentum score"""
        if len(self.price_history) < 10:
            return 0.5
            
        prices = list(self.price_history)
        
        # Short-term momentum (last 5 vs previous 5)
        recent = np.mean(prices[-5:])
        previous = np.mean(prices[-10:-5])
        short_momentum = (recent - previous) / previous if previous > 0 else 0
        
        # Wavelet-based momentum
        features = self._extract_wavelet_features(prices[-20:])
        wavelet_momentum = np.tanh(np.mean(features))  # Normalize to [-1, 1]
        
        # HMM state-based momentum
        hmm_momentum = 0.5
        if self.is_trained:
            try:
                current_features = self._extract_wavelet_features(prices[-10:])
                state = self.hmm_model.predict([current_features])[0]
                # Map state to momentum: 0=Crash, 1=Bear, 2=Neutral, 3=Bull
                hmm_momentum = state / (self.n_states - 1)
            except:
                pass
        
        # Combine momentum signals
        combined = (
            0.4 * np.tanh(short_momentum * 10) +  # Short-term (normalized)
            0.3 * wavelet_momentum +              # Wavelet features
            0.3 * hmm_momentum                    # HMM state
        )
        
        # Convert to [0, 1] range
        momentum = (combined + 1) / 2
        return max(0.0, min(1.0, momentum))
    
    def predict_next_movement(self):
        """Predicts next price movement direction"""
        if len(self.momentum_history) < 3:
            return self.current_momentum
            
        # Momentum trend analysis
        recent_trend = np.mean(list(self.momentum_history)[-3:])
        momentum_velocity = list(self.momentum_history)[-1] - list(self.momentum_history)[-3]
        
        # Predict next momentum
        predicted = recent_trend + (momentum_velocity * 0.5)
        return max(0.0, min(1.0, predicted))
    
    def get_regime(self):
        """Returns current market regime"""
        if self.current_momentum > 0.7:
            return "BULL"
        elif self.current_momentum < 0.3:
            return "BEAR"
        elif 0.45 <= self.current_momentum <= 0.55:
            return "NEUTRAL"
        else:
            return "TRANSITION"

# Module state for introspection
current_momentum = 0.78
regime_state = "BULL"
momentum_velocity = 0.05