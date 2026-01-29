function getApiBase(): string {
    // 1) Query param override: ?api=https://your-backend.example.com
    // 2) localStorage override (persisted)
    // 3) default: same origin (empty string)
    try {
        const params = new URLSearchParams(window.location.search);
        const qp = (params.get('api') || '').trim();
        if (qp) return qp.replace(/\/+$/, '');
    } catch { /* noop */ }
    try {
        const stored = (localStorage.getItem('apiBase') || '').trim();
        if (stored) return stored.replace(/\/+$/, '');
    } catch { /* noop */ }
    return '';
}

// API Base URL (dynamic)
let API_BASE = getApiBase();

function guessLanguageCode(): string {
    const navLang = (navigator.language || '').toLowerCase(); // e.g. "fr-fr"
    const code = navLang.split('-')[0] || '';
    return code || 'en';
}

// Types
interface Word {
    word: string;
    translation?: string;
    definition?: string;
    word_type?: string;
    examples?: string[];
    pronunciation?: string;
}

interface Stats {
    total_words: number;
    translated_words: number;
    vocab_file_exists: boolean;
}

interface Languages {
    [key: string]: string;
}

interface WordsResponse {
    words: Word[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
}

type OfflineWordsPayload = { words: string[] };

// State
class AppState {
    currentPage: number = 1;
    totalPages: number = 1;
    currentSearch: string = '';
    selectedLanguage: string = guessLanguageCode();
    selectedWordType: string = '';
    words: Word[] = [];
    stats: Stats = { total_words: 0, translated_words: 0, vocab_file_exists: false };
    languages: Languages = {};
    isLoading: boolean = false;
}

const state = new AppState();

let offlineWords: Word[] | null = null;

function isOfflineMode(): boolean {
    // If API_BASE is empty and server endpoints are not reachable, we fall back to static words.json
    return offlineWords !== null;
}

function hasBackendConfigured(): boolean {
    return !!API_BASE;
}

function updateBackendUiVisibility(): void {
    const downloadBtn = document.getElementById('downloadBtn') as HTMLButtonElement | null;
    const createAnkiBtn = document.getElementById('createAnkiBtn') as HTMLButtonElement | null;
    const dailyReviewBtn = document.getElementById('dailyReviewBtn') as HTMLButtonElement | null;

    const show = hasBackendConfigured();
    // On free/offline mode (Pages), hide backend-only features.
    if (downloadBtn) downloadBtn.style.display = show ? '' : 'none';
    if (createAnkiBtn) createAnkiBtn.style.display = show ? '' : 'none';
    if (dailyReviewBtn) dailyReviewBtn.style.display = show ? '' : 'none';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadLanguages();
    loadStats();
    loadWords();
    setupEventListeners();
    updateBackendUiVisibility();
});

// Event Listeners
function setupEventListeners(): void {
    // Download button
    const downloadBtn = document.getElementById('downloadBtn') as HTMLButtonElement;
    if (downloadBtn) {
        downloadBtn.addEventListener('click', handleDownload);
    }
    
    // Create Anki button
    const createAnkiBtn = document.getElementById('createAnkiBtn') as HTMLButtonElement;
    if (createAnkiBtn) {
        createAnkiBtn.addEventListener('click', handleCreateAnki);
    }
    
    // Daily review button
    const dailyReviewBtn = document.getElementById('dailyReviewBtn') as HTMLButtonElement;
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
    const searchBtn = document.getElementById('searchBtn') as HTMLButtonElement;
    const searchInput = document.getElementById('searchInput') as HTMLInputElement;
    
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
    const firstPage = document.getElementById('firstPage') as HTMLButtonElement;
    const prevPage = document.getElementById('prevPage') as HTMLButtonElement;
    const nextPage = document.getElementById('nextPage') as HTMLButtonElement;
    const lastPage = document.getElementById('lastPage') as HTMLButtonElement;
    
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
    const loadDailyBtn = document.getElementById('loadDailyBtn') as HTMLButtonElement;
    if (loadDailyBtn) {
        loadDailyBtn.addEventListener('click', loadDailyWords);
    }
    
    // Language selector
    const languageSelect = document.getElementById('languageSelect') as HTMLSelectElement;
    if (languageSelect) {
        languageSelect.addEventListener('change', (e) => {
            state.selectedLanguage = (e.target as HTMLSelectElement).value;
        });
    }
    
    // Word type filter
    const wordTypeFilter = document.getElementById('wordTypeFilter') as HTMLSelectElement;
    if (wordTypeFilter) {
        wordTypeFilter.addEventListener('change', (e) => {
            state.selectedWordType = (e.target as HTMLSelectElement).value;
            state.currentPage = 1;
            loadWords();
        });
    }
    
    // Close modal on outside click
    const dailyModal = document.getElementById('dailyModal');
    if (dailyModal) {
        dailyModal.addEventListener('click', (e) => {
            if (e.target && (e.target as HTMLElement).id === 'dailyModal') {
                dailyModal.classList.remove('active');
            }
        });
    }
}

// Load Languages
async function loadLanguages(): Promise<void> {
    // Offline/Pages mode: do not call backend, just use a small built-in list.
    if (!hasBackendConfigured()) {
        state.languages = {
            en: 'English',
            es: 'Spanish',
            fr: 'French',
            de: 'German',
            it: 'Italian',
            pt: 'Portuguese',
            ru: 'Russian',
            ar: 'Arabic',
            tr: 'Turkish',
            hi: 'Hindi',
            fa: 'Persian',
            ja: 'Japanese',
            ko: 'Korean',
            zh: 'Chinese',
        };
        const browserLang = guessLanguageCode();
        state.selectedLanguage = state.languages[browserLang] ? browserLang : 'en';
        const languageSelect = document.getElementById('languageSelect') as HTMLSelectElement;
        if (languageSelect) {
            languageSelect.innerHTML = Object.entries(state.languages)
                .map(([code, name]) => `<option value="${code}" ${code === state.selectedLanguage ? 'selected' : ''}>${name}</option>`)
                .join('');
        }
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/api/languages`);
        const data = await response.json();
        state.languages = data.languages;
        // Prefer browser language when supported, otherwise server default, otherwise English.
        const browserLang = guessLanguageCode();
        state.selectedLanguage = state.languages?.[browserLang] ? browserLang : (data.default || 'en');
        
        // Populate language select
        const languageSelect = document.getElementById('languageSelect') as HTMLSelectElement;
        if (languageSelect) {
            languageSelect.innerHTML = Object.entries(state.languages)
                .map(([code, name]) => `<option value="${code}" ${code === state.selectedLanguage ? 'selected' : ''}>${name}</option>`)
                .join('');
        }
    } catch (error) {
        console.error('Error loading languages:', error);
    }
}

// Load Stats
async function loadStats(): Promise<void> {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data: Stats = await response.json();
        state.stats = data;
        
        const totalWordsEl = document.getElementById('totalWords');
        const translatedWordsEl = document.getElementById('translatedWords');
        
        if (totalWordsEl) {
            totalWordsEl.textContent = data.total_words.toLocaleString();
        }
        if (translatedWordsEl) {
            translatedWordsEl.textContent = data.translated_words.toLocaleString();
        }
    } catch (error) {
        // Offline fallback: compute from static list if available
        if (offlineWords) {
            state.stats = {
                total_words: offlineWords.length,
                translated_words: offlineWords.filter(w => !!w.translation).length,
                vocab_file_exists: true
            };
            const totalWordsEl = document.getElementById('totalWords');
            const translatedWordsEl = document.getElementById('translatedWords');
            if (totalWordsEl) totalWordsEl.textContent = state.stats.total_words.toLocaleString();
            if (translatedWordsEl) translatedWordsEl.textContent = state.stats.translated_words.toLocaleString();
            return;
        }
        console.error('Error loading stats:', error);
    }
}

// Load Words
async function loadWords(page: number = state.currentPage): Promise<void> {
    const grid = document.getElementById('wordsGrid');
    if (!grid) return;
    
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
        const data: WordsResponse = await response.json();
        
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
        
    } catch (error) {
        // Offline fallback: load static list and do client-side pagination/search.
        try {
            if (!offlineWords) {
                const offlineResp = await fetch('static/data/words.json', { cache: 'no-cache' });
                const payload = (await offlineResp.json()) as OfflineWordsPayload;
                offlineWords = (payload.words || []).map((w) => ({ word: w }));
            }

            const q = state.currentSearch.trim().toLowerCase();
            const t = state.selectedWordType.trim().toLowerCase();
            let list = offlineWords || [];
            if (q) {
                list = list.filter(w =>
                    w.word.toLowerCase().includes(q) ||
                    (w.translation || '').toLowerCase().includes(q) ||
                    (w.definition || '').toLowerCase().includes(q)
                );
            }
            if (t) {
                list = list.filter(w => (w.word_type || '').toLowerCase() === t);
            }

            const perPage = 50;
            const total = list.length;
            const totalPages = Math.max(1, Math.ceil(total / perPage));
            const safePage = Math.min(Math.max(1, page), totalPages);
            const start = (safePage - 1) * perPage;
            const end = start + perPage;
            const words = list.slice(start, end);

            state.currentPage = safePage;
            state.totalPages = totalPages;
            state.words = words;
            updatePagination();
            attachPageNumberListeners();
            renderWords(words);
            showToast('Loaded offline word list (no backend). Set a backend URL for translations/examples.', 'success');
            // Also update stats
            loadStats();
            return;
        } catch (offlineErr) {
            grid.innerHTML = `<div class="loading"><p style="color: var(--danger-color);">Error loading: ${error instanceof Error ? error.message : 'Unknown error'}</p></div>`;
        }
    } finally {
        state.isLoading = false;
    }
}

// Render Words
function renderWords(words: Word[]): void {
    const grid = document.getElementById('wordsGrid');
    if (!grid) return;
    
    grid.innerHTML = words.map(word => createWordCard(word)).join('');
}

// Create Word Card
function createWordCard(word: Word): string {
    const hasDetails = !!(word.definition || word.word_type || word.examples);
    
    return `
        <div class="word-card" onclick="flipCard(this)">
            <div class="word-front">
                <div class="word-english">${escapeHtml(word.word)}</div>
                ${word.pronunciation ? `<div class="word-pronunciation">${escapeHtml(word.pronunciation)}</div>` : ''}
            </div>
            <div class="word-back">
                <div class="word-translation">${escapeHtml(word.translation || (isOfflineMode() ? 'Translation not loaded' : 'No translation'))}</div>
                ${!word.translation ? `<button class="btn btn-primary btn-translate" data-word="${escapeHtml(word.word)}" onclick="event.stopPropagation(); window.__translateWord?.('${escapeHtml(word.word)}');">Translate</button>` : ''}
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

async function translateViaLibre(word: string, target: string): Promise<string> {
    const cacheKey = `tr:${target}:${word.toLowerCase()}`;
    try {
        const cached = localStorage.getItem(cacheKey);
        if (cached) return cached;
    } catch { /* noop */ }

    const res = await fetch('https://libretranslate.de/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ q: word, source: 'en', target, format: 'text' })
    });
    if (!res.ok) throw new Error(`Translate failed (${res.status})`);
    const data = await res.json() as { translatedText?: string };
    const text = (data.translatedText || '').trim();
    if (!text) throw new Error('Empty translation');
    try { localStorage.setItem(cacheKey, text); } catch { /* noop */ }
    return text;
}

async function enrichFromDictionary(word: string): Promise<Partial<Word>> {
    // Free dictionary API for definition/examples (usage)
    const res = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word)}`);
    if (!res.ok) return {};
    const data = await res.json() as any[];
    const entry = data?.[0];
    const meaning = entry?.meanings?.[0];
    const def = meaning?.definitions?.[0];
    const examples: string[] = [];
    for (const d of (meaning?.definitions || []).slice(0, 3)) {
        if (d?.example) examples.push(String(d.example));
    }
    return {
        pronunciation: entry?.phonetics?.[0]?.text || '',
        word_type: meaning?.partOfSpeech || '',
        definition: def?.definition || '',
        examples: examples.slice(0, 2),
    };
}

// Expose a global helper used by the inline onclick in the card template.
(window as any).__translateWord = async (w: string) => {
    try {
        const target = state.selectedLanguage || 'en';
        if (target === 'en') {
            showToast('Select a target language first.', 'error');
            return;
        }
        const translated = await translateViaLibre(w, target);
        // Update in-memory lists
        const applyTo = (arr: Word[] | null) => {
            if (!arr) return;
            const item = arr.find(x => x.word.toLowerCase() === w.toLowerCase());
            if (item) item.translation = translated;
        };
        applyTo(state.words);
        applyTo(offlineWords);

        // Also fetch definition/examples for usage
        const extra = await enrichFromDictionary(w);
        const applyExtra = (arr: Word[] | null) => {
            if (!arr) return;
            const item = arr.find(x => x.word.toLowerCase() === w.toLowerCase());
            if (item) Object.assign(item, extra);
        };
        applyExtra(state.words);
        applyExtra(offlineWords);

        renderWords(state.words);
        loadStats();
        showToast('Translated and enriched.', 'success');
    } catch (e) {
        showToast(`Translation failed: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error');
    }
};

// Escape HTML
function escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update Pagination
function updatePagination(): void {
    const pageInfo = document.getElementById('pageInfo');
    const pageNumbers = document.getElementById('pageNumbers');
    const firstPage = document.getElementById('firstPage') as HTMLButtonElement;
    const prevPage = document.getElementById('prevPage') as HTMLButtonElement;
    const nextPage = document.getElementById('nextPage') as HTMLButtonElement;
    const lastPage = document.getElementById('lastPage') as HTMLButtonElement;
    
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
function generatePageNumbers(): string {
    const totalPages = state.totalPages;
    const currentPage = state.currentPage;
    const pages: string[] = [];
    
    if (totalPages <= 7) {
        // Show all pages if 7 or fewer
        for (let i = 1; i <= totalPages; i++) {
            pages.push(createPageButton(i, i === currentPage));
        }
    } else {
        // Show first page
        pages.push(createPageButton(1, currentPage === 1));
        
        if (currentPage <= 3) {
            // Show pages 2, 3, 4
            for (let i = 2; i <= 4; i++) {
                pages.push(createPageButton(i, i === currentPage));
            }
            pages.push(createPageButton('...', false, true));
            pages.push(createPageButton(totalPages, false));
        } else if (currentPage >= totalPages - 2) {
            // Show last pages
            pages.push(createPageButton('...', false, true));
            for (let i = totalPages - 3; i <= totalPages; i++) {
                pages.push(createPageButton(i, i === currentPage));
            }
        } else {
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
function createPageButton(page: number | string, isActive: boolean, isEllipsis: boolean = false): string {
    if (isEllipsis) {
        return `<span class="page-number ellipsis">${page}</span>`;
    }
    
    const pageNum = page as number;
    return `<button class="page-number ${isActive ? 'active' : ''}" data-page="${pageNum}">${pageNum}</button>`;
}

// Add event listeners for page number clicks
function attachPageNumberListeners(): void {
    const pageNumbers = document.getElementById('pageNumbers');
    if (pageNumbers) {
        pageNumbers.addEventListener('click', (e) => {
            const target = e.target as HTMLElement;
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
function handleSearch(): void {
    const searchInput = document.getElementById('searchInput') as HTMLInputElement;
    if (searchInput) {
        state.currentSearch = searchInput.value.trim();
        state.currentPage = 1;
        loadWords();
    }
}

// Flip Card
function flipCard(card: HTMLElement): void {
    card.classList.toggle('flipped');
}

// Make flipCard available globally
(window as any).flipCard = flipCard;

// Handle Download
async function handleDownload(): Promise<void> {
    const btn = document.getElementById('downloadBtn') as HTMLButtonElement;
    if (!btn) return;
    if (!hasBackendConfigured()) {
        showToast('Offline mode: connect a backend URL to download/translate the dataset.', 'error');
        return;
    }
    
    const originalText = btn.innerHTML;
    const includeDetails = (document.getElementById('includeDetails') as HTMLInputElement)?.checked ?? true;
    
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
        } else {
            showToast(data.error || 'Download error', 'error');
        }
    } catch (error) {
        showToast('Server connection error', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Handle Create Anki
async function handleCreateAnki(): Promise<void> {
    const btn = document.getElementById('createAnkiBtn') as HTMLButtonElement;
    if (!btn) return;
    if (!hasBackendConfigured()) {
        showToast('Offline mode: connect a backend URL to create Anki decks.', 'error');
        return;
    }
    
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
        } else {
            showToast(data.error || 'Error creating Anki deck', 'error');
        }
    } catch (error) {
        showToast('Server connection error', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Load Daily Words
async function loadDailyWords(): Promise<void> {
    const container = document.getElementById('dailyWords');
    if (!container) return;
    if (!hasBackendConfigured()) {
        container.innerHTML = `<p style="color: var(--text-secondary);">Offline mode: connect a backend URL to use Daily Review.</p>`;
        return;
    }
    
    const countInput = document.getElementById('dailyCount') as HTMLInputElement;
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
            ${data.words.map((word: Word) => createWordCard(word)).join('')}
        `;
        
    } catch (error) {
        container.innerHTML = `<p style="color: var(--danger-color);">Error: ${error instanceof Error ? error.message : 'Unknown error'}</p>`;
    }
}

// Show Toast
function showToast(message: string, type: 'success' | 'error' = 'success'): void {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
