"use strict";
function getApiBase() {
    // 1) Query param override: ?api=https://your-backend.example.com
    // 2) localStorage override (persisted)
    // 3) default: same origin (empty string)
    try {
        const params = new URLSearchParams(window.location.search);
        const qp = (params.get('api') || '').trim();
        if (qp)
            return qp.replace(/\/+$/, '');
    }
    catch { /* noop */ }
    try {
        const stored = (localStorage.getItem('apiBase') || '').trim();
        if (stored)
            return stored.replace(/\/+$/, '');
    }
    catch { /* noop */ }
    return '';
}
// API Base URL (dynamic)
let API_BASE = getApiBase();
function guessLanguageCode() {
    const navLang = (navigator.language || '').toLowerCase(); // e.g. "fr-fr"
    const code = navLang.split('-')[0] || '';
    return code || 'en';
}
// State
class AppState {
    constructor() {
        this.currentPage = 1;
        this.totalPages = 1;
        this.currentSearch = '';
        this.selectedLanguage = guessLanguageCode();
        this.selectedWordType = '';
        this.words = [];
        this.stats = { total_words: 0, translated_words: 0, vocab_file_exists: false };
        this.languages = {};
        this.isLoading = false;
    }
}
const state = new AppState();
// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadLanguages();
    loadStats();
    loadWords();
    setupEventListeners();
});
// Event Listeners
function setupEventListeners() {
    // Backend URL settings (for GitHub Pages / separate backend)
    const apiBaseInput = document.getElementById('apiBaseInput');
    const apiBaseSaveBtn = document.getElementById('apiBaseSaveBtn');
    const apiBaseClearBtn = document.getElementById('apiBaseClearBtn');
    if (apiBaseInput) {
        apiBaseInput.value = API_BASE;
    }
    if (apiBaseSaveBtn) {
        apiBaseSaveBtn.addEventListener('click', () => {
            const value = (apiBaseInput?.value || '').trim().replace(/\/+$/, '');
            try {
                localStorage.setItem('apiBase', value);
            }
            catch { /* noop */ }
            API_BASE = value;
            showToast(value ? `Backend set to: ${value}` : 'Using same-origin backend', 'success');
            state.currentPage = 1;
            loadLanguages();
            loadStats();
            loadWords();
        });
    }
    if (apiBaseClearBtn) {
        apiBaseClearBtn.addEventListener('click', () => {
            try {
                localStorage.removeItem('apiBase');
            }
            catch { /* noop */ }
            API_BASE = '';
            if (apiBaseInput)
                apiBaseInput.value = '';
            showToast('Backend cleared. Using same-origin backend.', 'success');
            state.currentPage = 1;
            loadLanguages();
            loadStats();
            loadWords();
        });
    }
    // Download button
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', handleDownload);
    }
    // Create Anki button
    const createAnkiBtn = document.getElementById('createAnkiBtn');
    if (createAnkiBtn) {
        createAnkiBtn.addEventListener('click', handleCreateAnki);
    }
    // Daily review button
    const dailyReviewBtn = document.getElementById('dailyReviewBtn');
    if (dailyReviewBtn) {
        dailyReviewBtn.addEventListener('click', () => {
            const modal = document.getElementById('dailyModal');
            if (modal) {
                modal.classList.add('active');
                loadDailyWords();
            }
        });
    }
    // Close modal
    const closeModal = document.getElementById('closeModal');
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            const modal = document.getElementById('dailyModal');
            if (modal) {
                modal.classList.remove('active');
            }
        });
    }
    // Search
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
    }
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleSearch();
            }
        });
    }
    // Pagination
    const firstPage = document.getElementById('firstPage');
    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');
    const lastPage = document.getElementById('lastPage');
    if (firstPage) {
        firstPage.addEventListener('click', () => {
            if (state.currentPage > 1) {
                state.currentPage = 1;
                loadWords();
            }
        });
    }
    if (prevPage) {
        prevPage.addEventListener('click', () => {
            if (state.currentPage > 1) {
                state.currentPage--;
                loadWords();
            }
        });
    }
    if (nextPage) {
        nextPage.addEventListener('click', () => {
            if (state.currentPage < state.totalPages) {
                state.currentPage++;
                loadWords();
            }
        });
    }
    if (lastPage) {
        lastPage.addEventListener('click', () => {
            if (state.currentPage < state.totalPages) {
                state.currentPage = state.totalPages;
                loadWords();
            }
        });
    }
    // Load daily words
    const loadDailyBtn = document.getElementById('loadDailyBtn');
    if (loadDailyBtn) {
        loadDailyBtn.addEventListener('click', loadDailyWords);
    }
    // Language selector
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        languageSelect.addEventListener('change', (e) => {
            state.selectedLanguage = e.target.value;
        });
    }
    // Word type filter
    const wordTypeFilter = document.getElementById('wordTypeFilter');
    if (wordTypeFilter) {
        wordTypeFilter.addEventListener('change', (e) => {
            state.selectedWordType = e.target.value;
            state.currentPage = 1;
            loadWords();
        });
    }
    // Close modal on outside click
    const dailyModal = document.getElementById('dailyModal');
    if (dailyModal) {
        dailyModal.addEventListener('click', (e) => {
            if (e.target && e.target.id === 'dailyModal') {
                dailyModal.classList.remove('active');
            }
        });
    }
}
// Load Languages
async function loadLanguages() {
    try {
        const response = await fetch(`${API_BASE}/api/languages`);
        const data = await response.json();
        state.languages = data.languages;
        // Prefer browser language when supported, otherwise server default, otherwise English.
        const browserLang = guessLanguageCode();
        state.selectedLanguage = state.languages?.[browserLang] ? browserLang : (data.default || 'en');
        // Populate language select
        const languageSelect = document.getElementById('languageSelect');
        if (languageSelect) {
            languageSelect.innerHTML = Object.entries(state.languages)
                .map(([code, name]) => `<option value="${code}" ${code === state.selectedLanguage ? 'selected' : ''}>${name}</option>`)
                .join('');
        }
    }
    catch (error) {
        console.error('Error loading languages:', error);
    }
}
// Load Stats
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data = await response.json();
        state.stats = data;
        const totalWordsEl = document.getElementById('totalWords');
        const translatedWordsEl = document.getElementById('translatedWords');
        if (totalWordsEl) {
            totalWordsEl.textContent = data.total_words.toLocaleString();
        }
        if (translatedWordsEl) {
            translatedWordsEl.textContent = data.translated_words.toLocaleString();
        }
    }
    catch (error) {
        console.error('Error loading stats:', error);
    }
}
// Load Words
async function loadWords(page = state.currentPage) {
    const grid = document.getElementById('wordsGrid');
    if (!grid)
        return;
    state.isLoading = true;
    grid.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading...</p></div>';
    try {
        const params = new URLSearchParams({
            page: page.toString(),
            per_page: '50',
            ...(state.currentSearch && { search: state.currentSearch }),
            ...(state.selectedWordType && { type: state.selectedWordType })
        });
        const response = await fetch(`${API_BASE}/api/words?${params}`);
        const data = await response.json();
        if (data.words.length === 0) {
            grid.innerHTML = '<div class="loading"><p>No words found</p></div>';
            return;
        }
        state.currentPage = data.page;
        state.totalPages = data.total_pages;
        state.words = data.words;
        updatePagination();
        attachPageNumberListeners();
        renderWords(data.words);
    }
    catch (error) {
        grid.innerHTML = `<div class="loading"><p style="color: var(--danger-color);">Error loading: ${error instanceof Error ? error.message : 'Unknown error'}</p></div>`;
    }
    finally {
        state.isLoading = false;
    }
}
// Render Words
function renderWords(words) {
    const grid = document.getElementById('wordsGrid');
    if (!grid)
        return;
    grid.innerHTML = words.map(word => createWordCard(word)).join('');
}
// Create Word Card
function createWordCard(word) {
    const hasDetails = !!(word.definition || word.word_type || word.examples);
    return `
        <div class="word-card" onclick="flipCard(this)">
            <div class="word-front">
                <div class="word-english">${escapeHtml(word.word)}</div>
                ${word.pronunciation ? `<div class="word-pronunciation">${escapeHtml(word.pronunciation)}</div>` : ''}
            </div>
            <div class="word-back">
                <div class="word-translation">${escapeHtml(word.translation || 'No translation')}</div>
                ${word.word_type ? `<div class="word-type-badge">${escapeHtml(word.word_type)}</div>` : ''}
                ${word.definition ? `<div class="word-definition">${escapeHtml(word.definition)}</div>` : ''}
                ${word.examples && word.examples.length > 0 ? `
                    <div class="word-examples">
                        <strong>Examples:</strong>
                        ${word.examples.map(ex => `<div class="example-item">${escapeHtml(ex)}</div>`).join('')}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}
// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
// Update Pagination
function updatePagination() {
    const pageInfo = document.getElementById('pageInfo');
    const pageNumbers = document.getElementById('pageNumbers');
    const firstPage = document.getElementById('firstPage');
    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');
    const lastPage = document.getElementById('lastPage');
    if (pageInfo) {
        pageInfo.textContent = `Page ${state.currentPage} of ${state.totalPages}`;
    }
    // Update button states
    if (firstPage) {
        firstPage.disabled = state.currentPage === 1;
    }
    if (prevPage) {
        prevPage.disabled = state.currentPage === 1;
    }
    if (nextPage) {
        nextPage.disabled = state.currentPage === state.totalPages;
    }
    if (lastPage) {
        lastPage.disabled = state.currentPage === state.totalPages;
    }
    // Generate page numbers
    if (pageNumbers) {
        pageNumbers.innerHTML = generatePageNumbers();
    }
}
// Generate page number buttons
function generatePageNumbers() {
    const totalPages = state.totalPages;
    const currentPage = state.currentPage;
    const pages = [];
    if (totalPages <= 7) {
        // Show all pages if 7 or fewer
        for (let i = 1; i <= totalPages; i++) {
            pages.push(createPageButton(i, i === currentPage));
        }
    }
    else {
        // Show first page
        pages.push(createPageButton(1, currentPage === 1));
        if (currentPage <= 3) {
            // Show pages 2, 3, 4
            for (let i = 2; i <= 4; i++) {
                pages.push(createPageButton(i, i === currentPage));
            }
            pages.push(createPageButton('...', false, true));
            pages.push(createPageButton(totalPages, false));
        }
        else if (currentPage >= totalPages - 2) {
            // Show last pages
            pages.push(createPageButton('...', false, true));
            for (let i = totalPages - 3; i <= totalPages; i++) {
                pages.push(createPageButton(i, i === currentPage));
            }
        }
        else {
            // Show middle pages
            pages.push(createPageButton('...', false, true));
            for (let i = currentPage - 1; i <= currentPage + 1; i++) {
                pages.push(createPageButton(i, i === currentPage));
            }
            pages.push(createPageButton('...', false, true));
            pages.push(createPageButton(totalPages, false));
        }
    }
    return pages.join('');
}
// Create page button HTML
function createPageButton(page, isActive, isEllipsis = false) {
    if (isEllipsis) {
        return `<span class="page-number ellipsis">${page}</span>`;
    }
    const pageNum = page;
    return `<button class="page-number ${isActive ? 'active' : ''}" data-page="${pageNum}">${pageNum}</button>`;
}
// Add event listeners for page number clicks
function attachPageNumberListeners() {
    const pageNumbers = document.getElementById('pageNumbers');
    if (pageNumbers) {
        pageNumbers.addEventListener('click', (e) => {
            const target = e.target;
            if (target.classList.contains('page-number') && !target.classList.contains('ellipsis')) {
                const page = parseInt(target.getAttribute('data-page') || '1', 10);
                if (page !== state.currentPage && page >= 1 && page <= state.totalPages) {
                    state.currentPage = page;
                    loadWords();
                }
            }
        });
    }
}
// Handle Search
function handleSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        state.currentSearch = searchInput.value.trim();
        state.currentPage = 1;
        loadWords();
    }
}
// Flip Card
function flipCard(card) {
    card.classList.toggle('flipped');
}
// Make flipCard available globally
window.flipCard = flipCard;
// Handle Download
async function handleDownload() {
    const btn = document.getElementById('downloadBtn');
    if (!btn)
        return;
    const originalText = btn.innerHTML;
    const includeDetails = document.getElementById('includeDetails')?.checked ?? true;
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span> Downloading...';
    try {
        const response = await fetch(`${API_BASE}/api/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                target_language: state.selectedLanguage,
                include_details: includeDetails
            })
        });
        const data = await response.json();
        if (data.success) {
            showToast(data.message, 'success');
            loadStats();
            setTimeout(() => loadWords(), 1000);
        }
        else {
            showToast(data.error || 'Download error', 'error');
        }
    }
    catch (error) {
        showToast('Server connection error', 'error');
    }
    finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}
// Handle Create Anki
async function handleCreateAnki() {
    const btn = document.getElementById('createAnkiBtn');
    if (!btn)
        return;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span> Creating...';
    try {
        const response = await fetch(`${API_BASE}/api/create-anki`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                deck_name: 'English Vocabulary 10000'
            })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Anki deck created! Downloading...', 'success');
            setTimeout(() => {
                window.location.href = `${API_BASE}/api/download-anki/${data.filename}`;
            }, 1000);
        }
        else {
            showToast(data.error || 'Error creating Anki deck', 'error');
        }
    }
    catch (error) {
        showToast('Server connection error', 'error');
    }
    finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}
// Load Daily Words
async function loadDailyWords() {
    const container = document.getElementById('dailyWords');
    if (!container)
        return;
    const countInput = document.getElementById('dailyCount');
    const count = parseInt(countInput?.value || '50', 10);
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading...</p></div>';
    try {
        const response = await fetch(`${API_BASE}/api/daily?count=${count}`);
        const data = await response.json();
        if (data.error) {
            container.innerHTML = `<p style="color: var(--danger-color);">${data.error}</p>`;
            return;
        }
        container.innerHTML = `
            <div style="grid-column: 1/-1; margin-bottom: 16px; padding: 12px; background: var(--bg-color); border-radius: 8px;">
                <strong>📅 Date:</strong> ${data.date} | 
                <strong>📊 Count:</strong> ${data.count.toLocaleString()} words
            </div>
            ${data.words.map((word) => createWordCard(word)).join('')}
        `;
    }
    catch (error) {
        container.innerHTML = `<p style="color: var(--danger-color);">Error: ${error instanceof Error ? error.message : 'Unknown error'}</p>`;
    }
}
// Show Toast
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast)
        return;
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
//# sourceMappingURL=app.js.map