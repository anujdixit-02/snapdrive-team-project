/* =========================================================
   SNAPDRIVE API CONFIGURATION
   ========================================================= */

const API_BASE = "http://127.0.0.1:8000";


/* =========================================================
   GET AUTH TOKEN
   ========================================================= */

function getToken() {

    return localStorage.getItem("token");

}


/* =========================================================
   AUTH HEADERS
   ========================================================= */

function getAuthHeaders() {

    const token = getToken();

    if (!token) {

        return {};

    }

    return {

        "Authorization": "Bearer " + token

    };

}


/* =========================================================
   AUTH FETCH
   ========================================================= */

async function apiFetch(
    endpoint,
    options = {}
) {

    const headers = {

        ...getAuthHeaders(),

        ...(options.headers || {})

    };


    const response = await fetch(

        API_BASE + endpoint,

        {

            ...options,

            headers

        }

    );


    if (response.status === 401) {

        localStorage.removeItem("token");

        localStorage.removeItem("username");

        localStorage.removeItem("email");

        window.location.href = "login.html";

        return null;

    }


    return response;

}


/* =========================================================
   JSON API HELPER
   ========================================================= */

async function apiJSON(
    endpoint,
    options = {}
) {

    const response =
        await apiFetch(
            endpoint,
            options
        );


    if (!response) {

        return null;

    }


    const text =
        await response.text();


    let data = null;


    try {

        data =
            text
                ? JSON.parse(text)
                : null;

    } catch {

        data = {

            detail: text

        };

    }


    if (!response.ok) {

        const message =
            data?.detail ||
            data?.message ||
            `HTTP ${response.status}`;

        throw new Error(message);

    }


    return data;

}


/* =========================================================
   FILE SIZE FORMATTER
   ========================================================= */

function formatFileSize(bytes) {

    if (
        bytes === null ||
        bytes === undefined ||
        isNaN(bytes)
    ) {

        return "0 B";

    }


    bytes = Number(bytes);


    if (bytes === 0) {

        return "0 B";

    }


    const units = [

        "B",
        "KB",
        "MB",
        "GB",
        "TB"

    ];


    const index =
        Math.floor(
            Math.log(bytes) /
            Math.log(1024)
        );


    const value =
        bytes /
        Math.pow(
            1024,
            index
        );


    return (
        value.toFixed(
            index === 0 ? 0 : 2
        ) +
        " " +
        units[index]
    );

}


/* =========================================================
   DATE FORMATTER
   ========================================================= */

function formatDate(dateValue) {

    if (!dateValue) {

        return "-";

    }


    const date =
        new Date(dateValue);


    if (isNaN(date.getTime())) {

        return "-";

    }


    return date.toLocaleString(
        undefined,
        {

            day: "2-digit",

            month: "short",

            year: "numeric",

            hour: "2-digit",

            minute: "2-digit"

        }
    );

}


/* =========================================================
   HTML ESCAPE
   ========================================================= */

function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}


/* =========================================================
   FILE EXTENSION
   ========================================================= */

function getFileExtension(filename) {

    if (!filename) {

        return "";

    }


    const parts =
        filename.split(".");


    if (parts.length < 2) {

        return "";

    }


    return parts
        .pop()
        .toLowerCase();

}


/* =========================================================
   FILE TYPE
   ========================================================= */

function getFileCategory(filename) {

    const extension =
        getFileExtension(filename);


    if (
        [
            "jpg",
            "jpeg",
            "png",
            "gif",
            "webp"
        ].includes(extension)
    ) {

        return "image";

    }


    if (
        [
            "mp4",
            "webm",
            "mov",
            "avi"
        ].includes(extension)
    ) {

        return "video";

    }


    if (
        [
            "pdf"
        ].includes(extension)
    ) {

        return "pdf";

    }


    if (
        [
            "doc",
            "docx",
            "txt"
        ].includes(extension)
    ) {

        return "document";

    }


    if (
        [
            "zip",
            "rar",
            "7z"
        ].includes(extension)
    ) {

        return "archive";

    }


    return "other";

}