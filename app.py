"""
PersonaSteer Benchmark - Web Application
A platform for evaluating personalized LLM alignment
"""

from flask import Flask, render_template, request, jsonify, session, send_file
import os
import json
import uuid
from datetime import datetime
from evaluator import BenchmarkEvaluator
from translations import get_translation, SUPPORTED_LANGUAGES

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Initialize evaluator
evaluator = BenchmarkEvaluator()


@app.before_request
def before_request():
    """Set default language"""
    if 'lang' not in session:
        session['lang'] = 'zh'


@app.route('/')
def index():
    """Main page"""
    lang = session.get('lang', 'zh')
    t = get_translation(lang)
    return render_template('index.html', t=t, lang=lang, languages=SUPPORTED_LANGUAGES)


@app.route('/set_language/<lang>')
def set_language(lang):
    """Change language"""
    if lang in SUPPORTED_LANGUAGES:
        session['lang'] = lang
    return jsonify({'success': True, 'lang': lang})


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    lang = session.get('lang', 'zh')
    t = get_translation(lang)
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': t['no_file_selected']})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': t['no_file_selected']})
    
    if not file.filename.endswith('.jsonl'):
        return jsonify({'success': False, 'error': t['invalid_format']})
    
    # Generate unique filename
    file_id = str(uuid.uuid4())[:8]
    filename = f"{file_id}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Validate file format with strict rules
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) == 0:
                raise ValueError("Empty file / 空文件")
            
            detected_methods = set()
            
            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                    
                try:
                    session_data = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Line {line_num}: Invalid JSON / 无效JSON - {str(e)}")
                
                # Check required top-level fields
                required_fields = ['session_id', 'user_profile', 'rounds']
                for field in required_fields:
                    if field not in session_data:
                        raise ValueError(f"Line {line_num}: Missing required field '{field}' / 缺少必填字段 '{field}'")
                
                # Validate session_id
                if not isinstance(session_data['session_id'], str) or len(session_data['session_id']) == 0:
                    raise ValueError(f"Line {line_num}: 'session_id' must be non-empty string / 'session_id' 必须为非空字符串")
                
                # Validate user_profile
                if not isinstance(session_data['user_profile'], str) or len(session_data['user_profile']) < 10:
                    raise ValueError(f"Line {line_num}: 'user_profile' must be string with at least 10 chars / 'user_profile' 至少10个字符")
                
                # Validate rounds
                rounds = session_data['rounds']
                if not isinstance(rounds, list) or len(rounds) == 0:
                    raise ValueError(f"Line {line_num}: 'rounds' must be non-empty array / 'rounds' 必须为非空数组")
                
                for r_idx, round_data in enumerate(rounds, 1):
                    # Check round fields
                    if 'round' not in round_data:
                        raise ValueError(f"Line {line_num}, Round {r_idx}: Missing 'round' field / 缺少 'round' 字段")
                    if 'user_message' not in round_data:
                        raise ValueError(f"Line {line_num}, Round {r_idx}: Missing 'user_message' field / 缺少 'user_message' 字段")
                    if 'responses' not in round_data:
                        raise ValueError(f"Line {line_num}, Round {r_idx}: Missing 'responses' field / 缺少 'responses' 字段")
                    
                    # Validate responses
                    responses = round_data['responses']
                    if not isinstance(responses, dict) or len(responses) == 0:
                        raise ValueError(f"Line {line_num}, Round {r_idx}: 'responses' must be non-empty object / 'responses' 必须为非空对象")
                    
                    # Track methods for consistency check
                    current_methods = set(responses.keys())
                    if not detected_methods:
                        detected_methods = current_methods
                    elif current_methods != detected_methods:
                        raise ValueError(f"Line {line_num}, Round {r_idx}: Inconsistent methods. Expected {detected_methods}, got {current_methods} / 方法不一致")
            
            method_list = list(detected_methods)
        
        return jsonify({
            'success': True, 
            'file_id': file_id,
            'filename': filename,
            'sessions': len([l for l in lines if l.strip()]),
            'methods': method_list,
            'message': t['upload_success']
        })
    
    except Exception as e:
        os.remove(filepath)
        return jsonify({'success': False, 'error': f"{t['parse_error']}: {str(e)}"})


@app.route('/evaluate', methods=['POST'])
def evaluate():
    """Start evaluation"""
    lang = session.get('lang', 'zh')
    t = get_translation(lang)
    
    data = request.json
    filename = data.get('filename')
    methods = data.get('methods', [])
    
    if not filename or not methods:
        return jsonify({'success': False, 'error': t['missing_params']})
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': t['file_not_found']})
    
    # Create evaluation task
    task_id = str(uuid.uuid4())[:8]
    results_folder = app.config['RESULTS_FOLDER']
    
    try:
        # Run evaluation with incremental saving
        results = evaluator.evaluate_file(
            filepath, methods, task_id, 
            results_folder=results_folder
        )
        
        # Save final results
        result_path = os.path.join(results_folder, f"{task_id}_results.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'results': results,
            'message': t['eval_complete']
        })
    
    except Exception as e:
        # 即使失败也尝试返回部分结果
        checkpoint_path = os.path.join(results_folder, f"{task_id}_checkpoint.json")
        if os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    partial = json.load(f)
                return jsonify({
                    'success': False, 
                    'error': f"{t['eval_error']}: {str(e)}",
                    'partial_results': partial,
                    'message': '部分评测结果已保存'
                })
            except:
                pass
        return jsonify({'success': False, 'error': f"{t['eval_error']}: {str(e)}"})


@app.route('/results/<task_id>')
def get_results(task_id):
    """Get evaluation results"""
    result_path = os.path.join(app.config['RESULTS_FOLDER'], f"{task_id}_results.json")
    
    if not os.path.exists(result_path):
        return jsonify({'success': False, 'error': 'Results not found'})
    
    with open(result_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    return jsonify({'success': True, 'results': results})


@app.route('/download_template')
def download_template():
    """Download sample data template"""
    template = {
        "session_id": "user_001_session_001",
        "user_profile": "He is a 22-year-old college student studying anthropology...",
        "user_personality": "He is curious and open-minded...",
        "rounds": [
            {
                "round": 1,
                "user_message": "Hey, just added you as a friend!",
                "responses": {
                    "Base": "Hello! How can I help you today?",
                    "YourMethod": "Hey! Nice to meet you! How's your day going?"
                }
            },
            {
                "round": 2,
                "user_message": "Just got out of class, a bit tired",
                "responses": {
                    "Base": "I understand. Rest is important for productivity.",
                    "YourMethod": "Classes can be exhausting! What subject was it?"
                }
            }
        ]
    }
    
    # Create template file
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 'template.jsonl')
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(template, ensure_ascii=False) + '\n')
    
    return send_file(template_path, as_attachment=True, download_name='template.jsonl')


@app.route('/api/status')
def api_status():
    """API health check"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    # use_reloader=False 防止在评测过程中因外部包变化导致服务器重启
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
