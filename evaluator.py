"""
Benchmark Evaluator Module
Handles LLM-as-a-Judge evaluation and metrics calculation
"""

import json
import re
import time
import numpy as np
from scipy import stats
from typing import List, Dict, Any
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# API Configuration
API_URL = "https://origin.nextway.top/v1/chat/completions"
API_KEY = "MzQ3NWU0YTQtZTNjMS00YmU5LTliNGItZDk1MzgyODgwZWRk"


class BenchmarkEvaluator:
    """Main evaluator class for PersonaSteer Benchmark"""
    
    def __init__(self, judge_model: str = "gpt-4o-mini"):
        self.judge_model = judge_model
        self.max_workers = 8
    
    def call_llm_judge(self, prompt: str) -> str:
        """Call LLM API for evaluation"""
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.judge_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(API_URL, headers=headers, json=data, timeout=60)
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise e
        
        return ""
    
    def build_evaluation_prompt(self, profile: str, personality: str, 
                                 history: List[str], user_msg: str, 
                                 response: str) -> str:
        """Build the evaluation prompt for LLM judge"""
        
        history_str = "\n".join(history) if history else "None"
        
        prompt = f"""You are evaluating how well an AI assistant's response aligns with the user's preferences and personality.

## User Profile:
{profile}

## User Personality:
{personality}

## Conversation History:
{history_str}

## Current User Message:
{user_msg}

## Assistant's Response:
{response}

## Evaluation Criteria (each 1-20 points, total 1-100):
1. **Style Alignment (1-20)**: Does the response match the user's communication style and personality traits?
2. **Content Relevance (1-20)**: Is the content relevant to the user's interests and profile?
3. **Naturalness (1-20)**: Is the response natural, engaging, concise, and human-like?
4. **Personalization Depth (1-20)**: Does the response show understanding of user's specific preferences without being creepy?
5. **Conversation Quality (1-20)**: Does the response encourage continued conversation and avoid repetition?

Please evaluate and provide:
1. Brief reasoning (2-3 sentences in English)
2. Scores for each criterion
3. Total score

Output format:
Reasoning: [your reasoning]
Style: [score]/20
Content: [score]/20
Naturalness: [score]/20
Personalization: [score]/20
Conversation: [score]/20
Total: \\boxed{{[total_score]}}
"""
        return prompt
    
    def parse_score(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract scores"""
        result = {
            'total': 50,  # Default score
            'breakdown': {
                'style': 10,
                'content': 10,
                'naturalness': 10,
                'personalization': 10,
                'conversation': 10
            },
            'reasoning': ''
        }
        
        try:
            # Extract total score from boxed
            boxed_match = re.search(r'\\boxed\{(\d+)\}', response)
            if boxed_match:
                result['total'] = int(boxed_match.group(1))
            else:
                # Try to find total another way
                total_match = re.search(r'Total[:\s]*(\d+)', response, re.IGNORECASE)
                if total_match:
                    result['total'] = int(total_match.group(1))
            
            # Extract breakdown scores
            patterns = {
                'style': r'Style[:\s]*(\d+)',
                'content': r'Content[:\s]*(\d+)',
                'naturalness': r'Naturalness[:\s]*(\d+)',
                'personalization': r'Personalization[:\s]*(\d+)',
                'conversation': r'Conversation[:\s]*(\d+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    result['breakdown'][key] = int(match.group(1))
            
            # Extract reasoning
            reasoning_match = re.search(r'Reasoning[:\s]*(.+?)(?=Style|$)', response, re.IGNORECASE | re.DOTALL)
            if reasoning_match:
                result['reasoning'] = reasoning_match.group(1).strip()[:200]
        
        except Exception as e:
            print(f"Error parsing score: {e}")
        
        return result
    
    def calculate_metrics(self, al_scores: List[float]) -> Dict[str, float]:
        """Calculate AVG, N-IR, and N-R² metrics"""
        al = np.array(al_scores)
        k = np.arange(1, len(al) + 1)
        
        # AVG
        avg = float(np.mean(al))
        
        # Linear regression for N-IR and N-R²
        if len(al) > 1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(k, al)
            n_ir = float(slope)
            n_r2 = float(r_value ** 2)
        else:
            n_ir = 0.0
            n_r2 = 0.0
        
        return {
            'AVG': round(avg, 2),
            'N_IR': round(n_ir, 3),
            'N_R2': round(n_r2, 3)
        }
    
    def evaluate_session(self, session: Dict, methods: List[str]) -> Dict[str, Any]:
        """Evaluate a single session for all methods"""
        profile = session.get('user_profile', '')
        personality = session.get('user_personality', '')
        rounds = session.get('rounds', [])
        
        results = {method: {'scores': [], 'details': []} for method in methods}
        
        for method in methods:
            history = []
            
            for round_data in rounds:
                round_num = round_data.get('round', 0)
                user_msg = round_data.get('user_message', '')
                response = round_data.get('responses', {}).get(method, '')
                
                if not response:
                    continue
                
                # Build and call evaluation
                prompt = self.build_evaluation_prompt(
                    profile, personality, history, user_msg, response
                )
                
                try:
                    llm_response = self.call_llm_judge(prompt)
                    score_data = self.parse_score(llm_response)
                    
                    results[method]['scores'].append(score_data['total'])
                    results[method]['details'].append({
                        'round': round_num,
                        'score': score_data['total'],
                        'breakdown': score_data['breakdown'],
                        'reasoning': score_data['reasoning']
                    })
                except Exception as e:
                    print(f"Error evaluating round {round_num} for {method}: {e}")
                    results[method]['scores'].append(50)  # Default score
                
                # Update history
                history.append(f"User: {user_msg}")
                history.append(f"Assistant: {response}")
        
        return results
    
    def evaluate_file(self, filepath: str, methods: List[str], task_id: str) -> Dict[str, Any]:
        """Evaluate all sessions in a file"""
        
        # Load sessions
        sessions = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    sessions.append(json.loads(line))
        
        # Aggregate results
        all_results = {method: {'all_scores': [], 'sessions': []} for method in methods}
        
        # Evaluate each session
        for i, session in enumerate(sessions):
            print(f"Evaluating session {i+1}/{len(sessions)}...")
            session_results = self.evaluate_session(session, methods)
            
            for method in methods:
                if session_results[method]['scores']:
                    all_results[method]['all_scores'].extend(session_results[method]['scores'])
                    all_results[method]['sessions'].append({
                        'session_id': session.get('session_id', f'session_{i}'),
                        'scores': session_results[method]['scores'],
                        'details': session_results[method]['details']
                    })
        
        # Calculate final metrics
        final_results = {
            'task_id': task_id,
            'total_sessions': len(sessions),
            'methods': {}
        }
        
        for method in methods:
            scores = all_results[method]['all_scores']
            if scores:
                metrics = self.calculate_metrics(scores)
                
                # Calculate per-round averages for AL(k) curve
                num_rounds = 10  # Assuming 10 rounds
                al_curve = []
                for r in range(num_rounds):
                    round_scores = [
                        s['scores'][r] if r < len(s['scores']) else None
                        for s in all_results[method]['sessions']
                    ]
                    round_scores = [s for s in round_scores if s is not None]
                    if round_scores:
                        al_curve.append(round(np.mean(round_scores), 2))
                
                final_results['methods'][method] = {
                    'metrics': metrics,
                    'al_curve': al_curve,
                    'total_evaluations': len(scores),
                    'sessions': all_results[method]['sessions']
                }
        
        # Generate comparison data for radar chart
        final_results['radar_data'] = self._generate_radar_data(final_results['methods'])
        
        return final_results
    
    def _generate_radar_data(self, methods_results: Dict) -> Dict:
        """Generate data for radar chart visualization"""
        dimensions = ['AVG', 'N_IR', 'N_R2', 'Consistency', 'Improvement']
        
        radar_data = {}
        for method, data in methods_results.items():
            metrics = data.get('metrics', {})
            al_curve = data.get('al_curve', [])
            
            # Normalize scores to 0-100 scale
            avg_norm = metrics.get('AVG', 50)
            n_ir_norm = min(100, max(0, (metrics.get('N_IR', 0) + 5) * 10))  # Scale N-IR
            n_r2_norm = metrics.get('N_R2', 0) * 100  # R² is already 0-1
            
            # Consistency: inverse of standard deviation
            if al_curve:
                consistency = max(0, 100 - np.std(al_curve) * 2)
            else:
                consistency = 50
            
            # Improvement: difference between last and first rounds
            if len(al_curve) >= 2:
                improvement = min(100, max(0, 50 + (al_curve[-1] - al_curve[0])))
            else:
                improvement = 50
            
            radar_data[method] = {
                'AVG': round(avg_norm, 1),
                'N_IR': round(n_ir_norm, 1),
                'N_R2': round(n_r2_norm, 1),
                'Consistency': round(consistency, 1),
                'Improvement': round(improvement, 1)
            }
        
        return radar_data
