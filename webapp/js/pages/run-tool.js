/**
 * Run Tool Page Logic
 * Handles tool parameter input and execution
 */

let currentTool = null;
let currentJobId = null;
let pollInterval = null;

// Initialize page
window.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (!isAuthenticated()) {
        window.location.href = '../index.html';
        return;
    }

    // Get tool name from URL
    const params = new URLSearchParams(window.location.search);
    const toolName = params.get('tool');

    if (!toolName) {
        alert('Инструмент не указан');
        window.location.href = 'home.html';
        return;
    }

    await loadTool(toolName);
});

// Load tool information
async function loadTool(toolName) {
    try {
        // Fetch all tools and find the specific one
        const tools = await apiRequest(API.tools);
        const tool = tools.find(t => t.name === toolName);

        if (!tool) {
            throw new Error('Инструмент не найден');
        }

        currentTool = tool;

        // Display tool information
        document.getElementById('tool-name').textContent = tool.display_name || tool.name;
        document.getElementById('tool-description').textContent = tool.description || 'Описание недоступно';
        document.getElementById('tool-category').textContent = getCategoryDisplayName(tool.category || 'other');

        // Generate parameter form
        generateParameterForm(tool.parameters || {});

        // Hide loading, show content
        document.getElementById('loading').style.display = 'none';
        document.getElementById('tool-header').style.display = 'block';
        document.getElementById('parameters-form').style.display = 'block';

    } catch (error) {
        console.error('Failed to load tool:', error);
        alert(`Ошибка загрузки инструмента: ${error.message}`);
        window.location.href = 'home.html';
    }
}

// Generate parameter input form
function generateParameterForm(parameters) {
    const container = document.getElementById('parameters-container');
    container.innerHTML = '';

    if (Object.keys(parameters).length === 0) {
        container.innerHTML = '<p style="color: #999;">Этот инструмент не требует параметров</p>';
        return;
    }

    Object.entries(parameters).forEach(([paramName, paramSpec]) => {
        const formGroup = document.createElement('div');
        formGroup.className = 'form-group';

        const label = document.createElement('label');
        label.htmlFor = `param-${paramName}`;
        label.innerHTML = `${paramSpec.display_name || paramName} ${paramSpec.required ? '<span class="required">*</span>' : ''}`;

        const input = createParameterInput(paramName, paramSpec);

        const description = document.createElement('div');
        description.className = 'param-description';
        description.textContent = paramSpec.description || '';

        formGroup.appendChild(label);
        formGroup.appendChild(input);
        if (paramSpec.description) {
            formGroup.appendChild(description);
        }

        container.appendChild(formGroup);
    });
}

// Create appropriate input element based on parameter type
function createParameterInput(paramName, paramSpec) {
    const inputId = `param-${paramName}`;
    let input;

    if (paramSpec.type === 'boolean') {
        input = document.createElement('select');
        input.innerHTML = `
            <option value="">-- Выберите --</option>
            <option value="true">Да</option>
            <option value="false">Нет</option>
        `;
    } else if (paramSpec.enum && paramSpec.enum.length > 0) {
        input = document.createElement('select');
        input.innerHTML = '<option value="">-- Выберите --</option>';
        paramSpec.enum.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            input.appendChild(opt);
        });
    } else if (paramSpec.type === 'integer' || paramSpec.type === 'number') {
        input = document.createElement('input');
        input.type = 'number';
        input.step = paramSpec.type === 'integer' ? '1' : 'any';
        if (paramSpec.default !== undefined) {
            input.value = paramSpec.default;
        }
    } else if (paramSpec.type === 'array' || paramSpec.type === 'object') {
        input = document.createElement('textarea');
        input.placeholder = paramSpec.type === 'array' ? '["item1", "item2"]' : '{"key": "value"}';
    } else {
        input = document.createElement('input');
        input.type = 'text';
        if (paramSpec.default !== undefined) {
            input.value = paramSpec.default;
        }
    }

    input.id = inputId;
    input.name = paramName;
    input.required = paramSpec.required || false;

    return input;
}

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');

    // Collect parameters
    const parameters = {};
    const formData = new FormData(form);

    for (const [key, value] of formData.entries()) {
        if (value === '') continue; // Skip empty values

        const paramSpec = currentTool.parameters[key];

        // Parse value based on type
        if (paramSpec.type === 'boolean') {
            parameters[key] = value === 'true';
        } else if (paramSpec.type === 'integer') {
            parameters[key] = parseInt(value);
        } else if (paramSpec.type === 'number') {
            parameters[key] = parseFloat(value);
        } else if (paramSpec.type === 'array' || paramSpec.type === 'object') {
            try {
                parameters[key] = JSON.parse(value);
            } catch (e) {
                alert(`Ошибка парсинга JSON для параметра "${paramSpec.display_name || key}"`);
                return;
            }
        } else {
            parameters[key] = value;
        }
    }

    // Disable form
    setLoading(submitBtn, true);
    form.querySelectorAll('input, select, textarea').forEach(el => el.disabled = true);

    try {
        // Submit job
        const job = await apiRequest(API.runTool, {
            method: 'POST',
            body: JSON.stringify({
                tool_name: currentTool.name,
                parameters: parameters,
            }),
        });

        currentJobId = job.job_id;

        // Show result section
        document.getElementById('result-section').style.display = 'block';
        document.getElementById('result-section').scrollIntoView({ behavior: 'smooth' });

        // Update initial job info
        updateJobStatus(job);

        // Start polling for updates
        startPolling();

    } catch (error) {
        console.error('Failed to submit job:', error);
        alert(`Ошибка запуска инструмента: ${error.message}`);

        // Re-enable form
        setLoading(submitBtn, false);
        form.querySelectorAll('input, select, textarea').forEach(el => el.disabled = false);
    }
}

// Start polling for job status
function startPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
    }

    document.getElementById('progress-bar').style.display = 'block';

    pollInterval = setInterval(async () => {
        try {
            const job = await apiRequest(API.jobDetail(currentJobId));
            updateJobStatus(job);

            // Stop polling if job is completed or failed
            if (job.status === 'completed' || job.status === 'failed') {
                clearInterval(pollInterval);
                document.getElementById('progress-bar').style.display = 'none';
            }
        } catch (error) {
            console.error('Failed to poll job status:', error);
            clearInterval(pollInterval);
        }
    }, 2000); // Poll every 2 seconds
}

// Update job status display
function updateJobStatus(job) {
    // Update status badge
    const statusBadge = document.getElementById('job-status');
    statusBadge.textContent = getStatusDisplayName(job.status);
    statusBadge.className = `status-badge ${job.status}`;

    // Update info
    document.getElementById('job-id').textContent = job.job_id;
    document.getElementById('job-status-text').textContent = getStatusDisplayName(job.status);
    document.getElementById('job-created').textContent = formatDateTime(job.created_at);

    // Calculate and display duration
    if (job.started_at && job.completed_at) {
        const duration = (new Date(job.completed_at) - new Date(job.started_at)) / 1000;
        document.getElementById('job-duration').textContent = formatDuration(duration);
    } else if (job.started_at) {
        const duration = (new Date() - new Date(job.started_at)) / 1000;
        document.getElementById('job-duration').textContent = formatDuration(duration) + ' (выполняется)';
    }

    // Update progress bar
    if (job.status === 'running') {
        const progressFill = document.getElementById('progress-fill');
        // Simulate progress (we don't have real progress data)
        const currentWidth = parseFloat(progressFill.style.width) || 0;
        if (currentWidth < 90) {
            progressFill.style.width = Math.min(currentWidth + 10, 90) + '%';
        }
    } else if (job.status === 'completed') {
        document.getElementById('progress-fill').style.width = '100%';
    }

    // Show result or error
    if (job.status === 'completed' && job.result) {
        const resultOutput = document.getElementById('result-output');
        const resultContent = document.getElementById('result-content');
        resultContent.textContent = JSON.stringify(job.result, null, 2);
        resultOutput.style.display = 'block';
        document.getElementById('error-message').style.display = 'none';
    } else if (job.status === 'failed' && job.error) {
        const errorMessage = document.getElementById('error-message');
        errorMessage.textContent = `❌ Ошибка: ${job.error}`;
        errorMessage.style.display = 'block';
        document.getElementById('result-output').style.display = 'none';
    }
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
        'other': '🔧 Другое',
    };
    return categoryMap[category] || category;
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
});
