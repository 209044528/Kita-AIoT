# n8n 工作流

访问 `http://localhost:5678`，导入 `workflows/` 下三个 JSON：

- `01_webhook_alarm.json`：外部 Webhook → Kita-AIoT Agent。
- `02_http_demo.json`：手动构造告警 → HTTP 调用 Agent。
- `03_mqtt_alarm.json`：MQTT 告警 → HTTP 调用 Agent。

仓库提供了仅连接本地匿名 Mosquitto 的 `credentials/mqtt.json`。可自动导入：

```powershell
docker compose exec -T n8n n8n import:credentials `
  --input=/credentials/mqtt.json `
  --projectId=<你的 n8n 项目 ID>
```

也可以在页面为 `MQTT 告警` 节点创建凭据：

- Protocol：`mqtt`
- Host：`mqtt`
- Port：`1883`
- Client ID：`n8n-kita-aiot`

保存并激活工作流后，向 `aiot/device/alarm/n8n` 发布消息即可触发。使用独立主题可避免 FastAPI 原生 MQTT Consumer 与 n8n 重复消费同一告警。

Webhook 工作流激活后：

```powershell
curl.exe -X POST http://localhost:5678/webhook/kita-aiot/alarm `
  -H "Content-Type: application/json" `
  -d '{"device_id":"device-003","alarm_type":"device_offline","level":"critical","message":"n8n Webhook 演示","temperature":29.0,"platform":"auto"}'
```
