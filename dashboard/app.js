let currentData = {
    logins: [],
    cookies: [],
    history: [],
    intelligence: null
};

let currentBrowser = 'chrome';

document.addEventListener('DOMContentLoaded', () => {
    // Add animation classes
    addLoadAnimations();
    // Load existing data for chrome first
    loadBrowser(currentBrowser);

    // Keyboard shortcut for search
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('searchInput').focus();
        }
    });
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
            currentData = { logins: [], cookies: [], history: [], intelligence: null };
            updateStats();
            renderTables();
        });
}

function updateStatus(message, type = 'success') {
    const statusBar = document.getElementById('statusBar');
    const statusText = statusBar.querySelector('.status-text');
    if (statusText) {
        statusText.textContent = message;
    } else {
        statusBar.textContent = message;
    }
    statusBar.className = 'status-bar';
    if (type === 'error') {
        statusBar.classList.add('error');
    }
}

function extractCurrentBrowser() {
    const btn = document.getElementById('extractBtn');
    if (btn.classList.contains('loading')) return;

    btn.classList.add('loading');
    btn.innerHTML = '<i class="fa-solid fa-spinner"></i> <span>RUNNING...</span>';
    updateStatus('Extracting... (Check Terminal)', 'loading');

    fetch(`/api/extract/${currentBrowser}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            btn.classList.remove('loading');
            btn.innerHTML = '<div class="btn-glow"></div><i class="fa-solid fa-bolt"></i> <span>RUN EXTRACTION</span>';

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
            btn.innerHTML = '<div class="btn-glow"></div><i class="fa-solid fa-bolt"></i> <span>RUN EXTRACTION</span>';
            showNotification('Request Failed', 'error');
        });
}


// -- Export Logic --

function openExportModal() {
    const modal = document.getElementById('exportModal');
    modal.style.display = 'block';
    setTimeout(() => modal.classList.add('show'), 10);
}

function closeExportModal() {
    const modal = document.getElementById('exportModal');
    modal.classList.remove('show');
    setTimeout(() => modal.style.display = 'none', 300);
}

function exportReport() {
    openExportModal();
}

function confirmExport() {
    const btn = document.querySelector('.btn-confirm');
    if (btn.classList.contains('loading')) return;

    // Get selected browsers
    const selectedBrowsers = Array.from(document.querySelectorAll('.browser-opt:checked')).map(cb => cb.value);

    // Get options
    const options = {
        browsers: selectedBrowsers,
        logins: document.getElementById('opt-logins').checked,
        cookies: document.getElementById('opt-cookies').checked,
        history: document.getElementById('opt-history').checked,
        top10: document.getElementById('opt-top10').checked
    };

    if (selectedBrowsers.length === 0) {
        showNotification('Please select at least one browser!', 'error');
        return;
    }

    btn.classList.add('loading');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Generating...</span>';

    // Original export btn state update for consistency
    const mainBtn = document.getElementById('exportBtn');
    if (mainBtn) {
        mainBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>GENERATING...</span>';
    }

    fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(options)
    })
        .then(res => res.json())
        .then(data => {
            btn.classList.remove('loading');
            btn.innerHTML = '<i class="fa-solid fa-download"></i> <span>Export & Download</span>';

            if (mainBtn) {
                mainBtn.innerHTML = '<i class="fa-solid fa-file-export"></i> <span>EXPORT REPORT</span>';
            }

            closeExportModal();

            if (data.status === 'success') {
                updateStatus('Report Generated', 'success');
                showNotification('Report Generated: ' + data.file, 'success');

                // Auto Download
                const link = document.createElement('a');
                link.href = '/reports/' + data.file;
                link.download = data.file; // Trigger download attribute
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

            } else {
                updateStatus('Export Failed', 'error');
                showNotification('Error: ' + data.log, 'error');
            }
        })
        .catch(err => {
            btn.classList.remove('loading');
            btn.innerHTML = '<i class="fa-solid fa-download"></i> <span>Export & Download</span>';
            if (mainBtn) {
                mainBtn.innerHTML = '<i class="fa-solid fa-file-export"></i> <span>EXPORT REPORT</span>';
            }
            showNotification('Request Failed', 'error');
        });
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(n => n.remove());

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fa-solid ${type === 'error' ? 'fa-circle-xmark' : 'fa-circle-check'}"></i>
        </div>
        <span class="notification-text">${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;
    notification.style.cssText = `
        position: fixed;
        top: 24px;
        right: 24px;
        padding: 16px 20px;
        background: ${type === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(0, 255, 157, 0.1)'};
        border: 1px solid ${type === 'error' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(0, 255, 157, 0.3)'};
        border-radius: 12px;
        color: ${type === 'error' ? '#ef4444' : '#00ff9d'};
        font-family: var(--font-mono);
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 14px;
        z-index: 3000;
        animation: slideIn 0.3s ease;
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        max-width: 400px;
    `;

    document.body.appendChild(notification);

    // Style close button
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: inherit;
        cursor: pointer;
        opacity: 0.6;
        padding: 4px;
        margin-left: auto;
        transition: opacity 0.2s;
    `;
    closeBtn.addEventListener('mouseenter', () => closeBtn.style.opacity = '1');
    closeBtn.addEventListener('mouseleave', () => closeBtn.style.opacity = '0.6');

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
    currentData.intelligence = root.intelligence || null;

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
    const startValue = parseInt(element.textContent.replace(/,/g, '')) || 0;
    const duration = 600;
    const startTime = performance.now();

    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function - ease out quart
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
    renderIntelligence(currentData.intelligence);
}

function renderIntelligence(intel) {
    const container = document.getElementById('intel-content');
    if (!intel) {
        container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-brain"></i><p>No intelligence data found for this browser.</p></div>';
        return;
    }
    
    let html = '';
    
    // Cloud Tokens
    html += '<h3 style="margin-top: 0;"><i class="fa-solid fa-cloud"></i> Cloud Sync Tokens</h3>';
    if (intel.cloud_tokens && intel.cloud_tokens.length > 0) {
        html += '<table class="cyber-table"><tr><th>Service</th><th>Token Name</th><th>Value</th></tr>';
        intel.cloud_tokens.forEach(t => {
            html += `<tr><td style="color:var(--accent-cyan);">${escapeHtml(t.service)}</td><td style="font-weight:bold;">${escapeHtml(t.token_name)}</td><td style="font-family:monospace; color:var(--accent-amber);">${escapeHtml(t.token_value)}</td></tr>`;
        });
        html += '</table>';
    } else {
         html += '<p style="color: var(--text-dim); font-size: 0.9em; margin-bottom: 30px;">No active cloud sync tokens found in cookies.</p>';
    }
    
    // Extensions
    html += '<h3><i class="fa-solid fa-puzzle-piece"></i> Browser Extensions</h3>';
    if (intel.extensions && intel.extensions.length > 0) {
        html += '<table class="cyber-table"><tr><th>Name</th><th>Version</th><th>Suspicious?</th><th>Flags</th></tr>';
        intel.extensions.forEach(e => {
            const isSus = e.suspicious ? '<span style="color: #ef4444; font-weight: bold; padding: 2px 6px; background: rgba(239, 68, 68, 0.1); border-radius: 4px;">YES</span>' : '<span style="color: var(--text-dim);">No</span>';
            const flags = e.flagged_permissions.join(', ') || '-';
            html += `<tr><td>${escapeHtml(e.name)}</td><td>${escapeHtml(e.version)}</td><td>${isSus}</td><td style="color:var(--accent-amber); font-family: monospace; font-size: 0.85em;">${escapeHtml(flags)}</td></tr>`;
        });
        html += '</table>';
    } else {
         html += '<p style="color: var(--text-dim); font-size: 0.9em; margin-bottom: 30px;">No extensions successfully analyzed or found.</p>';
    }
    
    // IOCs
    html += '<h3><i class="fa-solid fa-shield-halved"></i> Threat Intelligence (IOCs)</h3>';
    if (intel.iocs && intel.iocs.length > 0) {
        html += '<table class="cyber-table"><tr><th>Threat</th><th>URL</th><th>Timestamp</th></tr>';
        intel.iocs.forEach(i => {
           html += `<tr><td style="color: #ef4444; font-weight: bold;">${escapeHtml(i.threat)}</td><td style="font-family: monospace;">${escapeHtml(i.url)}</td><td>${escapeHtml(i.timestamp)}</td></tr>`;
        });
        html += '</table>';
    } else {
         html += '<p style="color: var(--text-dim); font-size: 0.9em; margin-bottom: 30px;">No known malicious domains detected in browsing history.</p>';
    }
    
    // Deleted History
    html += '<h3><i class="fa-solid fa-dumpster-fire"></i> Deleted History Carving</h3>';
    if (intel.deleted_history && intel.deleted_history.length > 0) {
        html += '<p style="color: var(--accent-amber); font-size: 0.9em; margin-bottom: 10px;">Found <strong>' + intel.deleted_history.length + '</strong> potentially deleted URLs carved from SQLite unallocated space.</p>';
        html += '<div style="max-height: 250px; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 6px; font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary); border: 1px solid var(--border-subtle);">';
        intel.deleted_history.slice(0, 500).forEach(u => {
            html += `<div style="padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">${escapeHtml(u)}</div>`;
        });
        if (intel.deleted_history.length > 500) html += `<div>...and ${intel.deleted_history.length - 500} more</div>`;
        html += '</div>';
    } else {
         html += '<p style="color: var(--text-dim); font-size: 0.9em;">No deleted URLs carved from history database.</p>';
    }
    
    container.innerHTML = html;
}

function renderLogins(data) {
    const tbody = document.getElementById('tbody-logins');
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="empty-state">
                    <i class="fa-solid fa-key"></i>
                    <p>No login data found.<br>Run extraction to fetch data.</p>
                </td>
            </tr>
        `;
        return;
    }

    data.slice(0, 500).forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${item.origin || item.hostname}
                    </span>
                    <a href="${item.origin || 'https://' + item.hostname}" target="_blank" rel="noopener" 
                       style="color: var(--text-dim); transition: all 0.2s; padding: 4px;"
                       onmouseenter="this.style.color='var(--accent-cyan)'"
                       onmouseleave="this.style.color='var(--text-dim)'">
                        <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.7rem;"></i>
                    </a>
                </div>
            </td>
            <td style="color: var(--text-secondary); font-family: var(--font-mono); font-size: 0.85rem;">
                ${escapeHtml(item.username)}
            </td>
            <td class="password-cell" onclick="togglePassword(this)">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span class="blur" style="color: var(--accent-amber);">${escapeHtml(item.password)}</span>
                    <button onclick="copyToClipboard('${escapeHtml(item.password).replace(/'/g, "\\'")}', event)" 
                            style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); color: var(--text-dim); cursor: pointer; padding: 6px 8px; border-radius: 6px; transition: all 0.2s;"
                            onmouseenter="this.style.borderColor='var(--accent-cyan)'; this.style.color='var(--accent-cyan)'"
                            onmouseleave="this.style.borderColor='var(--border-subtle)'; this.style.color='var(--text-dim)'"
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
                    <p>No cookies found.<br>Run extraction to fetch data.</p>
                </td>
            </tr>
        `;
        return;
    }

    data.slice(0, 200).forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${escapeHtml(item.host)}</td>
            <td style="font-weight: 500; color: var(--accent-secondary); font-family: var(--font-mono);">
                ${escapeHtml(item.name)}
            </td>
            <td style="color: var(--text-tertiary); font-family: var(--font-mono); font-size: 0.8rem; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                ${escapeHtml(item.value?.substring(0, 80) || '')}${item.value?.length > 80 ? '...' : ''}
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
                <td colspan="4" class="empty-state">
                    <i class="fa-solid fa-clock-rotate-left"></i>
                    <p>No history found.<br>Run extraction to fetch data.</p>
                </td>
            </tr>
        `;
        return;
    }

    data.slice(0, 200).forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div style="display: flex; align-items: center; gap: 10px; max-width: 350px;">
                    <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${escapeHtml(item.url)}
                    </span>
                    <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener" 
                       style="color: var(--text-dim); transition: all 0.2s; flex-shrink: 0; padding: 4px;"
                       onmouseenter="this.style.color='var(--accent-cyan)'"
                       onmouseleave="this.style.color='var(--text-dim)'">
                        <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.7rem;"></i>
                    </a>
                </div>
            </td>
            <td style="max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-secondary);">
                ${escapeHtml(item.title?.substring(0, 50) || '-')}${(item.title?.length || 0) > 50 ? '...' : ''}
            </td>
            <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-tertiary);">
                ${item.last_visit_time || '-'}
            </td>
            <td>
                <span style="font-family: var(--font-mono); color: var(--accent-blue); background: rgba(59, 130, 246, 0.12); padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                    ${item.visit_count}
                </span>
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
        const btn = event.target.closest('button');
        const icon = btn.querySelector('i');
        icon.className = 'fa-solid fa-check';
        btn.style.borderColor = 'var(--accent-green)';
        btn.style.color = 'var(--accent-green)';
        btn.style.background = 'var(--accent-green-glow)';

        setTimeout(() => {
            icon.className = 'fa-regular fa-copy';
            btn.style.borderColor = 'var(--border-subtle)';
            btn.style.color = 'var(--text-dim)';
            btn.style.background = 'rgba(255,255,255,0.03)';
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
    // Apply sort before rendering history
    sortHistory(activeData.history);
}

function sortHistory(dataOverride = null) {
    let data = dataOverride || currentData.history;
    const sortType = document.getElementById('historySort').value;

    // Create a copy to sort
    let sorted = [...data];

    if (sortType === 'visits') {
        // Most Visited (Descending)
        sorted.sort((a, b) => (b.visit_count || 0) - (a.visit_count || 0));
    } else if (sortType === 'recent') {
        // Recently Visited (Descending time)
        sorted.sort((a, b) => {
            const tA = a.last_visit_time || '';
            const tB = b.last_visit_time || '';
            return tB.localeCompare(tA);
        });
    }
    // Default: extraction order (no sort needed)

    renderHistory(sorted);
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

function fetchSystemArtifacts() {
    const container = document.getElementById('system-content');
    container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-spinner fa-spin" style="font-size: 2rem;"></i><p>Loading System OS Artifacts...</p></div>';
    
    fetch('/api/system_artifacts')
        .then(res => res.json())
        .then(data => {
            renderSystemArtifacts(data);
        })
        .catch(err => {
            container.innerHTML = '<div class="empty-state" style="color:#ef4444;"><i class="fa-solid fa-bug"></i><p>Error loading system artifacts.</p></div>';
            console.error(err);
        });
}

function renderSystemArtifacts(data) {
    const container = document.getElementById('system-content');
    if (!data || Object.keys(data).length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-laptop"></i><p>No system artifacts extracted yet. Run a browser extraction first to trigger OS data collection.</p></div>';
        return;
    }
    
    let html = '';
    
    // Wi-Fi
    html += '<h3 style="margin-top: 0; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);"><i class="fa-solid fa-wifi"></i> Wi-Fi Profiles & Passwords</h3>';
    if (data.wifi_profiles && data.wifi_profiles.length > 0) {
        html += '<table class="cyber-table"><tr><th>SSID (Network Name)</th><th>Password (Cleartext)</th></tr>';
        data.wifi_profiles.forEach(w => {
            html += `<tr><td style="color:var(--accent-cyan); font-weight:bold;">${escapeHtml(w.ssid)}</td><td style="font-family:monospace; color:var(--accent-amber);">${escapeHtml(w.password)}</td></tr>`;
        });
        html += '</table>';
    } else {
         html += '<p style="color: var(--text-dim); font-size: 0.9em; margin-bottom: 30px;">No Wi-Fi profiles found.</p>';
    }
    
    // USB
    html += '<h3 style="margin-top: 30px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);"><i class="fa-brands fa-usb"></i> USB Device History</h3>';
    if (data.usb_history && data.usb_history.length > 0) {
        html += '<table class="cyber-table"><tr><th>Device Name</th><th>Class</th><th>Serial / Device ID</th></tr>';
        data.usb_history.forEach(u => {
            html += `<tr><td style="color:var(--text-primary); font-weight:bold;">${escapeHtml(u.name)}</td><td>${escapeHtml(u.class)}</td><td style="font-family:monospace; font-size: 0.85em; color:var(--text-dim);">${escapeHtml(u.serial_number)}</td></tr>`;
        });
        html += '</table>';
    } else {
         html += '<p style="color: var(--text-dim); font-size: 0.9em; margin-bottom: 30px;">No USB history found.</p>';
    }
    
    // BAM
    html += '<h3 style="margin-top: 30px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);"><i class="fa-solid fa-terminal"></i> Application Execution History (BAM)</h3>';
    if (data.bam_execution_history && data.bam_execution_history.length > 0) {
        html += '<p style="color: var(--accent-amber); font-size: 0.9em; margin-bottom: 10px;">Found <strong>' + data.bam_execution_history.length + '</strong> recently executed programs across user profiles.</p>';
        html += '<div style="max-height: 400px; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 6px; font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary); border: 1px solid var(--border-subtle);">';
        data.bam_execution_history.forEach(b => {
            html += `<div style="padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);"><span style="color:var(--text-dim);">[User: ${escapeHtml(b.user_sid)}]</span> - <span style="color:var(--text-primary);">${escapeHtml(b.executable)}</span></div>`;
        });
        html += '</div>';
    } else {
         html += '<p style="color: var(--text-dim); font-size: 0.9em;">No BAM execution history found.</p>';
    }
    
    // Anti-Forensics
    html += '<h3 style="margin-top: 30px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);"><i class="fa-solid fa-user-shield"></i> Anti-Forensics & Privacy Tools</h3>';
    if (data.anti_forensics && data.anti_forensics.length > 0) {
        html += '<table class="cyber-table"><tr><th>Category</th><th>Name</th><th>Location / Path</th></tr>';
        data.anti_forensics.forEach(a => {
            html += `<tr><td style="color:var(--accent-pink); font-weight:bold;">${escapeHtml(a.category)}</td><td style="color:var(--text-primary);">${escapeHtml(a.name)}</td><td style="font-family:monospace; font-size: 0.85em; color:var(--text-dim);">${escapeHtml(a.path)}</td></tr>`;
        });
        html += '</table>';
    } else {
         html += '<p style="color: var(--text-dim); font-size: 0.9em; margin-bottom: 30px;">No suspicious anti-forensics tools or configurations found.</p>';
    }
    
    container.innerHTML = html;
}

// Ensure init checks if there's any system artifacts on load
window.addEventListener('DOMContentLoaded', () => {
    // Optionally auto-fetch system artifacts if available
    // fetchSystemArtifacts();
});

function openEdiscoveryModal() {
    const modal = document.getElementById('ediscoveryModal');
    modal.style.display = 'block';
    setTimeout(() => modal.classList.add('show'), 10);
    setTimeout(() => document.getElementById('ediscoveryInput').focus(), 100);
}

function closeEdiscoveryModal() {
    const modal = document.getElementById('ediscoveryModal');
    modal.classList.remove('show');
    setTimeout(() => modal.style.display = 'none', 300);
}

function runEdiscovery() {
    const keyword = document.getElementById('ediscoveryInput').value.trim();
    if (!keyword) {
        showNotification('Please enter a keyword', 'error');
        return;
    }
    
    const resultsContainer = document.getElementById('ediscoveryResults');
    resultsContainer.innerHTML = '<div style="padding:30px; text-align:center;"><i class="fa-solid fa-spinner fa-spin" style="font-size: 2rem; color: var(--accent-cyan);"></i><p style="margin-top:10px; color: var(--text-dim);">Scanning all artifacts...</p></div>';
    
    fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword: keyword })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            renderEdiscoveryResults(data.results, keyword);
        } else {
            resultsContainer.innerHTML = `<div style="padding:30px; text-align:center; color: #ef4444;"><i class="fa-solid fa-triangle-exclamation" style="font-size:2rem;"></i><p>Error: ${data.message}</p></div>`;
        }
    })
    .catch(err => {
        resultsContainer.innerHTML = `<div style="padding:30px; text-align:center; color: #ef4444;"><i class="fa-solid fa-triangle-exclamation" style="font-size:2rem;"></i><p>Network Error</p></div>`;
    });
}

function renderEdiscoveryResults(results, keyword) {
    const container = document.getElementById('ediscoveryResults');
    container.innerHTML = '';
    
    const highlight = (text) => {
        if (!text) return '';
        const regex = new RegExp(`(${keyword})`, 'gi');
        return escapeHtml(text).replace(regex, '<span style="background: var(--accent-amber); color: #000; font-weight: bold; padding: 0 2px; border-radius: 2px;">$1</span>');
    };
    
    let html = '<table class="cyber-table" style="font-size: 0.85rem;">';
    html += '<thead><tr><th style="width: 15%;">Browser</th><th style="width: 15%;">Type</th><th>Details</th></tr></thead><tbody>';
    
    let total = 0;
    
    // Logins
    results.logins.forEach(item => {
        total++;
        html += `<tr>
            <td><i class="fa-brands fa-${item.browserSource}" style="color: var(--text-dim); margin-right:5px;"></i> ${item.browserSource}</td>
            <td style="color: var(--accent-cyan);"><i class="fa-solid fa-key"></i> Login</td>
            <td style="font-family: var(--font-mono);">
                Target: ${highlight(item.origin || item.hostname)}<br>
                User: ${highlight(item.username)}<br>
                Pass: <span class="blur" style="color: var(--accent-amber);" onclick="this.classList.toggle('reveal')">${highlight(item.password)}</span>
            </td>
        </tr>`;
    });
    
    // Cookies
    results.cookies.forEach(item => {
        total++;
        html += `<tr>
            <td><i class="fa-brands fa-${item.browserSource}" style="color: var(--text-dim); margin-right:5px;"></i> ${item.browserSource}</td>
            <td style="color: var(--accent-secondary);"><i class="fa-solid fa-cookie-bite"></i> Cookie</td>
            <td style="font-family: var(--font-mono);">
                Host: ${highlight(item.host)}<br>
                Name: ${highlight(item.name)}<br>
                Value: <span style="word-break: break-all;">${highlight((item.value || '').substring(0, 100))}${item.value?.length > 100 ? '...' : ''}</span>
            </td>
        </tr>`;
    });
    
    // History
    results.history.forEach(item => {
        total++;
        html += `<tr>
            <td><i class="fa-brands fa-${item.browserSource}" style="color: var(--text-dim); margin-right:5px;"></i> ${item.browserSource}</td>
            <td style="color: var(--text-secondary);"><i class="fa-solid fa-clock-rotate-left"></i> History</td>
            <td style="font-family: var(--font-mono);">
                URL: <a href="${item.url}" target="_blank" style="color: var(--text-dim);">${highlight(item.url)}</a><br>
                Title: ${highlight(item.title)}
            </td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    
    if (total === 0) {
        container.innerHTML = `<div style="padding:30px; text-align:center; color: var(--text-dim);"><i class="fa-solid fa-magnifying-glass" style="font-size:2rem; margin-bottom:10px;"></i><p>No matches found for "${escapeHtml(keyword)}"</p></div>`;
    } else {
        container.innerHTML = `<div style="padding: 10px 15px; border-bottom: 1px solid var(--border-subtle); color: var(--accent-cyan); font-weight: 600;">Found ${total} matches for "${escapeHtml(keyword)}"</div>` + html;
    }
}

function openExportModal() {
    const modal = document.getElementById('exportModal');
    modal.style.display = 'block';
    setTimeout(() => modal.classList.add('show'), 10);
}

function closeExportModal() {
    const modal = document.getElementById('exportModal');
    modal.classList.remove('show');
    setTimeout(() => modal.style.display = 'none', 300);
}

function confirmExport() {
    const format = document.getElementById('exportFormat').value;
    
    // Get Checked Browsers
    const browsers = [];
    document.querySelectorAll('.browser-opt:checked').forEach(c => {
        browsers.push(c.value);
    });
    
    // Options
    const logins = document.getElementById('opt-logins').checked;
    const cookies = document.getElementById('opt-cookies').checked;
    const history = document.getElementById('opt-history').checked;
    const system = document.getElementById('opt-system').checked;

    closeExportModal();
    showNotification(`Generating ${format.toUpperCase()} Report...`, 'info');
    
    fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            format: format,
            browsers: browsers,
            logins: logins,
            cookies: cookies,
            history: history,
            system: system
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Export failed');
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const ext = format === 'zip' ? 'zip' : format === 'pdf' ? 'pdf' : 'xlsx';
        a.download = `BAF_Forensic_Export.${ext}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        showNotification('Report Downloaded Successfully', 'success');
    })
    .catch(error => {
        console.error('Export error:', error);
        showNotification('Failed to generate report', 'error');
    });
}
