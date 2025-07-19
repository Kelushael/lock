#!/usr/bin/env python3
"""
API KEY VALIDATION SCRIPT
Tests your API connections before live trading
"""

import os
from dotenv import load_dotenv
from core.env_vault import EnvVault

def test_kraken_connection():
    """Test Kraken API connection"""
    try:
        from execution.kraken_executor import QuantumKrakenExecutor
        vault = EnvVault()
        executor = QuantumKrakenExecutor(vault)
        
        # Test connection
        status = executor.get_portfolio_status()
        if 'error' not in status:
            print("✅ Kraken API: Connected successfully")
            print(f"   Portfolio value: ${status.get('estimated_value', 0):.2f}")
            return True
        else:
            print(f"❌ Kraken API: {status['error']}")
            return False
    except Exception as e:
        print(f"❌ Kraken API: Connection failed - {e}")
        return False

def test_llm_connections():
    """Test LLM API connections"""
    vault = EnvVault()
    results = {}
    
    # Test Groq
    if vault.groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=vault.groq_key)
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            print("✅ Groq API: Connected")
            results['groq'] = True
        except Exception as e:
            print(f"❌ Groq API: {e}")
            results['groq'] = False
    
    # Test Anthropic
    if vault.anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=vault.anthropic_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=5,
                messages=[{"role": "user", "content": "Test"}]
            )
            print("✅ Anthropic API: Connected")
            results['anthropic'] = True
        except Exception as e:
            print(f"❌ Anthropic API: {e}")
            results['anthropic'] = False
    
    # Test Ollama
    try:
        import ollama
        models = ollama.list()
        print(f"✅ Ollama: {len(models['models'])} models available")
        results['ollama'] = True
    except Exception as e:
        print(f"❌ Ollama: {e}")
        results['ollama'] = False
    
    return results

def main():
    print("🔍 VALIDATING SOVEREIGN SETUP")
    print("=" * 40)
    
    # Load environment
    load_dotenv()
    
    # Test connections
    kraken_ok = test_kraken_connection()
    llm_results = test_llm_connections()
    
    print("\n📊 VALIDATION SUMMARY")
    print(f"Kraken API: {'✅' if kraken_ok else '❌'}")
    print(f"LLM APIs: {sum(llm_results.values())}/{len(llm_results)} connected")
    
    if kraken_ok and any(llm_results.values()):
        print("\n🚀 READY FOR DEPLOYMENT!")
        print("Launch command: python main_quantum_trader.py")
    else:
        print("\n⚠️  Fix API connections before trading")

if __name__ == "__main__":
    main()