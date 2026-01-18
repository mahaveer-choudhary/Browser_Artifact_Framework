let currentData = {
    logins: [],
    cookies: [],
    history: []
};

let currentBrowser = 'chrome';

document.addEventListener('DOMContentLoaded', () => {
    // Add animation classes
    addLoadAnimations();
    // Load existing data for chrome first
    loadBrowser(currentBrowser);
});

function addLoadAnimations() {
    const cards = document.querySelectorAll('.stat-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
}

function loadBrowser(browser) {
    currentBrowser = browser;

    // Update UI with smooth transition
    document.querySelectorAll('.nav-btn').forEach(b => {
        b.classList.remove('active');
        b.style.transform = '';
    });

    const activeBtn = document.querySelector(`.nav-btn[data-browser="${browser}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    const title = document.getElementById('currentBrowserTitle');
    title.style.opacity = '0';
    title.style.transform = 'translateY(-10px)';

    setTimeout(() => {
        title.textContent = `${browser.charAt(0).toUpperCase() + browser.slice(1)} Data`;
        title.style.opacity = '1';
        title.style.transform = 'translateY(0)';
    }, 150);

    updateStatus('Loading...', 'loading');

    // Fetch Data
    fetch(`/api/data/secrets_${browser}.json`)
        .then(response => {
            if (!response.ok) throw new Error('No data found');
            return response.json();
        })
        .then(data => {
            updateStatus('Loaded', 'success');
            processData(data, browser);
        })
        .catch(err => {
            console.log(err);
            updateStatus('No Data Found (Run Extraction)', 'error');
            currentData = { logins: [], cookies: [], history: [] };
            updateStats();
            renderTables();
        });
}

function updateStatus(message, type = 'success') {
    const statusBar = document.getElementById('statusBar');
    statusBar.textContent = message;
    statusBar.className = 'status-bar';
    if (type === 'error') {
        statusBar.classList.add('error');
    }
}

function extractCurrentBrowser() {
    const btn = document.getElementById('extractBtn');
    if (btn.classList.contains('loading')) return;

    btn.classList.add('loading');
    btn.innerHTML = '<i class="fa-solid fa-spinner"></i> RUNNING...';
    updateStatus('Extracting... (Check Terminal)', 'loading');

    fetch(`/api/extract/${currentBrowser}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            btn.classList.remove('loading');
            btn.innerHTML = '<i class="fa-solid fa-bolt"></i> RUN EXTRACTION';

            if (data.status === 'success') {
                // Check for warnings in the log even on success
                if (data.log && (data.log.includes("CRITICAL WARNING") || data.log.includes("App-Bound key missing"))) {
                    updateStatus('Extraction Completed with Warnings', 'error');
                    alert("WARNING: App-Bound Key was NOT found!\n\nThis means passwords will still be encrypted.\n\nMake sure to run the dashboard as Administrator and kill all browser processes.");
                } else {
                    updateStatus('Extraction Complete', 'success');
                }
                loadBrowser(currentBrowser);
            } else {
                updateStatus('Extraction Failed', 'error');
                showNotification('Error: ' + data.log, 'error');
            }
        })
        .catch(err => {
            btn.classList.remove('loading');
            btn.innerHTML = '<i class="fa-solid fa-bolt"></i> RUN EXTRACTION';
            showNotification('Request Failed', 'error');
        });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fa-solid ${type === 'error' ? 'fa-circle-xmark' : 'fa-circle-check'}"></i>
        <span>${message}</span>
    `;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'error' ? 'rgba(248, 113, 113, 0.1)' : 'rgba(0, 255, 157, 0.1)'};
        border: 1px solid ${type === 'error' ? 'rgba(248, 113, 113, 0.3)' : 'rgba(0, 255, 157, 0.3)'};
        border-radius: 12px;
        color: ${type === 'error' ? '#f87171' : '#00ff9d'};
        font-family: var(--font-mono);
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        backdrop-filter: blur(10px);
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Add notification animations
const style = document.createElement('style');
style.innerHTML = `
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(100px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideOut {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(100px); }
    }
`;
document.head.appendChild(style);

function processData(data, browserKey) {
    const root = data[browserKey] || {};

    currentData.logins = root.logins || [];
    currentData.cookies = root.cookies || [];
    currentData.history = root.history || [];

    updateStats();
    renderTables();
}

function updateStats() {
    animateCounter('countLogins', currentData.logins.length);
    animateCounter('countCookies', currentData.cookies.length);
    animateCounter('countHistory', currentData.history.length);
}

function animateCounter(elementId, targetValue) {
    const element = document.getElementById(elementId);
    const startValue = parseInt(element.textContent) || 0;
    const duration = 500;
    const startTime = performance.now();

    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = Math.round(startValue + (targetValue - startValue) * easeOutQuart);

        element.textContent = currentValue.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }

    requestAnimationFrame(updateCounter);
}

function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.closest('.tab-btn').classList.add('active');

    // Switch views with animation
    document.querySelectorAll('.data-view').forEach(view => {
        view.classList.remove('active');
        view.style.display = 'none';
    });

    const targetView = document.getElementById(`view-${tab}`);
    targetView.style.display = 'block';
    targetView.style.opacity = '0';
    targetView.style.transform = 'translateY(10px)';

    requestAnimationFrame(() => {
        targetView.classList.add('active');
        targetView.style.opacity = '1';
        targetView.style.transform = 'translateY(0)';
        targetView.style.transition = 'all 0.3s ease';
    });
}

function renderTables() {
    renderLogins(currentData.logins);
    renderCookies(currentData.cookies);
    renderHistory(currentData.history);
}

function renderLogins(data) {
    const tbody = document.getElementById('tbody-logins');
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="empty-state">
                    <i class="fa-solid fa-key"></i>
                    <p>No login data found. Run extraction to fetch data.</p>
                </td>
            </tr>
        `;
        return;
    }

    data.slice(0, 500).forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.style.animation = `fadeIn 0.3s ease ${index * 0.02}s forwards`;
        tr.style.opacity = '0';
        tr.innerHTML = `
            <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                    ${item.origin || item.hostname}
                    <a href="${item.origin || 'https://' + item.hostname}" target="_blank" rel="noopener" 
                       style="color: var(--text-dim); transition: color 0.2s;">
                        <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.75rem;"></i>
                    </a>
                </div>
            </td>
            <td>${escapeHtml(item.username)}</td>
            <td class="password-cell" onclick="togglePassword(this)">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="blur">${escapeHtml(item.password)}</span>
                    <button onclick="copyToClipboard('${escapeHtml(item.password)}', event)" 
                            style="background: none; border: none; color: var(--text-dim); cursor: pointer; padding: 4px;"
                            title="Copy password">
                        <i class="fa-regular fa-copy"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderCookies(data) {
    const tbody = document.getElementById('tbody-cookies');
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="empty-state">
                    <i class="fa-solid fa-cookie-bite"></i>
                    <p>No cookies found. Run extraction to fetch data.</p>
                </td>
            </tr>
        `;
        return;
    }

    data.slice(0, 200).forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.style.animation = `fadeIn 0.3s ease ${index * 0.02}s forwards`;
        tr.style.opacity = '0';
        tr.innerHTML = `
            <td>${escapeHtml(item.host)}</td>
            <td style="font-weight: 500;">${escapeHtml(item.name)}</td>
            <td style="color: var(--text-dim); font-family: var(--font-mono); font-size: 0.8rem;">
                ${escapeHtml(item.value?.substring(0, 60) || '')}${item.value?.length > 60 ? '...' : ''}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderHistory(data) {
    const tbody = document.getElementById('tbody-history');
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="empty-state">
                    <i class="fa-solid fa-clock-rotate-left"></i>
                    <p>No history found. Run extraction to fetch data.</p>
                </td>
            </tr>
        `;
        return;
    }

    data.slice(0, 200).forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.style.animation = `fadeIn 0.3s ease ${index * 0.02}s forwards`;
        tr.style.opacity = '0';
        tr.innerHTML = `
            <td>
                <div style="display: flex; align-items: center; gap: 8px; max-width: 400px;">
                    <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${escapeHtml(item.url)}
                    </span>
                    <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener" 
                       style="color: var(--text-dim); transition: color 0.2s; flex-shrink: 0;">
                        <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.75rem;"></i>
                    </a>
                </div>
            </td>
            <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                ${escapeHtml(item.title?.substring(0, 60) || '')}
            </td>
            <td style="font-family: var(--font-mono); color: var(--accent-secondary);">
                ${item.visit_count}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function togglePassword(cell) {
    cell.classList.toggle('reveal');
}

function copyToClipboard(text, event) {
    event.stopPropagation();
    navigator.clipboard.writeText(text).then(() => {
        const icon = event.target.closest('button').querySelector('i');
        icon.className = 'fa-solid fa-check';
        icon.style.color = 'var(--accent-primary)';

        setTimeout(() => {
            icon.className = 'fa-regular fa-copy';
            icon.style.color = '';
        }, 2000);
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function filterTable() {
    const query = document.getElementById('searchInput').value.toLowerCase();

    const activeData = {
        logins: currentData.logins.filter(i =>
            (i.origin || i.hostname || '').toLowerCase().includes(query) ||
            (i.username || '').toLowerCase().includes(query)
        ),
        cookies: currentData.cookies.filter(i =>
            (i.host || '').toLowerCase().includes(query) ||
            (i.name || '').toLowerCase().includes(query)
        ),
        history: currentData.history.filter(i =>
            ((i.url || '') + (i.title || '')).toLowerCase().includes(query)
        )
    };

    renderLogins(activeData.logins);
    renderCookies(activeData.cookies);
    renderHistory(activeData.history);
}

// Debounce search for better performance
let searchTimeout;
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(filterTable, 200);
        });
    }
});
