/**
 * Data Explorer v2.0
 * Интерактивный просмотр JSON и CSV данных
 */

class DataExplorer {
    constructor() {
        this.currentData = null;
        this.currentFilename = null;
        this.currentView = 'tree';
        this.modal = null;

        this.init();
    }

    init() {
        // Создать модальное окно
        this.createModal();

        // Настроить обработчики событий
        this.setupEventListeners();
    }

    createModal() {
        const modalHTML = `
            <div id="data-explorer-modal" class="modal">
                <div class="modal-overlay" onclick="dataExplorer.close()"></div>
                <div class="modal-content data-explorer-content">
                    <div class="modal-header">
                        <h2>
                            <span class="modal-icon">📊</span>
                            <span>Data Explorer: </span>
                            <span id="explorer-filename" class="filename-display"></span>
                        </h2>
                        <button class="modal-close" onclick="dataExplorer.close()">✕</button>
                    </div>

                    <div class="modal-body">
                        <!-- Tabs -->
                        <div class="explorer-tabs">
                            <button class="tab-btn active" data-view="tree" onclick="dataExplorer.switchView('tree')">
                                🌳 Tree View
                            </button>
                            <button class="tab-btn" data-view="table" onclick="dataExplorer.switchView('table')">
                                📋 Table View
                            </button>
                            <button class="tab-btn" data-view="raw" onclick="dataExplorer.switchView('raw')">
                                📝 Raw JSON
                            </button>
                            <button class="tab-btn" data-view="chart" onclick="dataExplorer.switchView('chart')">
                                📊 Chart
                            </button>
                            <button class="tab-btn" data-view="stats" onclick="dataExplorer.switchView('stats')">
                                📈 Statistics
                            </button>
                        </div>

                        <!-- Views -->
                        <div class="explorer-views">
                            <!-- Tree View -->
                            <div id="tree-view" class="explorer-view active">
                                <div class="view-toolbar">
                                    <button onclick="dataExplorer.expandAll()">Expand All</button>
                                    <button onclick="dataExplorer.collapseAll()">Collapse All</button>
                                </div>
                                <div id="json-tree" class="tree-container"></div>
                            </div>

                            <!-- Table View -->
                            <div id="table-view" class="explorer-view">
                                <div class="view-toolbar">
                                    <input type="text" id="table-search" placeholder="🔍 Search in table..."
                                           oninput="dataExplorer.filterTable(this.value)">
                                    <select id="table-sort" onchange="dataExplorer.sortTable(this.value)">
                                        <option value="">Sort by...</option>
                                    </select>
                                </div>
                                <div class="table-wrapper">
                                    <table id="data-table" class="data-table">
                                        <thead></thead>
                                        <tbody></tbody>
                                    </table>
                                </div>
                            </div>

                            <!-- Raw View -->
                            <div id="raw-view" class="explorer-view">
                                <div class="view-toolbar">
                                    <button onclick="dataExplorer.copyRaw()">📋 Copy</button>
                                    <button onclick="dataExplorer.downloadRaw()">⬇️ Download</button>
                                    <label>
                                        <input type="checkbox" id="prettify-toggle" checked
                                               onchange="dataExplorer.togglePrettify()">
                                        Prettify
                                    </label>
                                </div>
                                <pre><code id="raw-json" class="json-code"></code></pre>
                            </div>

                            <!-- Chart View -->
                            <div id="chart-view" class="explorer-view">
                                <div class="view-toolbar">
                                    <select id="chart-type" onchange="dataExplorer.updateChart()">
                                        <option value="bar">Bar Chart</option>
                                        <option value="line">Line Chart</option>
                                        <option value="pie">Pie Chart</option>
                                        <option value="doughnut">Doughnut</option>
                                        <option value="radar">Radar</option>
                                    </select>
                                    <select id="chart-data-select" onchange="dataExplorer.updateChart()">
                                        <option value="">Auto-detect data...</option>
                                    </select>
                                </div>
                                <div class="chart-container">
                                    <canvas id="data-chart"></canvas>
                                </div>
                                <div id="chart-message" class="chart-message"></div>
                            </div>

                            <!-- Statistics View -->
                            <div id="stats-view" class="explorer-view">
                                <div id="data-statistics" class="statistics-grid"></div>
                            </div>
                        </div>
                    </div>

                    <div class="modal-footer">
                        <div class="file-info">
                            <span id="file-size-info"></span>
                            <span id="file-type-info"></span>
                        </div>
                        <div class="modal-actions">
                            <button class="btn btn-secondary" onclick="dataExplorer.exportAs('json')">
                                Export JSON
                            </button>
                            <button class="btn btn-secondary" onclick="dataExplorer.exportAs('csv')">
                                Export CSV
                            </button>
                            <button class="btn btn-primary" onclick="dataExplorer.close()">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('data-explorer-modal');
    }

    setupEventListeners() {
        // Закрытие по Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('active')) {
                this.close();
            }
        });
    }

    async open(filepath) {
        try {
            showNotification('Loading data...');

            // Загрузить данные
            const response = await fetch(`../${filepath}`);
            if (!response.ok) throw new Error('Failed to load file');

            const contentType = response.headers.get('content-type');
            let data;

            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                try {
                    data = JSON.parse(text);
                } catch {
                    data = { raw: text };
                }
            }

            this.currentData = data;
            this.currentFilename = filepath.split('/').pop();

            // Обновить UI
            document.getElementById('explorer-filename').textContent = this.currentFilename;
            document.getElementById('file-size-info').textContent =
                `Size: ${this.formatBytes(JSON.stringify(data).length)}`;
            document.getElementById('file-type-info').textContent =
                `Type: ${this.detectDataType(data)}`;

            // Показать модальное окно
            this.modal.classList.add('active');
            document.body.style.overflow = 'hidden';

            // Рендерить текущий view
            this.renderCurrentView();

            showNotification('Data loaded successfully!');
        } catch (error) {
            console.error('Error opening file:', error);
            showNotification('Error loading file: ' + error.message, 'error');
        }
    }

    close() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';

        // Очистить chart если есть
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
    }

    switchView(viewName) {
        this.currentView = viewName;

        // Обновить активные tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === viewName);
        });

        // Обновить активные views
        document.querySelectorAll('.explorer-view').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(`${viewName}-view`).classList.add('active');

        this.renderCurrentView();
    }

    renderCurrentView() {
        switch(this.currentView) {
            case 'tree':
                this.renderTreeView();
                break;
            case 'table':
                this.renderTableView();
                break;
            case 'raw':
                this.renderRawView();
                break;
            case 'chart':
                this.renderChartView();
                break;
            case 'stats':
                this.renderStatsView();
                break;
        }
    }

    // Tree View
    renderTreeView() {
        const container = document.getElementById('json-tree');
        container.innerHTML = this.buildTreeHTML(this.currentData, 0);

        // Добавить обработчики для expand/collapse
        container.querySelectorAll('.tree-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.target.closest('.tree-node').classList.toggle('collapsed');
            });
        });
    }

    buildTreeHTML(obj, level = 0) {
        if (obj === null) return '<span class="value null">null</span>';
        if (obj === undefined) return '<span class="value undefined">undefined</span>';

        const type = typeof obj;

        if (type === 'object') {
            if (Array.isArray(obj)) {
                return this.buildArrayHTML(obj, level);
            } else {
                return this.buildObjectHTML(obj, level);
            }
        } else {
            return `<span class="value ${type}">${this.escapeHtml(String(obj))}</span>`;
        }
    }

    buildObjectHTML(obj, level) {
        const keys = Object.keys(obj);
        if (keys.length === 0) return '<span class="value empty">{}</span>';

        let html = '<div class="tree-node">';
        html += '<span class="tree-toggle">▼</span>';
        html += '<span class="brace">{</span>';
        html += '<div class="tree-children">';

        keys.forEach((key, index) => {
            html += '<div class="tree-item">';
            html += `<span class="key">"${this.escapeHtml(key)}"</span>: `;
            html += this.buildTreeHTML(obj[key], level + 1);
            if (index < keys.length - 1) html += '<span class="comma">,</span>';
            html += '</div>';
        });

        html += '</div>';
        html += '<span class="brace">}</span>';
        html += '</div>';
        return html;
    }

    buildArrayHTML(arr, level) {
        if (arr.length === 0) return '<span class="value empty">[]</span>';

        let html = '<div class="tree-node">';
        html += '<span class="tree-toggle">▼</span>';
        html += '<span class="brace">[</span>';
        html += `<span class="array-length">${arr.length} items</span>`;
        html += '<div class="tree-children">';

        arr.forEach((item, index) => {
            html += '<div class="tree-item">';
            html += `<span class="index">${index}</span>: `;
            html += this.buildTreeHTML(item, level + 1);
            if (index < arr.length - 1) html += '<span class="comma">,</span>';
            html += '</div>';
        });

        html += '</div>';
        html += '<span class="brace">]</span>';
        html += '</div>';
        return html;
    }

    expandAll() {
        document.querySelectorAll('#json-tree .tree-node').forEach(node => {
            node.classList.remove('collapsed');
        });
    }

    collapseAll() {
        document.querySelectorAll('#json-tree .tree-node').forEach(node => {
            node.classList.add('collapsed');
        });
    }

    // Table View
    renderTableView() {
        const data = this.currentData;
        const table = document.getElementById('data-table');
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');

        thead.innerHTML = '';
        tbody.innerHTML = '';

        // Если это массив объектов - показать как таблицу
        if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
            const headers = Object.keys(data[0]);

            // Заполнить select для сортировки
            const sortSelect = document.getElementById('table-sort');
            sortSelect.innerHTML = '<option value="">Sort by...</option>' +
                headers.map(h => `<option value="${h}">${h}</option>`).join('');

            // Заголовки
            const headerRow = document.createElement('tr');
            headers.forEach(header => {
                const th = document.createElement('th');
                th.textContent = header;
                th.onclick = () => this.sortTableByColumn(header);
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);

            // Данные
            this.tableData = data;
            this.renderTableRows(data, headers);
        } else if (typeof data === 'object') {
            // Если это объект - показать key-value пары
            thead.innerHTML = '<tr><th>Key</th><th>Value</th></tr>';

            Object.entries(data).forEach(([key, value]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${this.escapeHtml(key)}</strong></td>
                    <td>${this.formatValue(value)}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td>Cannot display as table</td></tr>';
        }
    }

    renderTableRows(data, headers) {
        const tbody = document.getElementById('data-table').querySelector('tbody');
        tbody.innerHTML = '';

        data.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(header => {
                const td = document.createElement('td');
                td.innerHTML = this.formatValue(row[header]);
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    filterTable(searchTerm) {
        const rows = document.querySelectorAll('#data-table tbody tr');
        const term = searchTerm.toLowerCase();

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? '' : 'none';
        });
    }

    sortTable(column) {
        if (!column || !this.tableData) return;

        const sorted = [...this.tableData].sort((a, b) => {
            const aVal = a[column];
            const bVal = b[column];

            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return aVal - bVal;
            }
            return String(aVal).localeCompare(String(bVal));
        });

        const headers = Object.keys(this.tableData[0]);
        this.renderTableRows(sorted, headers);
    }

    sortTableByColumn(column) {
        this.sortTable(column);
    }

    // Raw View
    renderRawView() {
        const rawCode = document.getElementById('raw-json');
        const prettify = document.getElementById('prettify-toggle').checked;

        const jsonString = prettify
            ? JSON.stringify(this.currentData, null, 2)
            : JSON.stringify(this.currentData);

        rawCode.textContent = jsonString;
    }

    togglePrettify() {
        this.renderRawView();
    }

    copyRaw() {
        const text = document.getElementById('raw-json').textContent;
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!');
        });
    }

    downloadRaw() {
        const text = document.getElementById('raw-json').textContent;
        const blob = new Blob([text], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.currentFilename;
        a.click();
        URL.revokeObjectURL(url);
        showNotification('Download started!');
    }

    // Chart View
    renderChartView() {
        const chartData = this.extractChartData(this.currentData);
        const messageDiv = document.getElementById('chart-message');

        if (!chartData) {
            messageDiv.innerHTML = `
                <p>⚠️ Cannot auto-detect chartable data</p>
                <p>Expected format: Array of objects with numeric values</p>
            `;
            document.querySelector('.chart-container').style.display = 'none';
            return;
        }

        messageDiv.innerHTML = '';
        document.querySelector('.chart-container').style.display = 'block';

        // Заполнить data selector
        const dataSelect = document.getElementById('chart-data-select');
        dataSelect.innerHTML = '<option value="">Auto-detected</option>';

        this.updateChart();
    }

    extractChartData(data) {
        // Попытаться найти данные для графика
        if (Array.isArray(data) && data.length > 0) {
            const first = data[0];

            if (typeof first === 'object') {
                // Найти числовые поля
                const numericFields = Object.keys(first).filter(k =>
                    typeof first[k] === 'number'
                );

                // Найти текстовые поля для labels
                const labelFields = Object.keys(first).filter(k =>
                    typeof first[k] === 'string'
                );

                if (numericFields.length > 0) {
                    const labelField = labelFields[0] || Object.keys(first)[0];
                    const valueField = numericFields[0];

                    return {
                        labels: data.map(d => d[labelField] || d[Object.keys(d)[0]]),
                        datasets: [{
                            label: valueField,
                            data: data.map(d => d[valueField]),
                            backgroundColor: this.generateColors(data.length, 0.6),
                            borderColor: this.generateColors(data.length, 1),
                            borderWidth: 2
                        }]
                    };
                }
            }
        }

        return null;
    }

    updateChart() {
        const chartType = document.getElementById('chart-type').value;
        const chartData = this.extractChartData(this.currentData);

        if (!chartData) return;

        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        const ctx = document.getElementById('data-chart').getContext('2d');
        this.chartInstance = new Chart(ctx, {
            type: chartType,
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: chartType === 'pie' || chartType === 'doughnut'
                    }
                }
            }
        });
    }

    generateColors(count, alpha = 1) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = (i * 360 / count) % 360;
            colors.push(`hsla(${hue}, 70%, 60%, ${alpha})`);
        }
        return colors;
    }

    // Statistics View
    renderStatsView() {
        const stats = this.calculateStatistics(this.currentData);
        const container = document.getElementById('data-statistics');

        container.innerHTML = Object.entries(stats).map(([category, items]) => `
            <div class="stat-category">
                <h3>${category}</h3>
                <div class="stat-items">
                    ${Object.entries(items).map(([key, value]) => `
                        <div class="stat-item">
                            <span class="stat-label">${key}</span>
                            <span class="stat-value">${value}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    calculateStatistics(data) {
        const stats = {
            'General': {},
            'Structure': {},
            'Content': {}
        };

        // General
        stats.General['Type'] = Array.isArray(data) ? 'Array' : typeof data;
        stats.General['Size'] = this.formatBytes(JSON.stringify(data).length);

        if (Array.isArray(data)) {
            stats.General['Items'] = data.length;

            if (data.length > 0) {
                const first = data[0];
                if (typeof first === 'object') {
                    stats.Structure['Fields'] = Object.keys(first).length;
                    stats.Structure['Field Names'] = Object.keys(first).join(', ');
                }
            }
        } else if (typeof data === 'object') {
            stats.General['Keys'] = Object.keys(data).length;
            stats.Structure['Key Names'] = Object.keys(data).join(', ');
        }

        // Content analysis
        const jsonStr = JSON.stringify(data);
        stats.Content['Unique Values'] = new Set(jsonStr.match(/"([^"]*)"/g)).size;
        stats.Content['Numbers'] = (jsonStr.match(/\d+(\.\d+)?/g) || []).length;
        stats.Content['Nulls'] = (jsonStr.match(/null/g) || []).length;

        return stats;
    }

    // Export functions
    exportAs(format) {
        if (format === 'json') {
            const blob = new Blob([JSON.stringify(this.currentData, null, 2)],
                { type: 'application/json' });
            this.downloadBlob(blob, this.currentFilename);
        } else if (format === 'csv') {
            const csv = this.jsonToCSV(this.currentData);
            const blob = new Blob([csv], { type: 'text/csv' });
            const filename = this.currentFilename.replace('.json', '.csv');
            this.downloadBlob(blob, filename);
        }
    }

    jsonToCSV(data) {
        if (!Array.isArray(data) || data.length === 0) {
            return '';
        }

        const headers = Object.keys(data[0]);
        const rows = data.map(row =>
            headers.map(header => JSON.stringify(row[header] || '')).join(',')
        );

        return [headers.join(','), ...rows].join('\n');
    }

    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        showNotification('Download started!');
    }

    // Helper methods
    detectDataType(data) {
        if (Array.isArray(data)) {
            return `Array (${data.length} items)`;
        } else if (typeof data === 'object' && data !== null) {
            return `Object (${Object.keys(data).length} keys)`;
        } else {
            return typeof data;
        }
    }

    formatValue(value) {
        if (value === null) return '<em>null</em>';
        if (value === undefined) return '<em>undefined</em>';
        if (typeof value === 'object') {
            return `<code>${this.escapeHtml(JSON.stringify(value))}</code>`;
        }
        return this.escapeHtml(String(value));
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Глобальная инициализация
let dataExplorer;
document.addEventListener('DOMContentLoaded', () => {
    dataExplorer = new DataExplorer();
});
