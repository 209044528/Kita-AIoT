class App {
    constructor() {
        this.apiBase = '/api/v1';
        this.devicesContainer = document.getElementById('devices-container');
        this.alarmsContainer = document.getElementById('alarms-container');
        this.onlineCountEl = document.getElementById('online-count');
        
        this.deviceTemplate = document.getElementById('device-card-template');
        this.alarmTemplate = document.getElementById('alarm-item-template');
        
        this.devices = [];
        this.alarms = [];
        
        this.init();
    }

    async init() {
        await this.fetchData();
        // Set up polling every 10 seconds
        setInterval(() => this.fetchData(), 10000);
    }

    async fetchData() {
        try {
            // In a real app we'd fetch devices from an endpoint like /devices. 
            // Currently backend doesn't have a list all devices endpoint, but we can fetch alarms which give us device ids, 
            // or we know the 3 mock devices. Let's hardcode fetching the 3 known devices for the demo.
            const deviceIds = ['device-001', 'device-002', 'device-003'];
            const devicePromises = deviceIds.map(id => 
                fetch(`${this.apiBase}/devices/${id}/status`).then(res => res.json()).catch(() => null)
            );
            
            const devicesData = await Promise.all(devicePromises);
            this.devices = devicesData.filter(d => d && !d.detail);
            
            const alarmsRes = await fetch(`${this.apiBase}/alarms/`);
            const alarmsData = await alarmsRes.json();
            this.alarms = alarmsData.alarms || [];
            
            this.render();
        } catch (error) {
            console.error("Failed to fetch data:", error);
        }
    }

    render() {
        this.renderDevices();
        this.renderAlarms();
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
}

// Initialize App when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
