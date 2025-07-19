import json
import time
from groq import Groq
import anthropic
import ollama

class MetaCognitiveTrader:
    """Self-reflective AI agent with code comprehension"""
    
    def __init__(self, introspector, vault):
        self.introspector = introspector
        self.vault = vault
        self.memory = []
        self.decision_history = []
        
        # Initialize LLM clients
        self.groq_client = Groq(api_key=vault.groq_key)
        self.anthropic_client = anthropic.Anthropic(api_key=vault.anthropic_key)
        
    def analyze_and_decide(self, market_data):
        """Core meta-cognitive decision loop"""
        # Phase 1: Code introspection
        code_analysis = self.introspector.get_comprehensive_analysis()
        
        # Phase 2: Mathematical comprehension
        decision = self._comprehend_and_decide(code_analysis, market_data)
        
        # Phase 3: Store for self-reflection
        self.memory.append({
            'decision': decision,
            'code_state': code_analysis,
            'market_data': market_data,
            'timestamp': time.time()
        })
        
        return decision
    
    def _comprehend_and_decide(self, code_analysis, market_data):
        """Mathematical comprehension and decision making"""
        # Extract key insights from code analysis
        arb_insights = code_analysis.get('arbitrage_engine', {})
        conf_insights = code_analysis.get('confidence_engine', {})
        mom_insights = code_analysis.get('momentum_oracle', {})
        
        # Build comprehensive prompt for LLM
        prompt = self._build_decision_prompt(arb_insights, conf_insights, mom_insights, market_data)
        
        # Get decisions from multiple LLMs
        decisions = self._query_llm_council(prompt)
        
        # Aggregate decisions
        final_decision = self._aggregate_decisions(decisions)
        
        return final_decision
    
    def _build_decision_prompt(self, arb_insights, conf_insights, mom_insights, market_data):
        """Builds comprehensive decision prompt"""
        prompt = f"""
You are a meta-cognitive trading agent analyzing your own source code to make swap decisions.

ARBITRAGE ENGINE ANALYSIS:
- Algorithms: {arb_insights.get('algorithms', [])}
- Current Values: {arb_insights.get('current_values', {})}
- Parameters: {arb_insights.get('parameters', {})}

CONFIDENCE ENGINE ANALYSIS:
- Algorithms: {conf_insights.get('algorithms', [])}
- Current Values: {conf_insights.get('current_values', {})}
- Parameters: {conf_insights.get('parameters', {})}

MOMENTUM ORACLE ANALYSIS:
- Algorithms: {mom_insights.get('algorithms', [])}
- Current Values: {mom_insights.get('current_values', {})}
- Parameters: {mom_insights.get('parameters', {})}

CURRENT MARKET DATA:
{json.dumps(market_data, indent=2)}

Based on your analysis of the source code and current market conditions:

1. What arbitrage opportunities do you detect from the Bellman-Ford algorithm?
2. What is your confidence level based on the Bayesian parameters?
3. What does the wavelet-HMM momentum analysis suggest?
4. Should we execute a swap? If yes, specify the exact trade.

Respond in JSON format:
{{
  "decision": "SWAP" or "HOLD",
  "confidence": 0.0-1.0,
  "reasoning": "detailed mathematical reasoning",
  "swap_details": {{
    "from_asset": "SOL",
    "to_asset": "ETH", 
    "amount": 0.0,
    "expected_profit": 0.0
  }}
}}
"""
        return prompt
    
    def _query_llm_council(self, prompt):
        """Queries multiple LLMs for decision consensus"""
        decisions = []
        
        # Query Groq (Llama3-70B)
        try:
            groq_response = self.groq_client.chat.completions.create(
                model=self.vault.llm_config['cloud_models']['groq'],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            groq_decision = self._parse_llm_response(groq_response.choices[0].message.content)
            decisions.append(('groq', groq_decision))
        except Exception as e:
            print(f"Groq query failed: {e}")
        
        # Query Anthropic (Claude)
        try:
            claude_response = self.anthropic_client.messages.create(
                model=self.vault.llm_config['cloud_models']['anthropic'],
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            claude_decision = self._parse_llm_response(claude_response.content[0].text)
            decisions.append(('claude', claude_decision))
        except Exception as e:
            print(f"Claude query failed: {e}")
        
        # Query local LLMs via Ollama
        for model in self.vault.llm_config['local_models'][:2]:  # Limit to 2 for speed
            try:
                ollama_response = ollama.generate(model=model, prompt=prompt)
                ollama_decision = self._parse_llm_response(ollama_response['response'])
                decisions.append((model, ollama_decision))
            except Exception as e:
                print(f"Ollama {model} query failed: {e}")
        
        return decisions
    
    def _parse_llm_response(self, response_text):
        """Parses LLM response into structured decision"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return {
                    "decision": "HOLD",
                    "confidence": 0.5,
                    "reasoning": "Failed to parse response",
                    "swap_details": {}
                }
        except Exception as e:
            print(f"Response parsing failed: {e}")
            return {
                "decision": "HOLD",
                "confidence": 0.0,
                "reasoning": f"Parse error: {e}",
                "swap_details": {}
            }
    
    def _aggregate_decisions(self, decisions):
        """Aggregates multiple LLM decisions into final decision"""
        if not decisions:
            return {
                "decision": "HOLD",
                "confidence": 0.0,
                "reasoning": "No LLM responses received",
                "swap_details": {}
            }
        
        # Extract decisions and confidences
        swap_votes = sum(1 for _, d in decisions if d.get('decision') == 'SWAP')
        total_votes = len(decisions)
        avg_confidence = sum(d.get('confidence', 0) for _, d in decisions) / total_votes
        
        # Aggregate reasoning
        reasoning_parts = [f"{model}: {d.get('reasoning', 'No reasoning')}" 
                          for model, d in decisions]
        combined_reasoning = " | ".join(reasoning_parts)
        
        # Final decision logic
        should_swap = (swap_votes / total_votes) >= 0.6 and avg_confidence >= self.vault.confidence_threshold
        
        # Get best swap details from highest confidence decision
        best_decision = max(decisions, key=lambda x: x[1].get('confidence', 0))[1]
        
        return {
            "decision": "SWAP" if should_swap else "HOLD",
            "confidence": avg_confidence,
            "reasoning": combined_reasoning,
            "swap_details": best_decision.get('swap_details', {}),
            "vote_ratio": f"{swap_votes}/{total_votes}",
            "llm_count": total_votes
        }
    
    def record_trade_outcome(self, trade_result):
        """Records trade outcome for learning"""
        if self.decision_history:
            self.decision_history[-1]['outcome'] = trade_result
            
        # Update introspector modules with result
        for module_name in ['confidence_engine']:
            self.introspector.refresh_module_state(module_name)