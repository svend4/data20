/**
 * Tool Runner UI - Frontend для запуска инструментов
 * Phase 4.4: Interactive UI for all 57 tools
 */

class ToolRunnerUI {
    constructor() {
        this.apiAvailable = false;
        this.tools = null;
        this.categories = null;
        this.currentCategory = 'all';
        this.runningJobs = new Map();

        this.init();
    }

    async init() {
        // Проверить доступность API
        const apiStatus = await apiClient.checkAvailability();

        if (apiStatus) {
            this.apiAvailable = true;
            console.log('[Tool Runner] Backend API available:', apiStatus);

            // Подключиться к WebSocket
            apiClient.connectWebSocket();

            // Загрузить инструменты
            await this.loadTools();

            // Показать UI
            this.showToolRunner();
        } else {
            console.log('[Tool Runner] Backend API not available - static mode only');
            this.showStaticMode();
        }
    }

    async loadTools() {
        try {
            this.tools = await apiClient.getTools();
            this.categories = await apiClient.getCategories();

            console.log(`[Tool Runner] Loaded ${this.tools.total_tools} tools in ${Object.keys(this.categories).length} categories`);
        } catch (error) {
            console.error('[Tool Runner] Failed to load tools:', error);
        }
    }

    showToolRunner() {
        // Добавить кнопку "Tool Runner" в навигацию
        const navActions = document.querySelector('.nav-actions');
        if (!navActions) return;

        const runnerButton = document.createElement('button');
        runnerButton.className = 'btn btn-primary';
        runnerButton.innerHTML = '🚀 Run Tools';
        runnerButton.onclick = () => this.openToolRunner();

        navActions.appendChild(runnerButton);

        // Показать индикатор API
        this.updateAPIIndicator(true);
    }

    showStaticMode() {
        this.updateAPIIndicator(false);
    }

    updateAPIIndicator(available) {
        const indicator = document.getElementById('online-status');
        if (!indicator) return;

        if (available) {
            indicator.className = 'status-indicator online';
            indicator.textContent = '🟢 API Online';
            indicator.title = 'Backend API доступен - можно запускать инструменты';
        } else {
            indicator.className = 'status-indicator offline';
            indicator.textContent = '🔵 Static Mode';
            indicator.title = 'Backend API недоступен - только просмотр результатов';
        }
    }

    openToolRunner() {
        // Создать модальное окно с Tool Runner
        const modal = document.createElement('div');
        modal.className = 'tool-runner-modal';
        modal.innerHTML = `
            <div class="tool-runner-container">
                <div class="tool-runner-header">
                    <h2>🚀 Tool Runner</h2>
                    <button class="close-btn" onclick="this.closest('.tool-runner-modal').remove()">✕</button>
                </div>

                <div class="tool-runner-body">
                    <!-- Sidebar с категориями -->
                    <div class="tool-runner-sidebar">
                        <h3>Categories</h3>
                        <div class="category-list" id="category-list">
                            <button class="category-item active" data-category="all">
                                All Tools (${this.tools.total_tools})
                            </button>
                        </div>

                        <div class="running-jobs-section">
                            <h3>Running Jobs</h3>
                            <div id="running-jobs-list"></div>
                        </div>
                    </div>

                    <!-- Список инструментов -->
                    <div class="tool-runner-main">
                        <div class="search-bar">
                            <input type="text" id="tool-search" placeholder="Search tools..." />
                        </div>
                        <div class="tools-grid" id="tools-grid"></div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Заполнить категории
        this.renderCategories();

        // Заполнить инструменты
        this.renderTools();

        // Настроить поиск
        document.getElementById('tool-search').addEventListener('input', (e) => {
            this.searchTools(e.target.value);
        });

        // Закрыть по клику на фон
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    renderCategories() {
        const categoryList = document.getElementById('category-list');

        // Добавить категории
        for (const [categoryName, categoryData] of Object.entries(this.categories)) {
            const button = document.createElement('button');
            button.className = 'category-item';
            button.dataset.category = categoryName;
            button.innerHTML = `
                <span class="category-icon">${this.getCategoryIcon(categoryName)}</span>
                <span class="category-name">${categoryName}</span>
                <span class="category-count">${categoryData.count}</span>
            `;
            button.onclick = () => this.filterByCategory(categoryName);

            categoryList.appendChild(button);
        }
    }

    renderTools(filter = 'all') {
        const grid = document.getElementById('tools-grid');
        grid.innerHTML = '';

        let toolsToRender = [];

        if (filter === 'all') {
            toolsToRender = Object.values(this.tools.tools);
        } else {
            const categoryData = this.categories[filter];
            if (categoryData) {
                toolsToRender = categoryData.tools.map(name => this.tools.tools[name]);
            }
        }

        for (const tool of toolsToRender) {
            const card = this.createToolCard(tool);
            grid.appendChild(card);
        }
    }

    createToolCard(tool) {
        const card = document.createElement('div');
        card.className = 'tool-card';
        card.style.borderLeft = `4px solid ${tool.color}`;

        const hasParams = tool.parameters && tool.parameters.length > 0;

        card.innerHTML = `
            <div class="tool-card-header">
                <span class="tool-icon">${tool.icon}</span>
                <h3 class="tool-name">${tool.display_name}</h3>
            </div>
            <p class="tool-description">${tool.description}</p>
            <div class="tool-meta">
                <span class="tool-category">${tool.category}</span>
                <span class="tool-time">~${tool.estimated_time || 10}s</span>
                <span class="tool-complexity complexity-${tool.complexity}">${tool.complexity || 'low'}</span>
            </div>
            <div class="tool-actions">
                ${hasParams ?
                    `<button class="btn btn-secondary btn-sm" onclick="toolRunnerUI.showToolParams('${tool.name}')">
                        ⚙️ Configure
                    </button>` :
                    `<button class="btn btn-primary btn-sm" onclick="toolRunnerUI.runTool('${tool.name}')">
                        ▶️ Run
                    </button>`
                }
                <button class="btn btn-text btn-sm" onclick="toolRunnerUI.showToolInfo('${tool.name}')">
                    ℹ️ Info
                </button>
            </div>
        `;

        return card;
    }

    filterByCategory(category) {
        this.currentCategory = category;

        // Обновить активную категорию
        document.querySelectorAll('.category-item').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.category === category);
        });

        // Перерендерить инструменты
        this.renderTools(category);
    }

    async searchTools(query) {
        if (!query.trim()) {
            this.renderTools(this.currentCategory);
            return;
        }

        try {
            const results = await apiClient.searchTools(query);

            const grid = document.getElementById('tools-grid');
            grid.innerHTML = '';

            if (results.count === 0) {
                grid.innerHTML = '<p class="no-results">No tools found</p>';
                return;
            }

            for (const toolSummary of results.results) {
                const tool = this.tools.tools[toolSummary.name];
                if (tool) {
                    const card = this.createToolCard(tool);
                    grid.appendChild(card);
                }
            }
        } catch (error) {
            console.error('[Tool Runner] Search failed:', error);
        }
    }

    async runTool(toolName, parameters = {}) {
        try {
            console.log(`[Tool Runner] Running ${toolName}...`);

            // Запустить инструмент
            const response = await apiClient.runTool(toolName, parameters);

            console.log(`[Tool Runner] Job started:`, response);

            // Показать прогресс
            this.showJobProgress(response.job_id, toolName);

            // Подписаться на обновления
            apiClient.subscribeToJob(response.job_id, (data) => {
                this.handleJobUpdate(response.job_id, data);
            });

        } catch (error) {
            console.error('[Tool Runner] Failed to run tool:', error);
            alert(`Failed to run ${toolName}: ${error.message}`);
        }
    }

    showJobProgress(jobId, toolName) {
        const runningJobsList = document.getElementById('running-jobs-list');

        const jobCard = document.createElement('div');
        jobCard.className = 'job-progress-card';
        jobCard.id = `job-${jobId}`;
        jobCard.innerHTML = `
            <div class="job-header">
                <strong>${toolName}</strong>
                <button class="btn-icon" onclick="toolRunnerUI.cancelJob('${jobId}')" title="Cancel">
                    ✕
                </button>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
            <div class="job-status">Starting...</div>
        `;

        runningJobsList.appendChild(jobCard);
        this.runningJobs.set(jobId, { toolName, card: jobCard });
    }

    handleJobUpdate(jobId, data) {
        const job = this.runningJobs.get(jobId);
        if (!job) return;

        const { card } = job;
        const progressFill = card.querySelector('.progress-fill');
        const statusText = card.querySelector('.job-status');

        if (data.type === 'progress') {
            progressFill.style.width = `${data.progress}%`;
            statusText.textContent = data.message;
        } else if (data.type === 'complete') {
            progressFill.style.width = '100%';
            progressFill.style.background = data.status === 'completed' ? '#27ae60' : '#e74c3c';

            if (data.status === 'completed') {
                statusText.innerHTML = `
                    ✅ Completed in ${data.duration?.toFixed(1)}s
                    <br>
                    <small>Files: ${data.output_files.join(', ')}</small>
                `;

                // Автоматически удалить через 5 секунд
                setTimeout(() => {
                    card.style.animation = 'slideOut 0.3s ease-out';
                    setTimeout(() => {
                        card.remove();
                        this.runningJobs.delete(jobId);
                    }, 300);
                }, 5000);
            } else if (data.status === 'failed') {
                statusText.innerHTML = `❌ Failed: ${data.error}`;
            }
        }
    }

    async cancelJob(jobId) {
        try {
            await apiClient.cancelJob(jobId);

            const job = this.runningJobs.get(jobId);
            if (job) {
                job.card.remove();
                this.runningJobs.delete(jobId);
            }
        } catch (error) {
            console.error('[Tool Runner] Failed to cancel job:', error);
        }
    }

    showToolParams(toolName) {
        const tool = this.tools.tools[toolName];

        // Создать форму параметров
        const modal = document.createElement('div');
        modal.className = 'tool-params-modal';
        modal.innerHTML = `
            <div class="params-container">
                <h2>⚙️ Configure ${tool.display_name}</h2>
                <form id="tool-params-form">
                    ${tool.parameters.map(param => this.createParameterField(param)).join('')}
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">▶️ Run Tool</button>
                        <button type="button" class="btn btn-secondary" onclick="this.closest('.tool-params-modal').remove()">
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);

        // Обработать submit
        document.getElementById('tool-params-form').onsubmit = (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const parameters = {};

            for (const [key, value] of formData.entries()) {
                parameters[key] = value;
            }

            this.runTool(toolName, parameters);
            modal.remove();
        };

        // Закрыть по клику на фон
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    createParameterField(param) {
        let inputHTML = '';

        if (param.choices) {
            // Select dropdown
            inputHTML = `
                <select name="${param.name}" ${param.required ? 'required' : ''}>
                    ${param.choices.map(choice =>
                        `<option value="${choice}">${choice}</option>`
                    ).join('')}
                </select>
            `;
        } else if (param.type === 'bool') {
            // Checkbox
            inputHTML = `
                <input type="checkbox" name="${param.name}" ${param.default ? 'checked' : ''} />
            `;
        } else if (param.type === 'int') {
            // Number input
            inputHTML = `
                <input type="number" name="${param.name}"
                       value="${param.default || ''}"
                       ${param.required ? 'required' : ''} />
            `;
        } else {
            // Text input
            inputHTML = `
                <input type="text" name="${param.name}"
                       value="${param.default || ''}"
                       ${param.required ? 'required' : ''}
                       placeholder="${param.description}" />
            `;
        }

        return `
            <div class="form-group">
                <label>
                    ${param.name}
                    ${param.required ? '<span class="required">*</span>' : ''}
                </label>
                ${inputHTML}
                ${param.description ? `<small>${param.description}</small>` : ''}
            </div>
        `;
    }

    showToolInfo(toolName) {
        const tool = this.tools.tools[toolName];

        const modal = document.createElement('div');
        modal.className = 'tool-info-modal';
        modal.innerHTML = `
            <div class="info-container">
                <h2>${tool.icon} ${tool.display_name}</h2>
                <p>${tool.description}</p>

                <div class="info-section">
                    <h3>Details</h3>
                    <table>
                        <tr><td>Category:</td><td>${tool.category}</td></tr>
                        <tr><td>Complexity:</td><td>${tool.complexity}</td></tr>
                        <tr><td>Estimated Time:</td><td>~${tool.estimated_time}s</td></tr>
                        <tr><td>Output Formats:</td><td>${tool.output_formats.join(', ')}</td></tr>
                    </table>
                </div>

                ${tool.parameters.length > 0 ? `
                    <div class="info-section">
                        <h3>Parameters</h3>
                        <ul>
                            ${tool.parameters.map(p =>
                                `<li><strong>${p.name}</strong> (${p.type}${p.required ? ', required' : ''}): ${p.description}</li>`
                            ).join('')}
                        </ul>
                    </div>
                ` : ''}

                <button class="btn btn-primary" onclick="this.closest('.tool-info-modal').remove()">
                    Close
                </button>
            </div>
        `;

        document.body.appendChild(modal);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    getCategoryIcon(category) {
        const icons = {
            'graph': '🕸️',
            'visualization': '📊',
            'indexing': '📇',
            'search': '🔍',
            'analysis': '📈',
            'metadata': '🏷️',
            'export': '📤',
            'validation': '✅',
            'statistics': '📊',
            'other': '🔧'
        };
        return icons[category] || '🔧';
    }
}

// Auto-initialize
let toolRunnerUI;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        toolRunnerUI = new ToolRunnerUI();
    });
} else {
    toolRunnerUI = new ToolRunnerUI();
}
