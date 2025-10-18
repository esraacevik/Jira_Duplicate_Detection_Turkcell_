// =============================================
// Configuration
// =============================================
const API_BASE_URL = 'https://esracevik01-jira-duplicate-detection.hf.space/api';  // Hugging Face Spaces backend
const MIN_SEARCH_LENGTH = 10;
const DEBOUNCE_DELAY = 500;

// =============================================
// DOM Elements
// =============================================
const elements = {
    form: document.getElementById('reportForm'),
    summaryInput: document.getElementById('summary'),
    applicationSelect: document.getElementById('application'),
    platformSelect: document.getElementById('platform'),
    versionInput: document.getElementById('version'),
    searchBtn: document.getElementById('searchBtn'),
    charCount: document.getElementById('charCount'),
    loadingState: document.getElementById('loadingState'),
    resultsSection: document.getElementById('resultsSection'),
    resultsList: document.getElementById('resultsList'),
    warningBanner: document.getElementById('warningBanner'),
    noResults: document.getElementById('noResults'),
    resultsCount: document.getElementById('resultsCount'),
    searchTime: document.getElementById('searchTime'),
    duplicatesFound: document.getElementById('duplicatesFound')
};

// =============================================
// State Management
// =============================================
let searchTimeout = null;
let totalDuplicatesFound = 0;

// Character counter will be attached dynamically after form is built

// =============================================
// Form Submit Handler
// =============================================
elements.form.addEventListener('submit', (e) => {
    e.preventDefault();
    performSearch(true); // Show loading animation
});

// =============================================
// Search Function
// =============================================
async function performSearch(showLoading = true) {
    const summary = elements.summaryInput.value.trim();
    
    // Validation
    if (summary.length < MIN_SEARCH_LENGTH) {
        showNotification('lütfen en az 10 karakter girin', 'warning');
        return;
    }
    
    // Show loading state
    if (showLoading) {
        elements.loadingState.style.display = 'block';
        elements.resultsSection.style.display = 'none';
        elements.searchBtn.disabled = true;
    }
    
    // Get user's selected columns from systemConfig
    const systemConfig = JSON.parse(localStorage.getItem('systemConfig') || '{}');
    const selectedColumns = systemConfig.selectedColumns || ['Summary', 'Description'];
    
    // Get userId from session
    const session = JSON.parse(localStorage.getItem('userSession'));
    const userId = session?.uid || session?.username || 'anonymous';
    
    // Prepare request data
    const requestData = {
        query: summary,
        application: elements.applicationSelect.value || null,
        platform: elements.platformSelect.value || null,
        version: elements.versionInput.value || null,
        top_k: 10,
        selected_columns: selectedColumns,  // Send selected columns to backend
        user_id: userId  // Add user_id for user-specific search
    };
    
    console.log('🔍 Searching with user_id:', userId);
    
    try {
        const startTime = performance.now();
        
        // Make API call
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const endTime = performance.now();
        const searchTime = ((endTime - startTime) / 1000).toFixed(2);
        
        // Display results
        displayResults(data.results, searchTime);
        
        // Update stats
        totalDuplicatesFound += data.results.length;
        elements.duplicatesFound.textContent = totalDuplicatesFound;
        
    } catch (error) {
        console.error('Search error:', error);
        console.error('Error details:', error.message);
        console.log('API URL:', `${API_BASE_URL}/search`);
        alert(`API Balant Hatas!\n\nBackend alyor mu?\nURL: ${API_BASE_URL}/search\nHata: ${error.message}\n\nMock data gsteriliyor...`);
        displayMockResults(); // Show mock data for development
    } finally {
        elements.loadingState.style.display = 'none';
        elements.searchBtn.disabled = false;
    }
}

// =============================================
// Display Results
// =============================================
function displayResults(results, searchTime) {
    // Show results section
    elements.resultsSection.style.display = 'block';
    
    // Update meta info
    elements.resultsCount.textContent = `${results.length} sonu`;
    elements.searchTime.textContent = `~${searchTime}s`;
    
    // Check if we have results
    if (results.length === 0) {
        elements.warningBanner.style.display = 'none';
        elements.resultsList.style.display = 'none';
        elements.noResults.style.display = 'block';
        return;
    }
    
    // Show warning banner for similar reports
    elements.warningBanner.style.display = 'flex';
    elements.resultsList.style.display = 'block';
    elements.noResults.style.display = 'none';
    
    // Clear previous results
    elements.resultsList.innerHTML = '';
    
    // Render each result
    results.forEach((result, index) => {
        const card = createResultCard(result, index + 1);
        elements.resultsList.appendChild(card);
    });
    
    // Scroll to results
    elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// =============================================
// Create Result Card
// =============================================
function createResultCard(result, rank) {
    const card = document.createElement('div');
    card.className = 'result-card';
    
    // Determine match quality
    const { quality, emoji } = getMatchQuality(result.final_score);
    
    // Build metadata tags - show ALL properties except internal ones
    const excludedKeys = ['final_score', 'cross_encoder_score', 'version_similarity', 
                         'platform_similarity', 'language_similarity', 'index', 
                         'summary', 'Summary', 'description', 'Description', 'desc'];
    
    let metaTagsHTML = '';
    for (const [key, value] of Object.entries(result)) {
        if (!excludedKeys.includes(key) && value !== null && value !== undefined && value !== '' && value !== 'N/A') {
            const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            metaTagsHTML += `<span class="meta-tag" title="${displayKey}"><strong>${displayKey}:</strong> ${escapeHtml(String(value))}</span>`;
        }
    }
    
    // Prepare description with "Read More" functionality
    // Handle case-insensitive field names (Description vs description)
    const descValue = result.description || result.Description || result.desc || '';
    const summaryValue = result.summary || result.Summary || '';
    
    const fullDescription = escapeHtml(descValue);
    const shortDescription = descValue.length > 200 
        ? escapeHtml(descValue.substring(0, 200)) + '...' 
        : fullDescription;
    const needsReadMore = descValue.length > 200;
    
    // Build HTML
    card.innerHTML = `
        <div class="result-header">
            <div class="result-rank">
                <span class="rank-badge">#${rank}</span>
                <span class="match-quality match-${quality}">
                    ${emoji} ${getMatchQualityText(quality)}
                </span>
            </div>
            <span class="score-badge">Score: ${result.final_score.toFixed(4)}</span>
        </div>
        
        <div class="result-summary">${escapeHtml(summaryValue)}</div>
        
        <div class="result-description-container">
            <div class="result-description" data-full="${needsReadMore ? 'false' : 'true'}">
                <span class="description-text">${shortDescription}</span>
                <span class="description-full" style="display: none;">${fullDescription}</span>
            </div>
            ${needsReadMore ? `
                <button class="read-more-btn" onclick="toggleDescription(this)" style="
                    background: none;
                    border: none;
                    color: var(--primary-color);
                    font-weight: 600;
                    cursor: pointer;
                    padding: 4px 0;
                    margin-top: 4px;
                    font-size: 0.9rem;
                    text-decoration: underline;
                ">
                     Devamını Oku
                </button>
            ` : ''}
        </div>
        
        <div class="result-meta">
            ${metaTagsHTML}
        </div>
        
        <div class="result-scores">
            <span class="score-item">
                <span>Cross-Encoder:</span>
                <span class="score-value">${result.cross_encoder_score.toFixed(4)}</span>
            </span>
            ${result.version_similarity > 0 ? `
                <span class="score-item">
                    <span>Version:</span>
                    <span class="score-value">${result.version_similarity.toFixed(4)}</span>
                </span>
            ` : ''}
            ${result.platform_similarity > 0 ? `
                <span class="score-item">
                    <span>Platform:</span>
                    <span class="score-check"></span>
                </span>
            ` : ''}
            ${result.language_similarity > 0 ? `
                <span class="score-item">
                    <span>Language:</span>
                    <span class="score-check"></span>
                </span>
            ` : ''}
            <span class="score-item">
                <span>Index:</span>
                <span class="score-value">#${result.index}</span>
            </span>
        </div>
    `;
    
    return card;
}

// Toggle description visibility
function toggleDescription(button) {
    const container = button.previousElementSibling;
    const shortText = container.querySelector('.description-text');
    const fullText = container.querySelector('.description-full');
    const isFull = container.getAttribute('data-full') === 'true';
    
    if (isFull) {
        // Show short version
        shortText.style.display = 'inline';
        fullText.style.display = 'none';
        button.innerHTML = ' Devamını Oku';
        container.setAttribute('data-full', 'false');
    } else {
        // Show full version
        shortText.style.display = 'none';
        fullText.style.display = 'inline';
        button.innerHTML = ' Daha Az Göster';
        container.setAttribute('data-full', 'true');
    }
}

// =============================================
// Helper Functions
// =============================================
function getMatchQuality(score) {
    if (score >= 4.0) return { quality: 'excellent', emoji: '' };
    if (score >= 3.0) return { quality: 'very-good', emoji: '' };
    if (score >= 2.0) return { quality: 'good', emoji: '' };
    if (score >= 1.0) return { quality: 'moderate', emoji: '' };
    return { quality: 'weak', emoji: '' };
}

function getMatchQualityText(quality) {
    const texts = {
        'excellent': 'Mkemmel Eleme',
        'very-good': 'ok yi Eleme',
        'good': 'yi Eleme',
        'moderate': 'Orta Eleme',
        'weak': 'Zayf Eleme'
    };
    return texts[quality] || 'Bilinmeyen';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function hideResults() {
    elements.resultsSection.style.display = 'none';
}

function showNotification(message, type = 'info') {
    // Simple console notification for now
    console.log(`[${type.toUpperCase()}] ${message}`);
    // TODO: Implement toast notification
}

// =============================================
// Mock Data (for development without backend)
// =============================================
function displayMockResults() {
    const mockResults = [
        {
            index: 1234,
            summary: 'BiP mesaj gnderilirken uygulama kyor',
            description: 'Kullanc mesaj gndermeye altnda uygulama aniden kapanyor. Bu durum zellikle uzun mesajlarda grlyor...',
            application: 'BiP',
            platform: 'android',
            priority: 'high',
            component: 'Android Client',
            severity: 'Critical',
            cross_encoder_score: 5.2145,
            version_similarity: 1.0,
            platform_similarity: 1.0,
            language_similarity: 0.0,
            final_score: 5.9204
        },
        {
            index: 2345,
            summary: 'Mesaj gnderilemiyor, crash oluyor',
            description: 'Mesaj gnderme ilemi srasnda uygulama donuyor ve kapanyor...',
            application: 'BiP',
            platform: 'android',
            priority: 'medium',
            component: 'Android Client',
            severity: 'High',
            cross_encoder_score: 4.8521,
            version_similarity: 0.9,
            platform_similarity: 1.0,
            language_similarity: 0.0,
            final_score: 5.1875
        },
        {
            index: 3456,
            summary: 'Uygulama mesaj atarken kyor',
            description: 'BiP uygulamasnda mesaj yazp gnder butonuna bastmda uygulama kapanyor...',
            application: 'BiP',
            platform: 'android',
            priority: 'high',
            component: 'Android Client',
            severity: 'Critical',
            cross_encoder_score: 4.5123,
            version_similarity: 0.7,
            platform_similarity: 1.0,
            language_similarity: 0.0,
            final_score: 4.7654
        }
    ];
    
    displayResults(mockResults, '0.95');
}

// =============================================
// User Session Management
// =============================================
function showUserMenu() {
    const session = JSON.parse(localStorage.getItem('userSession'));
    const config = JSON.parse(localStorage.getItem('systemConfig'));
    
    const menu = confirm(
        ` ${session.name}\n` +
        ` ${session.username}\n` +
        `Role: ${session.role}\n\n` +
        ` Konfigürasyon:\n` +
        ` Sütunlar: ${config?.selectedColumns?.join(', ') || 'Varsayılan'}\n` +
        ` Model: ${config?.embeddingModel?.split('/').pop() || 'Varsayılan'}\n` +
        ` Top-K: ${config?.topK || '5'}\n\n` +
        `Çıkış yapmak istiyor musunuz?`
    );
    
    if (menu) {
        logout();
    }
}

function logout() {
    if (confirm('Çıkış yapmak istediğinizden emin misiniz?')) {
        localStorage.removeItem('userSession');
        localStorage.removeItem('dataSelection');
        localStorage.removeItem('systemConfig');
        window.location.href = 'login.html';
    }
}

// =============================================
// Load Statistics
// =============================================
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();
        
        if (data.success && data.stats) {
            // Update total reports count
            const totalReportsEl = document.getElementById('totalReports');
            if (totalReportsEl) {
                totalReportsEl.textContent = data.stats.total_reports.toLocaleString('tr-TR');
            }
            
            // If custom data is loaded, show a badge
            if (data.customDataLoaded) {
                const header = document.querySelector('.header');
                let badge = document.getElementById('customDataBadge');
                if (!badge) {
                    badge = document.createElement('div');
                    badge.id = 'customDataBadge';
                    badge.style.cssText = 'background: #10B981; color: white; padding: 6px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; margin-left: 12px; display: inline-block;';
                    badge.textContent = ` ${data.fileName}`;
                    const logo = header.querySelector('.logo');
                    logo.appendChild(badge);
                }
            }
        }
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

// =============================================
// Initialize
// =============================================
document.addEventListener('DOMContentLoaded', () => {
    console.log(' Bug Report System initialized');
    console.log('API Base URL:', API_BASE_URL);
    console.log('Ready to search for duplicate reports!');
    
    // Display user name
    const session = JSON.parse(localStorage.getItem('userSession'));
    if (session) {
        document.getElementById('userNameDisplay').textContent = session.name.split(' ')[0];
    }
    
    // Load statistics
    loadStatistics();
    
    // Build dynamic search form
    buildDynamicSearchForm();
    
    // Focus on summary input (after dynamic form is built)
    setTimeout(() => {
        const summaryInput = document.getElementById('summary');
        if (summaryInput) summaryInput.focus();
    }, 100);
});

// =============================================
// Build Dynamic Search Form Based on Selected Columns
// =============================================
async function buildDynamicSearchForm() {
    const config = JSON.parse(localStorage.getItem('systemConfig') || '{}');
    const selectedColumns = config.selectedColumns || [];
    const metadataColumns = config.metadataColumns || [];
    
    // Combine all columns (cross-encoder + metadata)
    const allColumns = [...new Set([...selectedColumns, ...metadataColumns])];
    
    const container = document.getElementById('dynamicSearchFields');
    const infoContainer = document.getElementById('selectedColumnsInfo');
    const columnsList = document.getElementById('selectedColumnsList');
    
    if (!container) return;
    
    // Display all selected columns info
    if (allColumns.length > 0 && infoContainer && columnsList) {
        columnsList.textContent = allColumns.join(', ');
        infoContainer.style.display = 'block';
    }
    
    // Kategorik stunlar (dropdown gsterilecek)
    const categoricalColumns = ['application', 'platform', 'priority', 'severity', 'frequency', 'component'];
    
    // Build form fields for all columns
    let formHTML = '';
    
    for (const columnName of allColumns) {
        const fieldId = columnName.toLowerCase().replace(/\s+/g, '_');
        const isCategorical = categoricalColumns.some(cat => fieldId.includes(cat));
        
        if (columnName.toLowerCase().includes('summary')) {
            formHTML += `
                <div class="form-group">
                    <label for="summary" class="form-label">
                        <span>${columnName}</span>
                        <span class="required">*</span>
                    </label>
                    <textarea 
                        id="summary" 
                        name="summary" 
                        class="form-input form-textarea"
                        placeholder="rn: Mesaj gnderilirken uygulama kyor..."
                        rows="3"
                        required
                    ></textarea>
                    <div class="input-hint">
                        <span id="charCount">0 / 200</span>
                    </div>
                </div>
            `;
        } else if (isCategorical) {
            // Kategorik sütun - dropdown gster
            formHTML += `
                <div class="form-group">
                    <label for="${fieldId}" class="form-label">${columnName}</label>
                    <select 
                        id="${fieldId}" 
                        name="${fieldId}" 
                        class="form-input form-select"
                        data-column="${columnName}"
                    >
                        <option value="">Ykleniyor...</option>
                    </select>
                </div>
            `;
        } else {
            // Normal text input
            formHTML += `
                <div class="form-group">
                    <label for="${fieldId}" class="form-label">${columnName}</label>
                    <input 
                        type="text" 
                        id="${fieldId}" 
                        name="${fieldId}" 
                        class="form-input"
                        placeholder="${columnName}"
                    >
                </div>
            `;
        }
    }
    
    container.innerHTML = formHTML;
    
    // Load options for categorical columns
    await loadCategoricalOptions(allColumns);
    
    // Re-attach character counter for summary
    const summaryInput = document.getElementById('summary');
    if (summaryInput) {
        summaryInput.addEventListener('input', (e) => {
            const length = e.target.value.length;
            const charCountEl = document.getElementById('charCount');
            if (charCountEl) {
                charCountEl.textContent = `${length} / 200`;
                charCountEl.style.color = length > 200 ? 'var(--danger-color)' : 'var(--gray-500)';
            }
            
            // Auto-search
            clearTimeout(searchTimeout);
            if (length >= MIN_SEARCH_LENGTH) {
                searchTimeout = setTimeout(() => {
                    performSearch(false);
                }, DEBOUNCE_DELAY);
            } else {
                hideResults();
            }
        });
    }
}

// =============================================
// Load Categorical Column Options
// =============================================
async function loadCategoricalOptions(allColumns) {
    const categoricalColumns = ['application', 'platform', 'priority', 'severity', 'frequency', 'component'];
    
    for (const columnName of allColumns) {
        const fieldId = columnName.toLowerCase().replace(/\s+/g, '_');
        const isCategorical = categoricalColumns.some(cat => fieldId.includes(cat));
        
        if (isCategorical) {
            const selectEl = document.getElementById(fieldId);
            if (!selectEl) continue;
            
            try {
                // Get current user's userId
                const session = JSON.parse(localStorage.getItem('userSession'));
                const userId = session?.uid || session?.username || 'anonymous';
                
                // Fetch unique values from backend
                const response = await fetch(`${API_BASE_URL}/column_values/${encodeURIComponent(columnName)}?user_id=${encodeURIComponent(userId)}`);
                const data = await response.json();
                
                if (data.success && data.values) {
                    // Build options
                    let optionsHTML = '<option value="">Tm</option>';
                    data.values.forEach(value => {
                        optionsHTML += `<option value="${value}">${value}</option>`;
                    });
                    selectEl.innerHTML = optionsHTML;
                } else {
                    selectEl.innerHTML = '<option value="">Seiniz</option>';
                }
            } catch (error) {
                console.error(`Failed to load options for ${columnName}:`, error);
                selectEl.innerHTML = '<option value="">Seiniz</option>';
            }
        }
    }
}

// =============================================
// Export for testing
// =============================================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        performSearch,
        displayResults,
        getMatchQuality
    };
}

