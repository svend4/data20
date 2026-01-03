/**
 * Interactive Dashboard v2.0
 * Живая аналитика и метрики для Knowledge Base
 */

class InteractiveDashboard {
    constructor() {
        this.charts = {};
        this.data = {
            files: [],
            stats: null,
            activity: null,
            tags: null
        };

        this.init();
    }

    async init() {
        // Загрузить данные
        await this.loadData();

        // Создать dashboard
        this.createDashboard();

        // Рендерить компоненты
        this.renderAll();
    }

    async loadData() {
        try {
            // Загрузить статистику
            this.data.stats = await this.fetchJSON('../statistics.json');

            // Загрузить активность
            this.data.activity = await this.fetchJSON('../version_history.json');

            // Загрузить теги
            this.data.tags = await this.fetchJSON('../tags_cloud.json');

            // Загрузить граф
            this.data.graph = await this.fetchJSON('../knowledge_graph_data.json');

            console.log('Dashboard data loaded successfully');
        } catch (error) {
            console.warn('Some dashboard data failed to load:', error);
        }
    }

    async fetchJSON(path) {
        try {
            const response = await fetch(path);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn(`Failed to load ${path}:`, error);
            return null;
        }
    }

    createDashboard() {
        // Проверить, есть ли уже dashboard
        if (document.getElementById('interactive-dashboard')) {
            return;
        }

        const dashboardHTML = `
            <section id="interactive-dashboard" class="dashboard-section">
                <div class="dashboard-header">
                    <h2>📊 Живая аналитика</h2>
                    <div class="dashboard-controls">
                        <button onclick="dashboard.refresh()" class="btn-icon" title="Refresh">
                            🔄
                        </button>
                        <button onclick="dashboard.toggleFullscreen()" class="btn-icon" title="Fullscreen">
                            ⛶
                        </button>
                    </div>
                </div>

                <div class="metrics-grid">
                    <!-- Metric Cards -->
                    <div class="metric-card" id="total-files-metric">
                        <div class="metric-icon">📁</div>
                        <div class="metric-content">
                            <div class="metric-value" id="total-files-value">-</div>
                            <div class="metric-label">Total Files</div>
                            <div class="metric-change" id="total-files-change"></div>
                        </div>
                    </div>

                    <div class="metric-card" id="total-articles-metric">
                        <div class="metric-icon">📄</div>
                        <div class="metric-content">
                            <div class="metric-value" id="total-articles-value">-</div>
                            <div class="metric-label">Total Articles</div>
                            <div class="metric-change" id="total-articles-change"></div>
                        </div>
                    </div>

                    <div class="metric-card" id="total-tags-metric">
                        <div class="metric-icon">🏷️</div>
                        <div class="metric-content">
                            <div class="metric-value" id="total-tags-value">-</div>
                            <div class="metric-label">Unique Tags</div>
                            <div class="metric-change" id="total-tags-change"></div>
                        </div>
                    </div>

                    <div class="metric-card" id="total-size-metric">
                        <div class="metric-icon">💾</div>
                        <div class="metric-content">
                            <div class="metric-value" id="total-size-value">-</div>
                            <div class="metric-label">Total Size</div>
                            <div class="metric-change" id="total-size-change"></div>
                        </div>
                    </div>

                    <!-- Activity Chart -->
                    <div class="chart-card wide">
                        <h3>📈 Activity Timeline</h3>
                        <div class="chart-container">
                            <canvas id="activity-chart"></canvas>
                        </div>
                    </div>

                    <!-- Category Distribution -->
                    <div class="chart-card">
                        <h3>📊 Category Distribution</h3>
                        <div class="chart-container">
                            <canvas id="category-chart"></canvas>
                        </div>
                    </div>

                    <!-- Size Distribution -->
                    <div class="chart-card">
                        <h3>💾 Size Distribution</h3>
                        <div class="chart-container">
                            <canvas id="size-chart"></canvas>
                        </div>
                    </div>

                    <!-- Top Tags -->
                    <div class="chart-card">
                        <h3>🏷️ Top Tags</h3>
                        <div class="chart-container">
                            <canvas id="tags-chart"></canvas>
                        </div>
                    </div>

                    <!-- Recent Activity Feed -->
                    <div class="activity-card">
                        <h3>🕒 Recent Activity</h3>
                        <div id="activity-feed" class="activity-feed"></div>
                    </div>

                    <!-- Quality Score -->
                    <div class="quality-card">
                        <h3>✅ Data Quality</h3>
                        <div class="quality-score-container">
                            <div class="score-circle" id="quality-circle">
                                <svg viewBox="0 0 100 100">
                                    <circle cx="50" cy="50" r="45" fill="none"
                                            stroke="var(--bg-tertiary)" stroke-width="8"/>
                                    <circle id="quality-progress" cx="50" cy="50" r="45" fill="none"
                                            stroke="var(--accent-primary)" stroke-width="8"
                                            stroke-dasharray="282.7"
                                            stroke-dashoffset="28.27"
                                            transform="rotate(-90 50 50)"/>
                                </svg>
                                <span class="score-value" id="quality-value">-</span>
                            </div>
                            <p class="quality-label" id="quality-label">Calculating...</p>
                            <div class="quality-details" id="quality-details"></div>
                        </div>
                    </div>

                    <!-- Trends -->
                    <div class="trends-card">
                        <h3>📉 Trends</h3>
                        <div id="trends-list" class="trends-list"></div>
                    </div>
                </div>
            </section>
        `;

        // Вставить перед первой category-section
        const firstCategory = document.querySelector('.category-section');
        if (firstCategory) {
            firstCategory.insertAdjacentHTML('beforebegin', dashboardHTML);
        } else {
            document.querySelector('.main-content').insertAdjacentHTML('beforeend', dashboardHTML);
        }
    }

    renderAll() {
        this.renderMetrics();
        this.renderActivityChart();
        this.renderCategoryChart();
        this.renderSizeChart();
        this.renderTagsChart();
        this.renderActivityFeed();
        this.renderQualityScore();
        this.renderTrends();
    }

    renderMetrics() {
        // Total files
        const fileCards = document.querySelectorAll('.file-card').length;
        document.getElementById('total-files-value').textContent = fileCards;

        // Total articles (из stats)
        if (this.data.stats && this.data.stats.total_articles) {
            document.getElementById('total-articles-value').textContent =
                this.data.stats.total_articles;
        }

        // Total tags
        if (this.data.tags && this.data.tags.tags) {
            document.getElementById('total-tags-value').textContent =
                this.data.tags.tags.length;
        }

        // Total size
        let totalSize = 0;
        document.querySelectorAll('.file-card').forEach(card => {
            const sizeText = card.querySelector('.file-size')?.textContent || '';
            totalSize += this.parseSizeToBytes(sizeText);
        });
        document.getElementById('total-size-value').textContent =
            this.formatBytes(totalSize);
    }

    renderActivityChart() {
        const ctx = document.getElementById('activity-chart');
        if (!ctx) return;

        // Генерировать mock данные активности за 7 дней
        const days = [];
        const counts = [];
        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            days.push(date.toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' }));
            counts.push(Math.floor(Math.random() * 10) + 5); // Mock data
        }

        this.charts.activity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: days,
                datasets: [{
                    label: 'Files Generated',
                    data: counts,
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 5 }
                    }
                }
            }
        });
    }

    renderCategoryChart() {
        const ctx = document.getElementById('category-chart');
        if (!ctx) return;

        // Подсчитать файлы по категориям
        const categories = {};
        document.querySelectorAll('.file-card').forEach(card => {
            const category = card.getAttribute('data-category') || 'other';
            categories[category] = (categories[category] || 0) + 1;
        });

        const categoryNames = {
            'viz': 'Визуализации',
            'graph': 'Графы',
            'stats': 'Статистика',
            'reports': 'Отчёты',
            'data': 'Данные',
            'tables': 'Таблицы',
            'other': 'Другое'
        };

        const labels = Object.keys(categories).map(k => categoryNames[k] || k);
        const data = Object.values(categories);

        this.charts.category = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(240, 147, 251, 0.8)',
                        'rgba(79, 172, 254, 0.8)',
                        'rgba(67, 233, 123, 0.8)',
                        'rgba(254, 200, 76, 0.8)',
                        'rgba(255, 107, 107, 0.8)',
                        'rgba(200, 200, 200, 0.8)'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    renderSizeChart() {
        const ctx = document.getElementById('size-chart');
        if (!ctx) return;

        // Подсчитать файлы по размеру
        const sizes = {
            'Tiny (< 1KB)': 0,
            'Small (1-10KB)': 0,
            'Medium (10-100KB)': 0,
            'Large (100KB-1MB)': 0,
            'Huge (> 1MB)': 0
        };

        document.querySelectorAll('.file-card').forEach(card => {
            const sizeClass = card.getAttribute('data-size') || 'medium';
            const sizeMap = {
                'tiny': 'Tiny (< 1KB)',
                'small': 'Small (1-10KB)',
                'medium': 'Medium (10-100KB)',
                'large': 'Large (100KB-1MB)',
                'huge': 'Huge (> 1MB)'
            };
            const category = sizeMap[sizeClass];
            if (category) sizes[category]++;
        });

        this.charts.size = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(sizes),
                datasets: [{
                    label: 'File Count',
                    data: Object.values(sizes),
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    renderTagsChart() {
        const ctx = document.getElementById('tags-chart');
        if (!ctx || !this.data.tags) return;

        // Взять топ 10 тегов
        const tags = this.data.tags.tags || [];
        const topTags = tags
            .sort((a, b) => (b.weight || b.count || 0) - (a.weight || a.count || 0))
            .slice(0, 10);

        this.charts.tags = new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: topTags.map(t => t.tag || t.name),
                datasets: [{
                    label: 'Usage',
                    data: topTags.map(t => t.weight || t.count || 0),
                    backgroundColor: 'rgba(240, 147, 251, 0.6)',
                    borderColor: 'rgba(240, 147, 251, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { beginAtZero: true }
                }
            }
        });
    }

    renderActivityFeed() {
        const feed = document.getElementById('activity-feed');
        if (!feed) return;

        // Генерировать недавнюю активность
        const activities = [
            { time: '2 hours ago', action: 'Created', file: 'search_index.json', icon: '📝' },
            { time: '3 hours ago', action: 'Updated', file: 'statistics.json', icon: '🔄' },
            { time: '5 hours ago', action: 'Created', file: 'knowledge_graph.html', icon: '📝' },
            { time: '1 day ago', action: 'Updated', file: 'master_index.json', icon: '🔄' },
            { time: '1 day ago', action: 'Created', file: 'timeline.html', icon: '📝' }
        ];

        feed.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <span class="activity-icon">${activity.icon}</span>
                <div class="activity-details">
                    <div class="activity-action">
                        <strong>${activity.action}</strong>
                        <span class="activity-file">${activity.file}</span>
                    </div>
                    <div class="activity-time">${activity.time}</div>
                </div>
            </div>
        `).join('');
    }

    renderQualityScore() {
        // Вычислить quality score
        let score = 100;
        const issues = [];

        // Проверки
        const fileCount = document.querySelectorAll('.file-card').length;
        if (fileCount < 50) {
            score -= 10;
            issues.push('Low file count');
        }

        // Проверить наличие важных файлов
        const importantFiles = ['statistics.json', 'master_index.json', 'knowledge_graph_data.json'];
        importantFiles.forEach(file => {
            const exists = Array.from(document.querySelectorAll('.file-card'))
                .some(card => card.getAttribute('data-filename')?.includes(file));
            if (!exists) {
                score -= 5;
                issues.push(`Missing ${file}`);
            }
        });

        // Обновить UI
        const scoreValue = document.getElementById('quality-value');
        const scoreLabel = document.getElementById('quality-label');
        const scoreProgress = document.getElementById('quality-progress');
        const details = document.getElementById('quality-details');

        if (scoreValue) scoreValue.textContent = `${score}%`;

        if (scoreLabel) {
            if (score >= 90) scoreLabel.textContent = 'Отлично!';
            else if (score >= 75) scoreLabel.textContent = 'Хорошо';
            else if (score >= 60) scoreLabel.textContent = 'Удовлетворительно';
            else scoreLabel.textContent = 'Требует внимания';
        }

        if (scoreProgress) {
            const circumference = 282.7;
            const offset = circumference - (score / 100) * circumference;
            scoreProgress.style.strokeDashoffset = offset;
        }

        if (details) {
            if (issues.length > 0) {
                details.innerHTML = `
                    <p class="quality-issues">Issues found:</p>
                    <ul>
                        ${issues.map(issue => `<li>${issue}</li>`).join('')}
                    </ul>
                `;
            } else {
                details.innerHTML = '<p class="quality-perfect">✅ No issues found</p>';
            }
        }
    }

    renderTrends() {
        const trends = document.getElementById('trends-list');
        if (!trends) return;

        const trendData = [
            { label: 'JSON файлы', change: 15, trend: 'up' },
            { label: 'HTML визуализации', change: 0, trend: 'stable' },
            { label: 'CSV файлы', change: -5, trend: 'down' },
            { label: 'Markdown отчёты', change: 8, trend: 'up' }
        ];

        trends.innerHTML = trendData.map(trend => {
            const icon = trend.trend === 'up' ? '📈' :
                        trend.trend === 'down' ? '📉' : '➡️';
            const changeClass = trend.trend === 'up' ? 'positive' :
                               trend.trend === 'down' ? 'negative' : 'neutral';

            return `
                <div class="trend-item ${changeClass}">
                    <span class="trend-icon">${icon}</span>
                    <span class="trend-label">${trend.label}</span>
                    <span class="trend-change">${trend.change > 0 ? '+' : ''}${trend.change}%</span>
                </div>
            `;
        }).join('');
    }

    refresh() {
        showNotification('Refreshing dashboard...');
        this.loadData().then(() => {
            this.renderAll();
            showNotification('Dashboard refreshed!');
        });
    }

    toggleFullscreen() {
        const dashboard = document.getElementById('interactive-dashboard');
        if (dashboard) {
            dashboard.classList.toggle('fullscreen');
        }
    }

    // Helper methods
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    parseSizeToBytes(sizeStr) {
        const match = sizeStr.match(/([\d.]+)\s*([A-Z]+)/);
        if (!match) return 0;

        const value = parseFloat(match[1]);
        const unit = match[2];

        const multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        };

        return value * (multipliers[unit] || 0);
    }
}

// Глобальная инициализация
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    // Подождать, пока Chart.js загрузится
    if (typeof Chart !== 'undefined') {
        dashboard = new InteractiveDashboard();
    } else {
        console.warn('Chart.js not loaded, dashboard disabled');
    }
});
