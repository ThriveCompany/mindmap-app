// API base URL - change this to your backend URL
const API_BASE = 'https://mindmap-backend-gys8.onrender.com';

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

function getToken() {
    return localStorage.getItem('token');
}

function redirectToDashboard() {
    window.location.href = 'dashboard.html';
}

function checkAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    // Optionally verify token with /me endpoint
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
                window.location.href = 'login.html';
            }, 1200);
        } else {
            const error = await response.json();
            showError('signup-error', error.detail || 'Signup failed');
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
            const error = await response.json();
            showError('login-error', error.detail || 'Login failed');
        }
    } catch (error) {
        showError('login-error', 'Network error. Please try again.');
    }
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    window.location.href = 'login.html';
}