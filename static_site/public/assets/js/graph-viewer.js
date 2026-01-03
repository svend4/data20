/**
 * Graph Viewer v2.0
 * Визуализация связей между файлами Knowledge Base
 */

class GraphViewer {
    constructor() {
        this.network = null;
        this.nodes = new vis.DataSet([]);
        this.edges = new vis.DataSet([]);
        this.graphData = null;

        this.init();
    }

    async init() {
        // Создать секцию графа
        this.createGraphSection();

        // Загрузить данные
        await this.loadGraphData();

        // Рендерить граф
        this.renderGraph();
    }

    createGraphSection() {
        // Проверить, есть ли уже секция
        if (document.getElementById('graph-viewer-section')) {
            return;
        }

        const graphHTML = `
            <section id="graph-viewer-section" class="graph-section">
                <div class="graph-header">
                    <h2>🕸️ Knowledge Graph</h2>
                    <div class="graph-controls">
                        <select id="graph-layout" onchange="graphViewer.changeLayout(this.value)">
                            <option value="forceDirected">Force-Directed</option>
                            <option value="hierarchical">Hierarchical</option>
                            <option value="circular">Circular</option>
                        </select>
                        <select id="graph-filter" onchange="graphViewer.filterGraph(this.value)">
                            <option value="all">All Files</option>
                            <option value="html">HTML Only</option>
                            <option value="json">JSON Only</option>
                            <option value="connected">Connected Only</option>
                        </select>
                        <button onclick="graphViewer.fitGraph()" class="btn-icon" title="Fit to screen">
                            ⛶
                        </button>
                        <button onclick="graphViewer.resetGraph()" class="btn-icon" title="Reset">
                            🔄
                        </button>
                        <button onclick="graphViewer.toggleFullscreen()" class="btn-icon" title="Fullscreen">
                            ⛶
                        </button>
                    </div>
                </div>

                <div class="graph-container-wrapper">
                    <div id="knowledge-graph-container" class="graph-container"></div>

                    <div class="graph-sidebar">
                        <div class="graph-legend">
                            <h4>Legend</h4>
                            <div class="legend-items">
                                <div class="legend-item">
                                    <span class="node-sample html"></span>
                                    <span>HTML Files</span>
                                </div>
                                <div class="legend-item">
                                    <span class="node-sample json"></span>
                                    <span>JSON Files</span>
                                </div>
                                <div class="legend-item">
                                    <span class="node-sample csv"></span>
                                    <span>CSV Files</span>
                                </div>
                                <div class="legend-item">
                                    <span class="node-sample md"></span>
                                    <span>Markdown Files</span>
                                </div>
                            </div>
                        </div>

                        <div class="graph-stats">
                            <h4>Statistics</h4>
                            <div class="stat-items">
                                <div class="stat-row">
                                    <span>Nodes:</span>
                                    <span id="graph-node-count">-</span>
                                </div>
                                <div class="stat-row">
                                    <span>Edges:</span>
                                    <span id="graph-edge-count">-</span>
                                </div>
                                <div class="stat-row">
                                    <span>Clusters:</span>
                                    <span id="graph-cluster-count">-</span>
                                </div>
                            </div>
                        </div>

                        <div class="graph-info">
                            <h4>Selected Node</h4>
                            <div id="node-info" class="node-info-content">
                                <p class="info-placeholder">Click on a node to see details</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        `;

        // Вставить после dashboard или перед первой category
        const dashboard = document.getElementById('interactive-dashboard');
        const insertPoint = dashboard || document.querySelector('.category-section');

        if (insertPoint) {
            insertPoint.insertAdjacentHTML('afterend', graphHTML);
        } else {
            document.querySelector('.main-content').insertAdjacentHTML('beforeend', graphHTML);
        }
    }

    async loadGraphData() {
        try {
            // Попытаться загрузить граф из данных
            const response = await fetch('../knowledge_graph_data.json');
            if (response.ok) {
                this.graphData = await response.json();
            } else {
                // Создать граф из файлов на странице
                this.graphData = this.buildGraphFromDOM();
            }

            console.log('Graph data loaded:', this.graphData);
        } catch (error) {
            console.warn('Failed to load graph data, building from DOM:', error);
            this.graphData = this.buildGraphFromDOM();
        }
    }

    buildGraphFromDOM() {
        const nodes = [];
        const edges = [];
        const nodeMap = new Map();

        // Собрать все файлы
        document.querySelectorAll('.file-card').forEach((card, index) => {
            const filename = card.getAttribute('data-filename') || `file-${index}`;
            const type = card.getAttribute('data-type') || 'unknown';
            const category = card.getAttribute('data-category') || 'other';

            const node = {
                id: filename,
                label: filename.replace(/\.(html|json|csv|md)$/, ''),
                type: type,
                category: category,
                title: filename
            };

            nodes.push(node);
            nodeMap.set(filename, node);
        });

        // Создать связи на основе схожести имён и категорий
        nodes.forEach(node1 => {
            nodes.forEach(node2 => {
                if (node1.id === node2.id) return;

                // Связать файлы с похожими именами
                const similarity = this.calculateSimilarity(node1.label, node2.label);
                if (similarity > 0.5) {
                    edges.push({
                        from: node1.id,
                        to: node2.id,
                        value: similarity
                    });
                }

                // Связать файлы одной категории
                if (node1.category === node2.category && node1.category !== 'other') {
                    edges.push({
                        from: node1.id,
                        to: node2.id,
                        value: 0.3,
                        dashes: true
                    });
                }
            });
        });

        return { nodes, edges };
    }

    calculateSimilarity(str1, str2) {
        // Простая мера схожести на основе общих слов
        const words1 = str1.toLowerCase().split(/[_\s-]+/);
        const words2 = str2.toLowerCase().split(/[_\s-]+/);

        const common = words1.filter(w => words2.includes(w)).length;
        const total = new Set([...words1, ...words2]).size;

        return common / total;
    }

    renderGraph() {
        const container = document.getElementById('knowledge-graph-container');
        if (!container) return;

        // Подготовить данные для vis.js
        this.prepareGraphData();

        // Опции графа
        const options = {
            nodes: {
                shape: 'dot',
                size: 16,
                font: {
                    size: 12,
                    color: '#2c3e50'
                },
                borderWidth: 2,
                shadow: true
            },
            edges: {
                width: 1,
                color: { inherit: 'both' },
                smooth: {
                    type: 'continuous'
                },
                arrows: {
                    to: {
                        enabled: false
                    }
                }
            },
            physics: {
                forceAtlas2Based: {
                    gravitationalConstant: -26,
                    centralGravity: 0.005,
                    springLength: 230,
                    springConstant: 0.18
                },
                maxVelocity: 146,
                solver: 'forceAtlas2Based',
                timestep: 0.35,
                stabilization: {
                    enabled: true,
                    iterations: 150
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true
            }
        };

        // Создать сеть
        this.network = new vis.Network(container, {
            nodes: this.nodes,
            edges: this.edges
        }, options);

        // Настроить события
        this.setupGraphEvents();

        // Обновить статистику
        this.updateGraphStats();
    }

    prepareGraphData() {
        if (!this.graphData || !this.graphData.nodes) return;

        // Очистить существующие данные
        this.nodes.clear();
        this.edges.clear();

        // Подготовить узлы
        const nodes = this.graphData.nodes.map(node => ({
            id: node.id,
            label: node.label || node.id,
            title: node.title || node.id,
            color: this.getColorByType(node.type || 'unknown'),
            size: (node.size || 1) * 15 + 10,
            group: node.type || 'unknown'
        }));

        // Подготовить рёбра
        const edges = (this.graphData.edges || []).map(edge => ({
            from: edge.from || edge.source,
            to: edge.to || edge.target,
            value: edge.value || edge.weight || 1,
            title: edge.label || '',
            dashes: edge.dashes || false
        }));

        // Добавить в DataSet
        this.nodes.add(nodes);
        this.edges.add(edges);
    }

    getColorByType(type) {
        const colors = {
            'html': { background: '#667eea', border: '#5568d3', highlight: { background: '#7e8ff0', border: '#667eea' } },
            'json': { background: '#f093fb', border: '#d77fe8', highlight: { background: '#f5a9fc', border: '#f093fb' } },
            'csv': { background: '#4facfe', border: '#3895e8', highlight: { background: '#6dbeff', border: '#4facfe' } },
            'md': { background: '#43e97b', border: '#2ed368', highlight: { background: '#5cee8f', border: '#43e97b' } },
            'unknown': { background: '#95a5a6', border: '#7f8c8d', highlight: { background: '#a8b9ba', border: '#95a5a6' } }
        };

        return colors[type.toLowerCase()] || colors.unknown;
    }

    setupGraphEvents() {
        // Клик на узел
        this.network.on('click', (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                this.showNodeInfo(nodeId);
            }
        });

        // Двойной клик - открыть файл
        this.network.on('doubleClick', (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                this.openFile(nodeId);
            }
        });

        // Hover эффект
        this.network.on('hoverNode', (params) => {
            this.highlightConnections(params.node);
        });

        this.network.on('blurNode', () => {
            this.resetHighlight();
        });

        // Стабилизация
        this.network.on('stabilizationIterationsDone', () => {
            this.network.setOptions({ physics: false });
        });
    }

    showNodeInfo(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node) return;

        // Найти связанные узлы
        const connectedEdges = this.network.getConnectedEdges(nodeId);
        const connectedNodes = this.network.getConnectedNodes(nodeId);

        const infoDiv = document.getElementById('node-info');
        infoDiv.innerHTML = `
            <div class="node-detail">
                <h5>${node.label}</h5>
                <div class="node-meta">
                    <div><strong>Type:</strong> ${node.group}</div>
                    <div><strong>Connections:</strong> ${connectedNodes.length}</div>
                    <div><strong>ID:</strong> ${node.id}</div>
                </div>
                <div class="node-connections">
                    <strong>Connected to:</strong>
                    <ul>
                        ${connectedNodes.slice(0, 10).map(id => {
                            const connectedNode = this.nodes.get(id);
                            return `<li>${connectedNode ? connectedNode.label : id}</li>`;
                        }).join('')}
                        ${connectedNodes.length > 10 ? `<li>... and ${connectedNodes.length - 10} more</li>` : ''}
                    </ul>
                </div>
                <button class="btn btn-primary" onclick="graphViewer.openFile('${node.id}')">
                    Open File
                </button>
            </div>
        `;
    }

    openFile(nodeId) {
        // Попытаться найти и открыть файл
        const filename = nodeId;
        window.open(`../${filename}`, '_blank');
    }

    highlightConnections(nodeId) {
        const connectedNodes = this.network.getConnectedNodes(nodeId);

        // Выделить связанные узлы
        const allNodes = this.nodes.get({ returnType: 'Object' });
        Object.keys(allNodes).forEach(id => {
            if (id === nodeId || connectedNodes.includes(id)) {
                allNodes[id].opacity = 1;
            } else {
                allNodes[id].opacity = 0.3;
            }
        });

        this.nodes.update(Object.values(allNodes));
    }

    resetHighlight() {
        const allNodes = this.nodes.get({ returnType: 'Object' });
        Object.keys(allNodes).forEach(id => {
            allNodes[id].opacity = 1;
        });
        this.nodes.update(Object.values(allNodes));
    }

    changeLayout(layout) {
        let options = {};

        switch (layout) {
            case 'hierarchical':
                options = {
                    layout: {
                        hierarchical: {
                            enabled: true,
                            direction: 'UD',
                            sortMethod: 'directed',
                            levelSeparation: 150,
                            nodeSpacing: 100
                        }
                    },
                    physics: false
                };
                break;

            case 'circular':
                options = {
                    layout: {
                        hierarchical: false
                    },
                    physics: {
                        enabled: true,
                        solver: 'repulsion',
                        repulsion: {
                            centralGravity: 0.5,
                            springLength: 200,
                            springConstant: 0.05,
                            nodeDistance: 200,
                            damping: 0.09
                        }
                    }
                };
                // Расположить узлы по кругу
                this.arrangeCircular();
                break;

            case 'forceDirected':
            default:
                options = {
                    layout: {
                        hierarchical: false
                    },
                    physics: {
                        enabled: true,
                        forceAtlas2Based: {
                            gravitationalConstant: -26,
                            centralGravity: 0.005,
                            springLength: 230,
                            springConstant: 0.18
                        },
                        solver: 'forceAtlas2Based'
                    }
                };
                break;
        }

        this.network.setOptions(options);
    }

    arrangeCircular() {
        const nodeIds = this.nodes.getIds();
        const radius = 300;
        const angleStep = (2 * Math.PI) / nodeIds.length;

        const updates = nodeIds.map((id, index) => {
            const angle = index * angleStep;
            return {
                id: id,
                x: Math.cos(angle) * radius,
                y: Math.sin(angle) * radius,
                fixed: { x: false, y: false }
            };
        });

        this.nodes.update(updates);
        this.network.fit();
    }

    filterGraph(filter) {
        let nodesToShow = this.nodes.getIds();

        switch (filter) {
            case 'html':
                nodesToShow = this.nodes.get({
                    filter: node => node.group === 'html'
                }).map(n => n.id);
                break;

            case 'json':
                nodesToShow = this.nodes.get({
                    filter: node => node.group === 'json'
                }).map(n => n.id);
                break;

            case 'connected':
                // Показать только узлы с хотя бы одним соединением
                nodesToShow = this.nodes.get({
                    filter: node => {
                        const connections = this.network.getConnectedNodes(node.id);
                        return connections && connections.length > 0;
                    }
                }).map(n => n.id);
                break;

            case 'all':
            default:
                // Показать все
                break;
        }

        // Обновить видимость узлов
        const allNodes = this.nodes.get({ returnType: 'Object' });
        Object.keys(allNodes).forEach(id => {
            allNodes[id].hidden = !nodesToShow.includes(id);
        });
        this.nodes.update(Object.values(allNodes));

        this.updateGraphStats();
        this.network.fit();
    }

    fitGraph() {
        this.network.fit({
            animation: {
                duration: 1000,
                easingFunction: 'easeInOutQuad'
            }
        });
    }

    resetGraph() {
        this.network.setOptions({
            physics: {
                enabled: true
            }
        });

        setTimeout(() => {
            this.network.setOptions({ physics: false });
        }, 2000);
    }

    toggleFullscreen() {
        const section = document.getElementById('graph-viewer-section');
        if (section) {
            section.classList.toggle('fullscreen');
            setTimeout(() => {
                this.network.fit();
            }, 100);
        }
    }

    updateGraphStats() {
        const visibleNodes = this.nodes.get({
            filter: node => !node.hidden
        });

        const visibleEdges = this.edges.get({
            filter: edge => {
                const fromNode = this.nodes.get(edge.from);
                const toNode = this.nodes.get(edge.to);
                return fromNode && toNode && !fromNode.hidden && !toNode.hidden;
            }
        });

        // Подсчитать кластеры (упрощённо - группы по типу)
        const groups = new Set(visibleNodes.map(n => n.group));

        document.getElementById('graph-node-count').textContent = visibleNodes.length;
        document.getElementById('graph-edge-count').textContent = visibleEdges.length;
        document.getElementById('graph-cluster-count').textContent = groups.size;
    }
}

// Глобальная инициализация
let graphViewer;
document.addEventListener('DOMContentLoaded', () => {
    // Подождать, пока vis.js загрузится
    if (typeof vis !== 'undefined') {
        graphViewer = new GraphViewer();
    } else {
        console.warn('vis.js not loaded, graph viewer disabled');
    }
});
