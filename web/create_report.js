// Configuration
const API_BASE_URL = 'http://localhost:5001/api';

// State
let searchTimeout = null;
let lastSearchParams = null;
let customDataLoaded = false;

// Check data status on load
async function checkDataStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/data_status`);
        if (response.ok) {
            const data = await response.json();
            customDataLoaded = data.customDataLoaded;
            console.log(' Data status:', customDataLoaded ? 'Custom data loaded' : 'Using default data');
            
            // Show banner if custom data is loaded
            if (customDataLoaded && data.dataInfo) {
                const banner = document.getElementById('customDataBanner');
                const info = document.getElementById('customDataInfo');
                
                if (banner && info) {
                    info.innerHTML = 
                        `<strong>Dosya:</strong> ${data.dataInfo.fileName}<br>` +
                        `<strong>Satr:</strong> ${data.dataInfo.rowCount.toLocaleString()}<br>` +
                        `<strong>sütun:</strong> ${data.dataInfo.columns.length}`;
                    banner.style.display = 'block';
                }
            }
        }
    } catch (error) {
        console.warn('Could not check data status:', error);
    }
}

// Initialize data status check
checkDataStatus();

// Form Submit Handler (will be attached in DOMContentLoaded)
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = document.getElementById('createReportForm');
    const submitBtn = document.getElementById('submitBtn');
    
    if (!form || !submitBtn) return;
    
    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Kaydediliyor...</span>';
    
    // Collect form data dynamically from all form inputs
    const formData = {};
    const formElements = form.querySelectorAll('input, select, textarea');
    
    formElements.forEach(element => {
        if (element.id && element.id !== 'submitBtn') {
            const value = element.value ? element.value.trim() : '';
            formData[element.id] = value;
        }
    });
    
    // Auto-generate Affects Version if component and app_version exist
    const componentEl = document.getElementById('component');
    const appVersionEl = document.getElementById('app_version') || document.getElementById('appVersion');
    
    if (componentEl && appVersionEl) {
        const component = componentEl.value;
        const appVersion = appVersionEl.value.trim();
        const platform = component.replace(' Client', '');
        const affectsVersion = appVersion ? `${platform} ${appVersion}` : '';
        
        formData.affects_version = affectsVersion;
        formData.component = component;
        formData.app_version = appVersion;
        
        console.log('Auto-generated Affects Version:', {
            component,
            platform,
            appVersion,
            affectsVersion
        });
    }
    
    console.log('Form data to submit:', formData);
    console.log('🔍 Checking reportToReplace:', reportToReplace);
    console.log('🔍 reportToReplace type:', typeof reportToReplace);
    console.log('🔍 reportToReplace === null?', reportToReplace === null);
    
    try {
        // Check if we're replacing an old report
        if (reportToReplace) {
            console.log('✅ reportToReplace is truthy, adding replace params...');
            formData.replace_report = true;
            formData.old_report_summary = reportToReplace.summary;
            formData.old_report_id = reportToReplace.reportId;
            console.log('🔄 Replacing old report:', reportToReplace);
            console.log('📤 formData with replace:', formData);
        } else {
            console.log('❌ reportToReplace is falsy, NOT replacing');
        }
        
        // Send to API
        const response = await fetch(`${API_BASE_URL}/create_report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Show success message
            const reportIdSpan = document.getElementById('reportId');
            const successMessage = document.getElementById('successMessage');
            
            if (reportIdSpan) reportIdSpan.textContent = data.report_id || 'N/A';
            if (successMessage) {
                // Update message based on whether we replaced a report
                if (reportToReplace) {
                    const successContent = successMessage.querySelector('strong');
                    if (successContent) {
                        successContent.innerHTML = `
                            <span style="font-size: 1.2rem; margin-right: 8px;">🔄</span>
                            Duplicate rapor başarıyla değiştirildi!
                        `;
                    }
                    const successPara = successMessage.querySelector('p');
                    if (successPara) {
                        successPara.innerHTML = `
                            Eski rapor silindi ve yeni rapor kaydedildi.<br>
                            Rapor ID: <strong id="reportId">${data.report_id || 'N/A'}</strong>
                        `;
                    }
                }
                
                successMessage.classList.add('show');
                successMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Hide success message after 5 seconds
                setTimeout(() => {
                    successMessage.classList.remove('show');
                }, 5000);
            }
            
            // Clear replace report state
            reportToReplace = null;
            const replaceMessage = document.getElementById('replaceMessage');
            if (replaceMessage) {
                replaceMessage.remove();
            }
            
            // Reset form
            form.reset();
        } else {
            throw new Error(data.error || 'Kaydetme baarsz');
        }
        
    } catch (error) {
        console.error('Create report error:', error);
        alert(`Rapor kaydedilemedi!\n\nHata: ${error.message}\n\nBackend alyor mu?`);
    } finally {
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Raporu Kaydet</span>';
    }
}

// Auto-detect Application from Summary (moved to attachFieldEventListeners)

// Search for Similar Reports
async function searchSimilarReports() {
    const summaryEl = document.getElementById('summary');
    const componentEl = document.getElementById('component');
    const appVersionEl = document.getElementById('appVersion');
    
    // Check if elements exist
    if (!summaryEl || !componentEl) {
        return; // Elements not yet created
    }
    
    const summary = summaryEl.value.trim();
    const component = componentEl.value;
    const appVersion = appVersionEl ? appVersionEl.value.trim() : '';
    
    // Need at least summary and component
    if (!summary || summary.length < 10 || !component) {
        if (similarReportsSection) {
            similarReportsSection.style.display = 'none';
        }
        return;
    }
    
    // Auto-detect application
    const summaryLower = summary.toLowerCase();
    let application = '';
    if (summaryLower.includes('bip')) application = 'BiP';
    else if (summaryLower.includes('tv+') || summaryLower.includes('tv plus')) application = 'TV+';
    else if (summaryLower.includes('fizy')) application = 'Fizy';
    else if (summaryLower.includes('paycell')) application = 'Paycell';
    else if (summaryLower.includes('lifebox')) application = 'LifeBox';
    else if (summaryLower.includes('hesabm') || summaryLower.includes('hesabim')) application = 'Hesabm';
    else if (summaryLower.includes('dergilik')) application = 'Dergilik';
    
    // Detect platform from component
    let platform = '';
    if (component.toLowerCase().includes('android')) platform = 'android';
    else if (component.toLowerCase().includes('ios')) platform = 'ios';
    
    // Check if search params changed
    const currentParams = JSON.stringify({ summary, application, platform, appVersion });
    if (currentParams === lastSearchParams) {
        return; // No change, skip search
    }
    lastSearchParams = currentParams;
    
    try {
        // Get elements
        const similarReportsSection = document.getElementById('similarReportsSection');
        const similarReportsList = document.getElementById('similarReportsList');
        
        if (!similarReportsSection || !similarReportsList) {
            return; // Elements not yet created
        }
        
        // Show loading
        similarReportsList.innerHTML = '<div style="text-align: center; padding: var(--spacing-lg); color: var(--gray-500);"> Benzer raporlar aranyor...</div>';
        similarReportsSection.style.display = 'block';
        
        // Build search request
        const searchRequest = {
            query: summary,
            top_k: 5
        };
        
        if (application) searchRequest.application = application;
        if (platform) searchRequest.platform = platform;
        if (appVersion) searchRequest.version = appVersion;
        
        // Call API
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(searchRequest)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display results
        if (data.results && data.results.length > 0) {
            displaySimilarReports(data.results);
        } else {
            const similarReportsSection = document.getElementById('similarReportsSection');
            if (similarReportsSection) {
                similarReportsSection.style.display = 'none';
            }
        }
        
    } catch (error) {
        console.error('Similar reports search error:', error);
        const similarReportsSection = document.getElementById('similarReportsSection');
        if (similarReportsSection) {
            similarReportsSection.style.display = 'none';
        }
    }
}

// Display Similar Reports
function displaySimilarReports(results) {
    const similarReportsSection = document.getElementById('similarReportsSection');
    const similarReportsList = document.getElementById('similarReportsList');
    const similarCount = document.getElementById('similarCount');
    
    if (!similarReportsSection || !similarReportsList || !similarCount) {
        return; // Elements not yet created
    }
    
    if (!results || results.length === 0) {
        similarReportsSection.style.display = 'none';
        return;
    }
    
    similarCount.textContent = results.length;
    similarReportsSection.style.display = 'block';
    
    // Copy result card HTML from app.js style
    similarReportsList.innerHTML = results.map((result, index) => {
        const matchQuality = getMatchQuality(result.final_score);
        const versionDisplay = result.app_version || 'N/A';
        
        return `
            <div class="result-card">
                <div class="result-header">
                    <span class="result-rank">#${index + 1}</span>
                    <span class="match-badge ${matchQuality.class}">${matchQuality.icon} ${matchQuality.text}</span>
                    <span class="result-score">Score: ${result.final_score.toFixed(4)}</span>
                </div>
                
                <h3 class="result-title">${escapeHtml(result.summary)}</h3>
                <p class="result-description">${escapeHtml(result.description.substring(0, 150))}...</p>
                
                <div class="result-meta">
                    <span class="meta-tag" title="Application"> ${result.application || 'Unknown'}</span>
                    <span class="meta-tag" title="Platform"> ${result.platform || 'unknown'}</span>
                    <span class="meta-tag" title="Version"> ${versionDisplay}</span>
                    <span class="meta-tag" title="Priority"> ${result.priority || 'none'}</span>
                </div>
                
                <div class="result-scores">
                    <div class="score-item">
                        <span class="score-label">Cross-Encoder:</span>
                        <span class="score-value">${result.cross_encoder_score.toFixed(4)}</span>
                    </div>
                    <div class="score-item">
                        <span class="score-label">Version:</span>
                        <span class="score-value">${result.version_similarity.toFixed(4)}</span>
                    </div>
                    <div class="score-item">
                        <span class="score-label">Platform:</span>
                        <span class="score-value">${result.platform_match ? '' : ''}</span>
                    </div>
                </div>
                
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--gray-200); display: flex; gap: 8px; align-items: center;">
                    <button 
                        class="replace-report-btn btn btn-secondary" 
                        data-index="${index}"
                        data-summary="${result.summary}"
                        data-report-id="${result.report_id || index}"
                        style="flex: 1; padding: 8px 16px; font-size: 0.85rem; background: linear-gradient(135deg, #FF9500 0%, #FF6B00 100%); color: white; border: none;"
                        title="Bu rapor duplicate ise, yeni raporu bu eskisinin yerine kaydet"
                    >
                        <span style="margin-right: 4px;">🔄</span>
                        <span>Bu Raporu Değiştir</span>
                    </button>
                    <span style="font-size: 0.75rem; color: var(--gray-500);">
                        (Eski rapor silinecek)
                    </span>
                </div>
            </div>
        `;
    }).join('');
    
    // Attach event listeners to replace buttons
    setTimeout(() => {
        const replaceButtons = document.querySelectorAll('.replace-report-btn');
        replaceButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const index = parseInt(this.getAttribute('data-index'));
                const summary = this.getAttribute('data-summary');
                const reportId = this.getAttribute('data-report-id');
                replaceReport(index, summary, reportId);
            });
        });
    }, 100);
}

// Replace Report - Delete old and save new
let reportToReplace = null;

function replaceReport(index, summary, reportId) {
    console.log('🔄 replaceReport called:', { index, summary, reportId });
    
    const confirmed = confirm(
        `🔄 Duplicate Rapor Değiştirme\n\n` +
        `Bu işlem:\n` +
        `1. Eski raporu ("${summary.substring(0, 50)}...") datadan silecek\n` +
        `2. Yeni raporu bunun yerine kaydedecek\n\n` +
        `Bu işlem geri alınamaz!\n\n` +
        `Devam etmek istiyor musunuz?`
    );
    
    if (confirmed) {
        // Store the report to replace
        reportToReplace = {
            index: index,
            summary: summary,
            reportId: reportId
        };
        
        console.log('✅ reportToReplace set:', reportToReplace);
        
        // Visually mark the card
        const cards = document.querySelectorAll('.result-card');
        cards.forEach((card, i) => {
            if (i === index) {
                card.style.border = '3px solid #FF9500';
                card.style.background = 'linear-gradient(135deg, #FFF9E6 0%, #FFEDD5 100%)';
            } else {
                card.style.opacity = '0.5';
            }
        });
        
        // Show message
        const messageDiv = document.createElement('div');
        messageDiv.id = 'replaceMessage';
        messageDiv.style.cssText = `
            background: linear-gradient(135deg, #FF9500 0%, #FF6B00 100%);
            color: white;
            padding: 16px;
            border-radius: 8px;
            margin: 16px 0;
            text-align: center;
            font-weight: 600;
            animation: pulse 2s infinite;
        `;
        messageDiv.innerHTML = `
            <span style="font-size: 1.2rem; margin-right: 8px;">🔄</span>
            <span>Seçilen rapor değiştirilecek! "Raporu Kaydet" butonuna tıklayın.</span>
        `;
        
        const similarReportsSection = document.getElementById('similarReportsSection');
        if (similarReportsSection) {
            similarReportsSection.insertBefore(messageDiv, similarReportsSection.firstChild);
        }
        
        // Scroll to form
        document.getElementById('createReportForm').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Get Match Quality
function getMatchQuality(score) {
    if (score >= 5.0) return { class: 'excellent', icon: '', text: 'Mükemmel Eşleşme' };
    if (score >= 4.0) return { class: 'good', icon: '', text: 'İyi Eşleşme' };
    if (score >= 3.0) return { class: 'moderate', icon: '', text: 'Orta Eşleşme' };
    return { class: 'weak', icon: '', text: 'Zayıf Eşleşme' };
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Debounced Search Trigger
function triggerSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(searchSimilarReports, 800); // 800ms debounce
}

// Real-time search listeners (moved to attachFieldEventListeners)

// User Session Management
function showUserMenu() {
    const session = JSON.parse(localStorage.getItem('userSession'));
    const config = JSON.parse(localStorage.getItem('systemConfig'));
    
    const menu = confirm(
        ` ${session.name}\n` +
        ` ${session.username}\n` +
        ` Role: ${session.role}\n\n` +
        ` Konfigrasyon:\n` +
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

// Load Statistics
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

// Build dynamic form fields based on selected cross-encoder and metadata columns
async function buildDynamicFormFields() {
    console.log(' buildDynamicFormFields() called');
    
    const container = document.getElementById('dynamicFormFields');
    if (!container) {
        console.error('Dynamic form fields container not found!');
        return;
    }
    
    const configString = localStorage.getItem('systemConfig');
    if (!configString) {
        console.warn(' No system config found, using default form');
        buildDefaultForm();
        return;
    }
    
    let config;
    try {
        config = JSON.parse(configString);
    } catch (e) {
        console.error('Failed to parse config:', e);
        buildDefaultForm();
        return;
    }
    
    const crossEncoderColumns = config.selectedColumns || [];
    const metadataColumns = config.metadataColumns || [];
    const selectedColumns = [...new Set([...crossEncoderColumns, ...metadataColumns])];
    
    // STEP 1: Backend'den datadaki TÜM sütunları al
    let allDataColumns = [];
    try {
        const response = await fetch(`${API_BASE_URL}/data_status`);
        const data = await response.json();
        
        // Custom data varsa onun sütunlarını, yoksa default sütunları al
        if (data.custom_data_loaded && data.custom_data_columns) {
            allDataColumns = data.custom_data_columns;
        } else if (data.default_data_columns) {
            allDataColumns = data.default_data_columns;
        }
        
        console.log(' Datadaki TÜM sütunlar:', allDataColumns);
    } catch (error) {
        console.error('Backend\'den sütunlar alınamadı:', error);
    }
    
    // STEP 2: Seçili ve seçilmemiş sütunları ayır
    const unselectedColumns = allDataColumns.filter(col => !selectedColumns.includes(col));
    
    console.log('SEÇİLEN sütunlar (Önce Bu Alanları Doldurun):', selectedColumns);
    console.log(' SEÇİLMEMİŞ sütunlar (Ek Bilgiler):', unselectedColumns);
    
    container.innerHTML = '';
    
    // STEP 3: ÖNEMLİ bölümünü oluştur (Seçili sütunlar)
    let fieldsHTML = `
        <div style="background: linear-gradient(135deg, #FFF9E6 0%, #FFE5B4 100%); padding: 16px; border-radius: 8px; border: 2px solid var(--primary-color); margin-bottom: 24px;">
            <h3 style="color: #1a1a1a; margin: 0 0 16px 0;"> Önce Bu Alanları Doldurun <span style="background: var(--primary-color); color: var(--secondary-color); padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; margin-left: 8px;">ÖNEMLİ</span></h3>
    `;
    
    selectedColumns.forEach(columnName => {
        const fieldHTML = createFormField(columnName, true);
        if (fieldHTML) fieldsHTML += fieldHTML;
    });
    
    fieldsHTML += '</div>';
    
    // STEP 4: EK BİLGİLER bölümünü oluştur (Seçilmemiş sütunlar)
    if (unselectedColumns.length > 0) {
        fieldsHTML += `
            <div style="margin-top: 24px;">
                <h3 style="color: #1a1a1a; margin: 0 0 16px 0;"> Ek Bilgiler (İsteğe Bağlı)</h3>
                <div class="form-row">
        `;
        
        unselectedColumns.forEach(columnName => {
            const fieldHTML = createFormField(columnName, false);
            if (fieldHTML) fieldsHTML += fieldHTML;
        });
        
        fieldsHTML += '</div></div>';
    }
    
    container.innerHTML = fieldsHTML;
    attachFieldEventListeners();
    console.log('Form oluşturuldu!');
}

// Build default form if no configuration is found
function buildDefaultForm() {
    const container = document.getElementById('dynamicFormFields');
    if (!container) return;
    
    container.innerHTML = `
        <!-- Summary -->
        <div class="form-group">
            <label for="summary" class="form-label">
                <span>Summary (zet)</span>
                <span class="required">*</span>
            </label>
            <input 
                type="text" 
                id="summary" 
                name="summary" 
                class="form-input"
                placeholder="Örnek: BiP mesaj gönderilirken uygulama çöküyor"
                required
                style="border: 2px solid var(--primary-color);"
            >
            <div style="font-size: 0.8rem; color: var(--gray-600); margin-top: 4px;">
                 Uygulama adn yazn (BiP, TV+, Fizy, vb.) - Otomatik tespit edilecek
            </div>
        </div>
        
        <!-- Platform and Version Row -->
        <div class="form-row">
            <div class="form-group">
                <label for="component" class="form-label">
                    <span>Platform</span>
                    <span class="required">*</span>
                </label>
                <select id="component" name="component" class="form-input form-select" required style="border: 2px solid var(--primary-color);">
                    <option value="">Seçiniz</option>
                    <option value="Android"> Android</option>
                    <option value="iOS"> iOS</option>
                    <option value="Web"> Web</option>
                </select>
                <div style="font-size: 0.8rem; color: var(--gray-600); margin-top: 4px;">
                     Platform bilgisi otomatik tespit edilir
                </div>
            </div>

            <div class="form-group">
                <label for="appVersion" class="form-label">
                    <span>App Version (Srm)</span>
                </label>
                <input 
                    type="text" 
                    id="appVersion" 
                    name="appVersion" 
                    class="form-input"
                    placeholder="Örnek: 3.70.19"
                    style="border: 2px solid var(--primary-color);"
                >
                <div style="font-size: 0.8rem; color: var(--gray-600); margin-top: 4px;">
                     Affects Version otomatik oluşturulacak (Platform + Sürüm)
                </div>
            </div>
        </div>
    `;
    
    attachFieldEventListeners();
}

// Create form field HTML based on column name
function createFormField(columnName, isCrossEncoder = false) {
    const col = columnName.toLowerCase();
    const fieldId = columnName.replace(/\s+/g, '_').toLowerCase();
    
    // Summary (Cross-encoder column)
    if (col.includes('summary') || col.includes('zet')) {
        return `
            <div class="form-group">
                <label for="summary" class="form-label">
                    <span>${columnName}</span>
                    <span class="required">*</span>
                </label>
                <input 
                    type="text" 
                    id="summary" 
                    name="summary" 
                    class="form-input"
                    placeholder="Örnek: BiP mesaj gönderilirken uygulama çöküyor"
                    required
                    style="border: 2px solid var(--primary-color);"
                >
                <div style="font-size: 0.8rem; color: var(--gray-600); margin-top: 4px;">
                     Uygulama adn yazn (BiP, TV+, Fizy, vb.) - Otomatik tespit edilecek
                </div>
            </div>
        `;
    }
    
    // Description (Cross-encoder column)
    if (col.includes('description') || col.includes('açıklama')) {
        return `
            <div class="form-group">
                <label for="description" class="form-label">
                    <span>${columnName}</span>
                </label>
                <textarea 
                    id="description" 
                    name="description" 
                    class="form-input form-textarea"
                    placeholder="Test admlar, beklenen ve gzlemlenen sonu..."
                    rows="4"
                    style="border: 2px solid var(--primary-color);"
                ></textarea>
                <div style="font-size: 0.8rem; color: var(--gray-600); margin-top: 4px;">
                     Detaylı açıklama benzer raporlar bulmak için önemlidir
                </div>
            </div>
        `;
    }
    
    // Platform / Component (Metadata column)
    if (col.includes('platform') || col.includes('component')) {
        return `
            <div class="form-group">
                <label for="component" class="form-label">
                    <span>${columnName}</span>
                    <span class="required">*</span>
                </label>
                <select id="component" name="component" class="form-input form-select" required style="border: 2px solid var(--primary-color);">
                    <option value="">Seçiniz</option>
                    <option value="Android"> Android</option>
                    <option value="iOS"> iOS</option>
                    <option value="Web"> Web</option>
                </select>
                <div style="font-size: 0.8rem; color: var(--gray-600); margin-top: 4px;">
                     Platform bilgisi otomatik tespit edilir
                </div>
            </div>
        `;
    }
    
    // App Version (Metadata column)
    if (col.includes('app version') || (col.includes('version') && !col.includes('affects'))) {
        return `
            <div class="form-group">
                <label for="appVersion" class="form-label">
                    <span>${columnName}</span>
                </label>
                <input 
                    type="text" 
                    id="appVersion" 
                    name="appVersion" 
                    class="form-input"
                    placeholder="Örnek: 3.70.19"
                    style="border: 2px solid var(--primary-color);"
                >
                <div style="font-size: 0.8rem; color: var(--gray-600); margin-top: 4px;">
                     Affects Version otomatik oluşturulacak (Platform + Sürüm)
                </div>
            </div>
        `;
    }
    
    // Application (Metadata column) - DROPDOWN
    if (col.includes('application') || col.includes('uygulama')) {
        return `
            <div class="form-group">
                <label for="application" class="form-label">
                    <span>${columnName}</span>
                </label>
                <select 
                    id="application" 
                    name="application" 
                    class="form-input form-select categorical-field"
                    data-column="${columnName}"
                    style="border: 2px solid var(--primary-color);"
                >
                    <option value="">Yükleniyor...</option>
                </select>
                <div style="font-size: 0.8rem; color: var(--gray-600); margin-top: 4px;">
                     Uygulama seçiniz
                </div>
            </div>
        `;
    }
    
    // Priority (Metadata column) - DROPDOWN
    if (col.includes('priority') || col.includes('ncelik')) {
        return `
            <div class="form-group">
                <label for="priority" class="form-label">
                    <span>${columnName}</span>
                </label>
                <select 
                    id="priority" 
                    name="priority" 
                    class="form-input form-select categorical-field"
                    data-column="${columnName}"
                    style="border: 2px solid var(--primary-color);"
                >
                    <option value="">Yükleniyor...</option>
                </select>
            </div>
        `;
    }
    
    // Check if it's a categorical column (for other columns)
    const categoricalColumns = ['severity', 'frequency', 'status', 'type'];
    const isCategorical = categoricalColumns.some(cat => col.includes(cat));
    
    if (isCategorical) {
        return `
            <div class="form-group">
                <label for="${fieldId}" class="form-label">
                    <span>${columnName}</span>
                </label>
                <select 
                    id="${fieldId}" 
                    name="${fieldId}" 
                    class="form-input form-select categorical-field"
                    data-column="${columnName}"
                    style="border: 2px solid var(--primary-color);"
                >
                    <option value="">Yükleniyor...</option>
                </select>
            </div>
        `;
    }
    
    // Generic text input for other columns
    return `
        <div class="form-group">
            <label for="${fieldId}" class="form-label">
                <span>${columnName}</span>
            </label>
            <input 
                type="text" 
                id="${fieldId}" 
                name="${fieldId}" 
                class="form-input"
                placeholder="${columnName}"
                style="border: 2px solid var(--primary-color);"
            >
        </div>
    `;
}

// Load categorical options for dropdown fields
async function loadCategoricalFieldOptions() {
    const categoricalFields = document.querySelectorAll('.categorical-field');
    
    for (const field of categoricalFields) {
        const columnName = field.getAttribute('data-column');
        if (!columnName) continue;
        
        try {
            const response = await fetch(`${API_BASE_URL}/column_values/${encodeURIComponent(columnName)}`);
            const data = await response.json();
            
            if (data.success && data.values) {
                let optionsHTML = '<option value="">Seçiniz</option>';
                data.values.forEach(value => {
                    optionsHTML += `<option value="${value}">${value}</option>`;
                });
                field.innerHTML = optionsHTML;
            } else {
                field.innerHTML = '<option value="">Seçiniz</option>';
            }
        } catch (error) {
            console.error(`Failed to load options for ${columnName}:`, error);
            field.innerHTML = '<option value="">Seiniz</option>';
        }
    }
}

// Re-attach event listeners to dynamically created fields
function attachFieldEventListeners() {
    const summaryField = document.getElementById('summary');
    const descriptionField = document.getElementById('description');
    const componentField = document.getElementById('component');
    const appVersionField = document.getElementById('appVersion');
    const applicationField = document.getElementById('application');
    
    // Load categorical dropdown options
    loadCategoricalFieldOptions();
    
    if (summaryField) {
        summaryField.addEventListener('input', triggerSearch);
        
        // Auto-detect Application from Summary
        summaryField.addEventListener('input', (e) => {
            const summary = e.target.value.toLowerCase();
            const form = document.getElementById('createReportForm');
            
            // Simple application detection
            let detectedApp = 'Unknown';
            if (summary.includes('bip')) detectedApp = 'BiP';
            else if (summary.includes('tv+') || summary.includes('tv plus')) detectedApp = 'TV+';
            else if (summary.includes('fizy')) detectedApp = 'Fizy';
            else if (summary.includes('paycell')) detectedApp = 'Paycell';
            else if (summary.includes('lifebox')) detectedApp = 'LifeBox';
            
            // Store for later use
            if (form) {
                form.dataset.detectedApp = detectedApp;
            }
            
            // Auto-fill Application field if it exists
            if (applicationField && !applicationField.value) {
                applicationField.value = detectedApp;
            }
        });
    }
    
    if (descriptionField) {
        descriptionField.addEventListener('input', triggerSearch);
    }
    
    if (componentField) {
        componentField.addEventListener('change', triggerSearch);
    }
    
    if (appVersionField) {
        appVersionField.addEventListener('input', triggerSearch);
    }
    
    console.log('Event listeners attached to form fields');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Create Report Form initialized');
    console.log('API Base URL:', API_BASE_URL);
    console.log('Real-time similar report search enabled');

    // Display user name
    const session = JSON.parse(localStorage.getItem('userSession'));
    if (session) {
        const userNameDisplay = document.getElementById('userNameDisplay');
        if (userNameDisplay) {
            userNameDisplay.textContent = session.name.split(' ')[0];
        }
    }

    // Build dynamic form fields
    buildDynamicFormFields();

    // Attach form submit handler
    const form = document.getElementById('createReportForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
        console.log('Form submit handler attached');
    }

    // Load statistics
    loadStatistics();
});

