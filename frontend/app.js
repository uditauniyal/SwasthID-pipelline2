// Smart Medical Card - Frontend Logic
// Theme: Clean Corporate (Navy/Gold/White)

const API_BASE_URL = 'http://localhost:8000';

const elements = {
    // Navigation
    tabs: document.querySelectorAll('.nav-tab'),
    tabPanes: document.querySelectorAll('.tab-pane'),

    // Status
    statusIndicator: document.getElementById('status-indicator'),

    // Upload Tab
    dropZone: document.getElementById('drop-zone'),
    fileInput: document.getElementById('file-input'),
    scanTypeSelect: document.getElementById('scan-type'),

    // Results Tab
    scanPreview: document.getElementById('scan-preview'),
    detectedBadge: document.getElementById('detected-type-badge'),
    resClassification: document.getElementById('res-classification'),
    resConfidence: document.getElementById('res-confidence'),
    resFindingsList: document.getElementById('res-findings-list'),

    // Actions
    btnBackUpload: document.getElementById('btn-back-upload'),
    btnGenerateReport: document.getElementById('btn-generate-report'),

    // Report Tab
    btnDownloadPdf: document.getElementById('btn-download-pdf'),
    reportContent: document.getElementById('report-content'),

    // Report Fields
    repDate: document.getElementById('rep-date'),
    repPatientId: document.getElementById('rep-patient-id'),
    repScanType: document.getElementById('rep-scan-type'),
    repNarrative: document.getElementById('rep-narrative'),
    repFindingsList: document.getElementById('rep-findings-list'),
    repClassification: document.getElementById('rep-classification'),
    repConfidence: document.getElementById('rep-confidence'),
    repRecommendationsList: document.getElementById('rep-recommendations-list'),
    repDisclaimer: document.getElementById('rep-disclaimer'),

    // Loading
    loadingOverlay: document.getElementById('loading-overlay')
};

// State
let currentFile = null;
let currentAnalysis = null;
let currentReportData = null;

// ===================================
// Initialization
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    setupEventListeners();
    setupTabs();
});

// ===================================
// Tab Logic
// ===================================

function setupTabs() {
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.tab;
            // Only allow switching if we have data or if it's the upload tab
            if (target !== 'scan-tab' && !currentAnalysis) {
                alert("Please upload and analyze a scan first.");
                return;
            }
            switchTab(target);
        });
    });
}

function switchTab(tabId) {
    elements.tabs.forEach(t => {
        if (t.dataset.tab === tabId) t.classList.add('active');
        else t.classList.remove('active');
    });

    elements.tabPanes.forEach(pane => {
        if (pane.id === tabId) pane.classList.add('active');
        else pane.classList.remove('active');
    });
}

// ===================================
// System Health
// ===================================

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const statusDot = elements.statusIndicator.querySelector('.status-dot');
        const statusText = elements.statusIndicator.querySelector('.status-text');

        if (response.ok) {
            statusDot.classList.add('online');
            statusText.textContent = "System Online";
        } else {
            statusDot.classList.remove('online');
            statusText.textContent = "Offline";
        }
    } catch (e) { console.error(e); }
}

// ===================================
// Event Listeners
// ===================================

function setupEventListeners() {
    // File Input
    elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    // Drag & Drop
    elements.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.dropZone.style.borderColor = 'var(--primary-blue)';
        elements.dropZone.style.backgroundColor = '#f0f9ff';
    });
    elements.dropZone.addEventListener('dragleave', () => {
        elements.dropZone.style.borderColor = '';
        elements.dropZone.style.backgroundColor = '';
    });
    elements.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.dropZone.style.borderColor = '';
        elements.dropZone.style.backgroundColor = '';
        if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
    });

    // Buttons
    elements.btnBackUpload.addEventListener('click', () => {
        switchTab('scan-tab');
        currentAnalysis = null;
        currentFile = null;
        elements.fileInput.value = '';
    });

    elements.btnGenerateReport.addEventListener('click', generateReport);
    elements.btnDownloadPdf.addEventListener('click', downloadPDF);
}

// ===================================
// Logic
// ===================================

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Invalid File Type. Please upload an image.');
        return;
    }
    currentFile = file;

    const reader = new FileReader();
    reader.onload = (e) => { elements.scanPreview.src = e.target.result; };
    reader.readAsDataURL(file);

    performAnalysis(file);
}

async function performAnalysis(file) {
    showLoading(true, "AI Analysis in Progress...");

    const scanType = elements.scanTypeSelect.value;
    let endpoint = '/analyze';
    if (scanType === 'breast_ultrasound') endpoint = '/analyze/breast-ultrasound';
    if (scanType === 'pcos_ultrasound') endpoint = '/analyze/pcos';

    const formData = new FormData();
    formData.append('file', file);
    if (endpoint === '/analyze' && scanType) formData.append('scan_type', scanType);

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Analysis failed');

        const data = await response.json();
        currentAnalysis = data;

        populateResults(data);
        switchTab('results-tab');

    } catch (error) {
        alert(`Analysis Error: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

function populateResults(data) {
    elements.detectedBadge.textContent = (data.scan_type || 'Unknown').toUpperCase();
    elements.resClassification.value = data.classification || 'N/A';
    elements.resConfidence.value = data.confidence || 'N/A';

    elements.resFindingsList.innerHTML = '';
    (data.findings || []).forEach(f => {
        const li = document.createElement('li');
        li.textContent = f;
        li.style.marginBottom = '0.5rem';
        elements.resFindingsList.appendChild(li);
    });
}

async function generateReport() {
    if (!currentFile || !currentAnalysis) return;

    // If we already generated logic locally, we can reuse or hit the endpoint
    // to simulate a full generation. The backend /report/generate mostly wraps the existing
    // analysis in a new JSON structure with patient metadata.

    showLoading(true, "Compiling Report...");

    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('patient_id', 'PT-' + Math.floor(Math.random() * 90000 + 10000));
    formData.append('patient_name', 'Patient #' + Math.floor(Math.random() * 100));
    // Pass existing scan type if we know it
    if (currentAnalysis.scan_type) formData.append('scan_type', currentAnalysis.scan_type);

    try {
        const response = await fetch(`${API_BASE_URL}/report/generate`, { method: 'POST', body: formData });
        const data = await response.json();
        currentReportData = data;

        populateReport(data);
        switchTab('report-tab');

    } catch (error) {
        alert('Report Generation Failed');
    } finally {
        showLoading(false);
    }
}

function populateReport(data) {
    if (!data.analysis) return;

    elements.repDate.textContent = new Date().toLocaleDateString();
    elements.repPatientId.textContent = data.patient_id;
    elements.repScanType.textContent = data.analysis.scan_type.toUpperCase();

    elements.repNarrative.textContent = data.analysis.report;

    elements.repClassification.textContent = data.analysis.classification;
    elements.repConfidence.textContent = data.analysis.confidence;

    elements.repFindingsList.innerHTML = '';
    data.analysis.findings.forEach(f => {
        const li = document.createElement('li');
        li.textContent = f;
        elements.repFindingsList.appendChild(li);
    });

    elements.repRecommendationsList.innerHTML = '';
    data.analysis.recommendations.forEach(r => {
        const li = document.createElement('li');
        li.textContent = r;
        elements.repRecommendationsList.appendChild(li);
    });
}

function downloadPDF() {
    const element = elements.reportContent;
    html2pdf().set({
        margin: 0.5,
        filename: `MedicalReport_${currentReportData ? currentReportData.patient_id : 'Scan'}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    }).from(element).save();
}

function showLoading(show, text = "Processing...") {
    if (show) {
        elements.loadingOverlay.querySelector('.loading-text').textContent = text;
        elements.loadingOverlay.classList.remove('hidden');
    } else {
        elements.loadingOverlay.classList.add('hidden');
    }
}
