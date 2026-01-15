# PersonaSteer Benchmark

🎯 **Personalized LLM Alignment Evaluation Platform**

Based on **ALOE Dataset** (COLING 2025), evaluation prompts referenced from **RLPA**.

## ✨ Features

- 📤 Upload `.jsonl` dialogue logs
- 🔬 LLM-as-a-Judge: 5-dimension scoring + binary alignment
- 📊 Visualization: AL(k) curves, radar charts, comparison tables
- 🌍 Multi-language: Chinese, English, Korean

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python app.py
# Visit http://localhost:5000
```

---

## 📋 JSONL Format

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session ID |
| `user_profile` | string | User background (facts) |
| `user_personality` | string | User personality traits |
| `rounds` | array | Dialogue rounds |

### Round Structure

```json
{
  "round": 1,
  "user_message": "Hey!",
  "responses": {
    "Base": "Hello!",
    "Ours": "Hey there!"
  }
}
```

### Example

```jsonl
{"session_id":"user_001","user_profile":"22-year-old student in NYC, likes hiking","user_personality":"curious, introverted, witty","rounds":[{"round":1,"user_message":"Hey!","responses":{"Base":"Hello!","Ours":"Hey! What's up?"}}]}
```

### Validation

```
✅ .jsonl extension
✅ Valid JSON per line
✅ Required fields exist
✅ rounds non-empty
✅ Consistent method names across rounds
```

---

## 📁 Project Structure

```
WEB_BENCHMARK/
├── app.py              # Flask app
├── evaluator.py        # LLM-as-a-Judge
├── translations.py     # i18n
├── sample_data.jsonl   # Example data
├── templates/          # HTML
├── static/             # CSS, JS
├── uploads/            # Uploaded files
└── results/            # Evaluation results
```

## 📊 Evaluation Metrics

### Primary Metric: AL(k)
**Alignment Level at k-turn** — Score at round k (0-100).

### Aggregated Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **AVG** | $\frac{1}{K} \sum_{k=1}^{K} AL(k)$ | Average alignment score |
| **Slope (b)** | $\arg\min_{b,a} \sum(b \cdot k + a - AL(k))^2$ | Improvement trend |
| **Intercept (a)** | Linear regression intercept | Initial alignment level |
| **R²** | Coefficient of determination | Stability of improvement |
| **N-AL(k)** | $\frac{AL(k) - \min AL}{\max AL - \min AL}$ | Normalized AL |
| **Binary Rate** | $\frac{\sum(binary=1)}{N} \times 100\%$ | "Want to continue" rate |

### Scoring Dimensions (5 × 20 = 100)

| Dimension | Key Points |
|-----------|------------|
| Style | Match user personality (extrovert→lively, introvert→calm) |
| Content | Relate to user's interests, profession, background |
| Naturalness | Conversational, concise, human-like |
| Personalization | Capture implicit needs, naturally integrated |
| Conversation | Drive meaningful dialogue, avoid repetition |

---

## 📝 LLM-as-a-Judge Evaluation

### Mode 1: Fine-grained Scoring (0-100)

5 dimensions × 20 points each. Output format:
```
Reasoning: [reason]
Style: [score]/20
Content: [score]/20  
Naturalness: [score]/20
Personalization: [score]/20
Conversation: [score]/20
Total: \boxed{[total]}
```

### Mode 2: Binary Judgment (0/1) ⭐ Primary

Simulates user perspective: "Do you want to continue chatting?"

**Strict criteria** — If ANY criterion fails, score = 0:
1. Naturalness
2. Relevance to interests  
3. Logical consistency
4. Excitement factor
5. Information value

Output: `\boxed{1}` (continue) or `\boxed{0}` (stop)

### Design References

| Source | Contribution |
|--------|--------------|
| **ALOE** | Data format, multi-turn AL(k) |
| **RLPA** | User-perspective evaluation, strict criteria |

## 📝 Data Generation

```python
import json

sessions = [{
    "session_id": "user_001_session_001",
    "user_profile": "22-year-old student...",
    "user_personality": "curious, introverted...",
    "rounds": [
        {"round": 1, "user_message": "Hey!", 
         "responses": {"Base": "Hi!", "Ours": "Hey there!"}}
    ]
}]

with open('data.jsonl', 'w') as f:
    for s in sessions:
        f.write(json.dumps(s, ensure_ascii=False) + '\n')
```

## 🔒 API Configuration

Edit `evaluator.py`:
```python
API_URL = "https://api.aigc369.com/v1/chat/completions"
```

## 📄 License

MIT License

---

Made with ❤️ by PersonaSteer Team
