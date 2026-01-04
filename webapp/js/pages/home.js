/**
 * Home Page Logic
 * Displays user info and tools list
 */

let allTools = [];
let filteredTools = [];
let currentCategory = 'all';
let currentUser = null;

// Initialize page
window.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (!isAuthenticated()) {
        window.location.href = '../index.html';
        return;
    }

    // Load data
    await loadUserInfo();
    await loadTools();
    await loadJobStats();
});

// Load user information
async function loadUserInfo() {
    try {
        const user = await apiRequest(API.me);
        currentUser = user;

        // Update UI
        const avatarEl = document.getElementById('user-avatar');
        const nameEl = document.getElementById('user-name');
        const emailEl = document.getElementById('user-email');

        // Set avatar (first letter of username)
        avatarEl.textContent = user.username.charAt(0).toUpperCase();

        // Set name and role
        nameEl.innerHTML = `${user.full_name || user.username} <span class="user-role ${user.role}">${getRoleDisplayName(user.role)}</span>`;

        // Set email
        emailEl.textContent = user.email;

        // Show admin button if admin
        if (user.role === 'admin') {
            document.getElementById('admin-btn').style.display = 'inline-block';
        }

    } catch (error) {
        console.error('Failed to load user info:', error);
        // Token might be invalid, redirect to login
        clearAuth();
        window.location.href = '../index.html';
    }
}

// Load tools from API
async function loadTools() {
    try {
        const tools = await apiRequest(API.tools);
        allTools = tools;
        filteredTools = tools;

        // Update stats
        document.getElementById('total-tools').textContent = tools.length;

        // Extract and display categories
        const categories = [...new Set(tools.map(t => t.category || 'other'))];
        document.getElementById('total-categories').textContent = categories.length;

        displayCategoryFilters(categories);
        displayTools(tools);

        // Hide loading, show grid
        document.getElementById('loading').style.display = 'none';
        document.getElementById('tools-grid').style.display = 'grid';

    } catch (error) {
        console.error('Failed to load tools:', error);
        document.getElementById('loading').innerHTML = `
            <p style="color: #e74c3c;">❌ Ошибка загрузки инструментов: ${error.message}</p>
        `;
    }
}

// Load job statistics
async function loadJobStats() {
    try {
        const jobs = await apiRequest(API.jobs);
        const completedJobs = jobs.filter(j => j.status === 'completed').length;
        document.getElementById('completed-jobs').textContent = completedJobs;
    } catch (error) {
        console.error('Failed to load job stats:', error);
        // Non-critical, just keep at 0
    }
}

// Display category filters
function displayCategoryFilters(categories) {
    const filtersContainer = document.getElementById('category-filters');

    // Keep "All" button
    const allButton = filtersContainer.querySelector('[data-category="all"]');
    filtersContainer.innerHTML = '';
    filtersContainer.appendChild(allButton);

    // Add category buttons
    categories.sort().forEach(category => {
        const btn = document.createElement('button');
        btn.className = 'category-btn';
        btn.dataset.category = category;
        btn.textContent = getCategoryDisplayName(category);
        btn.onclick = () => filterByCategory(category);
        filtersContainer.appendChild(btn);
    });
}

// Display tools in grid
function displayTools(tools) {
    const gridEl = document.getElementById('tools-grid');
    const noResultsEl = document.getElementById('no-results');

    if (tools.length === 0) {
        gridEl.style.display = 'none';
        noResultsEl.style.display = 'block';
        return;
    }

    noResultsEl.style.display = 'none';
    gridEl.style.display = 'grid';
    gridEl.innerHTML = '';

    tools.forEach(tool => {
        const card = createToolCard(tool);
        gridEl.appendChild(card);
    });
}

// Create tool card element
function createToolCard(tool) {
    const card = document.createElement('div');
    card.className = 'tool-card';
    card.onclick = () => runTool(tool.name);

    const icon = getToolIcon(tool.category);
    const paramsCount = tool.parameters ? Object.keys(tool.parameters).length : 0;
    const requiredParams = tool.parameters
        ? Object.values(tool.parameters).filter(p => p.required).length
        : 0;

    card.innerHTML = `
        <div class="tool-category">${getCategoryDisplayName(tool.category || 'other')}</div>
        <h3>
            <span class="tool-icon">${icon}</span>
            ${tool.display_name || tool.name}
        </h3>
        <p>${tool.description || 'Описание недоступно'}</p>
        <div class="tool-params">
            📝 Параметров: ${paramsCount} ${requiredParams > 0 ? `(${requiredParams} обязательных)` : ''}
        </div>
    `;

    return card;
}

// Filter tools by search query
function filterTools() {
    const searchQuery = document.getElementById('search-input').value.toLowerCase().trim();

    filteredTools = allTools.filter(tool => {
        // Category filter
        if (currentCategory !== 'all' && tool.category !== currentCategory) {
            return false;
        }

        // Search filter
        if (searchQuery) {
            const name = (tool.display_name || tool.name).toLowerCase();
            const description = (tool.description || '').toLowerCase();
            const category = (tool.category || '').toLowerCase();

            return name.includes(searchQuery) ||
                   description.includes(searchQuery) ||
                   category.includes(searchQuery);
        }

        return true;
    });

    displayTools(filteredTools);
}

// Filter by category
function filterByCategory(category) {
    currentCategory = category;

    // Update active button
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.category === category) {
            btn.classList.add('active');
        }
    });

    filterTools();
}

// Navigate to tool run page
function runTool(toolName) {
    window.location.href = `run-tool.html?tool=${encodeURIComponent(toolName)}`;
}

// Logout handler
function handleLogout() {
    if (confirm('Вы уверены, что хотите выйти?')) {
        clearAuth();
        window.location.href = '../index.html';
    }
}

// Helper: Get role display name
function getRoleDisplayName(role) {
    const roleMap = {
        'admin': '👑 Администратор',
        'user': '👤 Пользователь',
        'guest': '👥 Гость'
    };
    return roleMap[role] || role;
}

// Helper: Get category display name
function getCategoryDisplayName(category) {
    const categoryMap = {
        'statistics': '📊 Статистика',
        'visualization': '📈 Визуализация',
        'cleaning': '🧹 Очистка данных',
        'transformation': '🔄 Преобразование',
        'analysis': '🔍 Анализ',
        'ml': '🤖 Машинное обучение',
        'nlp': '💬 NLP',
        'timeseries': '⏰ Временные ряды',
        'text': '📝 Текст',
        'network': '🌐 Сети',
        'other': '🔧 Другое'
    };
    return categoryMap[category] || category;
}

// Helper: Get tool icon based on category
function getToolIcon(category) {
    const iconMap = {
        'statistics': '📊',
        'visualization': '📈',
        'cleaning': '🧹',
        'transformation': '🔄',
        'analysis': '🔍',
        'ml': '🤖',
        'nlp': '💬',
        'timeseries': '⏰',
        'text': '📝',
        'network': '🌐',
        'other': '🔧'
    };
    return iconMap[category] || '🔧';
}
