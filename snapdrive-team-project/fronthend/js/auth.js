// ============================================================
// SnapDrive - Authentication JavaScript
// ============================================================

const AUTH_API_BASE = window.location.origin;


// ============================================================
// Helper: Show message on login page
// ============================================================

function showAuthMessage(message, type = "error") {
    const messageBox =
        document.getElementById("authMessage") ||
        document.getElementById("loginMessage") ||
        document.getElementById("message");

    if (!messageBox) {
        console.error(message);
        return;
    }

    messageBox.textContent = message;
    messageBox.style.display = "block";

    if (type === "success") {
        messageBox.style.color = "#16a34a";
        messageBox.style.background = "#f0fdf4";
        messageBox.style.border = "1px solid #bbf7d0";
    } else {
        messageBox.style.color = "#dc2626";
        messageBox.style.background = "#fef2f2";
        messageBox.style.border = "1px solid #fecaca";
    }
}


// ============================================================
// Helper: Hide message
// ============================================================

function hideAuthMessage() {
    const messageBox =
        document.getElementById("authMessage") ||
        document.getElementById("loginMessage") ||
        document.getElementById("message");

    if (messageBox) {
        messageBox.style.display = "none";
        messageBox.textContent = "";
    }
}


// ============================================================
// Helper: Set login button loading state
// ============================================================

function setLoginLoading(isLoading) {

    const button =
        document.getElementById("loginBtn") ||
        document.querySelector('button[type="submit"]');

    if (!button) {
        return;
    }

    if (isLoading) {
        button.disabled = true;

        if (!button.dataset.originalText) {
            button.dataset.originalText = button.textContent;
        }

        button.textContent = "Signing In...";
    } else {
        button.disabled = false;

        if (button.dataset.originalText) {
            button.textContent = button.dataset.originalText;
        } else {
            button.textContent = "Sign In";
        }
    }
}


// ============================================================
// LOGIN
// ============================================================

async function login(event) {

    // IMPORTANT:
    // Prevent form submission if event exists.
    // This fixes:
    // "Cannot read properties of undefined (reading preventDefault)"
    if (event && typeof event.preventDefault === "function") {
        event.preventDefault();
    }

    hideAuthMessage();

    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");

    if (!emailInput || !passwordInput) {
        showAuthMessage(
            "Login form fields were not found. Please check the email and password input IDs."
        );
        return false;
    }

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    // --------------------------------------------------------
    // Validation
    // --------------------------------------------------------

    if (!email) {
        showAuthMessage("Please enter your email address.");
        emailInput.focus();
        return false;
    }

    if (!password) {
        showAuthMessage("Please enter your password.");
        passwordInput.focus();
        return false;
    }

    setLoginLoading(true);

    try {

        // ----------------------------------------------------
        // Send login request
        // ----------------------------------------------------

        const response = await fetch(
            AUTH_API_BASE + "/auth/login",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                }),

                cache: "no-store"
            }
        );

        // ----------------------------------------------------
        // Read response safely
        // ----------------------------------------------------

        const responseText = await response.text();

        console.log(
            "POST /auth/login:",
            response.status,
            responseText
        );

        let data = {};

        try {
            data = responseText
                ? JSON.parse(responseText)
                : {};
        } catch (jsonError) {

            console.error(
                "Login response was not valid JSON:",
                responseText
            );

            throw new Error(
                "The server returned an invalid response."
            );
        }

        // ----------------------------------------------------
        // Handle failed login
        // ----------------------------------------------------

        if (!response.ok) {

            let errorMessage = "Login failed.";

            if (data.detail) {

                if (typeof data.detail === "string") {
                    errorMessage = data.detail;
                }

                else if (Array.isArray(data.detail)) {

                    errorMessage = data.detail
                        .map(error => {
                            if (typeof error === "string") {
                                return error;
                            }

                            if (error.msg) {
                                return error.msg;
                            }

                            return JSON.stringify(error);
                        })
                        .join(", ");
                }

                else {
                    errorMessage = JSON.stringify(data.detail);
                }
            }

            throw new Error(
                errorMessage +
                " (HTTP " +
                response.status +
                ")"
            );
        }

        // ----------------------------------------------------
        // Get token
        // ----------------------------------------------------

        const token =
            data.access_token ||
            data.token ||
            data.accessToken;

        if (!token) {

            console.error(
                "Login response does not contain a token:",
                data
            );

            throw new Error(
                "Login succeeded, but the server did not return an authentication token."
            );
        }

        // ----------------------------------------------------
        // Store token
        // ----------------------------------------------------

        localStorage.setItem("token", token);

        // Store optional token under common names
        localStorage.setItem("access_token", token);

        // ----------------------------------------------------
        // Store user information if returned
        // ----------------------------------------------------

        if (data.user) {

            if (data.user.username) {
                localStorage.setItem(
                    "username",
                    data.user.username
                );
            }

            if (data.user.email) {
                localStorage.setItem(
                    "email",
                    data.user.email
                );
            }
        }

        if (data.username) {
            localStorage.setItem(
                "username",
                data.username
            );
        }

        if (data.email) {
            localStorage.setItem(
                "email",
                data.email
            );
        }

        // ----------------------------------------------------
        // Verify token by requesting /auth/me
        // ----------------------------------------------------

        try {

            const meResponse = await fetch(
                AUTH_API_BASE + "/auth/me",
                {
                    method: "GET",

                    headers: {
                        "Authorization": "Bearer " + token,
                        "Accept": "application/json"
                    },

                    cache: "no-store"
                }
            );

            const meText = await meResponse.text();

            console.log(
                "GET /auth/me:",
                meResponse.status,
                meText
            );

            if (meResponse.ok) {

                let user = {};

                try {
                    user = meText
                        ? JSON.parse(meText)
                        : {};
                } catch (e) {
                    user = {};
                }

                if (user.username) {
                    localStorage.setItem(
                        "username",
                        user.username
                    );
                }

                if (user.email) {
                    localStorage.setItem(
                        "email",
                        user.email
                    );
                }
            }

        } catch (meError) {

            console.warn(
                "Could not load /auth/me:",
                meError
            );

            // Do not remove the token here.
            // Login itself already succeeded.
        }

        // ----------------------------------------------------
        // Success
        // ----------------------------------------------------

        showAuthMessage(
            "Login successful. Redirecting...",
            "success"
        );

        // Small delay so user can see success message
        setTimeout(() => {

            window.location.href = "dashboard.html";

        }, 500);

        return false;

    } catch (error) {

        console.error(
            "Login error:",
            error
        );

        showAuthMessage(
            error.message || "Unable to login. Please try again."
        );

        // Remove potentially invalid token
        localStorage.removeItem("token");
        localStorage.removeItem("access_token");

        return false;

    } finally {

        setLoginLoading(false);
    }
}


// ============================================================
// LOGOUT
// ============================================================

function logout() {

    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    localStorage.removeItem("email");

    sessionStorage.clear();

    window.location.href = "login.html";
}


// ============================================================
// CHECK LOGIN STATUS
// ============================================================

function isLoggedIn() {

    const token = localStorage.getItem("token");

    return !!token;
}


// ============================================================
// GET CURRENT USER
// ============================================================

async function getCurrentUser() {

    const token = localStorage.getItem("token");

    if (!token) {
        return null;
    }

    try {

        const response = await fetch(
            AUTH_API_BASE + "/auth/me",
            {
                method: "GET",

                headers: {
                    "Authorization": "Bearer " + token,
                    "Accept": "application/json"
                },

                cache: "no-store"
            }
        );

        if (!response.ok) {

            if (
                response.status === 401 ||
                response.status === 403
            ) {

                localStorage.removeItem("token");
                localStorage.removeItem("access_token");
                localStorage.removeItem("username");
                localStorage.removeItem("email");
            }

            return null;
        }

        const user = await response.json();

        if (user.username) {
            localStorage.setItem(
                "username",
                user.username
            );
        }

        if (user.email) {
            localStorage.setItem(
                "email",
                user.email
            );
        }

        return user;

    } catch (error) {

        console.error(
            "getCurrentUser error:",
            error
        );

        return null;
    }
}


// ============================================================
// PROTECT DASHBOARD
// ============================================================

async function requireLogin() {

    const token = localStorage.getItem("token");

    if (!token) {

        window.location.href = "login.html";

        return null;
    }

    const user = await getCurrentUser();

    if (!user) {

        localStorage.removeItem("token");
        localStorage.removeItem("access_token");

        window.location.href = "login.html";

        return null;
    }

    return user;
}


// ============================================================
// AUTO LOGIN FORM HANDLER
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    const loginForm = document.getElementById("loginForm");

    if (loginForm) {

        loginForm.addEventListener(
            "submit",
            login
        );
    }

});


// ============================================================
// MAKE FUNCTIONS AVAILABLE TO INLINE HTML
// ============================================================

window.login = login;
window.logout = logout;
window.isLoggedIn = isLoggedIn;
window.getCurrentUser = getCurrentUser;
window.requireLogin = requireLogin;