# PersonaSteer Benchmark

🎯 **个性化大语言模型对齐评测平台**

一个用于评估个性化LLM对齐效果的Web平台，支持多方法对比、LLM-as-a-Judge评分和丰富的可视化。

## ✨ 功能特性

- 📤 **文件上传**: 支持 `.jsonl` 格式的对话日志上传
- 🔬 **自动评估**: 使用 GPT-4o 作为 Judge 进行多维度评分
- 📊 **可视化**: AL(k) 对齐曲线、雷达图、对比表格
- 🌍 **多语言**: 支持中文、英文、韩语
- 📈 **核心指标**: AVG、N-IR、N-R² 等专业评测指标

## 🚀 快速开始

### 1. 安装依赖

```bash
cd WEB_BENCHMARK
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

访问 http://localhost:5000

### 3. 准备数据

参见下方 **📋 JSONL 文件格式规范**

---

## 📋 JSONL 文件格式规范

### 文件要求

| 项目 | 要求 |
|------|------|
| **文件扩展名** | 必须为 `.jsonl` |
| **编码** | UTF-8 (无 BOM) |
| **每行格式** | 一个完整的 JSON 对象，以换行符 `\n` 结尾 |
| **文件大小** | 最大 50MB |
| **会话数量** | 建议 10-500 个会话 |

### 顶层字段 (必填)

每行 JSON 对象必须包含以下字段：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `session_id` | `string` | ✅ | 会话唯一标识符，格式: `user_{id}_session_{num}` |
| `user_profile` | `string` | ✅ | 用户画像（客观事实），50-500 字符 |
| `user_personality` | `string` | ✅ | 用户性格描述，50-300 字符 |
| `rounds` | `array` | ✅ | 对话轮次数组，长度 1-20 |

### rounds 数组元素 (必填)

`rounds` 数组中的每个对象必须包含：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `round` | `integer` | ✅ | 轮次编号，从 1 开始递增 |
| `user_message` | `string` | ✅ | 用户发送的消息，1-500 字符 |
| `responses` | `object` | ✅ | 各方法的响应，key 为方法名 |

### responses 对象

`responses` 是一个键值对对象：

| 项目 | 要求 |
|------|------|
| **Key** | 方法名称（如 `Base`, `PersonaSteer`, `RAG`），仅限字母数字下划线 |
| **Value** | 该方法生成的响应文本，`string` 类型，1-2000 字符 |
| **方法数量** | 至少 1 个，建议 2-5 个 |
| **一致性** | 所有 rounds 中的 responses 必须包含相同的方法名 |

### 完整示例

```jsonl
{"session_id":"user_001_session_001","user_profile":"He is a 22-year-old college student studying anthropology at a university in New York. He lives in a small apartment near campus with two roommates. He enjoys hiking, photography, and cooking fusion cuisine. He has a pet cat named Mochi.","user_personality":"He is curious and open-minded, always eager to learn about different cultures. He tends to be introverted but opens up once comfortable. He has a quirky sense of humor and appreciates witty conversations.","rounds":[{"round":1,"user_message":"Hey, just added you! What's up?","responses":{"Base":"Hello! I'm doing well, thank you for asking. How can I assist you today?","PersonaSteer":"Hey! Just chilling here. How's your day going? Any exciting adventures planned?"}},{"round":2,"user_message":"Nothing much, just got out of a boring lecture","responses":{"Base":"I understand. Lectures can sometimes be tedious. Is there anything specific you'd like to discuss?","PersonaSteer":"Oof, those long lectures can be draining! What topic was it? Sometimes the dry ones hide the coolest stuff."}}]}
{"session_id":"user_002_session_001","user_profile":"She is a 35-year-old software engineer working at a tech startup in Seattle.","user_personality":"She is highly organized and goal-oriented. She values efficiency but also knows how to relax.","rounds":[{"round":1,"user_message":"Hi there!","responses":{"Base":"Hello! How can I help you?","PersonaSteer":"Hey! Hope your day is going smoothly. What's on your mind?"}}]}
```

### 格式验证规则

上传时系统会自动验证：

```
✅ 文件扩展名为 .jsonl
✅ 每行是有效的 JSON
✅ 必填字段 session_id, user_profile, rounds 存在
✅ rounds 数组非空
✅ 每个 round 包含 round, user_message, responses
✅ responses 对象非空
❌ 空文件会被拒绝
❌ JSON 解析错误会被拒绝
❌ 缺少必填字段会被拒绝
```

### user_profile 内容建议

应包含客观事实（参考 ALOE 论文）：

```
✅ 推荐包含：
- 年龄范围 (如: 22-year-old)
- 职业/学校 (如: college student studying anthropology)
- 居住地点 (如: lives in New York)
- 兴趣爱好 (如: enjoys hiking, photography)
- 家庭/社交关系 (如: lives with two roommates)
- 独特事实 (如: has a pet cat named Mochi)

❌ 不应包含：
- 性格描述 (放在 user_personality)
- 过于敏感的信息
- 不可从对话中推断的信息
```

### user_personality 内容建议

应包含性格特征（参考 ALOE 论文）：

```
✅ 推荐包含：
- 社交倾向 (如: introverted, outgoing)
- 沟通风格 (如: witty, direct, empathetic)
- 情感特点 (如: curious, open-minded)
- 决策风格 (如: indecisive, analytical)
- 价值观 (如: values efficiency, authenticity)

❌ 不应包含：
- 客观事实 (放在 user_profile)
- 职业技能描述
```

### 多方法对比格式

如果要对比多种方法，确保所有 rounds 的 responses 包含相同的 key：

```json
{
  "rounds": [
    {
      "round": 1,
      "user_message": "Hello!",
      "responses": {
        "Base": "Hi! How can I help you?",
        "RAG": "Hello! Based on your interests, how can I assist?",
        "PersonaSteer": "Hey! What's up?"
      }
    },
    {
      "round": 2,
      "user_message": "I'm bored",
      "responses": {
        "Base": "I understand. Would you like some suggestions?",
        "RAG": "Maybe try one of your hobbies?",
        "PersonaSteer": "Ugh, I feel you. Anything specific you're in the mood for?"
      }
    }
  ]
}
```

---

## 📁 项目结构

```
WEB_BENCHMARK/
├── app.py              # Flask 主应用
├── evaluator.py        # 评估模块 (LLM-as-a-Judge)
├── translations.py     # 多语言支持
├── requirements.txt    # Python 依赖
├── sample_data.jsonl   # 示例数据
├── templates/
│   └── index.html      # 主页面模板
├── static/
│   ├── css/
│   │   └── style.css   # 样式文件
│   └── js/
│       └── main.js     # 前端逻辑
├── uploads/            # 上传文件目录
└── results/            # 评测结果目录
```

## 📊 评测指标

### AVG (Average Alignment Score)
对齐分数的平均值，反映整体对齐效果。

$$AVG = \frac{1}{K} \sum_{k=1}^{K} AL(k)$$

### N-IR (Normalized Improvement Rate)
归一化改进率，反映对齐分数随对话轮次的提升趋势。

$$N\text{-}IR = \text{slope of } AL(k) \sim k$$

### N-R² (Normalized R-squared)
归一化决定系数，反映对齐改进的稳定性和可预测性。

## 🔧 评分维度

每个响应从5个维度评分（各20分，共100分）：

1. **Style Alignment**: 回复风格与用户性格的匹配度
2. **Content Relevance**: 内容与用户兴趣的相关性
3. **Naturalness**: 回复的自然度和流畅度
4. **Personalization Depth**: 个性化理解的深度
5. **Conversation Quality**: 对话质量和延续性

## 📝 客户端数据生成

### Step 1: 准备测试用例

```python
# generate_dialogues.py
import json

def generate_test_cases(user_profiles, num_rounds=10):
    """为每个用户生成多轮对话"""
    test_cases = []
    
    for profile in user_profiles:
        session = {
            "session_id": f"user_{profile['id']}_session_001",
            "user_profile": profile['profile'],
            "user_personality": profile['personality'],
            "rounds": []
        }
        
        # 使用 User Simulator 生成对话
        for round_num in range(1, num_rounds + 1):
            user_msg = simulate_user_message(profile, round_num)
            
            responses = {}
            for method_name, model in models.items():
                responses[method_name] = model.generate(user_msg)
            
            session["rounds"].append({
                "round": round_num,
                "user_message": user_msg,
                "responses": responses
            })
        
        test_cases.append(session)
    
    return test_cases
```

### Step 2: 保存为 JSONL

```python
with open('my_benchmark_data.jsonl', 'w', encoding='utf-8') as f:
    for case in test_cases:
        f.write(json.dumps(case, ensure_ascii=False) + '\n')
```

### Step 3: 上传到平台

将生成的 `.jsonl` 文件上传到 Web 平台进行评测。

## 🔒 API 配置

评估使用以下 API 端点：

```python
API_URL = "https://origin.nextway.top/v1/chat/completions"
```

如需修改，请编辑 `evaluator.py` 中的配置。

## 🌐 语言设置

平台支持三种语言：
- 🇨🇳 中文 (默认)
- 🇺🇸 English
- 🇰🇷 한국어

点击右上角语言按钮切换。

## 📄 License

MIT License

## 🤝 Contributing

欢迎提交 Issue 和 Pull Request！

---

Made with ❤️ by PersonaSteer Team
