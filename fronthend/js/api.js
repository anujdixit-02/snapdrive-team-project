const API_BASE = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
    ? 'http://127.0.0.1:8000'
    : window.location.origin;

/**
 * Robust Toast notification system
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `btn btn-outline`;
    toast.style.cssText = `
        margin-top: 10px; 
        animation: fadeInUp 0.3s forwards; 
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); 
        background: var(--bg-card); 
        color: var(--text-main);
        border-left: 4px solid ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--primary)'};
        pointer-events: auto;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    `;
    
    let icon = '';
    if (type === 'success') icon = '<svg width="20" height="20" fill="none" stroke="var(--success)" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
    else if (type === 'error') icon = '<svg width="20" height="20" fill="none" stroke="var(--error)" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
    else icon = '<svg width="20" height="20" fill="none" stroke="var(--primary)" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';

    toast.innerHTML = `${icon}<span style="font-size: 14px; font-weight: 600;">${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

/**
 * Handle Auth Headers
 */
function getAuthHeader() {
    const tokenData = localStorage.getItem('token');
    if (!tokenData) return {};
    return { "Authorization": `Bearer ${tokenData}` };
}

/**
 * Get current User ID
 */
function getUserId() {
    let userId = localStorage.getItem('userId');
    if (userId) return parseInt(userId);
    return null;
}

/**
 * THEME MANAGEMENT
 */
function initTheme() {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcons(theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcons(newTheme);
}

function updateThemeIcons(theme) {
    const btn = document.getElementById('themeToggle');
    if (!btn) return;
    
    if (theme === 'dark') {
        btn.innerHTML = '<svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 9H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z"></path></svg>';
        btn.title = "Switch to Light Mode";
    } else {
        btn.innerHTML = '<svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path></svg>';
        btn.title = "Switch to Dark Mode";
    }
}

// Auto-init on load
document.addEventListener('DOMContentLoaded', initTheme);

/**
 * Global Loader Controls
 */
function showLoader(title = "Loading...", message = "Please wait") {
    const loader = document.getElementById('globalLoader');
    const titleEl = document.getElementById('globalLoaderTitle');
    const msgEl = document.getElementById('globalLoaderMessage');
    
    if (loader) {
        loader.style.display = 'flex';
        if (titleEl) titleEl.innerText = title;
        if (msgEl) msgEl.innerText = message;
    }
}

function updateLoader(title, message) {
    const titleEl = document.getElementById('globalLoaderTitle');
    const msgEl = document.getElementById('globalLoaderMessage');
    
    if (titleEl && title !== undefined) titleEl.innerText = title;
    if (msgEl && message !== undefined) msgEl.innerText = message;
}

function hideLoader() {
    const loader = document.getElementById('globalLoader');
    if (loader) {
        loader.style.display = 'none';
    }
}
 