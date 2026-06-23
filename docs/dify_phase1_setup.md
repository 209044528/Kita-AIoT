# Dify 一阶段配置说明

## 1. 创建知识库

在 Dify 控制台中新建知识库，上传以下文件：

- `docs/knowledge_base/device_manual.md`
- `docs/knowledge_base/maintenance_sop.md`
- `docs/knowledge_base/alarm_faq.md`
- `docs/knowledge_base/troubleshooting_guide.md`
- `docs/knowledge_base/historical_work_orders.md`

建议配置：

- 分段方式：按标题或自动分段。
- Top K：3。
- 相似度阈值：0.4 到 0.6。
- 开启引用来源返回。

## 2. 创建聊天应用

创建 Chatflow 或 Agent 应用，系统 Prompt 使用 `docs/prompts/dify_phase1_prompt.md`。

## 3. 配置 HTTP 工具

本地启动 FastAPI 后，将以下接口配置为 Dify 工具。若 Dify 运行在容器内，URL 中的 `localhost` 需要替换为宿主机 IP 或 Docker 网络地址。

| 工具名称 | Method | URL |
| --- | --- | --- |
| `get_device_status` | GET | `http://localhost:8001/api/v1/devices/{device_id}/status` |
| `get_recent_alarms` | GET | `http://localhost:8001/api/v1/devices/{device_id}/alarms` |
| `create_work_order` | POST | `http://localhost:8001/api/v1/work-orders` |
| `device_diagnosis` | POST | `http://localhost:8001/api/v1/tools/device-diagnosis` |

前三个是第一阶段核心工具，`device_diagnosis` 是可选演示接口，用于快速展示“状态 + 告警 + 知识库式建议”的组合结果。

## 4. 建议测试问题

- `device-001 温度高应该怎么处理？请查询设备状态和历史告警。`
- `device-003 离线超过 30 分钟，是否需要创建工单？`
- `温度超过 80 摄氏度时 SOP 怎么要求？`

## 5. 截图清单

完成 Dify 页面配置后，建议截图保存到 `docs/screenshots/`：

- `dify_knowledge_base.png`：知识库文档列表。
- `dify_tools.png`：三个 HTTP 工具配置。
- `dify_chat_demo.png`：一次问答演示，包含引用来源和工具调用结果。
