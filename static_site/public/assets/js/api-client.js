/**
 * API Client for Data20 Backend
 * Phase 4.4: Frontend integration with Backend API
 */

class APIClient {
    constructor(baseURL = 'http://localhost:8001') {
        this.baseURL = baseURL;
        this.ws = null;
        this.wsCallbacks = new Map();
    }

    /**
     * Проверить доступность API
     */
    async checkAvailability() {
        try {
            const response = await fetch(`${this.baseURL}/`);
            if (response.ok) {
                return await response.json();
            }
            return null;
        } catch (error) {
            console.log('[API] Backend not available:', error.message);
            return null;
        }
    }

    /**
     * Получить все инструменты
     */
    async getTools() {
        const response = await fetch(`${this.baseURL}/api/tools`);
        if (!response.ok) throw new Error('Failed to fetch tools');
        return await response.json();
    }

    /**
     * Получить информацию об инструменте
     */
    async getTool(toolName) {
        const response = await fetch(`${this.baseURL}/api/tools/${toolName}`);
        if (!response.ok) throw new Error(`Tool ${toolName} not found`);
        return await response.json();
    }

    /**
     * Получить категории
     */
    async getCategories() {
        const response = await fetch(`${this.baseURL}/api/categories`);
        if (!response.ok) throw new Error('Failed to fetch categories');
        return await response.json();
    }

    /**
     * Получить инструменты по категории
     */
    async getToolsByCategory(category) {
        const response = await fetch(`${this.baseURL}/api/categories/${category}`);
        if (!response.ok) throw new Error(`Category ${category} not found`);
        return await response.json();
    }

    /**
     * Поиск инструментов
     */
    async searchTools(query) {
        const response = await fetch(`${this.baseURL}/api/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Search failed');
        return await response.json();
    }

    /**
     * Запустить инструмент
     */
    async runTool(toolName, parameters = {}) {
        const response = await fetch(`${this.baseURL}/api/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tool_name: toolName,
                parameters: parameters
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to run tool');
        }

        return await response.json();
    }

    /**
     * Получить статус задачи
     */
    async getJobStatus(jobId) {
        const response = await fetch(`${this.baseURL}/api/jobs/${jobId}`);
        if (!response.ok) throw new Error(`Job ${jobId} not found`);
        return await response.json();
    }

    /**
     * Получить все задачи
     */
    async getAllJobs() {
        const response = await fetch(`${this.baseURL}/api/jobs`);
        if (!response.ok) throw new Error('Failed to fetch jobs');
        return await response.json();
    }

    /**
     * Отменить задачу
     */
    async cancelJob(jobId) {
        const response = await fetch(`${this.baseURL}/api/jobs/${jobId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error(`Failed to cancel job ${jobId}`);
        return await response.json();
    }

    /**
     * Получить статистику системы
     */
    async getSystemStats() {
        const response = await fetch(`${this.baseURL}/api/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        return await response.json();
    }

    /**
     * Подключиться к WebSocket для real-time обновлений
     */
    connectWebSocket() {
        const wsURL = this.baseURL.replace('http', 'ws') + '/ws';

        this.ws = new WebSocket(wsURL);

        this.ws.onopen = () => {
            console.log('[WS] Connected to backend');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this._handleWebSocketMessage(data);
        };

        this.ws.onerror = (error) => {
            console.error('[WS] Error:', error);
        };

        this.ws.onclose = () => {
            console.log('[WS] Disconnected');
            // Переподключение через 5 секунд
            setTimeout(() => this.connectWebSocket(), 5000);
        };
    }

    /**
     * Подписаться на обновления задачи
     */
    subscribeToJob(jobId, callback) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('[WS] WebSocket not connected');
            return;
        }

        this.wsCallbacks.set(jobId, callback);

        this.ws.send(JSON.stringify({
            action: 'subscribe',
            job_id: jobId
        }));
    }

    /**
     * Отписаться от обновлений задачи
     */
    unsubscribeFromJob(jobId) {
        this.wsCallbacks.delete(jobId);
    }

    /**
     * Обработать сообщение WebSocket
     */
    _handleWebSocketMessage(data) {
        const { type, job_id } = data;

        const callback = this.wsCallbacks.get(job_id);
        if (callback) {
            callback(data);

            // Если задача завершена, удалить callback
            if (type === 'complete') {
                this.wsCallbacks.delete(job_id);
            }
        }
    }

    /**
     * Закрыть WebSocket соединение
     */
    disconnectWebSocket() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Singleton instance
const apiClient = new APIClient();

// Auto-export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
}
