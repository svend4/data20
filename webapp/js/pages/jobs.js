/**
 * Jobs Page Logic
 * Displays and manages job history
 */

let allJobs = [];
let filteredJobs = [];
let autoRefreshInterval = null;

// Initialize page
window.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (!isAuthenticated()) {
        window.location.href = '../index.html';
        return;
    }

    await loadJobs();

    // Auto-refresh every 5 seconds
    autoRefreshInterval = setInterval(async () => {
        await loadJobs(true); // Silent refresh
    }, 5000);
});

// Load jobs from API
async function loadJobs(silent = false) {
    try {
        if (!silent) {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('jobs-list').style.display = 'none';
            document.getElementById('no-jobs').style.display = 'none';
        }

        const jobs = await apiRequest(API.jobs);
        allJobs = jobs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        filteredJobs = allJobs;

        // Extract unique tool names for filter
        const toolNames = [...new Set(jobs.map(j => j.tool_name))];
        updateToolFilter(toolNames);

        // Display jobs
        displayJobs(filteredJobs);

        // Hide loading, show content
        document.getElementById('loading').style.display = 'none';
        if (jobs.length === 0) {
            document.getElementById('no-jobs').style.display = 'block';
        } else {
            document.getElementById('jobs-list').style.display = 'flex';
        }

    } catch (error) {
        console.error('Failed to load jobs:', error);
        if (!silent) {
            document.getElementById('loading').innerHTML = `
                <p style="color: #e74c3c;">❌ Ошибка загрузки задач: ${error.message}</p>
            `;
        }
    }
}

// Update tool filter dropdown
function updateToolFilter(toolNames) {
    const toolFilter = document.getElementById('tool-filter');
    const currentValue = toolFilter.value;

    // Keep "All" option
    toolFilter.innerHTML = '<option value="all">Все инструменты</option>';

    toolNames.sort().forEach(toolName => {
        const option = document.createElement('option');
        option.value = toolName;
        option.textContent = toolName;
        toolFilter.appendChild(option);
    });

    // Restore previous selection
    if (currentValue && toolNames.includes(currentValue)) {
        toolFilter.value = currentValue;
    }
}

// Filter jobs
function filterJobs() {
    const statusFilter = document.getElementById('status-filter').value;
    const toolFilter = document.getElementById('tool-filter').value;

    filteredJobs = allJobs.filter(job => {
        // Status filter
        if (statusFilter !== 'all' && job.status !== statusFilter) {
            return false;
        }

        // Tool filter
        if (toolFilter !== 'all' && job.tool_name !== toolFilter) {
            return false;
        }

        return true;
    });

    displayJobs(filteredJobs);
}

// Display jobs
function displayJobs(jobs) {
    const listEl = document.getElementById('jobs-list');
    listEl.innerHTML = '';

    jobs.forEach(job => {
        const card = createJobCard(job);
        listEl.appendChild(card);
    });
}

// Create job card element
function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    card.id = `job-${job.job_id}`;

    const statusText = getStatusDisplayName(job.status);
    const duration = calculateDuration(job);

    card.innerHTML = `
        <div class="job-card-header">
            <div class="job-title">
                <h3>${job.tool_name}</h3>
                <div class="job-id">ID: ${job.job_id}</div>
            </div>
            <span class="status-badge ${job.status}">${statusText}</span>
        </div>

        <div class="job-info">
            <div class="job-info-item">
                <label>Создана</label>
                <value>${formatDateTime(job.created_at)}</value>
            </div>
            ${job.started_at ? `
                <div class="job-info-item">
                    <label>Запущена</label>
                    <value>${formatDateTime(job.started_at)}</value>
                </div>
            ` : ''}
            ${job.completed_at ? `
                <div class="job-info-item">
                    <label>Завершена</label>
                    <value>${formatDateTime(job.completed_at)}</value>
                </div>
            ` : ''}
            ${duration ? `
                <div class="job-info-item">
                    <label>Длительность</label>
                    <value>${duration}</value>
                </div>
            ` : ''}
            ${job.user_id ? `
                <div class="job-info-item">
                    <label>Пользователь</label>
                    <value>${job.user_id}</value>
                </div>
            ` : ''}
        </div>

        ${job.parameters && Object.keys(job.parameters).length > 0 ? `
            <div class="job-info">
                <div class="job-info-item">
                    <label>Параметры</label>
                    <value>${JSON.stringify(job.parameters, null, 2)}</value>
                </div>
            </div>
        ` : ''}

        <div class="job-actions">
            <button onclick="viewJobDetails('${job.job_id}')">
                👁️ Подробнее
            </button>
            ${(job.status === 'completed' || job.status === 'failed') ? `
                <button onclick="rerunJob('${job.job_id}')">
                    🔄 Повторить
                </button>
            ` : ''}
            ${job.status === 'running' ? `
                <button onclick="refreshJobStatus('${job.job_id}')">
                    ♻️ Обновить статус
                </button>
            ` : ''}
        </div>

        ${job.result ? `
            <div class="job-result" id="result-${job.job_id}" style="display: none;">
                <strong>Результат:</strong>
                <pre>${JSON.stringify(job.result, null, 2)}</pre>
            </div>
        ` : ''}

        ${job.error ? `
            <div class="job-result" style="background: #f8d7da; color: #842029;">
                <strong>Ошибка:</strong>
                <pre>${job.error}</pre>
            </div>
        ` : ''}
    `;

    return card;
}

// View job details
async function viewJobDetails(jobId) {
    const resultEl = document.getElementById(`result-${jobId}`);
    if (resultEl) {
        // Toggle result visibility
        resultEl.style.display = resultEl.style.display === 'none' ? 'block' : 'none';
    } else {
        // Fetch full job details
        try {
            const job = await apiRequest(API.jobDetail(jobId));
            alert(JSON.stringify(job, null, 2));
        } catch (error) {
            alert(`Ошибка загрузки деталей задачи: ${error.message}`);
        }
    }
}

// Refresh job status
async function refreshJobStatus(jobId) {
    try {
        const job = await apiRequest(API.jobDetail(jobId));

        // Update job in allJobs array
        const index = allJobs.findIndex(j => j.job_id === jobId);
        if (index !== -1) {
            allJobs[index] = job;
        }

        // Refilter and redisplay
        filterJobs();

    } catch (error) {
        alert(`Ошибка обновления статуса: ${error.message}`);
    }
}

// Rerun job with same parameters
async function rerunJob(jobId) {
    try {
        // Find the job
        const job = allJobs.find(j => j.job_id === jobId);
        if (!job) {
            alert('Задача не найдена');
            return;
        }

        if (!confirm(`Повторить выполнение инструмента "${job.tool_name}"?`)) {
            return;
        }

        // Submit new job with same parameters
        const newJob = await apiRequest(API.runTool, {
            method: 'POST',
            body: JSON.stringify({
                tool_name: job.tool_name,
                parameters: job.parameters || {},
            }),
        });

        alert(`Задача создана! ID: ${newJob.job_id}`);

        // Reload jobs list
        await loadJobs();

    } catch (error) {
        alert(`Ошибка повторного запуска: ${error.message}`);
    }
}

// Calculate job duration
function calculateDuration(job) {
    if (job.started_at && job.completed_at) {
        const duration = (new Date(job.completed_at) - new Date(job.started_at)) / 1000;
        return formatDuration(duration);
    } else if (job.started_at && job.status === 'running') {
        const duration = (new Date() - new Date(job.started_at)) / 1000;
        return formatDuration(duration) + ' (выполняется)';
    }
    return null;
}

// Helper: Get status display name
function getStatusDisplayName(status) {
    const statusMap = {
        'pending': '⏳ Ожидание',
        'running': '▶️ Выполняется',
        'completed': '✅ Завершено',
        'failed': '❌ Ошибка',
    };
    return statusMap[status] || status;
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});
