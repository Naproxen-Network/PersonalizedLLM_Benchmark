"""
Multi-language support for PersonaSteer Benchmark
Supports: Chinese (zh), English (en), Korean (ko)
"""

SUPPORTED_LANGUAGES = {
    'zh': '中文',
    'en': 'English',
    'ko': '한국어'
}

TRANSLATIONS = {
    'zh': {
        # Navigation
        'title': 'PersonaSteer Benchmark',
        'subtitle': '个性化大语言模型对齐评测平台',
        'home': '首页',
        'upload': '上传',
        'evaluate': '评测',
        'results': '结果',
        'docs': '文档',
        
        # Upload section
        'upload_title': '上传对话日志',
        'upload_desc': '上传您的模型生成的对话日志文件 (.jsonl 格式)',
        'select_file': '选择文件',
        'drag_drop': '或将文件拖拽到此处',
        'file_format': '支持的格式: .jsonl',
        'upload_btn': '上传文件',
        'download_template': '下载模板',
        
        # Evaluation section
        'eval_title': '开始评测',
        'eval_desc': '选择要评测的方法，系统将使用 LLM-as-a-Judge 进行评分',
        'select_methods': '选择评测方法',
        'start_eval': '开始评测',
        'evaluating': '评测中...',
        
        # Results section
        'results_title': '评测结果',
        'metrics_title': '核心指标',
        'al_curve_title': 'AL(k) 对齐曲线',
        'radar_title': '多维度对比雷达图',
        'details_title': '详细评分',
        'export_results': '导出结果',
        
        # Metrics
        'avg_score': '平均对齐分数',
        'n_ir': '归一化改进率',
        'n_r2': '归一化决定系数',
        'total_sessions': '评测会话数',
        'total_rounds': '评测轮数',
        
        # Messages
        'no_file_selected': '请选择文件',
        'invalid_format': '无效的文件格式，请上传 .jsonl 文件',
        'upload_success': '文件上传成功',
        'parse_error': '文件解析错误',
        'missing_params': '缺少必要参数',
        'file_not_found': '文件未找到',
        'eval_complete': '评测完成',
        'eval_error': '评测出错',
        'loading': '加载中...',
        
        # Documentation
        'doc_format_title': '数据格式说明',
        'doc_format_desc': '上传的 .jsonl 文件应包含以下字段',
        'doc_metrics_title': '评测指标说明',
        'doc_metrics_desc': '我们使用以下指标评估个性化对齐效果',
        
        # Footer
        'powered_by': '技术支持',
        'contact': '联系我们'
    },
    
    'en': {
        # Navigation
        'title': 'PersonaSteer Benchmark',
        'subtitle': 'Personalized LLM Alignment Evaluation Platform',
        'home': 'Home',
        'upload': 'Upload',
        'evaluate': 'Evaluate',
        'results': 'Results',
        'docs': 'Documentation',
        
        # Upload section
        'upload_title': 'Upload Conversation Logs',
        'upload_desc': 'Upload your model-generated conversation logs (.jsonl format)',
        'select_file': 'Select File',
        'drag_drop': 'or drag and drop here',
        'file_format': 'Supported format: .jsonl',
        'upload_btn': 'Upload File',
        'download_template': 'Download Template',
        
        # Evaluation section
        'eval_title': 'Start Evaluation',
        'eval_desc': 'Select methods to evaluate. The system will use LLM-as-a-Judge for scoring.',
        'select_methods': 'Select Methods',
        'start_eval': 'Start Evaluation',
        'evaluating': 'Evaluating...',
        
        # Results section
        'results_title': 'Evaluation Results',
        'metrics_title': 'Core Metrics',
        'al_curve_title': 'AL(k) Alignment Curve',
        'radar_title': 'Multi-dimensional Comparison Radar',
        'details_title': 'Detailed Scores',
        'export_results': 'Export Results',
        
        # Metrics
        'avg_score': 'Average Alignment Score',
        'n_ir': 'Normalized Improvement Rate',
        'n_r2': 'Normalized R-squared',
        'total_sessions': 'Total Sessions',
        'total_rounds': 'Total Rounds',
        
        # Messages
        'no_file_selected': 'Please select a file',
        'invalid_format': 'Invalid file format. Please upload a .jsonl file',
        'upload_success': 'File uploaded successfully',
        'parse_error': 'File parsing error',
        'missing_params': 'Missing required parameters',
        'file_not_found': 'File not found',
        'eval_complete': 'Evaluation completed',
        'eval_error': 'Evaluation error',
        'loading': 'Loading...',
        
        # Documentation
        'doc_format_title': 'Data Format Specification',
        'doc_format_desc': 'The uploaded .jsonl file should contain the following fields',
        'doc_metrics_title': 'Evaluation Metrics',
        'doc_metrics_desc': 'We use the following metrics to evaluate personalization alignment',
        
        # Footer
        'powered_by': 'Powered by',
        'contact': 'Contact Us'
    },
    
    'ko': {
        # Navigation
        'title': 'PersonaSteer Benchmark',
        'subtitle': '개인화 대규모 언어 모델 정렬 평가 플랫폼',
        'home': '홈',
        'upload': '업로드',
        'evaluate': '평가',
        'results': '결과',
        'docs': '문서',
        
        # Upload section
        'upload_title': '대화 로그 업로드',
        'upload_desc': '모델이 생성한 대화 로그 파일을 업로드하세요 (.jsonl 형식)',
        'select_file': '파일 선택',
        'drag_drop': '또는 여기에 드래그 앤 드롭',
        'file_format': '지원 형식: .jsonl',
        'upload_btn': '파일 업로드',
        'download_template': '템플릿 다운로드',
        
        # Evaluation section
        'eval_title': '평가 시작',
        'eval_desc': '평가할 방법을 선택하세요. 시스템이 LLM-as-a-Judge를 사용하여 점수를 매깁니다.',
        'select_methods': '방법 선택',
        'start_eval': '평가 시작',
        'evaluating': '평가 중...',
        
        # Results section
        'results_title': '평가 결과',
        'metrics_title': '핵심 지표',
        'al_curve_title': 'AL(k) 정렬 곡선',
        'radar_title': '다차원 비교 레이더',
        'details_title': '상세 점수',
        'export_results': '결과 내보내기',
        
        # Metrics
        'avg_score': '평균 정렬 점수',
        'n_ir': '정규화 개선율',
        'n_r2': '정규화 결정계수',
        'total_sessions': '총 세션 수',
        'total_rounds': '총 라운드 수',
        
        # Messages
        'no_file_selected': '파일을 선택해주세요',
        'invalid_format': '잘못된 파일 형식입니다. .jsonl 파일을 업로드해주세요',
        'upload_success': '파일 업로드 성공',
        'parse_error': '파일 파싱 오류',
        'missing_params': '필수 매개변수 누락',
        'file_not_found': '파일을 찾을 수 없음',
        'eval_complete': '평가 완료',
        'eval_error': '평가 오류',
        'loading': '로딩 중...',
        
        # Documentation
        'doc_format_title': '데이터 형식 사양',
        'doc_format_desc': '업로드된 .jsonl 파일은 다음 필드를 포함해야 합니다',
        'doc_metrics_title': '평가 지표',
        'doc_metrics_desc': '개인화 정렬을 평가하기 위해 다음 지표를 사용합니다',
        
        # Footer
        'powered_by': '기술 지원',
        'contact': '문의하기'
    }
}


def get_translation(lang: str = 'zh') -> dict:
    """Get translations for specified language"""
    return TRANSLATIONS.get(lang, TRANSLATIONS['zh'])
