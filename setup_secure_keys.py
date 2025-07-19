#!/usr/bin/env python3
"""
SECURE API KEY SETUP WIZARD
Guides you through safe API key configuration
"""

import os
import getpass
from pathlib import Path

def setup_kraken_keys():
    """Secure Kraken API setup"""
    print("🔐 KRAKEN API SETUP")
    print("Go to: https://www.kraken.com/u/security/api")
    print("Create API key with permissions: Query Funds, Query Open Orders, Query Closed Orders, Query Trades History, Create & Modify Orders")
    print()
    
    api_key = getpass.getpass("Enter Kraken API Key (hidden): ")
    api_secret = getpass.getpass("Enter Kraken API Secret (hidden): ")
    
    return api_key, api_secret

def setup_llm_keys():
    """Setup LLM API keys"""
    print("\n🤖 LLM API SETUP")
    
    # Groq (free tier available)
    print("Groq API (free): https://console.groq.com/keys")
    groq_key = getpass.getpass("Enter Groq API Key (optional, hidden): ")
    
    # Anthropic
    print("Anthropic API: https://console.anthropic.com/")
    anthropic_key = getpass.getpass("Enter Anthropic API Key (optional, hidden): ")
    
    return groq_key, anthropic_key

def write_env_file(kraken_key, kraken_secret, groq_key, anthropic_key):
    """Writes secure .env file"""
    env_content = f"""# KRAKEN API CONFIGURATION
KRAKEN_API_KEY={kraken_key}
KRAKEN_API_SECRET={kraken_secret}

# LLM API KEYS
GROQ_API_KEY={groq_key}
ANTHROPIC_API_KEY={anthropic_key}

# Local LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Trading Configuration
INITIAL_PORTFOLIO_VALUE=100.0
MIN_PROFIT_THRESHOLD=0.004
MAX_POSITION_SIZE=0.15
CONFIDENCE_THRESHOLD=0.65

# Quantum Parameters
ENTANGLEMENT_FACTOR=1.0
WAVELET_WINDOW=50
ABUNDANCE_MULTIPLIER=1.618
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Set secure permissions (Unix/Linux/Mac)
    try:
        os.chmod('.env', 0o600)  # Read/write for owner only
        print("✅ .env file created with secure permissions")
    except:
        print("⚠️  .env file created (set file permissions manually)")

def main():
    print("🔥 SOVEREIGN REALITY PROTOCOL - SECURE SETUP 🔥")
    print("=" * 50)
    
    # Setup Kraken
    kraken_key, kraken_secret = setup_kraken_keys()
    
    # Setup LLMs
    groq_key, anthropic_key = setup_llm_keys()
    
    # Write secure file
    write_env_file(kraken_key, kraken_secret, groq_key, anthropic_key)
    
    print("\n🎯 SETUP COMPLETE!")
    print("Your API keys are now securely stored in .env")
    print("Ready to launch: python main_quantum_trader.py")

if __name__ == "__main__":
    main()