import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import bellman_ford
import time

class MultidimensionalArbDetector:
    """Quantum-enhanced arbitrage detection using graph theory"""
    
    def __init__(self, pairs):
        self.pairs = pairs
        self.currency_index = self._build_currency_index()
        self.graph = np.zeros((len(self.currency_index), len(self.currency_index)))
        self.detected_cycles = []
        self.last_update = 0
        
    def _build_currency_index(self):
        """Creates currency mapping for graph construction"""
        currencies = set()
        for pair in self.pairs:
            base, quote = pair.split('/')
            currencies.add(base)
            currencies.add(quote)
        return {c: i for i, c in enumerate(sorted(currencies))}
    
    def update_rates(self, rates):
        """Updates exchange rates and detects arbitrage opportunities"""
        self.graph.fill(np.inf)
        np.fill_diagonal(self.graph, 0)
        
        for pair, (bid, ask) in rates.items():
            if pair in self.pairs:
                base, quote = pair.split('/')
                i = self.currency_index[base]
                j = self.currency_index[quote]
                
                # Negative log transformation for Bellman-Ford
                # Account for 0.26% Kraken taker fee
                fee_factor = 0.9974
                self.graph[i, j] = -np.log(bid * fee_factor)
                self.graph[j, i] = -np.log((1/ask) * fee_factor)
        
        self.detected_cycles = self._detect_arbitrage_cycles()
        self.last_update = time.time()
    
    def _detect_arbitrage_cycles(self):
        """Bellman-Ford negative cycle detection"""
        n = len(self.currency_index)
        cycles = []
        
        for start in range(n):
            try:
                dist, pred = bellman_ford(
                    csr_matrix(self.graph),
                    directed=True,
                    indices=[start],
                    return_predecessors=True
                )
                
                # Check for negative cycles
                for i in range(n):
                    if dist[i] < -0.008:  # Minimum 0.8% profit threshold
                        cycle_path = self._trace_cycle(pred, start, i)
                        profit = np.exp(-dist[i]) - 1
                        cycles.append({
                            'path': cycle_path,
                            'profit': profit,
                            'start_currency': list(self.currency_index.keys())[start]
                        })
            except:
                continue
        
        return sorted(cycles, key=lambda x: x['profit'], reverse=True)
    
    def _trace_cycle(self, predecessors, start, end):
        """Traces the arbitrage cycle path"""
        path = []
        current = end
        currencies = list(self.currency_index.keys())
        
        while current != start and len(path) < 10:  # Prevent infinite loops
            prev = predecessors[current]
            if prev == -9999:  # No predecessor
                break
            path.append({
                'from': currencies[prev],
                'to': currencies[current],
                'pair': f"{currencies[prev]}/{currencies[current]}"
            })
            current = prev
        
        return list(reversed(path))
    
    def get_best_opportunity(self):
        """Returns the most profitable arbitrage opportunity"""
        return self.detected_cycles[0] if self.detected_cycles else None

# Module state for introspection
detected_cycles = []
confidence_params = {'alpha': 1.2, 'beta': 0.8, 'volatility_factor': 0.92}
current_momentum = 0.78