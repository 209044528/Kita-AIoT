class App {
    constructor() {
        this.apiBase = '/api/v1';
        this.devicesContainer = document.getElementById('devices-container');
        this.alarmsContainer = document.getElementById('alarms-container');
        this.workOrdersContainer = document.getElementById('work-orders-container');
        this.workflowsContainer = document.getElementById('workflows-container');
        this.onlineCountEl = document.getElementById('online-count');
        this.workflowCountEl = document.getElementById('workflow-count');
        this.difyStatusEl = document.getElementById('dify-status');
        this.bailianStatusEl = document.getElementById('bailian-status');
        this.alarmForm = document.getElementById('alarm-form');
        this.knowledgeForm = document.getElementById('knowledge-form');
        
        this.deviceTemplate = document.getElementById('device-card-template');
        this.alarmTemplate = document.getElementById('alarm-item-template');
        this.recordTemplate = document.getElementById('record-item-template');
        
        this.devices = [];
        this.alarms = [];
        this.workOrders = [];
        this.workflows = [];
        
        this.init();
    }

    async init() {
        this.alarmForm.addEventListener('submit', event => this.runAlarmWorkflow(event));
        this.knowledgeForm.addEventListener('submit', event => this.askKnowledge(event));
        await this.fetchData();
        // Set up polling every 10 seconds
        setInterval(() => this.fetchData(), 10000);
    }

    async fetchData() {
        try {
            const [devicesRes, alarmsRes, ordersRes, workflowsRes, platformsRes] = await Promise.all([
                fetch(`${this.apiBase}/devices/`),
                fetch(`${this.apiBase}/alarms/`),
                fetch(`${this.apiBase}/work-orders/`),
                fetch(`${this.apiBase}/workflow-executions?limit=20`),
                fetch(`${this.apiBase}/platforms/status`)
            ]);
            const devicesData = await devicesRes.json();
            const alarmsData = await alarmsRes.json();
            const ordersData = await ordersRes.json();
            const workflowsData = await workflowsRes.json();
            const platformsData = await platformsRes.json();
            this.devices = devicesData.devices || [];
            this.alarms = alarmsData.alarms || [];
            this.workOrders = ordersData.work_orders || [];
            this.workflows = workflowsData.executions || [];
            this.platforms = platformsData;
            
            this.render();
        } catch (error) {
            console.error("Failed to fetch data:", error);
        }
    }

    render() {
        this.renderDevices();
        this.renderAlarms();
        this.renderWorkOrders();
        this.renderWorkflows();
        this.renderPlatforms();
    }

    renderDevices() {
        this.devicesContainer.innerHTML = '';
        let onlineCount = 0;

        this.devices.forEach((device, index) => {
            if (device.status === 'online') onlineCount++;
            
            const clone = this.deviceTemplate.content.cloneNode(true);
            const card = clone.querySelector('.device-card');
            
            // Stagger animation
            card.style.animationDelay = `${index * 0.1}s`;
            
            clone.querySelector('.device-name').textContent = device.name || device.device_id;
            
            const statusEl = clone.querySelector('.status-indicator');
            statusEl.textContent = device.status;
            statusEl.className = `status-indicator ${device.status}`;
            
            clone.querySelector('.location').textContent = device.location || 'Unknown Location';
            
            const tempEl = clone.querySelector('.temp-value');
            if (device.temperature !== null && device.temperature !== undefined) {
                tempEl.textContent = `${device.temperature.toFixed(1)}°C`;
                if (device.temperature > 80) tempEl.style.color = 'var(--status-critical)';
            } else {
                tempEl.textContent = '--°C';
            }
            
            const batteryBar = clone.querySelector('.battery-bar');
            if (device.battery_level !== null && device.battery_level !== undefined) {
                batteryBar.style.width = `${device.battery_level}%`;
                if (device.battery_level < 20) batteryBar.style.backgroundColor = 'var(--status-offline)';
                else if (device.battery_level < 50) batteryBar.style.backgroundColor = 'var(--status-warning)';
            } else {
                batteryBar.style.width = '0%';
            }

            this.devicesContainer.appendChild(clone);
        });

        this.onlineCountEl.textContent = onlineCount;
    }

    renderAlarms() {
        this.alarmsContainer.innerHTML = '';
        
        if (this.alarms.length === 0) {
            this.alarmsContainer.innerHTML = '<div class="empty-state">当前无告警</div>';
            return;
        }

        this.alarms.forEach((alarm, index) => {
            const clone = this.alarmTemplate.content.cloneNode(true);
            const item = clone.querySelector('.alarm-item');
            
            item.style.animationDelay = `${index * 0.1}s`;
            item.classList.add(alarm.level);
            
            const icon = clone.querySelector('.alarm-icon');
            icon.textContent = alarm.level === 'critical' ? '🔴' : '🟠';
            
            const typeMap = {
                'temperature_high': '高温告警',
                'device_offline': '设备离线',
                'vibration_high': '振动异常'
            };
            
            clone.querySelector('.alarm-type').textContent = typeMap[alarm.alarm_type] || alarm.alarm_type;
            
            const time = new Date(alarm.created_at);
            clone.querySelector('.alarm-time').textContent = time.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            clone.querySelector('.alarm-message').textContent = alarm.message;
            clone.querySelector('.alarm-device').textContent = alarm.device_id;
            
            this.alarmsContainer.appendChild(clone);
        });
    }

    renderWorkOrders() {
        this.workOrdersContainer.innerHTML = '';
        if (this.workOrders.length === 0) {
            this.workOrdersContainer.innerHTML = '<div class="empty-state">暂无工单</div>';
            return;
        }
        this.workOrders.slice(0, 10).forEach(order => {
            const clone = this.recordTemplate.content.cloneNode(true);
            clone.querySelector('.record-title').textContent = order.title;
            clone.querySelector('.record-meta').textContent = `${order.device_id} · ${order.priority}`;
            const status = clone.querySelector('.record-status');
            status.textContent = order.status;
            status.classList.add(order.status);
            this.workOrdersContainer.appendChild(clone);
        });
    }

    renderWorkflows() {
        this.workflowsContainer.innerHTML = '';
        this.workflowCountEl.textContent = this.workflows.length;
        if (this.workflows.length === 0) {
            this.workflowsContainer.innerHTML = '<div class="empty-state">暂无执行记录</div>';
            return;
        }
        this.workflows.slice(0, 10).forEach(workflow => {
            const clone = this.recordTemplate.content.cloneNode(true);
            clone.querySelector('.record-title').textContent = workflow.trigger_ref || workflow.execution_id;
            clone.querySelector('.record-meta').textContent = `${workflow.trigger_type} · ${workflow.platform}`;
            const status = clone.querySelector('.record-status');
            status.textContent = workflow.status;
            status.classList.add(workflow.status);
            this.workflowsContainer.appendChild(clone);
        });
    }

    renderPlatforms() {
        const setBadge = (element, name, configured) => {
            element.textContent = `${name} ${configured ? '已连接' : '未配置'}`;
            element.classList.toggle('connected', configured);
        };
        setBadge(this.difyStatusEl, 'Dify', Boolean(this.platforms?.dify?.configured));
        setBadge(this.bailianStatusEl, '百炼', Boolean(this.platforms?.bailian?.configured));
    }

    async runAlarmWorkflow(event) {
        event.preventDefault();
        const result = document.getElementById('alarm-result');
        const button = this.alarmForm.querySelector('button');
        button.disabled = true;
        result.textContent = 'Agent 正在分析，可能需要几十秒...';
        const deviceId = document.getElementById('alarm-device').value;
        const level = document.getElementById('alarm-level').value;
        const typeMap = {
            'device-001': 'temperature_high',
            'device-002': 'vibration_high',
            'device-003': 'device_offline'
        };
        try {
            const response = await fetch(`${this.apiBase}/alarms/report`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    device_id: deviceId,
                    alarm_type: typeMap[deviceId],
                    level,
                    message: document.getElementById('alarm-message').value,
                    temperature: deviceId === 'device-001' ? 86.8 : null,
                    platform: document.getElementById('alarm-platform').value
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || '工作流执行失败');
            const summary = {
                execution_id: data.execution_id,
                alarm_id: data.result?.alarm_id,
                platform: data.result?.agent?.platform,
                agent_analysis: data.result?.agent?.analysis,
                rag_references: (data.result?.rag_references || []).map(item => `${item.title} / ${item.section}`),
                work_order_id: data.result?.work_order_id
            };
            result.textContent = JSON.stringify(summary, null, 2);
            await this.fetchData();
        } catch (error) {
            result.textContent = `执行失败：${error.message}`;
        } finally {
            button.disabled = false;
        }
    }

    async askKnowledge(event) {
        event.preventDefault();
        const answer = document.getElementById('knowledge-answer');
        const references = document.getElementById('knowledge-references');
        const button = this.knowledgeForm.querySelector('button');
        button.disabled = true;
        answer.textContent = '正在检索知识库并生成回答...';
        references.innerHTML = '';
        try {
            const response = await fetch(`${this.apiBase}/knowledge/ask`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    question: document.getElementById('knowledge-question').value,
                    platform: document.getElementById('knowledge-platform').value,
                    device_id: document.getElementById('knowledge-device').value || null
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || '知识问答失败');
            answer.textContent = `[${data.platform}] ${data.answer}`;
            (data.references || []).forEach(item => {
                const card = document.createElement('div');
                card.className = 'reference-card';
                const title = document.createElement('strong');
                title.textContent = `${item.title} / ${item.section}`;
                const content = document.createElement('p');
                content.textContent = item.content;
                card.append(title, content);
                references.appendChild(card);
            });
        } catch (error) {
            answer.textContent = `回答失败：${error.message}`;
        } finally {
            button.disabled = false;
        }
    }
}

// Initialize App when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
