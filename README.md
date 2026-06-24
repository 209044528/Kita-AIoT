# Kita-AIoT：设备运维智能体工作流系统

Kita-AIoT 是一个面向 AIoT 设备运维场景的智能体工作流 Demo。二阶段实现了从设备告警到智能分析、知识检索、工单生成和执行追踪的完整技术链路：

> MQTT 告警 → FastAPI 工作流 → Dify RAG/Agent → PostgreSQL 持久化 → MinIO 文档 → 工单与日志

## 二阶段完成情况

| 目标 | 实现 |
| --- | --- |
| 一个 AI 平台完整接入 | Dify 作为主平台，提供 Workflow API 调用、RAG、5 个工具导入文件和完整配置步骤 |
| 另一个平台基础接入 | 阿里云百炼通过 OpenAI 兼容接口完成连通测试 |
| FastAPI 工具约 5 个 | 设备状态、历史告警、设备诊断、创建工单、查询设备文档 |
| PostgreSQL | 设备、告警、工单、调用日志、工作流执行、文档元数据 |
| MQTT 触发工作流 | FastAPI 启动 MQTT Consumer，告警到达后自动执行本地/Dify 工作流 |
| MinIO | 上传设备文档或图片、查询元数据、生成临时下载地址 |
| 可观测性 | HTTP 调用日志、工作流输入输出、状态和错误记录 |
| README / 架构图 / 演示 | 本文、Mermaid 架构图、录制脚本与素材目录 |

说明：Dify 和百炼真实调用需要你自己的平台地址与 API Key。未配置 Dify 时，系统会使用本地规则诊断，便于离线开发和测试。

## 系统架构

```mermaid
flowchart TB
    Device["AIoT 设备 / 告警模拟器"] -->|"MQTT"| Broker["Mosquitto"]
    Broker --> Consumer["FastAPI MQTT Consumer"]
    Consumer --> Workflow["告警工作流引擎"]
    Workflow -->|"Workflow API"| Dify["Dify + RAG"]
    Dify -->|"5 个 HTTP 工具"| API["FastAPI Agent Tools"]
    Bailian["阿里云百炼"] <-. "基础连通" .-> API
    Web["运维监控页面"] --> API
    API --> PostgreSQL[("PostgreSQL")]
    Workflow --> PostgreSQL
    API --> MinIO[("MinIO")]
```

详细设计见 [docs/phase2_design.md](docs/phase2_design.md)。

## 核心功能

### 告警工作流

MQTT Consumer 订阅 `aiot/device/alarm`。收到告警后：

1. 创建工作流执行记录。
2. 保存告警并更新设备状态。
3. 查询最近告警并生成本地诊断。
4. 配置 Dify 后调用 Dify Workflow API。
5. `critical` 告警自动创建 P1 工单。
6. 保存工作流输出、状态与错误。

HTTP 告警上报接口使用同一条工作流，便于测试。

### 5 个 Agent 核心工具

| 工具 | 接口 | 功能 |
| --- | --- | --- |
| `get_device_status` | `GET /api/v1/devices/{device_id}/status` | 查询设备状态 |
| `get_recent_alarms` | `GET /api/v1/devices/{device_id}/alarms` | 查询最近告警 |
| `diagnose_device` | `POST /api/v1/devices/diagnosis` | 状态、告警与规则式诊断 |
| `create_work_order` | `POST /api/v1/work-orders/` | 创建运维工单 |
| `list_device_documents` | `GET /api/v1/documents/` | 查询 MinIO 文档元数据 |

Dify 可直接导入 [docs/dify_tools_openapi.yaml](docs/dify_tools_openapi.yaml)。

### 数据持久化

二阶段使用 SQLAlchemy，正式环境连接 PostgreSQL。数据表：

- `devices`
- `alarms`
- `work_orders`
- `call_logs`
- `workflow_executions`
- `documents`

本地未配置 PostgreSQL 时默认使用 `kita_aiot.db` SQLite 文件，接口行为一致。

### MinIO 文档管理

- 上传设备说明书、现场图片或维修附件。
- 文档元数据写入数据库。
- 文件对象存入 MinIO。
- 下载时生成 1 小时有效的预签名 URL。

### Web 运维看板

访问首页可查看：

- 设备状态、温度、电量和位置。
- 实时告警。
- 自动生成或人工创建的工单。
- MQTT/HTTP 工作流执行记录。

页面每 10 秒自动刷新。

## 项目结构

```text
Kita-AIoT/
├─ app/
│  ├─ api/routers/                # 设备、告警、工单、文档、运维接口
│  ├─ core/                       # 配置、数据库、种子数据、序列化
│  ├─ mqtt/consumer.py            # MQTT 告警消费者
│  ├─ services/                   # 诊断、Dify/百炼、MinIO、工作流
│  ├─ models.py                   # SQLAlchemy 数据模型
│  └─ main.py                     # FastAPI 应用与调用日志中间件
├─ deploy/mosquitto.conf
├─ docs/
│  ├─ dify_phase2_setup.md
│  ├─ bailian_phase2_setup.md
│  ├─ dify_tools_openapi.yaml
│  ├─ phase2_design.md
│  ├─ demo/
│  └─ knowledge_base/
├─ scripts/mqtt_alarm_simulator.py
├─ web/
├─ .env.example
├─ Dockerfile
├─ docker-compose.yml
└─ requirements.txt
```

## 快速启动

### 方式一：本地轻量运行

使用 Python 3.12：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

默认使用 SQLite，不启动 MQTT Consumer 和 MinIO。

访问：

- 看板：<http://localhost:8001/>
- Swagger：<http://localhost:8001/docs>
- 健康检查：<http://localhost:8001/health>

### 方式二：Docker Compose 二阶段完整环境

复制配置：

```powershell
Copy-Item .env.example .env
```

在 `.env` 中按需填写 Dify 和百炼密钥，然后启动：

```powershell
docker compose up -d --build
```

服务地址：

| 服务 | 地址 |
| --- | --- |
| Kita-AIoT | <http://localhost:8001> |
| Swagger | <http://localhost:8001/docs> |
| PostgreSQL | `localhost:5432` |
| MQTT | `localhost:1883` |
| MinIO API | `localhost:9000` |
| MinIO Console | <http://localhost:9001> |

MinIO 默认账号和密码均为 `minioadmin`，仅适合本地演示。

## 环境配置

主要配置见 `.env.example`：

```env
DATABASE_URL=postgresql+psycopg://kita:kita_password@localhost:5432/kita_aiot

MQTT_ENABLED=true
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_TOPIC=aiot/device/alarm

MINIO_ENABLED=true
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=device-documents

DIFY_API_BASE_URL=
DIFY_API_KEY=
DIFY_WORKFLOW_ENABLED=false

BAILIAN_API_KEY=
BAILIAN_MODEL=qwen-plus
```

## 使用示例

### 1. 模拟 MQTT 告警

完整 Docker 环境启动后：

```powershell
.\.venv\Scripts\python.exe scripts\mqtt_alarm_simulator.py `
  --host localhost `
  --port 1883 `
  --topic aiot/device/alarm `
  --count 3
```

### 2. 不使用 Broker 测试工作流

```powershell
.\.venv\Scripts\python.exe scripts\mqtt_alarm_simulator.py `
  --dry-run `
  --count 1 `
  --post-url http://localhost:8001/api/v1/alarms/report
```

### 3. 查询工作流记录

```powershell
curl.exe http://localhost:8001/api/v1/workflow-executions
```

### 4. 查询调用日志

```powershell
curl.exe http://localhost:8001/api/v1/call-logs
```

### 5. 上传设备文档到 MinIO

```powershell
curl.exe -X POST http://localhost:8001/api/v1/documents/ `
  -F "device_id=device-001" `
  -F "file=@docs/knowledge_base/device_manual.md"
```

### 6. 获取文档下载地址

```powershell
curl.exe http://localhost:8001/api/v1/documents/{document_id}/download-url
```

### 7. 查看组件配置状态

```powershell
curl.exe http://localhost:8001/api/v1/platforms/status
```

### 8. 一键冒烟验收

```powershell
.\.venv\Scripts\python.exe scripts\phase2_smoke_test.py
```

## Dify 主平台

完整配置说明见 [docs/dify_phase2_setup.md](docs/dify_phase2_setup.md)。

关键步骤：

1. 上传 `docs/knowledge_base/` 到 Dify 知识库。
2. 导入 `docs/dify_tools_openapi.yaml`。
3. 创建告警分析 Workflow。
4. 配置 Workflow API 地址和 Key。
5. 设置 `DIFY_WORKFLOW_ENABLED=true`。
6. 发布 MQTT 告警，检查 Dify 与本地工作流记录。

## 阿里云百炼基础接入

配置说明见 [docs/bailian_phase2_setup.md](docs/bailian_phase2_setup.md)。

填写 `BAILIAN_API_KEY` 后，可调用：

```text
POST /api/v1/platforms/bailian/test
```

## API 补充清单

| Method | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/api/v1/devices/` | 查询全部设备 |
| `GET` | `/api/v1/alarms/` | 查询全部告警 |
| `POST` | `/api/v1/alarms/report` | HTTP 触发告警工作流 |
| `GET` | `/api/v1/work-orders/` | 查询工单 |
| `POST` | `/api/v1/documents/` | 上传 MinIO 文档 |
| `GET` | `/api/v1/documents/{id}/download-url` | 获取临时下载地址 |
| `GET` | `/api/v1/workflow-executions` | 查询工作流记录 |
| `GET` | `/api/v1/call-logs` | 查询 API 调用日志 |
| `GET` | `/api/v1/platforms/status` | 查询组件配置状态 |

## 演示视频 / GIF

录制分镜与命令见 [docs/demo/recording_script.md](docs/demo/recording_script.md)。

建议提交以下素材：

- `docs/demo/kita-aiot-phase2.mp4`
- `docs/demo/kita-aiot-phase2.gif`
- `docs/screenshots/phase2_dashboard.png`
- Dify Workflow 运行详情截图
- 百炼基础连通截图

真实平台截图和视频必须在填入你自己的账号凭据后录制，并注意遮挡密钥。

## 当前边界

- SQLAlchemy 当前使用自动建表，生产环境建议引入 Alembic 管理迁移。
- Dify 与百炼是否真实成功取决于外部平台地址、网络和有效 API Key。
- critical 告警自动建单；warning 重复次数策略可在后续阶段继续细化。
- MinIO 与 Mosquitto 的默认凭据/匿名访问仅用于本地演示。
