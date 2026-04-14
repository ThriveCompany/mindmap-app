const API_BASE = window.MINDMAP_API_BASE || 'https://mindmap-backend-gys8.onrender.com';

// Utility functions
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.style.display = 'block';
    animateCardError();
}

function hideError(elementId) {
    const element = document.getElementById(elementId);
    element.style.display = 'none';
}

function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.style.display = 'block';
    animateCardSuccess();
}

function hideSuccess(elementId) {
    const element = document.getElementById(elementId);
    element.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    document.body.classList.add('page-ready');
});

function animateCardSuccess() {
    const card = document.querySelector('.glass-card');
    if (!card) return;
    card.classList.add('success-glow');
    setTimeout(() => card.classList.remove('success-glow'), 1100);
}

function animateCardError() {
    const card = document.querySelector('.glass-card');
    if (!card) return;
    card.classList.remove('shake');
    void card.offsetWidth;
    card.classList.add('shake');
}

function saveToken(token) {
    localStorage.setItem('token', token);
}

function clearToken() {
    localStorage.removeItem('token');
}

function getToken() {
    return localStorage.getItem('token');
}

function redirectToDashboard() {
    window.location.href = 'dashboard.html';
}

function redirectToLogin() {
    window.location.href = 'login.html';
}

function checkAuth() {
    const token = getToken();
    if (!token) {
        redirectToLogin();
        return false;
    }
    return true;
}

function getAuthHeaders(headers = {}) {
    const token = getToken();
    if (!token) {
        return headers;
    }
    return {
        ...headers,
        Authorization: `Bearer ${token}`,
    };
}

async function getErrorMessage(response, fallbackMessage) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        try {
            const error = await response.json();
            return error.detail || error.message || fallbackMessage;
        } catch (parseError) {
            return fallbackMessage;
        }
    }
    return fallbackMessage;
}

async function authFetch(path, options = {}) {
    const headers = getAuthHeaders(options.headers || {});
    const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        clearToken();
        redirectToLogin();
        throw new Error('Your session has expired. Please log in again.');
    }

    return response;
}

async function fetchCurrentUser() {
    const response = await authFetch('/me');
    if (!response.ok) {
        throw new Error(await getErrorMessage(response, 'Unable to load your profile.'));
    }
    return response.json();
}

// Signup function
async function signup(username, password, confirmPassword) {
    if (password !== confirmPassword) {
        showError('signup-error', 'Passwords do not match');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        if (response.ok) {
            showSuccess('signup-success', `Account created for ${username}. Redirecting to login…`);
            setTimeout(() => {
                redirectToLogin();
            }, 1200);
        } else {
            showError('signup-error', await getErrorMessage(response, 'Signup failed'));
        }
    } catch (error) {
        showError('signup-error', 'Network error. Please try again.');
    }
}

// Login function
async function login(username, password) {
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        if (response.ok) {
            const data = await response.json();
            saveToken(data.access_token);
            showSuccess('login-success', `Welcome back, ${username}! Redirecting to your dashboard…`);
            setTimeout(() => {
                redirectToDashboard();
            }, 900);
        } else {
            showError('login-error', await getErrorMessage(response, 'Login failed'));
        }
    } catch (error) {
        showError('login-error', 'Network error. Please try again.');
    }
}

// Logout function
function logout() {
    clearToken();
    redirectToLogin();
}
