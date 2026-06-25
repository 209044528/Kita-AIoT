# 演示步骤

## 1. 启动

```powershell
docker compose up -d --build
```

地址：

- Web UI：<http://localhost:8001>
- n8n：<http://localhost:5678>
- MinIO：<http://localhost:9001>

## 2. Dify 演示

在页面“告警 → Agent → RAG → 工单”选择 Dify，运行告警。检查：

- 返回平台为 `dify`。
- 工作流记录为 `succeeded`。
- Dify 控制台出现运行记录。
- 引用列表包含说明书/SOP。
- critical 或连续 warning 创建工单。

## 3. 百炼演示

在 `.env` 配置 `BAILIAN_API_KEY`，重建 API 容器：

```powershell
docker compose up -d --build api
```

页面选择“阿里百炼”运行同一告警，比较两个平台输出。

## 4. n8n 演示

导入 `n8n/workflows/` 下三个工作流，配置 MQTT 凭据并激活。

Webhook：

```powershell
curl.exe -X POST http://localhost:5678/webhook/kita-aiot/alarm `
  -H "Content-Type: application/json" `
  -d '{"device_id":"device-003","alarm_type":"device_offline","level":"critical","message":"n8n Webhook 告警","platform":"dify"}'
```

MQTT：

```powershell
.\.venv\Scripts\python.exe scripts\mqtt_alarm_simulator.py `
  --host localhost `
  --topic aiot/device/alarm/n8n `
  --count 1 `
  --platform bailian
```

## 5. 知识库问答

在页面知识库问答区域分别选择本地 RAG、Dify 和百炼，提问：

- 温度超过 80 摄氏度时如何处理？
- 设备离线但电量正常，应优先检查什么？
- 哪些情况必须创建工单？
