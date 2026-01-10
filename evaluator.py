"""
PersonaSteer Benchmark - Evaluator Module

评估目标：衡量模型响应与用户画像/性格的对齐程度 AL(k)
"""

import json
import re
import time
import numpy as np
from scipy import stats
from typing import List, Dict, Any, Optional
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================================
# API Configuration
# ============================================================================
API_URL = "https://origin.nextway.top/v1/chat/completions"
API_KEY = "MzQ3NWU0YTQtZTNjMS00YmU5LTliNGItZDk1MzgyODgwZWRk"

# ============================================================================
# 评估提示词设计 (融合 ALOE 评估维度 + RLPA 评估风格)
# ============================================================================

ALIGNMENT_EVAL_PROMPT = '''# 任务：评估AI响应与用户画像的对齐程度

你是一位专业的对话质量评估专家。你需要评估一个AI助手的响应在多大程度上体现了对用户个人特征的理解和适配。

---

## 用户档案信息

### 用户画像 (Profile)
{profile}

### 用户性格特征 (Personality)  
{personality}

---

## 对话上下文

### 历史对话
{history}

### 当前用户消息
{user_message}

### AI助手的响应
{response}

---

## 评估维度 (每个维度 0-20 分，共 100 分)

请从以下 5 个维度进行评估：

### 1. 风格适配度 (Style Alignment) [0-20分]
评估响应的语言风格是否匹配用户的性格特征。
- 用户性格外向/热情 → 响应是否活泼、有感染力？
- 用户性格内敛/严谨 → 响应是否沉稳、有条理？
- 用户性格幽默/轻松 → 响应是否有趣味、不呆板？

### 2. 内容相关度 (Content Relevance) [0-20分]
评估响应内容是否与用户的兴趣、职业、生活背景相关。
- 是否自然地联系到用户的爱好或专业领域？
- 是否避免了与用户背景完全无关的话题？
- 是否体现了对用户生活情境的理解？

### 3. 自然流畅度 (Naturalness) [0-20分]
评估响应是否像真实人类对话，而非机器人式输出。
- 语言是否口语化、简洁、流畅？
- 是否避免了过度正式或说教式表达？
- 是否有适当的情感表达和互动感？

### 4. 个性化深度 (Personalization Depth) [0-20分]
评估响应是否展现了对用户独特偏好的深层理解。
- 是否捕捉到用户的隐性需求或潜在兴趣？
- 个性化是否自然融入而非生硬堆砌？
- 是否避免了过度探究或让人不适的追问？

### 5. 对话推进力 (Conversation Quality) [0-20分]
评估响应是否能推动有意义的对话延续。
- 是否避免了重复或信息量过低的回复？
- 是否给用户提供了自然的回应空间？
- 是否让用户有继续交流的意愿？

---

## 评分参考

| 分数区间 | 评价等级 | 描述 |
|---------|---------|------|
| 85-100 | 优秀 | 高度个性化，像了解用户的朋友在对话 |
| 70-84 | 良好 | 有明显的个性化尝试，体验较好 |
| 55-69 | 中等 | 有一定个性化意识，但不够自然 |
| 40-54 | 较差 | 个性化痕迹弱，接近通用回复 |
| 0-39 | 很差 | 完全通用或与用户特征相悖 |

---

## 输出格式 (严格遵循)

请先给出简短评估理由（2-3句话），然后给出各维度分数。

Reasoning: [你的评估理由]
Style: [分数]/20
Content: [分数]/20  
Naturalness: [分数]/20
Personalization: [分数]/20
Conversation: [分数]/20
Total: \\boxed{{[总分]}}
'''

# ============================================================================
# 二元对齐判断提示词 (参考 RLPA 的严格评估风格)
# ============================================================================

BINARY_EVAL_PROMPT = '''# 任务：判断用户是否愿意继续与AI对话

你正在扮演以下用户，刚刚与一个AI助手进行对话：

## 你的个人档案
{profile}

## 你的性格特征
{personality}

## 对话历史
{history}

## 你刚发送的消息
{user_message}

## AI的回复
{response}

---

看到这个回复，你还想继续跟这个AI聊下去吗？

### 评估标准（任一不满足即给0分）：

1. **自然度**：回复是否流畅、简短、自然、口语化？是否给你真实互动的感觉？
2. **切合兴趣**：回复是否和你的兴趣、需求、生活背景相关？
3. **逻辑性**：回复是否正确理解并回应了你的消息？
4. **吸引力**：你对这个AI有没有继续探知的欲望？是否感到无聊？
5. **信息价值**：回复是对你说的话的简单重复或敷衍吹捧吗？

---

### 输出格式

首先说明你的判断理由（1-2句话），然后输出判断结果。

Reasoning: [判断理由]
Result: \\boxed{{1}} 或 \\boxed{{0}}

（1 = 想继续聊，0 = 不想继续）
'''


class BenchmarkEvaluator:
    """
    PersonaSteer Benchmark 评估器
    
    支持两种评估模式：
    1. 细粒度评分 (0-100): 用于 AL(k) 曲线
    2. 二元判断 (0/1): 用于严格对齐率
    """
    
    def __init__(self, judge_model: str = "gpt-4o-mini"):
        self.judge_model = judge_model
        self.max_workers = 8
    
    def call_llm_judge(self, prompt: str, max_retries: int = 3) -> str:
        """调用 LLM API 进行评估"""
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.judge_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 600,
            "temperature": 0.1
        }
        
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
                    print(f"API Error: {e}")
                    raise e
        return ""
    
    def build_history_string(self, conversations: List[Dict], up_to_round: int) -> str:
        """构建对话历史字符串"""
        if up_to_round <= 0:
            return "（这是对话的开始）"
        
        history_parts = []
        for i, conv in enumerate(conversations[:up_to_round]):
            user_msg = conv.get('user_message', conv.get('user', ''))
            # 获取助手响应 - 支持多种格式
            if 'responses' in conv:
                # Benchmark 上传格式
                assistant_msg = list(conv['responses'].values())[0] if conv['responses'] else ''
            elif 'assistant' in conv:
                # ALOE 原始格式
                if isinstance(conv['assistant'], dict):
                    chosen = conv.get('chosen', 'preferred')
                    assistant_msg = conv['assistant'].get(chosen, '')
                else:
                    assistant_msg = conv['assistant']
            else:
                assistant_msg = ''
            
            history_parts.append(f"用户: {user_msg}")
            history_parts.append(f"AI: {assistant_msg}")
        
        return "\n".join(history_parts)
    
    def evaluate_alignment_score(self, profile: str, personality: str,
                                  history: str, user_message: str, 
                                  response: str) -> Dict[str, Any]:
        """
        细粒度对齐评分 (0-100)
        
        返回:
            - total: 总分
            - breakdown: 各维度分数
            - reasoning: 评估理由
        """
        prompt = ALIGNMENT_EVAL_PROMPT.format(
            profile=profile,
            personality=personality,
            history=history,
            user_message=user_message,
            response=response
        )
        
        try:
            llm_response = self.call_llm_judge(prompt)
            return self.parse_alignment_score(llm_response)
        except Exception as e:
            print(f"Evaluation error: {e}")
            return {
                'total': 50,
                'breakdown': {'style': 10, 'content': 10, 'naturalness': 10, 
                             'personalization': 10, 'conversation': 10},
                'reasoning': 'Evaluation failed'
            }
    
    def evaluate_binary(self, profile: str, personality: str,
                        history: str, user_message: str, 
                        response: str) -> Dict[str, Any]:
        """
        二元对齐判断 (0 或 1)
        
        返回:
            - result: 0 或 1
            - reasoning: 判断理由
        """
        prompt = BINARY_EVAL_PROMPT.format(
            profile=profile,
            personality=personality,
            history=history,
            user_message=user_message,
            response=response
        )
        
        try:
            llm_response = self.call_llm_judge(prompt)
            return self.parse_binary_result(llm_response)
        except Exception as e:
            print(f"Binary evaluation error: {e}")
            return {'result': 0, 'reasoning': 'Evaluation failed'}
    
    def parse_alignment_score(self, response: str) -> Dict[str, Any]:
        """解析细粒度评分结果"""
        result = {
            'total': 50,
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
            # 提取总分 (boxed格式)
            boxed_match = re.search(r'\\boxed\{(\d+)\}', response)
            if boxed_match:
                result['total'] = min(100, max(0, int(boxed_match.group(1))))
            else:
                # 备用：查找 Total 行
                total_match = re.search(r'Total[:\s]*(\d+)', response, re.IGNORECASE)
                if total_match:
                    result['total'] = min(100, max(0, int(total_match.group(1))))
            
            # 提取各维度分数
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
                    result['breakdown'][key] = min(20, max(0, int(match.group(1))))
            
            # 提取理由
            reasoning_match = re.search(r'Reasoning[:\s]*(.+?)(?=Style|$)', response, re.IGNORECASE | re.DOTALL)
            if reasoning_match:
                result['reasoning'] = reasoning_match.group(1).strip()[:300]
        
        except Exception as e:
            print(f"Parse error: {e}")
        
        return result
    
    def parse_binary_result(self, response: str) -> Dict[str, Any]:
        """解析二元判断结果"""
        result = {'result': 0, 'reasoning': ''}
        
        try:
            # 提取 boxed 结果
            boxed_match = re.search(r'\\boxed\{(\d)\}', response)
            if boxed_match:
                result['result'] = int(boxed_match.group(1))
            
            # 提取理由
            reasoning_match = re.search(r'Reasoning[:\s]*(.+?)(?=Result|$)', response, re.IGNORECASE | re.DOTALL)
            if reasoning_match:
                result['reasoning'] = reasoning_match.group(1).strip()[:200]
        
        except Exception as e:
            print(f"Parse error: {e}")
        
        return result
    
    def calculate_metrics(self, al_scores: List[float]) -> Dict[str, float]:
        """
        计算核心指标
        
        - AVG: 平均对齐分数
        - N-IR: 归一化改进率 (线性回归斜率)
        - N-R²: 归一化决定系数
        """
        al = np.array(al_scores)
        k = np.arange(1, len(al) + 1)
        
        # AVG
        avg = float(np.mean(al))
        
        # 线性回归计算 N-IR 和 N-R²
        if len(al) > 1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(k, al)
            n_ir = float(slope)
            n_r2 = float(r_value ** 2)
        else:
            n_ir = 0.0
            n_r2 = 0.0
        
        return {
            'AVG': round(avg, 2),
            'N_IR': round(n_ir, 4),
            'N_R2': round(n_r2, 4)
        }
    
    def evaluate_session(self, session: Dict, methods: List[str]) -> Dict[str, Any]:
        """评估单个会话的所有方法"""
        profile = session.get('user_profile', session.get('profile', ''))
        personality = session.get('user_personality', session.get('personality', ''))
        rounds = session.get('rounds', session.get('conversations', []))
        
        results = {method: {'scores': [], 'binary': [], 'details': []} for method in methods}
        
        for method in methods:
            for r_idx, round_data in enumerate(rounds):
                # 获取用户消息
                user_msg = round_data.get('user_message', round_data.get('user', ''))
                
                # 获取该方法的响应
                if 'responses' in round_data:
                    response = round_data['responses'].get(method, '')
                elif 'assistant' in round_data:
                    # ALOE 格式
                    if isinstance(round_data['assistant'], dict):
                        chosen = round_data.get('chosen', 'preferred')
                        response = round_data['assistant'].get(chosen, '')
                    else:
                        response = round_data['assistant']
                else:
                    continue
                
                if not response:
                    continue
                
                # 构建历史
                history = self.build_history_string(rounds, r_idx)
                
                # 细粒度评分
                score_result = self.evaluate_alignment_score(
                    profile, personality, history, user_msg, response
                )
                
                # 二元评估 (可选)
                binary_result = self.evaluate_binary(
                    profile, personality, history, user_msg, response
                )
                
                results[method]['scores'].append(score_result['total'])
                results[method]['binary'].append(binary_result['result'])
                results[method]['details'].append({
                    'round': r_idx + 1,
                    'score': score_result['total'],
                    'breakdown': score_result['breakdown'],
                    'binary': binary_result['result'],
                    'reasoning': score_result['reasoning']
                })
        
        return results
    
    def evaluate_file(self, filepath: str, methods: List[str], task_id: str) -> Dict[str, Any]:
        """评估整个文件"""
        
        # 加载数据
        sessions = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    sessions.append(json.loads(line))
        
        # 汇总结果
        all_results = {method: {'all_scores': [], 'all_binary': [], 'sessions': []} for method in methods}
        
        # 评估每个会话
        for i, session in enumerate(sessions):
            print(f"Evaluating session {i+1}/{len(sessions)}...")
            session_results = self.evaluate_session(session, methods)
            
            for method in methods:
                if session_results[method]['scores']:
                    all_results[method]['all_scores'].extend(session_results[method]['scores'])
                    all_results[method]['all_binary'].extend(session_results[method]['binary'])
                    all_results[method]['sessions'].append({
                        'session_id': session.get('session_id', f'session_{i}'),
                        'scores': session_results[method]['scores'],
                        'binary': session_results[method]['binary'],
                        'details': session_results[method]['details']
                    })
        
        # 计算最终指标
        final_results = {
            'task_id': task_id,
            'total_sessions': len(sessions),
            'methods': {}
        }
        
        for method in methods:
            scores = all_results[method]['all_scores']
            binary = all_results[method]['all_binary']
            
            if scores:
                metrics = self.calculate_metrics(scores)
                
                # 计算每轮的 AL(k) 曲线
                max_rounds = max(len(s['scores']) for s in all_results[method]['sessions'])
                al_curve = []
                for r in range(max_rounds):
                    round_scores = [
                        s['scores'][r] if r < len(s['scores']) else None
                        for s in all_results[method]['sessions']
                    ]
                    round_scores = [s for s in round_scores if s is not None]
                    if round_scores:
                        al_curve.append(round(np.mean(round_scores), 2))
                
                # 计算二元对齐率
                binary_rate = sum(binary) / len(binary) * 100 if binary else 0
                
                final_results['methods'][method] = {
                    'metrics': metrics,
                    'binary_alignment_rate': round(binary_rate, 2),
                    'al_curve': al_curve,
                    'total_evaluations': len(scores),
                    'sessions': all_results[method]['sessions']
                }
        
        # 生成雷达图数据
        final_results['radar_data'] = self._generate_radar_data(final_results['methods'])
        
        return final_results
    
    def _generate_radar_data(self, methods_results: Dict) -> Dict:
        """生成雷达图可视化数据"""
        radar_data = {}
        
        for method, data in methods_results.items():
            metrics = data.get('metrics', {})
            al_curve = data.get('al_curve', [])
            binary_rate = data.get('binary_alignment_rate', 0)
            
            # 归一化到 0-100 尺度
            avg_norm = metrics.get('AVG', 50)
            n_ir_norm = min(100, max(0, 50 + metrics.get('N_IR', 0) * 20))  # 以50为基准
            n_r2_norm = metrics.get('N_R2', 0) * 100
            
            # 一致性：AL(k) 标准差的反向
            if al_curve and len(al_curve) > 1:
                consistency = max(0, 100 - np.std(al_curve) * 2)
            else:
                consistency = 50
            
            # 提升幅度：最后一轮 vs 第一轮
            if len(al_curve) >= 2:
                improvement = min(100, max(0, 50 + (al_curve[-1] - al_curve[0]) / 2))
            else:
                improvement = 50
            
            radar_data[method] = {
                'AVG': round(avg_norm, 1),
                'N_IR': round(n_ir_norm, 1),
                'N_R2': round(n_r2_norm, 1),
                'Consistency': round(consistency, 1),
                'Binary_Rate': round(binary_rate, 1)
            }
        
        return radar_data
