# PersonaSteer Benchmark

🎯 **个性化大语言模型对齐评测平台**

基于 **ALOE 数据集** (COLING 2025) 设计，评估提示词参考 **RLPA** 项目。

## ✨ 功能特性

- 📤 **文件上传**: 支持 ALOE 格式的 `.jsonl` 对话日志
- 🔬 **LLM-as-a-Judge**: GPT-4o 五维度评分 + 二元对齐判断
- 📊 **可视化**: AL(k) 对齐曲线、雷达图、方法对比表格
- 🌍 **多语言**: 支持中文、英文、韩语
- 📈 **核心指标**: AVG、N-IR、N-R²、Binary Alignment Rate

---

## 🧠 评估设计理念

### 数据来源：ALOE (COLING 2025)
> 论文: [ALOE: Aligning LLMs with Personalized Preferences through Multi-Turn Online Learning](https://aclanthology.org/2025.coling-main.511.pdf)

ALOE 数据集包含：
- **Profile**: 用户背景 (职业、爱好、生活习惯等客观事实)
- **Personality**: 用户性格 (独立、感性、严谨等特质描述)
- **Conversations**: 多轮对话，含 preferred/rejected 响应对

### 评估参考：RLPA
评估提示词融合了 RLPA 的设计理念：
- **用户视角评估**: 模拟用户判断"是否想继续聊"
- **渐进式信息释放**: 考虑对话轮次对个性化的影响
- **严格评估标准**: 任一维度不达标即扣分

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

| 维度 | 英文名 | 评估要点 |
|------|--------|----------|
| 风格适配度 | Style Alignment | 语言风格是否匹配用户性格（外向→活泼，内敛→沉稳） |
| 内容相关度 | Content Relevance | 是否与用户的兴趣、职业、生活背景相关 |
| 自然流畅度 | Naturalness | 是否像真实人类对话，口语化、简洁 |
| 个性化深度 | Personalization | 是否捕捉到用户的隐性需求，自然融入而非生硬 |
| 对话推进力 | Conversation | 是否能推动有意义的对话延续，避免重复 |

### 评分等级参考

| 分数区间 | 等级 | 描述 |
|---------|------|------|
| 85-100 | 优秀 | 高度个性化，像了解用户的朋友在对话 |
| 70-84 | 良好 | 有明显的个性化尝试，体验较好 |
| 55-69 | 中等 | 有一定个性化意识，但不够自然 |
| 40-54 | 较差 | 个性化痕迹弱，接近通用回复 |
| 0-39 | 很差 | 完全通用或与用户特征相悖 |

---

## 📝 LLM-as-a-Judge 评估提示词

### 模式一：细粒度评分 (0-100)

用于计算 AL(k) 曲线，输出五维度分数和总分。

```
# 任务：评估AI响应与用户画像的对齐程度

你是一位专业的对话质量评估专家。你需要评估一个AI助手的响应
在多大程度上体现了对用户个人特征的理解和适配。

## 用户档案信息
### 用户画像 (Profile)
{profile}

### 用户性格特征 (Personality)  
{personality}

## 对话上下文
### 历史对话
{history}

### 当前用户消息
{user_message}

### AI助手的响应
{response}

## 评估维度 (每个维度 0-20 分，共 100 分)

### 1. 风格适配度 (Style Alignment) [0-20分]
- 用户性格外向/热情 → 响应是否活泼、有感染力？
- 用户性格内敛/严谨 → 响应是否沉稳、有条理？

### 2. 内容相关度 (Content Relevance) [0-20分]
- 是否自然地联系到用户的爱好或专业领域？
- 是否体现了对用户生活情境的理解？

### 3. 自然流畅度 (Naturalness) [0-20分]
- 语言是否口语化、简洁、流畅？
- 是否避免了过度正式或说教式表达？

### 4. 个性化深度 (Personalization Depth) [0-20分]
- 是否捕捉到用户的隐性需求或潜在兴趣？
- 个性化是否自然融入而非生硬堆砌？

### 5. 对话推进力 (Conversation Quality) [0-20分]
- 是否避免了重复或信息量过低的回复？
- 是否让用户有继续交流的意愿？

## 输出格式
Reasoning: [评估理由]
Style: [分数]/20
Content: [分数]/20  
Naturalness: [分数]/20
Personalization: [分数]/20
Conversation: [分数]/20
Total: \boxed{[总分]}
```

### 模式二：二元对齐判断 (0/1)

参考 RLPA 的严格评估风格，模拟用户视角判断"是否想继续聊"。

```
# 任务：判断用户是否愿意继续与AI对话

你正在扮演以下用户：

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

看到这个回复，你还想继续跟这个AI聊下去吗？

### 评估标准（任一不满足即给0分）：

1. **自然度**：回复是否流畅、简短、自然、口语化？
2. **切合兴趣**：回复是否和你的兴趣、需求相关？
3. **逻辑性**：回复是否正确理解并回应了你的消息？
4. **吸引力**：你对这个AI有没有继续探知的欲望？
5. **信息价值**：回复是对你说的话的简单重复吗？

## 输出格式
Reasoning: [判断理由]
Result: \boxed{1} 或 \boxed{0}
```

### 设计理念

| 来源 | 借鉴内容 |
|------|----------|
| **ALOE** | 数据格式 (profile + personality + conversations) |
| **ALOE** | 多轮对话评估，计算每轮 AL(k) |
| **RLPA** | 用户视角评估 ("是否想继续聊") |
| **RLPA** | 严格的评估标准 (任一不满足即扣分) |
| **RLPA** | 结构化输出格式 (\boxed{} 提取结果) |

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
