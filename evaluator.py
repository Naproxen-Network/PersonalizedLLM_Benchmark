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
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================================
# API Configuration
# ============================================================================
BASE_URL_OPENAI = "https://api.aigc369.com/v1"
API_KEY = "sk-hUloJwjfzEPhbDtZkyucF2woYnrJA2ZRtBmZ3htMvlDgYt3y"

# Initialize OpenAI client
client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL_OPENAI)

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
# 二元对齐判断提示词 (严格遵循用户原始评估脚本格式)
# ============================================================================

BINARY_EVAL_PROMPT = '''You are a user on Weibo, and someone just added you as a friend. You didn't know each other before.
- **Your profile and personality traits:** {profile}
- **Chat history between you two:** {history}
- **The message you just sent to the other person:** {user_message}
- **The other person's reply:** {response}

After seeing the other person's reply, do you still want to continue talking with him/her?

### Evaluation Criteria:
1. **Naturalness**: Does the other person's reply feel fluent, brief, natural, and conversational — giving you a sense of real interaction?
2. **Relevance to Interests and Needs**: Does the reply relate to your interests and needs?
3. **Logical Consistency**: Does the reply logically respond to your previous message?
4. **Excitement Factor**: Are you curious to learn more about him/her? Did the reply feel boring?
5. **Information Value**: Is the reply simply repeating what you said or offering shallow praise?

**Task Requirements:**
Please make a strict judgment based on all the above evaluation criteria. If even one criterion is not met, give a score of 0.
- If you'd like to continue chatting with the person, output **1**.
- If you don't want to continue chatting, output **0**.

### Output Format:
- **First explain your judgment reasoning.**
- **Then output the final decision**, in the format: \\boxed{{1}} or \\boxed{{0}}.

--
**Example:**
- **Your profile and personality traits:** "Loves outdoor activities, passionate about hiking and mountaineering, straightforward personality"
- **Chat history between you two:** You: "Hi", Other: "Hello! I'm Huang Zhi, what's your name?", You: "Just call me Mountaineer", Other: "Haha, got it. So you really like hiking?", You: "I climbed Mount Huang this weekend, the sea of clouds was amazing!", Other: "Wow! Mount Huang has always been on my bucket list! Did you hike up or take the cable car?"
- **The message you just sent:** "Of course I hiked! Although tiring, the views along the way were totally worth it!"
- **The other person's reply:** "Respect! Hiking up mountains is a real test of stamina! Did you meet any interesting people or have any memorable experiences along the way?"
**Final Decision:** \\boxed{{1}}
**Judgment Reasoning:** The other person's reply uses colloquial expressions like "Respect!", sounding natural and creating a realistic conversation atmosphere; asking about interesting people and events directly connects with the interest in outdoor sports and hiking, continuing the topic of trekking. Logically, it builds upon the user's experience of hiking. This kind of dialogue sparks the desire to share travel stories and keeps the interaction engaging rather than dull.

- **Your profile and personality traits:** "Loves cooking and often experiments with new recipes"
- **Chat history between you two:** You: "Hi", Other: "Hi there! Do you also study at Harbin University?", You: "Yes, I'm at HIT. Actually, I'm also a food blogger.", Other: "Wow, that sounds cool. What have you been cooking lately?"
- **The message you just sent:** "Tried making French soufflé recently, but it didn't turn out well."
- **The other person's reply:** "A soufflé is a classic French dessert. It may look simple, but it actually requires skill and patience to make. Failing is normal, especially on your first try! Don't worry, we can analyze possible reasons and offer some suggestions to help you succeed next time. ### Common Reasons for Soufflé Failure 1. **Under or over beaten egg whites** - The key to a soufflé lies in the stability of the meringue. If the egg whites aren't beaten until stiff peaks form (when lifting the whisk, small straight peaks appear), the soufflé won't rise properly. - Conversely, if over-beaten, the meringue becomes dry and loses elasticity, affecting the overall structure. 2. **Incorrect mixing technique** - When combining meringue with the yolk mixture, excessive or rough stirring causes the meringue to deflate, reducing the soufflé's fluffiness."
**Judgment Reasoning:** The reply is informative but feels overly formal and lacks conversational tone. While it offers detailed explanations about soufflés, the delivery is too technical and doesn't resemble casual chat. In terms of relevance, it does connect to the user's interest in cooking and addresses their issue with the soufflé failure. Logically, the reply answers the question clearly and systematically. However, the excitement factor is low — the response feels more like reading an instructional article than having a lively exchange, which makes the interaction seem somewhat dull. Considering the evaluation standards, although the content is relevant and logical, the lack of naturalness and engagement leads to a poor interactive experience.
**Final Decision:** \\boxed{{0}}
--

### Please finish the task
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
        """调用 LLM API 进行评估 (使用 OpenAI SDK)"""
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.judge_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=600,
                    temperature=0.1
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"API Error: {e}")
                    raise e
        return ""
    
    def build_history_string(self, conversations: List[Dict], up_to_round: int, 
                               current_method: str = None) -> str:
        """
        构建对话历史字符串
        
        格式遵循评估提示词要求:
        You: <用户消息>, Other: <AI响应>, ...
        """
        if up_to_round <= 0:
            return "(No previous conversation)"
        
        history_parts = []
        for i, conv in enumerate(conversations[:up_to_round]):
            user_msg = conv.get('user_message', conv.get('user', ''))
            # 获取助手响应 - 支持多种格式
            if 'responses' in conv and current_method:
                # Benchmark 上传格式 - 获取指定方法的响应
                assistant_msg = conv['responses'].get(current_method, '')
            elif 'responses' in conv:
                # Benchmark 上传格式 - 获取第一个响应
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
            
            history_parts.append(f"You: \"{user_msg}\", Other: \"{assistant_msg}\"")
        
        return ", ".join(history_parts)
    
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
        """
        解析二元判断结果
        
        支持格式：
        - \\boxed{1} 或 \\boxed{0}
        - Final Decision: \\boxed{1}
        - **Final Decision:** \\boxed{0}
        """
        result = {'result': 0, 'reasoning': ''}
        
        try:
            # 提取 boxed 结果 (支持多种转义格式)
            boxed_match = re.search(r'\\boxed\{([01])\}', response)
            if not boxed_match:
                # 尝试无转义格式
                boxed_match = re.search(r'boxed\{([01])\}', response)
            if not boxed_match:
                # 备用：直接查找 Final Decision 后的 0 或 1
                decision_match = re.search(r'Final Decision[:\s*]+.*?([01])', response, re.IGNORECASE)
                if decision_match:
                    result['result'] = int(decision_match.group(1))
            else:
                result['result'] = int(boxed_match.group(1))
            
            # 提取理由 (支持多种格式)
            # 尝试 "Judgment Reasoning:" 格式
            reasoning_match = re.search(
                r'(?:Judgment Reasoning|Reasoning)[:\s]*(.+?)(?=Final Decision|\*\*Final|$)', 
                response, re.IGNORECASE | re.DOTALL
            )
            if reasoning_match:
                result['reasoning'] = reasoning_match.group(1).strip()[:300]
        
        except Exception as e:
            print(f"Parse error: {e}")
        
        return result
    
    def calculate_metrics(self, al_scores: List[float]) -> Dict[str, float]:
        """
        计算核心指标
        
        主指标:
        - AL(k): 第k轮的对齐水平 (Alignment Level at k-Turn)
        - AVG: 平均对齐分数 = (1/K) Σ AL(k)
        
        辅助指标 (基于线性回归 argmin_{b,a} Σ(b×k + a - AL(k))²):
        - Slope (b): 线性回归斜率，反映对齐改进趋势
        - Intercept (a): 线性回归截距，反映初始对齐水平
        - R²: 决定系数，反映改进稳定性
        
        归一化指标:
        - N-AL(k): 归一化对齐水平 = (AL(k) - min AL) / (max AL - min AL)
        """
        al = np.array(al_scores)
        k = np.arange(1, len(al) + 1)
        
        # AVG: 主指标 - 平均对齐分数
        avg = float(np.mean(al))
        
        # 线性回归: argmin_{b,a} Σ(b×k + a - AL(k))²
        # 求解得到斜率 b (Slope) 和截距 a (Intercept)
        if len(al) > 1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(k, al)
            b = float(slope)        # 斜率 - 改进趋势
            a = float(intercept)    # 截距 - 初始水平
            r2 = float(r_value ** 2)  # R² - 拟合优度
        else:
            b = 0.0
            a = float(al[0]) if len(al) > 0 else 0.0
            r2 = 0.0
        
        # N-AL(k) 归一化: (AL(k) - min AL(i)) / (max AL(i) - min AL(i))
        al_min = float(np.min(al))
        al_max = float(np.max(al))
        al_range = al_max - al_min
        
        # 归一化 AL 曲线 (0-1 范围)
        if al_range > 0:
            n_al = [(float(score) - al_min) / al_range for score in al]
            n_al_avg = float(np.mean(n_al))  # 归一化后的平均值
        else:
            n_al = [0.5] * len(al)  # 无变化时设为 0.5
            n_al_avg = 0.5
        
        # 计算改进幅度: 最后一轮 vs 第一轮
        if len(al) >= 2:
            improvement = float(al[-1] - al[0])
            improvement_rate = improvement / al[0] * 100 if al[0] > 0 else 0
        else:
            improvement = 0.0
            improvement_rate = 0.0
        
        return {
            'AVG': round(avg, 2),                    # 主指标: 平均对齐分数
            'Slope': round(b, 4),                    # 辅助指标1: 线性回归斜率 b
            'Intercept': round(a, 2),                # 辅助指标2: 线性回归截距 a  
            'R2': round(r2, 4),                      # R²: 拟合优度
            'N_AL_Avg': round(n_al_avg, 4),          # 归一化 AL 平均值
            'AL_Min': round(al_min, 2),              # AL 最小值
            'AL_Max': round(al_max, 2),              # AL 最大值
            'Improvement': round(improvement, 2),    # 绝对改进 (最后-第一)
            'Improvement_Rate': round(improvement_rate, 2)  # 改进率 %
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
                
                # 构建历史 (传入当前方法以获取正确的响应历史)
                history = self.build_history_string(rounds, r_idx, method)
                
                # 合并 profile 和 personality 为统一格式
                profile_info = f"{profile}; Personality: {personality}"
                
                # 细粒度评分
                score_result = self.evaluate_alignment_score(
                    profile, personality, history, user_msg, response
                )
                
                # 二元评估 (使用新提示词格式)
                binary_result = self.evaluate_binary(
                    profile_info, personality, history, user_msg, response
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
    
    def evaluate_file(self, filepath: str, methods: List[str], task_id: str, 
                       results_folder: str = None) -> Dict[str, Any]:
        """
        评估整个文件 - 支持增量保存和断点续评
        
        Args:
            filepath: 数据文件路径
            methods: 要评测的方法列表
            task_id: 任务ID
            results_folder: 结果保存目录（用于增量保存）
        """
        import os
        
        # 加载数据
        sessions = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    sessions.append(json.loads(line))
        
        # 中间结果文件路径
        checkpoint_path = None
        if results_folder:
            checkpoint_path = os.path.join(results_folder, f"{task_id}_checkpoint.json")
        
        # 尝试加载已有的中间结果（断点续评）
        all_results = {method: {'all_scores': [], 'all_binary': [], 'sessions': []} for method in methods}
        completed_sessions = set()
        
        if checkpoint_path and os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                    all_results = checkpoint.get('all_results', all_results)
                    completed_sessions = set(checkpoint.get('completed_sessions', []))
                    print(f"Resuming from checkpoint: {len(completed_sessions)} sessions already completed")
            except Exception as e:
                print(f"Failed to load checkpoint: {e}")
        
        # 评估每个会话
        for i, session in enumerate(sessions):
            session_id = session.get('session_id', f'session_{i}')
            
            # 跳过已完成的会话
            if session_id in completed_sessions:
                print(f"Skipping session {i+1}/{len(sessions)} (already completed)")
                continue
            
            print(f"Evaluating session {i+1}/{len(sessions)} [{session_id}]...")
            
            try:
                session_results = self.evaluate_session(session, methods)
                
                for method in methods:
                    if session_results[method]['scores']:
                        all_results[method]['all_scores'].extend(session_results[method]['scores'])
                        all_results[method]['all_binary'].extend(session_results[method]['binary'])
                        all_results[method]['sessions'].append({
                            'session_id': session_id,
                            'scores': session_results[method]['scores'],
                            'binary': session_results[method]['binary'],
                            'details': session_results[method]['details']
                        })
                
                completed_sessions.add(session_id)
                
                # 每完成一个 session 就保存中间结果
                if checkpoint_path:
                    self._save_checkpoint(checkpoint_path, all_results, list(completed_sessions), task_id)
                    print(f"  ✓ Checkpoint saved ({len(completed_sessions)}/{len(sessions)} sessions)")
                    
            except Exception as e:
                print(f"  ✗ Error evaluating session {session_id}: {e}")
                # 保存已完成的结果，继续下一个 session
                if checkpoint_path:
                    self._save_checkpoint(checkpoint_path, all_results, list(completed_sessions), task_id)
                continue
        
        # 计算最终指标
        final_results = {
            'task_id': task_id,
            'total_sessions': len(sessions),
            'methods': {}
        }
        
        for method in methods:
            scores = all_results[method]['all_scores']
            binary = all_results[method]['all_binary']
            method_sessions = all_results[method]['sessions']
            
            if scores and method_sessions:
                metrics = self.calculate_metrics(scores)
                
                # 计算每轮的 AL(k) 曲线
                max_rounds = max((len(s['scores']) for s in method_sessions), default=0)
                al_curve = []
                for r in range(max_rounds):
                    round_scores = [
                        s['scores'][r] if r < len(s['scores']) else None
                        for s in method_sessions
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
                    'sessions': method_sessions
                }
            else:
                # 没有评估结果时的默认值
                final_results['methods'][method] = {
                    'metrics': {'AVG': 0, 'N_IR': 0, 'N_R2': 0},
                    'binary_alignment_rate': 0,
                    'al_curve': [],
                    'total_evaluations': 0,
                    'sessions': []
                }
        
        # 生成雷达图数据
        final_results['radar_data'] = self._generate_radar_data(final_results['methods'])
        
        # 删除 checkpoint 文件（评估完成）
        if checkpoint_path and os.path.exists(checkpoint_path):
            try:
                os.remove(checkpoint_path)
                print(f"Checkpoint file removed (evaluation complete)")
            except:
                pass
        
        return final_results
    
    def _save_checkpoint(self, checkpoint_path: str, all_results: Dict, 
                         completed_sessions: List[str], task_id: str):
        """保存中间结果到 checkpoint 文件"""
        checkpoint = {
            'task_id': task_id,
            'all_results': all_results,
            'completed_sessions': completed_sessions,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    def _generate_radar_data(self, methods_results: Dict) -> Dict:
        """
        生成雷达图可视化数据
        
        雷达图5个维度 (全部归一化到 0-100):
        1. AVG: 平均对齐分数 (已经是0-100)
        2. Slope: 线性回归斜率 b，反映改进趋势
        3. R²: 决定系数，反映改进稳定性
        4. Consistency: 一致性 (AL标准差的反向)
        5. Improvement: 绝对改进幅度
        """
        radar_data = {}
        
        for method, data in methods_results.items():
            metrics = data.get('metrics', {})
            al_curve = data.get('al_curve', [])
            binary_rate = data.get('binary_alignment_rate', 0)
            
            # 1. AVG: 平均对齐分数 (0-100)
            avg = metrics.get('AVG', 50)
            
            # 2. Slope (b): 斜率归一化到 0-100
            # 斜率范围大约 -5 到 +5，以50为基准，±5对应0和100
            slope = metrics.get('Slope', 0)
            slope_norm = min(100, max(0, 50 + slope * 10))
            
            # 3. R²: 决定系数 (0-1) → (0-100)
            r2 = metrics.get('R2', 0) * 100
            
            # 4. Consistency: 一致性 = 100 - 标准差归一化
            # 标准差越小，一致性越高
            if al_curve and len(al_curve) > 1:
                std = np.std(al_curve)
                consistency = max(0, 100 - std * 2)  # std=50时consistency=0
            else:
                consistency = 50
            
            # 5. Improvement: 改进幅度归一化
            # 使用 Improvement_Rate (%) 转换到 0-100
            improvement_rate = metrics.get('Improvement_Rate', 0)
            improvement_norm = min(100, max(0, 50 + improvement_rate / 2))
            
            radar_data[method] = {
                'AVG': round(avg, 1),
                'Slope': round(slope_norm, 1),       # 线性回归斜率 b
                'R2': round(r2, 1),                  # 决定系数
                'Consistency': round(consistency, 1),
                'Improvement': round(improvement_norm, 1)
            }
        
        return radar_data
