/* ============================================
   SNAPDRIVE - Frontend Logic (Upload, Files, Folders, Activity, Notifications)
   ============================================ */

/**
 * SVG ICON CONSTANTS
 */
const ICONS = {
    view: '<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>',
    download: '<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>',
    share: '<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/></svg>',
    delete: '<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-4v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>',
    folder: '<svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>',
    file: '<svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>',
    image: '<svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
    video: '<svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>',
    back: '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>'
};

/**
 * FOLDER STATE
 */
window.currentFolderId = null;
window.currentFolderName = null;

/**
 * CORE DATA LOADING
 */
async function loadDashboardData() {
    const userId = getUserId();
    if (!userId) return;
    
    const username = localStorage.getItem('username') || "User";

    // Static Profile Labels
    if (document.getElementById('userNameLabel')) document.getElementById('userNameLabel').innerText = username;
    if (document.getElementById('avatarLetter')) document.getElementById('avatarLetter').innerText = username.charAt(0).toUpperCase();

    // Greeting
    const hour = new Date().getHours();
    let g = "Good Evening";
    if (hour < 12) g = "Good Morning";
    else if (hour < 18) g = "Good Afternoon";
    if (document.getElementById('greetingLabel')) document.getElementById('greetingLabel').innerText = `${g}, ${username}! 👋`;

    // Trigger sequential loading
    await loadDashboardStats();
    await loadFiles(); 
    await loadSharedFiles();
    await loadActivities();
    await loadStorageDetails();
    loadNotifications();

    // Start notification polling
    if (!window._notifInterval) {
        window._notifInterval = setInterval(loadNotifications, 10000);
    }
}

window.rawRecentFiles = [];
window.rawFiles = [];
window.rawFolders = [];

/**
 * DASHBOARD STATS (uses folder_id=all to get total counts)
 */
async function loadDashboardStats() {
    const userId = getUserId();
    try {
        const response = await fetch(`${API_BASE}/files/search?user_id=${userId}&query=&folder_id=all`);
        const data = await response.json();
        if (response.ok) {
            if (document.getElementById('dashboard-total-files')) document.getElementById('dashboard-total-files').innerText = data.files.length;

            window.rawRecentFiles = data.files || [];
            applyFiltersRecent();
        }
    } catch (err) {}
}

/**
 * FILE MANAGEMENT (OWNED) - With Folder Support
 */
async function loadFiles() {
    const userId = getUserId();
    try {
        // Determine folder context
        const folderId = window.currentFolderId;
        const folderParam = folderId ? folderId : 'root';

        // Fetch files for current context
        const response = await fetch(`${API_BASE}/files/search?user_id=${userId}&query=&folder_id=${folderParam}`);
        const data = await response.json();

        if (response.ok) {
            window.rawFiles = data.files || [];
            if (!folderId) {
                // At root - fetch folders too
                const foldersRes = await fetch(`${API_BASE}/folders?user_id=${userId}`);
                const foldersData = await foldersRes.json();
                if (foldersRes.ok) {
                    window.rawFolders = foldersData.folders || [];
                } else {
                    window.rawFolders = [];
                }
            } else {
                window.rawFolders = [];
            }
            applyFiltersFiles();
        }
    } catch (err) {}
}

/**
 * Render file list with folders at the top (root view)
 */
function renderFileListWithFolders(folders, files, containerId) {
    const listBody = document.getElementById(containerId);
    if (!listBody) return;
    listBody.innerHTML = '';

    if (folders.length === 0 && files.length === 0) {
        listBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:40px; color:var(--text-muted);">No Records Found</td></tr>`;
        return;
    }

    // Render folders
    folders.forEach(folder => {
        const isOwner = folder.user_id === undefined || folder.user_id === getUserId();
        const date = new Date(folder.created_at).toLocaleDateString();
        const row = document.createElement('tr');
        row.className = 'file-row';
        row.style.cursor = 'pointer';
        row.onclick = () => {
            if (isOwner) {
                openFolder(folder.id, folder.name);
            } else {
                openSharedFolder(folder.id, folder.name);
            }
        };
        row.innerHTML = `
            <td>
                <div class="file-name-cell">
                    <div class="file-icon" style="color: #F59E0B; background: rgba(245, 158, 11, 0.1);">${ICONS.folder}</div>
                    <span style="font-weight: 700;">${folder.name}</span>
                </div>
            </td>
            <td><span style="text-transform: uppercase; font-size: 11px; font-weight: 800; color: var(--text-muted);">Folder</span></td>
            <td>—</td>
            <td>${date}</td>
            <td style="text-align: right;">
                <div style="display: flex; gap: 8px; justify-content: flex-end;">
                    ${isOwner ? `
                    <button class="btn btn-outline" style="padding: 6px;" title="Share Folder" onclick="event.stopPropagation(); shareFolder(${folder.id}, '${folder.name.replace(/'/g, "\\'")}')">${ICONS.share}</button>
                    <button class="btn btn-outline" style="padding: 6px; color: var(--error);" title="Delete Folder" onclick="event.stopPropagation(); deleteFolder(${folder.id})">${ICONS.delete}</button>
                    ` : `
                    <span style="font-size:11px; color:var(--text-muted); font-style:italic; padding-right:8px;">Shared with you</span>
                    `}
                </div>
            </td>
        `;
        listBody.appendChild(row);
    });

    // Render files
    files.forEach(file => {
        listBody.appendChild(createFileRow(file));
    });
}

/**
 * Render file list with a "Back" row at the top (inside folder view)
 */
function renderFileListWithBack(files, containerId) {
    const listBody = document.getElementById(containerId);
    if (!listBody) return;
    listBody.innerHTML = '';

    // Back row
    const backRow = document.createElement('tr');
    backRow.className = 'file-row';
    backRow.style.cursor = 'pointer';
    backRow.onclick = () => goBackToRoot();
    backRow.innerHTML = `
        <td colspan="5">
            <div class="file-name-cell" style="gap: 8px; color: var(--primary); font-weight: 700;">
                ${ICONS.back}
                <span>← Back to My Files</span>
                <span style="color: var(--text-muted); font-weight: 400; margin-left: 8px;">(Currently in: ${window.currentFolderName || 'Folder'})</span>
            </div>
        </td>
    `;
    listBody.appendChild(backRow);

    if (files.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `<td colspan="5" style="text-align:center; padding:40px; color:var(--text-muted);">No Records Found</td>`;
        listBody.appendChild(emptyRow);
        return;
    }

    files.forEach(file => {
        listBody.appendChild(createFileRow(file));
    });
}

/**
 * Create a single file table row element
 */
function createFileRow(file) {
    const date = new Date(file.uploaded_at).toLocaleDateString();
    const size = formatBytes(file.file_size);
    const ext = file.file_type.toLowerCase();

    // Check ownership
    const isOwner = file.user_id === undefined || file.user_id === getUserId();

    const row = document.createElement('tr');
    row.className = 'file-row';
    row.innerHTML = `
        <td>
            <div class="file-name-cell">
                <div class="file-icon" style="color: ${getFileColor(ext)}">${getFileSVG(ext)}</div>
                <span style="font-weight: 600;">${file.original_name}</span>
            </div>
        </td>
        <td><span style="text-transform: uppercase; font-size: 11px; font-weight: 800; color: var(--text-muted);">${ext}</span></td>
        <td>${size}</td>
        <td>${date}</td>
        <td style="text-align: right;">
            <div style="display: flex; gap: 8px; justify-content: flex-end;">
                <button class="btn btn-outline" style="padding: 6px;" title="View" onclick="viewFile(${file.id})">${ICONS.view}</button>
                <button class="btn btn-outline" style="padding: 6px;" title="Download" onclick="downloadFile(${file.id})">${ICONS.download}</button>
                ${isOwner ? `
                <button class="btn btn-outline" style="padding: 6px;" title="Share" onclick="shareFile(${file.id}, '${file.original_name.replace(/'/g, "\\'")}')">${ICONS.share}</button>
                <button class="btn btn-outline" style="padding: 6px; color: var(--error);" title="Delete" onclick="deleteFile(${file.id})">${ICONS.delete}</button>
                ` : `
                <span style="font-size:11px; color:var(--text-muted); font-style:italic; padding-right:8px;">Shared with you</span>
                `}
            </div>
        </td>
    `;
    return row;
}

/**
 * Render simple file list (used for Recent Files on dashboard)
 */
function renderFileList(files, containerId) {
    const listBody = document.getElementById(containerId);
    if (!listBody) return;
    listBody.innerHTML = '';

    if (files.length === 0) {
        listBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:40px; color:var(--text-muted);">No Records Found</td></tr>`;
        return;
    }

    files.forEach(file => {
        listBody.appendChild(createFileRow(file));
    });
}

/**
 * FOLDER NAVIGATION
 */
function openFolder(folderId, folderName) {
    window.currentFolderId = folderId;
    window.currentFolderName = folderName;
    loadFiles();
}

function goBackToRoot() {
    window.currentFolderId = null;
    window.currentFolderName = null;
    loadFiles();
}

window.currentSharedFolderId = null;
window.currentSharedFolderName = null;

async function loadSharedFiles() {
    const userId = getUserId();
    if (!userId) return;

    try {
        // Fetch shared folders
        const foldersRes = await fetch(`${API_BASE}/folders/shared-with-me?user_id=${userId}`);
        const foldersData = await foldersRes.json();
        
        // Fetch shared files
        const filesRes = await fetch(`${API_BASE}/files/shared-with-me?user_id=${userId}`);
        const filesData = await filesRes.json();
        
        if (foldersRes.ok && filesRes.ok) {
            window.rawSharedFolders = foldersData.shared_folders || [];
            window.rawSharedFiles = filesData.shared_files || [];
            
            // Only count root shared items (folders + files not in those folders)
            const sharedFolderIds = window.rawSharedFolders.map(f => f.id);
            const rootFilesCount = window.rawSharedFiles.filter(f => !f.folder_id || !sharedFolderIds.includes(f.folder_id)).length;
            const totalCount = window.rawSharedFolders.length + rootFilesCount;
            
            if (document.getElementById('dashboard-shared-count')) {
                document.getElementById('dashboard-shared-count').innerText = totalCount;
            }
            
            applyFiltersShared();
        }
    } catch (err) {}
}

window.currentSharedSubView = 'with-me';

function setSharedSubView(subView) {
    window.currentSharedSubView = subView;
    sessionStorage.setItem('sharedSubView', subView);
    const btnWithMe = document.getElementById('btn-sub-shared-with-me');
    const btnByMe = document.getElementById('btn-sub-shared-by-me');
    const viewWithMe = document.getElementById('sub-view-shared-with-me');
    const viewByMe = document.getElementById('sub-view-shared-by-me');

    if (subView === 'with-me') {
        if (btnWithMe) { btnWithMe.className = 'btn btn-primary'; }
        if (btnByMe) { btnByMe.className = 'btn btn-outline'; }
        if (viewWithMe) { viewWithMe.style.display = 'block'; }
        if (viewByMe) { viewByMe.style.display = 'none'; }
        loadSharedFiles();
    } else {
        if (btnWithMe) { btnWithMe.className = 'btn btn-outline'; }
        if (btnByMe) { btnByMe.className = 'btn btn-primary'; }
        if (viewWithMe) { viewWithMe.style.display = 'none'; }
        if (viewByMe) { viewByMe.style.display = 'block'; }
        loadSharedByMe();
    }
}

async function loadSharedByMe() {
    const userId = getUserId();
    if (!userId) return;

    try {
        const res = await fetch(`${API_BASE}/files/shared-by-me?user_id=${userId}`);
        const data = await res.json();
        
        if (res.ok) {
            renderSharedByMeList(data.shares || []);
        }
    } catch (err) {}
}

function renderSharedByMeList(shares) {
    const listBody = document.getElementById('sharedByMeBody');
    if (!listBody) return;
    listBody.innerHTML = '';

    if (shares.length === 0) {
        listBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:40px; color:var(--text-muted);">No Records Found</td></tr>`;
        return;
    }

    shares.forEach(share => {
        const date = new Date(share.shared_at).toLocaleDateString();
        const icon = share.type === 'folder' ? ICONS.folder : getFileSVG((share.name || '').split('.').pop());
        const color = share.type === 'folder' ? '#F59E0B' : getFileColor((share.name || '').split('.').pop());
        
        const row = document.createElement('tr');
        row.className = 'file-row';
        row.innerHTML = `
            <td>
                <div class="file-name-cell">
                    <div class="file-icon" style="color: ${color}; background: ${share.type === 'folder' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(59, 130, 246, 0.1)'}">${icon}</div>
                    <span style="font-weight: 700;">${share.name}</span>
                </div>
            </td>
            <td><span style="text-transform: uppercase; font-size: 11px; font-weight: 800; color: var(--text-muted);">${share.type}</span></td>
            <td><span style="font-weight: 600; color: var(--primary)">@${share.shared_with}</span> <span style="font-size:12px; color:var(--text-muted)">(${share.shared_with_email})</span></td>
            <td>${date}</td>
            <td style="text-align: right;">
                <button type="button" class="btn btn-outline" style="padding: 6px 12px; color: var(--error); font-size: 12px; display: inline-flex; align-items: center; gap: 4px;" title="Revoke Share" onclick="event.stopPropagation(); revokeShare('${share.type}', ${share.share_id}, '${share.name.replace(/'/g, "\\'")}')">
                    ✕ Revoke
                </button>
            </td>
        `;
        listBody.appendChild(row);
    });
}

async function revokeShare(shareType, shareId, itemName) {
    if (!confirm(`Are you sure you want to revoke access to "${itemName}"?`)) return;
    
    const userId = getUserId();
    try {
        const res = await fetch(`${API_BASE}/shares/${shareType}/${shareId}?user_id=${userId}`, {
            method: 'DELETE'
        });
        const data = await res.json();
        if (res.ok) {
            showToast(`Access to "${itemName}" revoked successfully`, 'success');
            loadSharedByMe();
        } else {
            showToast(data.detail || 'Failed to revoke share', 'error');
        }
    } catch (err) {
        showToast('Server connection error', 'error');
    }
}

function openSharedFolder(folderId, folderName) {
    window.currentSharedFolderId = folderId;
    window.currentSharedFolderName = folderName;
    loadSharedFiles();
}

function goBackToSharedRoot() {
    window.currentSharedFolderId = null;
    window.currentSharedFolderName = null;
    loadSharedFiles();
}

function renderSharedList(folders, files) {
    const listBody = document.getElementById('sharedFilesBody');
    if (!listBody) return;
    listBody.innerHTML = '';

    const folderId = window.currentSharedFolderId;

    if (folderId) {
        // Inside a shared folder
        // 1. Render Back row
        const backRow = document.createElement('tr');
        backRow.className = 'file-row';
        backRow.style.cursor = 'pointer';
        backRow.onclick = () => goBackToSharedRoot();
        backRow.innerHTML = `
            <td colspan="5">
                <div class="file-name-cell" style="gap: 8px; color: var(--primary); font-weight: 700;">
                    ${ICONS.back}
                    <span>← Back to Shared Files</span>
                    <span style="color: var(--text-muted); font-weight: 400; margin-left: 8px;">(Currently in: ${window.currentSharedFolderName || 'Folder'})</span>
                </div>
            </td>
        `;
        listBody.appendChild(backRow);

        // 2. Filter and render files inside this folder
        const folderFiles = files.filter(f => f.folder_id === folderId);
        if (folderFiles.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `<td colspan="5" style="text-align:center; padding:40px; color:var(--text-muted);">No Records Found</td>`;
            listBody.appendChild(emptyRow);
            return;
        }

        folderFiles.forEach(file => {
            listBody.appendChild(createSharedFileRow(file));
        });
    } else {
        // Root shared view
        if (folders.length === 0 && files.length === 0) {
            listBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:40px; color:var(--text-muted);">No Records Found</td></tr>`;
            return;
        }

        // Render shared folders
        folders.forEach(folder => {
            const date = new Date(folder.shared_at).toLocaleDateString();
            const row = document.createElement('tr');
            row.className = 'file-row';
            row.style.cursor = 'pointer';
            row.onclick = () => openSharedFolder(folder.id, folder.name);
            row.innerHTML = `
                <td>
                    <div class="file-name-cell">
                        <div class="file-icon" style="color: #F59E0B; background: rgba(245, 158, 11, 0.1);">${ICONS.folder}</div>
                        <span style="font-weight: 700;">${folder.name}</span>
                    </div>
                </td>
                <td><span style="font-weight:600; color:var(--primary)">@${folder.owner_name}</span></td>
                <td>—</td>
                <td>${date}</td>
                <td>—</td>
            `;
            listBody.appendChild(row);
        });

        // Render shared files that are at root (folder_id is null or not in our shared folders)
        const rawSharedFolderIds = (window.rawSharedFolders || []).map(f => f.id);
        const rootFiles = files.filter(f => !f.folder_id || !rawSharedFolderIds.includes(f.folder_id));
        
        rootFiles.forEach(file => {
            listBody.appendChild(createSharedFileRow(file));
        });
    }
}

function createSharedFileRow(file) {
    const date = new Date(file.shared_at).toLocaleDateString();
    const row = document.createElement('tr');
    row.className = 'file-row';
    row.innerHTML = `
        <td><div class="file-name-cell"><div class="file-icon" style="color: ${getFileColor(file.file_type)}">${getFileSVG(file.file_type)}</div><span style="font-weight:600;">${file.original_name}</span></div></td>
        <td><span style="font-weight:600; color:var(--primary)">@${file.owner_name}</span></td>
        <td>${formatBytes(file.file_size)}</td>
        <td>${date}</td>
        <td style="text-align:right;">
            <div style="display:flex; gap:8px; justify-content:flex-end;">
                <button class="btn btn-outline" style="padding:6px;" onclick="viewFile(${file.id})">${ICONS.view}</button>
                <button class="btn btn-outline" style="padding:6px;" onclick="downloadFile(${file.id})">${ICONS.download}</button>
            </div>
        </td>
    `;
    return row;
}

/**
 * ACTIVITY LOGS
 */
async function loadActivities() {
    const userId = getUserId();
    try {
        const response = await fetch(`${API_BASE}/activity/logs?user_id=${userId}`);
        const data = await response.json();
        if (response.ok) {
            if (document.getElementById('dashboard-activity-count')) document.getElementById('dashboard-activity-count').innerText = data.logs.length;
            if (document.getElementById('activityCountLabel')) document.getElementById('activityCountLabel').innerText = data.logs.length;
            
            renderActivityList(data.logs.slice(0, 5), 'recentActivityList');
            renderActivityList(data.logs, 'fullActivityList');
        }
    } catch (err) {}
}

function renderActivityList(logs, containerId) {
    const list = document.getElementById(containerId);
    if (!list) return;
    list.innerHTML = '';

    logs.forEach(log => {
        const item = document.createElement('div');
        item.className = 'activity-item';
        item.innerHTML = `
            <div class="activity-icon" style="color: var(--primary);">${getActionSVG(log.action)}</div>
            <div class="activity-content">
                <h4 style="font-weight: 800;">${log.action}</h4>
                <p style="font-size: 13px;">${log.description}</p>
                <div class="activity-time">${formatRelativeTime(new Date(log.created_at))}</div>
            </div>
        `;
        list.appendChild(item);
    });
}

/**
 * STORAGE DETAILS
 */
async function loadStorageDetails() {
    const userId = getUserId();
    try {
        const response = await fetch(`${API_BASE}/storage/usage?user_id=${userId}`);
        const data = await response.json();
        if (response.ok) {
            const used = data.used_storage_bytes;
            const total = 10 * 1024 * 1024 * 1024; // 10GB
            const percent = ((used / total) * 100).toFixed(1);
            
            if (document.getElementById('dashboard-storage-used')) document.getElementById('dashboard-storage-used').innerText = formatBytes(used);
            if (document.getElementById('storage-percent-label')) document.getElementById('storage-percent-label').innerText = `${percent}%`;
            if (document.getElementById('storage-progress-bar')) document.getElementById('storage-progress-bar').style.width = `${percent}%`;
            if (document.getElementById('storage-used-raw')) document.getElementById('storage-used-raw').innerText = formatBytes(used);
            if (document.getElementById('storage-free-raw')) document.getElementById('storage-free-raw').innerText = formatBytes(total - used);
        }
    } catch (err) {}
}

/**
 * ACTIONS
 */

// ----- UPLOAD MODAL -----
async function openUploadModal() {
    document.getElementById('uploadModal').style.display = 'flex';
    if (document.getElementById('modalFileInput')) document.getElementById('modalFileInput').value = '';
    if (document.getElementById('modalFolderInput')) document.getElementById('modalFolderInput').value = '';
    if (window.setUploadTab) window.setUploadTab('file');
    await populateUploadFolderDropdown();
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
}

async function populateUploadFolderDropdown() {
    const userId = getUserId();
    const select = document.getElementById('uploadFolderSelect');
    select.innerHTML = '<option value="">None (Root)</option>';

    try {
        const r = await fetch(`${API_BASE}/folders?user_id=${userId}`);
        const d = await r.json();
        if (r.ok) {
            d.folders.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f.id;
                opt.textContent = f.name;
                select.appendChild(opt);
            });
            // If currently inside a folder, pre-select it
            if (window.currentFolderId) {
                select.value = window.currentFolderId;
            }
        }
    } catch (err) {}
}

async function submitModalUpload() {
    const userId = getUserId();
    const folderSelect = document.getElementById('uploadFolderSelect');
    const folderId = folderSelect.value || null;

    if (window.currentUploadTab === 'file') {
        const fileInput = document.getElementById('modalFileInput');
        if (!fileInput.files[0]) {
            showToast('Please select a file', 'error');
            return;
        }

        showLoader("Uploading File", `Uploading "${fileInput.files[0].name}"...`);
        closeUploadModal();

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        let url = `${API_BASE}/files/upload?user_id=${userId}`;
        if (folderId) url += `&folder_id=${folderId}`;

        try {
            const r = await fetch(url, { method: "POST", body: formData });
            hideLoader();
            if (r.ok) {
                showToast("Upload Successful", "success");
                loadDashboardData();
            } else {
                const errData = await r.json();
                showToast(errData.detail || "Upload Failed", "error");
            }
        } catch (err) {
            hideLoader();
            showToast("Upload Error", "error");
        }
    } else {
        // Folder Upload
        const folderInput = document.getElementById('modalFolderInput');
        if (!folderInput.files || folderInput.files.length === 0) {
            showToast('Please select a folder', 'error');
            return;
        }

        const files = Array.from(folderInput.files);
        showLoader("Uploading Folder", `Analyzing and preparing ${files.length} files...`);
        closeUploadModal();

        // Group files by top-level folder name
        const folderGroups = {};
        files.forEach(file => {
            const path = file.webkitRelativePath || '';
            const parts = path.split('/');
            const topFolder = parts[0] || 'Uploaded Folder';
            if (!folderGroups[topFolder]) {
                folderGroups[topFolder] = [];
            }
            folderGroups[topFolder].push(file);
        });

        try {
            for (const folderName of Object.keys(folderGroups)) {
                // 1. Create the folder first
                updateLoader("Creating Folder", `Setting up directory "${folderName}"...`);
                const folderRes = await fetch(`${API_BASE}/folders?user_id=${userId}&name=${encodeURIComponent(folderName)}`, { method: 'POST' });
                if (!folderRes.ok) {
                    showToast(`Failed to create folder "${folderName}"`, 'error');
                    continue;
                }
                const folderData = await folderRes.json();
                const newFolderId = folderData.folder.id;

                // 2. Upload all files under this folder
                const groupFiles = folderGroups[folderName];
                for (let i = 0; i < groupFiles.length; i++) {
                    const file = groupFiles[i];
                    updateLoader(`Uploading to "${folderName}"`, `Uploading file ${i+1} of ${groupFiles.length}: ${file.name}`);
                    
                    const formData = new FormData();
                    formData.append("file", file);

                    const uploadRes = await fetch(`${API_BASE}/files/upload?user_id=${userId}&folder_id=${newFolderId}`, {
                        method: "POST",
                        body: formData
                    });

                    if (!uploadRes.ok) {
                        const err = await uploadRes.json();
                        showToast(`Failed to upload ${file.name}: ${err.detail || 'Error'}`, 'error');
                    }
                }
            }
            hideLoader();
            showToast("Folder upload completed successfully!", "success");
            loadDashboardData();
        } catch (error) {
            hideLoader();
            showToast("An error occurred during folder upload", "error");
        }
    }
}

// ----- FOLDER MODAL -----
function openFolderModal() {
    document.getElementById('folderModal').style.display = 'flex';
    document.getElementById('folderNameInput').value = '';
    setTimeout(() => document.getElementById('folderNameInput').focus(), 100);
}

function closeFolderModal() {
    document.getElementById('folderModal').style.display = 'none';
}

async function createFolder() {
    const userId = getUserId();
    const name = document.getElementById('folderNameInput').value.trim();
    if (!name) {
        showToast('Please enter a folder name', 'error');
        return;
    }

    try {
        const r = await fetch(`${API_BASE}/folders?user_id=${userId}&name=${encodeURIComponent(name)}`, { method: 'POST' });
        if (r.ok) {
            showToast(`Folder "${name}" created`, 'success');
            closeFolderModal();
            // Navigate to files view and reload
            switchView('files');
            loadFiles();
            loadActivities();
        } else {
            showToast('Failed to create folder', 'error');
        }
    } catch (err) { showToast('Error creating folder', 'error'); }
}

async function deleteFolder(folderId) {
    if (!confirm("Delete this folder and all files inside it?")) return;
    try {
        const r = await fetch(`${API_BASE}/folders/${folderId}?user_id=${getUserId()}`, { method: 'DELETE' });
        if (r.ok) {
            showToast("Folder Deleted", "success");
            goBackToRoot();
            loadDashboardData();
        }
    } catch (err) {}
}

// ----- FILE ACTIONS -----
async function deleteFile(fileId) {
    if (!confirm("Delete this file?")) return;
    try {
        const r = await fetch(`${API_BASE}/files/${fileId}?user_id=${getUserId()}`, { method: "DELETE" });
        if (r.ok) { showToast("File Deleted", "success"); loadDashboardData(); }
    } catch (err) {}
}

function downloadFile(fileId) {
    window.open(`${API_BASE}/files/${fileId}/download?user_id=${getUserId()}`, '_blank');
}

function viewFile(fileId) {
    window.open(`${API_BASE}/files/${fileId}/view?user_id=${getUserId()}`, '_blank');
}

async function searchFiles(q) {
    const userId = getUserId();
    const query = q.trim();
    
    if (query === '') {
        loadFiles();
        return;
    }
    
    try {
        const r = await fetch(`${API_BASE}/files/search?user_id=${userId}&query=${encodeURIComponent(query)}&folder_id=all`);
        const d = await r.json();
        if (r.ok) {
            switchView('files', true);
            window.rawFiles = d.files || [];
            window.rawFolders = d.folders || [];
            applyFiltersFiles();
        }
    } catch (err) {}
}

/**
 * MODAL & USER SEARCH (Share)
 */
function shareFile(id, name) {
    window.fileToShareId = id;
    window.folderToShareId = null;
    document.getElementById('shareModalFileName').innerText = name;
    document.getElementById('shareModal').style.display = 'flex';
}
function shareFolder(id, name) {
    window.folderToShareId = id;
    window.fileToShareId = null;
    document.getElementById('shareModalFileName').innerText = `Folder: ${name}`;
    document.getElementById('shareModal').style.display = 'flex';
}
function closeShareModal() { 
    document.getElementById('shareModal').style.display = 'none'; 
    window.fileToShareId = null;
    window.folderToShareId = null;
}

async function searchUsersModal(q) {
    if (q.length < 2) return;
    const r = await fetch(`${API_BASE}/users/search?query=${encodeURIComponent(q)}&exclude_user_id=${getUserId()}`);
    const d = await r.json();
    const container = document.getElementById('modalUserSearchResults');
    container.innerHTML = d.users.map(u => `
        <div style="padding:14px; background:var(--bg-main); border-radius:12px; display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <div><div style="font-weight:800;">${u.username}</div><div style="font-size:12px; color:var(--text-muted);">${u.email}</div></div>
            <button class="btn btn-primary" style="padding:6px 14px;" onclick="confirmSharing(${u.id}, '${u.username}')">Share</button>
        </div>
    `).join('');
}

async function confirmSharing(targetId, targetName) {
    let url = "";
    if (window.folderToShareId) {
        url = `${API_BASE}/folders/${window.folderToShareId}/share?target_user_id=${targetId}&user_id=${getUserId()}`;
    } else {
        url = `${API_BASE}/files/${window.fileToShareId}/share?target_user_id=${targetId}&user_id=${getUserId()}`;
    }
    const r = await fetch(url, { method: 'POST' });
    if (r.ok) { showToast(`Shared with ${targetName}`, "success"); closeShareModal(); loadActivities(); }
    else { showToast("Sharing failed", "error"); }
}

/**
 * NOTIFICATIONS
 */
async function loadNotifications() {
    const userId = getUserId();
    if (!userId) return;

    try {
        const r = await fetch(`${API_BASE}/notifications?user_id=${userId}`);
        const d = await r.json();
        if (!r.ok) return;

        const notifications = d.notifications || [];
        const unreadCount = notifications.filter(n => !n.is_read).length;

        // Update badge
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            if (unreadCount > 0) {
                badge.style.display = 'flex';
                badge.innerText = unreadCount > 99 ? '99+' : unreadCount;
            } else {
                badge.style.display = 'none';
            }
        }

        // Update dropdown list
        const listEl = document.getElementById('notificationsList');
        if (listEl) {
            if (notifications.length === 0) {
                listEl.innerHTML = '<div style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 12px;">No notifications yet</div>';
            } else {
                listEl.innerHTML = notifications.slice(0, 20).map(n => `
                    <div style="padding: 10px; border-radius: 8px; background: ${n.is_read ? 'transparent' : 'rgba(59, 130, 246, 0.05)'}; border-left: 3px solid ${n.is_read ? 'transparent' : 'var(--primary)'}; font-size: 13px;">
                        <div style="font-weight: ${n.is_read ? '400' : '700'}; margin-bottom: 4px;">${n.message}</div>
                        <div style="font-size: 11px; color: var(--text-muted);">${formatRelativeTime(new Date(n.created_at))}</div>
                    </div>
                `).join('');
            }
        }
    } catch (err) {}
}

function toggleNotificationsDropdown() {
    const dropdown = document.getElementById('notificationsDropdown');
    if (!dropdown) return;
    const isVisible = dropdown.style.display !== 'none';
    dropdown.style.display = isVisible ? 'none' : 'block';
}

async function markAllNotificationsAsRead() {
    const userId = getUserId();
    try {
        await fetch(`${API_BASE}/notifications/read-all?user_id=${userId}`, { method: 'POST' });
        loadNotifications();
        showToast('All notifications marked as read', 'success');
    } catch (err) {}
}

// Close notifications dropdown when clicking outside
document.addEventListener('click', function (e) {
    const dropdown = document.getElementById('notificationsDropdown');
    const btn = document.getElementById('notificationBtn');
    if (dropdown && btn && !btn.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = 'none';
    }
});

/**
 * HELPERS
 */
function formatBytes(b) {
    if (b === 0) return '0 Bytes';
    const k = 1024, i = Math.floor(Math.log(b) / Math.log(k));
    return parseFloat((b / Math.pow(k, i)).toFixed(2)) + ' ' + ['Bytes', 'KB', 'MB', 'GB', 'TB'][i];
}
function getFileSVG(e) { 
    const ext = e.toLowerCase();
    if (['jpg','jpeg','png'].includes(ext)) return ICONS.image; 
    if (['mp4','mov','avi'].includes(ext)) return ICONS.video;
    return ICONS.file; 
}
function getActionSVG(a) { 
    if (a==='UPLOAD') return ICONS.folder; if (a==='DOWNLOAD') return ICONS.download; 
    if (a==='SHARE') return ICONS.share; if (a==='DELETE') return ICONS.delete; 
    if (a==='CREATE_FOLDER') return ICONS.folder; if (a==='DELETE_FOLDER') return ICONS.delete;
    return ICONS.view;
}
function getFileColor(ext) {
    const m = { 'pdf':'#EF4444', 'doc':'#3B82F6', 'jpg':'#10B981', 'png':'#10B981', 'zip':'#8B5CF6' };
    return m[ext] || 'var(--text-muted)';
}
function formatRelativeTime(d) {
    const s = Math.floor((new Date() - d) / 1000);
    if (s < 60) return 'Just now';
    if (s < 3600) return Math.floor(s/60) + 'm ago';
    if (s < 86400) return Math.floor(s/3600) + 'h ago';
    return d.toLocaleDateString();
}

async function updateProfile() {
    const userId = getUserId();
    const usernameInput = document.getElementById('settings-name-input');
    const emailInput = document.getElementById('settings-email-input');
    const btn = document.getElementById('updateProfileBtn');

    if (!usernameInput || !emailInput) return;

    const username = usernameInput.value.trim();
    const email = emailInput.value.trim();

    if (!username || !email) {
        showToast("Please fill all fields", "error");
        return;
    }

    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>Saving...';

        const response = await fetch(`${API_BASE}/auth/update-profile?user_id=${userId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email })
        });

        const data = await response.json();

        if (response.ok) {
            // Update localStorage
            localStorage.setItem("username", username);
            localStorage.setItem("email", email);

            // Update UI components immediately
            if (document.getElementById('userNameLabel')) document.getElementById('userNameLabel').innerText = username;
            if (document.getElementById('avatarLetter')) document.getElementById('avatarLetter').innerText = username.charAt(0).toUpperCase();
            if (document.getElementById('settings-username-display')) document.getElementById('settings-username-display').innerText = username;
            if (document.getElementById('settings-email-display')) document.getElementById('settings-email-display').innerText = email;
            if (document.getElementById('settings-avatar-large')) document.getElementById('settings-avatar-large').innerText = username.charAt(0).toUpperCase();
            
            const hour = new Date().getHours();
            let g = "Good Evening";
            if (hour < 12) g = "Good Morning";
            else if (hour < 18) g = "Good Afternoon";
            if (document.getElementById('greetingLabel')) document.getElementById('greetingLabel').innerText = `${g}, ${username}! 👋`;

            showToast("Profile updated successfully!", "success");
        } else {
            showToast(data.detail || "Profile update failed", "error");
        }
    } catch (err) {
        showToast("Server connection error", "error");
    } finally {
        btn.disabled = false;
        btn.innerText = "Save Profile Info";
    }
}

async function changePassword() {
    const userId = getUserId();
    const currPassInput = document.getElementById('settings-curr-pass');
    const newPassInput = document.getElementById('settings-new-pass');
    const confPassInput = document.getElementById('settings-conf-pass');
    const btn = document.getElementById('changePasswordBtn');

    if (!currPassInput || !newPassInput || !confPassInput) return;

    const current_password = currPassInput.value;
    const new_password = newPassInput.value;
    const confirm_password = confPassInput.value;

    if (!current_password || !new_password || !confirm_password) {
        showToast("Please fill all password fields", "error");
        return;
    }

    if (new_password.length < 6) {
        showToast("New password must be at least 6 characters", "error");
        return;
    }

    if (new_password !== confirm_password) {
        showToast("New passwords do not match", "error");
        return;
    }

    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>Updating...';

        const response = await fetch(`${API_BASE}/auth/change-password?user_id=${userId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ current_password, new_password })
        });

        const data = await response.json();

        if (response.ok) {
            showToast("Password updated successfully!", "success");
            // Clear inputs
            currPassInput.value = '';
            newPassInput.value = '';
            confPassInput.value = '';
        } else {
            showToast(data.detail || "Password update failed", "error");
        }
    } catch (err) {
        showToast("Server connection error", "error");
    } finally {
        btn.disabled = false;
        btn.innerText = "Update Password";
    }
}

/**
 * FILTER AND SORT LOGIC
 */
function filterAndSortItems(items, isFolder, typeVal, dateVal, sizeVal, sortVal, ownerVal = '') {
    let filtered = [...items];

    // Filter by type
    if (typeVal && typeVal !== 'all') {
        if (typeVal === 'folder') {
            filtered = filtered.filter(item => isFolder(item));
        } else if (typeVal === 'file') {
            filtered = filtered.filter(item => !isFolder(item));
        } else {
            // Check file extension
            filtered = filtered.filter(item => {
                if (isFolder(item)) return false;
                const ext = (item.file_type || '').toLowerCase();
                if (typeVal === 'pdf') return ext === 'pdf';
                if (typeVal === 'doc') return ['doc', 'docx', 'txt'].includes(ext);
                if (typeVal === 'image') return ['jpg', 'jpeg', 'png'].includes(ext);
                if (typeVal === 'video') return ['mp4', 'mov', 'avi'].includes(ext);
                if (typeVal === 'zip') return ext === 'zip';
                return false;
            });
        }
    }

    // Filter by date
    if (dateVal && dateVal !== 'all') {
        const now = new Date();
        filtered = filtered.filter(item => {
            const dateStr = item.uploaded_at || item.created_at || item.shared_at;
            if (!dateStr) return true;
            const itemDate = new Date(dateStr);
            const diffTime = Math.abs(now - itemDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (dateVal === 'today') return diffDays <= 1;
            if (dateVal === 'week') return diffDays <= 7;
            if (dateVal === 'month') return diffDays <= 30;
            return true;
        });
    }

    // Filter by size
    if (sizeVal && sizeVal !== 'all') {
        filtered = filtered.filter(item => {
            if (isFolder(item)) return true; // keep folders
            const size = item.file_size || 0;
            if (sizeVal === 'small') return size < 1 * 1024 * 1024; // < 1MB
            if (sizeVal === 'medium') return size >= 1 * 1024 * 1024 && size <= 10 * 1024 * 1024; // 1MB-10MB
            if (sizeVal === 'large') return size > 10 * 1024 * 1024; // > 10MB
            return true;
        });
    }

    // Filter by owner
    if (ownerVal) {
        const cleanOwner = ownerVal.toLowerCase().replace('@', '');
        filtered = filtered.filter(item => {
            const owner = (item.owner_name || '').toLowerCase();
            return owner.includes(cleanOwner);
        });
    }

    // Sorting
    if (sortVal) {
        filtered.sort((a, b) => {
            // Sort by Date
            if (sortVal === 'newest' || sortVal === 'oldest') {
                const dateA = new Date(a.uploaded_at || a.created_at || a.shared_at || 0);
                const dateB = new Date(b.uploaded_at || b.created_at || b.shared_at || 0);
                return sortVal === 'newest' ? dateB - dateA : dateA - dateB;
            }
            // Sort by Size
            if (sortVal === 'size-desc' || sortVal === 'size-asc') {
                const sizeA = isFolder(a) ? 0 : (a.file_size || 0);
                const sizeB = isFolder(b) ? 0 : (b.file_size || 0);
                return sortVal === 'size-desc' ? sizeB - sizeA : sizeA - sizeB;
            }
            // Sort by Name
            if (sortVal === 'name-asc' || sortVal === 'name-desc') {
                const nameA = (a.original_name || a.name || '').toLowerCase();
                const nameB = (b.original_name || b.name || '').toLowerCase();
                if (nameA < nameB) return sortVal === 'name-asc' ? -1 : 1;
                if (nameA > nameB) return sortVal === 'name-asc' ? 1 : -1;
                return 0;
            }
            return 0;
        });
    }

    return filtered;
}

function applyFiltersFiles() {
    const typeVal = document.getElementById('filter-type-files')?.value || 'all';
    const dateVal = document.getElementById('filter-date-files')?.value || 'all';
    const sizeVal = document.getElementById('filter-size-files')?.value || 'all';
    const sortVal = document.getElementById('sort-files')?.value || 'newest';

    const isFolder = item => !item.original_name;

    const allItems = [...window.rawFolders, ...window.rawFiles];
    const filteredItems = filterAndSortItems(allItems, isFolder, typeVal, dateVal, sizeVal, sortVal);

    const folders = filteredItems.filter(isFolder);
    const files = filteredItems.filter(item => !isFolder(item));

    const folderId = window.currentFolderId;
    if (folderId) {
        renderFileListWithBack(files, 'fullFileListBody');
    } else {
        renderFileListWithFolders(folders, files, 'fullFileListBody');
    }
}

function applyFiltersShared() {
    const typeVal = document.getElementById('filter-type-shared')?.value || 'all';
    const dateVal = document.getElementById('filter-date-shared')?.value || 'all';
    const sizeVal = document.getElementById('filter-size-shared')?.value || 'all';
    const ownerVal = document.getElementById('filter-owner-shared')?.value || '';
    const sortVal = document.getElementById('sort-shared')?.value || 'newest';

    const isFolder = item => !item.original_name;

    const allItems = [...window.rawSharedFolders, ...window.rawSharedFiles];
    const filteredItems = filterAndSortItems(allItems, isFolder, typeVal, dateVal, sizeVal, sortVal, ownerVal);

    const folders = filteredItems.filter(isFolder);
    const files = filteredItems.filter(item => !isFolder(item));

    renderSharedList(folders, files);
}

function applyFiltersRecent() {
    const typeVal = document.getElementById('filter-type-recent')?.value || 'all';
    const sortVal = document.getElementById('sort-recent')?.value || 'newest';

    const isFolder = item => false;

    const filtered = filterAndSortItems(window.rawRecentFiles, isFolder, typeVal, 'all', 'all', sortVal);

    renderFileList(filtered.slice(0, 5), 'recentFilesBody');
}
 