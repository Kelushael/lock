import ast
import inspect
import importlib
import re
import time
from typing import Dict, Any

class CodeSelfInterpreter:
    """Meta-cognitive code introspection engine"""
    
    def __init__(self, module_names):
        self.modules = {}
        self.last_analysis = {}
        for name in module_names:
            self.modules[name] = self._capture_module_state(name)
    
    def _capture_module_state(self, module_name):
        """Captures source code and live state of trading modules"""
        try:
            # Import the module
            if '.' in module_name:
                module = importlib.import_module(module_name)
            else:
                module = importlib.import_module(f"engines.{module_name}")
            
            # Get source code
            source = inspect.getsource(module)
            
            # Extract live variables and state
            state = {}
            for name in dir(module):
                if not name.startswith('__'):
                    obj = getattr(module, name)
                    if not inspect.ismodule(obj) and not inspect.isfunction(obj):
                        try:
                            if isinstance(obj, (int, float, str, list, dict, bool)):
                                state[name] = obj
                            elif hasattr(obj, '__dict__'):
                                state[name] = {k: v for k, v in obj.__dict__.items() 
                                             if not k.startswith('_')}
                        except:
                            state[name] = "Unserializable"
            
            return {
                'source': source,
                'state': state,
                'timestamp': time.time()
            }
        except Exception as e:
            print(f"Failed to capture module {module_name}: {e}")
            return {'source': '', 'state': {}, 'timestamp': time.time()}
    
    def extract_mathematical_insights(self, module_name):
        """Extracts mathematical logic and current state"""
        if module_name not in self.modules:
            return {}
            
        module_data = self.modules[module_name]
        source = module_data['source']
        state = module_data['state']
        
        insights = {
            'algorithms': self._extract_algorithms(source),
            'parameters': self._extract_parameters(source, state),
            'current_values': self._extract_current_values(state),
            'mathematical_operations': self._extract_math_operations(source)
        }
        
        self.last_analysis[module_name] = insights
        return insights
    
    def _extract_algorithms(self, source):
        """Identifies key algorithms in the source code"""
        algorithms = []
        
        # Pattern matching for common algorithms
        patterns = {
            'Bellman-Ford': r'bellman_ford|negative.*cycle',
            'GARCH': r'arch_model|garch|volatility',
            'HMM': r'hmm\.|hidden.*markov|GaussianHMM',
            'Wavelet': r'pywt|wavelet|wavedec',
            'Kelly Criterion': r'kelly|win_prob.*loss',
            'Bayesian': r'alpha.*beta|prior|posterior'
        }
        
        for algo, pattern in patterns.items():
            if re.search(pattern, source, re.IGNORECASE):
                algorithms.append(algo)
        
        return algorithms
    
    def _extract_parameters(self, source, state):
        """Extracts key parameters and their values"""
        parameters = {}
        
        # Extract from state
        for key, value in state.items():
            if isinstance(value, (int, float)) and not key.startswith('_'):
                parameters[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, (int, float)):
                        parameters[f"{key}.{subkey}"] = subvalue
        
        return parameters
    
    def _extract_current_values(self, state):
        """Extracts current operational values"""
        values = {}
        
        # Look for specific trading-related values
        trading_keys = [
            'detected_cycles', 'confidence_params', 'current_momentum',
            'alpha', 'beta', 'volatility_factor', 'profit', 'threshold'
        ]
        
        for key in trading_keys:
            if key in state:
                values[key] = state[key]
        
        return values
    
    def _extract_math_operations(self, source):
        """Identifies mathematical operations in the code"""
        operations = []
        
        # Pattern matching for mathematical operations
        math_patterns = [
            r'np\.log|np\.exp',
            r'np\.mean|np\.std',
            r'np\.tanh|np\.sigmoid',
            r'\*\s*fee_factor',
            r'profit\s*=.*\-\s*1',
            r'confidence\s*\*.*momentum'
        ]
        
        for pattern in math_patterns:
            matches = re.findall(pattern, source)
            operations.extend(matches)
        
        return operations
    
    def refresh_module_state(self, module_name):
        """Refreshes the state of a specific module"""
        self.modules[module_name] = self._capture_module_state(module_name)
    
    def get_comprehensive_analysis(self):
        """Returns comprehensive analysis of all modules"""
        analysis = {}
        for module_name in self.modules.keys():
            analysis[module_name] = self.extract_mathematical_insights(module_name)
        return analysis