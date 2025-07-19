import os
from dotenv import load_dotenv

class EnvVault:
    """Secure environment variable management"""
    
    def __init__(self):
        load_dotenv()
        self.kraken_key = os.getenv("KRAKEN_API_KEY")
        self.kraken_secret = os.getenv("KRAKEN_API_SECRET")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Trading parameters
        self.initial_portfolio = float(os.getenv("INITIAL_PORTFOLIO_VALUE", "100.0"))
        self.min_profit = float(os.getenv("MIN_PROFIT_THRESHOLD", "0.004"))
        self.max_position = float(os.getenv("MAX_POSITION_SIZE", "0.15"))
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))
        
        # Quantum parameters
        self.entanglement_factor = float(os.getenv("ENTANGLEMENT_FACTOR", "1.0"))
        self.wavelet_window = int(os.getenv("WAVELET_WINDOW", "50"))
        self.abundance_multiplier = float(os.getenv("ABUNDANCE_MULTIPLIER", "1.618"))
        
        self.llm_config = {
            'local_models': [
                'llama3:70b',
                'mixtral:8x22b', 
                'command-r-plus'
            ],
            'cloud_models': {
                'groq': 'llama3-70b-8192',
                'anthropic': 'claude-3-5-sonnet-20240620'
            }
        }
    
    def validate(self):
        """Validates all required environment variables"""
        required = [
            self.kraken_key, self.kraken_secret,
            self.groq_key, self.anthropic_key
        ]
        if not all(required):
            raise ValueError("Missing required environment variables")
        return True