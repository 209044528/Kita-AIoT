class App {
    constructor() {
        this.apiBase = '/api/v1';
        this.devicesContainer = document.getElementById('devices-container');
        this.alarmsContainer = document.getElementById('alarms-container');
        this.workOrdersContainer = document.getElementById('work-orders-container');
        this.workflowsContainer = document.getElementById('workflows-container');
        this.onlineCountEl = document.getElementById('online-count');
        this.workflowCountEl = document.getElementById('workflow-count');
        
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
        await this.fetchData();
        // Set up polling every 10 seconds
        setInterval(() => this.fetchData(), 10000);
    }

    async fetchData() {
        try {
            const [devicesRes, alarmsRes, ordersRes, workflowsRes] = await Promise.all([
                fetch(`${this.apiBase}/devices/`),
                fetch(`${this.apiBase}/alarms/`),
                fetch(`${this.apiBase}/work-orders/`),
                fetch(`${this.apiBase}/workflow-executions?limit=20`)
            ]);
            const devicesData = await devicesRes.json();
            const alarmsData = await alarmsRes.json();
            const ordersData = await ordersRes.json();
            const workflowsData = await workflowsRes.json();
            this.devices = devicesData.devices || [];
            this.alarms = alarmsData.alarms || [];
            this.workOrders = ordersData.work_orders || [];
            this.workflows = workflowsData.executions || [];
            
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
}

// Initialize App when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
