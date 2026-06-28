async function registerUser() {
    const btn = document.getElementById('registerBtn');
    const btnText = document.getElementById('btnText');
    
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (!username || !email || !password) {
        showToast("Please fill all fields", "error");
        return;
    }

    try {
        btn.disabled = true;
        btnText.innerHTML = '<span class="spinner"></span>Registering...';

        const response = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showToast("Account created successfully! Redirecting to login...", "success");
            setTimeout(() => window.location.href = "login.html", 2000);
        } else {
            showToast(data.detail || "Registration failed", "error");
        }
    } catch (err) {
        showToast("Server connection error", "error");
    } finally {
        btn.disabled = false;
        if (btnText) btnText.innerText = 'Create Account';
        else btn.innerText = 'Create Account';
    }
}

async function login() {
    const btn = document.getElementById('loginBtn');
    const btnText = document.getElementById('btnText');
    
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (!email || !password) {
        showToast("Please enter email and password", "error");
        return;
    }

    try {
        btn.disabled = true;
        btnText.innerHTML = '<span class="spinner"></span>Signing In...';

        const response = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem("token", JSON.stringify({
                access_token: data.access_token,
                token_type: data.token_type,
                user_id: data.user_id
            }));
            localStorage.setItem("userId", data.user_id);
            localStorage.setItem("username", data.username);
            localStorage.setItem("email", data.email);
            
            showToast("Login successful!", "success");
            setTimeout(() => window.location.href = "dashboard.html", 1000);
        } else {
            showToast(data.detail || "Invalid credentials", "error");
        }
    } catch (err) {
        showToast("Server connection error", "error");
    } finally {
        btn.disabled = false;
        if (btnText) btnText.innerText = 'Sign In';
        else btn.innerText = 'Sign In';
    }
}

async function forgotPassword() {
    const btn = document.getElementById('forgotBtn');
    const btnText = document.getElementById('forgotBtnText');
    
    const email = document.getElementById('forgotEmail').value;
    const newPassword = document.getElementById('forgotNewPassword').value;
    const confirmPassword = document.getElementById('forgotConfirmPassword').value;

    if (!email || !newPassword || !confirmPassword) {
        showToast("Please fill all fields", "error");
        return;
    }

    if (newPassword.length < 6) {
        showToast("Password must be at least 6 characters", "error");
        return;
    }

    if (newPassword !== confirmPassword) {
        showToast("Passwords do not match", "error");
        return;
    }

    try {
        btn.disabled = true;
        btnText.innerHTML = '<span class="spinner"></span>Resetting...';

        const response = await fetch(`${API_BASE}/auth/forgot-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, new_password: newPassword })
        });

        const data = await response.json();

        if (response.ok) {
            showToast("Password reset successfully! You can now sign in.", "success");
            closeForgotPasswordModal();
        } else {
            showToast(data.detail || "Password reset failed", "error");
        }
    } catch (err) {
        showToast("Server connection error", "error");
    } finally {
        btn.disabled = false;
        if (btnText) btnText.innerText = 'Reset Password';
    }
}

function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}
 