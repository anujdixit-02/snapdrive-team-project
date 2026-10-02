/* =========================================================
   SNAPDRIVE - DASHBOARD / FILE MANAGEMENT
   ========================================================= */

(function () {
    "use strict";

    /*
     * IMPORTANT:
     * Do NOT use:
     * const API_BASE = ...
     *
     * api.js may already define API_BASE.
     *
     * We use a unique window property instead.
     */
    window.SNAPDRIVE_API_BASE =
        window.SNAPDRIVE_API_BASE || window.location.origin;

    /* =========================================================
       BASIC HELPERS
       ========================================================= */

    function getApiBase() {
        return window.SNAPDRIVE_API_BASE;
    }

    function getToken() {
        return (
            localStorage.getItem("token") ||
            localStorage.getItem("access_token") ||
            ""
        );
    }

    function authHeaders(extraHeaders = {}) {
        const token = getToken();

        return {
            ...extraHeaders,
            Authorization: token ? `Bearer ${token}` : ""
        };
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function escapeJs(value) {
        return String(value ?? "")
            .replace(/\\/g, "\\\\")
            .replace(/'/g, "\\'");
    }

    function formatFileSize(bytes) {
        bytes = Number(bytes || 0);

        if (bytes <= 0) {
            return "0 B";
        }

        const units = ["B", "KB", "MB", "GB", "TB"];
        const index = Math.floor(
            Math.log(bytes) / Math.log(1024)
        );

        const safeIndex = Math.min(index, units.length - 1);

        return (
            (bytes / Math.pow(1024, safeIndex))
                .toFixed(safeIndex === 0 ? 0 : 2) +
            " " +
            units[safeIndex]
        );
    }

    function formatDate(dateValue) {
        if (!dateValue) {
            return "—";
        }

        const date = new Date(dateValue);

        if (Number.isNaN(date.getTime())) {
            return "—";
        }

        return date.toLocaleString();
    }

    function getFileCategory(file) {
        const name = (
            file.original_name ||
            file.filename ||
            file.name ||
            ""
        ).toLowerCase();

        const type = (
            file.file_type ||
            file.mime_type ||
            ""
        ).toLowerCase();

        if (
            type.includes("image") ||
            /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(name)
        ) {
            return "image";
        }

        if (
            type.includes("pdf") ||
            /\.pdf$/i.test(name)
        ) {
            return "pdf";
        }

        if (
            type.includes("video") ||
            /\.(mp4|avi|mkv|mov|webm)$/i.test(name)
        ) {
            return "video";
        }

        if (
            /\.(doc|docx|txt|rtf)$/i.test(name) ||
            type.includes("text") ||
            type.includes("word")
        ) {
            return "doc";
        }

        if (
            /\.(zip|rar|7z|tar|gz)$/i.test(name)
        ) {
            return "zip";
        }

        return "other";
    }

    function showToast(message, type = "info") {
        /*
         * Use the dashboard's existing toast system if available.
         */
        if (
            typeof window.showToast === "function" &&
            window.showToast !== showToast
        ) {
            window.showToast(message, type);
            return;
        }

        /*
         * Fallback toast.
         */
        let toast = document.getElementById("snapdriveFallbackToast");

        if (!toast) {
            toast = document.createElement("div");
            toast.id = "snapdriveFallbackToast";

            toast.style.position = "fixed";
            toast.style.right = "24px";
            toast.style.bottom = "24px";
            toast.style.zIndex = "99999";
            toast.style.padding = "14px 18px";
            toast.style.borderRadius = "12px";
            toast.style.background = "#111827";
            toast.style.color = "#ffffff";
            toast.style.boxShadow =
                "0 10px 30px rgba(0,0,0,.25)";
            toast.style.fontSize = "14px";
            toast.style.maxWidth = "360px";

            document.body.appendChild(toast);
        }

        toast.textContent = message;
        toast.style.display = "block";

        clearTimeout(toast._timer);

        toast._timer = setTimeout(() => {
            toast.style.display = "none";
        }, 3500);
    }

    function showLoader(show = true) {
        const loader = document.getElementById("globalLoader");

        if (loader) {
            if (show) {
                loader.classList.add("show");
            } else {
                loader.classList.remove("show");
            }
        }
    }

    async function parseResponse(response) {
        const text = await response.text();

        let data = {};

        if (text) {
            try {
                data = JSON.parse(text);
            } catch {
                data = {
                    message: text
                };
            }
        }

        return data;
    }

    async function apiRequest(
        path,
        options = {}
    ) {
        const url = getApiBase() + path;

        const response = await fetch(url, {
            ...options,
            cache: options.cache || "no-store"
        });

        const data = await parseResponse(response);

        if (!response.ok) {
            const detail =
                data.detail ||
                data.message ||
                `HTTP ${response.status}`;

            throw new Error(detail);
        }

        return data;
    }

    /* =========================================================
       DASHBOARD
       ========================================================= */

    async function loadDashboardData() {
        await Promise.allSettled([
            loadFiles(),
            loadActivities(),
            loadStorageDetails(),
            loadNotifications(),
            loadSharedFiles()
        ]);
    }

    /* =========================================================
       FILES
       ========================================================= */

    async function loadFiles() {
        const token = getToken();

        if (!token) {
            console.error("No authentication token found.");
            return;
        }

        try {
            const data = await apiRequest(
                "/files",
                {
                    method: "GET",
                    headers: authHeaders({
                        "Content-Type": "application/json"
                    })
                }
            );

            let files = Array.isArray(data)
                ? data
                : (data.files || []);

            files = files.filter(
                file => !file.is_deleted
            );

            files.sort((a, b) => {
                const dateA = new Date(
                    a.created_at ||
                    a.uploaded_at ||
                    a.createdAt ||
                    0
                );

                const dateB = new Date(
                    b.created_at ||
                    b.uploaded_at ||
                    b.createdAt ||
                    0
                );

                return dateB - dateA;
            });

            console.log("SnapDrive files received:", files);

            renderMyFiles(files);
            renderRecentFiles(files);

            const totalFiles = document.getElementById(
                "dashboard-total-files"
            );

            if (totalFiles) {
                totalFiles.textContent = files.length;
            }

            /*
             * Support alternative dashboard IDs too.
             */
            const totalFilesAlt = document.getElementById(
                "totalFiles"
            );

            if (totalFilesAlt) {
                totalFilesAlt.textContent = files.length;
            }

            return files;

        } catch (error) {
            console.error(
                "loadFiles error:",
                error
            );

            const body = document.getElementById(
                "fullFileListBody"
            );

            if (body) {
                body.innerHTML = `
                    <tr>
                        <td colspan="5"
                            style="
                                text-align:center;
                                padding:30px;
                                color:var(--text-muted,#999);
                            ">
                            Unable to load files.
                        </td>
                    </tr>
                `;
            }

            const recent = document.getElementById(
                "recentFilesBody"
            );

            if (recent) {
                recent.innerHTML = `
                    <tr>
                        <td colspan="3"
                            style="
                                text-align:center;
                                padding:20px;
                                color:var(--text-muted,#999);
                            ">
                            Unable to load recent files.
                        </td>
                    </tr>
                `;
            }

            showToast(
                error.message || "Unable to load files.",
                "error"
            );
        }
    }

    function renderMyFiles(files) {
        const body = document.getElementById(
            "fullFileListBody"
        );

        if (!body) {
            return;
        }

        if (!files.length) {
            body.innerHTML = `
                <tr>
                    <td colspan="5"
                        style="
                            text-align:center;
                            padding:35px;
                            color:var(--text-muted,#999);
                        ">
                        No files uploaded yet.
                    </td>
                </tr>
            `;

            return;
        }

        body.innerHTML = files.map(file => {
            const id = Number(file.id);

            const name =
                file.original_name ||
                file.filename ||
                "Unnamed file";

            const category = getFileCategory(file);

            return `
                <tr>
                    <td>
                        <div style="
                            display:flex;
                            align-items:center;
                            gap:10px;
                        ">
                            <span>
                                ${escapeHtml(name)}
                            </span>
                        </div>
                    </td>

                    <td>
                        ${escapeHtml(
                            category.toUpperCase()
                        )}
                    </td>

                    <td>
                        ${formatFileSize(
                            file.file_size
                        )}
                    </td>

                    <td>
                        ${formatDate(
                            file.uploaded_at ||
                            file.created_at
                        )}
                    </td>

                    <td style="text-align:right;">
                        <button
                            type="button"
                            class="btn btn-outline"
                            onclick="viewFile(${id})">
                            View
                        </button>

                        <button
                            type="button"
                            class="btn btn-outline"
                            onclick="downloadFile(
                                ${id},
                                '${escapeJs(name)}'
                            )">
                            Download
                        </button>

                        <button
                            type="button"
                            class="btn btn-outline"
                            onclick="openShareModal(
                                ${id},
                                '${escapeJs(name)}'
                            )">
                            Share
                        </button>

                        <button
                            type="button"
                            class="btn btn-outline"
                            onclick="deleteFile(${id})">
                            Delete
                        </button>
                    </td>
                </tr>
            `;
        }).join("");
    }

    function renderRecentFiles(files) {
        const body = document.getElementById(
            "recentFilesBody"
        );

        if (!body) {
            return;
        }

        if (!files.length) {
            body.innerHTML = `
                <tr>
                    <td colspan="3"
                        style="
                            text-align:center;
                            padding:25px;
                            color:var(--text-muted,#999);
                        ">
                        No recent files.
                    </td>
                </tr>
            `;

            return;
        }

        body.innerHTML = files
            .slice(0, 5)
            .map(file => {
                const name =
                    file.original_name ||
                    file.filename ||
                    "Unnamed file";

                return `
                    <tr>
                        <td>
                            ${escapeHtml(name)}
                        </td>

                        <td>
                            ${formatFileSize(
                                file.file_size
                            )}
                        </td>

                        <td>
                            ${formatDate(
                                file.uploaded_at ||
                                file.created_at
                            )}
                        </td>
                    </tr>
                `;
            })
            .join("");
    }

    /* =========================================================
       VIEW FILE
       ========================================================= */

    async function viewFile(fileId) {
        const token = getToken();

        if (!token) {
            showToast(
                "Please login again.",
                "error"
            );
            return;
        }

        try {
            showLoader(true);

            const response = await fetch(
                `${getApiBase()}/files/${fileId}/view`,
                {
                    method: "GET",
                    headers: authHeaders(),
                    cache: "no-store"
                }
            );

            if (!response.ok) {
                const data =
                    await parseResponse(response);

                throw new Error(
                    data.detail ||
                    data.message ||
                    `Unable to view file. HTTP ${response.status}`
                );
            }

            const blob =
                await response.blob();

            const url =
                URL.createObjectURL(blob);

            window.open(
                url,
                "_blank",
                "noopener,noreferrer"
            );

            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 60000);

        } catch (error) {
            console.error(
                "View file error:",
                error
            );

            showToast(
                error.message ||
                "Unable to view file.",
                "error"
            );

        } finally {
            showLoader(false);
        }
    }

    /* =========================================================
       DOWNLOAD FILE
       ========================================================= */

    async function downloadFile(
        fileId,
        fileName = "download"
    ) {
        const token = getToken();

        if (!token) {
            showToast(
                "Please login again.",
                "error"
            );
            return;
        }

        try {
            showLoader(true);

            const response = await fetch(
                `${getApiBase()}/files/${fileId}/download`,
                {
                    method: "GET",
                    headers: authHeaders(),
                    cache: "no-store"
                }
            );

            if (!response.ok) {
                const data =
                    await parseResponse(response);

                throw new Error(
                    data.detail ||
                    data.message ||
                    `Download failed. HTTP ${response.status}`
                );
            }

            const blob =
                await response.blob();

            const url =
                URL.createObjectURL(blob);

            const link =
                document.createElement("a");

            link.href = url;
            link.download = fileName || "download";

            document.body.appendChild(link);
            link.click();
            link.remove();

            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 10000);

            showToast(
                "File downloaded successfully.",
                "success"
            );

        } catch (error) {
            console.error(
                "Download error:",
                error
            );

            showToast(
                error.message ||
                "Unable to download file.",
                "error"
            );

        } finally {
            showLoader(false);
        }
    }

    /* =========================================================
       DELETE FILE
       ========================================================= */

    function deleteFile(fileId) {
        if (
            typeof window.openConfirmModal ===
            "function"
        ) {
            window.openConfirmModal(
                "Delete File",
                "Are you sure you want to delete this file? This action cannot be undone.",
                async function () {
                    await performDeleteFile(fileId);
                },
                "Delete"
            );

            return;
        }

        /*
         * No native confirm().
         * If the dashboard confirmation modal is unavailable,
         * execute directly.
         */
        performDeleteFile(fileId);
    }

    async function performDeleteFile(fileId) {
        try {
            showLoader(true);

            await apiRequest(
                `/files/${fileId}`,
                {
                    method: "DELETE",
                    headers: authHeaders()
                }
            );

            showToast(
                "File deleted successfully.",
                "success"
            );

            await loadFiles();
            await loadStorageDetails();
            await loadActivities();

        } catch (error) {
            console.error(
                "Delete file error:",
                error
            );

            showToast(
                error.message ||
                "Unable to delete file.",
                "error"
            );

        } finally {
            showLoader(false);
        }
    }

    /* =========================================================
       UPLOAD MODAL
       ========================================================= */

    function openUploadModal() {
        const modal =
            document.getElementById(
                "uploadModal"
            );

        if (!modal) {
            console.error(
                "uploadModal element not found."
            );
            return;
        }

        modal.style.display = "flex";

        const fileInput =
            getUploadFileInput();

        if (fileInput) {
            fileInput.value = "";
        }

        updateSelectedFileUI(null);

        loadFolders();
    }

    function closeUploadModal() {
        const modal =
            document.getElementById(
                "uploadModal"
            );

        if (modal) {
            modal.style.display = "none";
        }
    }

    function getUploadFileInput() {
        /*
         * Support both versions of your dashboard.
         */
        return (
            document.getElementById(
                "modalFileInput"
            ) ||
            document.getElementById(
                "fileInput"
            )
        );
    }

    function updateSelectedFileUI(file) {
        const info =
            document.getElementById(
                "selectedFileInfo"
            );

        const name =
            document.getElementById(
                "selectedFileName"
            );

        const size =
            document.getElementById(
                "selectedFileSize"
            );

        if (!file) {
            if (info) {
                info.style.display = "none";
            }

            if (name) {
                name.textContent = "";
            }

            if (size) {
                size.textContent = "";
            }

            return;
        }

        if (info) {
            info.style.display = "block";
        }

        if (name) {
            name.textContent = file.name;
        }

        if (size) {
            size.textContent =
                formatFileSize(file.size);
        }
    }

    function handleFileSelection(event) {
        const input =
            event.target;

        if (
            input &&
            input.files &&
            input.files.length
        ) {
            updateSelectedFileUI(
                input.files[0]
            );
        }
    }

    async function submitModalUpload() {
        const fileInput =
            getUploadFileInput();

        if (
            !fileInput ||
            !fileInput.files ||
            !fileInput.files.length
        ) {
            showToast(
                "Please select a file first.",
                "warning"
            );
            return;
        }

        const token = getToken();

        if (!token) {
            showToast(
                "Your login session has expired.",
                "error"
            );

            return;
        }

        const file =
            fileInput.files[0];

        /*
         * Backend currently supports max 50 MB.
         */
        const MAX_FILE_SIZE =
            50 * 1024 * 1024;

        if (file.size > MAX_FILE_SIZE) {
            showToast(
                "File size cannot exceed 50 MB.",
                "warning"
            );

            return;
        }

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );

        /*
         * Optional folder support.
         */
        const folderSelect =
            document.getElementById(
                "uploadFolderSelect"
            );

        if (
            folderSelect &&
            folderSelect.value
        ) {
            formData.append(
                "folder_id",
                folderSelect.value
            );
        }

        try {
            showLoader(true);

            showToast(
                "Uploading file...",
                "info"
            );

            const response =
                await fetch(
                    `${getApiBase()}/files/upload`,
                    {
                        method: "POST",

                        headers: {
                            Authorization:
                                `Bearer ${token}`
                        },

                        body: formData,

                        cache: "no-store"
                    }
                );

            const data =
                await parseResponse(
                    response
                );

            console.log(
                "Upload response:",
                response.status,
                data
            );

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    data.message ||
                    `Upload failed. HTTP ${response.status}`
                );
            }

            fileInput.value = "";

            updateSelectedFileUI(null);

            closeUploadModal();

            showToast(
                "File uploaded successfully.",
                "success"
            );

            /*
             * Refresh dashboard.
             */
            await Promise.allSettled([
                loadFiles(),
                loadActivities(),
                loadStorageDetails(),
                loadNotifications()
            ]);

        } catch (error) {
            console.error(
                "Upload error:",
                error
            );

            showToast(
                error.message ||
                "File upload failed.",
                "error"
            );

        } finally {
            showLoader(false);
        }
    }

    /* =========================================================
       UPLOAD TABS
       ========================================================= */

    function setUploadTab(tab) {
        window.currentUploadTab = tab;

        const fileTab =
            document.getElementById(
                "tab-upload-file"
            );

        const folderTab =
            document.getElementById(
                "tab-upload-folder"
            );

        const fileGroup =
            document.getElementById(
                "fileUploadGroup"
            );

        const folderGroup =
            document.getElementById(
                "folderUploadGroup"
            );

        if (
            tab === "file"
        ) {
            if (fileTab) {
                fileTab.className =
                    "btn btn-primary";
            }

            if (folderTab) {
                folderTab.className =
                    "btn btn-outline";
            }

            if (fileGroup) {
                fileGroup.style.display =
                    "block";
            }

            if (folderGroup) {
                folderGroup.style.display =
                    "none";
            }

        } else {
            if (fileTab) {
                fileTab.className =
                    "btn btn-outline";
            }

            if (folderTab) {
                folderTab.className =
                    "btn btn-primary";
            }

            if (fileGroup) {
                fileGroup.style.display =
                    "none";
            }

            if (folderGroup) {
                folderGroup.style.display =
                    "block";
            }
        }
    }

    /* =========================================================
       FOLDERS
       ========================================================= */

    function openFolderModal() {
        const modal =
            document.getElementById(
                "folderModal"
            );

        if (modal) {
            modal.style.display = "flex";
        }
    }

    function closeFolderModal() {
        const modal =
            document.getElementById(
                "folderModal"
            );

        if (modal) {
            modal.style.display = "none";
        }
    }

    async function createFolder() {
        const input =
            document.getElementById(
                "folderNameInput"
            );

        if (
            !input ||
            !input.value.trim()
        ) {
            showToast(
                "Enter a folder name.",
                "warning"
            );

            return;
        }

        try {
            showLoader(true);

            const name =
                input.value.trim();

            const data =
                await apiRequest(
                    `/folders?name=${encodeURIComponent(name)}`,
                    {
                        method: "POST",
                        headers: authHeaders()
                    }
                );

            input.value = "";

            closeFolderModal();

            showToast(
                data.message ||
                "Folder created successfully.",
                "success"
            );

            await loadFolders();

        } catch (error) {
            console.error(
                "Create folder error:",
                error
            );

            showToast(
                error.message ||
                "Unable to create folder.",
                "error"
            );

        } finally {
            showLoader(false);
        }
    }

    async function loadFolders() {
        const token = getToken();

        if (!token) {
            return;
        }

        try {
            const data =
                await apiRequest(
                    "/folders",
                    {
                        method: "GET",
                        headers: authHeaders()
                    }
                );

            const select =
                document.getElementById(
                    "uploadFolderSelect"
                );

            if (!select) {
                return;
            }

            const folders =
                data.folders || [];

            select.innerHTML = `
                <option value="">
                    None (Root)
                </option>
            `;

            folders.forEach(folder => {
                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    folder.id;

                option.textContent =
                    folder.name;

                select.appendChild(
                    option
                );
            });

        } catch (error) {
            console.error(
                "loadFolders error:",
                error
            );
        }
    }

    /* =========================================================
       SHARED FILES
       ========================================================= */

    async function loadSharedFiles() {
        const token = getToken();

        if (!token) {
            return;
        }

        const subView =
            sessionStorage.getItem(
                "sharedSubView"
            ) || "with-me";

        if (
            subView === "by-me"
        ) {
            await loadSharedByMe();
            return;
        }

        try {
            const data =
                await apiRequest(
                    "/files/shared-with-me",
                    {
                        method: "GET",
                        headers: authHeaders()
                    }
                );

            const files =
                data.shared_files ||
                data.files ||
                [];

            /*
             * "Shared With Me" dashboard stat.
             */
            const sharedCountEl =
                document.getElementById(
                    "sharedCount"
                );

            if (sharedCountEl) {
                sharedCountEl.textContent =
                    files.length;
            }

            renderSharedFiles(files);

        } catch (error) {
            console.error(
                "loadSharedFiles error:",
                error
            );

            const body =
                document.getElementById(
                    "sharedFilesBody"
                );

            if (body) {
                body.innerHTML = `
                    <tr>
                        <td colspan="5"
                            style="
                                text-align:center;
                                padding:25px;
                                color:var(--text-muted,#999);
                            ">
                            Unable to load shared files.
                        </td>
                    </tr>
                `;
            }
        }
    }

    function renderSharedFiles(files) {
        const body =
            document.getElementById(
                "sharedFilesBody"
            );

        if (!body) {
            return;
        }

        if (!files.length) {
            body.innerHTML = `
                <tr>
                    <td colspan="5"
                        style="
                            text-align:center;
                            padding:30px;
                            color:var(--text-muted,#999);
                        ">
                        No files have been shared with you.
                    </td>
                </tr>
            `;

            return;
        }

        body.innerHTML = files.map(file => {
            const id =
                Number(
                    file.file_id ||
                    file.item_id ||
                    file.id
                );

            const name =
                file.original_name ||
                file.name ||
                "Unnamed file";

            return `
                <tr>
                    <td>
                        ${escapeHtml(name)}
                    </td>

                    <td>
                        ${escapeHtml(
                            file.owner_name ||
                            "Unknown"
                        )}
                    </td>

                    <td>
                        ${formatFileSize(
                            file.file_size
                        )}
                    </td>

                    <td>
                        ${formatDate(
                            file.shared_at
                        )}
                    </td>

                    <td style="text-align:right;">
                        <button
                            type="button"
                            class="btn btn-outline"
                            onclick="downloadFile(
                                ${id},
                                '${escapeJs(name)}'
                            )">
                            Download
                        </button>

                        <button
                            type="button"
                            class="btn btn-outline"
                            onclick="viewFile(${id})">
                            View
                        </button>
                    </td>
                </tr>
            `;
        }).join("");
    }

    /* =========================================================
       SHARED BY ME
       ========================================================= */

    async function loadSharedByMe() {
        const token = getToken();

        if (!token) {
            return;
        }

        try {
            const data =
                await apiRequest(
                    "/files/shared-by-me",
                    {
                        method: "GET",
                        headers: authHeaders()
                    }
                );

            const files =
                data.shares ||
                data.shared_files ||
                [];

            renderSharedByMe(files);

        } catch (error) {
            console.error(
                "loadSharedByMe error:",
                error
            );

            const body =
                document.getElementById(
                    "sharedByMeBody"
                );

            if (body) {
                body.innerHTML = `
                    <tr>
                        <td colspan="5"
                            style="
                                text-align:center;
                                padding:25px;
                                color:var(--text-muted,#999);
                            ">
                            Unable to load sharing history.
                        </td>
                    </tr>
                `;
            }
        }
    }

    function renderSharedByMe(files) {
        const body =
            document.getElementById(
                "sharedByMeBody"
            );

        if (!body) {
            return;
        }

        if (!files.length) {
            body.innerHTML = `
                <tr>
                    <td colspan="5"
                        style="
                            text-align:center;
                            padding:30px;
                            color:var(--text-muted,#999);
                        ">
                        You haven't shared any files yet.
                    </td>
                </tr>
            `;

            return;
        }

        body.innerHTML = files.map(item => {
            const shareId =
                Number(
                    item.share_id ||
                    item.id
                );

            const name =
                item.name ||
                item.original_name ||
                "Unnamed";

            return `
                <tr>
                    <td>
                        ${escapeHtml(name)}
                    </td>

                    <td>
                        ${escapeHtml(
                            item.type ||
                            "file"
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            item.shared_with ||
                            item.shared_with_email ||
                            "Unknown"
                        )}
                    </td>

                    <td>
                        ${formatDate(
                            item.shared_at
                        )}
                    </td>

                    <td style="text-align:right;">
                        <button
                            type="button"
                            class="btn btn-outline"
                            onclick="revokeShare(
                                'file',
                                ${shareId}
                            )">
                            Revoke
                        </button>
                    </td>
                </tr>
            `;
        }).join("");
    }

    function setSharedSubView(view) {
        sessionStorage.setItem(
            "sharedSubView",
            view
        );

        /*
         * IDs match dashboard.html's actual markup:
         * sharedWithMeSection / sharedByMeSection
         * sharedWithMeTab / sharedByMeTab
         */
        const withMe =
            document.getElementById(
                "sharedWithMeSection"
            );

        const byMe =
            document.getElementById(
                "sharedByMeSection"
            );

        const withMeButton =
            document.getElementById(
                "sharedWithMeTab"
            );

        const byMeButton =
            document.getElementById(
                "sharedByMeTab"
            );

        if (view === "by-me") {
            if (withMe) {
                withMe.style.display =
                    "none";
            }

            if (byMe) {
                byMe.style.display =
                    "block";
            }

            if (withMeButton) {
                withMeButton.classList.remove(
                    "active"
                );
            }

            if (byMeButton) {
                byMeButton.classList.add(
                    "active"
                );
            }

            loadSharedByMe();

        } else {
            if (withMe) {
                withMe.style.display =
                    "block";
            }

            if (byMe) {
                byMe.style.display =
                    "none";
            }

            if (withMeButton) {
                withMeButton.classList.add(
                    "active"
                );
            }

            if (byMeButton) {
                byMeButton.classList.remove(
                    "active"
                );
            }

            loadSharedFiles();
        }
    }

    /* =========================================================
       REVOKE SHARE
       ========================================================= */

    function revokeShare(
        shareType,
        shareId
    ) {
        if (
            typeof window.openConfirmModal ===
            "function"
        ) {
            window.openConfirmModal(
                "Revoke Share",
                "Are you sure you want to revoke access to this shared item?",
                async function () {
                    await performRevokeShare(
                        shareType,
                        shareId
                    );
                },
                "Revoke"
            );

            return;
        }

        performRevokeShare(
            shareType,
            shareId
        );
    }

    async function performRevokeShare(
        shareType,
        shareId
    ) {
        try {
            showLoader(true);

            await apiRequest(
                `/shares/${shareType}/${shareId}`,
                {
                    method: "DELETE",
                    headers: authHeaders()
                }
            );

            showToast(
                "Share access revoked.",
                "success"
            );

            await loadSharedByMe();
            await loadActivities();

        } catch (error) {
            console.error(
                "Revoke share error:",
                error
            );

            showToast(
                error.message ||
                "Unable to revoke share.",
                "error"
            );

        } finally {
            showLoader(false);
        }
    }

    /* =========================================================
       NOTIFICATIONS
       ========================================================= */

    async function loadNotifications() {
        const token = getToken();

        if (!token) {
            return;
        }

        try {
            const data =
                await apiRequest(
                    "/notifications",
                    {
                        method: "GET",
                        headers: authHeaders()
                    }
                );

            /*
             * dashboard.html only has a plain unread
             * dot indicator (#notificationDot), not a
             * numbered badge.
             */
            const badge =
                document.getElementById(
                    "notificationDot"
                );

            const unread =
                Number(
                    data.unread_count || 0
                );

            if (badge) {
                badge.style.display =
                    unread > 0 ? "block" : "none";
            }

            const list =
                document.getElementById(
                    "notificationsList"
                );

            if (list) {
                const notifications =
                    data.notifications || [];

                if (!notifications.length) {
                    list.innerHTML = `
                        <div style="
                            padding:20px;
                            text-align:center;
                            color:var(--text-muted,#999);
                        ">
                            No notifications.
                        </div>
                    `;
                } else {
                    list.innerHTML =
                        notifications
                            .map(notification => `
                                <div
                                    class="notification-item"
                                    style="
                                        padding:12px;
                                        border-bottom:1px solid var(--border-light,#ddd);
                                    "
                                    onclick="markNotificationRead(
                                        ${notification.id}
                                    )">
                                    <div>
                                        ${escapeHtml(
                                            notification.message ||
                                            "Notification"
                                        )}
                                    </div>

                                    <small style="
                                        color:var(--text-muted,#999);
                                    ">
                                        ${formatDate(
                                            notification.created_at
                                        )}
                                    </small>
                                </div>
                            `)
                            .join("");
                }
            }

        } catch (error) {
            console.error(
                "loadNotifications error:",
                error
            );
        }
    }

    async function markNotificationRead(
        notificationId
    ) {
        try {
            await apiRequest(
                `/notifications/${notificationId}/read`,
                {
                    method: "POST",
                    headers: authHeaders()
                }
            );

            await loadNotifications();

        } catch (error) {
            console.error(
                "markNotificationRead error:",
                error
            );
        }
    }

    async function markAllNotificationsAsRead() {
        try {
            let response;

            try {
                response =
                    await apiRequest(
                        "/notifications/read-all",
                        {
                            method: "POST",
                            headers: authHeaders()
                        }
                    );
            } catch {
                /*
                 * Compatibility with previous route.
                 */
                response =
                    await apiRequest(
                        "/notifications/mark-all-read",
                        {
                            method: "POST",
                            headers: authHeaders()
                        }
                    );
            }

            await loadNotifications();

            showToast(
                "All notifications marked as read.",
                "success"
            );

            return response;

        } catch (error) {
            console.error(
                "markAllNotificationsAsRead error:",
                error
            );

            showToast(
                error.message ||
                "Unable to update notifications.",
                "error"
            );
        }
    }

    /* =========================================================
       ACTIVITY
       ========================================================= */

    async function loadActivities() {
        const token = getToken();

        if (!token) {
            return;
        }

        try {
            const data =
                await apiRequest(
                    "/activity/logs",
                    {
                        method: "GET",
                        headers: authHeaders()
                    }
                );

            const logs =
                data.logs || [];

            const activityCount =
                document.getElementById(
                    "dashboard-activity-count"
                );

            if (activityCount) {
                activityCount.textContent =
                    logs.length;
            }

            const activityCountAlt =
                document.getElementById(
                    "activityCount"
                );

            if (activityCountAlt) {
                activityCountAlt.textContent =
                    logs.length;
            }

            renderActivityList(
                logs
            );

        } catch (error) {
            console.error(
                "loadActivities error:",
                error
            );
        }
    }

    function renderActivityList(logs) {
        const recent =
            document.getElementById(
                "recentActivityList"
            );

        /*
         * dashboard.html's dedicated Activity view
         * uses id="activityList" (not "fullActivityList").
         */
        const full =
            document.getElementById(
                "activityList"
            );

        if (recent) {
            if (!logs.length) {
                recent.innerHTML = `
                    <div style="
                        padding:20px;
                        color:var(--text-muted,#999);
                    ">
                        No activities yet.
                    </div>
                `;
            } else {
                recent.innerHTML =
                    logs
                        .slice(0, 5)
                        .map(log => `
                            <div style="
                                padding:10px;
                                border-bottom:1px solid var(--border-light,#ddd);
                            ">
                                <strong>
                                    ${escapeHtml(
                                        log.action ||
                                        "Activity"
                                    )}
                                </strong>

                                <br>

                                <small>
                                    ${escapeHtml(
                                        log.description ||
                                        ""
                                    )}
                                </small>

                                <br>

                                <small style="
                                    color:var(--text-muted,#999);
                                ">
                                    ${formatDate(
                                        log.created_at
                                    )}
                                </small>
                            </div>
                        `)
                        .join("");
            }
        }

        if (full) {
            if (!logs.length) {
                full.innerHTML = `
                    <div style="
                        padding:20px;
                        color:var(--text-muted,#999);
                    ">
                        No activities yet.
                    </div>
                `;
            } else {
                full.innerHTML =
                    logs
                        .map(log => `
                            <div style="
                                padding:14px;
                                border-bottom:1px solid var(--border-light,#ddd);
                            ">
                                <strong>
                                    ${escapeHtml(
                                        log.action ||
                                        "Activity"
                                    )}
                                </strong>

                                <br>

                                <span>
                                    ${escapeHtml(
                                        log.description ||
                                        ""
                                    )}
                                </span>

                                <br>

                                <small style="
                                    color:var(--text-muted,#999);
                                ">
                                    ${formatDate(
                                        log.created_at
                                    )}
                                </small>
                            </div>
                        `)
                        .join("");
            }
        }
    }

    /* =========================================================
       STORAGE
       ========================================================= */

    async function loadStorageDetails() {
        const token = getToken();

        if (!token) {
            return;
        }

        try {
            const data =
                await apiRequest(
                    "/files",
                    {
                        method: "GET",
                        headers: authHeaders()
                    }
                );

            const files =
                Array.isArray(data)
                    ? data
                    : (data.files || []);

            const used =
                files.reduce(
                    (total, file) =>
                        total +
                        Number(
                            file.file_size || 0
                        ),
                    0
                );

            /*
             * SnapDrive user storage limit.
             * Keep this aligned with storage_service.py.
             */
            const total =
                1024 * 1024 * 1024;

            const percent =
                Math.min(
                    100,
                    Math.round(
                        (used / total) * 100
                    )
                );

            const usedText =
                formatFileSize(used);

            updateStorageUI(
                used,
                total,
                percent,
                usedText
            );

        } catch (error) {
            console.error(
                "loadStorageDetails error:",
                error
            );
        }
    }

    function updateStorageUI(
        used,
        total,
        percent,
        usedText
    ) {

        /*
         * Dashboard stat card + Settings tab.
         */
        const dashboardStatStorage =
            document.getElementById(
                "storageUsed"
            );

        if (dashboardStatStorage) {
            dashboardStatStorage.textContent =
                usedText;
        }

        const settingsStorage =
            document.getElementById(
                "settingsStorage"
            );

        if (settingsStorage) {
            settingsStorage.textContent =
                usedText;
        }

        /*
         * Dashboard storage text.
         */
        const dashboardStorage =
            document.getElementById(
                "dashboard-storage-used"
            );

        if (dashboardStorage) {
            dashboardStorage.textContent =
                usedText;
        }

        /*
         * New dashboard IDs.
         */
        const dashboardUsed =
            document.getElementById(
                "dashboardStorageUsed"
            );

        if (dashboardUsed) {
            dashboardUsed.textContent =
                usedText;
        }

        const dashboardPercent =
            document.getElementById(
                "dashboardStoragePercent"
            );

        if (dashboardPercent) {
            dashboardPercent.textContent =
                percent + "%";
        }

        /*
         * Sidebar.
         */
        const sidebarText =
            document.getElementById(
                "sidebarStorageText"
            );

        if (sidebarText) {
            sidebarText.textContent =
                `${usedText} / 1 GB`;
        }

        const sidebarProgress =
            document.getElementById(
                "sidebarStorageProgress"
            );

        if (sidebarProgress) {
            sidebarProgress.style.width =
                percent + "%";
        }

        /*
         * Older storage IDs.
         */
        const oldPercent =
            document.getElementById(
                "storage-percent-label"
            );

        if (oldPercent) {
            oldPercent.textContent =
                percent + "%";
        }

        const oldProgress =
            document.getElementById(
                "storage-progress-bar"
            );

        if (oldProgress) {
            oldProgress.style.width =
                percent + "%";
        }

        const oldUsed =
            document.getElementById(
                "storage-used-raw"
            );

        if (oldUsed) {
            oldUsed.textContent =
                usedText;
        }

        /*
         * Storage details.
         */
        const storageDetailsUsed =
            document.getElementById(
                "storageDetailsUsed"
            );

        if (storageDetailsUsed) {
            storageDetailsUsed.textContent =
                usedText;
        }

        const storageDetailsPercent =
            document.getElementById(
                "storageDetailsPercent"
            );

        if (storageDetailsPercent) {
            storageDetailsPercent.textContent =
                percent + "%";
        }

        const storageDetailsText =
            document.getElementById(
                "storageDetailsText"
            );

        if (storageDetailsText) {
            storageDetailsText.textContent =
                `${usedText} of 1 GB used`;
        }

        const storageDetailsProgress =
            document.getElementById(
                "storageDetailsProgress"
            );

        if (storageDetailsProgress) {
            storageDetailsProgress.style.width =
                percent + "%";
        }

        /*
         * Circle progress.
         */
        const circles = [
            document.getElementById(
                "dashboardStorageCircle"
            ),
            document.getElementById(
                "storageDetailsCircle"
            )
        ];

        circles.forEach(circle => {
            if (!circle) {
                return;
            }

            const circumference =
                2 * Math.PI * 45;

            circle.style.strokeDasharray =
                circumference;

            circle.style.strokeDashoffset =
                circumference -
                (percent / 100) *
                    circumference;
        });
    }

    /* =========================================================
       SEARCH
       ========================================================= */

    async function searchFiles(query) {
        const searchQuery =
            String(query || "").trim();

        if (!searchQuery) {
            await loadFiles();
            return;
        }

        try {
            const data =
                await apiRequest(
                    `/search?query=${encodeURIComponent(
                        searchQuery
                    )}`,
                    {
                        method: "GET",
                        headers: authHeaders()
                    }
                );

            const files =
                data.files || [];

            renderMyFiles(files);
            renderRecentFiles(files);

            const filesView =
                document.getElementById(
                    "view-files"
                );

            if (
                filesView &&
                typeof window.switchView ===
                    "function"
            ) {
                window.switchView(
                    "files",
                    true
                );
            }

        } catch (error) {
            console.error(
                "Search error:",
                error
            );

            showToast(
                error.message ||
                "Search failed.",
                "error"
            );
        }
    }

    /* =========================================================
       FILTERS
       ========================================================= */

    function applyFiltersFiles() {
        /*
         * The complete file list is refreshed from backend.
         * This keeps the implementation reliable.
         */
        loadFiles();
    }

    function applyFiltersRecent() {
        loadFiles();
    }

    function applyFiltersShared() {
        loadSharedFiles();
    }

    /* =========================================================
       DRAG & DROP
       ========================================================= */

    function initializeUploadEvents() {
        const fileInput =
            getUploadFileInput();

        if (fileInput) {
            fileInput.addEventListener(
                "change",
                handleFileSelection
            );
        }

        const dropZone =
            document.getElementById(
                "uploadDropZone"
            );

        if (!dropZone) {
            return;
        }

        [
            "dragenter",
            "dragover"
        ].forEach(eventName => {
            dropZone.addEventListener(
                eventName,
                event => {
                    event.preventDefault();
                    event.stopPropagation();

                    dropZone.classList.add(
                        "drag-active"
                    );
                }
            );
        });

        [
            "dragleave",
            "drop"
        ].forEach(eventName => {
            dropZone.addEventListener(
                eventName,
                event => {
                    event.preventDefault();
                    event.stopPropagation();

                    dropZone.classList.remove(
                        "drag-active"
                    );
                }
            );
        });

        dropZone.addEventListener(
            "drop",
            event => {
                const files =
                    event.dataTransfer.files;

                if (
                    files &&
                    files.length
                ) {
                    /*
                     * Assign dropped file to
                     * the actual file input.
                     */
                    try {
                        const dataTransfer =
                            new DataTransfer();

                        dataTransfer.items.add(
                            files[0]
                        );

                        const input =
                            getUploadFileInput();

                        if (input) {
                            input.files =
                                dataTransfer.files;

                            updateSelectedFileUI(
                                files[0]
                            );
                        }

                    } catch (error) {
                        console.error(
                            "Drag/drop error:",
                            error
                        );
                    }
                }
            }
        );
    }

    /* =========================================================
       INITIALIZATION
       ========================================================= */

    function initializeUploadJS() {
        console.log(
            "SnapDrive upload.js initialized."
        );

        console.log(
            "SnapDrive API:",
            getApiBase()
        );

        initializeUploadEvents();
    }

    if (
        document.readyState ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initializeUploadJS
        );
    } else {
        initializeUploadJS();
    }

    /* =========================================================
       EXPORT FUNCTIONS TO WINDOW
       ========================================================= */

    window.loadDashboardData =
        loadDashboardData;

    window.loadFiles =
        loadFiles;

    window.renderMyFiles =
        renderMyFiles;

    window.renderRecentFiles =
        renderRecentFiles;

    window.viewFile =
        viewFile;

    window.downloadFile =
        downloadFile;

    window.deleteFile =
        deleteFile;

    window.performDeleteFile =
        performDeleteFile;

    window.openUploadModal =
        openUploadModal;

    window.closeUploadModal =
        closeUploadModal;

    window.submitModalUpload =
        submitModalUpload;

    window.setUploadTab =
        setUploadTab;

    window.openFolderModal =
        openFolderModal;

    window.closeFolderModal =
        closeFolderModal;

    window.createFolder =
        createFolder;

    window.loadFolders =
        loadFolders;

    window.loadSharedFiles =
        loadSharedFiles;

    window.loadSharedByMe =
        loadSharedByMe;

    window.renderSharedFiles =
        renderSharedFiles;

    window.renderSharedByMe =
        renderSharedByMe;

    window.setSharedSubView =
        setSharedSubView;

    window.revokeShare =
        revokeShare;

    window.loadNotifications =
        loadNotifications;

    window.markNotificationRead =
        markNotificationRead;

    window.markAllNotificationsAsRead =
        markAllNotificationsAsRead;

    window.loadActivities =
        loadActivities;

    window.renderActivityList =
        renderActivityList;

    window.loadStorageDetails =
        loadStorageDetails;

    window.searchFiles =
        searchFiles;

    window.applyFiltersFiles =
        applyFiltersFiles;

    window.applyFiltersRecent =
        applyFiltersRecent;

    window.applyFiltersShared =
        applyFiltersShared;
})();