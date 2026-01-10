/**
 * PersonaSteer Benchmark - Main JavaScript
 */

// Global state
let uploadedFile = null;
let uploadedFilename = null;
let detectedMethods = [];
let selectedMethods = [];
let evaluationResults = null;

// Chart instances
let alCurveChart = null;
let radarChart = null;

// Colors for different methods
const methodColors = {
    'Base': { bg: 'rgba(239, 68, 68, 0.2)', border: '#ef4444' },
    'RAG': { bg: 'rgba(245, 158, 11, 0.2)', border: '#f59e0b' },
    'PersonaSteer': { bg: 'rgba(99, 102, 241, 0.2)', border: '#6366f1' },
    'ALOE': { bg: 'rgba(16, 185, 129, 0.2)', border: '#10b981' },
    'RLPA': { bg: 'rgba(139, 92, 246, 0.2)', border: '#8b5cf6' },
    'default': { bg: 'rgba(6, 182, 212, 0.2)', border: '#06b6d4' }
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupFileUpload();
    setupNavigation();
});

/**
 * Setup file upload handlers
 */
function setupFileUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    
    // Click to upload
    dropZone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A') {
            fileInput.click();
        }
    });
    
    // File selected
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect({ target: fileInput });
        }
    });
}

/**
 * Handle file selection
 */
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Show loading state
    const statusBox = document.getElementById('uploadStatus');
    statusBox.classList.remove('hidden', 'error');
    statusBox.querySelector('.status-icon').textContent = '⏳';
    statusBox.querySelector('.status-text').textContent = 'Uploading...';
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            uploadedFilename = data.filename;
            statusBox.querySelector('.status-icon').textContent = '✅';
            statusBox.querySelector('.status-text').textContent = 
                `${data.message} (${data.sessions} sessions, ${data.methods.length} methods: ${data.methods.join(', ')})`;
            
            // Use methods returned from server (already validated)
            if (data.methods && data.methods.length > 0) {
                detectedMethods = data.methods;
                populateMethodSelector(detectedMethods);
            } else {
                // Fallback: parse file locally
                parseFileForMethods(file);
            }
        } else {
            throw new Error(data.error);
        }
    })
    .catch(error => {
        statusBox.classList.add('error');
        statusBox.querySelector('.status-icon').textContent = '❌';
        statusBox.querySelector('.status-text').textContent = error.message;
    });
}

/**
 * Parse file to detect available methods
 */
function parseFileForMethods(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const lines = e.target.result.trim().split('\n');
            const firstSession = JSON.parse(lines[0]);
            
            // Extract method names from first round's responses
            if (firstSession.rounds && firstSession.rounds.length > 0) {
                const responses = firstSession.rounds[0].responses || {};
                detectedMethods = Object.keys(responses);
                populateMethodSelector(detectedMethods);
            }
        } catch (err) {
            console.error('Error parsing file:', err);
        }
    };
    reader.readAsText(file);
}

/**
 * Populate method selector with detected methods
 */
function populateMethodSelector(methods) {
    const methodList = document.getElementById('methodList');
    methodList.innerHTML = '';
    
    methods.forEach(method => {
        const tag = document.createElement('div');
        tag.className = 'method-tag';
        tag.setAttribute('data-method', method);
        tag.innerHTML = `<span>🔹 ${method}</span>`;
        
        tag.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            tag.classList.toggle('selected');
            updateSelectedMethods();
        });
        
        methodList.appendChild(tag);
    });
    
    // Enable start button check
    updateSelectedMethods();
}

/**
 * Update selected methods list
 */
function updateSelectedMethods() {
    selectedMethods = [];
    document.querySelectorAll('.method-tag.selected').forEach(tag => {
        const method = tag.getAttribute('data-method');
        if (method) {
            selectedMethods.push(method);
        }
    });
    
    const startBtn = document.getElementById('startEvalBtn');
    startBtn.disabled = selectedMethods.length === 0 || !uploadedFilename;
    
    // Update button text to show selected count
    if (selectedMethods.length > 0) {
        startBtn.textContent = `开始评测 (${selectedMethods.length} 个方法)`;
    } else {
        startBtn.textContent = '开始评测';
    }
}

/**
 * Start evaluation
 */
function startEvaluation() {
    if (!uploadedFilename || selectedMethods.length === 0) return;
    
    const startBtn = document.getElementById('startEvalBtn');
    const progress = document.getElementById('evalProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    startBtn.disabled = true;
    progress.classList.remove('hidden');
    progress.classList.add('evaluating');
    progressFill.style.width = '10%';
    
    // Simulate progress
    let fakeProgress = 10;
    const progressInterval = setInterval(() => {
        fakeProgress = Math.min(fakeProgress + Math.random() * 5, 90);
        progressFill.style.width = fakeProgress + '%';
    }, 500);
    
    fetch('/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            filename: uploadedFilename,
            methods: selectedMethods
        })
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        
        if (data.success) {
            evaluationResults = data.results;
            progressText.textContent = '✅ ' + data.message;
            progress.classList.remove('evaluating');
            
            // Show results
            setTimeout(() => {
                displayResults(evaluationResults);
            }, 500);
        } else {
            throw new Error(data.error);
        }
    })
    .catch(error => {
        clearInterval(progressInterval);
        progressFill.style.width = '0%';
        progressText.textContent = '❌ ' + error.message;
        progress.classList.remove('evaluating');
        startBtn.disabled = false;
    });
}

/**
 * Display evaluation results
 */
function displayResults(results) {
    const resultsSection = document.getElementById('results');
    resultsSection.classList.remove('hidden');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Populate metrics grid
    populateMetricsGrid(results);
    
    // Draw charts
    drawALCurveChart(results);
    drawRadarChart(results);
    
    // Populate table
    populateResultsTable(results);
}

/**
 * Populate metrics cards
 */
function populateMetricsGrid(results) {
    const grid = document.getElementById('metricsGrid');
    grid.innerHTML = '';
    
    const methods = Object.keys(results.methods);
    const bestMethod = findBestMethod(results.methods);
    
    methods.forEach(method => {
        const data = results.methods[method];
        const metrics = data.metrics;
        const isBest = method === bestMethod;
        
        const card = document.createElement('div');
        card.className = 'metric-card';
        card.innerHTML = `
            <div class="value">${metrics.AVG}</div>
            <div class="label">${method} AVG ${isBest ? '🏆' : ''}</div>
        `;
        grid.appendChild(card);
    });
    
    // Add total sessions card
    const sessionsCard = document.createElement('div');
    sessionsCard.className = 'metric-card';
    sessionsCard.innerHTML = `
        <div class="value">${results.total_sessions}</div>
        <div class="label">Total Sessions</div>
    `;
    grid.appendChild(sessionsCard);
}

/**
 * Find best performing method
 */
function findBestMethod(methods) {
    let best = null;
    let bestScore = -Infinity;
    
    for (const [method, data] of Object.entries(methods)) {
        if (data.metrics.AVG > bestScore) {
            bestScore = data.metrics.AVG;
            best = method;
        }
    }
    
    return best;
}

/**
 * Draw AL(k) curve chart
 */
function drawALCurveChart(results) {
    const ctx = document.getElementById('alCurveChart').getContext('2d');
    
    if (alCurveChart) {
        alCurveChart.destroy();
    }
    
    const datasets = [];
    const methods = Object.keys(results.methods);
    
    methods.forEach((method, idx) => {
        const data = results.methods[method];
        const colors = methodColors[method] || methodColors['default'];
        
        datasets.push({
            label: method,
            data: data.al_curve,
            borderColor: colors.border,
            backgroundColor: colors.bg,
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6
        });
    });
    
    // Calculate max rounds
    const maxRounds = Math.max(...methods.map(m => results.methods[m].al_curve.length));
    const labels = Array.from({ length: maxRounds }, (_, i) => `Turn ${i + 1}`);
    
    alCurveChart = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#a0a0b0', font: { size: 12 } }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#a0a0b0' }
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#a0a0b0' },
                    title: {
                        display: true,
                        text: 'Alignment Score',
                        color: '#a0a0b0'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

/**
 * Draw radar chart
 */
function drawRadarChart(results) {
    const ctx = document.getElementById('radarChart').getContext('2d');
    
    if (radarChart) {
        radarChart.destroy();
    }
    
    const radarData = results.radar_data;
    const methods = Object.keys(radarData);
    const dimensions = ['AVG', 'N_IR', 'N_R2', 'Consistency', 'Improvement'];
    
    const datasets = methods.map((method, idx) => {
        const colors = methodColors[method] || methodColors['default'];
        return {
            label: method,
            data: dimensions.map(d => radarData[method][d]),
            borderColor: colors.border,
            backgroundColor: colors.bg,
            borderWidth: 2,
            pointRadius: 4
        };
    });
    
    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: dimensions,
            datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#a0a0b0', font: { size: 12 } }
                }
            },
            scales: {
                r: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    angleLines: { color: 'rgba(255,255,255,0.1)' },
                    pointLabels: { color: '#a0a0b0', font: { size: 11 } },
                    ticks: { 
                        color: '#606070',
                        backdropColor: 'transparent',
                        stepSize: 20
                    }
                }
            }
        }
    });
}

/**
 * Populate results table
 */
function populateResultsTable(results) {
    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = '';
    
    const methods = Object.keys(results.methods);
    const bestAVG = Math.max(...methods.map(m => results.methods[m].metrics.AVG));
    const bestNIR = Math.max(...methods.map(m => results.methods[m].metrics.N_IR));
    const bestNR2 = Math.max(...methods.map(m => results.methods[m].metrics.N_R2));
    
    methods.forEach(method => {
        const data = results.methods[method];
        const metrics = data.metrics;
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${method}</strong></td>
            <td class="${metrics.AVG === bestAVG ? 'best' : ''}">${metrics.AVG}</td>
            <td class="${metrics.N_IR === bestNIR ? 'best' : ''}">${metrics.N_IR}</td>
            <td class="${metrics.N_R2 === bestNR2 ? 'best' : ''}">${metrics.N_R2}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Export results as JSON
 */
function exportResults() {
    if (!evaluationResults) return;
    
    const blob = new Blob([JSON.stringify(evaluationResults, null, 2)], {
        type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `benchmark_results_${evaluationResults.task_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Change language
 */
function setLanguage(lang) {
    fetch(`/set_language/${lang}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        });
}

/**
 * Setup smooth navigation
 */
function setupNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const target = document.getElementById(targetId);
            
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
                
                // Update active state
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
}
