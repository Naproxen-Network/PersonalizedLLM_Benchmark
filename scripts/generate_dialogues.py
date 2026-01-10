"""
对话生成脚本 - 用于客户端生成测试数据
Dialogue Generation Script - For client-side test data generation

使用方法 / Usage:
    python generate_dialogues.py --profiles data/profiles.jsonl --output data/benchmark_input.jsonl
"""

import json
import argparse
import os
from typing import List, Dict, Any
import requests

# User Simulator Prompt (参考 RLPA)
USER_SIM_PROMPT = '''# 任务：模拟真实用户进行多轮对话

## 你的身份
你正在扮演一个真实的用户，根据以下profile和personality进行对话。

### 用户画像 (Profile)
{profile}

### 用户性格 (Personality)
{personality}

## 核心交互规则

### 1. 信息渐进释放机制
- 第1-2轮：仅透露最表面的信息，保持警惕
- 第3-4轮：逐渐展露一些兴趣爱好
- 第5-7轮：分享更深层的想法和经历
- 第8轮以后：如果对方足够有趣，可以深入交流

### 2. 社交态度递进原则
- 初期：礼貌但保持距离
- 中期：根据对方回复质量调整态度
- 后期：如果感觉舒适，展现真实自我

### 3. 真实社交模拟准则
- 使用口语化、简短的表达
- 偶尔使用表情或语气词
- 可以表达困惑、好奇、无聊等真实情绪
- 不要刻意提及profile中的所有信息

## 对话历史
{history}

## 输出
直接输出你作为用户的下一条消息（简短、自然、口语化）。不要解释你在做什么。
'''


def load_profiles(filepath: str) -> List[Dict]:
    """加载用户画像"""
    profiles = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                profiles.append(json.loads(line))
    return profiles


def call_user_simulator(profile: str, personality: str, history: List[str], api_url: str, api_key: str) -> str:
    """调用用户模拟器生成消息"""
    history_str = "\n".join(history) if history else "（这是对话的开始）"
    
    prompt = USER_SIM_PROMPT.format(
        profile=profile,
        personality=personality,
        history=history_str
    )
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.8
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling user simulator: {e}")
        return "嗨，你好！"


def call_model(model_name: str, user_message: str, history: List[str], 
               profile: str = None, api_url: str = None, api_key: str = None) -> str:
    """调用被测模型生成响应
    
    这里是示例实现，实际使用时需要根据你的模型接口进行修改
    """
    
    # 构建消息历史
    messages = []
    for i, msg in enumerate(history):
        role = "user" if i % 2 == 0 else "assistant"
        messages.append({"role": role, "content": msg})
    messages.append({"role": "user", "content": user_message})
    
    # 对于 Base 模型：普通对话
    if model_name == "Base":
        system_prompt = "You are a helpful and friendly assistant."
    
    # 对于 PersonaSteer / RAG 等方法：可以注入 profile 信息
    elif model_name == "PersonaSteer":
        system_prompt = f"""You are a personalized assistant. 
Known user context: {profile}
Respond naturally and show understanding of the user's interests and style."""
    
    else:
        system_prompt = "You are a helpful assistant."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling model {model_name}: {e}")
        return "I'm here to help!"


def generate_session(profile_data: Dict, methods: List[str], num_rounds: int,
                     api_url: str, api_key: str) -> Dict:
    """为单个用户生成完整的多轮对话会话"""
    
    profile = profile_data.get('profile', '')
    personality = profile_data.get('personality', '')
    user_id = profile_data.get('id', 'unknown')
    
    session = {
        "session_id": f"user_{user_id}_session_001",
        "user_profile": profile,
        "user_personality": personality,
        "rounds": []
    }
    
    # 每个方法维护独立的对话历史
    method_histories = {method: [] for method in methods}
    
    for round_num in range(1, num_rounds + 1):
        print(f"  Round {round_num}/{num_rounds}...")
        
        # 生成用户消息（基于某个方法的历史，这里用第一个方法的）
        primary_method = methods[0]
        user_message = call_user_simulator(
            profile, personality,
            method_histories[primary_method],
            api_url, api_key
        )
        
        # 各方法生成响应
        responses = {}
        for method in methods:
            response = call_model(
                method, user_message, 
                method_histories[method],
                profile, api_url, api_key
            )
            responses[method] = response
            
            # 更新该方法的历史
            method_histories[method].append(user_message)
            method_histories[method].append(response)
        
        session["rounds"].append({
            "round": round_num,
            "user_message": user_message,
            "responses": responses
        })
    
    return session


def main():
    parser = argparse.ArgumentParser(description='Generate benchmark dialogue data')
    parser.add_argument('--profiles', type=str, required=True, 
                        help='Path to profiles JSONL file')
    parser.add_argument('--output', type=str, required=True,
                        help='Output JSONL file path')
    parser.add_argument('--methods', type=str, nargs='+', 
                        default=['Base', 'PersonaSteer'],
                        help='Methods to evaluate')
    parser.add_argument('--rounds', type=int, default=10,
                        help='Number of dialogue rounds per session')
    parser.add_argument('--api_url', type=str, 
                        default='https://origin.nextway.top/v1/chat/completions',
                        help='API endpoint URL')
    parser.add_argument('--api_key', type=str, required=True,
                        help='API key')
    
    args = parser.parse_args()
    
    # 加载用户画像
    print(f"Loading profiles from {args.profiles}...")
    profiles = load_profiles(args.profiles)
    print(f"Loaded {len(profiles)} profiles")
    
    # 生成对话
    sessions = []
    for i, profile_data in enumerate(profiles):
        print(f"Generating session {i+1}/{len(profiles)}...")
        session = generate_session(
            profile_data, args.methods, args.rounds,
            args.api_url, args.api_key
        )
        sessions.append(session)
    
    # 保存结果
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        for session in sessions:
            f.write(json.dumps(session, ensure_ascii=False) + '\n')
    
    print(f"Saved {len(sessions)} sessions to {args.output}")
    print("Done! You can now upload this file to the benchmark platform.")


if __name__ == '__main__':
    main()
