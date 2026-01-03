/**
 * Authentication Logic
 * Login and Registration handlers
 */

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');

    // Clear error messages
    document.getElementById('login-error').style.display = 'none';
    document.getElementById('register-error').style.display = 'none';
    document.getElementById('register-success').style.display = 'none';
}

// Handle Login
async function handleLogin(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const errorEl = document.getElementById('login-error');

    // Hide previous errors
    errorEl.style.display = 'none';

    // Get form data
    const username = form.username.value.trim();
    const password = form.password.value;

    // Validation
    if (!username || !password) {
        showError('login-error', 'Заполните все поля');
        return;
    }

    // Set loading state
    setLoading(submitBtn, true);

    try {
        // Call login API
        const response = await apiRequest(API.login, {
            method: 'POST',
            body: JSON.stringify({ username, password }),
            noAuth: true,
        });

        // Save tokens
        setToken(response.access_token, response.refresh_token);

        // Get user info
        const user = await apiRequest(API.me);
        setUser(user);

        // Redirect to home page
        window.location.href = 'pages/home.html';

    } catch (error) {
        console.error('Login error:', error);
        showError('login-error', error.message || 'Ошибка входа. Проверьте логин и пароль.');
        setLoading(submitBtn, false);
    }
}

// Handle Registration
async function handleRegister(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const errorEl = document.getElementById('register-error');
    const successEl = document.getElementById('register-success');

    // Hide previous messages
    errorEl.style.display = 'none';
    successEl.style.display = 'none';

    // Get form data
    const username = form.username.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;
    const full_name = form.full_name.value.trim() || null;

    // Validation
    if (!username || !email || !password) {
        showError('register-error', 'Заполните все обязательные поля');
        return;
    }

    if (username.length < 3) {
        showError('register-error', 'Логин должен быть минимум 3 символа');
        return;
    }

    if (password.length < 8) {
        showError('register-error', 'Пароль должен быть минимум 8 символов');
        return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showError('register-error', 'Введите корректный email');
        return;
    }

    // Set loading state
    setLoading(submitBtn, true);

    try {
        // Call register API
        const user = await apiRequest(API.register, {
            method: 'POST',
            body: JSON.stringify({ username, email, password, full_name }),
            noAuth: true,
        });

        // Show success message
        showSuccess('register-success',
            `Регистрация успешна! ${user.role === 'admin' ? '👑 Вы - администратор!' : ''} Теперь войдите в систему.`
        );

        // Clear form
        form.reset();

        // Auto-switch to login tab after 2 seconds
        setTimeout(() => {
            showTab('login');
            // Pre-fill username
            document.getElementById('login-username').value = username;
        }, 2000);

    } catch (error) {
        console.error('Registration error:', error);

        let errorMessage = 'Ошибка регистрации';
        if (error.message.includes('Username already registered')) {
            errorMessage = 'Этот логин уже занят';
        } else if (error.message.includes('Email already registered')) {
            errorMessage = 'Этот email уже зарегистрирован';
        } else if (error.message.includes('at least 8 characters')) {
            errorMessage = 'Пароль должен быть минимум 8 символов';
        } else {
            errorMessage = error.message;
        }

        showError('register-error', errorMessage);
    } finally {
        setLoading(submitBtn, false);
    }
}

// Check if already logged in
window.addEventListener('DOMContentLoaded', () => {
    if (isAuthenticated()) {
        // Verify token is valid
        apiRequest(API.me)
            .then(() => {
                // Token valid, redirect to home
                window.location.href = 'pages/home.html';
            })
            .catch(() => {
                // Token invalid, clear and stay on login page
                clearAuth();
            });
    }
});
